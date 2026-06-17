"use client"; // runs in the browser (uses state + fetch)

import { useState } from "react";

// The backend's RAG endpoint: retrieve relevant chunks -> grounded, cited answer.
const BACKEND_ASK_URL = "http://localhost:8000/ask";

export default function Home() {
  const [input, setInput] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [busy, setBusy] = useState(false);

  async function ask() {
    if (!input.trim() || busy) return;
    setBusy(true);
    setAnswer("");
    setSources([]);
    try {
      const res = await fetch(BACKEND_ASK_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }), // backend reads {message}
      });
      const data = await res.json(); // { answer, sources }
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (e) {
      setAnswer("Error: " + e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-8 font-sans">
      <h1 className="text-2xl font-bold">Everything App</h1>
      <p className="mb-6 text-sm text-gray-500">
        Module 1 — ask your documents (RAG: retrieve → grounded answer with citations)
      </p>

      <div className="mb-4 flex gap-2">
        <input
          className="flex-1 rounded-lg border px-3 py-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && ask()}
          placeholder="Ask something about your documents..."
        />
        <button
          className="rounded-lg bg-black px-4 py-2 text-white disabled:opacity-40"
          onClick={ask}
          disabled={busy}
        >
          {busy ? "…" : "Ask"}
        </button>
      </div>

      <div className="min-h-32 whitespace-pre-wrap rounded-lg border bg-gray-50 p-4">
        {busy ? (
          <span className="text-gray-400">Retrieving and answering…</span>
        ) : answer ? (
          answer
        ) : (
          <span className="text-gray-400">The cited answer will appear here.</span>
        )}
      </div>

      {sources.length > 0 && (
        <div className="mt-4 text-sm">
          <div className="mb-1 font-semibold text-gray-700">Sources</div>
          <ul className="space-y-1">
            {sources.map((s) => (
              <li key={s.n} className="text-gray-600">
                [{s.n}] {s.title}{" "}
                <span className="text-gray-400">(score {s.score})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}
