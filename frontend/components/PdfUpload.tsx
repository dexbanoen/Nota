"use client";
import { useRef, useState } from "react";
import { uploadDocument, type Document } from "@/lib/api";

interface Props {
  courseId: number;
  onUploaded: (doc: Document) => void;
}

export default function PdfUpload({ courseId, onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  async function handleFile(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const doc = await uploadDocument(courseId, file);
      onUploaded(doc);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    // Reset so same file can be re-uploaded
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div>
      <div
        id="pdf-dropzone"
        onClick={() => !loading && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? "var(--accent)" : "var(--border)"}`,
          borderRadius: 12,
          padding: "32px 24px",
          textAlign: "center",
          cursor: loading ? "not-allowed" : "pointer",
          transition: "border-color 0.2s, background 0.2s",
          background: dragOver ? "rgba(99,102,241,0.05)" : "transparent",
        }}
      >
        {loading ? (
          <>
            <div
              style={{
                fontSize: "1.5rem",
                marginBottom: "8px",
                animation: "spin 1s linear infinite",
              }}
            >
              ⏳
            </div>
            <p style={{ color: "var(--text-muted)", margin: 0, fontSize: "0.875rem" }}>
              Processing PDF — this may take a moment…
            </p>
          </>
        ) : (
          <>
            <div style={{ fontSize: "2rem", marginBottom: "8px" }}>📄</div>
            <p
              style={{
                margin: "0 0 4px",
                fontWeight: 600,
                fontSize: "0.9rem",
                color: "var(--text)",
              }}
            >
              Drop a PDF here or click to upload
            </p>
            <p style={{ margin: 0, fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Selectable text only · One file at a time
            </p>
          </>
        )}
      </div>

      <input
        ref={inputRef}
        id="pdf-file-input"
        type="file"
        accept=".pdf"
        onChange={handleChange}
        style={{ display: "none" }}
      />

      {error && (
        <p
          style={{
            color: "var(--error)",
            fontSize: "0.8rem",
            marginTop: "8px",
            marginBottom: 0,
          }}
        >
          ⚠ {error}
        </p>
      )}
    </div>
  );
}
