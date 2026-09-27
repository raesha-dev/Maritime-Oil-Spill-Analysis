from __future__ import annotations

from datetime import datetime

from ..config import Settings
from ..models import (
    AISIntegrity,
    AssessmentState,
    Candidate,
    CandidateRanking,
    ConsistencyComponents,
    DashboardAssessment,
    DashboardDetection,
    DashboardIncident,
    DashboardSimulation,
    DashboardSnapshot,
    OriginEstimate,
    VesselContext,
)
from ..schemas.detection import ArtifactDetection
from ..schemas.incident import ArtifactHindcast, ArtifactIncident, CandidateArtifactSet
from ..schemas.simulation import ArtifactRun
from .artifacts import Artifacts
from .attribution import build_fixture_attribution
from ..models import EvidenceEvent


def build_artifact_dashboard(
    incident_id: str,
    artifacts: Artifacts,
    settings: Settings,
    evidence_events: list[EvidenceEvent],
) -> DashboardSnapshot:
    incident = ArtifactIncident.model_validate(artifacts.load_incident(incident_id))
    detection_data = ArtifactDetection.model_validate(
        artifacts.load_detection(incident_id)
    )
    hindcast_data = ArtifactHindcast.model_validate(
        artifacts.load_hindcast(incident_id)
    )
    candidate_data = CandidateArtifactSet.model_validate(
        artifacts.load_candidates(incident_id)
    )
    tracks = artifacts.load_ais_tracks(incident_id)
    positions = {
        feature.get("properties", {}).get("mmsi"): feature.get("geometry", {}).get(
            "coordinates", []
        )[-1]
        for feature in tracks.get("features", [])
        if feature.get("geometry", {}).get("coordinates")
    }
    runs = [
        ArtifactRun.model_validate(run)
        for run in artifacts.list_runs(incident_id)
    ]
    runs_by_mmsi = {run.mmsi: run for run in runs}

    candidates: list[Candidate] = []
    for vessel in candidate_data.candidates + candidate_data.uncertainty_reserve:
        run = runs_by_mmsi.get(vessel.mmsi)
        candidates.append(
            Candidate(
                vessel=VesselContext(
                    vessel_id=run.candidate_id if run else vessel.mmsi,
                    name=vessel.name,
                    vessel_type=vessel.vessel_type,
                    mmsi=vessel.mmsi,
                    imo=vessel.imo,
                    latest_position=tuple(positions[vessel.mmsi])
                    if vessel.mmsi in positions
                    else None,
                    ais_integrity=AISIntegrity(
                        {
                            "INSUFFICIENT": "insufficient_evidence",
                        }.get(
                            vessel.ais_integrity.value,
                            vessel.ais_integrity.value.lower(),
                        )
                    ),
                    behavioral_anomaly_score=None,
                    vessel_risk_profile=None,
                ),
                distance_to_origin_km=vessel.proximity_km,
                attribution_score=None,
                compute_priority=None,
                source_consistency_score=(
                    run.source_consistency_score if run is not None else None
                ),
                rank=vessel.rank,
            )
        )

    reserve_mmsi = {
        vessel.mmsi for vessel in candidate_data.uncertainty_reserve
    }
    ranking = CandidateRanking(
        incident_id=incident_id,
        candidates=[vessel for vessel in candidates if vessel.vessel.mmsi not in reserve_mmsi],
        uncertainty_reserve=[vessel for vessel in candidates if vessel.vessel.mmsi in reserve_mmsi],
        raw_candidate_count=candidate_data.raw_candidate_count,
    )

    simulations = [
        DashboardSimulation(
            id=run.run_id,
            candidate_id=run.candidate_id,
            source_consistency_score=run.source_consistency_score,
            components=ConsistencyComponents(
                **{name: component.value for name, component in run.components.items()}
            ),
        )
        for run in runs
    ]
    selected_run = runs[0] if len(runs) == 1 else None
    attribution = build_fixture_attribution(candidate_data, selected_run, settings)
    assessment = DashboardAssessment(
        state={
            "SUPPORTS_INVESTIGATION": AssessmentState.further_investigation,
            "AMBIGUOUS": AssessmentState.expand_candidate_pool,
            "NULL_STATE": AssessmentState.no_sufficiently_consistent_vessel,
        }[attribution.attribution.outcome.value],
        message=attribution.attribution.message,
        dossier=(
            [line.text for line in attribution.dossier.lines]
            if attribution.dossier is not None
            else []
        ),
    )

    update_times: list[datetime] = [incident.processed_at]
    update_times.extend(event.created_at for event in evidence_events)
    update_times.extend(run.generated_at for run in runs)

    return DashboardSnapshot(
        incident=DashboardIncident(
            incident_id=incident.incident_id,
            title=incident.title,
            aoi=incident.aoi,
            detected_at=incident.detected_at,
        ),
        detection=DashboardDetection(
            id=None,
            scene_id=detection_data.scene_id,
            satellite=detection_data.satellite,
            acquired_at=detection_data.acquired_at,
            centroid=tuple(detection_data.centroid),
            area_km2=detection_data.area_km2,
            oil_confidence=detection_data.oil_confidence,
            classification=detection_data.classification,
            confidence_tier=detection_data.confidence_tier,
            pipeline_status=detection_data.pipeline_status,
        ),
        hindcast=OriginEstimate(
            center=hindcast_data.center,
            radius_km=hindcast_data.radius_km,
            release_window_start=hindcast_data.release_window_start,
            release_window_end=hindcast_data.release_window_end,
            probability_contours=[],
            model=hindcast_data.model,
            is_fallback=hindcast_data.is_fallback,
            warnings=hindcast_data.warnings,
        ),
        ranking=ranking,
        simulations=simulations,
        assessment=assessment,
        evidence_events=evidence_events,
        updated_at=max(update_times),
    )