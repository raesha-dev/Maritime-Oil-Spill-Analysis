"""Tests for artifact loading from data/incidents/ directory."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import Settings, backend_root, project_root, resolve_config_path
from app.services.artifacts import (
    ArtifactNotFoundError,
    Artifacts,
    InvalidArtifactError,
)


def test_default_paths_are_independent_of_working_directory() -> None:
    settings = Settings()
    assert settings.data_dir == project_root / "data"
    assert Path(settings.database_path) == backend_root / "spill-forensics.db"
    assert settings.cache_dir == backend_root / ".cache"
    assert settings.cache_dir == backend_root / ".cache"
    assert resolve_config_path("data", Path("unused"), project_root) == project_root / "data"


def test_settings_reject_invalid_thresholds_and_data_directories(tmp_path) -> None:
    settings = Settings()
    with pytest.raises(ValueError, match="source_score_threshold"):
        Settings(**{**settings.__dict__, "source_score_threshold": 1.1})
    with pytest.raises(ValueError, match="SPILL_API_DATA_DIR"):
        Settings(**{**settings.__dict__, "data_dir": tmp_path / "missing"})


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


def test_load_ais_and_precomputed_run_artifacts() -> None:
    artifacts = Artifacts(project_root / "data")

    tracks = artifacts.load_ais_tracks("SIH26143-2025-001")
    run = artifacts.load_run("SIH26143-2025-001", "OD-ENS-001")
    frames = artifacts.load_run_frames("SIH26143-2025-001", "OD-ENS-001")

    assert tracks["type"] == "FeatureCollection"
    assert run["candidate_id"] == "OCEAN_PRIDE"
    assert frames["type"] == "FeatureCollection"
    matched = artifacts.find_run(
        "SIH26143-2025-001",
        "563214000",
        datetime(2025, 9, 8, 16, tzinfo=timezone.utc),
        "cmes-era5-v1",
    )
    assert matched["run_id"] == "OD-ENS-001"

    with pytest.raises(ArtifactNotFoundError):
        artifacts.find_run(
            "SIH26143-2025-001",
            "563214000",
            datetime(2025, 9, 8, 17, tzinfo=timezone.utc),
            "cmes-era5-v1",
        )


def test_artifact_paths_reject_traversal_and_unknown_files() -> None:
    artifacts = Artifacts(project_root / "data")

    with pytest.raises(ArtifactNotFoundError):
        artifacts.load_incident("../backend")
    with pytest.raises(ArtifactNotFoundError):
        artifacts.load_run("SIH26143-2025-001", "../../config")
    with pytest.raises(ArtifactNotFoundError):
        artifacts.load_geojson("SIH26143-2025-001", "../../config")
    with pytest.raises(ArtifactNotFoundError):
        artifacts.get_asset_path("SIH26143-2025-001", "../../.env")


def test_invalid_artifact_schema_is_rejected(tmp_path) -> None:
    incident_dir = tmp_path / "incidents" / "SIH26143-2025-001"
    incident_dir.mkdir(parents=True)
    (incident_dir / "incident.json").write_text(
        '{"incident_id":"SIH26143-2025-001"}', encoding="utf-8"
    )

    with pytest.raises(InvalidArtifactError):
        Artifacts(tmp_path).load_incident("SIH26143-2025-001")


def test_get_asset_path() -> None:
    """Should return path to asset file."""
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    artifacts = Artifacts(data_dir)
    path = artifacts.get_asset_path("SIH26143-2025-001", "slick_preview.png")
    assert path.name == "slick_preview.png"
