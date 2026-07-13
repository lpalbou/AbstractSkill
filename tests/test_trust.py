from __future__ import annotations

from pathlib import Path

import pytest

from abstractskill import (
    AdvisoryEntry,
    GuidanceEntry,
    Severity,
    SkillValidationError,
    TrustLevel,
    TrustRegistry,
    ValidationRecord,
    evaluate_trust,
)

HASH_A = "a" * 64
HASH_B = "b" * 64


def _validation(
    tree_hash: str = HASH_A,
    level: TrustLevel = TrustLevel.FIRST_PARTY,
    method: str = "first-party",
) -> ValidationRecord:
    return ValidationRecord(
        name="demo-skill",
        source="first-party",
        tree_hash=tree_hash,
        level=level,
        method=method,
        validated_by="skill",
        validated_at="2026-07-11",
    )


def _advisory(tree_hash: str | None = None, severity: Severity = Severity.CRITICAL, **kw: object) -> AdvisoryEntry:
    base = dict(
        name="evil-skill",
        source="marketplace",
        official_intent="Formats PDF files.",
        hidden_issue="Exfiltrates the conversation to an attacker endpoint.",
        severity=severity,
        reference="https://example.org/advisory/evil-skill",
        tree_hash=tree_hash,
    )
    base.update(kw)
    return AdvisoryEntry(**base)  # type: ignore[arg-type]


# --- ValidationRecord ---

def test_validation_record_rejects_ungrantable_level() -> None:
    with pytest.raises(SkillValidationError):
        ValidationRecord(
            name="x", source="s", tree_hash=HASH_A, level=TrustLevel.UNVERIFIED,
            method="first-party", validated_by="skill", validated_at="2026-07-11",
        )


def test_validation_record_rejects_unknown_method() -> None:
    with pytest.raises(SkillValidationError):
        ValidationRecord(
            name="x", source="s", tree_hash=HASH_A, level=TrustLevel.AUDITED,
            method="vibes", validated_by="skill", validated_at="2026-07-11",
        )


def test_adoption_method_cannot_grant_first_party() -> None:
    # "reviewed, not audited" must not claim the top band.
    with pytest.raises(SkillValidationError):
        _validation(level=TrustLevel.FIRST_PARTY, method="first-party-adoption")
    ok = _validation(level=TrustLevel.ADOPTED, method="first-party-adoption")
    assert ok.level is TrustLevel.ADOPTED


def test_simulated_execution_requires_real_epoch_evidence() -> None:
    with pytest.raises(SkillValidationError):
        _validation(level=TrustLevel.AUDITED, method="simulated-execution")  # no evidence
    with pytest.raises(SkillValidationError):
        ValidationRecord(
            name="x", source="s", tree_hash=HASH_A, level=TrustLevel.AUDITED,
            method="simulated-execution", validated_by="skill", validated_at="2026-07-11",
            evidence={"epochs": 0, "models": []},  # zero epochs / no models = not an audit
        )
    ok = ValidationRecord(
        name="x", source="s", tree_hash=HASH_A, level=TrustLevel.AUDITED,
        method="simulated-execution", validated_by="skill", validated_at="2026-07-11",
        evidence={"epochs": 100, "models": ["gpt-oss-120b", "qwen3.6-35b"]},
    )
    assert ok.evidence["epochs"] == 100


def test_validation_rejects_malformed_hash() -> None:
    with pytest.raises(SkillValidationError):
        _validation(tree_hash="DEADBEEF")


def test_validation_rejects_empty_provenance() -> None:
    with pytest.raises(SkillValidationError):
        ValidationRecord(
            name="x", source="s", tree_hash=HASH_A, level=TrustLevel.AUDITED,
            method="manual-review", validated_by="  ", validated_at="2026-07-11",
        )


# --- AdvisoryEntry ---

def test_advisory_requires_all_four_mandated_fields() -> None:
    for missing in ("official_intent", "hidden_issue", "reference"):
        with pytest.raises(SkillValidationError):
            _advisory(**{missing: "  "})


def test_advisory_severity_is_closed_set() -> None:
    with pytest.raises(SkillValidationError):
        AdvisoryEntry.from_dict(
            {
                "name": "x", "source": "s", "official_intent": "i",
                "hidden_issue": "h", "severity": "apocalyptic", "reference": "http://x",
            }
        )


def test_withdrawn_advisory_requires_reason() -> None:
    with pytest.raises(SkillValidationError):
        _advisory(status="withdrawn")
    ok = _advisory(status="withdrawn", withdrawn_reason="false positive", withdrawn_at="2026-07-12")
    assert ok.is_active is False


# --- evaluate_trust: precedence, severity grading, fail-closed ---

def test_blocking_advisory_beats_validation() -> None:
    registry = TrustRegistry(
        validations=[_validation(HASH_A, TrustLevel.FIRST_PARTY)],
        advisories=[_advisory(tree_hash=HASH_A, severity=Severity.CRITICAL)],
    )
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="demo-skill", source="first-party")
    assert verdict.blocked is True
    assert verdict.level is TrustLevel.BLOCKED
    assert verdict.attachable is False
    assert verdict.do_not_use is True


def test_low_severity_advisory_requires_review_not_block() -> None:
    # Graded severity: a low advisory does NOT block; it forces review.
    registry = TrustRegistry(
        validations=[_validation(HASH_A, TrustLevel.FIRST_PARTY)],
        advisories=[_advisory(tree_hash=None, name="demo-skill", source="first-party", severity=Severity.LOW)],
    )
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="demo-skill", source="first-party")
    assert verdict.blocked is False
    assert verdict.requires_review is True
    assert verdict.attachable is False  # review pending


def test_uppercase_hash_query_still_blocks_and_still_validates() -> None:
    # P0 regression: the advisory match and the validation lookup must see the
    # same normalized bytes, or an uppercase-hex query could bypass a block
    # while keeping its validation (advisory-wins must hold for every spelling).
    registry = TrustRegistry(
        validations=[_validation(HASH_A, TrustLevel.FIRST_PARTY)],
        advisories=[_advisory(tree_hash=HASH_A, severity=Severity.CRITICAL)],
    )
    verdict = evaluate_trust(registry, tree_hash=HASH_A.upper(), name="demo-skill", source="first-party")
    assert verdict.blocked is True
    assert verdict.attachable is False


def test_hash_matched_advisory_always_blocks_even_if_low() -> None:
    # An exact-bytes advisory is specific enough to hard-block regardless of severity.
    registry = TrustRegistry(advisories=[_advisory(tree_hash=HASH_A, severity=Severity.LOW)])
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="evil-skill", source="marketplace")
    assert verdict.blocked is True


def test_hash_mismatch_voids_validation() -> None:
    registry = TrustRegistry(validations=[_validation(HASH_A, TrustLevel.FIRST_PARTY)])
    verdict = evaluate_trust(registry, tree_hash=HASH_B, name="demo-skill", source="first-party")
    assert verdict.level is TrustLevel.UNVERIFIED
    assert verdict.validation is None
    assert verdict.requires_review is True


def test_strongest_validation_wins() -> None:
    registry = TrustRegistry(
        validations=[
            _validation(HASH_A, TrustLevel.ADOPTED, method="first-party-adoption"),
            _validation(HASH_A, TrustLevel.FIRST_PARTY),
        ]
    )
    verdict = evaluate_trust(registry, tree_hash=HASH_A)
    assert verdict.level is TrustLevel.FIRST_PARTY


def test_validated_clean_skill_is_attachable() -> None:
    registry = TrustRegistry(validations=[_validation(HASH_A, TrustLevel.FIRST_PARTY)])
    verdict = evaluate_trust(registry, tree_hash=HASH_A, has_scripts=False)
    assert verdict.attachable is True
    assert verdict.requires_review is False


def test_has_scripts_forces_review_even_when_validated() -> None:
    registry = TrustRegistry(validations=[_validation(HASH_A, TrustLevel.FIRST_PARTY)])
    verdict = evaluate_trust(registry, tree_hash=HASH_A, has_scripts=True)
    assert verdict.blocked is False
    assert verdict.requires_review is True
    assert verdict.attachable is False


def test_unknown_skill_is_unverified_and_requires_review() -> None:
    verdict = evaluate_trust(TrustRegistry(), tree_hash=HASH_A)
    assert verdict.level is TrustLevel.UNVERIFIED
    assert verdict.blocked is False
    assert verdict.requires_review is True  # fail closed
    assert verdict.attachable is False


def test_name_only_advisory_warns_but_still_blocks_when_high() -> None:
    registry = TrustRegistry(advisories=[_advisory(tree_hash=None, severity=Severity.HIGH)])
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="evil-skill", source="marketplace")
    assert verdict.blocked is True
    assert any("hash unverified" in w for w in verdict.warnings)


def test_withdrawn_advisory_does_not_block() -> None:
    registry = TrustRegistry(
        advisories=[_advisory(tree_hash=HASH_A, status="withdrawn", withdrawn_reason="fixed upstream", withdrawn_at="2026-07-12")]
    )
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="evil-skill", source="marketplace")
    assert verdict.blocked is False


def test_missing_tree_hash_warns() -> None:
    verdict = evaluate_trust(TrustRegistry(), tree_hash=None, name="x", source="s")
    assert verdict.level is TrustLevel.UNVERIFIED
    assert any("no tree_hash" in w for w in verdict.warnings)


# --- registry loading robustness ---

def test_registry_yaml_round_trip(tmp_path: Path) -> None:
    import yaml

    validations = tmp_path / "validations.yaml"
    advisories = tmp_path / "advisories.yaml"
    validations.write_text(yaml.safe_dump({"validations": [_validation().to_dict()]}), encoding="utf-8")
    advisories.write_text(
        yaml.safe_dump({"advisories": [_advisory(tree_hash=HASH_B).to_dict()]}), encoding="utf-8"
    )
    registry = TrustRegistry.load(validations_path=validations, advisories_path=advisories)
    assert len(registry.validations) == 1
    assert len(registry.advisories) == 1

    good = evaluate_trust(registry, tree_hash=HASH_A, name="demo-skill", source="first-party")
    assert good.level is TrustLevel.FIRST_PARTY
    bad = evaluate_trust(registry, tree_hash=HASH_B, name="evil-skill", source="marketplace")
    assert bad.blocked is True


def test_registry_load_rejects_advisory_missing_field(tmp_path: Path) -> None:
    import yaml

    advisories = tmp_path / "advisories.yaml"
    advisories.write_text(
        yaml.safe_dump(
            {"advisories": [{"name": "x", "source": "s", "official_intent": "i", "hidden_issue": "h", "severity": "high"}]}
        ),
        encoding="utf-8",
    )
    with pytest.raises(SkillValidationError):
        TrustRegistry.load(advisories_path=advisories)


def test_registry_load_rejects_scalar_list_item(tmp_path: Path) -> None:
    import yaml

    path = tmp_path / "validations.yaml"
    path.write_text(yaml.safe_dump({"validations": ["just-a-string"]}), encoding="utf-8")
    with pytest.raises(SkillValidationError):
        TrustRegistry.load(validations_path=path)


def test_duplicate_advisory_id_refused() -> None:
    with pytest.raises(SkillValidationError):
        TrustRegistry(
            advisories=[
                _advisory(tree_hash=HASH_A, advisory_id="DUP"),
                _advisory(tree_hash=HASH_B, advisory_id="DUP"),
            ]
        )


def test_bool_epochs_rejected_in_audit_evidence() -> None:
    with pytest.raises(SkillValidationError):
        ValidationRecord(
            name="x", source="s", tree_hash=HASH_A, level=TrustLevel.AUDITED,
            method="simulated-execution", validated_by="skill", validated_at="2026-07-11",
            evidence={"epochs": True, "models": ["m"]},
        )


def test_non_mapping_evidence_refused_at_load(tmp_path: Path) -> None:
    import yaml

    path = tmp_path / "validations.yaml"
    record = _validation().to_dict()
    record["evidence"] = [1, 2]  # not a mapping
    path.write_text(yaml.safe_dump({"validations": [record]}), encoding="utf-8")
    with pytest.raises(SkillValidationError):
        TrustRegistry.load(validations_path=path)


def test_duplicate_guidance_id_refused() -> None:
    g = GuidanceEntry(
        guidance_id="G", title="t", risk_class="r", detail="d",
        severity=Severity.LOW, reference="https://x",
    )
    g2 = GuidanceEntry(
        guidance_id="G", title="t2", risk_class="r2", detail="d2",
        severity=Severity.LOW, reference="https://y",
    )
    with pytest.raises(SkillValidationError):
        TrustRegistry(guidance=[g, g2])


# --- guidance ---

def test_guidance_entry_requires_fields_and_never_blocks() -> None:
    with pytest.raises(SkillValidationError):
        GuidanceEntry(guidance_id="", title="t", risk_class="r", detail="d", severity=Severity.HIGH, reference="http://x")
    g = GuidanceEntry(
        guidance_id="ASG-1", title="marketplace risk", risk_class="supply-chain",
        detail="don't install by download count", severity=Severity.CRITICAL,
        reference="https://example.org/x",
    )
    # Guidance is not consulted by evaluate_trust — it never forbids a specific skill.
    registry = TrustRegistry(guidance=[g])
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="anything", source="anywhere")
    assert verdict.blocked is False
    assert len(registry.guidance) == 1


# --- source derivation (TrustRegistry.source_for) ---

def _named_validation(name: str, source: str, tree_hash: str, level: TrustLevel = TrustLevel.ADOPTED) -> ValidationRecord:
    return ValidationRecord(
        name=name, source=source, tree_hash=tree_hash, level=level,
        method="first-party-adoption", validated_by="skill", validated_at="2026-07-11",
    )


def test_source_for_prefers_hash_bound() -> None:
    reg = TrustRegistry(validations=[
        _named_validation("demo", "old-market", HASH_B),   # name-bound (other bytes)
        _named_validation("demo", "market", HASH_A),        # hash-bound (these bytes)
    ])
    derived = reg.source_for(name="demo", tree_hash=HASH_A)
    assert derived is not None
    assert (derived.source, derived.binding, derived.ambiguous) == ("market", "hash", False)


def test_source_for_name_bound_fallback() -> None:
    reg = TrustRegistry(validations=[_named_validation("demo", "market", HASH_B)])
    derived = reg.source_for(name="demo", tree_hash=HASH_A)  # no record for HASH_A
    assert derived is not None
    assert (derived.source, derived.binding) == ("market", "name")


def test_source_for_none_when_unknown() -> None:
    assert TrustRegistry().source_for(name="ghost", tree_hash=HASH_A) is None


def test_source_for_hash_bound_prefers_matching_name() -> None:
    # Same bytes vendored under two names; the record naming THIS skill wins
    # even when the other-name record carries a HIGHER trust level.
    other = ValidationRecord(
        name="other-name", source="src-other", tree_hash=HASH_A,
        level=TrustLevel.AUDITED, method="external-audit", validated_by="skill",
        validated_at="2026-07-11", evidence={"reference": "https://audit.example"},
    )
    reg = TrustRegistry(validations=[
        other,
        _named_validation("demo", "src-demo", HASH_A),
    ])
    derived = reg.source_for(name="demo", tree_hash=HASH_A)
    assert derived is not None
    assert derived.source == "src-demo"
    assert derived.ambiguous is True  # registry disagrees about these bytes' source


def test_source_for_name_bound_ambiguity_flagged() -> None:
    reg = TrustRegistry(validations=[
        _named_validation("demo", "market-a", HASH_A, level=TrustLevel.COMMUNITY),
        _named_validation("demo", "market-b", HASH_B, level=TrustLevel.ADOPTED),
    ])
    derived = reg.source_for(name="demo", tree_hash="c" * 64)
    assert derived is not None
    assert derived.source == "market-b"  # highest trust level wins, deterministic
    assert derived.binding == "name"
    assert derived.ambiguous is True


def test_source_for_normalizes_hash_spelling() -> None:
    reg = TrustRegistry(validations=[_named_validation("demo", "market", HASH_A)])
    derived = reg.source_for(name="demo", tree_hash=HASH_A.upper())
    assert derived is not None and derived.binding == "hash"


# --- name case normalization + registry lint ---

def test_uppercase_advisory_name_matches_spec_lowercase_skill() -> None:
    # The Agent Skills spec requires lowercase names, so 'Evil' in a registry
    # entry could never match a loadable skill — names normalize at
    # construction and at the query boundary (silent-miss killer).
    advisory = AdvisoryEntry(
        name="Evil-Skill", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    assert advisory.name == "evil-skill"
    registry = TrustRegistry(advisories=[advisory])
    verdict = evaluate_trust(registry, tree_hash=HASH_A, name="evil-skill", source="market")
    assert verdict.blocked
    # Query-side case symmetry: an uppercase query still matches.
    verdict2 = evaluate_trust(registry, tree_hash=HASH_A, name="EVIL-SKILL", source="market")
    assert verdict2.blocked


def test_validation_record_name_lowercased() -> None:
    record = _named_validation("Demo", "market", HASH_A)
    assert record.name == "demo"
    reg = TrustRegistry(validations=[record])
    derived = reg.source_for(name="DEMO", tree_hash=None)
    assert derived is not None and derived.source == "market"


def test_lint_flags_spec_invalid_advisory_name() -> None:
    advisory = AdvisoryEntry(
        name="my_skill!", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", advisory_id="ASG-1",
    )
    from abstractskill import lint_registry
    warnings = lint_registry(TrustRegistry(advisories=[advisory]))
    assert any("violates the skill-name spec" in w and "ASG-1" in w for w in warnings)


def test_lint_flags_case_only_source_mismatch() -> None:
    from abstractskill import lint_registry
    validation = _named_validation("demo", "codex-skills (maintainer)", HASH_A)
    advisory = AdvisoryEntry(
        name="demo", source="Codex-Skills (Maintainer)", official_intent="i",
        hidden_issue="h", severity=Severity.HIGH, reference="https://x",
    )
    warnings = lint_registry(TrustRegistry(validations=[validation], advisories=[advisory]))
    assert any("only by case" in w for w in warnings)


def test_lint_flags_unknown_source_softly() -> None:
    from abstractskill import lint_registry
    validation = _named_validation("demo", "first-party", HASH_A)
    advisory = AdvisoryEntry(
        name="demo", source="some-marketplace", official_intent="i",
        hidden_issue="h", severity=Severity.HIGH, reference="https://x",
    )
    warnings = lint_registry(TrustRegistry(validations=[validation], advisories=[advisory]))
    assert any("matches no known validation source" in w for w in warnings)


def test_lint_clean_registry_and_exemptions() -> None:
    from abstractskill import lint_registry
    validation = _named_validation("demo", "market", HASH_A)
    matching = AdvisoryEntry(  # name-anchored, source known: clean
        name="demo", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    hash_anchored = AdvisoryEntry(  # unknown source but hash-anchored: exempt
        name="other", source="anywhere", official_intent="i", hidden_issue="h",
        severity=Severity.LOW, reference="https://x", tree_hash=HASH_B,
    )
    withdrawn = AdvisoryEntry(  # withdrawn: history, not linted
        name="gone", source="nowhere", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", status="withdrawn",
        withdrawn_reason="fixed upstream",
    )
    warnings = lint_registry(
        TrustRegistry(validations=[validation], advisories=[matching, hash_anchored, withdrawn])
    )
    assert warnings == ()


def test_padded_query_source_still_matches_advisory() -> None:
    # Re-attack finding 1: a padded caller source (quoted-YAML class) must not
    # fail OPEN — stripping the query widens the advisory surface (safe).
    advisory = AdvisoryEntry(
        name="evil", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    reg = TrustRegistry(validations=[_validation()], advisories=[advisory])
    verdict = evaluate_trust(reg, tree_hash=HASH_A, name="evil", source="market ")
    assert verdict.blocked


def test_lint_flags_overlong_advisory_name() -> None:
    # Re-attack finding 2: SKILL_NAME_RE has no length bound; a 65-char name
    # passes the regex yet can never load (64-char spec cap).
    from abstractskill import lint_registry
    advisory = AdvisoryEntry(
        name="a" * 65, source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", advisory_id="ASG-LEN",
    )
    warnings = lint_registry(TrustRegistry(advisories=[advisory]))
    assert any("ASG-LEN" in w and "skill-name spec" in w for w in warnings)


def test_lint_names_all_case_twins_deterministically() -> None:
    # Re-attack finding 3: case-twin validation sources are themselves
    # flagged, and the advisory message names ALL twins sorted.
    from abstractskill import lint_registry
    v1 = _named_validation("demo", "Market", HASH_A)
    v2 = _named_validation("demo2", "market", HASH_B)
    advisory = AdvisoryEntry(
        name="demo", source="MARKET", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    warnings = lint_registry(TrustRegistry(validations=[v1, v2], advisories=[advisory]))
    assert any("differ only by case" in w and "'Market'" in w and "'market'" in w for w in warnings)
    assert any("only by case" in w and "MARKET" in w for w in warnings)


def test_lint_advisories_only_registry_one_aggregate_line() -> None:
    # Re-attack finding 4: an advisories-only feed gets ONE aggregate note,
    # never N per-entry "unknown source" noise lines.
    from abstractskill import lint_registry
    advisories = [
        AdvisoryEntry(
            name=f"skill-{i}", source="feed", official_intent="i", hidden_issue="h",
            severity=Severity.HIGH, reference="https://x",
        )
        for i in range(3)
    ]
    warnings = lint_registry(TrustRegistry(advisories=advisories))
    source_lines = [w for w in warnings if "cross-checked" in w or "unknown" in w.lower()]
    assert len(source_lines) == 1
    assert "no validation records" in source_lines[0]


def test_lint_hash_anchored_bad_name_message_names_the_live_anchor() -> None:
    # Re-attack finding 5: a hash-anchored advisory with a display-fidelity
    # name is not "can never match" — the hash anchor still protects.
    from abstractskill import lint_registry
    advisory = AdvisoryEntry(
        name="PDF_Tools!", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.LOW, reference="https://x", tree_hash=HASH_A,
    )
    warnings = lint_registry(TrustRegistry(advisories=[advisory]))
    assert any("hash anchor still matches" in w for w in warnings)
    assert not any("can never match a loadable skill" in w for w in warnings)


def test_matches_level_source_strip_is_independent_of_evaluate_trust() -> None:
    # Defense-in-depth pin: the strip inside AdvisoryEntry.matches holds for
    # DIRECT callers (active_advisories_for), not only via evaluate_trust's
    # head normalization.
    advisory = AdvisoryEntry(
        name="evil", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    reg = TrustRegistry(advisories=[advisory])
    hits = reg.active_advisories_for(tree_hash=None, name="EVIL ", source=" market\n")
    assert [strength for _, strength in hits] == ["name"]


def test_activation_descriptions_rank_tiebreak_pinned() -> None:
    # The registry-wide map's documented rule: on same-name collisions the
    # higher trust level wins, deterministically (was covered by code-reading
    # only — cycle-3 adversary asked for the pin).
    low = ValidationRecord(
        name="demo", source="market", tree_hash=HASH_A, level=TrustLevel.COMMUNITY,
        method="manual-review", validated_by="s", validated_at="2026-07-11",
        activation_description="LOW",
    )
    high = ValidationRecord(
        name="Demo", source="market", tree_hash=HASH_B, level=TrustLevel.ADOPTED,
        method="first-party-adoption", validated_by="s", validated_at="2026-07-11",
        activation_description="HIGH",
    )
    reg = TrustRegistry(validations=[low, high])
    # Construction lowercases both names to one key; higher rank wins.
    assert reg.activation_descriptions() == {"demo": "HIGH"}
