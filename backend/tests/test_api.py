from fastapi.testclient import TestClient

import app.main as api
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
            "components": {"spatial_iou": 0.89, "centroid_match": 0.84, "shape_match": 0.72, "area_curve_dtw": 0.78},
        }
        first_simulation = client.post("/api/v1/simulations", json=simulation_body)
        cached_simulation = client.post("/api/v1/simulations", json=simulation_body)
        assert first_simulation.status_code == 201
        assert first_simulation.json()["cached"] is False
        assert cached_simulation.json()["cached"] is True

        assessment = client.post("/api/v1/incidents/SIH26143-2025-001/assessment", json={"candidates": [{
            "candidate": candidate, "source_consistency_score": first_simulation.json()["source_consistency_score"],
        }]})
        assert assessment.status_code == 200
        assert "does not establish causation" in assessment.json()["message"]

        message = client.post("/api/v1/messages", json={
            "incident_id": "SIH26143-2025-001", "role": "analyst", "body": "Run the comparison."
        })
        assert message.status_code == 201
        assert client.get("/api/v1/incidents/SIH26143-2025-001/messages").json()[0]["body"] == "Run the comparison."

        with client.websocket_connect("/api/v1/incidents/SIH26143-2025-001/messages/live") as websocket:
            websocket.send_json({"role": "system", "body": "Simulation queued."})
            assert websocket.receive_json()["body"] == "Simulation queued."
