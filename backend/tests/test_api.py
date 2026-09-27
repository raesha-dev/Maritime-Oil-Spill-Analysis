import shutil

from fastapi.testclient import TestClient

from app.cache.store import RunCache
from app.config import project_root
from app.jobs.registry import RunRegistry
import app.main as api
from app.services.artifacts import Artifacts
from app.storage import Store


def test_complete_forensic_workflow(tmp_path) -> None:
    api.store = Store(str(tmp_path / "api.db"))
    with TestClient(api.app) as client:
        assert client.get("/health").json()["status"] == "ok"

        incident = client.post("/api/v1/incidents", json={
            "incident_id": "SIH26143-2025-001",
            "title": "Bay of Bengal investigation",
            "aoi": [[92.0, 12.0], [93.0, 12.0], [92.5, 13.0]],
            "detected_at": "2025-09-09T08:17:00Z",
        })
        assert incident.status_code == 201

        unsafe_incident = client.post("/api/v1/incidents", json={
            "incident_id": "UNSAFE-INCIDENT",
            "title": "This vessel caused the spill",
            "aoi": [[92.0, 12.0], [93.0, 12.0], [92.5, 13.0]],
            "detected_at": "2025-09-09T08:17:00Z",
        })
        assert unsafe_incident.status_code == 422

        detection = client.post("/api/v1/incidents/SIH26143-2025-001/detections", json={
            "scene_id": "S1A_IW_GRDH_20250909",
            "satellite": "Sentinel-1",
            "acquired_at": "2025-09-09T08:17:00Z",
            "centroid": [92.861, 12.374],
            "area_km2": 12.4,
            "oil_confidence": 0.91,
            "classification": "oil",
            "confidence_tier": "high",
            "observed_polygon": [[92.8, 12.3], [92.9, 12.3], [92.85, 12.4]],
        })
        assert detection.status_code == 201

        hindcast = client.post("/api/v1/incidents/SIH26143-2025-001/hindcasts", json={
            "detection_id": detection.json()["id"],
            "current_knots": 1.2,
            "current_bearing_degrees": 45,
            "wind_knots": 8,
            "wind_bearing_degrees": 90,
        })
        assert hindcast.status_code == 200
        assert hindcast.json()["model"] == "deterministic-hindcast-adapter"
        assert hindcast.json()["is_fallback"] is True

        ranked = client.post("/api/v1/candidates/rank", json={
            "incident_id": "SIH26143-2025-001",
            "candidates": [{
                "vessel_id": "OCEAN_PRIDE", "name": "OCEAN PRIDE", "vessel_type": "Tanker",
                "mmsi": "563214000", "latest_position": [92.54, 12.31],
                "ais_integrity": "consistent", "behavioral_anomaly_score": 0.2,
                "vessel_risk_profile": 0.3, "distance_to_origin_km": 12,
                "trajectory_alignment": 0.9, "speed_profile_alignment": 0.8,
            }],
        })
        assert ranked.status_code == 200
        candidate = ranked.json()["candidates"][0]

        simulation_body = {
            "incident_id": "SIH26143-2025-001", "candidate": candidate,
            "release_time": "2025-09-08T16:00:00Z", "environment_cache_key": "cmes-era5-v1",
            "components": {"spatial_iou": 0.01, "centroid_match": 0.01, "shape_match": 0.01, "area_curve_dtw": 0.01},
        }
        first_simulation = client.post("/api/v1/simulations", json=simulation_body)
        cached_simulation = client.post("/api/v1/simulations", json=simulation_body)
        assert first_simulation.status_code == 201
        assert first_simulation.json()["cached"] is False
        assert first_simulation.json()["source_consistency_score"] == 0.82
        assert first_simulation.json()["components"]["spatial_iou"] == 0.89
        assert cached_simulation.json()["cached"] is True

        assessment = client.post("/api/v1/incidents/SIH26143-2025-001/assessment", json={"candidates": [{
            "candidate": candidate, "source_consistency_score": first_simulation.json()["source_consistency_score"],
        }]})
        assert assessment.status_code == 200
        assert "does not establish causation" in assessment.json()["message"]

        dashboard = client.get("/api/v1/incidents/SIH26143-2025-001/dashboard")
        assert dashboard.status_code == 200
        assert dashboard.json()["detection"]["scene_id"] == "S1A_IW_GRDH_20250909"
        assert dashboard.json()["hindcast"] is not None
        assert dashboard.json()["hindcast"]["is_fallback"] is True
        assert dashboard.json()["ranking"]["candidates"][0]["vessel"]["vessel_id"] == "OCEAN_PRIDE"
        assert dashboard.json()["assessment"]["state"] == "further_investigation"

        message = client.post("/api/v1/messages", json={
            "incident_id": "SIH26143-2025-001", "role": "analyst", "body": "Run the comparison."
        })
        assert message.status_code == 201
        unsafe_message = client.post("/api/v1/messages", json={
            "incident_id": "SIH26143-2025-001",
            "role": "analyst",
            "body": "This vessel caused the spill.",
        })
        assert unsafe_message.status_code == 422
        assert client.get("/api/v1/incidents/SIH26143-2025-001/messages").json()[0]["body"] == "Run the comparison."

        with client.websocket_connect("/api/v1/incidents/SIH26143-2025-001/messages/live") as websocket:
            websocket.send_json({"role": "system", "body": "Simulation queued."})
            assert websocket.receive_json()["body"] == "Simulation queued."


def test_artifact_read_endpoints_include_provenance_and_real_fixture_data(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(api, "store", Store(str(tmp_path / "artifact-api.db")))
    with TestClient(api.app) as client:
        incident_id = "SIH26143-2025-001"
        status = client.get("/api/v1/system/status")
        incident = client.get(f"/api/v1/incidents/{incident_id}")
        detection = client.get(f"/api/v1/incidents/{incident_id}/detection")
        hindcast = client.get(f"/api/v1/incidents/{incident_id}/hindcast")
        candidates = client.get(f"/api/v1/incidents/{incident_id}/candidates")
        layers = client.get(f"/api/v1/incidents/{incident_id}/layers")
        tracks = client.get(f"/api/v1/incidents/{incident_id}/ais-tracks")
        frames = client.get(f"/api/v1/incidents/{incident_id}/runs/OD-ENS-001/frames")
        attribution = client.get(f"/api/v1/incidents/{incident_id}/attribution")
        dossier = client.get(
            f"/api/v1/incidents/{incident_id}/candidates/563214000/dossier"
        )
        evidence = client.get(f"/api/v1/incidents/{incident_id}/evidence")
        unscored_dossier = client.get(
            f"/api/v1/incidents/{incident_id}/candidates/563214001/dossier"
        )
        missing = client.get("/api/v1/incidents/UNKNOWN-INCIDENT/layers")

        assert status.status_code == 200
        assert status.json()["demo_mode"] is True
        assert incident.json()["provenance"]["tag"] == "OBSERVED"
        assert detection.json()["provenance"]["tag"] == "OBSERVED"
        assert hindcast.json()["provenance"]["tag"] == "INFERRED"
        assert candidates.json()["provenance"]["tag"] == "INFERRED"
        assert layers.status_code == 200
        assert layers.json()["observed_slick"]["provenance"]["tag"] == "OBSERVED"
        assert layers.json()["origin_field"]["provenance"]["tag"] == "INFERRED"
        assert tracks.json()["data"]["features"][0]["properties"]["mmsi"] == "563214000"
        assert frames.json()["data"]["features"][0]["properties"]["offset_hours"] == 0
        assert attribution.json()["provenance"]["tag"] == "COMPARED"
        assert attribution.json()["data"]["attribution"]["outcome"] == "SUPPORTS_INVESTIGATION"
        assert attribution.json()["data"]["attribution"]["top"][0]["mmsi"] == "563214000"
        assert dossier.json()["data"]["vessel_name"] == "OCEAN PRIDE"
        assert dossier.json()["data"]["verdict"] == attribution.json()["data"]["attribution"]["message"]
        assert evidence.status_code == 200
        assert evidence.json()["data"] == []
        assert evidence.json()["provenance"]["tag"] == "SYSTEM"
        assert unscored_dossier.status_code == 404
        assert missing.status_code == 404


def test_precomputed_async_run_sse_status_and_cache(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api, "run_registry", RunRegistry())
    monkeypatch.setattr(api, "run_cache", RunCache(tmp_path / "run-cache"))
    incident_id = "SIH26143-2025-001"
    body = {
        "mmsi": "563214000",
        "release_time": "2025-09-08T16:00:00Z",
        "environment": "cmes-era5-v1",
    }

    with TestClient(api.app) as client:
        submitted = client.post(
            f"/api/v1/incidents/{incident_id}/counterfactual", json=body
        )
        assert submitted.status_code == 202
        run_id = submitted.json()["run_id"]

        events = client.get(f"/api/v1/runs/{run_id}/events")
        status = client.get(f"/api/v1/runs/{run_id}")
        assert events.status_code == 200
        assert "data:" in events.text
        assert "COMPLETE" in events.text
        assert status.json()["state"] == "COMPLETE"
        assert status.json()["result"]["run"]["run_id"] == "OD-ENS-001"
        assert status.json()["result"]["frames"]["features"]
        run_frames = client.get(f"/api/v1/runs/{run_id}/frames")
        assert run_frames.json()["provenance"]["tag"] == "SIMULATED"
        assert run_frames.json()["data"]["features"]

        cached = client.post(
            f"/api/v1/incidents/{incident_id}/counterfactual", json=body
        )
        assert cached.status_code == 202
        assert cached.json()["cached"] is True
        assert client.get(f"/api/v1/runs/{cached.json()['run_id']}").json()["state"] == "COMPLETE"

        assert client.get("/api/v1/runs/unknown-run").status_code == 404
        assert client.get("/api/v1/runs/unknown-run/events").status_code == 404
        assert client.post(
            "/api/v1/incidents/UNKNOWN-INCIDENT/counterfactual", json=body
        ).status_code == 404
        assert client.post(
            f"/api/v1/incidents/{incident_id}/counterfactual",
            json={**body, "release_time": "2025-09-08T16:00:00"},
        ).status_code == 422


def test_attribution_returns_null_state_when_fixture_has_no_run(tmp_path, monkeypatch) -> None:
    incident_id = "SIH26143-2025-001"
    source = project_root / "data" / "incidents" / incident_id
    target = tmp_path / "data" / "incidents" / incident_id
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("runs"))
    monkeypatch.setattr(api, "artifacts", Artifacts(tmp_path / "data"))

    with TestClient(api.app) as client:
        response = client.get(f"/api/v1/incidents/{incident_id}/attribution")

    assert response.status_code == 200
    assert response.json()["provenance"]["tag"] == "GAP"
    assert response.json()["data"]["attribution"]["outcome"] == "NULL_STATE"
    assert response.json()["data"]["attribution"]["top"] is None
    assert response.json()["data"]["dossier"] is None


def test_json_and_pdf_report_exports_use_the_shared_report(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(api, "store", Store(str(tmp_path / "report-api.db")))

    with TestClient(api.app) as client:
        json_response = client.get(
            "/api/v1/incidents/SIH26143-2025-001/report/json"
        )
        pdf_response = client.get(
            "/api/v1/incidents/SIH26143-2025-001/report/pdf"
        )
        missing_json = client.get("/api/v1/incidents/UNKNOWN/report/json")
        missing_pdf = client.get("/api/v1/incidents/UNKNOWN/report/pdf")

    assert json_response.status_code == 200
    report = json_response.json()
    assert report["incident"]["data"]["incident_id"] == "SIH26143-2025-001"
    assert report["incident"]["provenance"]["source"] == "incident.json"
    assert report["attribution"]["data"]["attribution"]["outcome"] == "SUPPORTS_INVESTIGATION"
    assert report["runs"][0]["data"]["run_id"] == "OD-ENS-001"
    assert report["evidence"]["data"] == []
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert "SIH26143-2025-001-forensic-report.pdf" in pdf_response.headers["content-disposition"]
    assert pdf_response.content.startswith(b"%PDF-")
    assert pdf_response.content.rstrip().endswith(b"%%EOF")
    assert missing_json.status_code == 404
    assert missing_pdf.status_code == 404


def test_reports_handle_no_run_as_null_state(tmp_path, monkeypatch) -> None:
    incident_id = "SIH26143-2025-001"
    source = project_root / "data" / "incidents" / incident_id
    target = tmp_path / "data" / "incidents" / incident_id
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("runs"))
    monkeypatch.setattr(api, "artifacts", Artifacts(tmp_path / "data"))
    monkeypatch.setattr(api, "store", Store(str(tmp_path / "null-report.db")))

    with TestClient(api.app) as client:
        report = client.get(f"/api/v1/incidents/{incident_id}/report/json")
        pdf = client.get(f"/api/v1/incidents/{incident_id}/report/pdf")

    assert report.status_code == 200
    assert report.json()["attribution"]["data"]["attribution"]["outcome"] == "NULL_STATE"
    assert report.json()["runs"] == []
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")
