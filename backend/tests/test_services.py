from app.config import Settings
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
