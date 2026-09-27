export type JsonRecord = Record<string, unknown>;

export interface ProvenanceEnvelope<T> {
  data: T;
  provenance: {
    tag: "OBSERVED" | "INFERRED" | "SIMULATED" | "COMPARED" | "SYSTEM" | "GAP";
    source: string;
    generated_at: string;
    model_run_id: string | null;
    assumptions: string[];
    degraded_inputs: string[];
  };
}

export type Integrity = "consistent" | "gap" | "inconsistent" | "insufficient_evidence";

export interface Candidate {
  vessel: {
    vessel_id: string;
    name: string;
    vessel_type: string;
    mmsi: string;
    imo?: string | null;
    latest_position: [number, number] | null;
    ais_integrity: Integrity;
    behavioral_anomaly_score: number | null;
    vessel_risk_profile: number | null;
  };
  distance_to_origin_km: number;
  trajectory_alignment: number | null;
  speed_profile_alignment: number | null;
  attribution_score: number | null;
  compute_priority: number | null;
  source_consistency_score: number | null;
  rank: number;
}

export interface DashboardSnapshot {
  incident: { incident_id: string; title: string; detected_at: string; aoi: [number, number][] };
  detection: {
    id: string | null;
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

export type GeoJSONFeatureCollection = {
  type: "FeatureCollection";
  features: Array<Record<string, unknown>>;
};

export interface MapLayers {
  observed_slick: ProvenanceEnvelope<GeoJSONFeatureCollection>;
  ais_tracks: ProvenanceEnvelope<GeoJSONFeatureCollection>;
  origin_field: ProvenanceEnvelope<GeoJSONFeatureCollection>;
}

export interface SystemStatus {
  service: "spill-forensics-api";
  version: string;
  demo_mode: boolean;
  scenario: "clean" | "null_state";
}

export interface RunRequest {
  mmsi: string;
  release_time: string;
  environment?: string;
}

export interface RunAccepted {
  run_id: string;
  cached: boolean;
}

export interface RunStatus {
  run_id: string;
  state: "QUEUED" | "RUNNING" | "COMPLETE" | "FAILED";
  progress: number;
  message: string;
  cached: boolean;
  result: { run: JsonRecord; frames: GeoJSONFeatureCollection } | null;
}

export interface AttributionBundle {
  attribution: {
    outcome: "SUPPORTS_INVESTIGATION" | "AMBIGUOUS" | "NULL_STATE";
    message: string;
    top: Array<Record<string, unknown>> | null;
    gap: number | null;
  };
  dossier: {
    vessel_name: string;
    headline: string;
    lines: Array<{ tag: "PHYSICS" | "BEHAVIORAL" | "RISK_CONTEXT"; text: string }>;
    verdict: string;
  } | null;
}

export interface EvidenceEvent {
  id: string;
  occurred_at: string;
  kind: string;
  description: string;
  source_ref: string;
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

const apiBaseUrl = (import.meta.env["VITE_FORENSICS_API_URL"] ?? "http://localhost:8000").replace(
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

async function requestBlob(path: string): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}`);
  } catch {
    throw new ForensicsApiError("The analysis service is unreachable.");
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
  return response.blob();
}

export const forensicsApi = {
  health: () => request<{ status: "ok" }>("/health"),
  systemStatus: () => request<SystemStatus>("/api/v1/system/status"),
  createIncident: (body: JsonRecord) =>
    request<JsonRecord>("/api/v1/incidents", { method: "POST", body: JSON.stringify(body) }),
  getIncident: (incidentId: string) =>
    request<ProvenanceEnvelope<JsonRecord>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}`,
    ),
  getDashboard: (incidentId: string) =>
    request<DashboardSnapshot>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/dashboard`),
  getDetection: (incidentId: string) =>
    request<ProvenanceEnvelope<JsonRecord>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/detection`,
    ),
  getHindcast: (incidentId: string) =>
    request<ProvenanceEnvelope<JsonRecord>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/hindcast`,
    ),
  getCandidates: (incidentId: string) =>
    request<ProvenanceEnvelope<JsonRecord>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/candidates`,
    ),
  getMapLayers: (incidentId: string) =>
    request<MapLayers>(`/api/v1/incidents/${encodeURIComponent(incidentId)}/layers`),
  getAisTracks: (incidentId: string) =>
    request<ProvenanceEnvelope<GeoJSONFeatureCollection>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/ais-tracks`,
    ),
  getArtifactRunFrames: (incidentId: string, runId: string) =>
    request<ProvenanceEnvelope<GeoJSONFeatureCollection>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/runs/${encodeURIComponent(runId)}/frames`,
    ),
  getAttribution: (incidentId: string, runId?: string) =>
    request<ProvenanceEnvelope<AttributionBundle>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/attribution${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`,
    ),
  getDossier: (incidentId: string, mmsi: string, runId?: string) =>
    request<ProvenanceEnvelope<AttributionBundle["dossier"]>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/candidates/${encodeURIComponent(mmsi)}/dossier${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`,
    ),
  getEvidenceEnvelope: (incidentId: string) =>
    request<ProvenanceEnvelope<EvidenceEvent[]>>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/evidence`,
    ),
  submitCounterfactual: (incidentId: string, body: RunRequest) =>
    request<RunAccepted>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/counterfactual`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  getRun: (runId: string) =>
    request<RunStatus>(`/api/v1/runs/${encodeURIComponent(runId)}`),
  getRunFrames: (runId: string) =>
    request<ProvenanceEnvelope<GeoJSONFeatureCollection>>(
      `/api/v1/runs/${encodeURIComponent(runId)}/frames`,
    ),
  subscribeRunEvents(runId: string, onUpdate: (update: RunStatus) => void, onError?: () => void) {
    const events = new EventSource(
      `${apiBaseUrl}/api/v1/runs/${encodeURIComponent(runId)}/events`,
    );
    events.onmessage = (event) => onUpdate(JSON.parse(event.data) as RunStatus);
    events.onerror = () => onError?.();
    return events;
  },
  exportReportJson: (incidentId: string, runId?: string) =>
    request<JsonRecord>(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/report/json${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`,
    ),
  exportReportPdf: (incidentId: string, runId?: string) =>
    requestBlob(
      `/api/v1/incidents/${encodeURIComponent(incidentId)}/report/pdf${runId ? `?run_id=${encodeURIComponent(runId)}` : ""}`,
    ),
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
