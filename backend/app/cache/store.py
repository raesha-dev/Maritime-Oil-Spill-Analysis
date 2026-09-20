"""Cache for simulation results keyed on candidate + environment + release_time."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class RunCache:
    """Cache for simulation results keyed on candidate + environment + release_time."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def key(self, incident_id: str, mmsi: str, release_time: str, environment: str) -> str:
        """Generate a SHA256-based cache key."""
        raw = json.dumps(
            [incident_id, mmsi, release_time, environment],
            sort_keys=True
        )
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def get(self, key: str) -> dict | None:
        """Get cached result by key."""
        path = self.root / f"{key}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def put(self, key: str, value: dict) -> None:
        """Store result in cache."""
        path = self.root / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f)
