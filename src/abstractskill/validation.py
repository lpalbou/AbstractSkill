"""Validation helpers for Agent Skills."""

from __future__ import annotations

import re
from typing import Any

from abstractskill.errors import SkillValidationError

# Spec (agentskills.io): 1-64 chars, lowercase a-z/0-9 and hyphens only,
# no leading/trailing hyphen, no consecutive hyphens. The structure
# [token](-[token])* enforces all hyphen rules without lookaheads.
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKILL_FILENAME = "SKILL.md"

MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500


def coerce_bool_flag(value: Any, *, field_name: str) -> bool:
    """Parse a structured-data boolean without Python truthiness traps.

    ``bool("false")`` is ``True`` in Python, so config/registry readers
    must never use bare ``bool(...)`` on YAML/JSON scalars. Accept the
    common boolean spellings and refuse everything else loudly.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "on"}:
            return True
        if lowered in {"false", "no", "0", "off"}:
            return False
    raise SkillValidationError(
        f"{field_name} must be a boolean or boolean-like scalar "
        "('true'/'false', 'yes'/'no', '1'/'0', 'on'/'off')"
    )


def validate_skill_name(name: str) -> str:
    """Validate an Agent Skills `name` field."""
    if not isinstance(name, str):
        raise SkillValidationError("skill name must be a string")
    normalized = name.strip()
    if not normalized:
        raise SkillValidationError("skill name is required")
    if len(normalized) > MAX_NAME_LENGTH:
        raise SkillValidationError(
            f"skill name must be at most {MAX_NAME_LENGTH} characters"
        )
    if not SKILL_NAME_RE.fullmatch(normalized):
        raise SkillValidationError(
            "skill name must use lowercase letters, digits, and single hyphens "
            "(no leading, trailing, or consecutive hyphens)"
        )
    return normalized


def validate_description(description: str) -> str:
    """Validate an Agent Skills `description` field (non-empty, spec max length)."""
    normalized = description.strip()
    if not normalized:
        raise SkillValidationError("SKILL.md frontmatter requires a non-empty description")
    if len(normalized) > MAX_DESCRIPTION_LENGTH:
        raise SkillValidationError(
            f"skill description must be at most {MAX_DESCRIPTION_LENGTH} characters "
            f"(got {len(normalized)})"
        )
    return normalized


def validate_compatibility(compatibility: str) -> str:
    """Validate an Agent Skills `compatibility` field (spec max length)."""
    normalized = compatibility.strip()
    if len(normalized) > MAX_COMPATIBILITY_LENGTH:
        raise SkillValidationError(
            f"skill compatibility must be at most {MAX_COMPATIBILITY_LENGTH} characters "
            f"(got {len(normalized)})"
        )
    return normalized


def validate_directory_name_match(name: str, directory_name: str) -> None:
    """Ensure the skill name matches its leaf directory name."""
    if name != directory_name:
        raise SkillValidationError(
            f"skill name {name!r} must match directory name {directory_name!r}"
        )
