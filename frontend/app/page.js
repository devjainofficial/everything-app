"use client"; // this component runs in the browser (it uses state + fetch streaming)

import { useState } from "react";

// The backend's STREAMING endpoint. The browser talks to FastAPI, which talks to the
// gateway. The browser never touches the gateway or a model directly.
const BACKEND_STREAM_URL = "http://localhost:8000/chat/stream";

export default function Home() {
  const [input, setInput] = useState("");   // what the user is typing
  const [answer, setAnswer] = useState("");  // the streamed-in answer
  const [busy, setBusy] = useState(false);   // true while a request is streaming

  async function send() {
    if (!input.trim() || busy) return;
    setBusy(true);
    setAnswer("");

    // 1. POST the question to the backend's streaming endpoint.
    const res = await fetch(BACKEND_STREAM_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input }),
    });

    // 2. Get a READER over the response body's raw byte stream, plus a decoder
    //    to turn bytes into text. `buffer` holds bytes we've received but not yet
    //    split into complete lines.
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    // 3. Loop: pull chunks as they arrive and process any COMPLETE lines.
    while (true) {
      const { value, done } = await reader.read();
      if (done) break; // server closed the stream
      buffer += decoder.decode(value, { stream: true });

      // SSE lines are newline-separated. Split, but keep the last (maybe partial)
      // piece in the buffer for the next read.
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trimStart(); // drop "data:" + the leading space
        if (payload === "[DONE]") continue;         // end-of-stream sentinel
        // payload is JSON (e.g. "Red" or "\n"); parse to recover the exact token.
        const token = JSON.parse(payload);
        setAnswer((prev) => prev + token);          // append -> UI updates live
      }
    }

    setBusy(false);
  }

  return (
    <main className="mx-auto max-w-2xl p-8 font-sans">
      <h1 className="text-2xl font-bold">Everything App</h1>
      <p className="mb-6 text-sm text-gray-500">
        Module 0 — browser → FastAPI → LiteLLM gateway → model
      </p>

      <div className="mb-4 flex gap-2">
        <input
          className="flex-1 rounded-lg border px-3 py-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Ask something..."
        />
        <button
          className="rounded-lg bg-black px-4 py-2 text-white disabled:opacity-40"
          onClick={send}
          disabled={busy}
        >
          {busy ? "…" : "Send"}
        </button>
      </div>

      <div className="min-h-32 whitespace-pre-wrap rounded-lg border bg-gray-50 p-4">
        {answer || <span className="text-gray-400">The answer will stream in here.</span>}
      </div>
    </main>
  );
}
