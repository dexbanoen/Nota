from dataclasses import dataclass
import fitz  # PyMuPDF


@dataclass
class ParsedPage:
    """Represents extracted text from a single PDF page."""
    page_number: int  # 1-indexed
    text: str


class PDFParserAdapter:
    """
    Adapter around PyMuPDF for extracting text from PDF files.

    Only extracts selectable text; does not perform OCR.
    Pages with no selectable text return an empty string.
    """

    def extract_pages(self, file_path: str) -> list[ParsedPage]:
        """
        Extract text from every page of a PDF.

        Args:
            file_path: Absolute or relative path to the PDF file.

        Returns:
            List of ParsedPage objects, one per page (1-indexed).
        """
        pages: list[ParsedPage] = []

        with fitz.open(file_path) as doc:
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text("text") or ""
                pages.append(
                    ParsedPage(page_number=page_index + 1, text=text.strip())
                )

        return pages
