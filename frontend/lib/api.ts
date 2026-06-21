// lib/api.ts — All calls to the FastAPI backend go through this file.

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// ─────────────────────────────────────────────
// Types mirroring backend Pydantic schemas
// ─────────────────────────────────────────────

export interface Course {
  id: number;
  name: string;
  created_at: string;
}

export interface Document {
  id: number;
  course_id: number;
  filename: string;
  status: "UPLOADED" | "PROCESSING" | "PROCESSED" | "FAILED";
  page_count: number;
  uploaded_at: string;
  processed_at: string | null;
  error_message: string | null;
}

export interface Source {
  document_id: number;
  filename: string;
  page_number: number;
  chunk_text: string;
  relevance_score: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ─────────────────────────────────────────────
// Course endpoints
// ─────────────────────────────────────────────

export async function createCourse(name: string): Promise<Course> {
  const res = await fetch(`${BASE_URL}/courses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return handleResponse<Course>(res);
}

export async function getCourses(): Promise<Course[]> {
  const res = await fetch(`${BASE_URL}/courses`, { cache: "no-store" });
  return handleResponse<Course[]>(res);
}

export async function getCourse(courseId: number): Promise<Course> {
  const res = await fetch(`${BASE_URL}/courses/${courseId}`, {
    cache: "no-store",
  });
  return handleResponse<Course>(res);
}

// ─────────────────────────────────────────────
// Document endpoints
// ─────────────────────────────────────────────

export async function uploadDocument(
  courseId: number,
  file: File
): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE_URL}/courses/${courseId}/documents`, {
    method: "POST",
    body: form,
  });
  return handleResponse<Document>(res);
}

export async function getDocuments(courseId: number): Promise<Document[]> {
  const res = await fetch(`${BASE_URL}/courses/${courseId}/documents`, {
    cache: "no-store",
  });
  return handleResponse<Document[]>(res);
}

// ─────────────────────────────────────────────
// Chat endpoint (non-streaming, legacy)
// ─────────────────────────────────────────────

export async function askQuestion(
  courseId: number,
  question: string
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/courses/${courseId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return handleResponse<ChatResponse>(res);
}

// ─────────────────────────────────────────────
// Chat endpoint (streaming via SSE)
// ─────────────────────────────────────────────

export interface StreamCallbacks {
  onSources: (sources: Source[]) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

/**
 * Ask a question and receive a streaming answer via Server-Sent Events.
 *
 * The backend sends:
 *   event: sources  → JSON array of Source objects
 *   event: token    → a single text token (JSON-encoded string)
 *   event: done     → stream complete
 *   event: error    → error details
 *
 * Returns an AbortController so the caller can cancel the stream.
 */
export function askQuestionStream(
  courseId: number,
  question: string,
  callbacks: StreamCallbacks
): AbortController {
  const controller = new AbortController();

  (async () => {
    try {
      const res = await fetch(`${BASE_URL}/courses/${courseId}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      });

      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const body = await res.json();
          detail = body.detail || JSON.stringify(body);
        } catch {
          detail = await res.text();
        }
        callbacks.onError(detail);
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        callbacks.onError("No response body");
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE messages are separated by double newlines
        const messages = buffer.split("\n\n");
        // Keep the last incomplete chunk in the buffer
        buffer = messages.pop() || "";

        for (const message of messages) {
          if (!message.trim()) continue;

          // Parse SSE: "event: <type>\ndata: <payload>"
          let eventType = "";
          let dataStr = "";

          for (const line of message.split("\n")) {
            if (line.startsWith("event: ")) {
              eventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              dataStr = line.slice(6);
            }
          }

          if (!eventType) continue;

          switch (eventType) {
            case "sources":
              try {
                const sources: Source[] = JSON.parse(dataStr);
                callbacks.onSources(sources);
              } catch {
                // ignore malformed sources
              }
              break;
            case "token":
              try {
                const token: string = JSON.parse(dataStr);
                callbacks.onToken(token);
              } catch {
                // Raw text fallback
                callbacks.onToken(dataStr);
              }
              break;
            case "done":
              callbacks.onDone();
              return;
            case "error":
              try {
                const err = JSON.parse(dataStr);
                callbacks.onError(err.detail || "Unknown error");
              } catch {
                callbacks.onError(dataStr || "Unknown error");
              }
              return;
          }
        }
      }

      // Stream ended without explicit 'done' event
      callbacks.onDone();
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return; // User cancelled — not an error
      }
      callbacks.onError(err instanceof Error ? err.message : "Stream failed");
    }
  })();

  return controller;
}
