import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { MatchGroupSummary, MatchGroupDetail } from "../lib/types";

export default function Reconciliation() {
  const [groups, setGroups] = useState<MatchGroupSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState("needs_review");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<MatchGroupDetail | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    try {
      const res = await api.listGroups({ status: filter, limit: 100 });
      setGroups(res.groups);
      setTotal(res.total);
    } finally {
      setBusy(false);
    }
  }

  async function openGroup(id: string) {
    setSelectedId(id);
    const d = await api.getGroup(id);
    setDetail(d);
  }

  async function resolve(action: "accept_survivor" | "reject_match") {
    if (!detail) return;
    await api.resolveGroup(detail.id, { action, notes: `Resolved via UI: ${action}` });
    setDetail(null);
    setSelectedId(null);
    await load();
  }

  useEffect(() => { load(); }, [filter]);

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Identity resolution</span>
          <h1 className="page-title">Reconciliation</h1>
          <p className="page-subtitle">
            {total} groups · filter: {filter}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border rounded px-3 py-1 text-sm"
          >
            <option value="needs_review">Needs review</option>
            <option value="resolved">Resolved</option>
            <option value="">All</option>
          </select>
          <button
            onClick={load}
            className="px-3 py-1 bg-slate-900 text-white rounded text-sm hover:bg-slate-700"
            disabled={busy}
          >
            {busy ? "Loading…" : "Refresh"}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-4">
        {/* Left: groups list */}
        <div className="col-span-5 detail-panel">
          <div className="panel-header">
            <span>Candidate groups</span>
          </div>
          <div className="max-h-[70vh] overflow-y-auto">
            {groups.map((g) => (
              <button
                key={g.id}
                onClick={() => openGroup(g.id)}
                className={`w-full text-left px-3 py-2 border-b hover:bg-slate-50 ${
                  selectedId === g.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">
                    {g.record_ids.length} records
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
                    {g.match_type}
                  </span>
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Confidence {g.confidence_score.toFixed(2)} · {g.id.slice(0, 8)}
                </div>
              </button>
            ))}
            {groups.length === 0 && !busy && (
              <div className="p-4 text-sm text-slate-500">No groups found.</div>
            )}
          </div>
        </div>

        {/* Right: detail */}
        <div className="col-span-7 detail-panel">
          <div className="panel-header">
            <span>Side-by-side comparison</span>
          </div>
          {!detail && (
            <div className="p-6 text-sm text-slate-500">
              Select a group from the left to inspect its records.
            </div>
          )}
          {detail && (
            <div className="p-4 space-y-4">
              <div className="text-sm text-slate-700">
                <span className="font-medium">Match type:</span> {detail.match_type} ·{" "}
                <span className="font-medium">Confidence:</span>{" "}
                {detail.confidence_score.toFixed(2)}
              </div>

              {detail.evidence.conflicts && Object.keys(detail.evidence.conflicts).length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded p-2 text-xs">
                  <div className="font-medium text-amber-800 mb-1">Conflicts detected:</div>
                  {Object.entries(detail.evidence.conflicts).map(([field, values]) => (
                    <div key={field} className="text-amber-800">
                      <span className="font-mono">{field}</span>: {values.join(" | ")}
                    </div>
                  ))}
                </div>
              )}

              {/* Records table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-left border-b bg-slate-50">
                      <th className="p-2">Source</th>
                      <th className="p-2">Name</th>
                      <th className="p-2">Email</th>
                      <th className="p-2">Phone</th>
                      <th className="p-2">DOB</th>
                      <th className="p-2">City</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.records.map((r) => (
                      <tr
                        key={r.id}
                        className={`border-b ${
                          r.is_survivor_suggestion ? "bg-emerald-50" : ""
                        }`}
                      >
                        <td className="p-2">
                          <span className="font-medium">{r.source_system}</span>
                          {r.is_survivor_suggestion && (
                            <span className="ml-1 text-[10px] bg-emerald-600 text-white rounded px-1">
                              SUGGESTED
                            </span>
                          )}
                        </td>
                        <td className="p-2">{r.full_name || "—"}</td>
                        <td className="p-2">{r.email || "—"}</td>
                        <td className="p-2">{r.phone || "—"}</td>
                        <td className="p-2">{r.date_of_birth || "—"}</td>
                        <td className="p-2">{r.city || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2 border-t">
                <button
                  onClick={() => resolve("accept_survivor")}
                  className="px-4 py-2 bg-emerald-600 text-white rounded text-sm hover:bg-emerald-700"
                >
                  Accept survivor
                </button>
                <button
                  onClick={() => resolve("reject_match")}
                  className="px-4 py-2 bg-slate-200 text-slate-800 rounded text-sm hover:bg-slate-300"
                >
                  Reject match
                </button>
              </div>

              {/* Survivorship suggestion */}
              <div className="bg-slate-50 border rounded p-3 text-xs">
                <div className="font-medium text-slate-700 mb-2">
                  Survivorship suggestion
                </div>
                <div className="text-slate-600 mb-1">
                  Winner: <span className="font-medium">{detail.survivorship_suggestion.surviving_source}</span>
                </div>
                <ul className="space-y-0.5">
                  {Object.entries(detail.survivorship_suggestion.values).map(([k, v]) => (
                    <li key={k} className="text-slate-600">
                      <span className="font-mono text-slate-500">{k}</span> = {String(v ?? "—")}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}