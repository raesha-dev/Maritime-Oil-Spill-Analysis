"""Schema definitions for the SpillTrack API."""

from .common import EvidenceTag, Provenance, Confidence, Envelope, SystemStatus
from .vessel import VesselCandidate, AISIntegrity, VesselRiskProfile, BehavioralFlag
from .simulation import (
    ConsistencyScore,
    ScoreComponent,
    SimulationFrame,
    RunStatus,
    RunRequest,
    RunAccepted,
    RunStatusResponse,
)
from .evidence import Dossier, DossierLine, AttributionResult, AttributionOutcome

__all__ = [
    # Common
    "EvidenceTag",
    "Provenance",
    "Confidence",
    "Envelope",
    "SystemStatus",
    # Vessel
    "VesselCandidate",
    "AISIntegrity",
    "VesselRiskProfile",
    "BehavioralFlag",
    # Simulation
    "ConsistencyScore",
    "ScoreComponent",
    "SimulationFrame",
    "RunStatus",
    "RunRequest",
    "RunAccepted",
    "RunStatusResponse",
    # Evidence
    "Dossier",
    "DossierLine",
    "AttributionResult",
    "AttributionOutcome",
]
from .detection import ArtifactDetection