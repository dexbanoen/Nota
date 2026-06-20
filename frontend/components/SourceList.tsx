"use client";
import type { Source } from "@/lib/api";

interface Props {
  sources: Source[];
}

export default function SourceList({ sources }: Props) {
  if (sources.length === 0) return null;

  return (
    <div>
      <h4
        style={{
          margin: "0 0 12px",
          fontSize: "0.8rem",
          fontWeight: 600,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
        }}
      >
        Sources
      </h4>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {sources.map((src, i) => (
          <div
            key={i}
            id={`source-${i}`}
            style={{
              background: "var(--surface-2)",
              border: "1px solid var(--border)",
              borderLeft: "3px solid var(--accent)",
              borderRadius: 8,
              padding: "12px 16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "1rem",
                marginBottom: "6px",
              }}
            >
              <span
                style={{
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  color: "var(--text)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                📄 {src.filename}
              </span>
              <div style={{ display: "flex", gap: "6px", flexShrink: 0 }}>
                <span
                  style={{
                    background:
                      src.relevance_score >= 0.5
                        ? "rgba(34,197,94,0.15)"
                        : "rgba(245,158,11,0.15)",
                    color:
                      src.relevance_score >= 0.5
                        ? "var(--success)"
                        : "var(--warning)",
                    borderRadius: 4,
                    padding: "2px 8px",
                    fontSize: "0.7rem",
                    fontWeight: 600,
                  }}
                >
                  {Math.round(src.relevance_score * 100)}% match
                </span>
                <span
                  style={{
                    background: "rgba(99,102,241,0.15)",
                    color: "var(--accent-hover)",
                    borderRadius: 4,
                    padding: "2px 8px",
                    fontSize: "0.75rem",
                    fontWeight: 600,
                  }}
                >
                  p. {src.page_number}
                </span>
              </div>
            </div>
            <p
              style={{
                margin: 0,
                fontSize: "0.8rem",
                color: "var(--text-muted)",
                lineHeight: 1.5,
                display: "-webkit-box",
                WebkitLineClamp: 3,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {src.chunk_text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
