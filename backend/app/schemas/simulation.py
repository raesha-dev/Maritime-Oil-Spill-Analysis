from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .common import Confidence
from ..vocabulary.guard import SafeText


class ScoreComponent(BaseModel):
    label: str  # "Spatial Overlap (IoU)"
    value: float
    uncertainty: float  # the "± 0.04" your metrics panel already shows


class ConsistencyScore(BaseModel):
    overall: float
    confidence: Confidence
    gap_to_next_best: float | None = None
    components: list[ScoreComponent]  # exactly four, always all four


class SimulationFrame(BaseModel):
    offset_hours: int  # 0, 6, 12, 24 — your frame strip
    simulated_geojson: dict
    observed_geojson: dict | None = None


class RunStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class RunRequest(BaseModel):
    mmsi: str
    release_time: datetime
    environment: str = "cmes-era5-v1"

    @field_validator("release_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("release_time must include a timezone")
        return value


class RunAccepted(BaseModel):
    run_id: str
    cached: bool = False


class RunStatusResponse(BaseModel):
    run_id: str
    state: RunStatus
    progress: float = Field(ge=0, le=1)
    message: SafeText
    cached: bool = False
    result: dict | None = None


class ArtifactScoreComponent(BaseModel):
    value: float = Field(ge=0, le=1)
    uncertainty: float = Field(ge=0, le=1)


class ArtifactRun(BaseModel):
    run_id: str
    candidate_id: str
    mmsi: str = Field(pattern=r"^\d{9}$")
    release_time: datetime
    environment: str
    source_consistency_score: float = Field(ge=0, le=1)
    components: dict[str, ArtifactScoreComponent]
    confidence: Confidence
    gap_to_next_best: float | None = Field(default=None, ge=0, le=1)
    generated_at: datetime
    model_run_id: str
    cached: bool

    @field_validator("release_time", "generated_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("run timestamps must include a timezone")
        return value

    @model_validator(mode="after")
    def require_all_score_components(self) -> "ArtifactRun":
        expected = {"spatial_iou", "centroid_match", "shape_match", "area_curve_dtw"}
        if set(self.components) != expected:
            raise ValueError("run artifact must contain all four score components")
        return self
