"""Curated catalog contract — the curated-only install path's validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from abstractskill import CatalogEntry, SkillValidationError, lint_catalog, load_catalog
from abstractskill.catalog import SkillCatalog

REPO = Path(__file__).resolve().parent.parent
SHIPPED_CATALOG = REPO / "registry" / "catalog.yaml"

SHA = "a" * 40
TREE = "b" * 64


def _entry(**overrides) -> CatalogEntry:
    base = dict(
        name="demo-skill",
        source="owner/repo",
        repo="owner/repo",
        upstream_ref=SHA,
        subdir="skills/demo-skill",
        license="MIT",
        archetype="knowledge",
        risk="low",
        improves="testing",
    )
    base.update(overrides)
    return CatalogEntry(**base)


def test_entry_uppercase_name_refused() -> None:
    # The catalog name goes through the spec validator — a case typo dies
    # loudly at load, never lowercased into ambiguity (the shelf dir and the
    # trust key must be the exact spec spelling).
    with pytest.raises(SkillValidationError):
        _entry(name="Demo-Skill")


def test_entry_requires_full_sha() -> None:
    with pytest.raises(SkillValidationError):
        _entry(upstream_ref="main")
    with pytest.raises(SkillValidationError):
        _entry(upstream_ref="abc123")  # short sha: still movable-by-collision, refused


def test_entry_repo_slug_only() -> None:
    # Arbitrary URLs cannot ride the repo field — curated-only is structural.
    with pytest.raises(SkillValidationError):
        _entry(repo="https://evil.example/repo.git")
    with pytest.raises(SkillValidationError):
        _entry(repo="owner/repo/extra")


def test_entry_subdir_traversal_refused() -> None:
    for bad in ("../outside", "skills/../../etc", "/abs/path", "skills\\win"):
        with pytest.raises(SkillValidationError):
            _entry(subdir=bad)


def test_entry_closed_sets_enforced() -> None:
    with pytest.raises(SkillValidationError):
        _entry(archetype="mystery")
    with pytest.raises(SkillValidationError):
        _entry(risk="unknown")


def test_vendored_requires_hash() -> None:
    with pytest.raises(SkillValidationError):
        _entry(vendored=True)  # no expected_tree_hash
    entry = _entry(vendored=True, expected_tree_hash=TREE)
    assert entry.expected_tree_hash == TREE


def test_load_catalog_duplicate_names_refused(tmp_path: Path) -> None:
    doc = f"""
skills:
- {{name: dup, source: o/r, repo: o/r, upstream_ref: {SHA}, subdir: s/dup, license: MIT, archetype: knowledge, risk: low, improves: x}}
- {{name: dup, source: o/r, repo: o/r, upstream_ref: {SHA}, subdir: s/dup2, license: MIT, archetype: knowledge, risk: low, improves: y}}
"""
    path = tmp_path / "catalog.yaml"
    path.write_text(doc, encoding="utf-8")
    with pytest.raises(SkillValidationError):
        load_catalog(path)


def test_redistribution_refusing_license_refused_at_construction() -> None:
    # Vendoring copies bytes: the gate is an ALLOWLIST (a denylist passed
    # every non-permitting license it never heard of — CC-BY-NC, BUSL-1.1,
    # SSPL). Anything off the allowlist refuses by default.
    for bad in (
        "source-available", "Source-Available (view only)", "unknown",
        "proprietary", "CC-BY-NC-4.0", "BUSL-1.1", "SSPL-1.0", "Elastic-2.0",
    ):
        with pytest.raises(SkillValidationError):
            _entry(license=bad)
    # Allowlisted labels pass case-insensitively.
    for good in ("MIT", "Apache-2.0", "bsd-3-clause"):
        _entry(license=good)


def test_flag_shaped_and_traversal_slugs_refused() -> None:
    # Adversary A2: segments must start alphanumeric — argv/URL safety never
    # rests on how a consumer wraps the slug.
    for bad in ("-o/-r", "../..", "owner/..", "owner/-flag", ".x/repo"):
        with pytest.raises(SkillValidationError):
            _entry(repo=bad)


def test_lint_catalog_flags() -> None:
    evidence = ("https://example.org/ref",)
    vendored_missing = _entry(name="ghost", vendored=True, expected_tree_hash=TREE, evidence=evidence)
    unlisted_on_shelf = _entry(name="stray", evidence=evidence)
    risky_no_notes = _entry(name="danger", risk="risky", evidence=evidence)
    no_evidence = _entry(name="bare")
    catalog = SkillCatalog(entries=(vendored_missing, unlisted_on_shelf, risky_no_notes, no_evidence))
    warnings = lint_catalog(catalog, shelf_names=["stray"])
    text = "\n".join(warnings)
    assert "ghost" in text and "absent from the shelf" in text
    assert "stray" in text and "not vendored" in text
    assert "danger" in text and "risky" in text
    assert "bare" in text and "no evidence" in text


def test_shipped_catalog_loads_and_lints_clean() -> None:
    # The shipped curated catalog must always validate; lint against the real
    # shelf must be quiet (a warning is registry rot or a curation mistake —
    # either needs a human, so the test forces one).
    catalog = load_catalog(SHIPPED_CATALOG)
    assert len(catalog.entries) >= 8
    shelf = REPO / "registry" / "skills"
    shelf_names = [p.name for p in shelf.iterdir() if p.is_dir()]
    assert lint_catalog(catalog, shelf_names) == ()


def test_vendored_catalog_pins_match_shelf_bytes() -> None:
    # Adversary C finding 11: a corrupted catalog pin must go red in CI, not
    # surface at the next re-vendor with an error blaming upstream.
    from abstractskill import inspect_skill_dir

    catalog = load_catalog(SHIPPED_CATALOG)
    shelf = REPO / "registry" / "skills"
    for entry in catalog.entries:
        if not entry.vendored:
            continue
        assert entry.expected_tree_hash == inspect_skill_dir(shelf / entry.name).tree_hash, entry.name


def test_shipped_catalog_pins_are_immutable_shapes() -> None:
    catalog = load_catalog(SHIPPED_CATALOG)
    for entry in catalog.entries:
        assert len(entry.upstream_ref) == 40  # never a branch or tag
        assert entry.license.lower() not in {"unknown", ""}
        assert entry.improves  # curation rationale is mandatory in practice
