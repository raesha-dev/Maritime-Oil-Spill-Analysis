from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel

from ..vocabulary.guard import SafeText
from .vessel import VesselCandidate


class DossierLine(BaseModel):
    tag: Literal["PHYSICS", "BEHAVIORAL", "RISK_CONTEXT"]
    text: SafeText


class Dossier(BaseModel):
    vessel_name: str
    headline: SafeText
    lines: list[DossierLine]
    verdict: SafeText


class AttributionOutcome(str, Enum):
    SUPPORTS_INVESTIGATION = "SUPPORTS_INVESTIGATION"
    AMBIGUOUS = "AMBIGUOUS"
    NULL_STATE = "NULL_STATE"


class AttributionResult(BaseModel):
    outcome: AttributionOutcome
    message: SafeText
    top: list[VesselCandidate] | None = None
    gap: float | None = None


class AttributionBundle(BaseModel):
    attribution: AttributionResult
    dossier: Dossier | None = None
