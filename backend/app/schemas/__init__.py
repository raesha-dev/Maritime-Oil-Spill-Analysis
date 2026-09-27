"""Schema definitions for the SpillTrack API."""

from .common import EvidenceTag, Provenance, Confidence
from .vessel import VesselCandidate, AISIntegrity, VesselRiskProfile, BehavioralFlag
from .simulation import (
    ConsistencyScore,
    ScoreComponent,
    SimulationFrame,
    RunStatus,
    RunRequest,
    RunAccepted,
)
from .evidence import Dossier, DossierLine, AttributionResult, AttributionOutcome

__all__ = [
    # Common
    "EvidenceTag",
    "Provenance",
    "Confidence",
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
    # Evidence
    "Dossier",
    "DossierLine",
    "AttributionResult",
    "AttributionOutcome",
]
from .detection import ArtifactDetection