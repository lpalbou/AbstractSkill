"""Prompt helpers for progressive skill disclosure."""

from __future__ import annotations

import html

from abstractskill.models import SkillMetadata


def format_available_skills_xml(skills: list[SkillMetadata]) -> str:
    """Render a deterministic `<available_skills>` block for host prompts."""
    if not skills:
        return "<available_skills></available_skills>"

    lines = ["<available_skills>"]
    for skill in sorted(skills, key=lambda item: item.name):
        lines.append("  <skill>")
        lines.append(f"    <name>{html.escape(skill.name)}</name>")
        lines.append(f"    <description>{html.escape(skill.description)}</description>")
        lines.append("  </skill>")
    lines.append("</available_skills>")
    return "\n".join(lines)
