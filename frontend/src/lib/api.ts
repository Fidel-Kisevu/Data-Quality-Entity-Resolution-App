// Thin fetch wrapper for the DataQ backend.
// Base URL is proxied via vite.config.ts (see below).

const BASE = "/api-proxy";

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 200)}`);
  }
  return res.json();
}

export const api = {
  // --- Reconciliation ---
  listGroups: (params?: { match_type?: string; status?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.match_type) q.set("match_type", params.match_type);
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    return jsonFetch<{ total: number; returned: number; groups: any[] }>(
      `/reconciliation/groups?${q.toString()}`
    );
  },
  getGroup: (id: string) =>
    jsonFetch<any>(`/reconciliation/groups/${id}`),
  resolveGroup: (id: string, body: { action: string; notes?: string; override_values?: Record<string, unknown> }) =>
    jsonFetch<any>(`/reconciliation/groups/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  // --- Trusted Data ---
  listTrustedCustomers: (limit = 100, offset = 0) =>
    jsonFetch<any>(`/trusted/customers?limit=${limit}&offset=${offset}`),
  getTrustedCustomer: (id: string) =>
    jsonFetch<any>(`/trusted/customers/${id}`),
  exportTrustedUrl: () => `${BASE}/trusted/export`,

  // --- AI Analyst ---
  ask: (question: string) =>
    jsonFetch<any>(`/ai/query`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  // --- Audit ---
  listAudit: (params?: { event_type?: string; entity_type?: string; actor?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.event_type) q.set("event_type", params.event_type);
    if (params?.entity_type) q.set("entity_type", params.entity_type);
    if (params?.actor) q.set("actor", params.actor);
    if (params?.limit) q.set("limit", String(params.limit));
    return jsonFetch<any>(`/audit?${q.toString()}`);
  },
  auditSummary: () => jsonFetch<any>(`/audit/summary`),
  auditForRecord: (id: string) => jsonFetch<any>(`/audit/record/${id}`),
};