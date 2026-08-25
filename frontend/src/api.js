const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function fetchStatus() {
  return handle(await fetch(`${BASE_URL}/status`));
}

export async function askQuestion(question) {
  return handle(
    await fetch(`${BASE_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    })
  );
}

export async function uploadPdf(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  return handle(
    await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    })
  );
}
