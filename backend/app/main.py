from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    Assessment,
    AssessmentRequest,
    CandidateRankingRequest,
    Detection,
    DetectionCreate,
    EvidenceEvent,
    EvidenceEventCreate,
    HealthResponse,
    HindcastRequest,
    Incident,
    IncidentCreate,
    Message,
    MessageCreate,
    SimulationRequest,
    SimulationResult,
)
from .services import (
    DeterministicDriftAdapter,
    assess,
    rank_candidates,
    run_counterfactual_simulation,
    simulation_cache_key,
    source_consistency_score,
)
from .storage import Store

VERSION = "0.1.0"
store = Store(settings.database_path)
drift_engine = DeterministicDriftAdapter()


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.initialize()
    yield


app = FastAPI(
    title="SpillTrack Forensic API", version=VERSION, openapi_url="/api/v1/openapi.json",
    docs_url="/docs", lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": str(exc.status_code), "message": exc.detail, "request_id": request_id}},
        headers={"X-Request-ID": request_id},
    )


def now() -> datetime:
    return datetime.now(timezone.utc)


def payload(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


def incident_or_404(incident_id: str) -> Incident:
    with store.connection() as connection:
        row = connection.execute("SELECT payload FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"incident '{incident_id}' was not found")
    return Incident.model_validate(store.decode(row["payload"]))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(version=VERSION)


@app.post("/api/v1/incidents", response_model=Incident, status_code=status.HTTP_201_CREATED)
def create_incident(body: IncidentCreate) -> Incident:
    timestamp = now()
    incident = Incident(**body.model_dump(), created_at=timestamp, updated_at=timestamp)
    with store.connection() as connection:
        existing = connection.execute("SELECT 1 FROM incidents WHERE incident_id = ?", (body.incident_id,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"incident '{body.incident_id}' already exists")
        connection.execute(
            "INSERT INTO incidents(incident_id, payload, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (incident.incident_id, store.encode(payload(incident)), timestamp.isoformat(), timestamp.isoformat()),
        )
    return incident


@app.get("/api/v1/incidents/{incident_id}", response_model=Incident)
def get_incident(incident_id: str) -> Incident:
    return incident_or_404(incident_id)


@app.post("/api/v1/incidents/{incident_id}/detections", response_model=Detection, status_code=status.HTTP_201_CREATED)
def create_detection(incident_id: str, body: DetectionCreate) -> Detection:
    incident_or_404(incident_id)
    timestamp = now()
    detection = Detection(
        **body.model_dump(), id=uuid4(), incident_id=incident_id, created_at=timestamp,
        pipeline_status="proceed" if body.classification == "oil" and body.confidence_tier == "high" else ("validate" if body.classification == "oil" and body.confidence_tier == "medium" else "stopped"),
    )
    with store.connection() as connection:
        connection.execute(
            "INSERT INTO detections(id, incident_id, payload, created_at) VALUES (?, ?, ?, ?)",
            (str(detection.id), incident_id, store.encode(payload(detection)), timestamp.isoformat()),
        )
    return detection


def detection_or_404(detection_id: UUID) -> Detection:
    with store.connection() as connection:
        row = connection.execute("SELECT payload FROM detections WHERE id = ?", (str(detection_id),)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"detection '{detection_id}' was not found")
    return Detection.model_validate(store.decode(row["payload"]))


@app.post("/api/v1/incidents/{incident_id}/hindcasts")
def create_hindcast(incident_id: str, body: HindcastRequest):
    incident_or_404(incident_id)
    detection = detection_or_404(body.detection_id)
    if detection.incident_id != incident_id:
        raise HTTPException(status_code=422, detail="detection does not belong to this incident")
    if detection.pipeline_status == "stopped":
        raise HTTPException(status_code=409, detail="hindcast is blocked because detection confidence/classification did not pass the gate")
    return drift_engine.hindcast(detection, body)


@app.post("/api/v1/candidates/rank")
def create_candidate_ranking(body: CandidateRankingRequest):
    incident_or_404(body.incident_id)
    return rank_candidates(body.candidates, body.incident_id, body.shortlist_size)


@app.post("/api/v1/simulations", response_model=SimulationResult, status_code=status.HTTP_201_CREATED)
def create_simulation(body: SimulationRequest) -> SimulationResult:
    incident_or_404(body.incident_id)
    key = simulation_cache_key(body)
    with store.connection() as connection:
        row = connection.execute("SELECT payload FROM simulations WHERE cache_key = ?", (key,)).fetchone()
        if row:
            return SimulationResult.model_validate({**store.decode(row["payload"]), "cached": True})
        timestamp = now()
        components = run_counterfactual_simulation(body)

        result = SimulationResult(
            id=uuid4(),
            incident_id=body.incident_id,
            candidate_id=body.candidate.vessel.vessel_id,
            source_consistency_score=source_consistency_score(components),
            components=components,
            cache_key=key,
            cached=False,
            created_at=timestamp,
        )
        connection.execute(
            "INSERT INTO simulations(cache_key, payload, created_at) VALUES (?, ?, ?)",
            (key, store.encode(payload(result)), timestamp.isoformat()),
        )
    return result


@app.post("/api/v1/incidents/{incident_id}/assessment", response_model=Assessment)
def create_assessment(incident_id: str, body: AssessmentRequest) -> Assessment:
    incident_or_404(incident_id)
    return assess(sorted(body.candidates, key=lambda item: item.source_consistency_score, reverse=True), settings)


@app.post("/api/v1/evidence-events", response_model=EvidenceEvent, status_code=status.HTTP_201_CREATED)
def create_evidence_event(body: EvidenceEventCreate) -> EvidenceEvent:
    incident_or_404(body.incident_id)
    event = EvidenceEvent(**body.model_dump(), id=uuid4(), created_at=now())
    with store.connection() as connection:
        connection.execute(
            "INSERT INTO evidence_events(id, incident_id, payload, occurred_at, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(event.id), event.incident_id, store.encode(payload(event)), event.occurred_at.isoformat(), event.created_at.isoformat()),
        )
    return event


@app.get("/api/v1/incidents/{incident_id}/evidence-events", response_model=list[EvidenceEvent])
def list_evidence_events(incident_id: str) -> list[EvidenceEvent]:
    incident_or_404(incident_id)
    with store.connection() as connection:
        rows = connection.execute("SELECT payload FROM evidence_events WHERE incident_id = ? ORDER BY occurred_at", (incident_id,)).fetchall()
    return [EvidenceEvent.model_validate(store.decode(row["payload"])) for row in rows]


@app.post("/api/v1/messages", response_model=Message, status_code=status.HTTP_201_CREATED)
def create_message(body: MessageCreate) -> Message:
    incident_or_404(body.incident_id)
    message = Message(**body.model_dump(), id=uuid4(), created_at=now())
    with store.connection() as connection:
        connection.execute(
            "INSERT INTO messages(id, incident_id, payload, created_at) VALUES (?, ?, ?, ?)",
            (str(message.id), message.incident_id, store.encode(payload(message)), message.created_at.isoformat()),
        )
    return message


@app.get("/api/v1/incidents/{incident_id}/messages", response_model=list[Message])
def list_messages(incident_id: str) -> list[Message]:
    incident_or_404(incident_id)
    with store.connection() as connection:
        rows = connection.execute("SELECT payload FROM messages WHERE incident_id = ? ORDER BY created_at", (incident_id,)).fetchall()
    return [Message.model_validate(store.decode(row["payload"])) for row in rows]


@app.websocket("/api/v1/incidents/{incident_id}/messages/live")
async def live_messages(websocket: WebSocket, incident_id: str) -> None:
    try:
        incident_or_404(incident_id)
    except HTTPException:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    try:
        while True:
            incoming = await websocket.receive_json()
            message = MessageCreate(incident_id=incident_id, **incoming)
            created = create_message(message)
            await websocket.send_json(payload(created))
    except WebSocketDisconnect:
        return
