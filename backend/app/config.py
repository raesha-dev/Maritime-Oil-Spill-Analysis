from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


project_root = Path(__file__).resolve().parents[2]
backend_root = Path(__file__).resolve().parents[1]
load_dotenv(project_root / ".env")
load_dotenv(backend_root / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv(
        "SPILL_API_DATABASE_PATH", str(Path(__file__).resolve().parents[1] / "spill-forensics.db")
    )
    data_dir: Path = Path(os.getenv("SPILL_API_DATA_DIR", "data"))
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv(
            "SPILL_API_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",")
        if origin.strip()
    )
    source_score_threshold: float = float(os.getenv("SPILL_API_SOURCE_SCORE_THRESHOLD", "0.65"))
    minimum_score_gap: float = float(os.getenv("SPILL_API_MINIMUM_SCORE_GAP", "0.07"))
    demo_mode: bool = os.getenv("SPILL_API_DEMO_MODE", "true").lower() == "true"
    scenario: str = os.getenv("SPILL_API_SCENARIO", "clean")


settings = Settings()
