from __future__ import annotations
from fastapi.responses import FileResponse

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .config import settings
from .cache.store import RunCache
from .jobs.registry import Run, RunRegistry, RunState
from .models import (
    Assessment,
    AssessmentRequest,
    CandidateRanking,
    CandidateRankingRequest,
    ConsistencyComponents,
    DashboardDetection,
    DashboardIncident,
    DashboardSimulation,
    DashboardAssessment,
    DashboardSnapshot,
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
    OriginEstimate,
    SimulationRequest,
    SimulationResult,
)
from .services import (
    DeterministicDriftAdapter,
    assess,
    rank_candidates,
    simulation_cache_key,
)
from .storage import Store
from .schemas.incident import ArtifactIncident
from .schemas.detection import ArtifactDetection
from .schemas.common import Envelope, EvidenceTag, Provenance, SystemStatus
from .schemas.evidence import (
    AttributionBundle,
    AttributionOutcome,
    AttributionResult,
    Dossier,
)
from .schemas.report import ForensicReport
from .schemas.incident import (
    ArtifactHindcast,
    CandidateArtifactSet,
    GeoJSONFeatureCollection,
    MapLayers,
)
from .schemas.simulation import ArtifactRun, RunAccepted, RunRequest, RunStatusResponse
from .services.artifacts import (
    ArtifactNotFoundError,
    Artifacts,
    InvalidArtifactError,
)
from .services.attribution import build_fixture_attribution
from .services.reports import build_report
from .services.report_pdf import render_report_pdf
from pydantic import ValidationError

VERSION = "0.1.0"
store = Store(settings.database_path)
drift_engine = DeterministicDriftAdapter()
artifacts = Artifacts(settings.data_dir)
run_registry = RunRegistry()
run_cache = RunCache(settings.cache_dir)


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


@app.exception_handler(ArtifactNotFoundError)
async def artifact_not_found_handler(
    request: Request, exc: ArtifactNotFoundError
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "404",
                "message": "Requested incident artifact was not found",
                "request_id": request_id,
            }
        },
        headers={"X-Request-ID": request_id},
    )


@app.exception_handler(InvalidArtifactError)
async def invalid_artifact_handler(
    request: Request, exc: InvalidArtifactError
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "500",
                "message": "Incident artifact is invalid or unreadable",
                "request_id": request_id,
            }
        },
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


@app.get("/api/v1/system/status", response_model=SystemStatus)
def system_status() -> SystemStatus:
    return SystemStatus(
        service="spill-forensics-api",
        version=VERSION,
        demo_mode=settings.demo_mode,
        scenario=settings.scenario,
    )


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


@app.get("/api/v1/incidents/{incident_id}", response_model=Envelope[ArtifactIncident])
def get_incident(incident_id: str) -> Envelope[ArtifactIncident]:
    return Envelope(
        data=ArtifactIncident.model_validate(artifacts.load_incident(incident_id)),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.OBSERVED, "incident.json"
        ),
    )

@app.get("/api/v1/incidents/{incident_id}/detection", response_model=Envelope[ArtifactDetection])
def get_detection(incident_id: str) -> Envelope[ArtifactDetection]:
    return Envelope(
        data=ArtifactDetection.model_validate(artifacts.load_detection(incident_id)),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.OBSERVED, "detection.json"
        ),
    )

@app.get("/api/v1/incidents/{incident_id}/hindcast", response_model=Envelope[ArtifactHindcast])
def get_hindcast(incident_id: str) -> Envelope[ArtifactHindcast]:
    return Envelope(
        data=ArtifactHindcast.model_validate(artifacts.load_hindcast(incident_id)),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.INFERRED, "hindcast.json"
        ),
    )

@app.get("/api/v1/incidents/{incident_id}/candidates", response_model=Envelope[CandidateArtifactSet])
def get_candidates(incident_id: str) -> Envelope[CandidateArtifactSet]:
    return Envelope(
        data=CandidateArtifactSet.model_validate(artifacts.load_candidates(incident_id)),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.INFERRED, "candidates.json"
        ),
    )

@app.get("/api/v1/incidents/{incident_id}/slick")
def get_slick(incident_id: str) -> Envelope[GeoJSONFeatureCollection]:
    return Envelope(
        data=GeoJSONFeatureCollection.model_validate(
            artifacts.load_geojson(incident_id, "slick_observed")
        ),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.OBSERVED, "slick_observed.geojson"
        ),
    )

@app.get("/api/v1/incidents/{incident_id}/hindcast-field")
def get_hindcast_field(incident_id: str) -> Envelope[GeoJSONFeatureCollection]:
    return Envelope(
        data=GeoJSONFeatureCollection.model_validate(
            artifacts.load_geojson(incident_id, "hindcast_field")
        ),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.INFERRED, "hindcast_field.geojson"
        ),
    )


def artifact_provenance(
    incident_id: str, tag: EvidenceTag, source: str
) -> Provenance:
    incident = artifacts.load_incident(incident_id)
    return Provenance(
        tag=tag,
        source=source,
        generated_at=datetime.fromisoformat(
            incident["processed_at"].replace("Z", "+00:00")
        ),
        model_run_id=incident.get("model_run_id"),
    )


@app.get("/api/v1/incidents/{incident_id}/layers", response_model=MapLayers)
def get_map_layers(incident_id: str) -> MapLayers:
    return MapLayers(
        observed_slick=Envelope(
            data=artifacts.load_geojson(incident_id, "slick_observed"),
            provenance=artifact_provenance(
                incident_id, EvidenceTag.OBSERVED, "slick_observed.geojson"
            ),
        ),
        ais_tracks=Envelope(
            data=artifacts.load_ais_tracks(incident_id),
            provenance=artifact_provenance(
                incident_id, EvidenceTag.OBSERVED, "ais_tracks.geojson"
            ),
        ),
        origin_field=Envelope(
            data=artifacts.load_geojson(incident_id, "hindcast_field"),
            provenance=artifact_provenance(
                incident_id, EvidenceTag.INFERRED, "hindcast_field.geojson"
            ),
        ),
    )


@app.get("/api/v1/incidents/{incident_id}/ais-tracks")
def get_ais_tracks(incident_id: str) -> Envelope[dict[str, Any]]:
    return Envelope(
        data=artifacts.load_ais_tracks(incident_id),
        provenance=artifact_provenance(
            incident_id, EvidenceTag.OBSERVED, "ais_tracks.geojson"
        ),
    )


@app.get("/api/v1/incidents/{incident_id}/runs/{run_id}/frames")
def get_run_frames(
    incident_id: str, run_id: str
) -> Envelope[GeoJSONFeatureCollection]:
    artifact_run = ArtifactRun.model_validate(artifacts.load_run(incident_id, run_id))
    return Envelope(
        data=GeoJSONFeatureCollection.model_validate(
            artifacts.load_run_frames(incident_id, run_id)
        ),
        provenance=Provenance(
            tag=EvidenceTag.SIMULATED,
            source=f"runs/{run_id}_frames.geojson",
            generated_at=artifact_run.generated_at,
            model_run_id=artifact_run.model_run_id,
        ),
    )


def select_incident_run(incident_id: str, run_id: str | None) -> ArtifactRun | None:
    runs = artifacts.list_runs(incident_id)
    if run_id is not None:
        return ArtifactRun.model_validate(artifacts.load_run(incident_id, run_id))
    if len(runs) > 1:
        raise HTTPException(
            status_code=409,
            detail="run_id is required when an incident has multiple run artifacts",
        )
    return ArtifactRun.model_validate(runs[0]) if runs else None


@app.get(
    "/api/v1/incidents/{incident_id}/attribution",
    response_model=Envelope[AttributionBundle],
)
def get_fixture_attribution(
    incident_id: str, run_id: str | None = None
) -> Envelope[AttributionBundle]:
    incident = artifacts.load_incident(incident_id)
    candidates = CandidateArtifactSet.model_validate(
        artifacts.load_candidates(incident_id)
    )
    run = select_incident_run(incident_id, run_id)
    bundle = build_fixture_attribution(candidates, run, settings)
    return Envelope(
        data=bundle,
        provenance=Provenance(
            tag=EvidenceTag.COMPARED if run else EvidenceTag.GAP,
            source=f"runs/{run.run_id}.json" if run else "runs/ (no completed comparison)",
            generated_at=(
                run.generated_at
                if run
                else datetime.fromisoformat(incident["processed_at"].replace("Z", "+00:00"))
            ),
            model_run_id=run.model_run_id if run else incident.get("model_run_id"),
        ),
    )


@app.get(
    "/api/v1/incidents/{incident_id}/candidates/{mmsi}/dossier",
    response_model=Envelope[Dossier],
)
def get_fixture_dossier(
    incident_id: str, mmsi: str, run_id: str | None = None
) -> Envelope[Dossier]:
    if len(mmsi) != 9 or not mmsi.isdigit():
        raise HTTPException(status_code=422, detail="mmsi must contain nine digits")
    incident = artifacts.load_incident(incident_id)
    candidates = CandidateArtifactSet.model_validate(
        artifacts.load_candidates(incident_id)
    )
    if not any(candidate.mmsi == mmsi for candidate in candidates.candidates):
        raise HTTPException(status_code=404, detail="candidate was not found")
    run = select_incident_run(incident_id, run_id)
    if run is None or run.mmsi != mmsi:
        raise HTTPException(status_code=404, detail="completed candidate run was not found")
    bundle = build_fixture_attribution(candidates, run, settings)
    if bundle.dossier is None:
        raise HTTPException(
            status_code=409,
            detail="dossier is unavailable for this null-state result",
        )
    return Envelope(
        data=bundle.dossier,
        provenance=Provenance(
            tag=EvidenceTag.COMPARED,
            source=f"runs/{run.run_id}.json",
            generated_at=run.generated_at,
            model_run_id=run.model_run_id,
        ),
    )


@app.get(
    "/api/v1/incidents/{incident_id}/evidence",
    response_model=Envelope[list[EvidenceEvent]],
)
def get_fixture_evidence(incident_id: str) -> Envelope[list[EvidenceEvent]]:
    incident = artifacts.load_incident(incident_id)
    with store.connection() as connection:
        rows = connection.execute(
            "SELECT payload FROM evidence_events WHERE incident_id = ? ORDER BY occurred_at",
            (incident_id,),
        ).fetchall()
    events = [EvidenceEvent.model_validate(store.decode(row["payload"])) for row in rows]
    return Envelope(
        data=events,
        provenance=Provenance(
            tag=EvidenceTag.SYSTEM,
            source="SQLite evidence_events",
            generated_at=now(),
            model_run_id=incident.get("model_run_id"),
            assumptions=["Only persisted evidence events are included."],
        ),
    )


def report_evidence(incident_id: str) -> list[EvidenceEvent]:
    with store.connection() as connection:
        rows = connection.execute(
            "SELECT payload FROM evidence_events WHERE incident_id = ? ORDER BY occurred_at",
            (incident_id,),
        ).fetchall()
    return [EvidenceEvent.model_validate(store.decode(row["payload"])) for row in rows]


@app.get(
    "/api/v1/incidents/{incident_id}/report/json",
    response_model=ForensicReport,
)
def get_json_report(
    incident_id: str, run_id: str | None = None
) -> ForensicReport:
    return build_report(
        incident_id,
        artifacts,
        settings,
        report_evidence(incident_id),
        run_id=run_id,
    )


@app.get("/api/v1/incidents/{incident_id}/report/pdf")
def get_pdf_report(incident_id: str, run_id: str | None = None) -> Response:
    report = build_report(
        incident_id,
        artifacts,
        settings,
        report_evidence(incident_id),
        run_id=run_id,
    )
    filename = f"{incident_id}-forensic-report.pdf"
    return Response(
        content=render_report_pdf(report),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def run_cache_key(incident_id: str, request: RunRequest) -> str:
    return run_cache.key(
        incident_id,
        request.mmsi,
        request.release_time.astimezone(timezone.utc).isoformat(),
        request.environment,
    )


async def execute_precomputed_run(
    run: Run, incident_id: str, stored_run: dict[str, Any], cache_key: str
) -> None:
    try:
        await run_registry.publish(
            run,
            state=RunState.RUNNING,
            progress=0.25,
            message="Loading stored run frames",
        )
        frames = await asyncio.to_thread(
            artifacts.load_run_frames, incident_id, stored_run["run_id"]
        )
        result = {"run": stored_run, "frames": frames}
        await run_registry.publish(
            run,
            state=RunState.COMPLETE,
            progress=1.0,
            message="Stored run artifacts loaded",
            result=result,
        )
        run_cache.put(cache_key, result)
    except Exception:
        await run_registry.publish(
            run,
            state=RunState.FAILED,
            progress=1.0,
            message="Stored run artifacts could not be loaded",
        )


@app.post(
    "/api/v1/incidents/{incident_id}/counterfactual",
    response_model=RunAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_counterfactual_run(
    incident_id: str, request: RunRequest
) -> RunAccepted:
    stored_run = artifacts.find_run(
        incident_id,
        request.mmsi,
        request.release_time,
        request.environment,
    )
    cache_key = run_cache_key(incident_id, request)
    cached_result = run_cache.get(cache_key)
    if cached_result is not None:
        try:
            stored_run = ArtifactRun.model_validate(cached_result["run"]).model_dump(
                mode="json"
            )
            frames = GeoJSONFeatureCollection.model_validate(
                cached_result["frames"]
            ).model_dump(mode="json")
            result = {"run": stored_run, "frames": frames}
        except (KeyError, TypeError, ValidationError):
            result = None
        if result is not None:
            run = run_registry.create(cached=True)
            await run_registry.publish(
                run,
                state=RunState.COMPLETE,
                progress=1.0,
                message="Stored run result restored from cache",
                result=result,
            )
            return RunAccepted(run_id=run.run_id, cached=True)

    run = run_registry.create()
    asyncio.create_task(
        execute_precomputed_run(run, incident_id, stored_run, cache_key)
    )
    return RunAccepted(run_id=run.run_id, cached=False)


def run_status_payload(run: Run) -> RunStatusResponse:
    return RunStatusResponse(
        run_id=run.run_id,
        state=run.state,
        progress=run.progress,
        message=run.message,
        cached=run.cached,
        result=run.result,
    )


@app.get("/api/v1/runs/{run_id}", response_model=RunStatusResponse)
def get_run_status(run_id: str) -> RunStatusResponse:
    run = run_registry.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run was not found")
    return run_status_payload(run)


@app.get(
    "/api/v1/runs/{run_id}/frames",
    response_model=Envelope[GeoJSONFeatureCollection],
)
def get_registered_run_frames(
    run_id: str,
) -> Envelope[GeoJSONFeatureCollection]:
    run = run_registry.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run was not found")
    if run.result is None:
        raise HTTPException(status_code=409, detail="run frames are not available yet")
    artifact_run = ArtifactRun.model_validate(run.result["run"])
    return Envelope(
        data=GeoJSONFeatureCollection.model_validate(run.result["frames"]),
        provenance=Provenance(
            tag=EvidenceTag.SIMULATED,
            source=f"runs/{artifact_run.run_id}_frames.geojson",
            generated_at=artifact_run.generated_at,
            model_run_id=artifact_run.model_run_id,
        ),
    )


@app.get("/api/v1/runs/{run_id}/events")
async def stream_run_events(run_id: str) -> StreamingResponse:
    run = run_registry.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run was not found")

    async def events():
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=16)
        run.subscribers.append(queue)
        try:
            current = run_status_payload(run).model_dump(mode="json")
            yield f"data: {json.dumps(current)}\n\n"
            if run.state in {RunState.COMPLETE, RunState.FAILED}:
                return
            while True:
                update = await queue.get()
                yield f"data: {json.dumps(update, default=str)}\n\n"
                if update["state"] in {RunState.COMPLETE, RunState.FAILED}:
                    return
        finally:
            run.subscribers.remove(queue)

    return StreamingResponse(events(), media_type="text/event-stream")

@app.get("/api/v1/incidents/{incident_id}/slick-preview")
def get_slick_preview(incident_id: str):
    path = artifacts.get_asset_path(incident_id, "slick_preview.png")
    return FileResponse(path, media_type="image/png")

@app.get("/api/v1/incidents/{incident_id}/hindcast-field-preview")
def get_hindcast_field_preview(incident_id: str):
    path = artifacts.get_asset_path(incident_id, "hindcast_field.png")
    return FileResponse(path, media_type="image/png")

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


def latest_detection(incident_id: str) -> Detection | None:
    with store.connection() as connection:
        row = connection.execute(
            "SELECT payload FROM detections WHERE incident_id = ? ORDER BY created_at DESC LIMIT 1", (incident_id,)
        ).fetchone()
    return Detection.model_validate(store.decode(row["payload"])) if row else None


@app.get("/api/v1/incidents/{incident_id}/dashboard", response_model=DashboardSnapshot)
def get_dashboard(incident_id: str) -> DashboardSnapshot:
    incident = incident_or_404(incident_id)
    ranking_payload = store.get_artifact(incident_id, "ranking")
    hindcast_payload = store.get_artifact(incident_id, "hindcast")
    assessment_payload = store.get_artifact(incident_id, "assessment")
    events = list_evidence_events(incident_id)
    simulations = [SimulationResult.model_validate(item) for item in store.list_simulations(incident_id)]
    artifact_times = [
        store.artifact_updated_at(incident_id, artifact_type)
        for artifact_type in ("ranking", "hindcast", "assessment")
    ]
    update_times = [
        incident.updated_at, *(event.created_at for event in events), *(run.created_at for run in simulations),
        *(datetime.fromisoformat(value) for value in artifact_times if value),
    ]
    return DashboardSnapshot(
        incident=DashboardIncident(
            incident_id=incident.incident_id,
            title=incident.title,
            aoi=incident.aoi,
            detected_at=incident.detected_at,
        ),
        detection=(
            DashboardDetection(
                id=detection.id,
                scene_id=detection.scene_id,
                satellite=detection.satellite,
                acquired_at=detection.acquired_at,
                centroid=detection.centroid,
                area_km2=detection.area_km2,
                oil_confidence=detection.oil_confidence,
                classification=detection.classification,
                confidence_tier=detection.confidence_tier,
                pipeline_status=detection.pipeline_status,
            )
            if (detection := latest_detection(incident_id))
            else None
        ),
        hindcast=OriginEstimate.model_validate(hindcast_payload) if hindcast_payload else None,
        ranking=CandidateRanking.model_validate(ranking_payload) if ranking_payload else None,
        simulations=[
            DashboardSimulation(
                id=str(simulation.id),
                candidate_id=simulation.candidate_id,
                source_consistency_score=simulation.source_consistency_score,
                components=simulation.components,
            )
            for simulation in simulations
        ],
        assessment=(
            DashboardAssessment(
                state=assessment.state,
                message=assessment.message,
                dossier=assessment.dossier,
            )
            if (assessment := Assessment.model_validate(assessment_payload))
            else None
        ) if assessment_payload else None,
        evidence_events=events,
        updated_at=max(update_times),
    )


@app.post("/api/v1/incidents/{incident_id}/hindcasts")
def create_hindcast(incident_id: str, body: HindcastRequest):
    incident_or_404(incident_id)
    detection = detection_or_404(body.detection_id)
    if detection.incident_id != incident_id:
        raise HTTPException(status_code=422, detail="detection does not belong to this incident")
    if detection.pipeline_status == "stopped":
        raise HTTPException(status_code=409, detail="hindcast is blocked because detection confidence/classification did not pass the gate")
    result = drift_engine.hindcast(detection, body)
    store.save_artifact(incident_id, "hindcast", payload(result), now().isoformat())
    return result


@app.post("/api/v1/candidates/rank")
def create_candidate_ranking(body: CandidateRankingRequest):
    incident_or_404(body.incident_id)
    result = rank_candidates(body.candidates, body.incident_id, body.shortlist_size)
    store.save_artifact(body.incident_id, "ranking", payload(result), now().isoformat())
    return result


@app.post("/api/v1/simulations", response_model=SimulationResult, status_code=status.HTTP_201_CREATED)
def create_simulation(body: SimulationRequest) -> SimulationResult:
    incident_or_404(body.incident_id)
    stored_run = ArtifactRun.model_validate(
        artifacts.find_run(
            body.incident_id,
            body.candidate.vessel.mmsi,
            body.release_time,
            body.environment_cache_key,
        )
    )
    if stored_run.candidate_id != body.candidate.vessel.vessel_id:
        raise HTTPException(
            status_code=404,
            detail="no precomputed run matches this candidate",
        )
    key = simulation_cache_key(body)
    with store.connection() as connection:
        row = connection.execute("SELECT payload FROM simulations WHERE cache_key = ?", (key,)).fetchone()
        if row:
            return SimulationResult.model_validate({**store.decode(row["payload"]), "cached": True})
        timestamp = now()
        components = ConsistencyComponents(
            **{
                name: stored_run.components[name].value
                for name in ("spatial_iou", "centroid_match", "shape_match", "area_curve_dtw")
            }
        )

        result = SimulationResult(
            id=uuid4(),
            incident_id=body.incident_id,
            candidate_id=body.candidate.vessel.vessel_id,
            source_consistency_score=stored_run.source_consistency_score,
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
    result = assess(sorted(body.candidates, key=lambda item: item.source_consistency_score, reverse=True), settings)
    store.save_artifact(incident_id, "assessment", payload(result), now().isoformat())
    return result


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
