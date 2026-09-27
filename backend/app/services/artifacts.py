from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Artifacts:
    """Load read-only incident artifacts from the data directory."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)

    def _incident_dir(self, incident_id: str) -> Path:
        return self.data_dir / "incidents" / incident_id

    def _load_json(self, incident_id: str, filename: str) -> dict[str, Any]:
        path = self._incident_dir(incident_id) / filename

        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def load_incident(self, incident_id: str) -> dict[str, Any]:
        return self._load_json(incident_id, "incident.json")

    def load_detection(self, incident_id: str) -> dict[str, Any]:
        return self._load_json(incident_id, "detection.json")

    def load_hindcast(self, incident_id: str) -> dict[str, Any]:
        return self._load_json(incident_id, "hindcast.json")

    def load_candidates(self, incident_id: str) -> dict[str, Any]:
        return self._load_json(incident_id, "candidates.json")

    def load_geojson(
        self, incident_id: str, name: str
    ) -> dict[str, Any]:
        return self._load_json(incident_id, f"{name}.geojson")

    def get_asset_path(self, incident_id: str, filename: str) -> Path:
        return self._incident_dir(incident_id) / filename