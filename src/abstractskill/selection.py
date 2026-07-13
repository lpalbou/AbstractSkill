"""Trust-gated skill selection: the ONE composed pipeline for a context.

The trust gate is only as good as the discipline that runs it. `evaluate_trust`
+ `effective_tools` + `format_available_skills_xml` are separate primitives, so
a host can wire them in the wrong order and compose a skill the gate would have
refused (the README's pure-discovery quickstart is exactly that naive shape —
fine for listing, unsafe for activation). This module makes the ordering
STRUCTURAL: `select_skills_for_context` loads → hashes → trust-gates → returns
only the skills that may be composed, so a per-phase resolver (the entity
config object's visit/work/personal/sleep sections) calls one function and
cannot skip the gate.

Ordering enforced here (fail-closed):
1. load each named skill from the configured root(s) (vendored shelf, plus
   optional user roots — later valid copy wins) and inspect its tree
   (tree_hash + has_scripts — never frontmatter claims); the parsed
   SKILL.md bytes are cross-checked against the hashed tree's own digest
   (a swap between the two reads refuses the skill — the verdict must
   attest the bytes that get composed); any failure holds THAT skill as
   missing, never the whole selection;
2. resolve the skill's candidate SOURCES: the caller-supplied one (explicit,
   blank treated as absent) plus ALL registry-derived candidates at the
   winning binding strength (hash-bound = exact provenance for these bytes;
   name-bound = weaker claims about a prior tree, warned) — so a names-only
   context config (the per-phase ``skills:`` list) still matches
   name-anchored advisories;
3. evaluate_trust against EVERY candidate source and keep the WORST verdict
   (blocked > requires_review > attachable) with warnings unioned — neither a
   wrong caller string nor a losing registry record can evade an advisory;
4. BLOCKED → never active; attachable → active; requires_review → active ONLY
   if the operator explicitly enabled it for this context (bare name, or the
   durable ``name@tree_hash`` pin that attests bytes); otherwise held;
5. activation descriptions come from the record matching the CURRENT hash
   (a stale record for other bytes never overrides the prompt line).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Mapping

from abstractskill.errors import SkillError, SkillValidationError
from abstractskill.loader import FilesystemSkillLoader, WarningCallback, _warn
from abstractskill.models import SkillMetadata
from abstractskill.tree import inspect_skill_dir
from abstractskill.trust import TrustRegistry, TrustVerdict, evaluate_trust
from abstractskill.validation import SKILL_FILENAME, validate_skill_name

# A tree hash is always the full sha256 hex — a PREFIX pin would weaken the
# attestation to whatever collides in the prefix, so nothing shorter is a pin.
_TREE_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class SkillSelection:
    """The trust-gated outcome for one context (e.g. one entity phase).

    ``active`` is the ONLY set a host should compose into tools/prompt — it is
    attachable-or-operator-enabled and never blocked. ``held`` needs an
    operator decision; ``blocked`` must never be shown as available.

    ``resolved_paths``/``resolved_tree_hashes`` name the WINNING copy for
    every name that loaded and hashed cleanly (active, held, and blocked
    alike): the path says which copy an operator decision would apply to,
    the tree hash is the exact value to write into a hash-pinned enable
    (``name@hash``). Missing names have no attested copy and appear in
    neither mapping.
    """

    active: tuple[SkillMetadata, ...] = ()
    held: tuple[tuple[str, TrustVerdict], ...] = ()  # requires_review, not enabled
    blocked: tuple[tuple[str, TrustVerdict], ...] = ()
    # Not safely evaluable: unloadable from the shelf, OR refused because the
    # bytes could not be attested (load↔hash divergence). Automation must not
    # treat `missing` as "vendor it" — read the warning for the reason.
    missing: tuple[str, ...] = ()
    activation_descriptions: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    resolved_paths: Mapping[str, Path] = field(default_factory=dict)
    resolved_tree_hashes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Seal the Mapping fields (frozen blocks rebinding, not mutation):
        # resolved_tree_hashes is exactly what an operator copies into a
        # hash pin — a mutable view of it would be a corruptible authority.
        for name in ("activation_descriptions", "resolved_paths", "resolved_tree_hashes"):
            value = getattr(self, name)
            if not isinstance(value, MappingProxyType):
                object.__setattr__(self, name, MappingProxyType(dict(value)))

    @property
    def active_names(self) -> tuple[str, ...]:
        return tuple(meta.name for meta in self.active)


def _worse_verdict(a: TrustVerdict, b: TrustVerdict) -> TrustVerdict:
    """Pick the more restrictive of two verdicts (blocked > review > attachable).

    Used when the same bytes are checked under several candidate sources: the
    gate must honor whichever source an advisory matched. Ties keep ``a``
    (candidates are ordered caller-first, so ties keep the explicit source's
    reasons). Warnings are unioned by the caller, not here.
    """
    if a.blocked:
        return a
    if b.blocked:
        return b
    if a.requires_review or not b.requires_review:
        return a
    return b


def _has_name_anchored_advisory_for(registry: TrustRegistry, name: str) -> bool:
    """Whether an active hash-less advisory could match THIS name if a source
    were known — advisories for other names can never match it, so they must
    not trigger the no-source warning (warning noise trains operators to
    ignore #FALLBACK)."""
    return any(
        a.is_active and a.tree_hash is None and a.name == name
        for a in registry.advisories
    )


def _parse_enabled(
    entries: Iterable[str],
    note,
) -> tuple[set[str], dict[str, set[str]]]:
    """Split operator ``enabled`` entries into bare-name grants and hash pins.

    A pinned entry is ``name@<full sha256 tree hash>``: the grant attests
    BYTES, so a shadow copy under the same name can never ride a standing
    enable. Fail-closed parsing: a malformed entry (bad name, short/non-hex
    hash, stray ``@``) grants NOTHING — demoting it to a bare-name grant
    would silently widen exactly the surface the pin narrows. When a name
    has any pin, the pins GOVERN: a bare entry for the same name is ignored
    loudly (otherwise the pin is decorative). Names stay EXACT-match
    (case-normalizing a GRANT widens activation — the registry's
    match-widening rule applies to advisory/record matching, never to
    authorization); only the hex hash is case-normalized (presentation,
    not identity).
    """
    bare: set[str] = set()
    pins: dict[str, set[str]] = {}
    # Type-contract guards on the GRANT surface (fail-open risk class): a
    # host passing `enabled="review"` (the YAML scalar-vs-list slip) would
    # otherwise iterate CHARACTERS — each a silent one-letter grant; None
    # would crash the whole phase.
    if entries is None:
        entries = ()
    elif isinstance(entries, str):
        entries = (entries,)
    for entry in entries:
        if not isinstance(entry, str) or not entry.strip():
            note(f"#FALLBACK: malformed enabled entry {entry!r} ignored (no grant)")
            continue
        text = entry.strip()
        if "@" not in text:
            bare.add(text)
            continue
        name_part, _, hash_part = text.partition("@")
        hash_part = hash_part.strip().lower()
        try:
            pinned_name = validate_skill_name(name_part)
        except SkillValidationError as exc:
            note(f"#FALLBACK: malformed enabled pin {entry!r} ignored (no grant): {exc}")
            continue
        if not _TREE_HASH_RE.fullmatch(hash_part):
            note(
                f"#FALLBACK: malformed enabled pin {entry!r} ignored (no grant): "
                "the pin must be the full 64-hex sha256 tree hash"
            )
            continue
        pins.setdefault(pinned_name, set()).add(hash_part)
    for contradicted in sorted(bare & pins.keys()):
        note(
            f"#FALLBACK: enabled entries for skill {contradicted!r} mix a bare "
            "name with hash pin(s); the pins govern and the bare entry is "
            "ignored (a bare grant would make the pin decorative)"
        )
        bare.discard(contradicted)
    return bare, pins


def select_skills_for_context(
    registry: TrustRegistry,
    shelf_root: Path | str | list[Path | str],
    names: Iterable[str],
    *,
    sources: Mapping[str, str] | None = None,
    enabled: Iterable[str] = (),
    on_warning: WarningCallback | None = None,
) -> SkillSelection:
    """Resolve a context's named skills into a trust-gated selection.

    ``shelf_root`` is the home's vendored skill directory — or a LIST of
    roots (e.g. curated shelf + a user skills dir): precedence follows
    ``FilesystemSkillLoader`` (later VALID copy wins on name collision; a
    broken later copy falls back loudly to the earlier one), and the gate
    evaluates the WINNING copy's own bytes. A user-root skill shadowing a
    curated name never inherits the curated validation RECORD — its
    different tree hash matches no record, so it is UNVERIFIED and held —
    while byte-identical copies activate on the curated record regardless of
    root (trust binds to content, not location). The remaining name-bound
    surface is the ``enabled`` grant: a standing enable activates whatever
    requires_review copy wins precedence, so that activation is always
    LOUDLY noted with the winning path and hash, never silent. A shadow that
    parses but fails tree inspection holds the name as missing (the loader
    already committed to it) — a user-dir write can deny a curated skill,
    loudly, never substitute for it.
    ``names`` are the skills the context config activates. ``sources``
    optionally maps skill name -> source for name/source advisory matching;
    when the caller passes none (the names-only per-phase config), sources
    are DERIVED from the registry's validation records
    (``TrustRegistry.source_candidates_for``) — provenance lives with the
    vendored shelf's records, never in the phase config. ``enabled`` are the
    names the operator explicitly review-enabled for THIS context (a
    requires_review skill is active only if listed here; blocked is never
    active regardless). An entry may be HASH-PINNED as ``name@tree_hash``
    (full sha256): the grant then applies only when the winning copy's tree
    hash matches a pin — the durable form, since a bare name would activate
    whatever copy wins root precedence. Pins govern over a bare entry for
    the same name; a pin that matches no longer holds the skill with a loud
    note naming both hashes (re-pin deliberately after reviewing the new
    bytes — ``resolved_tree_hashes`` carries the value to pin). Pins never
    constrain ATTACHABLE skills: they lift review, they are not a second
    registry.
    """
    loader = FilesystemSkillLoader(shelf_root)
    sources = sources or {}

    active: list[SkillMetadata] = []
    held: list[tuple[str, TrustVerdict]] = []
    blocked: list[tuple[str, TrustVerdict]] = []
    missing: list[str] = []
    descriptions: dict[str, str] = {}
    warnings: list[str] = []
    resolved_paths: dict[str, Path] = {}
    resolved_hashes: dict[str, str] = {}

    def _note(msg: str) -> None:
        _warn(msg, on_warning)
        warnings.append(msg)

    enabled_bare, enabled_pins = _parse_enabled(enabled, _note)

    # A duplicated name in the context config is a config bug, not two
    # activations: process each name once (order preserved), loudly.
    requested = list(names)
    unique_names = list(dict.fromkeys(requested))
    if len(unique_names) != len(requested):
        dupes = sorted({n for n in unique_names if requested.count(n) > 1})
        _note(f"#FALLBACK: duplicate skill name(s) in context config ignored: {dupes}")

    for name in unique_names:
        try:
            loaded = loader.load(name, on_warning=on_warning)
            # Inside the same containment: a bad tree (symlink, file deleted
            # mid-hash) must hold THIS skill, never crash the whole phase's
            # selection — one bad apple cannot deny every other skill.
            # Deliberately NARROW (SkillError + filesystem races only): a
            # logic bug in loader/tree code must surface, not silently
            # demote every skill to "not loadable".
            inventory = inspect_skill_dir(loaded.root_dir)
        except (SkillError, OSError) as exc:
            missing.append(name)
            _note(f"#FALLBACK: skill {name!r} named for this context is not loadable: {exc}")
            continue

        # --- load→inspect byte cross-check (TOCTOU) -------------------------
        # The verdict below attests inventory.tree_hash, but the COMPOSED
        # document came from the loader's earlier read: on a user-writable
        # root, a swap between the two reads would activate bytes the gate
        # never evaluated. Compare the digest of the bytes actually parsed
        # against the same file's digest inside the hashed tree; any
        # divergence refuses THIS skill (re-run when the tree is stable —
        # persistent divergence means the root is being actively rewritten).
        hashed_skill_md = next(
            (r.sha256 for r in inventory.files if r.rel_path == SKILL_FILENAME), None
        )
        if loaded.skill_md_sha256 is not None and hashed_skill_md is None:
            # Distinct diagnosis: the hashed tree carries NO exact-case
            # SKILL.md entry (case-aliased `skill.md` opened by a
            # case-insensitive filesystem, or deleted mid-walk) — a
            # persistent state, not a race; the race wording would
            # misdirect the operator.
            missing.append(name)
            _note(
                f"#FALLBACK: skill {name!r} at {loaded.root_dir} has no "
                f"exact-case {SKILL_FILENAME} in its hashed tree (case-aliased "
                "filename on a case-insensitive filesystem, or deleted "
                "mid-inspection); refusing — the verdict cannot attest the "
                "parsed document"
            )
            continue
        if loaded.skill_md_sha256 is not None and loaded.skill_md_sha256 != hashed_skill_md:
            missing.append(name)
            _note(
                f"#FALLBACK: skill {name!r} at {loaded.root_dir} changed between "
                f"load and hash (parsed SKILL.md sha256 {loaded.skill_md_sha256[:16]}… "
                f"vs hashed {str(hashed_skill_md)[:16]}…); refusing this selection — "
                "re-run, and treat the root as compromised if it persists"
            )
            continue

        resolved_paths[name] = loaded.root_dir
        resolved_hashes[name] = inventory.tree_hash

        # --- candidate sources ---------------------------------------------
        # Explicit caller mapping first (blank/whitespace = absent, loudly);
        # then EVERY registry-derived candidate at the winning strength.
        # All candidates are advisory-checked below — a losing record's
        # source could be the one an advisory targets.
        explicit_source: str | None = None
        raw_source = sources.get(name)
        if raw_source is not None:
            # Type-contract guard: a non-string source (host bug) must demote
            # to derivation with a loud note, never crash the whole phase.
            if not isinstance(raw_source, str):
                _note(
                    f"#FALLBACK: non-string source supplied for skill {name!r} "
                    f"({type(raw_source).__name__}); treating as absent "
                    "(deriving from the registry instead)"
                )
            elif not raw_source.strip():
                _note(
                    f"#FALLBACK: blank source supplied for skill {name!r}; "
                    "treating as absent (deriving from the registry instead)"
                )
            else:
                explicit_source = raw_source.strip()

        derived = registry.source_candidates_for(name=name, tree_hash=inventory.tree_hash)
        check_sources: list[str] = []
        if explicit_source is not None:
            check_sources.append(explicit_source)
        for candidate in derived:
            if candidate.source not in check_sources:
                check_sources.append(candidate.source)

        if derived:
            derived_sources = {c.source for c in derived}
            if explicit_source is None and derived[0].binding == "name":
                _note(
                    f"#FALLBACK: source for skill {name!r} derived from name-bound "
                    f"validation record(s) ({sorted(derived_sources)}); these bytes "
                    "match no validated tree, so the provenance is a prior tree's claim"
                )
            if derived[0].ambiguous:
                _note(
                    f"#FALLBACK: registry records disagree on the source of skill "
                    f"{name!r} ({sorted(derived_sources)}); checking advisories "
                    "against every candidate"
                )
            if explicit_source is not None and explicit_source not in derived_sources:
                _note(
                    f"#FALLBACK: caller-supplied source {explicit_source!r} for skill "
                    f"{name!r} contradicts registry provenance ({sorted(derived_sources)}, "
                    f"{derived[0].binding}-bound); checking advisories against all of them"
                )
        if not check_sources and _has_name_anchored_advisory_for(registry, name):
            _note(
                f"#FALLBACK: no source for skill {name!r} (none supplied, none in the "
                "registry); name/source advisory matching is disabled for it "
                "(hash-anchored advisories still apply)"
            )

        # --- verdict: worst across every candidate source -------------------
        verdicts = [
            evaluate_trust(
                registry,
                tree_hash=inventory.tree_hash,
                name=name,
                source=candidate,
                has_scripts=inventory.has_scripts,
            )
            for candidate in (check_sources or [None])
        ]
        verdict = verdicts[0]
        for other in verdicts[1:]:
            verdict = _worse_verdict(verdict, other)
        # Union warnings from EVERY evaluated verdict (order-preserving,
        # deduped): the losing verdict's caveats must not vanish — and they
        # go through _note so on_warning/logging hosts see them too.
        for caveat in dict.fromkeys(w for v in verdicts for w in v.warnings):
            _note(caveat)

        if verdict.blocked:
            blocked.append((name, verdict))
            continue

        # --- operator enable grant ------------------------------------------
        # Hash pins govern when present: the grant applies only to the exact
        # tree the operator reviewed. A bare-name grant remains valid but is
        # the weaker form (name-bound while trust binds to bytes), so its
        # activation is loudly noted with the winning copy's path and hash.
        granted = False
        grant_pinned = False
        if verdict.requires_review:
            pin_set = enabled_pins.get(name)
            if pin_set is not None:
                if inventory.tree_hash in pin_set:
                    granted = True
                    grant_pinned = True
                else:
                    _note(
                        f"#FALLBACK: operator enable for skill {name!r} is pinned to "
                        f"tree(s) {sorted(p[:16] + '…' for p in pin_set)}, but the "
                        f"winning copy at {loaded.root_dir} has tree "
                        f"{inventory.tree_hash[:16]}…; the grant does not apply "
                        "(held — re-pin deliberately after reviewing the new bytes)"
                    )
            elif name in enabled_bare:
                granted = True

        if verdict.attachable or granted:
            if verdict.requires_review and grant_pinned:
                _note(
                    f"skill {name!r} activated by hash-pinned operator enable "
                    f"from {loaded.root_dir} (tree {inventory.tree_hash[:16]}…)"
                )
            elif verdict.requires_review:
                # The bare enable grant is name-bound while trust binds to
                # bytes: a standing enable would otherwise SILENTLY activate
                # whatever copy wins precedence (e.g. a user-root shadow of a
                # curated name). Name the winning copy so the swap is never
                # silent.
                _note(
                    f"skill {name!r} activated by operator enable with "
                    f"requires_review bytes from {loaded.root_dir} "
                    f"(tree {inventory.tree_hash[:16]}…)"
                )
            active.append(loaded.document.metadata)
            # Activation description from the record bound to THESE bytes only
            # (a stale record for other bytes must not override the prompt
            # line); ties resolve by highest trust level, the same
            # deterministic rule TrustRegistry.activation_descriptions uses.
            described = [
                r for r in registry.validations_for(inventory.tree_hash)
                if r.activation_description
            ]
            if described:
                best = max(described, key=lambda r: r.level.rank)
                descriptions[name] = best.activation_description or ""
            continue
        held.append((name, verdict))

    return SkillSelection(
        active=tuple(active),
        held=tuple(held),
        blocked=tuple(blocked),
        missing=tuple(missing),
        activation_descriptions=descriptions,
        warnings=tuple(warnings),
        resolved_paths=resolved_paths,
        resolved_tree_hashes=resolved_hashes,
    )
