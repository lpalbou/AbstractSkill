"""Tests for the bundled registry accessors and seed_registry()."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

import abstractskill.bundled as bundled
from abstractskill import (
    SeedReport,
    TrustLevel,
    TrustRegistry,
    bundled_registry_dir,
    bundled_registry_version,
    evaluate_trust,
    hash_skill_tree,
    inspect_skill_dir,
    seed_registry,
)

REPO = Path(__file__).resolve().parent.parent
TRUST_FILES = ("advisories.yaml", "catalog.yaml", "guidance.yaml", "validations.yaml")
LICENSES = (
    "licenses/meshvault-live-editing.LICENSE",
    "licenses/verification-before-completion.LICENSE",
)

# The bundle version must move whenever the bundled content moves. When this
# test fails: bump `version:` in src/abstractskill/registry/catalog.yaml, then
# update BOTH values below (the digest printed in the failure message).
PINNED_VERSION = "2026.09.25"
PINNED_DIGEST = "61d8b95ae2c07c247b516d4a76963b49019860b292a0d68117e20122fa6f16fa"


def _bundle_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for key, path in bundled._bundled_items(root):
        digest.update(key.encode("utf-8") + b"\0")
        digest.update(bundled._hash_item(path, path.is_dir()).encode("ascii") + b"\n")
    return digest.hexdigest()


@pytest.fixture
def fake_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A writable copy of the real bundle, served in place of the package data."""
    copy = tmp_path / "bundle"
    shutil.copytree(bundled_registry_dir(), copy)
    monkeypatch.setattr(bundled, "bundled_registry_dir", lambda: copy)
    return copy


def _all_items() -> set[str]:
    skills = {f"skills/{p.name}" for p in (bundled_registry_dir() / "skills").iterdir() if p.is_dir()}
    return skills | set(TRUST_FILES) | set(LICENSES)


def test_bundled_dir_is_the_package_registry_with_14_skills() -> None:
    root = bundled_registry_dir()
    assert root == REPO / "src" / "abstractskill" / "registry"
    skills = sorted(p.name for p in (root / "skills").iterdir() if p.is_dir())
    assert len(skills) == 14
    assert all((root / "skills" / name / "SKILL.md").is_file() for name in skills)
    for name in TRUST_FILES:
        assert (root / name).is_file()


def test_bundle_version_is_pinned_to_content() -> None:
    version = bundled_registry_version()
    digest = _bundle_digest(bundled_registry_dir())
    assert (version, digest) == (PINNED_VERSION, PINNED_DIGEST), (
        "bundled registry content or version changed: bump `version:` in "
        "src/abstractskill/registry/catalog.yaml and pin "
        f"PINNED_VERSION={version!r}, PINNED_DIGEST={digest!r}"
    )


def test_first_seed_adds_everything(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    report = seed_registry(dest)
    assert isinstance(report, SeedReport)
    assert report.dest == dest
    assert set(report.added) == _all_items()
    assert report.updated == report.kept_user_modified == report.unchanged == ()
    assert report.bundled_version == bundled_registry_version()
    assert report.previous_version is None
    assert report.changed
    for name in (bundled_registry_dir() / "skills").iterdir():
        assert hash_skill_tree(dest / "skills" / name.name) == hash_skill_tree(name)
    manifest = json.loads((dest / ".seeded.json").read_text(encoding="utf-8"))
    assert manifest["bundled_version"] == report.bundled_version
    assert set(manifest["items"]) == _all_items()


def test_second_seed_changes_nothing(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    before = {p: p.stat().st_mtime_ns for p in dest.rglob("*")}
    report = seed_registry(dest)
    assert set(report.unchanged) == _all_items()
    assert report.added == report.updated == report.kept_user_modified == ()
    assert not report.changed
    assert report.previous_version == report.bundled_version
    assert {p: p.stat().st_mtime_ns for p in dest.rglob("*")} == before


def test_operator_edit_is_kept(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    skill_md = dest / "skills" / "backlog" / "SKILL.md"
    edited = skill_md.read_bytes() + b"\nOperator note.\n"
    skill_md.write_bytes(edited)
    validations = dest / "validations.yaml"
    validations.write_bytes(validations.read_bytes() + b"\n# local\n")

    report = seed_registry(dest)
    assert set(report.kept_user_modified) == {"skills/backlog", "validations.yaml"}
    assert skill_md.read_bytes() == edited
    assert validations.read_bytes().endswith(b"# local\n")


def test_foreign_item_is_never_claimed(tmp_path: Path) -> None:
    """A same-named skill the seed never wrote is operator content."""
    dest = tmp_path / "shelf"
    (dest / "skills" / "coredoc").mkdir(parents=True)
    (dest / "skills" / "coredoc" / "SKILL.md").write_text("mine\n", encoding="utf-8")
    report = seed_registry(dest)
    assert "skills/coredoc" in report.kept_user_modified
    assert (dest / "skills" / "coredoc" / "SKILL.md").read_text(encoding="utf-8") == "mine\n"
    assert (dest / "skills" / "backlog" / "SKILL.md").is_file()


def test_bundle_update_refreshes_untouched_items_only(tmp_path: Path, fake_bundle: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    operator_md = dest / "skills" / "review" / "SKILL.md"
    operator_md.write_bytes(operator_md.read_bytes() + b"\nlocal\n")

    # A newer bundle changes two skills and the validations file.
    for name in ("adr", "review"):
        path = fake_bundle / "skills" / name / "SKILL.md"
        path.write_bytes(path.read_bytes() + b"\nupstream change\n")
    (fake_bundle / "validations.yaml").write_bytes(
        (fake_bundle / "validations.yaml").read_bytes() + b"\n# v2\n"
    )
    catalog = fake_bundle / "catalog.yaml"
    catalog.write_text(
        catalog.read_text(encoding="utf-8").replace(
            f'version: "{PINNED_VERSION}"', 'version: "2099.01.01"'
        ),
        encoding="utf-8",
    )

    report = seed_registry(dest)
    assert set(report.updated) == {"skills/adr", "validations.yaml", "catalog.yaml"}
    assert report.kept_user_modified == ("skills/review",)
    assert report.bundled_version == "2099.01.01"
    assert report.previous_version == PINNED_VERSION
    assert hash_skill_tree(dest / "skills" / "adr") == hash_skill_tree(fake_bundle / "skills" / "adr")
    assert operator_md.read_bytes().endswith(b"\nlocal\n")
    assert not (dest / ".seed-staging").exists()

    # The refreshed shelf is stable: another seed writes nothing.
    assert seed_registry(dest).updated == ()


def test_new_bundled_skill_is_added(tmp_path: Path, fake_bundle: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    extra = fake_bundle / "skills" / "zz-new"
    extra.mkdir()
    (extra / "SKILL.md").write_text("---\nname: zz-new\ndescription: x\n---\n", encoding="utf-8")
    report = seed_registry(dest)
    assert report.added == ("skills/zz-new",)


def test_seeded_shelf_verifies_against_seeded_validations(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    registry = TrustRegistry.load(
        validations_path=dest / "validations.yaml",
        advisories_path=dest / "advisories.yaml",
        guidance_path=dest / "guidance.yaml",
    )
    for skill_dir in sorted((dest / "skills").iterdir()):
        inv = inspect_skill_dir(skill_dir)
        verdict = evaluate_trust(
            registry, tree_hash=inv.tree_hash, name=skill_dir.name, has_scripts=inv.has_scripts
        )
        assert verdict.level in (TrustLevel.FIRST_PARTY, TrustLevel.ADOPTED), skill_dir.name


def test_unreadable_manifest_fails_loudly(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    dest.mkdir()
    (dest / ".seeded.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(Exception, match="seed manifest"):
        seed_registry(dest)
