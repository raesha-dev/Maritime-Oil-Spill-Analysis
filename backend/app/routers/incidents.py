"""Incident router with GET endpoints."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..config import settings
from ..models import (
    DashboardSnapshot,
    Detection,
    DetectionCreate,
    HealthResponse,
    Incident,
    IncidentCreate,
    OriginEstimate,
)
from ..services import DeterministicDriftAdapter
from ..storage import Store

router = APIRouter()

VERSION = "0.1.0"
store = Store(settings.database_path)
drift_engine = DeterministicDriftAdapter()


@asynccontextmanager
async def lifespan(_: Any):
    store.initialize()
    yield


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(version=VERSION)


@router.post("", response_model=Incident, status_code=status.HTTP_201_CREATED)
async def create_incident(body: IncidentCreate) -> Incident:
    from datetime import datetime, timezone

    def now() -> datetime:
        return datetime.now(timezone.utc)

    timestamp = now()
    incident = Incident(**body.model_dump(), created_at=timestamp, updated_at=timestamp)
    with store.connection() as connection:
        existing = connection.execute(
            "SELECT 1 FROM incidents WHERE incident_id = ?", (body.incident_id,)
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=409, detail=f"incident '{body.incident_id}' already exists"
            )
        connection.execute(
            "INSERT INTO incidents(incident_id, payload, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (
                incident.incident_id,
                store.encode({"incident_id": incident.incident_id, "payload": incident.model_dump()}),
                timestamp.isoformat(),
                timestamp.isoformat(),
            ),
        )
    return incident


@router.get("/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str) -> Incident:
    with store.connection() as connection:
        row = connection.execute(
            "SELECT payload FROM incidents WHERE incident_id = ?", (incident_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"incident '{incident_id}' was not found")
    data = store.decode(row["payload"])
    return Incident.model_validate(data)


@router.post(
    "/{incident_id}/detections", response_model=Detection, status_code=status.HTTP_201_CREATED
)
async def create_detection(incident_id: str, body: DetectionCreate) -> Detection:
    from datetime import datetime, timezone
    from uuid import uuid4

    def now() -> datetime:
        return datetime.now(timezone.utc)

    with store.connection() as connection:
        existing = connection.execute(
            "SELECT 1 FROM incidents WHERE incident_id = ?", (incident_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(
                status_code=404, detail=f"incident '{incident_id}' was not found"
            )

    timestamp = now()
    detection = Detection(
        **body.model_dump(),
        id=uuid4(),
        incident_id=incident_id,
        created_at=timestamp,
        pipeline_status="proceed"
        if body.classification == "oil" and body.confidence_tier == "high"
        else ("validate" if body.classification == "oil" and body.confidence_tier == "medium" else "stopped"),
    )
    with store.connection() as connection:
        connection.execute(
            "INSERT INTO detections(id, incident_id, payload, created_at) VALUES (?, ?, ?, ?)",
            (
                str(detection.id),
                incident_id,
                store.encode({"id": str(detection.id), "payload": detection.model_dump()}),
                timestamp.isoformat(),
            ),
        )
    return detection


@router.get("/{incident_id}/detection")
async def get_detection(incident_id: str) -> Detection:
    with store.connection() as connection:
        row = connection.execute(
            "SELECT payload FROM detections WHERE incident_id = ? ORDER BY created_at DESC LIMIT 1",
            (incident_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"detection for incident '{incident_id}' not found")
    data = store.decode(row["payload"])
    return Detection.model_validate(data)


@router.get("/{incident_id}/hindcast")
async def get_hindcast(incident_id: str) -> OriginEstimate:
    payload = store.get_artifact(incident_id, "hindcast")
    if payload is None:
        raise HTTPException(status_code=404, detail=f"hindcast for incident '{incident_id}' not found")
    return OriginEstimate.model_validate(payload)


@router.get("/{incident_id}/layers")
async def get_layers(incident_id: str) -> dict[str, Any]:
    """Get map layers bundle - placeholder for artifact loading."""
    return {"incident_id": incident_id, "layers": "placeholder"}


@router.get("/{incident_id}/candidates")
async def get_candidates(incident_id: str) -> dict[str, Any]:
    """Get candidate vessels for incident - placeholder."""
    payload = store.get_artifact(incident_id, "ranking")
    if payload is None:
        return {"incident_id": incident_id, "candidates": [], "raw_candidate_count": 0}
    return payload
