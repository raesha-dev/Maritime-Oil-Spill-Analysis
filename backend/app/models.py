from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


Score = Annotated[float, Field(ge=0, le=1)]
Coordinate = tuple[Annotated[float, Field(ge=-180, le=180)], Annotated[float, Field(ge=-90, le=90)]]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class HealthResponse(StrictModel):
    status: Literal["ok"] = "ok"
    service: Literal["spill-forensics-api"] = "spill-forensics-api"
    version: str


class IncidentCreate(StrictModel):
    incident_id: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{2,63}$")
    title: str = Field(min_length=3, max_length=160)
    aoi: list[Coordinate] = Field(min_length=3, max_length=500)
    detected_at: datetime

    @field_validator("detected_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("detected_at must include a timezone")
        return value


class Incident(IncidentCreate):
    created_at: datetime
    updated_at: datetime


class DetectionCreate(StrictModel):
    scene_id: str = Field(min_length=3, max_length=100)
    satellite: Literal["Sentinel-1"]
    acquired_at: datetime
    centroid: Coordinate
    area_km2: Annotated[float, Field(gt=0, le=1_000_000)]
    oil_confidence: Score
    classification: Literal["oil", "algae", "low_wind", "other"]
    confidence_tier: Literal["high", "medium", "low"]
    observed_polygon: list[Coordinate] = Field(min_length=3, max_length=2_000)

    @field_validator("acquired_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("acquired_at must include a timezone")
        return value


class Detection(DetectionCreate):
    id: UUID
    incident_id: str
    created_at: datetime
    pipeline_status: Literal["proceed", "validate", "stopped"]


class HindcastRequest(StrictModel):
    detection_id: UUID
    current_knots: Annotated[float, Field(ge=0, le=20)]
    current_bearing_degrees: Annotated[float, Field(ge=0, lt=360)]
    wind_knots: Annotated[float, Field(ge=0, le=100)]
    wind_bearing_degrees: Annotated[float, Field(ge=0, lt=360)]
    lookback_hours: Annotated[int, Field(ge=1, le=168)] = 18
    ensemble_size: Annotated[int, Field(ge=1, le=100)] = 10


class OriginEstimate(StrictModel):
    center: Coordinate
    radius_km: Annotated[float, Field(gt=0)]
    release_window_start: datetime
    release_window_end: datetime
    probability_contours: list[list[Coordinate]]
    model: str = Field(min_length=3, max_length=100)
    is_fallback: bool = False
    warnings: list[str] = Field(default_factory=list, max_length=10)


class AISIntegrity(str, Enum):
    consistent = "consistent"
    gap = "gap"
    inconsistent = "inconsistent"
    insufficient_evidence = "insufficient_evidence"


class VesselContext(StrictModel):
    vessel_id: str = Field(pattern=r"^[A-Z0-9_-]{3,64}$")
    name: str = Field(min_length=1, max_length=120)
    vessel_type: str = Field(min_length=2, max_length=60)
    mmsi: str = Field(pattern=r"^\d{9}$")
    imo: str | None = Field(default=None, pattern=r"^\d{7}$")
    latest_position: Coordinate
    ais_integrity: AISIntegrity
    behavioral_anomaly_score: Score = 0
    vessel_risk_profile: Score = 0


class CandidateInput(VesselContext):
    distance_to_origin_km: Annotated[float, Field(ge=0, le=10_000)]
    trajectory_alignment: Score
    speed_profile_alignment: Score


class Candidate(StrictModel):
    vessel: VesselContext
    distance_to_origin_km: float
    trajectory_alignment: Score
    speed_profile_alignment: Score
    attribution_score: Score
    compute_priority: Score
    rank: Annotated[int, Field(ge=1)]


class CandidateRankingRequest(StrictModel):
    incident_id: str
    candidates: list[CandidateInput] = Field(min_length=1, max_length=100)
    shortlist_size: Annotated[int, Field(ge=1, le=10)] = 5


class CandidateRanking(StrictModel):
    incident_id: str
    candidates: list[Candidate]
    uncertainty_reserve: list[Candidate]
    raw_candidate_count: int


class ConsistencyComponents(StrictModel):
    spatial_iou: Score
    centroid_match: Score
    shape_match: Score
    area_curve_dtw: Score


class SimulationRequest(StrictModel):
    incident_id: str
    candidate: Candidate
    release_time: datetime
    environment_cache_key: str = Field(min_length=8, max_length=200)
    components: ConsistencyComponents

    @field_validator("release_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("release_time must include a timezone")
        return value


class SimulationFrame(StrictModel):
    hour: Literal[0, 6, 12, 24]
    geojson: dict[str, Any]


class SimulationResult(StrictModel):
    id: UUID
    run_id: UUID
    incident_id: str
    candidate_id: str
    source_consistency_score: Score
    components: ConsistencyComponents
    cache_key: str
    cached: bool
    provider: str
    frames: list[SimulationFrame] = Field(min_length=4, max_length=4)
    created_at: datetime


class AssessmentState(str, Enum):
    further_investigation = "further_investigation"
    no_sufficiently_consistent_vessel = "no_sufficiently_consistent_vessel"
    expand_candidate_pool = "expand_candidate_pool"


class Assessment(StrictModel):
    state: AssessmentState
    top_candidate: Candidate | None
    message: str
    dossier: list[str]


class CandidateEvaluation(StrictModel):
    candidate: Candidate
    source_consistency_score: Score


class AssessmentRequest(StrictModel):
    candidates: list[CandidateEvaluation] = Field(min_length=1, max_length=100)


class EvidenceKind(str, Enum):
    observed = "OBSERVED"
    inferred = "INFERRED"
    simulated = "SIMULATED"
    system = "SYSTEM"


class EvidenceEventCreate(StrictModel):
    incident_id: str
    occurred_at: datetime
    kind: EvidenceKind
    description: str = Field(min_length=3, max_length=500)
    source_ref: str = Field(min_length=3, max_length=200)


class EvidenceEvent(EvidenceEventCreate):
    id: UUID
    created_at: datetime


class MessageRole(str, Enum):
    analyst = "analyst"
    system = "system"
    model = "model"


class MessageCreate(StrictModel):
    incident_id: str
    role: MessageRole
    body: str = Field(min_length=1, max_length=4_000)
    correlation_id: UUID | None = None


class Message(MessageCreate):
    id: UUID
    created_at: datetime


class DashboardSnapshot(StrictModel):
    """The single read contract consumed by the dynamic analyst dashboard."""

    incident: Incident
    detection: Detection | None
    hindcast: OriginEstimate | None
    ranking: CandidateRanking | None
    simulations: list[SimulationResult]
    assessment: Assessment | None
    evidence_events: list[EvidenceEvent]
    updated_at: datetime


class ApiEnvelope(StrictModel):
    request_id: UUID = Field(default_factory=uuid4)
    data: dict | list | str | None = None
