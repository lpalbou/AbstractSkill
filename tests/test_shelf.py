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

EXPECTED_SHELF = {
    "abstractframework-gateway",
    "adversarial-iteration",
    "adr",
    "architect",
    "backlog",
    "cicd",
    "coredoc",
    "entity-self-knowledge",
    "review",
    "uxreview",
    "verification-before-completion",
}
# adversarial-iteration is authored first-party; the codex-skills entries are
# adopted (maintainer-authored, first-party reviewed — architect/adr/cicd/
# review/uxreview added on the 2026-07-11 operator directive, architect with
# two upstream improvements folded first); verification-before-completion is
# the first catalog-curated third-party skill (obra/superpowers,
# manual-review → adopted, pinned in registry/catalog.yaml).
EXPECTED_LEVELS = {
    "abstractframework-gateway": TrustLevel.FIRST_PARTY,
    "adversarial-iteration": TrustLevel.FIRST_PARTY,
    "adr": TrustLevel.ADOPTED,
    "architect": TrustLevel.ADOPTED,
    "backlog": TrustLevel.ADOPTED,
    "cicd": TrustLevel.ADOPTED,
    "coredoc": TrustLevel.ADOPTED,
    "entity-self-knowledge": TrustLevel.FIRST_PARTY,
    "review": TrustLevel.ADOPTED,
    "uxreview": TrustLevel.ADOPTED,
    "verification-before-completion": TrustLevel.ADOPTED,
}
EXPECTED_SOURCES = {
    "abstractframework-gateway": "first-party",
    "adversarial-iteration": "first-party",
    "adr": "codex-skills (maintainer)",
    "architect": "codex-skills (maintainer)",
    "backlog": "codex-skills (maintainer)",
    "cicd": "codex-skills (maintainer)",
    "coredoc": "codex-skills (maintainer)",
    "entity-self-knowledge": "first-party",
    "review": "codex-skills (maintainer)",
    "uxreview": "codex-skills (maintainer)",
    "verification-before-completion": "obra/superpowers",
}
# Skills allowed to carry scripts/ (requires_review at the gate until the
# operator enables them). Vendoring a scripts-bearing catalog entry adds its
# name HERE — the admission review's explicit signature, never a silent pass.
EXPECTED_SCRIPTS_BEARING: set[str] = set()


def test_shelf_discovers_exactly_the_expected_skills() -> None:
    # Equality, not subset: a rogue vendored skill or a removed one must fail.
    loader = FilesystemSkillLoader([SHELF])
    names = {meta.name for meta in loader.discover()}
    assert names == EXPECTED_SHELF


def test_validations_cover_exactly_the_shelf() -> None:
    # No stale record for removed bytes, no missing record for a present skill.
    registry = TrustRegistry.load(validations_path=VALIDATIONS)
    assert {record.name for record in registry.validations} == EXPECTED_SHELF


def test_shelf_scripts_presence_matches_expectations() -> None:
    # Per-skill expectation, not a blanket ban: a scripts-bearing catalog
    # entry may be vendored (it stays requires_review at the gate), but its
    # name must be added to EXPECTED_SCRIPTS_BEARING deliberately.
    for name in EXPECTED_SHELF:
        expected = name in EXPECTED_SCRIPTS_BEARING
        assert inspect_skill_dir(SHELF / name).has_scripts is expected, name


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
        # The REAL per-skill source (adversary C finding 10: a hardcoded wrong
        # source here would keep passing while a name-anchored advisory blocks
        # the skill in the live pipeline).
        source = EXPECTED_SOURCES[meta.name]
        verdict = evaluate_trust(
            registry,
            tree_hash=inventory.tree_hash,
            name=meta.name,
            source=source,
            has_scripts=inventory.has_scripts,
        )
        assert verdict.level is EXPECTED_LEVELS[meta.name]
        assert verdict.blocked is False
        if meta.name in EXPECTED_SCRIPTS_BEARING:
            # Scripts force review regardless of validation level.
            assert verdict.requires_review is True
        else:
            # Script-free and advisory-free → attachable.
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
    # 2026-07-12 adversary F1: the rendered activation surface must never
    # advertise a faculty the body deliberately un-teaches (probe is
    # engine-only today; the co-signed correction pulled it from the body).
    assert "probe" not in block.lower()


def test_first_party_shelf_entries_carry_no_activation_override() -> None:
    # 2026-07-12 adversary F3: an override lives OUTSIDE the byte pin, so its
    # drift is invisible to hash checks — and it drifted within one authoring
    # wave (the probe P0). First-party skills own their frontmatter, so the
    # frontmatter IS the activation text; overrides are for vendored trees
    # we cannot edit. Structural gate, not convention.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "refresh_shelf_policy_check", REPO / "scripts" / "refresh_shelf.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name, policy in mod.SHELF_POLICY.items():
        if policy["method"] == "first-party":
            assert policy["activation_description"] is None, (
                f"first-party skill {name!r} carries an activation override; "
                "edit its frontmatter instead (re-hash + re-pin is the path)"
            )


def test_a_tampered_shelf_skill_loses_trust() -> None:
    registry = TrustRegistry.load(validations_path=VALIDATIONS, advisories_path=ADVISORIES)
    verdict = evaluate_trust(
        registry, tree_hash="0" * 64, name="coredoc", source="codex-skills (maintainer)"
    )
    assert verdict.level is TrustLevel.UNVERIFIED
    assert verdict.validation is None
    assert verdict.requires_review is True


def test_shipped_registry_lints_clean() -> None:
    # The lint runs on every refresh; the shipped registry must produce zero
    # warnings (a warning here is either real registry rot or lint noise —
    # both need a human decision, so this test forces one).
    from abstractskill import lint_registry

    registry = TrustRegistry.load(
        validations_path=VALIDATIONS,
        advisories_path=ADVISORIES,
        guidance_path=GUIDANCE,
    )
    assert lint_registry(registry) == ()
