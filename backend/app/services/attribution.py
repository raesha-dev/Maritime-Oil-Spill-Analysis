from __future__ import annotations

from ..config import Settings
from ..schemas.evidence import (
    AttributionBundle,
    AttributionOutcome,
    AttributionResult,
    Dossier,
    DossierLine,
)
from ..schemas.incident import CandidateArtifactSet
from ..schemas.simulation import ArtifactRun
from ..schemas.vessel import VesselCandidate
from ..vocabulary.templates import (
    BEHAVIORAL_ARTIFACT_FLAG,
    NO_COMPLETED_COMPARISON,
    NULL_STATE,
    PHYSICS_LINE,
    RISK_CONTEXT,
    VERDICT_AMBIGUOUS,
    VERDICT_SUPPORTS,
)


def build_fixture_attribution(
    candidate_artifacts: CandidateArtifactSet,
    run: ArtifactRun | None,
    settings: Settings,
) -> AttributionBundle:
    if run is None:
        return AttributionBundle(
            attribution=AttributionResult(
                outcome=AttributionOutcome.NULL_STATE,
                message=NO_COMPLETED_COMPARISON,
            )
        )

    candidate_data = next(
        (item for item in candidate_artifacts.candidates if item.mmsi == run.mmsi),
        None,
    )
    if candidate_data is None:
        return AttributionBundle(
            attribution=AttributionResult(
                outcome=AttributionOutcome.NULL_STATE,
                message=NO_COMPLETED_COMPARISON,
            )
        )

    candidate = candidate_data.model_copy(
        update={"consistency_score": run.source_consistency_score}
    )
    score = run.source_consistency_score
    gap = run.gap_to_next_best

    if score < settings.source_score_threshold:
        outcome = AttributionOutcome.NULL_STATE
        message = NULL_STATE
        top = None
        dossier = None
    elif gap is None or gap < settings.minimum_score_gap:
        outcome = AttributionOutcome.AMBIGUOUS
        message = VERDICT_AMBIGUOUS
        top = [candidate]
        dossier = build_dossier(candidate, run, gap, message)
    else:
        outcome = AttributionOutcome.SUPPORTS_INVESTIGATION
        message = VERDICT_SUPPORTS
        top = [candidate]
        dossier = build_dossier(candidate, run, gap, message)

    return AttributionBundle(
        attribution=AttributionResult(
            outcome=outcome,
            message=message,
            top=top,
            gap=gap,
        ),
        dossier=dossier,
    )


def build_dossier(
    candidate: VesselCandidate,
    run: ArtifactRun,
    gap: float | None,
    verdict: str,
) -> Dossier:
    lines = [
        DossierLine(
            tag="PHYSICS",
            text=PHYSICS_LINE.format(
                overall=run.source_consistency_score,
                gap=gap if gap is not None else 0,
            ),
        )
    ]

    for flag in candidate.behavioral_flags:
        lines.append(
            DossierLine(
                tag="BEHAVIORAL",
                text=BEHAVIORAL_ARTIFACT_FLAG.format(
                    kind=flag.kind.replace("_", " ").lower(),
                    detail=flag.detail,
                ),
            )
        )

    risk = candidate.risk_profile
    if (
        risk is not None
        and risk.built_year is not None
        and risk.hull_type is not None
        and risk.psc_detentions_3yr is not None
    ):
        age = max(0, run.generated_at.year - risk.built_year)
        lines.append(
            DossierLine(
                tag="RISK_CONTEXT",
                text=RISK_CONTEXT.format(
                    built_year=risk.built_year,
                    age=age,
                    hull=risk.hull_type.lower(),
                    detentions=risk.psc_detentions_3yr,
                ),
            )
        )

    return Dossier(
        vessel_name=candidate.name,
        headline=f"Further investigation: {candidate.name}",
        lines=lines,
        verdict=verdict,
    )