from __future__ import annotations

import re

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


BANNED = [
    r"\bcaused?\b",
    r"\bresponsible\b",
    r"\bguilty\b",
    r"\bculprit\b",
    r"\bidentified as the (source|polluter)\b",
    r"\bthe source is\b",
    r"\bproven\b",
    r"\bconvicted?\b",
    r"\bperpetrator\b",
]

_BANNED_RE = [re.compile(p, re.IGNORECASE) for p in BANNED]


class VocabularyViolation(ValueError):
    pass


def assert_safe(text: str) -> str:
    for rx in _BANNED_RE:
        if rx.search(text):
            raise VocabularyViolation(
                f"Forensic-safe vocabulary violation: {rx.pattern!r} in {text!r}"
            )
    return text


class SafeText(str):
    """Any user-facing string field. Validated at construction time."""

    def __new__(cls, value: str) -> "SafeText":
        assert_safe(value)
        return super().__new__(cls, value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source: type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls, core_schema.str_schema()
        )
