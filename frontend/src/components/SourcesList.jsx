import React from "react";

export default function SourcesList({ sources }) {
  if (!sources?.length) return null;

  return (
    <div className="sources">
      {sources.map((s) => (
        <span className="source-chip" key={s.index} title={s.excerpt}>
          <span className="idx">[{s.index}]</span>
          {s.source_file} · p.{s.page_number}
          {s.method === "ocr" && <span className="flag">OCR</span>}
        </span>
      ))}
    </div>
  );
}
