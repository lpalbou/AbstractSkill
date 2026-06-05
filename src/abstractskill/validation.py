"""Validation helpers for Agent Skills."""

from __future__ import annotations

import re

from abstractskill.errors import SkillValidationError

SKILL_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
SKILL_FILENAME = "SKILL.md"


def validate_skill_name(name: str) -> str:
    """Validate an Agent Skills `name` field."""
    if not isinstance(name, str):
        raise SkillValidationError("skill name must be a string")
    normalized = name.strip()
    if not normalized:
        raise SkillValidationError("skill name is required")
    if len(normalized) > 64:
        raise SkillValidationError("skill name must be at most 64 characters")
    if not SKILL_NAME_RE.fullmatch(normalized):
        raise SkillValidationError(
            "skill name must use lowercase letters, digits, and hyphens only"
        )
    return normalized


def validate_directory_name_match(name: str, directory_name: str) -> None:
    """Ensure the skill name matches its leaf directory name."""
    if name != directory_name:
        raise SkillValidationError(
            f"skill name {name!r} must match directory name {directory_name!r}"
        )
