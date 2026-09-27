import asyncio

import pytest
from pathlib import Path

from app.cache.store import RunCache
from app.config import Settings, project_root
from app.jobs.registry import RunRegistry, RunState
from app.schemas.evidence import AttributionOutcome
from app.schemas.incident import CandidateArtifactSet
from app.schemas.simulation import ArtifactRun
from app.services.artifacts import Artifacts
from app.services.attribution import build_fixture_attribution
from app.models import CandidateEvaluation, CandidateInput, ConsistencyComponents
from app.services import assess, rank_candidates, source_consistency_score


def candidate(vessel_id: str, distance: float, risk: float = 0, behavior: float = 0) -> CandidateInput:
    return CandidateInput(
        vessel_id=vessel_id, name=vessel_id, vessel_type="Tanker", mmsi="123456789",
        latest_position=(92.54, 12.31), ais_integrity="consistent", distance_to_origin_km=distance,
        trajectory_alignment=0.9, speed_profile_alignment=0.8,
        vessel_risk_profile=risk, behavioral_anomaly_score=behavior,
    )


def test_risk_and_behavior_do_not_change_physics_score() -> None:
    normal = candidate("NORMAL", 10)
    high_risk = candidate("RISK", 10, risk=1, behavior=1)
    ranking = rank_candidates([normal, high_risk], "SIH26143-001", 2)
    scores = {item.vessel.vessel_id: item.attribution_score for item in ranking.candidates}
    priorities = {item.vessel.vessel_id: item.compute_priority for item in ranking.candidates}
    assert scores["NORMAL"] == scores["RISK"]
    assert priorities["RISK"] > priorities["NORMAL"]


def test_source_score_is_weighted_and_bounded() -> None:
    score = source_consistency_score(ConsistencyComponents(
        spatial_iou=1, centroid_match=1, shape_match=1, area_curve_dtw=1
    ))
    assert score == 1


def test_low_pool_returns_explicit_null_result() -> None:
    ranking = rank_candidates([candidate("LOW", 90)], "SIH26143-001", 1)
    result = assess([CandidateEvaluation(candidate=ranking.candidates[0], source_consistency_score=0.2)], Settings(source_score_threshold=0.95))
    assert result.state == "no_sufficiently_consistent_vessel"
    assert "NO SUFFICIENTLY CONSISTENT VESSEL IDENTIFIED" in result.message


def test_run_registry_publishes_status_and_cached_result() -> None:
    async def exercise_registry() -> None:
        registry = RunRegistry()
        run = registry.create()
        updates: asyncio.Queue[dict] = asyncio.Queue()
        run.subscribers.append(updates)

        await registry.publish(
            run,
            state=RunState.RUNNING,
            progress=0.5,
            message="Loaded stored frame",
            result={"frame_count": 2},
        )

        update = await updates.get()
        assert update["run_id"] == run.run_id
        assert update["state"] == RunState.RUNNING
        assert update["progress"] == 0.5
        assert update["cached"] is False
        assert update["result"] == {"frame_count": 2}

    asyncio.run(exercise_registry())


def test_run_cache_round_trip_and_safe_key_handling(tmp_path) -> None:
    cache = RunCache(tmp_path)
    key = cache.key(
        "SIH26143-2025-001",
        "563214000",
        "2025-09-08T16:00:00+00:00",
        "cmes-era5-v1",
    )
    payload = {"run_id": "OD-ENS-001", "frames": []}

    assert len(key) == 64
    assert cache.key("another-incident", "563214000", "2025-09-08T16:00:00+00:00", "cmes-era5-v1") != key
    cache.put(key, payload)
    assert cache.get(key) == payload
    assert cache.get("../outside") is None
    with pytest.raises(ValueError):
        cache.put("../outside", payload)

    (tmp_path / f"{key}.json").write_text("not-json", encoding="utf-8")
    assert cache.get(key) is None


def test_fixture_attribution_uses_only_stored_candidate_run() -> None:
    artifacts = Artifacts(project_root / "data")
    candidates = CandidateArtifactSet.model_validate(
        artifacts.load_candidates("SIH26143-2025-001")
    )
    run = ArtifactRun.model_validate(
        artifacts.load_run("SIH26143-2025-001", "OD-ENS-001")
    )

    result = build_fixture_attribution(candidates, run, Settings())

    assert result.attribution.outcome is AttributionOutcome.SUPPORTS_INVESTIGATION
    assert result.attribution.top is not None
    assert [candidate.mmsi for candidate in result.attribution.top] == ["563214000"]
    assert result.attribution.top[0].consistency_score == 0.82
    assert result.attribution.gap == 0.08
    assert result.dossier is not None
    assert any(line.tag == "RISK_CONTEXT" for line in result.dossier.lines)
    assert any(line.tag == "PHYSICS" for line in result.dossier.lines)


def test_fixture_attribution_returns_null_without_a_completed_run() -> None:
    artifacts = Artifacts(project_root / "data")
    candidates = CandidateArtifactSet.model_validate(
        artifacts.load_candidates("SIH26143-2025-001")
    )

    result = build_fixture_attribution(candidates, None, Settings())

    assert result.attribution.outcome is AttributionOutcome.NULL_STATE
    assert result.attribution.top is None
    assert result.dossier is None
