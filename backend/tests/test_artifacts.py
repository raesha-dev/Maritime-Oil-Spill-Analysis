"""Tests for artifact loading from data/incidents/ directory."""

from pathlib import Path

from app.services.artifacts import Artifacts


def test_load_incident() -> None:
    """Should load incident.json from data directory."""
    # Test file is in backend/tests/, so parents[2] = project root
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    incident = artifacts.load_incident("SIH26143-2025-001")
    assert incident["incident_id"] == "SIH26143-2025-001"
    assert incident["title"] == "Bay of Bengal demonstration"
    assert incident["scene_id"] == "S1A_IW_GRDH_20250909"
    assert incident["model_run_id"] == "OD-ENS-0914-07"


def test_load_detection() -> None:
    """Should load detection.json from data directory."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    detection = artifacts.load_detection("SIH26143-2025-001")
    assert detection["centroid"] == [92.861, 12.374]
    assert detection["area_km2"] == 12.4
    assert detection["oil_confidence"] == 0.91
    assert detection["classification"] == "oil"


def test_load_hindcast() -> None:
    """Should load hindcast.json from data directory."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    hindcast = artifacts.load_hindcast("SIH26143-2025-001")
    assert hindcast["center"] == [92.54, 12.31]
    assert hindcast["radius_km"] == 18
    assert hindcast["release_window_start"] == "2025-09-08T14:00:00Z"


def test_load_candidates() -> None:
    """Should load candidates.json from data directory."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    candidates = artifacts.load_candidates("SIH26143-2025-001")
    assert len(candidates["candidates"]) == 5
    assert candidates["candidates"][0]["name"] == "OCEAN PRIDE"
    assert candidates["candidates"][0]["mmsi"] == "563214000"
    assert candidates["raw_candidate_count"] == 18


def test_load_geojson() -> None:
    """Should load GeoJSON files from data directory."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    slick = artifacts.load_geojson("SIH26143-2025-001", "slick_observed")
    assert slick["type"] == "FeatureCollection"
    assert len(slick["features"]) == 1
    assert slick["features"][0]["properties"]["kind"] == "observed"


def test_get_asset_path() -> None:
    """Should return path to asset file."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    path = artifacts.get_asset_path("SIH26143-2025-001", "slick_preview.png")
    assert path.name == "slick_preview.png"
