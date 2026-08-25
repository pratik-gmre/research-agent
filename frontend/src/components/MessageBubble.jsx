import React from "react";
import SourcesList from "./SourcesList.jsx";

export default function MessageBubble({ role, text, sources }) {
  return (
    <div className={`message ${role}`}>
      <span className="role-tag">{role === "user" ? "You" : "Assistant"}</span>
      <div className="bubble" lang={role === "assistant" ? undefined : undefined}>
        {text}
      </div>
      {role === "assistant" && <SourcesList sources={sources} />}
    </div>
  );
}
