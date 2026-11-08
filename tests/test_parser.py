from __future__ import annotations

import html

import pytest

from abstractskill import (
    SkillParseError,
    SkillValidationError,
    content_hash,
    format_available_skills_xml,
    parse_skill_md,
)


def test_parse_skill_md_extracts_frontmatter_and_body() -> None:
    text = """---
name: demo-skill
description: A demo skill for tests.
license: MIT
allowed-tools: read_file write_file
metadata:
  version: "1"
---

# Instructions

Do the thing.
"""
    doc = parse_skill_md(text, directory_name="demo-skill")

    assert doc.metadata.name == "demo-skill"
    assert doc.metadata.description == "A demo skill for tests."
    assert doc.metadata.license == "MIT"
    assert doc.metadata.allowed_tools == ("read_file", "write_file")
    assert doc.metadata.metadata == {"version": "1"}
    assert "# Instructions" in doc.body
    assert doc.content_hash == content_hash(text)


def test_parse_skill_md_requires_frontmatter() -> None:
    with pytest.raises(SkillParseError):
        parse_skill_md("no frontmatter here")


def test_parse_skill_md_accepts_crlf_line_endings() -> None:
    # Windows-authored skills arrive with CRLF; they must parse identically.
    text = (
        "---\r\n"
        "name: demo-skill\r\n"
        "description: CRLF authored skill.\r\n"
        "---\r\n"
        "\r\n"
        "# Instructions\r\n"
    )
    doc = parse_skill_md(text, directory_name="demo-skill")
    assert doc.metadata.name == "demo-skill"
    assert "# Instructions" in doc.body


def test_parse_skill_md_ignores_indented_delimiter_inside_frontmatter() -> None:
    # An indented "---" is legitimate YAML content (e.g. inside a block
    # scalar) and must not close the frontmatter early.
    text = """---
name: demo-skill
description: |
  first line
   ---
  still description
---

Body.
"""
    doc = parse_skill_md(text, directory_name="demo-skill")
    assert "still description" in doc.metadata.description
    assert doc.body.strip() == "Body."


def test_parse_skill_md_does_not_split_on_exotic_line_boundaries() -> None:
    # str.splitlines() split on \x0c (form feed) and let an embedded "---"
    # close the frontmatter early: the description was SILENTLY truncated
    # and the rest injected into the body, while YAML never saw the \x0c.
    # Only \n, \r\n, \r are line breaks here, so the character reaches
    # PyYAML, which refuses it LOUDLY — refusal over silent truncation.
    text = (
        "---\n"
        "name: demo-skill\n"
        "description: legit\x0c---\x0cinjected: pwned\n"
        "---\n"
        "BODY\n"
    )
    with pytest.raises(SkillParseError):
        parse_skill_md(text, directory_name="demo-skill")


def test_parse_skill_md_rejects_consecutive_hyphen_names() -> None:
    text = """---
name: pdf--processing
description: Invalid name per spec.
---
"""
    with pytest.raises(SkillValidationError):
        parse_skill_md(text)


def test_parse_skill_md_enforces_description_ceiling() -> None:
    long_description = "x" * 1025
    text = f"""---
name: demo-skill
description: {long_description}
---
"""
    with pytest.raises(SkillValidationError):
        parse_skill_md(text)


def test_parse_skill_md_enforces_compatibility_ceiling() -> None:
    long_compat = "y" * 501
    text = f"""---
name: demo-skill
description: Fine.
compatibility: {long_compat}
---
"""
    with pytest.raises(SkillValidationError):
        parse_skill_md(text)


def test_parse_skill_md_validates_directory_name() -> None:
    text = """---
name: demo-skill
description: Demo
---
"""
    with pytest.raises(SkillValidationError):
        parse_skill_md(text, directory_name="other-name")


def test_format_available_skills_xml_is_deterministic() -> None:
    from abstractskill.models import SkillMetadata

    skills = [
        SkillMetadata(name="beta", description="Second"),
        SkillMetadata(name="alpha", description="First"),
    ]
    rendered = format_available_skills_xml(skills)
    assert rendered.index("alpha") < rendered.index("beta")
    assert "<available_skills>" in rendered
    assert "<name>alpha</name>" in rendered
    # Metadata-only skills know no location: no <path>, no hint (unchanged shape).
    assert "<path>" not in rendered and "read_file" not in rendered


def test_format_available_skills_xml_names_each_skill_path(tmp_path) -> None:
    """The block tells the model WHERE a skill is (operator 2026-11-08: an agent
    searched the workspace and read a stale copy; the host serves files under
    the listed path even where its workspace policies would refuse them)."""
    from pathlib import Path

    from abstractskill.models import SkillMetadata
    from abstractskill.prompt import SKILL_PATH_HINT

    located = tmp_path / "shelf" / "skills" / "alpha" / "SKILL.md"
    skills = [
        SkillMetadata(name="alpha", description="First", source_path=located),
        SkillMetadata(name="beta", description="Second & more"),
    ]
    rendered = format_available_skills_xml(skills, paths={"beta": Path("/elsewhere/beta/SKILL.md")})
    assert f"<path>{html.escape(str(located))}</path>" in rendered
    assert "<path>/elsewhere/beta/SKILL.md</path>" in rendered, "an explicit path override wins"
    assert rendered.rstrip().endswith(SKILL_PATH_HINT)
    assert "read the SKILL.md at its <path> with read_file" in rendered
    assert rendered.index("</available_skills>") < rendered.index(SKILL_PATH_HINT)
    # Determinism: the same input renders the same bytes.
    assert rendered == format_available_skills_xml(skills, paths={"beta": Path("/elsewhere/beta/SKILL.md")})
