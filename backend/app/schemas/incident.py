from datetime import datetime

from pydantic import BaseModel


class ArtifactIncident(BaseModel):
    incident_id: str
    title: str
    scene_id: str
    satellite: str
    aoi: list[list[float]]
    detected_at: datetime
    processed_at: datetime
    model_run_id: str