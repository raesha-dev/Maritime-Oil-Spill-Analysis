"""Fixed templates for user-facing strings. No f-strings scattered across services."""

from .guard import SafeText

# Physics line
PHYSICS_LINE = SafeText(
    "Simulated release is consistent with the observed slick "
    "(overall {overall:.2f}) — a {gap:.2f} gap over the next-ranked candidate. "
    "Reflects physical plausibility, not confirmed causation."
)

# Behavioral flags
BEHAVIORAL_SPEED_DROP = SafeText(
    "AIS shows an unexplained speed drop from {from_kn:.1f} kn to {to_kn:.1f} kn "
    "at {at:%H:%M}, {lead_min} min before the estimated release window. "
    "Raises the possibility of a deliberate stop; it does not by itself "
    "establish one."
)

BEHAVIORAL_LOITERING = SafeText(
    "AIS shows vessel loitering near the release window with no navigation "
    "corroborated by radar or satellite. "
    "Raises the possibility of an intentional stop; it does not by itself "
    "establish one."
)

BEHAVIORAL_ROUTE_DEVIATION = SafeText(
    "AIS track deviates significantly from the vessel's typical routing. "
    "Raises the possibility of a course change; it does not by itself "
    "establish one."
)

BEHAVIORAL_AIS_GAP_TIMING = SafeText(
    "An AIS gap coincides with the estimated release window. "
    "Raises the possibility of intentional signal suppression; it does not by itself "
    "establish one."
)
BEHAVIORAL_ARTIFACT_FLAG = SafeText(
    "The AIS artifact records a {kind} flag: {detail}. "
    "This is contextual information, not proof of a release."
)

# Risk context
RISK_CONTEXT = SafeText(
    "Built {built_year} ({age} yrs), {hull}, {detentions} PSC detentions in the "
    "past 3 years. Background only — not evidence of causation."
)

# Verdicts
VERDICT_SUPPORTS = SafeText(
    "The available evidence supports investigating this vessel further. "
    "It does not identify this vessel as the source."
)

VERDICT_AMBIGUOUS = SafeText(
    "The top candidates are too close to distinguish reliably. "
    "Expand the candidate pool and escalate to a human investigator."
)

NULL_STATE = SafeText(
    "No sufficiently consistent vessel identified. Origin estimate may be "
    "unreliable — recommend re-examining detection and hindcast inputs."
)
NO_COMPLETED_COMPARISON = SafeText(
    "No completed comparison is available. No vessel can be assessed from the current artifacts."
)
