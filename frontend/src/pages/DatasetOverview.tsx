import { useEffect, useState } from "react";

const BASE = "/api-proxy";

interface SourceRow {
  id: string;
  name: string;
  source_system: string;
  original_filename: string;
  status: string;
  row_count: number | null;
  created_at: string;
}

interface SourceDetail extends SourceRow {
  stored_path: string;
  profile: {
    row_count: number;
    column_count: number;
    columns: Record<
      string,
      {
        dtype: string;
        null_count: number;
        null_pct: number;
        unique_count: number;
        sample_values: string[];
      }
    >;
  };
  updated_at: string;
}

export default function DatasetOverview() {
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SourceDetail | null>(null);

  async function load() {
    const res = await fetch(`${BASE}/sources`);
    const data = await res.json();
    setSources(data);
    if (data.length > 0 && !selectedId) {
      openSource(data[0].id);
    }
  }

  async function openSource(id: string) {
    setSelectedId(id);
    const res = await fetch(`${BASE}/sources/${id}`);
    if (res.ok) setDetail(await res.json());
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Data profiling</span>
          <h1 className="page-title">Dataset Overview</h1>
          <p className="page-subtitle">
            Per-dataset profile: column types, null density, uniqueness, samples.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-4">
        {/* Source picker */}
        <div className="col-span-4 detail-panel">
          <div className="panel-header">
            <span>Datasets ({sources.length})</span>
          </div>
          <div className="max-h-[70vh] overflow-y-auto">
            {sources.map((s) => (
              <button
                key={s.id}
                onClick={() => openSource(s.id)}
                className={`w-full text-left p-3 border-b hover:bg-slate-50 ${
                  selectedId === s.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="text-sm font-medium truncate">
                  {s.original_filename}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-[10px] font-mono bg-slate-100 px-2 py-0.5 rounded">
                    {s.source_system}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {s.row_count ?? "?"} rows
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Detail */}
        <div className="col-span-8 space-y-4">
          {!detail && (
            <div className="panel-card p-6 text-sm text-slate-300">
              Select a dataset to see its profile.
            </div>
          )}
          {detail && (
            <>
              {/* Header cards */}
              <div className="grid grid-cols-4 gap-3">
                <div className="metric-card">
                  <span className="metric-label">Rows</span>
                  <strong className="metric-value">{detail.profile?.row_count ?? "—"}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Columns</span>
                  <strong className="metric-value">{detail.profile?.column_count ?? "—"}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Source</span>
                  <strong className="metric-value">{detail.source_system}</strong>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Status</span>
                  <strong className="metric-value low-risk">{detail.status}</strong>
                </div>
              </div>

              {/* Column profile table */}
              {detail.profile && (
                <div className="detail-panel">
                  <div className="panel-header">
                    <span>Column profile</span>
                  </div>
                  <div className="max-h-[60vh] overflow-y-auto">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-slate-50 border-b">
                        <tr className="text-left">
                          <th className="p-2">Column</th>
                          <th className="p-2">Type</th>
                          <th className="p-2 text-right">Nulls</th>
                          <th className="p-2 text-right">Null %</th>
                          <th className="p-2 text-right">Unique</th>
                          <th className="p-2">Sample values</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(detail.profile.columns).map(
                          ([col, meta]) => {
                            const isHighNull = meta.null_pct > 10;
                            return (
                              <tr key={col} className="border-b hover:bg-slate-50">
                                <td className="p-2 font-mono font-medium">{col}</td>
                                <td className="p-2 text-slate-500">{meta.dtype}</td>
                                <td
                                  className={`p-2 text-right font-mono ${
                                    isHighNull ? "text-red-600 font-semibold" : ""
                                  }`}
                                >
                                  {meta.null_count}
                                </td>
                                <td
                                  className={`p-2 text-right font-mono ${
                                    isHighNull ? "text-red-600 font-semibold" : ""
                                  }`}
                                >
                                  {meta.null_pct.toFixed(1)}%
                                </td>
                                <td className="p-2 text-right font-mono">
                                  {meta.unique_count}
                                </td>
                                <td className="p-2 text-slate-500 truncate max-w-xs">
                                  {meta.sample_values.slice(0, 2).join(", ")}
                                </td>
                              </tr>
                            );
                          }
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* File info */}
              <div className="border rounded-lg bg-white p-3 text-xs">
                <div className="text-slate-500">
                  <span className="font-medium">Stored at:</span>{" "}
                  <span className="font-mono">{detail.stored_path}</span>
                </div>
                <div className="text-slate-500 mt-1">
                  <span className="font-medium">Uploaded:</span>{" "}
                  {new Date(detail.created_at).toLocaleString()}
                </div>
                <div className="text-slate-500 mt-1">
                  <span className="font-medium">Updated:</span>{" "}
                  {new Date(detail.updated_at).toLocaleString()}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}