"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getCourses, type Course } from "@/lib/api";
import CourseCard from "@/components/CourseCard";
import CourseForm from "@/components/CourseForm";

export default function CoursesPage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCourses()
      .then(setCourses)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function handleCourseCreated(course: Course) {
    setCourses((prev) => [course, ...prev]);
  }

  return (
    <div
      style={{
        maxWidth: 720,
        margin: "0 auto",
        padding: "2rem 1.5rem",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "2rem",
        }}
      >
        <div>
          <Link
            href="/"
            style={{
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              display: "block",
              marginBottom: "4px",
            }}
          >
            ← Home
          </Link>
          <h1
            style={{
              margin: 0,
              fontSize: "1.75rem",
              fontWeight: 700,
              color: "var(--text)",
            }}
          >
            Courses
          </h1>
        </div>
      </div>

      {/* Create form */}
      <div style={{ marginBottom: "2rem" }}>
        <CourseForm onCreated={handleCourseCreated} />
      </div>

      {/* Course list */}
      {loading ? (
        <p style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
          Loading…
        </p>
      ) : error ? (
        <p style={{ color: "var(--error)", fontSize: "0.875rem" }}>
          ⚠ {error}
        </p>
      ) : courses.length === 0 ? (
        <div
          style={{
            textAlign: "center",
            padding: "3rem 0",
            color: "var(--text-muted)",
          }}
        >
          <p style={{ fontSize: "2rem", margin: "0 0 8px" }}>🎓</p>
          <p style={{ margin: 0, fontSize: "0.875rem" }}>
            No courses yet. Create your first course above.
          </p>
        </div>
      ) : (
        <div
          id="courses-list"
          style={{ display: "flex", flexDirection: "column", gap: "12px" }}
        >
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
