"""Candidate router with ranking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..models import CandidateRanking, CandidateRankingRequest
from ..services import rank_candidates

router = APIRouter()


class RankRequest(BaseModel):
    incident_id: str
    candidates: list[dict]
    shortlist_size: int = 5


@router.post("/rank")
async def create_candidate_ranking(body: CandidateRankingRequest) -> CandidateRanking:
    """Create candidate ranking."""
    result = rank_candidates(body.candidates, body.incident_id, body.shortlist_size)
    return result


@router.post("/{incident_id}/candidates/expand")
async def expand_search(incident_id: str) -> dict[str, Any]:
    """Expand candidate pool."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
