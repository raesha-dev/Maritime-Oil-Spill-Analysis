from __future__ import annotations

import json
from pathlib import Path
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ValidationError

from ..schemas.detection import ArtifactDetection
from ..schemas.incident import (
    ArtifactHindcast,
    ArtifactIncident,
    CandidateArtifactSet,
    GeoJSONFeatureCollection,
)
from ..schemas.simulation import ArtifactRun


class ArtifactNotFoundError(FileNotFoundError):
    pass


class InvalidArtifactError(ValueError):
    pass


class Artifacts:
    """Load read-only incident artifacts from the data directory."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir).resolve()

    def _incident_dir(self, incident_id: str) -> Path:
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{2,63}", incident_id):
            raise ArtifactNotFoundError("incident artifact was not found")
        incident_dir = (self.data_dir / "incidents" / incident_id).resolve()
        if not incident_dir.is_relative_to(self.data_dir / "incidents"):
            raise ArtifactNotFoundError("incident artifact was not found")
        return incident_dir

    def _load_json(self, incident_id: str, filename: str) -> dict[str, Any]:
        incident_dir = self._incident_dir(incident_id)
        path = (incident_dir / filename).resolve()
        if not path.is_relative_to(incident_dir):
            raise ArtifactNotFoundError("incident artifact was not found")
        if not path.is_file():
            raise ArtifactNotFoundError("incident artifact was not found")

        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            raise InvalidArtifactError("incident artifact could not be read") from exc
        if not isinstance(payload, dict):
            raise InvalidArtifactError("incident artifact must contain a JSON object")
        return payload

    @staticmethod
    def _validated(payload: dict[str, Any], schema: type[BaseModel]) -> dict[str, Any]:
        try:
            return schema.model_validate(payload).model_dump(mode="json")
        except ValidationError as exc:
            raise InvalidArtifactError("incident artifact does not match its schema") from exc

    def load_incident(self, incident_id: str) -> dict[str, Any]:
        return self._validated(
            self._load_json(incident_id, "incident.json"), ArtifactIncident
        )

    def load_detection(self, incident_id: str) -> dict[str, Any]:
        return self._validated(
            self._load_json(incident_id, "detection.json"), ArtifactDetection
        )

    def load_hindcast(self, incident_id: str) -> dict[str, Any]:
        return self._validated(
            self._load_json(incident_id, "hindcast.json"), ArtifactHindcast
        )

    def load_candidates(self, incident_id: str) -> dict[str, Any]:
        return self._validated(
            self._load_json(incident_id, "candidates.json"), CandidateArtifactSet
        )

    def load_ais_tracks(self, incident_id: str) -> dict[str, Any]:
        return self._validated(
            self._load_json(incident_id, "ais_tracks.geojson"),
            GeoJSONFeatureCollection,
        )

    def load_run(self, incident_id: str, run_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id):
            raise ArtifactNotFoundError("run artifact was not found")
        return self._validated(
            self._load_json(incident_id, f"runs/{run_id}.json"), ArtifactRun
        )

    def list_runs(self, incident_id: str) -> list[dict[str, Any]]:
        runs_dir = self._incident_dir(incident_id) / "runs"
        if not runs_dir.is_dir():
            return []
        return [
            self.load_run(incident_id, path.stem)
            for path in sorted(runs_dir.glob("*.json"))
        ]

    def find_run(
        self,
        incident_id: str,
        mmsi: str,
        release_time: datetime,
        environment: str,
    ) -> dict[str, Any]:
        runs_dir = self._incident_dir(incident_id) / "runs"
        requested_time = release_time.astimezone(timezone.utc)
        if runs_dir.is_dir():
            for run in self.list_runs(incident_id):
                try:
                    run_time = datetime.fromisoformat(
                        run["release_time"].replace("Z", "+00:00")
                    ).astimezone(timezone.utc)
                except (KeyError, TypeError, ValueError):
                    continue
                if (
                    run.get("mmsi") == mmsi
                    and run_time == requested_time
                    and run.get("environment") == environment
                ):
                    return run
        raise ArtifactNotFoundError("matching precomputed run was not found")

    def load_run_frames(self, incident_id: str, run_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id):
            raise ArtifactNotFoundError("run artifact was not found")
        return self._validated(
            self._load_json(incident_id, f"runs/{run_id}_frames.geojson"),
            GeoJSONFeatureCollection,
        )

    def load_geojson(
        self, incident_id: str, name: str
    ) -> dict[str, Any]:
        if name not in {"slick_observed", "hindcast_field"}:
            raise ArtifactNotFoundError("incident artifact was not found")
        return self._validated(
            self._load_json(incident_id, f"{name}.geojson"),
            GeoJSONFeatureCollection,
        )

    def get_asset_path(self, incident_id: str, filename: str) -> Path:
        if filename not in {"slick_preview.png", "hindcast_field.png"}:
            raise ArtifactNotFoundError("incident asset was not found")
        incident_dir = self._incident_dir(incident_id)
        path = (incident_dir / filename).resolve()
        if not path.is_relative_to(incident_dir) or not path.is_file():
            raise ArtifactNotFoundError("incident asset was not found")
        return path