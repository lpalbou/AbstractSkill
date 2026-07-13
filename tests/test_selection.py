"""Trust-gated selection pipeline — the structural ordering that a naive host
would otherwise get wrong (blocked-not-review trap, source-less advisory)."""

from __future__ import annotations

from pathlib import Path

import yaml

from abstractskill import (
    AdvisoryEntry,
    Severity,
    TrustRegistry,
    ValidationRecord,
    TrustLevel,
    hash_skill_tree,
    select_skills_for_context,
)


def _write_skill(root: Path, name: str, description: str = "A demo skill.") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nBody for {name}.\n",
        encoding="utf-8",
    )
    return skill_dir


def _validation(name: str, tree_hash: str, level: TrustLevel = TrustLevel.FIRST_PARTY) -> ValidationRecord:
    return ValidationRecord(
        name=name, source="first-party", tree_hash=tree_hash, level=level,
        method="first-party", validated_by="skill", validated_at="2026-07-11",
    )


def test_validated_clean_skill_is_active(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "good")
    reg = TrustRegistry(validations=[_validation("good", hash_skill_tree(d))])
    sel = select_skills_for_context(reg, shelf, ["good"])
    assert sel.active_names == ("good",)
    assert sel.held == () and sel.blocked == ()


def test_multi_root_shadow_never_inherits_curated_trust(tmp_path: Path) -> None:
    # Multi-root selection (curated shelf + user dir): the user copy WINS by
    # loader precedence but its different bytes match no validation record —
    # it must be HELD as unverified, never active on the curated record.
    curated = tmp_path / "curated"
    user = tmp_path / "user"
    curated_dir = _write_skill(curated, "good", description="Curated copy.")
    _write_skill(user, "good", description="User shadow copy.")
    reg = TrustRegistry(validations=[_validation("good", hash_skill_tree(curated_dir))])

    sel = select_skills_for_context(reg, [curated, user], ["good"])
    assert sel.active_names == ()
    assert [n for n, _ in sel.held] == ["good"]

    # Same call without the shadow: the curated copy activates normally.
    sel_curated = select_skills_for_context(reg, [curated], ["good"])
    assert sel_curated.active_names == ("good",)


def test_broken_user_shadow_falls_back_to_curated_loudly(tmp_path: Path) -> None:
    # A user-root SKILL.md that cannot even decode (binary bytes) must not
    # crash the selection NOR deny the skill: the loader skips it with a
    # #FALLBACK and the curated copy activates on its own record.
    curated = tmp_path / "curated"
    user = tmp_path / "user"
    curated_dir = _write_skill(curated, "good")
    bad_dir = user / "good"
    bad_dir.mkdir(parents=True)
    (bad_dir / "SKILL.md").write_bytes(b"\xff\xfe\x00broken")
    reg = TrustRegistry(validations=[_validation("good", hash_skill_tree(curated_dir))])

    warnings: list[str] = []
    sel = select_skills_for_context(
        reg, [curated, user], ["good"], on_warning=warnings.append
    )
    assert sel.active_names == ("good",)
    assert any("#FALLBACK" in w and "not valid UTF-8" in w for w in warnings)


def test_standing_enable_on_shadow_activates_loudly_with_path(tmp_path: Path) -> None:
    # The enable grant is name-bound while trust binds to bytes: a standing
    # enable DOES activate a user shadow (unverified + enabled), but the
    # activation must name the winning copy's path and hash — never silent.
    curated = tmp_path / "curated"
    user = tmp_path / "user"
    curated_dir = _write_skill(curated, "tooled", description="Curated copy.")
    shadow_dir = _write_skill(user, "tooled", description="User shadow.")
    reg = TrustRegistry(validations=[_validation("tooled", hash_skill_tree(curated_dir))])

    warnings: list[str] = []
    sel = select_skills_for_context(
        reg, [curated, user], ["tooled"], enabled=["tooled"],
        on_warning=warnings.append,
    )
    assert sel.active_names == ("tooled",)
    note = next(w for w in warnings if "activated by operator enable" in w)
    assert str(shadow_dir) in note  # the WINNING copy is named, not the curated one


def test_unverified_skill_is_held_not_active(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    _write_skill(shelf, "unknown")
    sel = select_skills_for_context(TrustRegistry(), shelf, ["unknown"])
    assert sel.active_names == ()
    assert [n for n, _ in sel.held] == ["unknown"]


def test_operator_enable_activates_a_held_skill(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    _write_skill(shelf, "unknown")
    sel = select_skills_for_context(TrustRegistry(), shelf, ["unknown"], enabled=["unknown"])
    assert sel.active_names == ("unknown",)


def test_blocked_skill_is_never_active_even_if_enabled(tmp_path: Path) -> None:
    # The blocked-not-review trap: a blocked verdict has requires_review=False.
    # Operator "enable" must NOT activate it (blocked is harder than review).
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "evil")
    advisory = AdvisoryEntry(
        name="evil", source="market", official_intent="i", hidden_issue="exfiltrates secrets",
        severity=Severity.CRITICAL, reference="https://x", tree_hash=hash_skill_tree(d),
    )
    reg = TrustRegistry(advisories=[advisory])
    sel = select_skills_for_context(
        reg, shelf, ["evil"], sources={"evil": "market"}, enabled=["evil"],
    )
    assert sel.active_names == ()
    assert [n for n, _ in sel.blocked] == ["evil"]


def test_source_less_name_anchored_advisory_warns(tmp_path: Path) -> None:
    # P1-A: a name-anchored advisory exists but the host supplies no source →
    # the check can't match; the pipeline must say so loudly, not silently pass.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "suspect")
    advisory = AdvisoryEntry(
        name="suspect", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["suspect"])  # no sources
    assert any("no source" in w for w in sel.warnings)


def test_source_supplied_name_anchored_advisory_blocks(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    _write_skill(shelf, "suspect")
    advisory = AdvisoryEntry(
        name="suspect", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["suspect"], sources={"suspect": "market"})
    assert [n for n, _ in sel.blocked] == ["suspect"]


def test_missing_skill_is_reported_not_crashed(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    shelf.mkdir()
    sel = select_skills_for_context(TrustRegistry(), shelf, ["nope"])
    assert sel.missing == ("nope",)
    assert sel.active_names == ()


def test_scripts_skill_is_held_until_enabled(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "tooled")
    (d / "scripts").mkdir()
    (d / "scripts" / "run.py").write_text("print('x')\n", encoding="utf-8")
    reg = TrustRegistry(validations=[_validation("tooled", hash_skill_tree(d))])
    # Even validated, scripts force review — not active by default.
    sel = select_skills_for_context(reg, shelf, ["tooled"])
    assert sel.active_names == ()
    assert [n for n, _ in sel.held] == ["tooled"]


def test_source_derived_from_hash_bound_record_matches_advisory(tmp_path: Path) -> None:
    # THE c645 scenario: a names-only phase config (no sources passed) must
    # still match a name-anchored advisory — provenance comes from the
    # registry's validation record for these exact bytes.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "vendored")
    tree = hash_skill_tree(d)
    validation = ValidationRecord(
        name="vendored", source="market", tree_hash=tree, level=TrustLevel.ADOPTED,
        method="first-party-adoption", validated_by="skill", validated_at="2026-07-11",
    )
    advisory = AdvisoryEntry(
        name="vendored", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(validations=[validation], advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["vendored"])  # NO sources arg
    assert [n for n, _ in sel.blocked] == ["vendored"]
    # Exact (hash-bound) provenance: no weaker-fallback warning, no "no source".
    assert not any("no source" in w for w in sel.warnings)
    assert not any("name-bound" in w for w in sel.warnings)


def test_source_derived_from_name_bound_record_warns_but_matches(tmp_path: Path) -> None:
    # The vendored bytes drifted (no validation for the CURRENT hash), but a
    # record for the same name carries the last known provenance — the
    # advisory still matches, loudly labeled as weaker.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "drifted")
    stale_validation = ValidationRecord(
        name="drifted", source="market", tree_hash="0" * 64, level=TrustLevel.ADOPTED,
        method="first-party-adoption", validated_by="skill", validated_at="2026-07-10",
    )
    advisory = AdvisoryEntry(
        name="drifted", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.CRITICAL, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(validations=[stale_validation], advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["drifted"])
    assert [n for n, _ in sel.blocked] == ["drifted"]
    assert any("name-bound" in w for w in sel.warnings)


def test_explicit_source_still_wins_over_registry(tmp_path: Path) -> None:
    # Caller-supplied source is authoritative when no hash-bound record
    # contradicts it; a (name, caller-source) advisory matches.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "explicit")
    advisory = AdvisoryEntry(
        name="explicit", source="caller-market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(advisories=[advisory])
    sel = select_skills_for_context(
        reg, shelf, ["explicit"], sources={"explicit": "caller-market"}
    )
    assert [n for n, _ in sel.blocked] == ["explicit"]


def test_contradicting_caller_source_cannot_evade_advisory(tmp_path: Path) -> None:
    # Fail-closed cross-check: registry attests these bytes came from
    # "market" (where an advisory targets it); a caller claiming a different
    # source must not bypass the block.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "evasive")
    tree = hash_skill_tree(d)
    validation = ValidationRecord(
        name="evasive", source="market", tree_hash=tree, level=TrustLevel.ADOPTED,
        method="first-party-adoption", validated_by="skill", validated_at="2026-07-11",
    )
    advisory = AdvisoryEntry(
        name="evasive", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(validations=[validation], advisories=[advisory])
    sel = select_skills_for_context(
        reg, shelf, ["evasive"], sources={"evasive": "innocent-looking"}
    )
    assert [n for n, _ in sel.blocked] == ["evasive"]
    assert any("contradicts registry provenance" in w for w in sel.warnings)


def test_no_source_anywhere_still_warns(tmp_path: Path) -> None:
    # No caller source AND no registry record: the original loud warning
    # (name/source matching disabled) must survive the derivation change.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "orphan")
    advisory = AdvisoryEntry(
        name="orphan", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x", tree_hash=None,
    )
    reg = TrustRegistry(advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["orphan"])
    assert any("no source" in w for w in sel.warnings)
    # Not blocked — the advisory can't match without a source; held as
    # unverified instead (fail-closed default).
    assert [n for n, _ in sel.held] == [("orphan")]


def test_losing_hash_bound_candidate_still_blocks(tmp_path: Path) -> None:
    # Adversary finding 1: two hash-bound records for the SAME bytes with
    # different sources; the advisory targets the LOSING (lower-trust)
    # candidate. The gate must check every candidate, not the winner.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "dual")
    tree = hash_skill_tree(d)
    winner = ValidationRecord(
        name="dual", source="mirror", tree_hash=tree, level=TrustLevel.ADOPTED,
        method="first-party-adoption", validated_by="s", validated_at="2026-07-11",
    )
    loser = ValidationRecord(
        name="dual", source="market", tree_hash=tree, level=TrustLevel.COMMUNITY,
        method="manual-review", validated_by="s", validated_at="2026-07-11",
    )
    advisory = AdvisoryEntry(
        name="dual", source="market", official_intent="i", hidden_issue="trojan",
        severity=Severity.HIGH, reference="https://x",
    )
    reg = TrustRegistry(validations=[winner, loser], advisories=[advisory])
    # Variant A: names-only call.
    sel = select_skills_for_context(reg, shelf, ["dual"])
    assert [n for n, _ in sel.blocked] == ["dual"]
    assert any("disagree on the source" in w for w in sel.warnings)
    # Variant B: caller explicitly supplies the WINNING (innocent) source —
    # must still block via the losing candidate, with zero silent paths.
    sel_b = select_skills_for_context(reg, shelf, ["dual"], sources={"dual": "mirror"})
    assert [n for n, _ in sel_b.blocked] == ["dual"]


def test_explicit_source_vs_name_bound_contradiction_blocks(tmp_path: Path) -> None:
    # Adversary finding 2: a caller-supplied source must not silently
    # override NAME-bound registry provenance whose advisory would block.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "drifted2")
    stale = ValidationRecord(
        name="drifted2", source="market", tree_hash="0" * 64, level=TrustLevel.ADOPTED,
        method="first-party-adoption", validated_by="s", validated_at="2026-07-10",
    )
    advisory = AdvisoryEntry(
        name="drifted2", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.CRITICAL, reference="https://x",
    )
    reg = TrustRegistry(validations=[stale], advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["drifted2"], sources={"drifted2": "vendor-x"})
    assert [n for n, _ in sel.blocked] == ["drifted2"]
    assert any("contradicts registry provenance" in w for w in sel.warnings)


def test_blank_explicit_source_treated_as_absent(tmp_path: Path) -> None:
    # Adversary finding 3: sources={name: ""} must not silently disable
    # name/source matching NOR suppress the loud no-source warning.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "suspect2")
    advisory = AdvisoryEntry(
        name="suspect2", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    reg = TrustRegistry(advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["suspect2"], sources={"suspect2": "  "})
    assert any("blank source" in w for w in sel.warnings)
    assert any("no source" in w for w in sel.warnings)


def test_bad_tree_holds_one_skill_not_the_phase(tmp_path: Path) -> None:
    # Adversary finding 5: a symlink-bearing skill must land in `missing`,
    # never crash the whole selection (one bad apple ≠ phase denial).
    shelf = tmp_path / "skills"
    good = _write_skill(shelf, "good2")
    bad = _write_skill(shelf, "trap")
    (bad / "link").symlink_to(tmp_path)
    reg = TrustRegistry(validations=[_validation("good2", hash_skill_tree(good))])
    sel = select_skills_for_context(reg, shelf, ["good2", "trap"])
    assert sel.active_names == ("good2",)
    assert sel.missing == ("trap",)
    assert any("trap" in w and "#FALLBACK" in w for w in sel.warnings)


def test_duplicate_names_processed_once_with_warning(tmp_path: Path) -> None:
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "solo")
    reg = TrustRegistry(validations=[_validation("solo", hash_skill_tree(d))])
    sel = select_skills_for_context(reg, shelf, ["solo", "solo"])
    assert sel.active_names == ("solo",)
    assert any("duplicate skill name" in w for w in sel.warnings)


def test_non_string_source_contained_not_crashing(tmp_path: Path) -> None:
    # Re-attack NEW-1: a host bug passing a non-string source must demote to
    # derivation with a loud note, never crash the whole phase.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "typed")
    reg = TrustRegistry(validations=[_validation("typed", hash_skill_tree(d))])
    sel = select_skills_for_context(reg, shelf, ["typed"], sources={"typed": 123})  # type: ignore[dict-item]
    assert sel.active_names == ("typed",)
    assert any("non-string source" in w for w in sel.warnings)


def test_logic_bug_in_tree_inspection_surfaces(tmp_path: Path, monkeypatch) -> None:
    # Re-attack NEW-2: containment is for SkillError/OSError only — a logic
    # bug (TypeError) in tree code must SURFACE, not demote skills silently.
    import abstractskill.selection as selection_mod

    shelf = tmp_path / "skills"
    _write_skill(shelf, "buggy")

    def _boom(_root):  # simulates a regression in inspect_skill_dir
        raise TypeError("synthetic bug")

    monkeypatch.setattr(selection_mod, "inspect_skill_dir", _boom)
    try:
        select_skills_for_context(TrustRegistry(), shelf, ["buggy"])
        raise AssertionError("logic bug was swallowed")
    except TypeError:
        pass


def test_verdict_caveats_reach_on_warning(tmp_path: Path) -> None:
    # Re-attack NEW-3: verdict-level caveats (e.g. name/source-only advisory
    # match) must reach the on_warning channel, not only the returned tuple.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "caveat")
    advisory = AdvisoryEntry(
        name="caveat", source="market", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    reg = TrustRegistry(advisories=[advisory])
    seen: list[str] = []
    sel = select_skills_for_context(
        reg, shelf, ["caveat"], sources={"caveat": "market"}, on_warning=seen.append
    )
    assert [n for n, _ in sel.blocked] == ["caveat"]
    assert any("name/source match" in w or "hash unverified" in w for w in seen)


def test_whitespace_in_registry_source_still_matches_advisory(tmp_path: Path) -> None:
    # Adversary finding 4: a quoted YAML scalar with trailing whitespace must
    # not silently void the (name, source) match — stripped write-back.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "spacey")
    validation = ValidationRecord(
        name="spacey ", source=" market ", tree_hash=hash_skill_tree(d),
        level=TrustLevel.ADOPTED, method="first-party-adoption",
        validated_by="s", validated_at="2026-07-11",
    )
    advisory = AdvisoryEntry(
        name=" spacey", source="market ", official_intent="i", hidden_issue="h",
        severity=Severity.HIGH, reference="https://x",
    )
    reg = TrustRegistry(validations=[validation], advisories=[advisory])
    sel = select_skills_for_context(reg, shelf, ["spacey"])
    assert [n for n, _ in sel.blocked] == ["spacey"]


def test_activation_description_only_from_current_hash(tmp_path: Path) -> None:
    # P2-F: a stale record for other bytes must not override the prompt line.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "doc")
    current = hash_skill_tree(d)
    stale = "0" * 64
    reg = TrustRegistry(
        validations=[
            ValidationRecord(
                name="doc", source="first-party", tree_hash=stale, level=TrustLevel.FIRST_PARTY,
                method="first-party", validated_by="skill", validated_at="2026-07-11",
                activation_description="STALE override",
            ),
            ValidationRecord(
                name="doc", source="first-party", tree_hash=current, level=TrustLevel.FIRST_PARTY,
                method="first-party", validated_by="skill", validated_at="2026-07-11",
                activation_description="CURRENT override",
            ),
        ]
    )
    sel = select_skills_for_context(reg, shelf, ["doc"])
    assert sel.activation_descriptions.get("doc") == "CURRENT override"


def test_uppercase_config_name_fails_closed(tmp_path: Path) -> None:
    # Case normalization deliberately stops at the loader boundary: a config
    # naming 'Solo' cannot load (spec-lowercase names) and lands in missing —
    # fail-closed — and an uppercase `enabled` entry never activates a held
    # skill (it stays visibly held).
    shelf = tmp_path / "skills"
    _write_skill(shelf, "solo2")
    sel = select_skills_for_context(TrustRegistry(), shelf, ["Solo2"])
    assert sel.missing == ("Solo2",)
    sel2 = select_skills_for_context(TrustRegistry(), shelf, ["solo2"], enabled=["SOLO2"])
    assert sel2.active_names == ()
    assert [n for n, _ in sel2.held] == ["solo2"]


# --- hash-pinned enables -----------------------------------------------------


def test_hash_pinned_enable_activates_matching_bytes(tmp_path: Path) -> None:
    # The durable enable form: `name@tree_hash` grants exactly the reviewed
    # bytes; the activation note says the grant was hash-pinned.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "pinme")
    pin = hash_skill_tree(d)
    warnings: list[str] = []
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["pinme"], enabled=[f"pinme@{pin}"],
        on_warning=warnings.append,
    )
    assert sel.active_names == ("pinme",)
    assert any("hash-pinned operator enable" in w for w in warnings)


def test_hash_pinned_enable_mismatch_holds_and_names_both_hashes(tmp_path: Path) -> None:
    # A pin that no longer matches the winning copy must NOT activate — the
    # exact shadow-swap scenario the pin exists to stop — and the note names
    # both the pinned and the actual hash so re-pinning is a deliberate act.
    curated = tmp_path / "curated"
    user = tmp_path / "user"
    curated_dir = _write_skill(curated, "pinme", description="Reviewed copy.")
    _write_skill(user, "pinme", description="Shadow copy.")
    reviewed_pin = hash_skill_tree(curated_dir)

    warnings: list[str] = []
    sel = select_skills_for_context(
        TrustRegistry(), [curated, user], ["pinme"],
        enabled=[f"pinme@{reviewed_pin}"], on_warning=warnings.append,
    )
    assert sel.active_names == ()
    assert [n for n, _ in sel.held] == ["pinme"]
    note = next(w for w in warnings if "pinned to" in w)
    assert reviewed_pin[:16] in note
    assert sel.resolved_tree_hashes["pinme"][:16] in note


def test_pins_govern_over_bare_entry_for_same_name(tmp_path: Path) -> None:
    # `enabled: ["x", "x@WRONG"]` must not fall back to the bare grant — that
    # would make every pin decorative. The bare entry is ignored loudly.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "mixed")
    wrong_pin = "a" * 64
    warnings: list[str] = []
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["mixed"], enabled=["mixed", f"mixed@{wrong_pin}"],
        on_warning=warnings.append,
    )
    assert sel.active_names == ()
    assert [n for n, _ in sel.held] == ["mixed"]
    assert any("pins govern" in w for w in warnings)


def test_malformed_pin_grants_nothing(tmp_path: Path) -> None:
    # Fail-closed: a short/non-hex/bad-name/double-@/overlong pin is dropped
    # with a warning — never demoted to a bare-name grant (that would widen
    # what it narrows).
    shelf = tmp_path / "skills"
    _write_skill(shelf, "target")
    warnings: list[str] = []
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["target"],
        enabled=[
            "target@deadbeef",          # short
            "Bad Name@" + "b" * 64,     # invalid name
            "@" + "c" * 64,             # empty name
            "  ",                       # blank entry
            "target@@" + "d" * 64,      # double @ -> hex part fails
            "target@" + "e" * 65,       # overlong hash
        ],
        on_warning=warnings.append,
    )
    assert sel.active_names == ()
    assert [n for n, _ in sel.held] == ["target"]
    assert sum("malformed enabled" in w for w in warnings) == 6


def test_uppercase_hex_pin_matches_case_normalized(tmp_path: Path) -> None:
    # Hex case is presentation, not identity: an uppercase-hex pin grants
    # the same bytes (the hash value is what attests).
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "shouty")
    pin = hash_skill_tree(d).upper()
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["shouty"], enabled=[f"shouty@{pin}"],
    )
    assert sel.active_names == ("shouty",)


def test_enabled_scalar_string_never_grants_per_character(tmp_path: Path) -> None:
    # The YAML scalar-vs-list slip (`enabled: "a"` instead of `enabled: [a]`)
    # must not iterate characters into one-letter grants; the scalar is
    # treated as a single entry.
    shelf = tmp_path / "skills"
    _write_skill(shelf, "a")  # single-char names are spec-valid
    _write_skill(shelf, "ab")
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["a", "ab"], enabled="ab",
    )
    # "ab" granted as ONE name; "a" must NOT be granted by iteration.
    assert sel.active_names == ("ab",)
    assert [n for n, _ in sel.held] == ["a"]
    # And None crashes nothing:
    sel_none = select_skills_for_context(TrustRegistry(), shelf, ["a"], enabled=None)
    assert [n for n, _ in sel_none.held] == ["a"]


def test_multiple_pins_any_match_grants(tmp_path: Path) -> None:
    # An operator may allow two reviewed trees (e.g. old + new during a
    # rollout): matching ANY listed pin grants.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "dualpin")
    real = hash_skill_tree(d)
    other = "f" * 64
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["dualpin"],
        enabled=[f"dualpin@{other}", f"dualpin@{real}"],
    )
    assert sel.active_names == ("dualpin",)


def test_pin_never_constrains_attachable_bytes(tmp_path: Path) -> None:
    # Pins lift review; they are not a second registry. An attachable skill
    # activates even when a stale pin names different bytes.
    shelf = tmp_path / "skills"
    d = _write_skill(shelf, "validated")
    reg = TrustRegistry(validations=[_validation("validated", hash_skill_tree(d))])
    sel = select_skills_for_context(
        reg, shelf, ["validated"], enabled=["validated@" + "0" * 64],
    )
    assert sel.active_names == ("validated",)


# --- load→inspect byte cross-check (TOCTOU) ----------------------------------


def test_skill_md_swap_between_load_and_hash_refuses(tmp_path: Path, monkeypatch) -> None:
    # If SKILL.md changes between the loader's read and the tree hash walk,
    # the verdict would attest bytes that were never parsed. Simulate the
    # race by doctoring the inventory's per-file digest for SKILL.md.
    import abstractskill.selection as selection_mod
    from abstractskill.tree import inspect_skill_dir as real_inspect

    shelf = tmp_path / "skills"
    _write_skill(shelf, "raced")

    def doctored_inspect(path):
        inv = real_inspect(path)
        swapped = tuple(
            type(r)(rel_path=r.rel_path, size_bytes=r.size_bytes, sha256="e" * 64)
            if r.rel_path == "SKILL.md" else r
            for r in inv.files
        )
        return type(inv)(
            root_dir=inv.root_dir, files=swapped, tree_hash=inv.tree_hash,
            total_bytes=inv.total_bytes, has_scripts=inv.has_scripts,
        )

    monkeypatch.setattr(selection_mod, "inspect_skill_dir", doctored_inspect)
    warnings: list[str] = []
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["raced"], on_warning=warnings.append,
    )
    assert sel.missing == ("raced",)
    assert sel.active_names == () and sel.held == ()
    assert any("changed between load and hash" in w for w in warnings)
    # No attested copy: the raced name appears in neither resolved mapping.
    assert "raced" not in sel.resolved_paths
    assert "raced" not in sel.resolved_tree_hashes


def test_crlf_skill_md_passes_byte_cross_check(tmp_path: Path) -> None:
    # The digest compares RAW bytes on both sides — a CRLF-authored SKILL.md
    # must not false-positive as a swap (the old text-mode read translated
    # newlines and would have).
    shelf = tmp_path / "skills"
    d = shelf / "windowsy"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(
        b"---\r\nname: windowsy\r\ndescription: CRLF-authored.\r\n---\r\n\r\nBody.\r\n"
    )
    warnings: list[str] = []
    sel = select_skills_for_context(
        TrustRegistry(), shelf, ["windowsy"], on_warning=warnings.append,
    )
    assert [n for n, _ in sel.held] == ["windowsy"]  # unverified, but LOADED
    assert not any("changed between load and hash" in w for w in warnings)


# --- resolved copy surfacing ---------------------------------------------------


def test_selection_mappings_are_sealed_read_only(tmp_path: Path) -> None:
    # frozen=True blocks rebinding, not in-place mutation — and
    # resolved_tree_hashes is exactly what an operator copies into a hash
    # pin. The Mapping fields must be real read-only views.
    import pytest

    shelf = tmp_path / "skills"
    _write_skill(shelf, "sealme")
    sel = select_skills_for_context(TrustRegistry(), shelf, ["sealme"])
    with pytest.raises(TypeError):
        sel.resolved_tree_hashes["sealme"] = "0" * 64  # type: ignore[index]
    with pytest.raises(TypeError):
        sel.resolved_paths["sealme"] = Path("/tmp")  # type: ignore[index]


def test_resolved_paths_and_hashes_cover_all_attested_outcomes(tmp_path: Path) -> None:
    # Operators deciding on held/blocked entries need WHICH copy and the
    # exact hash to pin; missing names have no attested copy.
    curated = tmp_path / "curated"
    active_dir = _write_skill(curated, "activeone")
    held_dir = _write_skill(curated, "heldone")
    blocked_dir = _write_skill(curated, "blockedone")
    reg = TrustRegistry(
        validations=[_validation("activeone", hash_skill_tree(active_dir))],
        advisories=[
            AdvisoryEntry(
                name="blockedone", source="market",
                tree_hash=hash_skill_tree(blocked_dir),
                official_intent="test", hidden_issue="test",
                severity=Severity.CRITICAL, reference="https://example.test/adv",
            )
        ],
    )
    sel = select_skills_for_context(
        reg, curated, ["activeone", "heldone", "blockedone", "ghost"],
    )
    assert sel.active_names == ("activeone",)
    assert [n for n, _ in sel.held] == ["heldone"]
    assert [n for n, _ in sel.blocked] == ["blockedone"]
    assert sel.missing == ("ghost",)
    assert sel.resolved_paths == {
        "activeone": active_dir, "heldone": held_dir, "blockedone": blocked_dir,
    }
    assert sel.resolved_tree_hashes["heldone"] == hash_skill_tree(held_dir)
    assert "ghost" not in sel.resolved_paths
