"""Offline tests for scripts/vendor_skill.py — the network/write path.

No network: `_fetch_pinned` is monkeypatched to a local fixture tree. These
pin the fail-closed behaviors the mechanism adversary demanded (symlink
refusal, hash-mismatch refusal, overwrite refusal, byte-sensitive identity,
VCS/junk exclusion, root-subdir refusal).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location(
    "vendor_skill", REPO / "scripts" / "vendor_skill.py"
)
vendor_skill = importlib.util.module_from_spec(_spec)
sys.modules["vendor_skill"] = vendor_skill
_spec.loader.exec_module(vendor_skill)

from abstractskill import CatalogEntry, hash_skill_tree  # noqa: E402

SHA = "c" * 40


def _entry(name: str = "demo-skill", **overrides) -> CatalogEntry:
    base = dict(
        name=name,
        source="owner/repo",
        repo="owner/repo",
        upstream_ref=SHA,
        subdir=f"skills/{name}",
        license="MIT",
        archetype="knowledge",
        risk="low",
        improves="testing",
    )
    base.update(overrides)
    return CatalogEntry(**base)


def _make_upstream(root: Path, name: str = "demo-skill", body: str = "Body.\n") -> Path:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: A demo skill for vendor tests.\n---\n\n{body}",
        encoding="utf-8",
    )
    return skill


@pytest.fixture()
def sandbox(tmp_path: Path, monkeypatch):
    """Fake upstream repo + isolated shelf; no network, no real git."""
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _make_upstream(upstream)

    shelf = tmp_path / "shelf"
    shelf.mkdir()
    monkeypatch.setattr(vendor_skill, "SHELF", shelf)
    monkeypatch.setattr(vendor_skill, "REPO", tmp_path)
    monkeypatch.setattr(vendor_skill, "_fetch_pinned", lambda entry, workdir: upstream)
    return upstream, shelf


def test_vendor_happy_path(sandbox) -> None:
    upstream, shelf = sandbox
    assert vendor_skill.vendor(_entry()) == 0
    dest = shelf / "demo-skill"
    assert (dest / "SKILL.md").is_file()


def test_symlink_in_upstream_refused(sandbox, tmp_path: Path) -> None:
    upstream, shelf = sandbox
    (upstream / "skills" / "demo-skill" / "link").symlink_to(tmp_path)
    with pytest.raises(SystemExit, match="symlink"):
        vendor_skill.vendor(_entry())
    assert not (shelf / "demo-skill").exists()


def test_expected_hash_mismatch_refused(sandbox) -> None:
    upstream, shelf = sandbox
    entry = _entry(expected_tree_hash="0" * 64)
    with pytest.raises(SystemExit, match="TREE HASH MISMATCH"):
        vendor_skill.vendor(entry)
    assert not (shelf / "demo-skill").exists()


def test_expected_hash_match_vendors(sandbox) -> None:
    upstream, shelf = sandbox
    pinned = hash_skill_tree(upstream / "skills" / "demo-skill")
    assert vendor_skill.vendor(_entry(expected_tree_hash=pinned)) == 0
    assert hash_skill_tree(shelf / "demo-skill") == pinned


def test_differing_shelf_bytes_refused_without_force(sandbox) -> None:
    upstream, shelf = sandbox
    dest = shelf / "demo-skill"
    dest.mkdir()
    # Same file name, same LENGTH, different bytes; mtime equalized — the
    # stat-shallow-compare hole the adversary found must never pass this.
    staged_src = upstream / "skills" / "demo-skill" / "SKILL.md"
    tampered = staged_src.read_text(encoding="utf-8").replace("Body.", "Evil.")
    (dest / "SKILL.md").write_text(tampered, encoding="utf-8")
    st = staged_src.stat()
    os.utime(dest / "SKILL.md", (st.st_atime, st.st_mtime))
    with pytest.raises(SystemExit, match="DIFFERENT bytes"):
        vendor_skill.vendor(_entry())
    # --force replaces after review
    assert vendor_skill.vendor(_entry(), force=True) == 0
    assert "Evil." not in (dest / "SKILL.md").read_text(encoding="utf-8")


def test_identical_shelf_is_noop(sandbox) -> None:
    upstream, shelf = sandbox
    assert vendor_skill.vendor(_entry()) == 0
    assert vendor_skill.vendor(_entry()) == 0  # idempotent, no --force needed


def test_frontmatter_name_mismatch_refused(sandbox) -> None:
    upstream, shelf = sandbox
    entry = _entry(name="other-name", subdir="skills/demo-skill")
    with pytest.raises(SystemExit, match="frontmatter name"):
        vendor_skill.vendor(entry)


def test_vcs_and_junk_never_reach_the_shelf(sandbox) -> None:
    upstream, shelf = sandbox
    skill = upstream / "skills" / "demo-skill"
    (skill / ".git").mkdir()
    (skill / ".git" / "config").write_text("x", encoding="utf-8")
    (skill / ".DS_Store").write_bytes(b"junk")
    assert vendor_skill.vendor(_entry()) == 0
    dest = shelf / "demo-skill"
    assert not (dest / ".git").exists()
    assert not (dest / ".DS_Store").exists()


def test_root_subdir_refused(sandbox) -> None:
    upstream, shelf = sandbox
    # The catalog contract refuses traversal spellings at construction; this
    # bypasses the contract deliberately to pin the SCRIPT's own containment
    # (defense in depth — the check must hold even if the contract regressed).
    entry = _entry()
    object.__setattr__(entry, "subdir", "skills/..")
    with pytest.raises(SystemExit, match="repo root"):
        vendor_skill.vendor(entry)
