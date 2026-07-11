"""Integration tests over the real first-party shelf + trust registries.

These pin the maintainer directive's concrete deliverables: the shelf parses,
its validation records match the vendored bytes (trust binds to bytes), and
the advisory registry is well-formed with all mandated fields.
"""

from __future__ import annotations

from pathlib import Path

from abstractskill import (
    FilesystemSkillLoader,
    TrustLevel,
    TrustRegistry,
    evaluate_trust,
    inspect_skill_dir,
)

REPO = Path(__file__).resolve().parent.parent
SHELF = REPO / "registry" / "skills"
VALIDATIONS = REPO / "registry" / "validations.yaml"
ADVISORIES = REPO / "registry" / "advisories.yaml"
GUIDANCE = REPO / "registry" / "guidance.yaml"

EXPECTED_SHELF = {"adversarial-iteration", "backlog", "coredoc"}
# adversarial-iteration is authored first-party; coredoc/backlog are adopted
# (reviewed, not yet behaviorally audited).
EXPECTED_LEVELS = {
    "adversarial-iteration": TrustLevel.FIRST_PARTY,
    "backlog": TrustLevel.ADOPTED,
    "coredoc": TrustLevel.ADOPTED,
}


def test_shelf_discovers_exactly_the_expected_skills() -> None:
    # Equality, not subset: a rogue vendored skill or a removed one must fail.
    loader = FilesystemSkillLoader([SHELF])
    names = {meta.name for meta in loader.discover()}
    assert names == EXPECTED_SHELF


def test_validations_cover_exactly_the_shelf() -> None:
    # No stale record for removed bytes, no missing record for a present skill.
    registry = TrustRegistry.load(validations_path=VALIDATIONS)
    assert {record.name for record in registry.validations} == EXPECTED_SHELF


def test_shelf_skills_have_no_scripts() -> None:
    # The v1 cut is knowledge/procedure packs only.
    for name in EXPECTED_SHELF:
        assert inspect_skill_dir(SHELF / name).has_scripts is False


def test_validation_records_match_vendored_bytes() -> None:
    # The crux of "trust binds to bytes": each record's tree_hash must equal
    # the hash of the vendored tree, or the record is stale (run refresh_shelf).
    registry = TrustRegistry.load(validations_path=VALIDATIONS)
    by_name = {record.name: record for record in registry.validations}
    assert EXPECTED_SHELF <= set(by_name)
    for name in EXPECTED_SHELF:
        inventory = inspect_skill_dir(SHELF / name)
        assert by_name[name].tree_hash == inventory.tree_hash, (
            f"{name} validation is stale vs vendored bytes; run scripts/refresh_shelf.py"
        )


def test_shelf_skills_evaluate_to_their_levels_and_are_attachable() -> None:
    registry = TrustRegistry.load(
        validations_path=VALIDATIONS, advisories_path=ADVISORIES, guidance_path=GUIDANCE
    )
    loader = FilesystemSkillLoader([SHELF])
    for meta in loader.discover():
        if meta.name not in EXPECTED_SHELF:
            continue
        inventory = inspect_skill_dir(SHELF / meta.name)
        source = "first-party" if meta.name == "adversarial-iteration" else "codex-skills (maintainer)"
        verdict = evaluate_trust(
            registry,
            tree_hash=inventory.tree_hash,
            name=meta.name,
            source=source,
            has_scripts=inventory.has_scripts,
        )
        assert verdict.level is EXPECTED_LEVELS[meta.name]
        assert verdict.blocked is False
        # Shelf skills are script-free and advisory-free → attachable.
        assert verdict.attachable is True


def test_advisory_registry_loads_and_guidance_is_populated() -> None:
    # The advisory registry is intentionally empty at v1 (no self-asserted
    # specific malicious skill); class-level protection lives in guidance.
    registry = TrustRegistry.load(advisories_path=ADVISORIES, guidance_path=GUIDANCE)
    assert len(registry.advisories) == 0
    assert len(registry.guidance) >= 3
    for g in registry.guidance:
        assert g.detail.strip()
        assert g.reference.startswith("http")


def test_activation_description_override_reaches_the_prompt() -> None:
    # F2: the codex skills' descriptions name "Codex"; the catalog must render
    # the host-side override, not the vendored description, while the tree
    # stays byte-verbatim.
    from abstractskill import FilesystemSkillLoader, format_available_skills_xml

    registry = TrustRegistry.load(validations_path=VALIDATIONS)
    overrides = registry.activation_descriptions()
    assert "coredoc" in overrides and "backlog" in overrides
    assert "Codex" not in overrides["coredoc"]

    metas = FilesystemSkillLoader([SHELF]).discover()
    block = format_available_skills_xml(metas, descriptions=overrides)
    assert "Codex" not in block  # overridden away for the two adopted skills
    # adversarial-iteration has no override → its own description renders.
    assert "adversarial-iteration" in block


def test_a_tampered_shelf_skill_loses_trust() -> None:
    registry = TrustRegistry.load(validations_path=VALIDATIONS, advisories_path=ADVISORIES)
    verdict = evaluate_trust(
        registry, tree_hash="0" * 64, name="coredoc", source="codex-skills (maintainer)"
    )
    assert verdict.level is TrustLevel.UNVERIFIED
    assert verdict.validation is None
    assert verdict.requires_review is True
