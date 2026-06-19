"use client";
import type { Document } from "@/lib/api";

interface Props {
  documents: Document[];
}

const STATUS_CONFIG: Record<
  Document["status"],
  { color: string; label: string; dot: string }
> = {
  UPLOADED: {
    color: "var(--text-muted)",
    label: "Uploaded",
    dot: "#94a3b8",
  },
  PROCESSING: {
    color: "var(--processing)",
    label: "Processing…",
    dot: "#6366f1",
  },
  PROCESSED: {
    color: "var(--success)",
    label: "Ready",
    dot: "#22c55e",
  },
  FAILED: {
    color: "var(--error)",
    label: "Failed",
    dot: "#ef4444",
  },
};

export default function DocumentList({ documents }: Props) {
  if (documents.length === 0) {
    return (
      <p
        style={{
          color: "var(--text-muted)",
          fontSize: "0.875rem",
          margin: 0,
          padding: "16px 0",
        }}
      >
        No documents uploaded yet.
      </p>
    );
  }

  return (
    <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: "8px" }}>
      {documents.map((doc) => {
        const cfg = STATUS_CONFIG[doc.status];
        return (
          <li
            key={doc.id}
            id={`doc-${doc.id}`}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "14px 18px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "1rem",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
              <span style={{ fontSize: "1.1rem", flexShrink: 0 }}>📄</span>
              <div style={{ minWidth: 0 }}>
                <p
                  style={{
                    margin: "0 0 2px",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                    color: "var(--text)",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {doc.filename}
                </p>
                {doc.page_count > 0 && (
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {doc.page_count} pages
                  </p>
                )}
                {doc.error_message && (
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "var(--error)" }}>
                    {doc.error_message}
                  </p>
                )}
              </div>
            </div>

            <span
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "0.8rem",
                color: cfg.color,
                flexShrink: 0,
                fontWeight: 500,
              }}
            >
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  background: cfg.dot,
                  display: "inline-block",
                }}
              />
              {cfg.label}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
