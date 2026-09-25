"""Tests for the bundled registry accessors and seed_registry()."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import re
import time
from pathlib import Path

import pytest

import abstractskill.bundled as bundled
from abstractskill import (
    SeedReport,
    SkillError,
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


def _set_bundle_version(bundle: Path, version: str) -> None:
    catalog = bundle / "catalog.yaml"
    text = catalog.read_text(encoding="utf-8")
    catalog.write_text(re.sub(r'(?m)^version: ".*"$', f'version: "{version}"', text), encoding="utf-8")


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


def test_existing_item_without_manifest_is_never_claimed(tmp_path: Path) -> None:
    """A same-named skill at a never-seeded dest is kept; identical items are adopted."""
    dest = tmp_path / "shelf"
    (dest / "skills" / "coredoc").mkdir(parents=True)
    (dest / "skills" / "coredoc" / "SKILL.md").write_text("mine\n", encoding="utf-8")
    shutil.copytree(bundled_registry_dir() / "skills" / "adr", dest / "skills" / "adr")
    report = seed_registry(dest)
    assert report.kept_unknown_provenance == ("skills/coredoc",)
    assert report.kept == {"skills/coredoc": "kept_unknown_provenance"}
    assert report.unchanged == ("skills/adr",)
    assert (dest / "skills" / "coredoc" / "SKILL.md").read_text(encoding="utf-8") == "mine\n"
    assert (dest / "skills" / "backlog" / "SKILL.md").is_file()
    manifest = json.loads((dest / ".seeded.json").read_text(encoding="utf-8"))
    assert "skills/adr" in manifest["items"] and "skills/coredoc" not in manifest["items"]


def test_lost_manifest_adopts_identical_items_and_keeps_the_rest(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    (dest / ".seeded.json").unlink()
    skill_md = dest / "skills" / "backlog" / "SKILL.md"
    skill_md.write_bytes(skill_md.read_bytes() + b"\nedit\n")
    report = seed_registry(dest)
    assert report.previous_version is None
    assert report.kept_unknown_provenance == ("skills/backlog",)
    assert set(report.unchanged) == _all_items() - {"skills/backlog"}
    manifest = json.loads((dest / ".seeded.json").read_text(encoding="utf-8"))
    assert set(manifest["items"]) == _all_items() - {"skills/backlog"}


def test_foreign_item_with_manifest_is_kept_foreign(tmp_path: Path, fake_bundle: Path) -> None:
    """The bundle gains a skill the operator already created: never claimed."""
    dest = tmp_path / "shelf"
    seed_registry(dest)
    (dest / "skills" / "zz-new").mkdir()
    (dest / "skills" / "zz-new" / "SKILL.md").write_text("operator\n", encoding="utf-8")
    (fake_bundle / "skills" / "zz-new").mkdir()
    (fake_bundle / "skills" / "zz-new" / "SKILL.md").write_text(
        "---\nname: zz-new\ndescription: x\n---\n", encoding="utf-8"
    )
    report = seed_registry(dest)
    assert report.kept_foreign == ("skills/zz-new",)
    assert (dest / "skills" / "zz-new" / "SKILL.md").read_text(encoding="utf-8") == "operator\n"


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
    _set_bundle_version(fake_bundle, "2099.01.01")

    report = seed_registry(dest)
    assert set(report.updated) == {"skills/adr", "validations.yaml", "catalog.yaml"}
    assert report.kept_user_modified == ("skills/review",)
    assert report.bundled_version == "2099.01.01"
    assert report.previous_version == PINNED_VERSION
    assert hash_skill_tree(dest / "skills" / "adr") == hash_skill_tree(fake_bundle / "skills" / "adr")
    assert operator_md.read_bytes().endswith(b"\nlocal\n")
    assert not list(dest.glob(".seed-staging*"))

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
    with pytest.raises(SkillError, match="seed manifest") as excinfo:
        seed_registry(dest)
    assert "delete" not in str(excinfo.value).lower()


def test_unknown_manifest_schema_fails_loudly(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    manifest_path = dest / ".seeded.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema"] = 99
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SkillError, match="schema 99"):
        seed_registry(dest)


def test_older_bundle_never_replaces_newer_seed(tmp_path: Path, fake_bundle: Path) -> None:
    dest = tmp_path / "shelf"
    newer = fake_bundle / "skills" / "adr" / "SKILL.md"
    older_bytes = newer.read_bytes()
    newer.write_bytes(older_bytes + b"\nnewer\n")
    _set_bundle_version(fake_bundle, "2099.01.01")
    seed_registry(dest)

    newer.write_bytes(older_bytes)
    _set_bundle_version(fake_bundle, PINNED_VERSION)
    report = seed_registry(dest)
    assert report.previous_version == "2099.01.01"
    assert set(report.kept_newer) == {"skills/adr", "catalog.yaml"}
    assert report.updated == ()
    assert (dest / "skills" / "adr" / "SKILL.md").read_bytes().endswith(b"\nnewer\n")
    manifest = json.loads((dest / ".seeded.json").read_text(encoding="utf-8"))
    assert manifest["bundled_version"] == "2099.01.01"


def test_skill_dropped_from_bundle_is_reported_not_deleted(
    tmp_path: Path, fake_bundle: Path
) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    shutil.rmtree(fake_bundle / "skills" / "uxreview")
    report = seed_registry(dest)
    assert report.not_in_bundle == ("skills/uxreview",)
    assert (dest / "skills" / "uxreview" / "SKILL.md").is_file()
    # Once the host removes it, it leaves the report and the manifest.
    shutil.rmtree(dest / "skills" / "uxreview")
    assert seed_registry(dest).not_in_bundle == ()
    manifest = json.loads((dest / ".seeded.json").read_text(encoding="utf-8"))
    assert "skills/uxreview" not in manifest["items"]


def test_symlinked_and_unreadable_items_are_kept_with_reasons(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    elsewhere = tmp_path / "elsewhere"
    shutil.copytree(dest / "skills" / "adr", elsewhere)
    shutil.rmtree(dest / "skills" / "adr")
    (dest / "skills" / "adr").symlink_to(elsewhere, target_is_directory=True)
    (dest / "skills" / "cicd" / "linked.md").symlink_to(tmp_path / "outside.md")
    report = seed_registry(dest)
    assert report.kept_symlink == ("skills/adr",)
    assert report.kept_unreadable == ("skills/cicd",)
    assert report.kept == {"skills/adr": "kept_symlink", "skills/cicd": "kept_unreadable"}
    assert (dest / "skills" / "adr").is_symlink()


def test_symlinked_staging_is_refused(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    dest.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    (dest / ".seed-staging").symlink_to(target, target_is_directory=True)
    with pytest.raises(SkillError, match="symlink"):
        seed_registry(dest)
    assert target.is_dir()


def test_refuses_to_seed_into_the_bundle() -> None:
    with pytest.raises(SkillError, match="bundled registry itself"):
        seed_registry(bundled_registry_dir() / "sub")


def test_failed_folder_swap_restores_the_old_skill(
    tmp_path: Path, fake_bundle: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "shelf"
    seed_registry(dest)
    target = dest / "skills" / "adr"
    seeded_hash = hash_skill_tree(target)
    md = fake_bundle / "skills" / "adr" / "SKILL.md"
    md.write_bytes(md.read_bytes() + b"\nupstream change\n")

    real_replace = os.replace

    def failing_replace(src, dst):  # the "new copy in" rename fails
        if Path(dst) == target and Path(src).name == "adr":
            raise OSError("injected rename failure")
        return real_replace(src, dst)

    monkeypatch.setattr(bundled.os, "replace", failing_replace)
    with pytest.raises(OSError, match="injected"):
        seed_registry(dest)
    assert hash_skill_tree(target) == seeded_hash
    assert not list(dest.glob(".seed-staging*"))

    monkeypatch.setattr(bundled.os, "replace", real_replace)
    assert seed_registry(dest).updated == ("skills/adr",)


_WORKER = """
import json, sys, time
from pathlib import Path
from abstractskill import TrustRegistry, evaluate_trust, inspect_skill_dir, seed_registry

dest, go = Path(sys.argv[1]), Path(sys.argv[2])
deadline = time.monotonic() + 30
while not go.exists() and time.monotonic() < deadline:
    time.sleep(0.001)
report = seed_registry(dest)
registry = TrustRegistry.load(
    validations_path=dest / "validations.yaml", advisories_path=dest / "advisories.yaml"
)
levels = {
    p.name: evaluate_trust(
        registry, tree_hash=inspect_skill_dir(p).tree_hash, name=p.name
    ).level.value
    for p in sorted((dest / "skills").iterdir())
}
print(json.dumps({"added": list(report.added), "unchanged": list(report.unchanged),
                  "kept": report.kept, "levels": levels}))
"""


def test_concurrent_seeds_from_four_processes(tmp_path: Path) -> None:
    dest = tmp_path / "shelf"
    go = tmp_path / "go"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(bundled.__file__).resolve().parent.parent)
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", _WORKER, str(dest), str(go)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env,
        )
        for _ in range(4)
    ]
    time.sleep(0.5)  # let every interpreter reach the start line
    go.touch()
    results = []
    for proc in procs:
        out, err = proc.communicate(timeout=120)
        assert proc.returncode == 0, err
        results.append(json.loads(out))

    expected = _all_items()
    skill_names = {k.split("/", 1)[1] for k in expected if k.startswith("skills/")}
    for result in results:
        assert result["kept"] == {}
        assert set(result["added"]) | set(result["unchanged"]) == expected
        assert set(result["levels"]) == skill_names
        assert set(result["levels"].values()) <= {"first_party", "adopted"}
    assert sorted(len(r["added"]) for r in results) == [0, 0, 0, len(expected)]

    manifest = json.loads((dest / ".seeded.json").read_text(encoding="utf-8"))
    assert set(manifest["items"]) == expected
    follow_up = seed_registry(dest)
    assert (len(follow_up.added), len(follow_up.unchanged), follow_up.kept) == (0, len(expected), {})
    assert not list(dest.glob(".seed-staging*")) and not list(dest.glob(".seeded.json.*"))
