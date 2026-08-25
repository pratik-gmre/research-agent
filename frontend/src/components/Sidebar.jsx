import React, { useRef, useState } from "react";
import { uploadPdf } from "../api.js";

export default function Sidebar({ status, onStatusRefresh }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  async function handleFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      await uploadPdf(file);
      await onStatusRefresh();
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-eyebrow">IOE Entrance Prep</span>
        <span className="brand-title">Research Assistant</span>
      </div>

      <div className="sidebar-section">
        <h3>Add exam PDF</h3>
        <label className="upload-box" htmlFor="pdf-upload">
          <input
            id="pdf-upload"
            ref={inputRef}
            type="file"
            accept="application/pdf"
            onChange={handleFile}
            disabled={uploading}
          />
          <div className="upload-label">
            {uploading ? "Indexing… this can take a minute" : "Click to upload a PDF"}
          </div>
        </label>
        {uploadError && (
          <div className="status-line" style={{ color: "#e88", marginTop: 8 }}>
            {uploadError}
          </div>
        )}
      </div>

       <div className="sidebar-section">
        <h3>Indexed papers</h3>
        {status?.indexed_files?.length ? (
          <ul className="file-list">
            {status.indexed_files.map((f) => (
              <li key={f}>
                <span className="dot" />
                {f}
              </li>
            ))}
          </ul>
        ) : (
          <div className="status-line">No PDFs indexed yet.</div>
        )}
      </div> 

      <div className="sidebar-section" style={{ marginTop: "auto" }}>
        <div className="status-line">
          {status ? `${status.indexed_chunks} chunks in index` : "connecting…"}
        </div>
      </div>
    </aside>
  );
}
