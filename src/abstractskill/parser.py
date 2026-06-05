"""SKILL.md parsing."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from abstractskill.errors import SkillParseError, SkillValidationError
from abstractskill.hash import content_hash
from abstractskill.models import SkillDocument, SkillMetadata
from abstractskill.validation import validate_skill_name

_FRONTMATTER_DELIM = "---"


def _split_frontmatter(text: str) -> tuple[Mapping[str, Any], str]:
    stripped = text.lstrip("\ufeff")
    if not stripped.startswith(f"{_FRONTMATTER_DELIM}\n"):
        raise SkillParseError("SKILL.md must start with YAML frontmatter")

    lines = stripped.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIM:
        raise SkillParseError("SKILL.md frontmatter opening delimiter is missing")

    closing_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == _FRONTMATTER_DELIM:
            closing_idx = idx
            break
    if closing_idx is None:
        raise SkillParseError("SKILL.md frontmatter closing delimiter is missing")

    frontmatter_text = "\n".join(lines[1:closing_idx])
    body = "\n".join(lines[closing_idx + 1 :])
    if body.startswith("\n"):
        body = body[1:]

    try:
        loaded = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as exc:
        raise SkillParseError(f"invalid YAML frontmatter: {exc}") from exc

    if not isinstance(loaded, dict):
        raise SkillParseError("SKILL.md frontmatter must be a mapping")
    return loaded, body


def _parse_allowed_tools(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        tokens = raw.split()
    elif isinstance(raw, list):
        tokens = [str(item).strip() for item in raw if str(item).strip()]
    else:
        raise SkillValidationError("allowed-tools must be a string or list of strings")
    return tuple(tokens)


def _metadata_from_frontmatter(
    frontmatter: Mapping[str, Any],
    *,
    source_path: Path | None = None,
) -> SkillMetadata:
    if "name" not in frontmatter:
        raise SkillValidationError("SKILL.md frontmatter requires 'name'")
    if "description" not in frontmatter:
        raise SkillValidationError("SKILL.md frontmatter requires 'description'")

    name = validate_skill_name(str(frontmatter["name"]))
    description = str(frontmatter["description"]).strip()
    if not description:
        raise SkillValidationError("SKILL.md frontmatter requires a non-empty description")

    license_value = frontmatter.get("license")
    compatibility = frontmatter.get("compatibility")
    extra = frontmatter.get("metadata")
    if extra is not None and not isinstance(extra, dict):
        raise SkillValidationError("metadata frontmatter field must be a mapping")

    allowed_raw = frontmatter.get("allowed-tools", frontmatter.get("allowed_tools"))
    allowed_tools = _parse_allowed_tools(allowed_raw)

    return SkillMetadata(
        name=name,
        description=description,
        license=str(license_value).strip() if license_value is not None else None,
        compatibility=str(compatibility).strip() if compatibility is not None else None,
        allowed_tools=allowed_tools,
        metadata=dict(extra or {}),
        source_path=source_path,
    )


def parse_skill_md(
    text: str,
    *,
    source_path: Path | None = None,
    directory_name: str | None = None,
) -> SkillDocument:
    """Parse SKILL.md text into metadata and instructions."""
    frontmatter, body = _split_frontmatter(text)
    metadata = _metadata_from_frontmatter(frontmatter, source_path=source_path)

    if directory_name is not None:
        from abstractskill.validation import validate_directory_name_match

        validate_directory_name_match(metadata.name, directory_name)

    return SkillDocument(
        metadata=metadata,
        body=body,
        raw=text,
        content_hash=content_hash(text),
    )
