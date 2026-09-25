import { useEffect, useState } from "react";

const BASE = "/api-proxy";

interface Finding {
  id: string;
  rule_id: string;
  entity_type: string;
  record_id: string;
  severity: string;
  message: string;
  evidence: Record<string, unknown> | null;
  status: string;
  created_at: string;
}

interface Summary {
  total_open_findings: number;
  by_severity: Record<string, number>;
  by_rule: Record<string, number>;
  by_entity_type: Record<string, number>;
}

const SEVERITY_COLORS: Record<string, string> = {
  Critical: "bg-red-100 text-red-700 border-red-200",
  High: "bg-orange-100 text-orange-700 border-orange-200",
  Medium: "bg-amber-100 text-amber-700 border-amber-200",
  Low: "bg-slate-100 text-slate-600 border-slate-200",
  Info: "bg-blue-100 text-blue-700 border-blue-200",
};

const SEVERITY_BADGE: Record<string, string> = {
  Critical: "bg-red-600 text-white",
  High: "bg-orange-600 text-white",
  Medium: "bg-amber-500 text-white",
  Low: "bg-slate-500 text-white",
  Info: "bg-blue-500 text-white",
};

export default function QualityFindings() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [total, setTotal] = useState(0);
  const [severity, setSeverity] = useState<string>("");
  const [ruleId, setRuleId] = useState<string>("");
  const [entityType, setEntityType] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Finding | null>(null);
  const [busy, setBusy] = useState(false);

  async function loadSummary() {
    const res = await fetch(`${BASE}/quality/summary`);
    setSummary(await res.json());
  }

  async function loadFindings() {
    setBusy(true);
    try {
      const q = new URLSearchParams();
      q.set("limit", "200");
      if (severity) q.set("severity", severity);
      if (ruleId) q.set("rule_id", ruleId);
      if (entityType) q.set("entity_type", entityType);
      const res = await fetch(`${BASE}/quality/findings?${q.toString()}`);
      const data = await res.json();
      setFindings(data.findings);
      setTotal(data.total);
    } finally {
      setBusy(false);
    }
  }

  async function openFinding(id: string) {
    setSelectedId(id);
    const res = await fetch(`${BASE}/quality/findings/${id}`);
    if (res.ok) setDetail(await res.json());
  }

  useEffect(() => { loadSummary(); }, []);
  useEffect(() => { loadFindings(); }, [severity, ruleId, entityType]);

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Monitoring</span>
          <h1 className="page-title">Quality Findings</h1>
          <p className="page-subtitle">
            22 rules across Completeness, Validity, Uniqueness, Consistency, Anomaly.
          </p>
        </div>
      </header>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-5 gap-3">
          <button
            onClick={() => setSeverity("")}
            className={`metric-card text-left ${
              !severity ? "ring-2 ring-cyan-400" : ""
            }`}
          >
            <div className="text-xs text-slate-500">All findings</div>
            <div className="text-3xl font-semibold">{summary.total_open_findings}</div>
          </button>
          {(["Critical", "High", "Medium", "Low"] as const).map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverity(severity === sev ? "" : sev)}
              className={`metric-card text-left ${SEVERITY_COLORS[sev]} ${
                severity === sev ? "ring-2 ring-cyan-400" : ""
              }`}
            >
              <div className="text-xs font-medium">{sev}</div>
              <div className="text-3xl font-semibold">
                {summary.by_severity[sev] ?? 0}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 items-center">
        <select
          value={ruleId}
          onChange={(e) => setRuleId(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="">All rules</option>
          {summary &&
            Object.entries(summary.by_rule)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([rule, n]) => (
                <option key={rule} value={rule}>
                  {rule} ({n})
                </option>
              ))}
        </select>
        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          className="border rounded px-3 py-1 text-sm"
        >
          <option value="">All entities</option>
          <option value="customer">customer</option>
          <option value="transaction">transaction</option>
        </select>
        <span className="text-xs text-slate-500 ml-auto">
          {total} findings {busy && "· loading…"}
        </span>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* Findings list */}
        <div className="col-span-7 detail-panel">
          <div className="panel-header">
            <span>Findings</span>
          </div>
          <div className="max-h-[65vh] overflow-y-auto">
            {findings.map((f) => (
              <button
                key={f.id}
                onClick={() => openFinding(f.id)}
                className={`w-full text-left p-3 border-b hover:bg-slate-50 ${
                  selectedId === f.id ? "bg-blue-50" : ""
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      SEVERITY_BADGE[f.severity] || "bg-slate-500 text-white"
                    }`}
                  >
                    {f.severity}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    {f.rule_id}
                  </span>
                  <span className="text-[10px] text-slate-400 ml-auto">
                    {f.entity_type}
                  </span>
                </div>
                <div className="text-sm text-slate-800">{f.message}</div>
                <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                  {f.record_id.slice(0, 12)}…
                </div>
              </button>
            ))}
            {findings.length === 0 && !busy && (
              <div className="p-6 text-sm text-slate-500 text-center">
                No findings match this filter.
              </div>
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="col-span-5 detail-panel">
          <div className="panel-header">
            <span>Finding detail</span>
          </div>
          {!detail && (
            <div className="p-6 text-sm text-slate-500">
              Select a finding from the left.
            </div>
          )}
          {detail && (
            <div className="p-4 space-y-3 text-sm">
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                    SEVERITY_BADGE[detail.severity] || "bg-slate-500 text-white"
                  }`}
                >
                  {detail.severity}
                </span>
                <span className="text-xs font-mono text-slate-500">
                  {detail.rule_id}
                </span>
                <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded-full text-slate-700 ml-auto">
                  {detail.status}
                </span>
              </div>
              <div className="text-sm text-slate-800">{detail.message}</div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                <div>
                  <span className="text-slate-400">Entity:</span>{" "}
                  {detail.entity_type}
                </div>
                <div>
                  <span className="text-slate-400">When:</span>{" "}
                  {new Date(detail.created_at).toLocaleString()}
                </div>
                <div className="col-span-2">
                  <span className="text-slate-400">Record ID:</span>{" "}
                  <span className="font-mono text-[11px]">{detail.record_id}</span>
                </div>
              </div>

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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}