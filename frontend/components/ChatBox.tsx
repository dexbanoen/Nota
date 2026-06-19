"use client";
import { useState } from "react";
import { askQuestion, type ChatResponse } from "@/lib/api";
import SourceList from "./SourceList";

interface Props {
  courseId: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: ChatResponse["sources"];
}

export default function ChatBox({ courseId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await askQuestion(courseId, question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Request failed.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "⚠ An error occurred. Please check that Ollama is running and try again.",
          sources: [],
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "calc(100vh - 200px)",
        minHeight: 400,
      }}
    >
      {/* Message list */}
      <div
        id="chat-messages"
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
          paddingBottom: "1rem",
        }}
      >
        {messages.length === 0 && (
          <p
            style={{
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: "0.875rem",
              marginTop: "4rem",
            }}
          >
            Ask a question about your course material to get started.
          </p>
        )}

        {messages.map((msg, i) => (
          <div key={i}>
            {msg.role === "user" ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-end",
                }}
              >
                <div
                  id={`msg-user-${i}`}
                  style={{
                    background: "var(--accent)",
                    color: "#fff",
                    borderRadius: "12px 12px 2px 12px",
                    padding: "12px 16px",
                    maxWidth: "75%",
                    fontSize: "0.9rem",
                    lineHeight: 1.5,
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div
                  id={`msg-assistant-${i}`}
                  style={{
                    background: "var(--surface)",
                    border: "1px solid var(--border)",
                    borderRadius: "12px 12px 12px 2px",
                    padding: "16px",
                    maxWidth: "85%",
                    fontSize: "0.9rem",
                    lineHeight: 1.6,
                    color: "var(--text)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {msg.content}
                </div>
                {msg.sources && msg.sources.length > 0 && (
                  <div style={{ maxWidth: "85%" }}>
                    <SourceList sources={msg.sources} />
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div
            id="chat-loading"
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: "12px 12px 12px 2px",
              padding: "16px",
              width: "fit-content",
              fontSize: "0.875rem",
              color: "var(--text-muted)",
            }}
          >
            <span style={{ animation: "pulse 1.5s ease-in-out infinite" }}>
              Thinking…
            </span>
          </div>
        )}
      </div>

      {/* Error bar */}
      {error && (
        <p
          style={{
            color: "var(--error)",
            fontSize: "0.8rem",
            margin: "0 0 8px",
          }}
        >
          ⚠ {error}
        </p>
      )}

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", gap: "10px", marginTop: "auto" }}
      >
        <textarea
          id="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e as unknown as React.FormEvent);
            }
          }}
          placeholder="Ask about your course material… (Enter to send)"
          rows={2}
          disabled={loading}
          style={{
            flex: 1,
            resize: "none",
            fontSize: "0.9rem",
          }}
        />
        <button
          id="send-question-btn"
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            alignSelf: "flex-end",
            background: loading || !input.trim() ? "var(--surface-2)" : "var(--accent)",
            color: loading || !input.trim() ? "var(--text-muted)" : "#fff",
            border: "none",
            borderRadius: 8,
            padding: "10px 20px",
            fontSize: "0.875rem",
            fontWeight: 600,
            transition: "background 0.2s",
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
