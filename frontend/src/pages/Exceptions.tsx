import { useEffect, useState } from "react";

const BASE = "/api-proxy";

interface ExceptionRow {
  id: string;
  exception_type: string;
  severity: string;
  status: string;
  related_entity_type: string;
  related_record_ids: string[];
  group_id: string | null;
  title: string;
  description: string;
  system_suggestion: string | null;
  evidence: Record<string, unknown> | null;
  resolution_decision: string | null;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

const STATUSES = ["new", "in_review", "resolved", "rejected", "escalated"];

export default function Exceptions() {
  const [exceptions, setExceptions] = useState<ExceptionRow[]>([]);
  const [filterStatus, setFilterStatus] = useState("new");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ExceptionRow | null>(null);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const q = new URLSearchParams();
    if (filterStatus) q.set("status", filterStatus);
    if (filterSeverity) q.set("severity", filterSeverity);
    const res = await fetch(`${BASE}/exceptions?${q.toString()}`);
    if (!res.ok) {
      // Backend doesn't have this endpoint yet — degrade gracefully
      setExceptions([]);
      return;
    }
    const data = await res.json();
    setExceptions(Array.isArray(data) ? data : data.exceptions || []);
  }

  async function openException(id: string) {
    setSelectedId(id);
    const res = await fetch(`${BASE}/exceptions/${id}`);
    if (res.ok) {
      setDetail(await res.json());
      setNotes("");
    }
  }

  async function updateStatus(newStatus: string) {
    if (!detail) return;
    setBusy(true);
    try {
      await fetch(`${BASE}/exceptions/${detail.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: newStatus,
          resolution_notes: notes || `Status changed to ${newStatus}`,
        }),
      });
      setDetail(null);
      setSelectedId(null);
      await load();
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus, filterSeverity]);

  const severityColors: Record<string, string> = {
    Critical: "bg-red-100 text-red-700",
    High: "bg-orange-100 text-orange-700",
    Medium: "bg-amber-100 text-amber-700",
    Low: "bg-slate-100 text-slate-700",
  };

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Human review</span>
          <h1 className="page-title">Exceptions</h1>
          <p className="page-subtitle">
            Cases requiring human judgment. Every decision is audited.
          </p>
        </div>
      </header>

      {/* Filters */}
      <div className="flex gap-2">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="">All severities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* List */}
        <div className="col-span-5 detail-panel">
          <div className="panel-header">
            <span>Queue ({exceptions.length})</span>
          </div>
          <div className="max-h-[65vh] overflow-y-auto">
            {exceptions.map((e) => (
              <button
                key={e.id}
                onClick={() => openException(e.id)}
                className={`w-full text-left p-3 border-b hover:bg-slate-50 ${
                  selectedId === e.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      severityColors[e.severity] || "bg-slate-100"
                    }`}
                  >
                    {e.severity}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {e.exception_type}
                  </span>
                </div>
                <div className="text-sm font-medium text-slate-800 truncate">
                  {e.title}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {new Date(e.created_at).toLocaleString()}
                </div>
              </button>
            ))}
            {exceptions.length === 0 && (
              <div className="p-4 text-sm text-slate-500">
                No exceptions match this filter.
              </div>
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="col-span-7 detail-panel">
          <div className="panel-header">
            <span>Detail</span>
          </div>
          {!detail && (
            <div className="p-6 text-sm text-slate-500">
              Select an exception from the left to review.
            </div>
          )}
          {detail && (
            <div className="p-4 space-y-4 text-sm">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      severityColors[detail.severity] || "bg-slate-100"
                    }`}
                  >
                    {detail.severity}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {detail.exception_type}
                  </span>
                  <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded-full">
                    {detail.status}
                  </span>
                </div>
                <h2 className="text-lg font-semibold">{detail.title}</h2>
                <p className="text-slate-600 mt-1">{detail.description}</p>
              </div>

              {detail.system_suggestion && (
                <div className="bg-blue-50 border border-blue-200 rounded p-3 text-xs">
                  <div className="font-medium text-blue-800 mb-1">
                    System suggestion
                  </div>
                  <div className="text-blue-800">{detail.system_suggestion}</div>
                </div>
              )}

              {detail.evidence && (
                <div>
                  <div className="text-xs font-medium text-slate-600 mb-1">
                    EVIDENCE
                  </div>
                  <pre className="text-[11px] bg-slate-50 p-2 rounded overflow-x-auto">
                    {JSON.stringify(detail.evidence, null, 2)}
                  </pre>
                </div>
              )}

              <div>
                <label className="block text-xs text-slate-600 mb-1">
                  Resolution notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full border rounded px-2 py-1 text-sm"
                  placeholder="Optional context for the audit log…"
                />
              </div>

              {detail.status === "new" || detail.status === "in_review" ? (
                <div className="flex flex-wrap gap-2 pt-2 border-t">
                  <button
                    onClick={() => updateStatus("resolved")}
                    disabled={busy}
                    className="px-4 py-2 bg-emerald-600 text-white rounded text-sm hover:bg-emerald-700"
                  >
                    Resolve
                  </button>
                  <button
                    onClick={() => updateStatus("rejected")}
                    disabled={busy}
                    className="px-4 py-2 bg-slate-200 rounded text-sm hover:bg-slate-300"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => updateStatus("escalated")}
                    disabled={busy}
                    className="px-4 py-2 bg-amber-100 text-amber-800 rounded text-sm hover:bg-amber-200"
                  >
                    Escalate
                  </button>
                  {detail.status === "new" && (
                    <button
                      onClick={() => updateStatus("in_review")}
                      disabled={busy}
                      className="px-4 py-2 bg-slate-100 rounded text-sm hover:bg-slate-200"
                    >
                      Mark in review
                    </button>
                  )}
                </div>
              ) : (
                <div className="pt-2 border-t text-xs text-slate-500">
                  Resolved at {detail.resolved_at
                    ? new Date(detail.resolved_at).toLocaleString()
                    : "—"}
                  {detail.resolution_notes && (
                    <div className="mt-1 italic">{detail.resolution_notes}</div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}