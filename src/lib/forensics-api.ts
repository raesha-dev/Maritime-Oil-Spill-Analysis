export type JsonRecord = Record<string, unknown>;

export type Integrity = "consistent" | "gap" | "inconsistent" | "insufficient_evidence";

export interface Candidate {
  vessel: {
    vessel_id: string;
    name: string;
    vessel_type: string;
    mmsi: string;
    imo?: string | null;
    latest_position: [number, number];
    ais_integrity: Integrity;
    behavioral_anomaly_score: number;
    vessel_risk_profile: number;
  };
  distance_to_origin_km: number;
  trajectory_alignment: number;
  speed_profile_alignment: number;
  attribution_score: number;
  compute_priority: number;
  rank: number;
}

export interface DashboardSnapshot {
  incident: { incident_id: string; title: string; detected_at: string; aoi: [number, number][] };
  detection: {
    id: string;
    satellite: string;
    acquired_at: string;
    centroid: [number, number];
    area_km2: number;
    oil_confidence: number;
    classification: string;
    confidence_tier: "high" | "medium" | "low";
    pipeline_status: "proceed" | "validate" | "stopped";
  } | null;
  hindcast: {
    center: [number, number];
    radius_km: number;
    release_window_start: string;
    release_window_end: string;
    model: string;
    is_fallback: boolean;
    warnings: string[];
  } | null;
  ranking: {
    candidates: Candidate[];
    uncertainty_reserve: Candidate[];
    raw_candidate_count: number;
  } | null;
  simulations: Array<{
    id: string;
    candidate_id: string;
    source_consistency_score: number;
    components: {
      spatial_iou: number;
      centroid_match: number;
      shape_match: number;
      area_curve_dtw: number;
    };
  }>;
  assessment: {
    state: "further_investigation" | "no_sufficiently_consistent_vessel" | "expand_candidate_pool";
    message: string;
    dossier: string[];
  } | null;
  evidence_events: Array<{
    id: string;
    occurred_at: string;
    kind: string;
    description: string;
    source_ref: string;
  }>;
  updated_at: string;
}

export class ForensicsApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "ForensicsApiError";
  }
}

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE ??
  import.meta.env.VITE_FORENSICS_API_URL ??
  "http://localhost:8000"
).replace(
  /\/$/,
  "",
);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ForensicsApiError(
      "The analysis service is unreachable. Safe demo fallback is active.",
    );
  }
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      error?: { message?: string };
    } | null;
    throw new ForensicsApiError(
      body?.error?.message ?? `Analysis service returned HTTP ${response.status}.`,
      response.status,
    );
  }
  return response.json() as Promise<T>;
}

export const forensicsApi = {
  health: () => request<{ status: "ok" }>("/health"),
  createIncident: (body: JsonRecord) =>
    request<JsonRecord>("/api/v1/incidents", { method: "POST", body: JSON.stringify(body) }),
  getIncident: (incidentId: string) =>
    request<JsonRecord>(`/api/v1/incidents/${encodeURIComponent(incidentId)}`),
  getDashboard: (incidentId: string) =>
    request<DashboardSnapshot>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/dashboard`),
  createDetection: (incidentId: string, body: JsonRecord) =>
    request<JsonRecord>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/detections`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  createHindcast: (incidentId: string, body: JsonRecord) =>
    request<JsonRecord>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/hindcasts`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  rankCandidates: (body: JsonRecord) =>
    request<JsonRecord>("/api/v1/candidates/rank", { method: "POST", body: JSON.stringify(body) }),
  createSimulation: (body: JsonRecord) =>
    request<JsonRecord>("/api/v1/simulations", { method: "POST", body: JSON.stringify(body) }),
  createAssessment: (incidentId: string, body: JsonRecord) =>
    request<JsonRecord>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/assessment`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  listEvidence: (incidentId: string) =>
    request<JsonRecord[]>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/evidence-events`),
  createEvidence: (body: JsonRecord) =>
    request<JsonRecord>("/api/v1/evidence-events", { method: "POST", body: JSON.stringify(body) }),
  listMessages: (incidentId: string) =>
    request<JsonRecord[]>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/messages`),
  sendMessage: (body: JsonRecord) =>
    request<JsonRecord>("/api/v1/messages", { method: "POST", body: JSON.stringify(body) }),
  subscribeMessages(
    incidentId: string,
    onMessage: (message: JsonRecord) => void,
    onError?: () => void,
  ) {
    const socketBase = apiBaseUrl.replace(/^http/, "ws");
    const socket = new WebSocket(
      `${socketBase}/api/v1/incidents/${encodeURIComponent(incidentId)}/messages/live`,
    );
    socket.onmessage = (event) => onMessage(JSON.parse(event.data) as JsonRecord);
    socket.onerror = () => onError?.();
    return socket;
  },
};
