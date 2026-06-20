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
// Chat endpoint
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
