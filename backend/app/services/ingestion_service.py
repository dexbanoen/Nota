import os
import logging
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories.course_repository import CourseRepository
from app.repositories.document_repository import DocumentRepository
from app.models.document import DocumentStatus
from app.adapters.pdf_parser_adapter import PDFParserAdapter
from app.chunking.page_chunking_strategy import PageChunkingStrategy
from app.services.embedding_service import EmbeddingService
from app.vector_store.chroma_store import ChromaStore, ChunkRecord

logger = logging.getLogger(__name__)
settings = get_settings()


class IngestionService:
    """
    Orchestrates the full PDF ingestion pipeline:

    1. Validate the file is a PDF
    2. Save the file to local storage
    3. Create/update the document record (status: PROCESSING)
    4. Extract text page-by-page via PyMuPDF
    5. Chunk each page
    6. Generate embeddings (batch per document for efficiency)
    7. Store chunks + embeddings in ChromaDB
    8. Mark document as PROCESSED
    9. On any failure, mark document as FAILED with the error message
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.course_repo = CourseRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.pdf_parser = PDFParserAdapter()
        self.chunker = PageChunkingStrategy()
        self.embedding_service = EmbeddingService()
        self.chroma = ChromaStore()

    def ingest(
        self,
        course_id: int,
        filename: str,
        file_bytes: bytes,
    ) -> int:
        """
        Run the full ingestion pipeline for one PDF.

        Args:
            course_id: The course this PDF belongs to.
            filename: Original filename (used in metadata).
            file_bytes: Raw PDF bytes from the upload.

        Returns:
            The created document's id.

        Raises:
            ValueError: If the file is not a valid PDF.
        """
        # 1. Validate PDF magic bytes
        if not file_bytes.startswith(b"%PDF"):
            raise ValueError(f"File '{filename}' does not appear to be a valid PDF.")

        # 2. Save the PDF to local storage
        file_path = self._save_pdf(course_id, filename, file_bytes)

        # 3. Create the document record with PROCESSING status
        document = self.doc_repo.create_document(
            course_id=course_id,
            filename=filename,
            file_path=file_path,
            status=DocumentStatus.PROCESSING,
        )

        try:
            # 4. Extract text page-by-page
            parsed_pages = self.pdf_parser.extract_pages(file_path)

            # 5. Chunk every page
            all_chunks = []
            for page in parsed_pages:
                chunks = self.chunker.chunk(page.page_number, page.text)
                all_chunks.extend(chunks)

            if not all_chunks:
                logger.warning(
                    "Document %d (%s) produced no text chunks. "
                    "The PDF may contain only images or scanned pages.",
                    document.id,
                    filename,
                )

            # 6. Generate embeddings in batch
            chunk_texts = [c.text for c in all_chunks]
            embeddings: list[list[float]] = []
            if chunk_texts:
                embeddings = self.embedding_service.embed_texts(chunk_texts)

            # 7. Store chunks + embeddings in ChromaDB
            chroma_records = [
                ChunkRecord(
                    id=f"course_{course_id}_doc_{document.id}_page_{chunk.page_number}_chunk_{chunk.chunk_index}",
                    text=chunk.text,
                    embedding=embedding,
                    course_id=course_id,
                    document_id=document.id,
                    filename=filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                )
                for chunk, embedding in zip(all_chunks, embeddings)
            ]
            self.chroma.add_chunks(chroma_records)

            # 8. Mark document as PROCESSED
            self.doc_repo.update_processed(document, page_count=len(parsed_pages))
            logger.info(
                "Ingestion complete: document %d, %d pages, %d chunks.",
                document.id, len(parsed_pages), len(all_chunks),
            )

        except Exception as exc:
            # 9. Mark as FAILED and preserve the error message
            error_msg = str(exc)
            logger.error(
                "Ingestion failed for document %d: %s", document.id, error_msg
            )
            self.doc_repo.update_failed(document, error_message=error_msg)

        return document.id

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _save_pdf(self, course_id: int, filename: str, file_bytes: bytes) -> str:
        """Save the raw PDF bytes to the per-course storage directory."""
        storage_root = os.path.abspath(settings.pdf_storage_path)
        course_dir = os.path.join(storage_root, f"course_{course_id}")
        os.makedirs(course_dir, exist_ok=True)

        file_path = os.path.join(course_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return file_path
