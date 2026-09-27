"""Tests for vocabulary guard - blocks causal language."""

import pytest
from pydantic import ValidationError

from app.vocabulary.guard import VocabularyViolation, assert_safe, SafeText
from app.vocabulary.templates import PHYSICS_LINE, VERDICT_SUPPORTS, NULL_STATE
from app.schemas.evidence import DossierLine
from app.models import Assessment, AssessmentState


def test_vocabulary_guard_blocks_causal_language() -> None:
    """The vocabulary guard must block any causal claim."""
    with pytest.raises(VocabularyViolation):
        assert_safe("This vessel caused the spill.")
    with pytest.raises(VocabularyViolation):
        assert_safe("The source is this vessel.")
    with pytest.raises(VocabularyViolation):
        assert_safe("This vessel is responsible for the oil.")
    with pytest.raises(VocabularyViolation):
        assert_safe("This vessel is the culprit.")
    with pytest.raises(VocabularyViolation):
        assert_safe("This vessel was identified as the polluter.")


def test_vocabulary_guard_allows_safe_text() -> None:
    """Safe forensic language must be allowed."""
    assert_safe("This vessel is consistent with the observed slick.")
    assert_safe("This result supports further investigation.")
    assert_safe("This result raises the possibility that this candidate merits further investigation.")
    assert_safe("The assessment does not rule out other vessels.")


def test_safe_text_in_templates() -> None:
    """Templates should return SafeText."""
    assert isinstance(PHYSICS_LINE, SafeText)
    assert isinstance(VERDICT_SUPPORTS, SafeText)
    assert isinstance(NULL_STATE, SafeText)


def test_safe_text_blocks_causal_when_used() -> None:
    """SafeText must validate at construction."""
    # Safe text works
    SafeText("This vessel is consistent with the observed slick.")

    # Causal text fails
    with pytest.raises(VocabularyViolation):
        SafeText("This vessel caused the spill.")


def test_pydantic_user_facing_fields_enforce_safe_text() -> None:
    with pytest.raises(ValidationError) as dossier_error:
        DossierLine(tag="PHYSICS", text="This vessel caused the spill.")
    assert isinstance(dossier_error.value.errors()[0]["ctx"]["error"], VocabularyViolation)

    with pytest.raises(ValidationError) as assessment_error:
        Assessment(
            state=AssessmentState.further_investigation,
            top_candidate=None,
            message="This vessel caused the spill.",
            dossier=[],
        )
    assert isinstance(assessment_error.value.errors()[0]["ctx"]["error"], VocabularyViolation)
