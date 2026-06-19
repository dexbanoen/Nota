"use client";
import Link from "next/link";

export default function HomePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        textAlign: "center",
      }}
    >
      {/* Logo mark */}
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 16,
          background: "linear-gradient(135deg, #6366f1, #818cf8)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 28,
          marginBottom: "1.5rem",
          boxShadow: "0 0 40px rgba(99,102,241,0.3)",
        }}
      >
        📚
      </div>

      <h1
        style={{
          fontSize: "clamp(2.5rem, 6vw, 4rem)",
          fontWeight: 800,
          margin: "0 0 0.5rem",
          background: "linear-gradient(135deg, #e2e8f0, #818cf8)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          letterSpacing: "-0.02em",
        }}
      >
        Nota
      </h1>

      <p
        style={{
          color: "var(--text-muted)",
          fontSize: "1.125rem",
          maxWidth: 480,
          margin: "0 0 2.5rem",
        }}
      >
        A local-first study assistant. Upload lecture PDFs, ask questions, and
        get answers grounded in your own course material — no cloud, no
        tracking.
      </p>

      <Link href="/courses" id="go-to-courses-btn">
        <button
          style={{
            background: "linear-gradient(135deg, #6366f1, #818cf8)",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "14px 36px",
            fontSize: "1rem",
            fontWeight: 600,
            letterSpacing: "0.01em",
            boxShadow: "0 4px 20px rgba(99,102,241,0.4)",
            transition: "transform 0.15s, box-shadow 0.15s",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform =
              "translateY(-2px)";
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 6px 28px rgba(99,102,241,0.5)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLButtonElement).style.transform =
              "translateY(0)";
            (e.currentTarget as HTMLButtonElement).style.boxShadow =
              "0 4px 20px rgba(99,102,241,0.4)";
          }}
        >
          Open Courses →
        </button>
      </Link>

      {/* Feature pills */}
      <div
        style={{
          display: "flex",
          gap: "0.75rem",
          flexWrap: "wrap",
          justifyContent: "center",
          marginTop: "3rem",
        }}
      >
        {[
          "🔒 100% Local",
          "📄 PDF Ingestion",
          "🔍 Semantic Search",
          "🤖 llama3.1:8b",
        ].map((label) => (
          <span
            key={label}
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 20,
              padding: "6px 14px",
              fontSize: "0.8rem",
              color: "var(--text-muted)",
            }}
          >
            {label}
          </span>
        ))}
      </div>
    </main>
  );
}
