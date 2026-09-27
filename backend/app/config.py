from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


project_root = Path(__file__).resolve().parents[2]
backend_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")
load_dotenv(backend_root / ".env", override=True)


def resolve_config_path(value: str | None, default: Path, base: Path) -> Path:
    path = Path(value) if value else default
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


@dataclass(frozen=True)
class Settings:
    database_path: str = str(
        resolve_config_path(
            os.getenv("SPILL_API_DATABASE_PATH"),
            Path("spill-forensics.db"),
            backend_root,
        )
    )
    data_dir: Path = resolve_config_path(
        os.getenv("SPILL_API_DATA_DIR"), Path("data"), project_root
    )
    cache_dir: Path = resolve_config_path(
        os.getenv("SPILL_API_CACHE_DIR"), Path(".cache"), backend_root
    )
    cache_dir: Path = resolve_config_path(
        os.getenv("SPILL_API_CACHE_DIR"), Path(".cache"), backend_root
    )
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "SPILL_API_ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:5173",
        ).split(",")
        if origin.strip()
    )
    source_score_threshold: float = float(
        os.getenv("SPILL_API_SOURCE_SCORE_THRESHOLD", "0.65")
    )
    minimum_score_gap: float = float(
        os.getenv("SPILL_API_MINIMUM_SCORE_GAP", "0.07")
    )
    demo_mode: bool = env_bool("SPILL_API_DEMO_MODE", True)
    scenario: str = os.getenv("SPILL_API_SCENARIO", "clean")

    def __post_init__(self) -> None:
        for name, value in (
            ("source_score_threshold", self.source_score_threshold),
            ("minimum_score_gap", self.minimum_score_gap),
        ):
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be a finite value between 0 and 1")

        if not self.allowed_origins:
            raise ValueError("SPILL_API_ALLOWED_ORIGINS must contain at least one origin")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"Invalid CORS origin: {origin!r}")

        if not self.data_dir.is_dir():
            raise ValueError(f"SPILL_API_DATA_DIR is not an existing directory: {self.data_dir}")
        if self.scenario not in {"clean", "null_state"}:
            raise ValueError("SPILL_API_SCENARIO must be 'clean' or 'null_state'")


settings = Settings()