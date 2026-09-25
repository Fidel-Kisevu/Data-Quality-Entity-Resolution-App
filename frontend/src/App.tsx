import { useEffect, useState } from "react";
import DataSources from "./pages/DataSources";
import DatasetOverview from "./pages/DatasetOverview";
import QualityFindings from "./pages/QualityFindings";
import Reconciliation from "./pages/Reconciliation";
import Exceptions from "./pages/Exceptions";
import TrustedData from "./pages/TrustedData";
import AIAnalyst from "./pages/AIAnalyst";
import AuditTrail from "./pages/AuditTrail";

type Page =
  | "home"
  | "sources"
  | "overview"
  | "findings"
  | "reconciliation"
  | "exceptions"
  | "trusted"
  | "ai"
  | "audit";

interface DashboardStats {
  sources: { total: number; profiled: number };
  customers: { raw: number; trusted: number; duplicates_linked: number };
  transactions: { total: number; linked: number; coverage_pct: number };
  matching: { total_groups: number; resolved: number; open: number; health_pct: number };
  quality: { total_findings: number; critical_findings: number };
  exceptions: { total: number; open: number; critical_open: number };
  audit: { total_events: number };
  risk: { level: string; points: number };
}

const NAV: { id: Page; label: string; icon: string }[] = [
  { id: "home", label: "Home", icon: "◈" },
  { id: "sources", label: "Data Sources", icon: "◎" },
  { id: "overview", label: "Dataset Overview", icon: "▣" },
  { id: "findings", label: "Quality Findings", icon: "◇" },
  { id: "reconciliation", label: "Reconciliation", icon: "◌" },
  { id: "exceptions", label: "Exceptions", icon: "△" },
  { id: "trusted", label: "Trusted Data", icon: "✦" },
  { id: "ai", label: "AI Analyst", icon: "✧" },
  { id: "audit", label: "Audit Trail", icon: "◍" },
];

const TOP_NAV: Page[] = ["home", "overview", "findings", "reconciliation", "trusted"];
const SIDEBAR_NAV = NAV.filter((item) => !TOP_NAV.includes(item.id));

function Home() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api-proxy/dashboard/stats")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setStats)
      .catch((e) => setError(String(e)));
  }, []);

  const riskClass =
    stats?.risk.level === "High"
      ? "high-risk"
      : stats?.risk.level === "Medium"
      ? "medium-risk"
      : "low-risk";

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Operations intelligence</span>
          <h1 className="page-title">DataQ</h1>
        </div>
      </header>

      {!stats && !error && (
        <div className="panel-card">Loading live stats…</div>
      )}

      {error && (
        <div className="panel-card" style={{ color: "#b91c1c" }}>
          Could not load dashboard stats: {error}
        </div>
      )}

      {stats && (
        <>
          <section className="hero-panel">
            <div className="hero-copy">
              <span className="status-pill">Live monitoring</span>
              <h2>Trust every customer record across every source.</h2>
              <p>
                Monitor data quality, resolve duplicates, and surface exceptions before they
                affect downstream operations.
              </p>
            </div>

            <div className="hero-stack">
              <div className="mini-metric">
                <span>Match health</span>
                <strong>{stats.matching.health_pct}%</strong>
              </div>
              <div className="mini-metric accent">
                <span>Open exceptions</span>
                <strong>{stats.exceptions.open}</strong>
              </div>
            </div>
          </section>

          <div className="metric-grid">
            <div className="metric-card">
              <span className="metric-label">Sources ingested</span>
              <strong className="metric-value">{stats.sources.total}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Trusted customers</span>
              <strong className="metric-value">{stats.customers.trusted}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Duplicates linked</span>
              <strong className="metric-value">{stats.customers.duplicates_linked}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Risk score</span>
              <strong className={`metric-value ${riskClass}`}>
                {stats.risk.level}
              </strong>
            </div>
          </div>

          <div className="content-grid two-up">
            <div className="panel-card">
              <div className="card-header">
                <h3>Pipeline status</h3>
                <span className="chip success">Stable</span>
              </div>
              <div className="pipeline-list">
                <div>
                  <span>Profiling</span>
                  <strong>
                    {stats.sources.profiled}/{stats.sources.total} complete
                  </strong>
                </div>
                <div>
                  <span>Quality findings</span>
                  <strong>{stats.quality.total_findings} open</strong>
                </div>
                <div>
                  <span>Match groups</span>
                  <strong>
                    {stats.matching.resolved}/{stats.matching.total_groups} resolved
                  </strong>
                </div>
                <div>
                  <span>Transaction linking</span>
                  <strong>{stats.transactions.coverage_pct}% coverage</strong>
                </div>
              </div>
            </div>

            <div className="panel-card">
              <div className="card-header">
                <h3>Immediate priorities</h3>
                <span className="chip warning">
                  {stats.exceptions.open + stats.quality.critical_findings} items
                </span>
              </div>
              <ul className="priority-list">
                {stats.quality.critical_findings > 0 && (
                  <li>
                    Resolve {stats.quality.critical_findings} critical quality findings.
                  </li>
                )}
                {stats.exceptions.critical_open > 0 && (
                  <li>
                    Review {stats.exceptions.critical_open} critical exceptions in the queue.
                  </li>
                )}
                {stats.matching.open > 0 && (
                  <li>
                    Approve or reject {stats.matching.open} pending match groups.
                  </li>
                )}
                {stats.quality.critical_findings === 0 &&
                  stats.exceptions.critical_open === 0 &&
                  stats.matching.open === 0 && (
                    <li>No action required — pipeline is clean.</li>
                  )}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default function App() {
  const [page, setPage] = useState<Page>("home");

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-panel">
          <div className="brand-mark">D</div>
          <div>
            <div className="brand-name">DataQ</div>
            <div className="brand-subtitle">Data quality platform</div>
          </div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {SIDEBAR_NAV.map((n) => (
            <button
              key={n.id}
              onClick={() => setPage(n.id)}
              className={`nav-button ${page === n.id ? "is-active" : ""}`}
            >
              <span className="nav-icon">{n.icon}</span>
              <span>{n.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="status-dot" />
          <span>MVP · Phase 0 locked</span>
        </div>
      </aside>

      <main className="main-panel">
        <div className="topbar">
          <nav className="header-nav" aria-label="Top navigation">
            {TOP_NAV.map((item) => {
              const navItem = NAV.find((entry) => entry.id === item);
              if (!navItem) return null;

              return (
                <button
                  key={navItem.id}
                  onClick={() => setPage(navItem.id)}
                  className={`topbar-link ${page === navItem.id ? "is-active" : ""}`}
                >
                  {navItem.label}
                </button>
              );
            })}
          </nav>

          <div className="topbar-actions">
            <button className="ghost-button">Export</button>
            <button className="primary-button">Run quality scan</button>
          </div>
        </div>

        {page === "home" && <Home />}
        {page === "sources" && <DataSources />}
        {page === "overview" && <DatasetOverview />}
        {page === "findings" && <QualityFindings />}
        {page === "reconciliation" && <Reconciliation />}
        {page === "exceptions" && <Exceptions />}
        {page === "trusted" && <TrustedData />}
        {page === "ai" && <AIAnalyst />}
        {page === "audit" && <AuditTrail />}
      </main>
    </div>
  );
}