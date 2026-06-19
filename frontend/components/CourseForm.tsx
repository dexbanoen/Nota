"use client";
import { useState } from "react";
import { createCourse, type Course } from "@/lib/api";

interface Props {
  onCreated: (course: Course) => void;
}

export default function CourseForm({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const course = await createCourse(name.trim());
      onCreated(course);
      setName("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create course.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "20px 24px",
      }}
    >
      <h3
        style={{
          margin: "0 0 16px",
          fontSize: "0.95rem",
          fontWeight: 600,
          color: "var(--text)",
        }}
      >
        New Course
      </h3>

      <div style={{ display: "flex", gap: "10px" }}>
        <input
          id="course-name-input"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Algorithms & Data Structures"
          disabled={loading}
          style={{ flex: 1 }}
        />
        <button
          id="create-course-btn"
          type="submit"
          disabled={loading || !name.trim()}
          style={{
            background: loading ? "var(--surface-2)" : "var(--accent)",
            color: loading ? "var(--text-muted)" : "#fff",
            border: "none",
            borderRadius: 8,
            padding: "10px 20px",
            fontSize: "0.875rem",
            fontWeight: 600,
            whiteSpace: "nowrap",
            transition: "background 0.2s",
          }}
        >
          {loading ? "Creating…" : "Create"}
        </button>
      </div>

      {error && (
        <p
          style={{
            color: "var(--error)",
            fontSize: "0.8rem",
            marginTop: "8px",
            marginBottom: 0,
          }}
        >
          {error}
        </p>
      )}
    </form>
  );
}
