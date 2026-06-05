from __future__ import annotations

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
