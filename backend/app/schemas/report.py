from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .common import Envelope
from .detection import ArtifactDetection
from .evidence import AttributionBundle
from .incident import ArtifactHindcast, ArtifactIncident, CandidateArtifactSet
from .simulation import ArtifactRun
from ..models import EvidenceEvent
from ..vocabulary.guard import SafeText


class ForensicReport(BaseModel):
    generated_at: datetime
    incident: Envelope[ArtifactIncident]
    detection: Envelope[ArtifactDetection] | None = None
    hindcast: Envelope[ArtifactHindcast] | None = None
    candidates: Envelope[CandidateArtifactSet] | None = None
    attribution: Envelope[AttributionBundle]
    evidence: Envelope[list[EvidenceEvent]]
    runs: list[Envelope[ArtifactRun]] = Field(default_factory=list)
    unavailable_artifacts: list[SafeText] = Field(default_factory=list)