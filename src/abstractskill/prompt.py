"""Prompt helpers for progressive skill disclosure."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Mapping

from abstractskill.models import SkillMetadata

#: The sentence that closes a block carrying at least one ``<path>``: the model
#: reads the skill where the host says it is, instead of searching the
#: workspace and finding a stale copy (operator 2026-11-08).
SKILL_PATH_HINT = (
    "To use a skill, read the SKILL.md at its <path> with read_file "
    "(the files beside it, under the same folder, are readable too); "
    "do not search the workspace for another copy."
)


def format_available_skills_xml(
    skills: list[SkillMetadata],
    *,
    descriptions: Mapping[str, str] | None = None,
    paths: Mapping[str, Path | str] | None = None,
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

    Each skill whose location is known — ``paths[name]`` when given, else the
    SKILL.md the loader read (``SkillMetadata.source_path``) — also renders a
    ``<path>`` element, and the block then ends with :data:`SKILL_PATH_HINT`.
    The path is the one place the model is told where the skill IS: a run's
    host serves files under it even where its workspace policies would refuse
    them (AbstractRuntime's ``read_file`` interception), so the model never
    has to search for the skill. A metadata-only skill (no path known) renders
    as before.
    """
    if not skills:
        return "<available_skills></available_skills>"

    overrides = descriptions or {}
    path_overrides = paths or {}
    lines = ["<available_skills>"]
    any_path = False
    for skill in sorted(skills, key=lambda item: item.name):
        description = overrides.get(skill.name, skill.description)
        location = path_overrides.get(skill.name, skill.source_path)
        lines.append("  <skill>")
        lines.append(f"    <name>{html.escape(skill.name)}</name>")
        lines.append(f"    <description>{html.escape(description)}</description>")
        if location:
            any_path = True
            lines.append(f"    <path>{html.escape(str(location))}</path>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    if any_path:
        lines.append(SKILL_PATH_HINT)
    return "\n".join(lines)
