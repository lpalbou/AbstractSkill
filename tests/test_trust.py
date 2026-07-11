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
