"use client";

import { useState, useRef, useCallback } from "react";

type UploadStatus = "idle" | "loading" | "done" | "error";

const MAX_FILE_SIZE = 5 * 1024 * 1024;

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [answerKey, setAnswerKey] = useState(0);
  const [queryLoading, setQueryLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const selectFile = useCallback((f: File) => {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      setUploadStatus("error");
      setUploadMessage("Only PDF files are accepted");
      setFile(null);
      return;
    }
    if (f.size > MAX_FILE_SIZE) {
      setUploadStatus("error");
      setUploadMessage("File exceeds 5 MB — please choose a smaller PDF");
      setFile(null);
      return;
    }
    setFile(f);
    setUploadStatus("idle");
    setUploadMessage("");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) selectFile(f);
    },
    [selectFile]
  );

  const handleUpload = () => {
    if (!file || uploadStatus === "loading") return;
    setUploadStatus("loading");
    setUploadProgress(0);

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        setUploadProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          setUploadStatus("done");
          setUploadMessage(`"${file.name}" ready to query`);
        } else {
          setUploadStatus("error");
          setUploadMessage(data.detail ?? "Upload failed");
        }
      } catch {
        setUploadStatus("error");
        setUploadMessage("Upload failed");
      }
    };

    xhr.onerror = () => {
      setUploadStatus("error");
      setUploadMessage("Connection error — is the server running?");
    };

    xhr.open("POST", "/ingest");
    xhr.send(formData);
  };

  const handleQuery = async () => {
    if (!question.trim() || queryLoading) return;
    setQueryLoading(true);
    setAnswer("");
    try {
      const res = await fetch("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setAnswer(res.ok ? data.answer : `Error: ${data.detail ?? "Query failed"}`);
      setAnswerKey((k) => k + 1);
    } catch {
      setAnswer("Connection error — is the server running?");
      setAnswerKey((k) => k + 1);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleQuery();
  };

  const statusColor = (s: UploadStatus) => {
    if (s === "error") return "var(--c-error)";
    if (s === "done") return "var(--c-success)";
    return "var(--c-muted)";
  };

  return (
    <main
      className="relative min-h-screen px-6 py-20"
      style={{ zIndex: 1 }}
    >
      <div className="mx-auto max-w-2xl flex flex-col gap-12">

        {/* Header */}
        <header className="fade-up" style={{ animationDelay: "0ms" }}>
          <h1
            className="text-5xl font-medium tracking-tight mb-3"
            style={{
              fontFamily: "var(--font-playfair), Georgia, serif",
              color: "var(--c-text)",
            }}
          >
            RAG Archive
          </h1>
          <p
            className="text-xs uppercase"
            style={{ color: "var(--c-muted)", letterSpacing: "0.18em" }}
          >
            Upload documents · Ask anything
          </p>
        </header>

        {/* Upload */}
        <section className="fade-up" style={{ animationDelay: "100ms" }}>
          <p
            className="text-xs uppercase mb-3"
            style={{ color: "var(--c-muted)", letterSpacing: "0.15em" }}
          >
            Document
          </p>

          {/* Drop zone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragEnter={() => setDragOver(true)}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className="rounded-xl p-10 text-center cursor-pointer transition-all duration-300"
            style={{
              border: `1.5px dashed ${dragOver ? "var(--c-accent)" : uploadStatus === "error" ? "var(--c-error)" : "var(--c-border)"}`,
              backgroundColor: dragOver ? "var(--c-accent-dim)" : uploadStatus === "error" ? "rgba(196,96,96,0.06)" : "var(--c-surface)",
              boxShadow: dragOver ? "0 0 32px rgba(201,168,108,0.12)" : "none",
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) selectFile(f);
              }}
            />

            {/* Icon */}
            <div
              className="mx-auto mb-4 flex items-center justify-center rounded-full"
              style={{
                width: 44,
                height: 44,
                backgroundColor: "var(--c-accent-dim)",
                color: "var(--c-accent)",
              }}
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 16V4m0 0L8 8m4-4l4 4" />
                <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
              </svg>
            </div>

            {file ? (
              <p
                className="text-sm"
                style={{
                  fontFamily: "var(--font-jetbrains), monospace",
                  color: "var(--c-accent)",
                }}
              >
                {file.name}
              </p>
            ) : (
              <p className="text-sm" style={{ color: "var(--c-muted)" }}>
                Drag a PDF here, or{" "}
                <span style={{ color: "var(--c-accent)" }}>click to browse</span>
              </p>
            )}
          </div>

          {/* Hint — always visible */}
          <p
            className="mt-1.5 text-center text-xs"
            style={{ color: "var(--c-muted)" }}
          >
            PDF only · max 5 MB
          </p>

          {uploadMessage && (
            <p
              className="mt-2 text-xs"
              style={{ color: statusColor(uploadStatus) }}
            >
              {uploadMessage}
            </p>
          )}

          {/* Progress bar — visible only while uploading */}
          {uploadStatus === "loading" && (
            <div className="mt-3 flex items-center gap-2">
              <div
                className="flex-1 rounded-full"
                style={{ height: 4, backgroundColor: "var(--c-accent-dim)" }}
              >
                <div
                  className="rounded-full transition-all duration-200"
                  style={{
                    height: 4,
                    width: `${uploadProgress}%`,
                    backgroundColor: "var(--c-accent)",
                  }}
                />
              </div>
              <span
                className="text-xs"
                style={{ color: "var(--c-muted)", minWidth: 28 }}
              >
                {uploadProgress}%
              </span>
            </div>
          )}

          {file && uploadStatus !== "done" && (
            <button
              onClick={handleUpload}
              disabled={uploadStatus === "loading"}
              className="mt-4 px-5 py-2 text-sm rounded-lg border transition-all duration-200"
              style={{
                borderColor: "var(--c-accent)",
                color: uploadStatus === "loading" ? "var(--c-muted)" : "var(--c-accent)",
                backgroundColor: "transparent",
                cursor: uploadStatus === "loading" ? "not-allowed" : "pointer",
                letterSpacing: "0.02em",
              }}
            >
              {uploadStatus === "loading" ? "Ingesting…" : "Ingest document"}
            </button>
          )}
        </section>

        {/* Divider */}
        <div
          className="fade-up h-px"
          style={{
            background:
              "linear-gradient(to right, transparent, var(--c-accent), transparent)",
            opacity: 0.35,
            animationDelay: "180ms",
          }}
        />

        {/* Query */}
        <section className="fade-up" style={{ animationDelay: "240ms" }}>
          <p
            className="text-xs uppercase mb-3"
            style={{ color: "var(--c-muted)", letterSpacing: "0.15em" }}
          >
            Query
          </p>

          <div
            className="rounded-xl p-4 transition-colors duration-200"
            style={{
              backgroundColor: "var(--c-surface)",
              border: "1px solid var(--c-border)",
            }}
          >
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents…"
              rows={3}
              className="w-full resize-none text-sm bg-transparent outline-none leading-relaxed"
              style={{ color: "var(--c-text)", fontFamily: "inherit" }}
            />
            <div
              className="flex items-center justify-between mt-3 pt-3"
              style={{ borderTop: "1px solid var(--c-border)" }}
            >
              <span className="text-xs" style={{ color: "var(--c-muted)" }}>
                ⌘ ↵ to send
              </span>
              <button
                onClick={handleQuery}
                disabled={queryLoading || !question.trim()}
                className="px-4 py-1.5 text-xs rounded-md border transition-all duration-200"
                style={{
                  borderColor:
                    question.trim() && !queryLoading
                      ? "var(--c-accent)"
                      : "var(--c-border)",
                  color:
                    question.trim() && !queryLoading
                      ? "var(--c-accent)"
                      : "var(--c-muted)",
                  backgroundColor: "transparent",
                  cursor:
                    question.trim() && !queryLoading ? "pointer" : "not-allowed",
                  letterSpacing: "0.04em",
                }}
              >
                {queryLoading ? "Searching…" : "Ask"}
              </button>
            </div>
          </div>

          {/* Answer */}
          {answer && (
            <div key={answerKey} className="mt-6 fade-up">
              <p
                className="text-xs uppercase mb-3"
                style={{ color: "var(--c-muted)", letterSpacing: "0.15em" }}
              >
                Response
              </p>
              <div
                className="rounded-xl p-5"
                style={{
                  backgroundColor: "var(--c-surface)",
                  border: "1px solid var(--c-border)",
                }}
              >
                <p
                  className="text-sm leading-relaxed whitespace-pre-wrap"
                  style={{
                    color: "var(--c-text)",
                    fontFamily: "var(--font-jetbrains), monospace",
                  }}
                >
                  {answer}
                </p>
              </div>
            </div>
          )}
        </section>

      </div>
    </main>
  );
}
