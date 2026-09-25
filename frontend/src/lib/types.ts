// Shared types matching backend responses.

export interface MatchGroupSummary {
  id: string;
  match_type: "probable" | "possible" | "exact";
  confidence_score: number;
  status: string;
  record_ids: string[];
  evidence: {
    signals?: Record<string, number>;
    conflicts?: Record<string, string[]>;
    size?: number;
  };
  created_at: string;
}

export interface MatchGroupDetail {
  id: string;
  match_type: string;
  confidence_score: number;
  status: string;
  evidence: {
    signals?: Record<string, number>;
    conflicts?: Record<string, string[]>;
    size?: number;
  };
  records: CustomerRecord[];
  survivorship_suggestion: {
    surviving_record_id: string;
    surviving_source: string;
    values: Record<string, string | null>;
  };
}

export interface CustomerRecord {
  id: string;
  source_system: string;
  source_customer_id: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  address_line1?: string | null;
  city: string | null;
  country: string | null;
  status: string;
  is_survivor_suggestion?: boolean;
}

export interface TrustedCustomer {
  id: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  date_of_birth: string | null;
  city: string | null;
  country: string | null;
  status: string;
  confidence_score: number | null;
  is_manually_reviewed: boolean;
  lineage: LineageEntry[];
}

export interface LineageEntry {
  customer_id: string;
  source_system: string;
  source_customer_id: string;
  is_survivor: boolean;
}

export interface TrustedCustomerDetail extends TrustedCustomer {
  address_line1: string | null;
  transactions: TransactionRow[];
}

export interface TransactionRow {
  id: string;
  transaction_date: string | null;
  amount: string | null;
  currency: string | null;
  status: string;
  source_system: string;
}

export interface AIResponse {
  question: string;
  answer: string;
  evidence: Record<string, unknown>;
  matched_rule: string;
  grounded: boolean;
  latency_ms: number;
}

export interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  actor: string;
  action: string;
  before_state: Record<string, unknown> | null;
  after_state: Record<string, unknown> | null;
  notes: string | null;
  created_at: string;
}

export interface AuditSummary {
  total_events: number;
  by_event_type: Record<string, number>;
  by_actor: Record<string, number>;
}