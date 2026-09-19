"""Prompt helpers for progressive skill disclosure."""

from __future__ import annotations

import html
from typing import Mapping

from abstractskill.models import SkillMetadata


def format_available_skills_xml(
    skills: list[SkillMetadata],
    *,
    descriptions: Mapping[str, str] | None = None,
) -> str:
    """Render a deterministic `<available_skills>` block for host prompts.

    ``descriptions`` is an optional per-name override for the activation text.
    A vendored skill's own ``description`` may name a foreign product (the
    codex skills say "Use when Codex needs to…"); the trust layer carries a
    host-side ``activation_description`` override on the validation record so
    the catalog activates on framework-appropriate text WITHOUT mutating the
    vendored tree. Pass ``registry.activation_descriptions()`` here to apply
    those overrides. The map is keyed by skill name; the host is responsible
    for having resolved the active version per name.
    """
    if not skills:
        return "<available_skills></available_skills>"

    overrides = descriptions or {}
    lines = ["<available_skills>"]
    for skill in sorted(skills, key=lambda item: item.name):
        description = overrides.get(skill.name, skill.description)
        lines.append("  <skill>")
        lines.append(f"    <name>{html.escape(skill.name)}</name>")
        lines.append(f"    <description>{html.escape(description)}</description>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)
