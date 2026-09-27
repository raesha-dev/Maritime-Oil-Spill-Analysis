"""Tests for schema definitions."""

from datetime import datetime

import pytest

from app.schemas import (
    AttributionOutcome,
    AttributionResult,
    BehavioralFlag,
    ConsistencyScore,
    Confidence,
    Dossier,
    DossierLine,
    EvidenceTag,
    Provenance,
    RunAccepted,
    RunRequest,
    RunStatus,
    ScoreComponent,
    SimulationFrame,
    VesselCandidate,
    VesselRiskProfile,
    AISIntegrity,
)


def test_provenance_schema() -> None:
    """Provenance must have all required fields."""
    provenance = Provenance(
        tag=EvidenceTag.OBSERVED,
        source="Sentinel-1 S1A_IW_20260910T0413",
        generated_at=datetime(2026, 9, 10, 4, 13, 0),
        model_run_id="OD-ENS-0914-07",
        assumptions=["ERA5 wind data used"],
        degraded_inputs=["cloud_mask_missing"],
    )
    assert provenance.tag == EvidenceTag.OBSERVED
    assert provenance.source == "Sentinel-1 S1A_IW_20260910T0413"
    assert provenance.model_run_id == "OD-ENS-0914-07"
    assert provenance.assumptions == ["ERA5 wind data used"]
    assert provenance.degraded_inputs == ["cloud_mask_missing"]


def test_vessel_candidate_schema() -> None:
    """VesselCandidate must have all required fields."""
    BehavioralFlag.model_rebuild()
    VesselCandidate.model_rebuild()
    candidate = VesselCandidate(
        rank=1,
        mmsi="123456789",
        name="OCEAN PRIDE",
        vessel_type="Tanker",
        proximity_km=12.5,
        ais_integrity=AISIntegrity.CONSISTENT,
        consistency_score=0.82,
        in_uncertainty_reserve=False,
        risk_profile=VesselRiskProfile(
            built_year=2005,
            hull_type="SINGLE",
            flag="IN",
            psc_detentions_3yr=2,
            sanctions_listed=False,
        ),
        behavioral_flags=[
            BehavioralFlag(
                kind="SPEED_DROP",
                detail="Unexplained stop before release window",
                at=datetime(2025, 9, 8, 14, 20, 0),
            )
        ],
    )
    assert candidate.rank == 1
    assert candidate.name == "OCEAN PRIDE"
    assert candidate.proximity_km == 12.5
    assert candidate.ais_integrity == AISIntegrity.CONSISTENT
    assert candidate.consistency_score == 0.82
    assert len(candidate.behavioral_flags) == 1
    assert candidate.in_uncertainty_reserve is False


def test_score_component_schema() -> None:
    """ScoreComponent must have label, value, and uncertainty."""
    component = ScoreComponent(
        label="Spatial Overlap (IoU)",
        value=0.89,
        uncertainty=0.04,
    )
    assert component.label == "Spatial Overlap (IoU)"
    assert component.value == 0.89
    assert component.uncertainty == 0.04


def test_consistency_score_schema() -> None:
    """ConsistencyScore must have four components and confidence."""
    score = ConsistencyScore(
        overall=0.82,
        confidence=Confidence.HIGH,
        gap_to_next_best=0.08,
        components=[
            ScoreComponent(label="Spatial Overlap (IoU)", value=0.89, uncertainty=0.04),
            ScoreComponent(label="Centroid Match", value=0.84, uncertainty=0.05),
            ScoreComponent(label="Area Evolution", value=0.78, uncertainty=0.06),
            ScoreComponent(label="Shape Similarity", value=0.72, uncertainty=0.07),
        ],
    )
    assert score.overall == 0.82
    assert score.confidence == Confidence.HIGH
    assert score.gap_to_next_best == 0.08
    assert len(score.components) == 4


def test_simulation_frame_schema() -> None:
    """SimulationFrame must have offset_hours and simulated_geojson."""
    frame = SimulationFrame(
        offset_hours=12,
        simulated_geojson={"type": "Polygon", "coordinates": [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]},
        observed_geojson={"type": "Polygon", "coordinates": [[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9], [0.1, 0.1]]},
    )
    assert frame.offset_hours == 12
    assert frame.simulated_geojson["type"] == "Polygon"
    assert frame.observed_geojson is not None


def test_run_request_schema() -> None:
    """RunRequest must have incident_id, mmsi, release_time, and environment."""
    request = RunRequest(
        incident_id="SIH26143-2025-001",
        mmsi="123456789",
        release_time="2025-09-08T16:00:00Z",
        environment="cmes-era5-v1",
    )
    assert request.incident_id == "SIH26143-2025-001"
    assert request.mmsi == "123456789"
    assert request.release_time == "2025-09-08T16:00:00Z"
    assert request.environment == "cmes-era5-v1"


def test_run_accepted_schema() -> None:
    """RunAccepted must have run_id and cached flag."""
    response = RunAccepted(run_id="OD-ENS-12345678", cached=False)
    assert response.run_id == "OD-ENS-12345678"
    assert response.cached is False
    cached_response = RunAccepted(run_id="OD-ENS-87654321", cached=True)
    assert cached_response.cached is True


def test_dossier_schema() -> None:
    """Dossier must have vessel_name, headline, lines, and verdict."""
    dossier = Dossier(
        vessel_name="OCEAN PRIDE",
        headline="Best Candidate for Bay of Bengal Spill",
        lines=[
            DossierLine(tag="PHYSICS", text="Simulated release is consistent with observed slick"),
            DossierLine(tag="BEHAVIORAL", text="AIS shows no anomalous behavior"),
            DossierLine(tag="RISK_CONTEXT", text="Vessel has clean PSC record"),
        ],
        verdict="This result supports further investigation. It does not identify this vessel as the source.",
    )
    assert dossier.vessel_name == "OCEAN PRIDE"
    assert dossier.headline == "Best Candidate for Bay of Bengal Spill"
    assert len(dossier.lines) == 3
    assert "supports further investigation" in dossier.verdict.lower()


def test_attribution_result_schema() -> None:
    """AttributionResult must have outcome, message, top candidates, and gap."""
    AttributionResult.model_rebuild()
    result = AttributionResult(
        outcome=AttributionOutcome.SUPPORTS_INVESTIGATION,
        message="This result supports further investigation.",
        top=[{
            "rank": 1,
            "mmsi": "123456789",
            "name": "OCEAN PRIDE",
            "vessel_type": "Tanker",
            "proximity_km": 12.5,
            "ais_integrity": "CONSISTENT",
            "consistency_score": 0.82,
        }],
        gap=0.08,
    )
    assert result.outcome == AttributionOutcome.SUPPORTS_INVESTIGATION
    assert result.message == "This result supports further investigation."
    assert len(result.top) == 1
    assert result.gap == 0.08


def test_attribution_null_state() -> None:
    """Null state attribution must have no top candidates."""
    result = AttributionResult(
        outcome=AttributionOutcome.NULL_STATE,
        message="No sufficiently consistent vessel identified.",
        top=None,
        gap=None,
    )
    assert result.outcome == AttributionOutcome.NULL_STATE
    assert result.top is None
    assert result.gap is None
