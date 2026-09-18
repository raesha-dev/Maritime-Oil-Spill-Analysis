from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel


class DossierLine(BaseModel):
    tag: Literal["PHYSICS", "BEHAVIORAL", "RISK_CONTEXT"]
    text: str  # Will be validated as SafeText by vocabulary guard


class Dossier(BaseModel):
    vessel_name: str
    headline: str
    lines: list[DossierLine]
    verdict: str


class AttributionOutcome(str, Enum):
    SUPPORTS_INVESTIGATION = "SUPPORTS_INVESTIGATION"
    AMBIGUOUS = "AMBIGUOUS"
    NULL_STATE = "NULL_STATE"


class AttributionResult(BaseModel):
    outcome: AttributionOutcome
    message: str
    top: list[dict] | None = None  # VesselCandidate data as dict
    gap: float | None = None
