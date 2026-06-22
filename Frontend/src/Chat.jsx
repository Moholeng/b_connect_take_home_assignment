import { useState, useRef, useEffect } from "react";
import { sendChatMessage } from "./api";

const STORAGE_KEY = "bconnect_chat_history";

// Read saved history from localStorage once, before the first render.
// Wrapped in try/catch so corrupt/blocked storage can't crash the app.
function loadStoredMessages() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export default function Chat() {
  // Lazy initializer: the function runs only on the first render.
  const [messages, setMessages] = useState(loadStoredMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  // Persist to localStorage whenever the message list changes.
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch {
      /* storage full or unavailable — non-fatal, just skip persisting */
    }
  }, [messages]);

  // Keep the latest message in view.
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setLoading(true);
    try {
      const data = await sendChatMessage(text);
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "error", content: err.message || "Something went wrong." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Clear both the UI and the persisted history.
  function clearHistory() {
    setMessages([]);
  }

  return (
    <section className="flex flex-col rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-700">
          Ask the Network Assistant
        </h2>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            Clear
          </button>
        )}
      </div>

      {/* Message history */}
      <div className="h-80 space-y-3 overflow-y-auto px-4 py-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400">
            Try “Which venue has the most active sessions?” or “What's the age
            and gender breakdown?”
          </p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span
              className={`inline-block max-w-[85%] whitespace-pre-line rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-blue-600 text-white"
                  : m.role === "error"
                  ? "border border-red-200 bg-red-50 text-red-700"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {m.content}
            </span>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="text-left">
            <span className="inline-block rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-500">
              typing…
            </span>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-gray-100 p-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about venues or sessions…"
          disabled={loading}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </section>
  );
}