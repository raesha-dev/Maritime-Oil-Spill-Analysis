"""Router layer for the SpillTrack API."""

from .incidents import router as incidents_router
from .candidates import router as candidates_router
from .simulation import router as simulation_router
from .evidence import router as evidence_router
from .reports import router as reports_router

__all__ = [
    "incidents_router",
    "candidates_router",
    "simulation_router",
    "evidence_router",
    "reports_router",
]
