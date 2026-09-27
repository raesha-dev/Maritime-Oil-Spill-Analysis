"""Cache for simulation results keyed on candidate + environment + release_time."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import uuid


class RunCache:
    """Cache for simulation results keyed on candidate + environment + release_time."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def key(self, incident_id: str, mmsi: str, release_time: str, environment: str) -> str:
        """Generate a SHA256-based cache key."""
        raw = json.dumps(
            [incident_id, mmsi, release_time, environment],
            sort_keys=True
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict | None:
        """Get cached result by key."""
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            return None
        path = self.root / f"{key}.json"
        try:
            with path.open(encoding="utf-8") as file:
                payload = json.load(file)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def put(self, key: str, value: dict) -> None:
        """Store result in cache."""
        if not re.fullmatch(r"[a-f0-9]{64}", key):
            raise ValueError("cache key must be a SHA-256 digest")
        path = self.root / f"{key}.json"
        temporary_path = self.root / f".{key}.{uuid.uuid4().hex}.tmp"
        try:
            temporary_path.write_text(
                json.dumps(value, separators=(",", ":"), sort_keys=True),
                encoding="utf-8",
            )
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)
