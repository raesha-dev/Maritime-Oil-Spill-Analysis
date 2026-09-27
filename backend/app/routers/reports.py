"""Reports router with export endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter()


@router.get("/{incident_id}/report/json")
async def get_report_json(incident_id: str) -> dict[str, Any]:
    """Get incident report as JSON."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/{incident_id}/report/pdf")
async def get_report_pdf(incident_id: str) -> bytes:
    """Get incident report as PDF."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
