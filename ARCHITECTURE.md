# Nota: Architecture & Design Overview

This document provides a high-level overview of the Nota system architecture, design patterns, and internal data flows. This is intended to help you understand the codebase for future development or technical interviews.

## 1. High-Level Architecture

Nota is built as a **Layered Modular Monolith**. It consists of a React/Next.js frontend that communicates with a FastAPI Python backend. The backend is responsible for all business logic, data processing, and AI integration.

```mermaid
graph TD
    Client[Next.js Frontend\nReact, Tailwind] -->|HTTP REST API| API[FastAPI Backend]
    
    subgraph Backend Monolith
        API --> Services[Service Layer]
        
        Services --> Repos[Repository Layer]
        Services --> Adapters[Adapter Layer]
        Services --> VectorDB[ChromaDB Vector Store]
        
        Repos --> SQLite[(SQLite DB\nRelational Metadata)]
        Adapters --> Ollama[Local Ollama\nLLM & Embeddings]
        Adapters --> PyMuPDF[PyMuPDF\nText Extraction]
    end
```

## 2. Design Patterns

The backend strictly follows several software engineering design patterns to keep the code modular, testable, and clean:

### Layered Architecture / Service Layer Pattern
Instead of writing business logic directly inside the API routes, the API routes are completely "dumb". They immediately pass requests to the **Service Layer** (`CourseService`, `IngestionService`, `RAGService`). The Service Layer orchestrates the process.

### Repository Pattern
The Service layer never writes raw SQL queries. Instead, it calls the **Repository Layer** (`CourseRepository`, `DocumentRepository`). This abstracts away the database operations (using SQLAlchemy), meaning if we ever wanted to swap SQLite for PostgreSQL, we would only need to change the Repositories, not the Services.

### Adapter Pattern
We wrap external libraries and APIs (like PyMuPDF and Ollama) in **Adapters** (`PDFParserAdapter`, `OllamaLLMAdapter`). This isolates the rest of the application from third-party code changes. If we decided to swap Ollama for OpenAI, we would just write a new `OpenAIAdapter` without changing the core RAG logic.

### Strategy Pattern
Text chunking uses the Strategy pattern. We defined a base `ChunkingStrategy` interface, and implemented `PageChunkingStrategy`. If we later want to chunk text by paragraphs instead of pages, we can just create a `ParagraphChunkingStrategy` and swap it in.

## 3. Core Pipelines (Internals)

There are two major data flows in Nota: **Ingestion** (uploading a PDF) and **Retrieval** (asking a question).

### A. The PDF Ingestion Pipeline
When a user uploads a PDF, the `IngestionService` takes over.

```mermaid
sequenceDiagram
    participant User
    participant API as Documents API
    participant Ingestion as IngestionService
    participant PDF as PDFParserAdapter
    participant Ollama as OllamaEmbeddingAdapter
    participant Chroma as ChromaStore
    participant DB as SQLite

    User->>API: Upload PDF
    API->>Ingestion: ingest(file_bytes)
    Ingestion->>DB: Save Document status = PROCESSING
    Ingestion->>PDF: Extract text page-by-page
    PDF-->>Ingestion: Return ParsedPages
    Ingestion->>Ingestion: Chunk text (PageChunkingStrategy)
    Ingestion->>Ollama: embed_texts(chunks)
    Ollama-->>Ingestion: Return Vectors
    Ingestion->>Chroma: Store Chunks + Vectors
    Ingestion->>DB: Update Document status = PROCESSED
    Ingestion-->>API: Success
    API-->>User: Return Document Details
```

### B. The RAG Retrieval Pipeline
When a user asks a question, the `RAGService` orchestrates the retrieval-augmented generation. We use Server-Sent Events (SSE) to stream the response back to the client progressively.

```mermaid
sequenceDiagram
    participant User
    participant API as Chat API
    participant RAG as RAGService
    participant OllamaEmb as OllamaEmbeddingAdapter
    participant Chroma as ChromaStore
    participant OllamaLLM as OllamaLLMAdapter

    User->>API: Ask Question
    API->>RAG: ask_stream(course_id, question)
    RAG->>OllamaEmb: embed(question)
    OllamaEmb-->>RAG: Return Question Vector
    RAG->>Chroma: search(vector, course_id, limit=5)
    Chroma-->>RAG: Return top 5 relevant text chunks
    RAG-->>API: Stream Sources (Filename, Page)
    API-->>User: Display Sources Immediately
    RAG->>OllamaLLM: generate_stream(context=chunks, question)
    loop Token Generation
        OllamaLLM-->>RAG: Yield token
        RAG-->>API: Stream token (SSE)
        API-->>User: Display token progressively
    end
```

## 4. Component Interactions

Here is a breakdown of what interacts with what in the backend:

*   **`app/api/`**: The entry point. Extracts JSON/Form data from HTTP requests, validates it using Pydantic schemas, and calls a Service.
*   **`app/services/`**: Contains the core logic. 
    *   `IngestionService` talks to the `PDFParserAdapter` to get text, `EmbeddingService` to get vectors, `ChromaStore` to save chunks, and `DocumentRepository` to update statuses.
    *   `RAGService` talks to the `EmbeddingService` to vectorize the question, `ChromaStore` to search, and `LLMService` to generate the final answer.
*   **`app/repositories/`**: The only layer that imports `Session` from SQLAlchemy. Reads/writes to SQLite using the models defined in `app/models/`.
*   **`app/adapters/`**: The only layer that imports `httpx` (for Ollama HTTP requests) or `fitz` (PyMuPDF).
*   **`app/vector_store/`**: The only layer that imports `chromadb`. Maintains a persistent connection to the local Chroma DB directory.

## 5. Security & Privacy Context

For an interview context, emphasize that Nota was intentionally built as a **local-first** application.
1.  **Data Sovereignty**: Course materials are never sent to a cloud provider. PDFs are saved locally in `/storage`.
2.  **Private AI**: Vector embeddings and LLM generations run locally via Ollama, preventing third-party data collection.
3.  **Scoped Retrieval**: ChromaDB searches are strictly filtered by `course_id`. A user asking a question in the "Physics" course will mathematically never retrieve text chunks from the "History" course, preventing data contamination.
