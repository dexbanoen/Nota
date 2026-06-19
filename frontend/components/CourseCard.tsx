"use client";
import Link from "next/link";
import type { Course } from "@/lib/api";

interface Props {
  course: Course;
}

export default function CourseCard({ course }: Props) {
  const date = new Date(course.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <Link href={`/courses/${course.id}`} style={{ display: "block" }}>
      <div
        id={`course-card-${course.id}`}
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "20px 24px",
          transition: "border-color 0.2s, transform 0.15s, box-shadow 0.15s",
          cursor: "pointer",
        }}
        onMouseEnter={(e) => {
          const el = e.currentTarget as HTMLDivElement;
          el.style.borderColor = "var(--accent)";
          el.style.transform = "translateY(-2px)";
          el.style.boxShadow = "0 6px 24px rgba(99,102,241,0.15)";
        }}
        onMouseLeave={(e) => {
          const el = e.currentTarget as HTMLDivElement;
          el.style.borderColor = "var(--border)";
          el.style.transform = "translateY(0)";
          el.style.boxShadow = "none";
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: "1rem",
          }}
        >
          <div>
            <h3
              style={{
                margin: "0 0 4px",
                fontSize: "1rem",
                fontWeight: 600,
                color: "var(--text)",
              }}
            >
              {course.name}
            </h3>
            <p
              style={{
                margin: 0,
                fontSize: "0.8rem",
                color: "var(--text-muted)",
              }}
            >
              Created {date}
            </p>
          </div>
          <span
            style={{
              flexShrink: 0,
              fontSize: "1.25rem",
              opacity: 0.5,
            }}
          >
            →
          </span>
        </div>
      </div>
    </Link>
  );
}
