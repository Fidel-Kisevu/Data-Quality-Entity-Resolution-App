import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { TrustedCustomer, TrustedCustomerDetail } from "../lib/types";

export default function TrustedData() {
  const [customers, setCustomers] = useState<TrustedCustomer[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TrustedCustomerDetail | null>(null);
  const [search, setSearch] = useState("");

  async function load() {
    const res = await api.listTrustedCustomers(200, 0);
    setCustomers(res.customers);
    setTotal(res.total);
  }

  async function openCustomer(id: string) {
    setSelectedId(id);
    const d = await api.getTrustedCustomer(id);
    setDetail(d);
  }

  useEffect(() => { load(); }, []);

  const filtered = customers.filter(
    (c) =>
      !search ||
      (c.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
      (c.email || "").toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-shell">
      <header className="page-header">
        <div>
          <span className="eyebrow">Trust layer</span>
          <h1 className="page-title">Trusted Data</h1>
          <p className="page-subtitle">{total} trusted customer records</p>
        </div>
        <div className="flex gap-2">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search name or email…"
            className="border rounded px-3 py-1 text-sm w-64"
          />
          <a
            href={api.exportTrustedUrl()}
            className="px-3 py-1 bg-slate-900 text-white rounded text-sm hover:bg-slate-700"
          >
            Export CSV
          </a>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-4">
        {/* Table */}
        <div className="col-span-7 detail-panel">
          <div className="max-h-[75vh] overflow-y-auto">
            <table className="data-table">
              <thead className="sticky top-0 bg-slate-50 border-b">
                <tr className="text-left">
                  <th className="p-2">Name</th>
                  <th className="p-2">Email</th>
                  <th className="p-2">City</th>
                  <th className="p-2">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => openCustomer(c.id)}
                    className={`border-b cursor-pointer hover:bg-slate-50 ${
                      selectedId === c.id ? "bg-blue-50" : ""
                    }`}
                  >
                    <td className="p-2 font-medium">{c.full_name || "—"}</td>
                    <td className="p-2 text-slate-600">{c.email || "—"}</td>
                    <td className="p-2 text-slate-600">{c.city || "—"}</td>
                    <td className="p-2 text-xs">
                      {c.confidence_score != null
                        ? c.confidence_score.toFixed(2)
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Detail */}
        <div className="col-span-5 detail-panel">
          <div className="panel-header">
            <span>Record detail</span>
          </div>
          {!detail && (
            <div className="p-6 text-sm text-slate-500">
              Click a row to see full detail and lineage.
            </div>
          )}
          {detail && (
            <div className="p-4 space-y-4 text-sm">
              <div>
                <div className="text-lg font-semibold">{detail.full_name}</div>
                <div className="text-slate-500">{detail.email}</div>
                <div className="text-slate-500">{detail.phone}</div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs text-slate-700">
                <div><span className="text-slate-500">DOB:</span> {detail.date_of_birth || "—"}</div>
                <div><span className="text-slate-500">City:</span> {detail.city || "—"}</div>
                <div><span className="text-slate-500">Country:</span> {detail.country || "—"}</div>
                <div><span className="text-slate-500">Status:</span> {detail.status}</div>
              </div>

              {/* Lineage */}
              <div>
                <div className="text-xs font-medium text-slate-600 mb-1">
                  LINEAGE ({detail.lineage.length} source records)
                </div>
                <div className="space-y-1">
                  {detail.lineage.map((l) => (
                    <div
                      key={l.customer_id}
                      className={`flex items-center justify-between text-xs px-2 py-1 rounded ${
                        l.is_survivor ? "bg-emerald-50" : "bg-slate-50"
                      }`}
                    >
                      <span className="font-medium">{l.source_system}</span>
                      <span className="text-slate-500 font-mono">{l.source_customer_id}</span>
                      {l.is_survivor && (
                        <span className="text-[10px] bg-emerald-600 text-white rounded px-1">
                          SURVIVOR
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Transactions */}
              <div>
                <div className="text-xs font-medium text-slate-600 mb-1">
                  TRANSACTIONS ({detail.transactions.length})
                </div>
                {detail.transactions.length === 0 && (
                  <div className="text-xs text-slate-500">No linked transactions.</div>
                )}
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {detail.transactions.map((t) => (
                    <div key={t.id} className="text-xs flex justify-between border-b py-1">
                      <span className="text-slate-500">{t.transaction_date}</span>
                      <span className="font-medium">
                        {t.amount} {t.currency}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}