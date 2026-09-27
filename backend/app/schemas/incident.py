from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import Envelope
from .vessel import VesselCandidate
from ..vocabulary.guard import SafeText


class ArtifactIncident(BaseModel):
    incident_id: str
    title: SafeText
    scene_id: str
    satellite: str
    aoi: list[list[float]]
    detected_at: datetime
    processed_at: datetime
    model_run_id: str


class MapLayers(BaseModel):
    observed_slick: Envelope[dict]
    ais_tracks: Envelope[dict]
    origin_field: Envelope[dict]


class ArtifactHindcast(BaseModel):
    model_config = ConfigDict(extra="allow")

    center: tuple[float, float]
    radius_km: float = Field(gt=0)
    release_window_start: datetime
    release_window_end: datetime
    model: str
    is_fallback: bool = False
    warnings: list[str] = Field(default_factory=list)


class CandidateArtifactSet(BaseModel):
    candidates: list[VesselCandidate]
    raw_candidate_count: int = Field(ge=0)
    uncertainty_reserve: list[VesselCandidate] = Field(default_factory=list)


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[dict[str, Any]]