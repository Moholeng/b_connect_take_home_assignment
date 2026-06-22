// Base URL for the FastAPI backend. Vite exposes env vars prefixed with VITE_.
// Falls back to localhost:8000 so it works out of the box in dev.
const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Small wrapper around fetch that throws on non-2xx responses and parses JSON.
// Centralising this means every call gets consistent error handling.
async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    // Try to surface FastAPI's {"detail": "..."} message; fall back to status.
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* response had no JSON body — keep the status text */
    }
    throw new Error(detail);
  }

  return res.json();
}

// GET /sync-status -> latest SyncLog object, or null if no sync has ever run.
export function getSyncStatus() {
  return request("/sync-status");
}

// GET /venues -> array of venues, each with a nested access_points array.
export function getVenues() {
  return request("/venues");
}

// GET /sessions -> paginated wrapper: { total, limit, offset, items: [...] }.
// We return .items so callers get a plain array of sessions.
export async function getSessions({ limit = 50 } = {}) {
  const page = await request(`/sessions?limit=${limit}`);
  return page.items;
}

// POST /sync -> triggers the ingestion pipeline, returns the new SyncLog record.
export function triggerSync() {
  return request("/sync", { method: "POST" });
}

// GET /insights -> { insights: string, model: string }
export function getInsights() {
  return request("/insights");
}

// POST /chat -> { reply: string }
export function sendChatMessage(message) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}