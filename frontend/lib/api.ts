export type StrategyName = "simple" | "advanced";

export type GenerateEmailPayload = {
  intent: string;
  key_facts: string[];
  tone: string;
  strategy: StrategyName;
  model?: string;
};

export type QualityScores = {
  fact_recall_integration: number;
  tone_audience_fit: number;
  professional_email_quality: number;
  overall: number;
};

export type GenerateEmailResponse = {
  intent?: string | null;
  key_facts: string[];
  subject: string;
  email: string;
  included_facts: string[];
  missing_facts: string[];
  quality_scores: QualityScores;
  attempt_count: number;
  model_used: string;
  strategy_used: StrategyName;
  needs_human_review: boolean;
  review_reasons: string[];
  hallucination_flag: boolean;
  judge_reason: string;
  prompt_version: string;
};

export type HealthResponse = {
  status: string;
  groq_api_key_configured: boolean;
  primary_model: string;
  fallback_model: string;
  judge_model: string;
  prompt_version: string;
  storage: string;
};

export type HistoryItem = {
  id: number;
  created_at: string;
  intent: string;
  key_facts: string[];
  tone: string;
  strategy: StrategyName;
  model_used: string;
  subject: string;
  email: string;
  included_facts: string[];
  missing_facts: string[];
  quality_scores: QualityScores;
  attempt_count: number;
  needs_human_review: boolean;
  review_reasons: string[];
  hallucination_flag: boolean;
  judge_reason: string;
  prompt_version: string;
};

export type HistoryResponse = {
  items: HistoryItem[];
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    let detail = `Request failed with HTTP ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        detail = data.detail.map((item: { msg?: string; type?: string }) => item.msg || item.type).join("; ");
      }
    } catch {
      // Keep fallback message.
    }
    throw new Error(detail);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export function generateEmail(payload: GenerateEmailPayload): Promise<GenerateEmailResponse> {
  return request<GenerateEmailResponse>("/api/generate-email", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getHistory(): Promise<HistoryResponse> {
  return request<HistoryResponse>("/api/history");
}

export function deleteHistoryItem(id: number): Promise<void> {
  return request<void>(`/api/history/${id}`, {
    method: "DELETE"
  });
}
