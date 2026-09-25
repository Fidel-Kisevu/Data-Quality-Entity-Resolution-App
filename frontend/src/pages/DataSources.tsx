import { useEffect, useRef, useState } from "react";

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

const SOURCE_SYSTEMS = ["CRM", "ERP", "MKT"] as const;

export default function DataSources() {
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [sourceSystem, setSourceSystem] = useState<string>("CRM");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function load() {
    const res = await fetch(`${BASE}/sources`);
    const data = await res.json();
    setSources(data);
  }

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    setUploadResult(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(
        `${BASE}/sources/upload?source_system=${sourceSystem}`,
        { method: "POST", body: form }
      );
      if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);

      const result = await res.json();
      setUploadResult(
        `Uploaded as ${result.source_system}. ID ${result.id.slice(0, 8)}. Now ingest to parse.`
      );

      // Auto-ingest
      const ingestRes = await fetch(`${BASE}/sources/${result.id}/ingest`, {
        method: "POST",
      });
      if (ingestRes.ok) {
        const ingest = await ingestRes.json();
        setUploadResult(
          `Ingested ${ingest.rows_inserted} rows (entity: ${ingest.entity_type}).`
        );
      }

      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const statusColors: Record<string, string> = {
    raw: "bg-amber-100 text-amber-700",
    profiled: "bg-emerald-100 text-emerald-700",
  };

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Ingestion</span>
          <h1 className="page-title">Data Sources</h1>
          <p className="page-subtitle">
            Upload CSV or Excel files. Files are profiled on ingest.
          </p>
        </div>
      </header>

      {/* Upload card */}
      <form onSubmit={upload} className="panel-card space-y-3">
        <div className="grid grid-cols-12 gap-3 items-end">
          <div className="col-span-5">
            <label className="block text-xs text-slate-600 mb-1">File</label>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full border rounded px-2 py-1 text-sm"
            />
          </div>
          <div className="col-span-3">
            <label className="block text-xs text-slate-600 mb-1">Source system</label>
            <select
              value={sourceSystem}
              onChange={(e) => setSourceSystem(e.target.value)}
              className="w-full border rounded px-2 py-1 text-sm"
            >
              {SOURCE_SYSTEMS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="col-span-4 flex gap-2">
            <button
              type="submit"
              disabled={!file || uploading}
              className="primary-button disabled:opacity-50"
            >
              {uploading ? "Uploading…" : "Upload & Ingest"}
            </button>
          </div>
        </div>

        {uploadResult && (
          <div className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
            ✓ {uploadResult}
          </div>
        )}
        {error && (
          <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
            ✗ {error}
          </div>
        )}
      </form>

      {/* Sources table */}
      <div className="detail-panel">
        <div className="panel-header">
          <span>Uploaded sources ({sources.length})</span>
        </div>
        <table className="data-table">
          <thead className="bg-slate-50 border-b">
            <tr className="text-left">
              <th className="p-2">File</th>
              <th className="p-2">Source system</th>
              <th className="p-2">Status</th>
              <th className="p-2 text-right">Rows</th>
              <th className="p-2">Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-b">
                <td className="p-2 font-medium">{s.original_filename}</td>
                <td className="p-2">
                  <span className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded">
                    {s.source_system}
                  </span>
                </td>
                <td className="p-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      statusColors[s.status] || "bg-slate-100 text-slate-700"
                    }`}
                  >
                    {s.status}
                  </span>
                </td>
                <td className="p-2 text-right">{s.row_count ?? "—"}</td>
                <td className="p-2 text-xs text-slate-500">
                  {new Date(s.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {sources.length === 0 && (
              <tr>
                <td colSpan={5} className="p-4 text-sm text-slate-500 text-center">
                  No sources uploaded yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}