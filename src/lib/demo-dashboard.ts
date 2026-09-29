import type { Candidate, DashboardSnapshot } from "./forensics-api";

const candidate = (
  rank: number,
  name: string,
  vesselType: string,
  distance: number,
  score: number,
  integrity: Candidate["vessel"]["ais_integrity"],
): Candidate => ({
  vessel: {
    vessel_id: name.replaceAll(" ", "_"),
    name,
    vessel_type: vesselType,
    mmsi: "563214000",
    imo: "9234567",
    latest_position: [92.54, 12.31],
    ais_integrity: integrity,
    behavioral_anomaly_score: 0.2,
    vessel_risk_profile: 0.3,
  },
  distance_to_origin_km: distance,
  trajectory_alignment: score,
  speed_profile_alignment: score,
  attribution_score: score,
  compute_priority: score,
  rank,
});

const candidates = [
  candidate(1, "OCEAN PRIDE", "Tanker", 12, 0.82, "consistent"),
  candidate(2, "EASTERN STAR", "Cargo", 18, 0.74, "gap"),
  candidate(3, "SEA VOYAGER", "Tanker", 25, 0.61, "consistent"),
  candidate(4, "AL ZUBARA", "Cargo", 28, 0.48, "gap"),
  candidate(5, "BLUE HORIZON", "Tanker", 31, 0.42, "inconsistent"),
];

/** Clearly labelled local fallback. It is never presented as a live model result. */
export const demoDashboard: DashboardSnapshot = {
  incident: {
    incident_id: "SIH26143-2025-001",
    title: "Bay of Bengal demonstration",
    detected_at: "2025-09-09T08:17:00Z",
    aoi: [
      [92, 12],
      [93, 12],
      [92.5, 13],
    ],
  },
  detection: {
    id: "demo-detection",
    satellite: "Sentinel-1",
    acquired_at: "2025-09-09T08:17:00Z",
    centroid: [92.861, 12.374],
    area_km2: 12.4,
    oil_confidence: 0.91,
    classification: "oil",
    confidence_tier: "high",
    pipeline_status: "proceed",
  },
  hindcast: {
    center: [92.54, 12.31],
    radius_km: 18,
    release_window_start: "2025-09-08T14:00:00Z",
    release_window_end: "2025-09-08T18:00:00Z",
    model: "demo fallback - not a scientific forecast",
    is_fallback: true,
    warnings: ["Local demo fallback: not a live satellite or scientific model output."],
  },
  ranking: { candidates, uncertainty_reserve: [], raw_candidate_count: 18 },
  simulations: [
    {
      id: "demo-simulation",
      run_id: "demo-simulation",
      incident_id: "SIH26143-2025-001",
      candidate_id: "OCEAN_PRIDE",
      source_consistency_score: 0.82,
      components: {
        spatial_iou: 0.89,
        centroid_match: 0.84,
        shape_match: 0.72,
        area_curve_dtw: 0.78,
      },
      cache_key: "demo",
      cached: false,
      provider: "demo-counterfactual-provider",
      frames: [0, 6, 12, 24].map((hour) => ({
        hour: hour as 0 | 6 | 12 | 24,
        geojson: {
          type: "FeatureCollection" as const,
          features: [],
        },
      })),
    },
  ],
  assessment: {
    state: "further_investigation",
    message:
      "This result supports further investigation. It does not establish causation by itself.",
    dossier: [
      "OCEAN PRIDE is a ranked candidate present in the origin space-time window.",
      "Its trajectory is consistent with the evaluated release window.",
      "The result raises the possibility that this candidate merits further investigation.",
      "The assessment does not rule out other vessels or an unreliable origin estimate.",
    ],
  },
  evidence_events: [
    {
      id: "1",
      occurred_at: "2025-09-08T14:20:00Z",
      kind: "OBSERVED",
      description: "Vessel enters probable origin region",
      source_ref: "demo-ais",
    },
    {
      id: "2",
      occurred_at: "2025-09-08T14:45:00Z",
      kind: "INFERRED",
      description: "Estimated release window",
      source_ref: "demo-hindcast",
    },
    {
      id: "3",
      occurred_at: "2025-09-08T15:00:00Z",
      kind: "SIMULATED",
      description: "Hypothetical release",
      source_ref: "demo-simulation",
    },
    {
      id: "4",
      occurred_at: "2025-09-09T08:17:00Z",
      kind: "OBSERVED",
      description: "Sentinel-1 detects slick",
      source_ref: "demo-sar",
    },
  ],
  updated_at: "2025-09-09T08:30:00Z",
};
