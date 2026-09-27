from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceTag(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    SIMULATED = "SIMULATED"
    COMPARED = "COMPARED"
    SYSTEM = "SYSTEM"
    GAP = "GAP"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class Provenance(BaseModel):
    """Attached to every artifact-derived payload. Never optional."""

    tag: EvidenceTag
    source: str  # "Sentinel-1 S1A_IW_20260910T0413"
    generated_at: datetime
    model_run_id: str | None = None  # "OD-ENS-0914-07"
    assumptions: list[str] = Field(default_factory=list)
    degraded_inputs: list[str] = Field(default_factory=list)
