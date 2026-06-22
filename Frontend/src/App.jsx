import { useEffect, useState, useCallback } from "react";
import Chat from "./Chat";
import {
  getSyncStatus,
  getVenues,
  getSessions,
  triggerSync,
  getInsights,
} from "./api";

// ── Small reusable bits ──────────────────────────────────────────────

// Inline spinner used in the button and loading states.
function Spinner({ className = "h-4 w-4" }) {
  return (
    <svg
      className={`animate-spin ${className}`}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  );
}

// Formats an ISO timestamp into something human-readable; guards against null.
function formatTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

// Colour-coded pill for a status string (success / partial / error / online…).
function StatusPill({ status }) {
  const colors = {
    success: "bg-green-100 text-green-800",
    online: "bg-green-100 text-green-800",
    partial: "bg-yellow-100 text-yellow-800",
    error: "bg-red-100 text-red-800",
    offline: "bg-red-100 text-red-800",
  };
  const cls = colors[status] ?? "bg-gray-100 text-gray-800";
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

// Wraps a dashboard section with a title and consistent card styling.
function Section({ title, children, count }) {
  return (
    <section className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
        {count != null && (
          <span className="text-xs text-gray-400">{count} total</span>
        )}
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  );
}

// ── Main dashboard ───────────────────────────────────────────────────

export default function App() {
  const [syncStatus, setSyncStatus] = useState(null);
  const [venues, setVenues] = useState([]);
  const [sessions, setSessions] = useState([]);

  const [loading, setLoading] = useState(true); // initial page load
  const [syncing, setSyncing] = useState(false); // POST /sync in flight
  const [error, setError] = useState(null); // backend unreachable / failed

  // AI insights state
  const [insights, setInsights] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [insightsError, setInsightsError] = useState(null);

  // Fetches all three datasets in parallel. Reused by the initial mount
  // effect and by the Sync button's post-success refresh.
  const loadAll = useCallback(async () => {
    setError(null);
    try {
      const [status, venueList, sessionList] = await Promise.all([
        getSyncStatus(),
        getVenues(),
        getSessions(),
      ]);
      setSyncStatus(status);
      setVenues(venueList);
      setSessions(sessionList);
    } catch (err) {
      // Most likely the backend is down or CORS is misconfigured.
      setError(err.message || "Could not reach the backend.");
    }
  }, []);

  // GET /insights handler: spinner, fetch, display or error.
  async function generateInsights() {
    setInsightsLoading(true);
    setInsightsError(null);
    try {
      const data = await getInsights();
      setInsights(data.insights);
    } catch (err) {
      setInsightsError(err.message || "Could not generate insights.");
    } finally {
      setInsightsLoading(false);
    }
  }

  // Initial fetch on mount.
  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadAll();
      setLoading(false);
    })();
  }, [loadAll]);

  // Sync button handler: disable + spinner, POST /sync, then re-fetch everything.
  async function handleSync() {
    setSyncing(true);
    setError(null);
    try {
      await triggerSync();
      await loadAll(); // refresh venues, sessions, and status without a reload
    } catch (err) {
      setError(err.message || "Sync failed.");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="mx-auto max-w-6xl px-4 py-6">
        {/* Header */}
        <header className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-bold">b-connect Wi-Fi Dashboard</h1>
          <button
            onClick={handleSync}
            disabled={syncing}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {syncing && <Spinner />}
            {syncing ? "Syncing…" : "Sync Data"}
          </button>
        </header>

        {/* Status banner */}
        <div className="mb-6">
          {error ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : syncStatus ? (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-md border border-gray-200 bg-white px-4 py-3 text-sm">
              <span>
                <span className="text-gray-500">Last Sync:</span>{" "}
                {formatTime(syncStatus.finished_at ?? syncStatus.started_at)}
              </span>
              <span className="flex items-center gap-1">
                <span className="text-gray-500">Status:</span>{" "}
                <StatusPill status={syncStatus.status} />
              </span>
              <span className="text-gray-400">
                {syncStatus.venues_synced ?? 0} venues ·{" "}
                {syncStatus.sessions_synced ?? 0} sessions
              </span>
              {syncStatus.error_message && (
                <span className="text-red-600">{syncStatus.error_message}</span>
              )}
            </div>
          ) : (
            <div className="rounded-md border border-gray-200 bg-white px-4 py-3 text-sm text-gray-500">
              No sync has run yet. Click “Sync Data” to ingest the controller feed.
            </div>
          )}
        </div>

        {/* Loading skeleton for the very first load */}
        {loading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Spinner className="h-5 w-5 text-gray-400" />
            Loading dashboard…
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {/* AI Network Insights */}
            <Section title="AI Network Insights">
              <div className="space-y-3 px-4 py-4">
                <button
                  onClick={generateInsights}
                  disabled={insightsLoading}
                  className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {insightsLoading && <Spinner />}
                  {insightsLoading ? "Analyzing…" : "Generate Insights"}
                </button>

                {insightsError && (
                  <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {insightsError}
                  </div>
                )}

                {insights && !insightsError && (
                  <div className="whitespace-pre-line rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-800">
                    {insights}
                  </div>
                )}
              </div>
            </Section>

            {/* Interactive chat agent */}
            <Chat />

            {/* Venues */}
            <Section title="Venues" count={venues.length}>
              {venues.length === 0 ? (
                <p className="px-4 py-6 text-sm text-gray-500">No venues found.</p>
              ) : (
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Name</th>
                      <th className="px-4 py-2">City</th>
                      <th className="px-4 py-2">Country</th>
                      <th className="px-4 py-2">Access Points</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {venues.map((v) => (
                      <tr key={v.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-medium">{v.name}</td>
                        <td className="px-4 py-2 text-gray-600">{v.city ?? "—"}</td>
                        <td className="px-4 py-2 text-gray-600">{v.country ?? "—"}</td>
                        <td className="px-4 py-2 text-gray-600">
                          {v.access_points?.length ?? 0}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Section>

            {/* Sessions */}
            <Section title="Sessions" count={sessions.length}>
              {sessions.length === 0 ? (
                <p className="px-4 py-6 text-sm text-gray-500">No sessions found.</p>
              ) : (
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Client MAC</th>
                      <th className="px-4 py-2">Device</th>
                      <th className="px-4 py-2">SSID</th>
                      <th className="px-4 py-2">Start</th>
                      <th className="px-4 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {sessions.map((s) => (
                      <tr key={s.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 font-mono text-xs">{s.client_mac}</td>
                        <td className="px-4 py-2 text-gray-600">
                          {s.device_type ?? s.os ?? "—"}
                        </td>
                        <td className="px-4 py-2 text-gray-600">{s.ssid ?? "—"}</td>
                        <td className="px-4 py-2 text-gray-600">
                          {formatTime(s.start_time)}
                        </td>
                        <td className="px-4 py-2">
                          {/* No end_time means the session is still active */}
                          <StatusPill status={s.end_time ? "ended" : "active"} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}