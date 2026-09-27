from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from ..vocabulary.guard import SafeText


class AISIntegrity(str, Enum):
    CONSISTENT = "CONSISTENT"
    GAP = "GAP"  # amber
    INCONSISTENT = "INCONSISTENT"  # red
    INSUFFICIENT = "INSUFFICIENT"  # grey


class VesselRiskProfile(BaseModel):
    """Context only. Never an input to Source Consistency."""

    built_year: int | None = None
    hull_type: Literal["SINGLE", "DOUBLE", "UNKNOWN"] | None = None
    flag: str | None = None  # ISO-2, e.g. "IN" — not a flag emoji
    psc_detentions_3yr: int | None = None
    sanctions_listed: bool | None = None


class BehavioralFlag(BaseModel):
    kind: Literal["SPEED_DROP", "LOITERING", "ROUTE_DEVIATION", "AIS_GAP_TIMING"]
    detail: SafeText
    at: datetime  # rendered via templates only


class VesselCandidate(BaseModel):
    rank: int
    mmsi: str
    imo: str | None = None
    name: SafeText
    vessel_type: str
    proximity_km: float
    ais_integrity: AISIntegrity
    consistency_score: float | None = None  # None until simulated
    in_uncertainty_reserve: bool = False
    risk_profile: VesselRiskProfile | None = None
    behavioral_flags: list[BehavioralFlag] = Field(default_factory=list)
