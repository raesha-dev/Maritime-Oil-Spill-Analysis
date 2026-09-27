"""Evidence router with evidence events endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


class EvidenceEventCreate(BaseModel):
    incident_id: str
    occurred_at: str
    kind: str
    description: str
    source_ref: str


@router.post("")
async def create_evidence_event(body: EvidenceEventCreate) -> dict[str, Any]:
    """Create evidence event."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/{incident_id}/evidence-events")
async def list_evidence_events(incident_id: str) -> list[dict[str, Any]]:
    """List evidence events for incident."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
