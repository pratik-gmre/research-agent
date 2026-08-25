import React, { useEffect, useState, useCallback } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import { askQuestion, fetchStatus } from "./api.js";

export default function App() {
  const [status, setStatus] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refreshStatus = useCallback(async () => {
    try {
      const s = await fetchStatus();
      setStatus(s);
    } catch {
      setStatus({ indexed_chunks: 0, indexed_files: [] });
    }
  }, []);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  async function handleSend() {
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const result = await askQuestion(question);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, sources: result.sources },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="app-shell">
      <Sidebar status={status} onStatusRefresh={refreshStatus} />

      <div className="chat-column">
        <div className="chat-header">
          <h1>IOE Entrance Exam Q&amp;A</h1>
          <p>Grounded answers with page-level citations from your indexed papers.</p>
        </div>

        <ChatWindow messages={messages} loading={loading} />

        <div className="composer">
          {error && <div className="error-banner">{error}</div>}
          <div className="composer-inner">
            <textarea
              placeholder="Ask a question about your syllabus or a past paper…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button className="send-btn" onClick={handleSend} disabled={loading || !input.trim()}>
              {loading ? "…" : "Ask"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
