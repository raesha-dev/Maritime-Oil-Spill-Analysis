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

Relative `SPILL_API_DATABASE_PATH` values resolve from `backend/`; relative `SPILL_API_DATA_DIR` values resolve from the repository root. The defaults are `backend/spill-forensics.db` and `data/`. The JSON cache defaults to the ignored `backend/.cache/` directory.

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
| Read incident artifacts and map layers | `GET /api/v1/incidents/{incident_id}`, `/detection`, `/hindcast`, `/candidates`, `/layers`, `/ais-tracks` |
| Start fixture-backed counterfactual run | `POST /api/v1/incidents/{incident_id}/counterfactual`; poll `/api/v1/runs/{run_id}` or stream `/events` |
| Export incident report | `GET /api/v1/incidents/{incident_id}/report/json` or `/report/pdf`; optional `run_id` selects a stored run |
| Send/list messages | `POST/GET /api/v1/.../messages` |
| Live message echo | `WS /api/v1/incidents/{incident_id}/messages/live` |

## Model integration boundary

`app/services/` is the active service package. `DeterministicDriftAdapter` remains a labelled development fallback and must not be represented as a scientific drift prediction. Artifact-backed GET, counterfactual, attribution, and report paths read the validated fixture files under `data/incidents/`; the API does not load external trained weights.

The source-consistency score is strictly derived from spatial, centroid, shape, and area-curve inputs. The artifact-backed assessment uses only a stored run's score and gap; candidates without a matching run remain unscored. Vessel Risk Profile and AIS Behavioral Anomaly are context/priority inputs only and never enter the stored source-consistency score.

The database-backed workflow and artifact-backed fixture workflow coexist: create endpoints persist analyst/API submissions in SQLite, while fixture GET and report paths read precomputed artifacts. Hindcast responses carry `is_fallback` and `warnings`; deterministic outputs must not be treated as scientific analysis. The dashboard currently reads the SQLite snapshot route; it does not yet request the artifact route family or run SSE.

## Frontend connection

Set `VITE_FORENSICS_API_URL` in the repository-root `.env` to the API address (for local development, `http://localhost:8000`). The dashboard calls `GET /api/v1/incidents/SIH26143-2025-001/dashboard` on load and on refresh. A live view requires detection, hindcast, ranking, at least one simulation, and assessment data. If the service is unreachable, or that incident is incomplete, it switches to a visibly labelled **DEMO FALLBACK** state. Fallback data is local, deterministic, and must not be represented as live satellite/model output.

## Verification

```bash
cd backend
pytest
```
