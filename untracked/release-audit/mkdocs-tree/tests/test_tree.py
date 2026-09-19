from __future__ import annotations

from pathlib import Path

import pytest

from abstractskill import SkillValidationError
from abstractskill.tree import hash_skill_tree, inspect_skill_dir, read_skill_resource


def _make_skill_tree(root: Path) -> Path:
    skill_dir = root / "demo-skill"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: Demo.\n---\n\nBody.\n",
        encoding="utf-8",
    )
    (skill_dir / "references" / "guide.md").write_text("Reference.\n", encoding="utf-8")
    return skill_dir


def test_hash_skill_tree_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    skill_dir = _make_skill_tree(tmp_path)
    first = hash_skill_tree(skill_dir)
    assert first == hash_skill_tree(skill_dir)

    (skill_dir / "references" / "guide.md").write_text("Changed.\n", encoding="utf-8")
    assert hash_skill_tree(skill_dir) != first


def test_hash_skill_tree_ignores_os_junk(tmp_path: Path) -> None:
    skill_dir = _make_skill_tree(tmp_path)
    before = hash_skill_tree(skill_dir)
    (skill_dir / ".DS_Store").write_bytes(b"junk")
    assert hash_skill_tree(skill_dir) == before


def test_hash_skill_tree_is_injective_against_delimiter_forgery(tmp_path: Path) -> None:
    # POSIX permits \n in filenames; a text-delimited manifest would let a
    # crafted single file collide with a two-file tree. The length-prefixed
    # manifest must keep these trees distinct.
    import hashlib

    tree_a = tmp_path / "a"
    tree_a.mkdir()
    (tree_a / "x").write_bytes(b"payload-x")
    (tree_a / "y").write_bytes(b"payload-y")

    digest_x = hashlib.sha256(b"payload-x").hexdigest()
    tree_b = tmp_path / "b"
    tree_b.mkdir()
    forged_name = f"x\n{digest_x}\ny"
    (tree_b / forged_name).write_bytes(b"payload-y")

    assert hash_skill_tree(tree_a) != hash_skill_tree(tree_b)


def test_hash_skill_tree_refuses_symlinks(tmp_path: Path) -> None:
    skill_dir = _make_skill_tree(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (skill_dir / "link.txt").symlink_to(outside)
    with pytest.raises(SkillValidationError):
        hash_skill_tree(skill_dir)


def test_inspect_skill_dir_reports_scripts_structurally(tmp_path: Path) -> None:
    skill_dir = _make_skill_tree(tmp_path)
    inventory = inspect_skill_dir(skill_dir)
    assert inventory.has_scripts is False
    assert [item.rel_path for item in inventory.files] == [
        "SKILL.md",
        "references/guide.md",
    ]

    scripts = skill_dir / "scripts"
    scripts.mkdir()
    (scripts / "run.py").write_text("print('hi')\n", encoding="utf-8")
    inventory = inspect_skill_dir(skill_dir)
    assert inventory.has_scripts is True
    assert [item.rel_path for item in inventory.script_files] == ["scripts/run.py"]
    assert inventory.tree_hash == hash_skill_tree(skill_dir)


def test_code_outside_scripts_dir_still_flags_has_scripts(tmp_path: Path) -> None:
    # Adversary-found: keying has_scripts on the scripts/ dir alone lets a
    # skill ship executable code under bin/ or references/ and evade the
    # requires_review gate. Code EXTENSIONS anywhere in the tree flag it.
    skill_dir = _make_skill_tree(tmp_path)
    hooks = skill_dir / "references"
    (hooks / "helper.py").write_text("print('evade')\n", encoding="utf-8")
    inventory = inspect_skill_dir(skill_dir)
    assert inventory.has_scripts is True
    # Passive resources alone never flag.
    (hooks / "helper.py").unlink()
    assert inspect_skill_dir(skill_dir).has_scripts is False


def test_read_skill_resource_enforces_bounds(tmp_path: Path) -> None:
    skill_dir = _make_skill_tree(tmp_path)

    data = read_skill_resource(skill_dir, "references/guide.md", max_bytes=1024)
    assert data == b"Reference.\n"

    with pytest.raises(SkillValidationError):
        read_skill_resource(skill_dir, "references/guide.md", max_bytes=4)

    with pytest.raises(SkillValidationError):
        read_skill_resource(skill_dir, "../outside.txt", max_bytes=1024)

    outside = tmp_path / "secret.txt"
    outside.write_text("secret", encoding="utf-8")
    (skill_dir / "leak.txt").symlink_to(outside)
    with pytest.raises(SkillValidationError):
        read_skill_resource(skill_dir, "leak.txt", max_bytes=1024)
