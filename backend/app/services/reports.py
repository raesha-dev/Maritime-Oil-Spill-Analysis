from __future__ import annotations

from datetime import datetime, timezone

from ..config import Settings
from ..models import EvidenceEvent
from ..schemas.common import Envelope, EvidenceTag, Provenance
from ..schemas.detection import ArtifactDetection
from ..schemas.evidence import AttributionBundle
from ..schemas.incident import (
    ArtifactHindcast,
    ArtifactIncident,
    CandidateArtifactSet,
)
from ..schemas.report import ForensicReport
from ..schemas.simulation import ArtifactRun
from .artifacts import ArtifactNotFoundError, Artifacts
from .attribution import build_fixture_attribution


def build_report(
    incident_id: str,
    artifacts: Artifacts,
    settings: Settings,
    evidence: list[EvidenceEvent],
    run_id: str | None = None,
) -> ForensicReport:
    incident_data = artifacts.load_incident(incident_id)
    incident = ArtifactIncident.model_validate(incident_data)
    processed_at = incident.processed_at
    unavailable: list[str] = []

    def load_optional_json(filename: str, loader, schema):
        try:
            data = schema.model_validate(loader(incident_id))
        except ArtifactNotFoundError:
            unavailable.append(f"Optional artifact unavailable: {filename}")
            return None
        return Envelope(
            data=data,
            provenance=Provenance(
                tag=EvidenceTag.INFERRED,
                source=filename,
                generated_at=processed_at,
                model_run_id=incident.model_run_id,
            ),
        )

    detection = load_optional_json(
        "detection.json", artifacts.load_detection, ArtifactDetection
    )
    hindcast = load_optional_json(
        "hindcast.json", artifacts.load_hindcast, ArtifactHindcast
    )
    candidates = load_optional_json(
        "candidates.json", artifacts.load_candidates, CandidateArtifactSet
    )

    runs = [ArtifactRun.model_validate(run) for run in artifacts.list_runs(incident_id)]
    if run_id is not None:
        attributed_run = ArtifactRun.model_validate(
            artifacts.load_run(incident_id, run_id)
        )
    else:
        attributed_run = runs[0] if len(runs) == 1 else None
        if len(runs) > 1:
            unavailable.append("Attribution omitted: specify a run when multiple runs exist")
    attribution_bundle = (
        build_fixture_attribution(candidates.data, attributed_run, settings)
        if candidates is not None
        else build_fixture_attribution(CandidateArtifactSet(candidates=[], raw_candidate_count=0), None, settings)
    )

    return ForensicReport(
        generated_at=datetime.now(timezone.utc),
        incident=Envelope(
            data=incident,
            provenance=Provenance(
                tag=EvidenceTag.OBSERVED,
                source="incident.json",
                generated_at=processed_at,
                model_run_id=incident.model_run_id,
            ),
        ),
        detection=detection,
        hindcast=hindcast,
        candidates=candidates,
        attribution=Envelope(
            data=attribution_bundle,
            provenance=Provenance(
                tag=EvidenceTag.COMPARED if attributed_run else EvidenceTag.GAP,
                source=(
                    f"runs/{attributed_run.run_id}.json"
                    if attributed_run
                    else "no unique completed run"
                ),
                generated_at=attributed_run.generated_at if attributed_run else processed_at,
                model_run_id=(
                    attributed_run.model_run_id if attributed_run else incident.model_run_id
                ),
            ),
        ),
        evidence=Envelope(
            data=evidence,
            provenance=Provenance(
                tag=EvidenceTag.SYSTEM,
                source="SQLite evidence_events",
                generated_at=datetime.now(timezone.utc),
                model_run_id=incident.model_run_id,
                assumptions=["Only persisted evidence events are included."],
            ),
        ),
        runs=[
            Envelope(
                data=run,
                provenance=Provenance(
                    tag=EvidenceTag.SIMULATED,
                    source=f"runs/{run.run_id}.json",
                    generated_at=run.generated_at,
                    model_run_id=run.model_run_id,
                ),
            )
            for run in runs
        ],
        unavailable_artifacts=unavailable,
    )