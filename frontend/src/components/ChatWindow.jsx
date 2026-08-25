import React, { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble.jsx";

export default function ChatWindow({ messages, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (!messages.length) {
    return (
      <div className="chat-scroll">
        <div className="empty-state">
          <div className="mark">प्रश्न सोध्नुहोस्</div>
          <p>
            Ask a question about your entrance exam material — in Nepali,
            English, or mixed. Answers are grounded only in your uploaded
            PDFs, with page citations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-scroll">
      {messages.map((m, i) => (
        <MessageBubble key={i} role={m.role} text={m.text} sources={m.sources} />
      ))}
      {loading && <div className="typing">retrieving and generating…</div>}
      <div ref={bottomRef} />
    </div>
  );
}
