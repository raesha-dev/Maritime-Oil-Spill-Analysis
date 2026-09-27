from datetime import datetime

from pydantic import BaseModel


class ArtifactDetection(BaseModel):
    scene_id: str
    satellite: str
    acquired_at: datetime
    centroid: list[float]
    area_km2: float
    oil_confidence: float
    classification: str
    confidence_tier: str
    pipeline_status: str
    classification_breakdown: dict[str, float]