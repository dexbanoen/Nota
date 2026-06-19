# Nota — Local-First RAG Study Assistant

Nota is a senior-level MVP project for a local-first study assistant. It allows users to create courses, upload lecture PDFs, and ask questions grounded entirely in the uploaded material.

Designed to run locally, Nota ensures absolute privacy. Your PDFs never leave your machine, and the AI runs locally on your own hardware using Ollama. No cloud, no API keys, no subscriptions.

## Tech Stack

**Frontend**
* Next.js (App Router)
* React & TypeScript
* Tailwind CSS (v4)
* Fetch API client

**Backend**
* FastAPI (Python)
* SQLAlchemy (SQLite)
* Pydantic (Data validation)
* PyMuPDF (PDF text extraction)
* ChromaDB (Local vector database)
* Local Ollama (Embeddings and LLM generation)

## Architecture Summary

Nota uses a **Layered Modular Monolith** architecture in the backend:

1. **API Layer**: Thin FastAPI routes handling HTTP requests.
2. **Service Layer**: Orchestrates business logic (`CourseService`, `IngestionService`, `RAGService`).
3. **Repository Layer**: Abstracts database operations (`CourseRepository`, `DocumentRepository`).
4. **Adapter Layer**: Wraps external tools and libraries (`PDFParserAdapter`, `OllamaEmbeddingAdapter`, `OllamaLLMAdapter`).
5. **Data Layer**: SQLite for relational metadata (courses, documents) and ChromaDB for vector embeddings and text chunks.

## Prerequisites

Before running Nota, ensure you have the following installed:

1. **Python 3.10+**
2. **Node.js 18+** & npm
3. **Ollama** installed locally (https://ollama.com)

## Running Ollama

Nota relies on local AI models via Ollama. You must pull the required models and keep the Ollama server running.

1. Open a terminal and run the Ollama server (if not already running in the background):
   ```bash
   ollama serve
   ```
2. Pull the LLM model (for answering questions):
   ```bash
   ollama pull llama3.1:8b
   ```
3. Pull the embedding model (for vector search):
   ```bash
   ollama pull nomic-embed-text
   ```

## Running the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create your `.env` file (a `.env.example` is provided):
   ```bash
   cp .env.example .env
   ```
4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

The backend API will be available at `http://localhost:8000`.
On first startup, it will automatically create the SQLite database and necessary data directories.

## Running the Frontend

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Create your `.env.local` file (a `.env.local.example` is provided):
   ```bash
   cp .env.local.example .env.local
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

The frontend UI will be available at `http://localhost:3000`.

## Example User Flow

1. **Open Nota**: Navigate to `http://localhost:3000` in your browser.
2. **Create a Course**: Click "Open Courses", enter a course name (e.g., "Operating Systems"), and click "Create".
3. **Upload PDFs**: Click into your new course and upload your lecture slides or notes (PDF format).
4. **Backend Processing**: The backend extracts the text, splits it into overlapping chunks, generates vector embeddings using Ollama, and stores them in ChromaDB.
5. **Study Chat**: Once processing is complete, click "Study Chat".
6. **Ask a Question**: Ask something like "What is virtual memory?".
7. **RAG Retrieval**: The system searches ChromaDB for the 5 most relevant chunks from your specific course.
8. **LLM Generation**: The local `llama3.1:8b` model generates a concise answer based *only* on those chunks.
9. **View Sources**: The UI displays the answer along with citations showing the exact filename and page number where the information was found.

## Known MVP Limitations

* **No OCR**: PDFs must contain selectable text. Images or scanned documents without text layers will yield empty chunks.
* **Synchronous Ingestion**: PDF processing happens synchronously during the upload request. Large PDFs may cause the upload request to time out.
* **Single User**: There is no authentication or multi-user isolation.
* **No Cloud Backup**: All data is stored locally. Deleting the `backend/data` or `storage/pdfs` folders will erase your data.

## Future Expansion Ideas

* Implement background workers (e.g., Celery or RQ) for asynchronous PDF ingestion.
* Add OCR support via Tesseract for scanned documents.
* Implement conversation memory (history) in the chat page.
* Add features for generating flashcards or quizzes from the course material.
* Dockerize the application for easier deployment.
