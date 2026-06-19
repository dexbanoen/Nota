"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getCourse, type Course } from "@/lib/api";
import ChatBox from "@/components/ChatBox";

interface Props {
  courseId: number;
}

export default function ChatPageClient({ courseId }: Props) {
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCourse(courseId)
      .then(setCourse)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [courseId]);

  if (loading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)" }}>
        Loading chat…
      </div>
    );
  }

  if (error || !course) {
    return (
      <div style={{ padding: "3rem", textAlign: "center" }}>
        <p style={{ color: "var(--error)", marginBottom: "1rem" }}>⚠ {error}</p>
        <Link href={`/courses/${courseId}`} style={{ color: "var(--accent)" }}>
          ← Back to Course
        </Link>
      </div>
    );
  }

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
          marginBottom: "1rem",
        }}
      >
        <div>
          <Link
            href={`/courses/${course.id}`}
            style={{
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              display: "block",
              marginBottom: "4px",
            }}
          >
            ← {course.name}
          </Link>
          <h1
            style={{
              margin: 0,
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--text)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            💬 Study Chat
          </h1>
        </div>
      </div>

      <ChatBox courseId={course.id} />
    </div>
  );
}
