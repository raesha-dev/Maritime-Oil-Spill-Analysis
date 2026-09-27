"""Simulation router with counterfactual and SSE endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

router = APIRouter()


class SimulationRequest(BaseModel):
    incident_id: str
    candidate: dict
    release_time: str
    environment: str = "cmes-era5-v1"
    components: dict


class RunAccepted(BaseModel):
    run_id: str
    cached: bool = False


@router.post("/{incident_id}/counterfactual", status_code=202)
async def start_counterfactual(incident_id: str, body: SimulationRequest) -> RunAccepted:
    """Start counterfactual simulation."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/runs/{run_id}")
async def get_run_status(run_id: str) -> dict[str, Any]:
    """Get simulation run status."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/runs/{run_id}/events")
async def stream_run_events(run_id: str):
    """Stream SSE events for simulation progress."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
