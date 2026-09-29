from __future__ import annotations

from datetime import timedelta
from hashlib import sha256
from math import cos, pi, sin
from typing import Protocol

from .config import Settings
from .models import (
    Assessment,
    AssessmentState,
    Candidate,
    CandidateInput,
    CandidateRanking,
    ConsistencyComponents,
    Detection,
    HindcastRequest,
    OriginEstimate,
    CandidateEvaluation,
    SimulationFrame,
    SimulationRequest,
)


class DriftEngine(Protocol):
    """Replace this adapter with OpenDrift without changing HTTP contracts."""

    def hindcast(self, detection: Detection, request: HindcastRequest) -> OriginEstimate: ...


class DeterministicDriftAdapter:
    """A repeatable local adapter for UI development; it is not a physics model."""

    def hindcast(self, detection: Detection, request: HindcastRequest) -> OriginEstimate:
        longitude, latitude = detection.centroid
        hours = request.lookback_hours
        # Move from observed centroid opposite the combined current/wind vector.
        current_km = request.current_knots * 1.852 * hours
        wind_km = request.wind_knots * 1.852 * hours * 0.03
        bearing = request.current_bearing_degrees * pi / 180
        wind_bearing = request.wind_bearing_degrees * pi / 180
        east_km = -(current_km * sin(bearing) + wind_km * sin(wind_bearing))
        north_km = -(current_km * cos(bearing) + wind_km * cos(wind_bearing))
        origin_latitude = latitude + north_km / 111.32
        origin_longitude = longitude + east_km / max(0.01, 111.32 * cos(latitude * pi / 180))
        radius = max(2.0, (current_km + wind_km) / max(3, request.ensemble_size))
        center = (round(origin_longitude, 6), round(origin_latitude, 6))
        contour = self._circle(center, radius, 24)
        return OriginEstimate(
            center=center,
            radius_km=round(radius, 2),
            release_window_start=detection.acquired_at - timedelta(hours=hours),
            release_window_end=detection.acquired_at - timedelta(hours=max(1, hours - 4)),
            probability_contours=[contour],
            model="deterministic-hindcast-adapter",
            is_fallback=True,
            warnings=[
                "Deterministic development fallback: this result is not an OpenDrift or scientific forecast."
            ],
        )

    @staticmethod
    def _circle(center: tuple[float, float], radius_km: float, steps: int) -> list[tuple[float, float]]:
        longitude, latitude = center
        return [
            (
                round(longitude + radius_km * sin((index / steps) * 2 * pi) / (111.32 * cos(latitude * pi / 180)), 6),
                round(latitude + radius_km * cos((index / steps) * 2 * pi) / 111.32, 6),
            )
            for index in range(steps + 1)
        ]


class CounterfactualSimulationProvider:
    """Deterministic provider boundary for candidate-specific counterfactual runs."""

    name = "deterministic-counterfactual-provider"

    def simulate(self, request: SimulationRequest) -> list[SimulationFrame]:
        longitude, latitude = request.candidate.vessel.latest_position
        return [
            SimulationFrame(
                hour=hour,
                geojson={
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {
                            "candidate_id": request.candidate.vessel.vessel_id,
                            "hour": hour,
                            "source": "counterfactual",
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [self._circle(
                                (longitude + hour * 0.002, latitude + hour * 0.001),
                                0.01 + hour * 0.00035,
                            )],
                        },
                    }],
                },
            )
            for hour in (0, 6, 12, 24)
        ]

    @staticmethod
    def _circle(center: tuple[float, float], radius: float) -> list[list[float]]:
        longitude, latitude = center
        return [
            [
                round(longitude + radius * sin((index / 24) * 2 * pi), 6),
                round(latitude + radius * cos((index / 24) * 2 * pi), 6),
            ]
            for index in range(25)
        ]


def rank_candidates(request: list[CandidateInput], incident_id: str, shortlist_size: int) -> CandidateRanking:
    ranked: list[Candidate] = []
    for item in request:
        # Attribution uses only proximity/trajectory/speed evidence. BAS/VRP are priority-only.
        proximity = max(0.0, 1 - item.distance_to_origin_km / 100)
        physics = round(0.45 * proximity + 0.35 * item.trajectory_alignment + 0.20 * item.speed_profile_alignment, 4)
        priority = round(0.70 * physics + 0.20 * item.behavioral_anomaly_score + 0.10 * item.vessel_risk_profile, 4)
        ranked.append(Candidate(
            vessel=item.model_dump(exclude={"distance_to_origin_km", "trajectory_alignment", "speed_profile_alignment"}),
            distance_to_origin_km=item.distance_to_origin_km,
            trajectory_alignment=item.trajectory_alignment,
            speed_profile_alignment=item.speed_profile_alignment,
            attribution_score=physics,
            compute_priority=priority,
            rank=1,
        ))
    ranked.sort(key=lambda candidate: (-candidate.compute_priority, candidate.vessel.vessel_id))
    ranked = [candidate.model_copy(update={"rank": index}) for index, candidate in enumerate(ranked, 1)]
    return CandidateRanking(
        incident_id=incident_id,
        candidates=ranked[:shortlist_size],
        uncertainty_reserve=ranked[shortlist_size:],
        raw_candidate_count=len(ranked),
    )


def source_consistency_score(components: ConsistencyComponents) -> float:
    # The only source score formula. It cannot consume risk or behavior inputs.
    return round(
        0.35 * components.spatial_iou
        + 0.25 * components.centroid_match
        + 0.20 * components.shape_match
        + 0.20 * components.area_curve_dtw,
        4,
    )


def simulation_cache_key(request: SimulationRequest) -> str:
    stable = "|".join((
        request.candidate.vessel.vessel_id,
        request.environment_cache_key,
        request.release_time.isoformat(),
        request.components.model_dump_json(),
    ))
    return sha256(stable.encode("utf-8")).hexdigest()


def assess(candidates: list[CandidateEvaluation], settings: Settings) -> Assessment:
    if not candidates:
        return Assessment(
            state=AssessmentState.no_sufficiently_consistent_vessel,
            top_candidate=None,
            message="NO SUFFICIENTLY CONSISTENT VESSEL IDENTIFIED - Origin estimate may be unreliable; recommend re-examining detection and hindcast inputs.",
            dossier=[],
        )
    top = candidates[0]
    runner_up = candidates[1] if len(candidates) > 1 else None
    gap = top.source_consistency_score - (runner_up.source_consistency_score if runner_up else 0)
    if top.source_consistency_score < settings.source_score_threshold:
        return Assessment(
            state=AssessmentState.no_sufficiently_consistent_vessel,
            top_candidate=top.candidate,
            message="NO SUFFICIENTLY CONSISTENT VESSEL IDENTIFIED - Origin estimate may be unreliable; recommend re-examining detection and hindcast inputs.",
            dossier=[],
        )
    if runner_up and gap < settings.minimum_score_gap:
        return Assessment(
            state=AssessmentState.expand_candidate_pool,
            top_candidate=top.candidate,
            message="The leading candidates are too close to distinguish reliably. Expand the candidate pool and escalate to a human investigator.",
            dossier=dossier_for(top.candidate),
        )
    return Assessment(
        state=AssessmentState.further_investigation,
        top_candidate=top.candidate,
        message="This result supports further investigation. It does not establish causation by itself.",
        dossier=dossier_for(top.candidate),
    )


def dossier_for(candidate: Candidate) -> list[str]:
    return [
        f"{candidate.vessel.name} is a ranked candidate present in the origin space-time window.",
        "Its trajectory is consistent with the evaluated release window.",
        "The result raises the possibility that this candidate merits further investigation.",
        "The assessment does not rule out other vessels or an unreliable origin estimate.",
    ]
