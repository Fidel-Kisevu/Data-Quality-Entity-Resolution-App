import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { AuditEvent, AuditSummary } from "../lib/types";

export default function AuditTrail() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [filterType, setFilterType] = useState("");
  const [filterActor, setFilterActor] = useState("");
  const [recordId, setRecordId] = useState("");
  const [recordEvents, setRecordEvents] = useState<AuditEvent[] | null>(null);

  async function load() {
    const [list, sum] = await Promise.all([
      api.listAudit({
        event_type: filterType || undefined,
        actor: filterActor || undefined,
        limit: 200,
      }),
      api.auditSummary(),
    ]);
    setEvents(list.events);
    setSummary(sum);
  }

  async function lookupRecord() {
    if (!recordId.trim()) return;
    const res = await api.auditForRecord(recordId.trim());
    setRecordEvents(res.events);
  }

  useEffect(() => { load(); }, [filterType, filterActor]);

  const eventColors: Record<string, string> = {
    "source.uploaded": "bg-blue-100 text-blue-700",
    "source.ingested": "bg-blue-100 text-blue-700",
    "quality.run": "bg-amber-100 text-amber-700",
    "matching.run": "bg-purple-100 text-purple-700",
    "matching.resolve_all": "bg-emerald-100 text-emerald-700",
    "matching.resolve": "bg-emerald-100 text-emerald-700",
    "ai.query": "bg-pink-100 text-pink-700",
    "transactions.linked": "bg-cyan-100 text-cyan-700",
  };

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Compliance</span>
          <h1 className="page-title">Audit Trail</h1>
          <p className="page-subtitle">
            Immutable history of every state change.
          </p>
        </div>
      </header>

      {summary && (
        <div className="grid grid-cols-4 gap-3">
          <div className="metric-card">
            <span className="metric-label">Total events</span>
            <strong className="metric-value">{summary.total_events}</strong>
          </div>
          {Object.entries(summary.by_event_type).slice(0, 3).map(([k, v]) => (
            <div key={k} className="metric-card">
              <span className="metric-label truncate">{k}</span>
              <strong className="metric-value">{v}</strong>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 items-center">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="">All event types</option>
          {summary &&
            Object.keys(summary.by_event_type).map((k) => (
              <option key={k} value={k}>
                {k}
              </option>
            ))}
        </select>
        <select
          value={filterActor}
          onChange={(e) => setFilterActor(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="">All actors</option>
          <option value="system">system</option>
          <option value="user">user</option>
        </select>
        <div className="ml-auto flex gap-2">
          <input
            value={recordId}
            onChange={(e) => setRecordId(e.target.value)}
            placeholder="Lookup record by ID…"
            className="border rounded px-3 py-1 text-sm w-64"
          />
          <button
            onClick={lookupRecord}
            className="px-3 py-1 bg-slate-900 text-white rounded text-sm hover:bg-slate-700"
          >
            Lookup
          </button>
          {recordEvents && (
            <button
              onClick={() => { setRecordEvents(null); setRecordId(""); }}
              className="px-3 py-1 bg-slate-200 rounded text-sm"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="detail-panel">
        <div className="panel-header">
          <span>{recordEvents ? `Record history (${recordEvents.length} events)` : `Timeline (${events.length} events)`}</span>
        </div>
        <div className="max-h-[60vh] overflow-y-auto">
          {(recordEvents || events).map((e) => (
            <div key={e.id} className="p-3 border-b hover:bg-slate-50">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                    eventColors[e.event_type] || "bg-slate-100 text-slate-700"
                  }`}
                >
                  {e.event_type}
                </span>
                <span className="text-xs text-slate-500 font-mono">{e.actor}</span>
                <span className="text-xs text-slate-400 ml-auto">
                  {new Date(e.created_at).toLocaleString()}
                </span>
              </div>
              <div className="text-sm text-slate-800">{e.notes || e.action}</div>
              {e.after_state && (
                <details className="mt-1">
                  <summary className="text-xs text-slate-500 cursor-pointer">
                    after_state
                  </summary>
                  <pre className="text-[11px] bg-slate-50 p-2 mt-1 rounded overflow-x-auto">
                    {JSON.stringify(e.after_state, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}