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
