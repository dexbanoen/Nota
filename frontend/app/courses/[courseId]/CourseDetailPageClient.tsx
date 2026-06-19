"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { getCourse, getDocuments, type Course, type Document } from "@/lib/api";
import PdfUpload from "@/components/PdfUpload";
import DocumentList from "@/components/DocumentList";

interface Props {
  courseId: number;
}

export default function CourseDetailPageClient({ courseId }: Props) {
  const [course, setCourse] = useState<Course | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCourseData = useCallback(async () => {
    try {
      const [courseData, docsData] = await Promise.all([
        getCourse(courseId),
        getDocuments(courseId),
      ]);
      setCourse(courseData);
      setDocuments(docsData);
      setError(null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load course.");
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  useEffect(() => {
    fetchCourseData();
    // Poll every 5s if there are processing documents
    const interval = setInterval(() => {
      setDocuments((currentDocs) => {
        const isProcessing = currentDocs.some((d) => d.status === "PROCESSING");
        if (isProcessing) {
          fetchCourseData();
        }
        return currentDocs;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchCourseData]);

  function handleDocumentUploaded(doc: Document) {
    setDocuments((prev) => [doc, ...prev]);
  }

  if (loading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        Loading…
      </div>
    );
  }

  if (error || !course) {
    return (
      <div style={{ padding: "3rem", textAlign: "center" }}>
        <p style={{ color: "var(--error)", marginBottom: "1rem" }}>⚠ {error}</p>
        <Link href="/courses" style={{ color: "var(--accent)" }}>
          ← Back to Courses
        </Link>
      </div>
    );
  }

  const hasProcessedDocs = documents.some((d) => d.status === "PROCESSED");

  return (
    <div
      style={{
        maxWidth: 800,
        margin: "0 auto",
        padding: "2rem 1.5rem",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: "2rem",
          gap: "1rem",
        }}
      >
        <div>
          <Link
            href="/courses"
            style={{
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              display: "block",
              marginBottom: "4px",
            }}
          >
            ← Courses
          </Link>
          <h1
            style={{
              margin: 0,
              fontSize: "1.75rem",
              fontWeight: 700,
              color: "var(--text)",
            }}
          >
            {course.name}
          </h1>
        </div>

        <Link href={`/courses/${course.id}/chat`} id="study-chat-link">
          <button
            disabled={!hasProcessedDocs}
            style={{
              background: hasProcessedDocs ? "var(--accent)" : "var(--surface-2)",
              color: hasProcessedDocs ? "#fff" : "var(--text-muted)",
              border: "none",
              borderRadius: 8,
              padding: "10px 20px",
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: hasProcessedDocs ? "pointer" : "not-allowed",
              boxShadow: hasProcessedDocs ? "0 4px 14px rgba(99,102,241,0.3)" : "none",
              transition: "transform 0.15s, box-shadow 0.15s",
            }}
            title={!hasProcessedDocs ? "Upload and process PDFs to enable chat" : ""}
          >
            💬 Study Chat
          </button>
        </Link>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
        {/* Upload section */}
        <section>
          <h2
            style={{
              margin: "0 0 16px",
              fontSize: "1.1rem",
              fontWeight: 600,
              color: "var(--text)",
            }}
          >
            Upload Lecture
          </h2>
          <PdfUpload courseId={course.id} onUploaded={handleDocumentUploaded} />
        </section>

        {/* Documents section */}
        <section>
          <h2
            style={{
              margin: "0 0 16px",
              fontSize: "1.1rem",
              fontWeight: 600,
              color: "var(--text)",
            }}
          >
            Documents
          </h2>
          <DocumentList documents={documents} />
        </section>
      </div>
    </div>
  );
}
