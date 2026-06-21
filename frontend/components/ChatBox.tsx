"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { askQuestionStream, type Source } from "@/lib/api";
import SourceList from "./SourceList";

interface Props {
  courseId: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export default function ChatBox({ courseId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const question = input.trim();
      if (!question || loading) return;

      // Add user message
      setMessages((prev) => [...prev, { role: "user", content: question }]);
      setInput("");
      setLoading(true);
      setError(null);

      // Add a placeholder assistant message that will be streamed into
      const assistantIdx = messages.length + 1; // index after adding user msg

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "", sources: [], isStreaming: true },
      ]);

      abortRef.current = askQuestionStream(courseId, question, {
        onSources(sources) {
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[assistantIdx];
            if (msg) {
              updated[assistantIdx] = { ...msg, sources };
            }
            return updated;
          });
        },

        onToken(token) {
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[assistantIdx];
            if (msg) {
              updated[assistantIdx] = {
                ...msg,
                content: msg.content + token,
              };
            }
            return updated;
          });
        },

        onDone() {
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[assistantIdx];
            if (msg) {
              updated[assistantIdx] = { ...msg, isStreaming: false };
            }
            return updated;
          });
          setLoading(false);
          abortRef.current = null;
        },

        onError(errorMsg) {
          setError(errorMsg);
          setMessages((prev) => {
            const updated = [...prev];
            const msg = updated[assistantIdx];
            if (msg) {
              updated[assistantIdx] = {
                ...msg,
                content:
                  msg.content ||
                  "⚠ An error occurred. Please check that Ollama is running and try again.",
                isStreaming: false,
              };
            }
            return updated;
          });
          setLoading(false);
          abortRef.current = null;
        },
      });
    },
    [courseId, input, loading, messages.length]
  );

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last?.isStreaming) {
        updated[updated.length - 1] = { ...last, isStreaming: false };
      }
      return updated;
    });
    setLoading(false);
    abortRef.current = null;
  }, []);

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
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
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
                    minHeight: msg.isStreaming && !msg.content ? 40 : undefined,
                  }}
                >
                  {msg.content}
                  {msg.isStreaming && (
                    <span
                      style={{
                        display: "inline-block",
                        width: 6,
                        height: "1em",
                        background: "var(--accent)",
                        borderRadius: 2,
                        marginLeft: 2,
                        verticalAlign: "text-bottom",
                        animation: "blink 1s step-end infinite",
                      }}
                    />
                  )}
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

        <div ref={messagesEndRef} />
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
        {loading ? (
          <button
            id="cancel-btn"
            type="button"
            onClick={handleCancel}
            style={{
              alignSelf: "flex-end",
              background: "var(--error)",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "10px 20px",
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: "pointer",
              transition: "background 0.2s",
            }}
          >
            Stop
          </button>
        ) : (
          <button
            id="send-question-btn"
            type="submit"
            disabled={!input.trim()}
            style={{
              alignSelf: "flex-end",
              background: !input.trim()
                ? "var(--surface-2)"
                : "var(--accent)",
              color: !input.trim() ? "var(--text-muted)" : "#fff",
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
        )}
      </form>

      {/* Blinking cursor animation */}
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
