# SpillTrack forensic API

This is a standalone FastAPI backend for the existing TanStack dashboard. It has stable JSON contracts, SQLite persistence, CORS controls, structured error responses, deterministic caching, a live WebSocket message channel, and OpenAPI documentation at `/docs`.

## Start locally

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set `SPILL_API_DATABASE_PATH` to an absolute path when launching the service from another directory. The default database is `backend/spill-forensics.db`.

## Core contracts

| Need | Endpoint |
| --- | --- |
| Create/read an incident | `POST` / `GET /api/v1/incidents` |
| Read the complete dashboard state | `GET /api/v1/incidents/{incident_id}/dashboard` |
| Send SAR detection output | `POST /api/v1/incidents/{incident_id}/detections` |
| Request a hindcast | `POST /api/v1/incidents/{incident_id}/hindcasts` |
| Build a ranked vessel funnel | `POST /api/v1/candidates/rank` |
| Store/reuse a counterfactual run | `POST /api/v1/simulations` |
| Return forensic-safe assessment | `POST /api/v1/incidents/{incident_id}/assessment` |
| Record evidence events | `POST/GET /api/v1/.../evidence-events` |
| Send/list messages | `POST/GET /api/v1/.../messages` |
| Live message echo | `WS /api/v1/incidents/{incident_id}/messages/live` |

## Model integration boundary

`app/services.py` contains `DriftEngine` and `DeterministicDriftAdapter`. Replace that adapter with an OpenDrift or AI-backed implementation while preserving its typed request and response models. The current adapter deliberately gives repeatable development results; it must not be represented as a scientific drift prediction.

The source-consistency score is strictly derived from spatial, centroid, shape, and area-curve inputs. The final assessment endpoint accepts only tested candidates and applies its threshold/gap logic to that source score. Vessel Risk Profile and AIS Behavioral Anomaly are included only in compute priority, never in the physics score or final assessment.

Every successful pipeline endpoint writes its latest result to the incident's dashboard snapshot. This gives the frontend one stable read contract while provider adapters evolve. `DeterministicDriftAdapter` is deliberately a demo fallback; a real OpenDrift/AI provider replaces the adapter while retaining these same input/output models. Hindcast responses explicitly carry `is_fallback` and `warnings`; the dashboard displays **MODEL FALLBACK** rather than treating that output as live scientific analysis.

## Frontend connection

Set `VITE_FORENSICS_API_URL` in the repository-root `.env` to the API address (for local development, `http://localhost:8000`). The dashboard calls `GET /api/v1/incidents/SIH26143-2025-001/dashboard` on load and on refresh. A live view requires detection, hindcast, ranking, at least one simulation, and assessment data. If the service is unreachable, or that incident is incomplete, it switches to a visibly labelled **DEMO FALLBACK** state. Fallback data is local, deterministic, and must not be represented as live satellite/model output.

## Verification

```bash
cd backend
pytest
```
