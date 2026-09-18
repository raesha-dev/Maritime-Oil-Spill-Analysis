from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from .common import Confidence


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
    incident_id: str
    mmsi: str
    release_time: str
    environment: str = "cmes-era5-v1"


class RunAccepted(BaseModel):
    run_id: str
    cached: bool = False
