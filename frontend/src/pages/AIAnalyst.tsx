import { useState } from "react";
import { api } from "../lib/api";
import type { AIResponse } from "../lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  meta?: AIResponse;
}

const SUGGESTIONS = [
  "how many customers?",
  "how many active customers?",
  "top 5 cities",
  "how many from ERP?",
  "average transaction amount",
  "total transaction amount",
  "how many transactions?",
  "what is the meaning of life?",
];

export default function AIAnalyst() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send(question: string) {
    if (!question.trim()) return;
    const userMsg: Message = { role: "user", content: question };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);
    try {
      const res: AIResponse = await api.ask(question);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, meta: res }]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Error: ${e.message}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page-shell h-full flex flex-col">
      <header className="page-header">
        <div>
          <span className="eyebrow">AI assistance</span>
          <h1 className="page-title">AI Analyst</h1>
          <p className="page-subtitle">
            Grounded answers, using only trusted data. Refuses when the answer cannot be grounded.
          </p>
        </div>
      </header>

      <div className="detail-panel flex-1 flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-sm text-slate-500">
              <p className="mb-3">Try one of these questions:</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="px-3 py-1 text-xs bg-slate-100 hover:bg-slate-200 rounded-full"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-2xl rounded-lg px-4 py-2 text-sm ${
                  m.role === "user"
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                <div>{m.content}</div>
                {m.meta && (
                  <div className="mt-2 pt-2 border-t border-slate-200 text-[11px] text-slate-500 space-y-0.5">
                    <div>
                      <span className="font-mono">rule:</span> {m.meta.matched_rule}
                    </div>
                    {m.meta.matched_rule.startsWith("refuse") ? (
                      <div className="text-amber-600 font-medium">
                        ⚠️ Refused — no grounded answer available
                      </div>
                    ) : (
                      <div>
                        <span className="font-mono">grounded:</span>{" "}
                        {m.meta.grounded ? "yes" : "no"} · {m.meta.latency_ms}ms
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {busy && (
            <div className="text-sm text-slate-500">Thinking…</div>
          )}
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
          className="border-t p-3 flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about trusted data…"
            className="flex-1 border rounded px-3 py-2 text-sm"
            disabled={busy}
          />
          <button
            type="submit"
            disabled={busy || !input.trim()}
            className="px-4 py-2 bg-slate-900 text-white rounded text-sm hover:bg-slate-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}