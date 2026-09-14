export type OpportunityType =
  | "hackathon"
  | "internship"
  | "fellowship"
  | "scholarship"
  | "conference"
  | "certification"
  | "other";

export type OpportunityStatus = "new" | "seen" | "saved" | "dismissed" | "expired";

export interface WatchSettings {
  enabled: boolean;
  frequency_minutes: number;
  allowed_domains: string[];
  opportunity_types: string[];
  max_queries_per_run: number;
  max_results_per_query: number;
  minimum_relevance_score: number | null;
  daily_max_runs: number;
}

export interface Profile {
  id: string;
  full_name: string;
  language: "fr" | "en";
  interests: string[];
  countries: string[];
  mobility_countries: string[];
  study_level: string;
  skills: string[];
  relevance_threshold: number;
  watch: WatchSettings;
}

export interface Opportunity {
  id: string;
  type: OpportunityType;
  title: string;
  organization: string;
  summary: string;
  relevance_score: number;
  confidence_score: number;
  relevance_reasons: string[];
  deadline: string | null;
  eligibility: Record<string, unknown>;
  source_url: string;
  verified_at: string;
  status: OpportunityStatus;
}

export interface OpportunityPage {
  items: Opportunity[];
  page: number;
  page_size: number;
  total: number;
}

export interface Run {
  id: string;
  trigger: "manual" | "scheduled";
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
  opportunities_found: number;
  error_message: string | null;
  urls_processed: string[];
}

export interface WatchState {
  last_run_at: string | null;
  next_run_at: string | null;
  last_successful_run_at: string | null;
  runs_today: number;
  daily_max_runs: number;
  processed_urls_count: number;
  enabled: boolean;
  frequency_minutes: number;
}

const BASE_URL: string =
  (import.meta as unknown as { env: Record<string, string> }).env
    .VITE_API_URL ?? "http://127.0.0.1:8000";

// Clé API injectée au build (VITE_API_KEY). Absente en dev local :
// aucun header envoyé, le backend local reste ouvert.
// Dans le bundle packagé la clé est lisible par extraction — protection
// anti-abus occasionnels uniquement. Les vrais remparts coûts sont le
// rate-limit (429) et le quota quotidien partagé via DynamoDB.
const API_KEY: string =
  (import.meta as unknown as { env: Record<string, string> }).env
    .VITE_API_KEY ?? "";

async function request<T>(path: string, init?: RequestInit, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${BASE_URL}/api/v1${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(API_KEY ? { "x-api-key": API_KEY } : {}),
    },
    ...init,
    signal,
  });
  if (response.status === 401) {
    throw new Error("Accès refusé : clé API invalide ou expirée.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Erreur ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  getWatchState: () => request<WatchState>("/watch"),

  getProfile: () => request<Profile>("/profile"),

  updateProfile: (profile: Partial<Profile>) =>
    request<Profile>("/profile", {
      method: "PUT",
      body: JSON.stringify(profile),
    }),

  listOpportunities: (params: {
    page?: number;
    page_size?: number;
    min_score?: number;
    status?: string;
    since?: string;
  }) => {
    const query = new URLSearchParams();
    if (params.page) query.set("page", String(params.page));
    if (params.page_size) query.set("page_size", String(params.page_size));
    if (params.min_score !== undefined) query.set("min_score", String(params.min_score));
    if (params.status) query.set("status", params.status);
    if (params.since) query.set("since", params.since);
    const suffix = query.toString() ? `?${query.toString()}` : "";
    return request<OpportunityPage>(`/opportunities${suffix}`);
  },

  getOpportunity: (id: string) => request<Opportunity>(`/opportunities/${id}`),

  submitFeedback: (id: string, action: "interested" | "not_interested" | "saved" | "dismissed") =>
    request<{ opportunity_id: string; action: string; recorded_at: string }>(
      `/opportunities/${id}/feedback`,
      { method: "POST", body: JSON.stringify({ action }) }
    ),

  createRun: (signal?: AbortSignal) =>
    request<Run>("/runs", { method: "POST" }, signal),

  getRun: (id: string) => request<Run>(`/runs/${id}`),
};
