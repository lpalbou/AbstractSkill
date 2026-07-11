from __future__ import annotations

from pathlib import Path

import pytest

from abstractskill import FilesystemSkillLoader, SkillNotFoundError


def _write_skill(root: Path, name: str, description: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {name}
description: {description}
---

Body for {name}.
""",
        encoding="utf-8",
    )


def test_filesystem_loader_discovers_and_loads(tmp_path: Path) -> None:
    user_root = tmp_path / "user"
    project_root = tmp_path / "project"
    _write_skill(user_root, "shared-skill", "User copy")
    _write_skill(project_root, "shared-skill", "Project override")
    _write_skill(project_root, "project-only", "Project skill")

    loader = FilesystemSkillLoader([user_root, project_root])
    discovered = loader.discover()

    assert [skill.name for skill in discovered] == ["project-only", "shared-skill"]
    assert discovered[1].description == "Project override"

    loaded = loader.load("project-only")
    assert loaded.root_dir == project_root / "project-only"
    assert "Body for project-only." in loaded.document.body


def test_filesystem_loader_missing_skill(tmp_path: Path) -> None:
    loader = FilesystemSkillLoader([tmp_path])
    with pytest.raises(SkillNotFoundError):
        loader.load("missing")


def _write_broken_skill(root: Path, name: str) -> None:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("no frontmatter at all\n", encoding="utf-8")


def test_discover_warns_on_broken_skill_instead_of_silent_skip(tmp_path: Path) -> None:
    _write_skill(tmp_path, "good-skill", "Valid")
    _write_broken_skill(tmp_path, "broken-skill")

    warnings: list[str] = []
    loader = FilesystemSkillLoader([tmp_path])
    discovered = loader.discover(on_warning=warnings.append)

    assert [skill.name for skill in discovered] == ["good-skill"]
    assert len(warnings) == 1
    assert "#FALLBACK" in warnings[0]
    assert "broken-skill" in warnings[0]


def test_load_and_discover_agree_when_override_copy_is_broken(tmp_path: Path) -> None:
    # A broken later-root copy must not shadow a valid earlier-root skill:
    # whatever discover lists, load must return.
    user_root = tmp_path / "user"
    project_root = tmp_path / "project"
    _write_skill(user_root, "shared-skill", "Valid user copy")
    _write_broken_skill(project_root, "shared-skill")

    warnings: list[str] = []
    loader = FilesystemSkillLoader([user_root, project_root])

    discovered = loader.discover(on_warning=warnings.append)
    assert [skill.name for skill in discovered] == ["shared-skill"]
    assert discovered[0].description == "Valid user copy"

    loaded = loader.load("shared-skill", on_warning=warnings.append)
    assert loaded.root_dir == user_root / "shared-skill"
    assert loaded.document.metadata.description == "Valid user copy"
    assert any("#FALLBACK" in message for message in warnings)


def test_load_raises_parse_error_when_only_broken_copies_exist(tmp_path: Path) -> None:
    from abstractskill import SkillParseError

    _write_broken_skill(tmp_path, "broken-skill")
    loader = FilesystemSkillLoader([tmp_path])
    with pytest.raises(SkillParseError):
        loader.load("broken-skill")


def test_load_rejects_traversal_shaped_names(tmp_path: Path) -> None:
    from abstractskill import SkillValidationError

    _write_skill(tmp_path, "good-skill", "Valid")
    loader = FilesystemSkillLoader([tmp_path])
    with pytest.raises(SkillValidationError):
        loader.load("../good-skill")
