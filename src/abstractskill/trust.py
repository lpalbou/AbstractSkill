"""Skill trust: validation records, do-not-use advisories, guidance, verdicts.

This module answers ONE question with ONE code path for every surface
(gateway console picker, runtime activation, operator browsing): "how much
should this exact skill be trusted, is it forbidden, and does it need review
before use?" The maintainer directive (2026-07-11) requires a system of
validated skills AND a notice of skills people should NOT use.

Design invariants:

- TRUST BINDS TO THE TREE HASH, never the name. A name is claimable; the bytes
  are not. A validation of hash H says nothing about hash H' — any byte change
  voids trust and demands re-validation. (See ``hash_skill_tree``.)
- ADVISORY WINS. A do-not-use advisory (critical/high severity, or any
  hash-matched specific advisory) forces a BLOCKED verdict regardless of any
  validation record — there is no silent override of a safety notice.
- SEVERITY IS GRADED, not binary. critical/high block; medium/low do not
  block but force review (the verdict says so). The advisory's stated meaning
  and the verdict never contradict each other.
- FAIL CLOSED. Only a positively-validated, advisory-free, script-free skill
  is ``attachable`` without a decision. UNVERIFIED, scripts-present, and
  low/medium advisories all set ``requires_review`` — a consumer reading only
  ``attachable`` never attaches an unvetted skill by accident.
- FOUR MANDATED FIELDS on every advisory (maintainer's a/b/c/d): official
  intent, hidden issue, severity, reference. Construction refuses loudly if
  any is missing.
- GUIDANCE ≠ ADVISORY. A category-level risk notice that names no specific
  skill is GUIDANCE (informational, never blocks a specific skill). Calling a
  class label a do-not-use advisory would be an inert notice masquerading as
  protection.
- EVERY VERDICT IS EXPLAINABLE: it names the records it rests on.
- The registry is data, not authority: this module INFORMS; consumers ENFORCE.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from abstractskill.errors import SkillValidationError

logger = logging.getLogger("abstractskill")

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class TrustLevel(str, Enum):
    """Ordered trust bands. Higher ordinal = more trusted.

    BLOCKED is separate from the ladder: it is a VERDICT an advisory forces,
    never a level a validation grants.
    """

    BLOCKED = "blocked"
    UNVERIFIED = "unverified"
    COMMUNITY = "community"
    ADOPTED = "adopted"  # externally authored, first-party reviewed (not audited).
    AUDITED = "audited"  # passed a behavioral/simulation audit or external audit.
    FIRST_PARTY = "first_party"  # authored and owned by the framework.

    @property
    def rank(self) -> int:
        return _TRUST_ORDER.index(self)


_TRUST_ORDER = [
    TrustLevel.BLOCKED,
    TrustLevel.UNVERIFIED,
    TrustLevel.COMMUNITY,
    TrustLevel.ADOPTED,
    TrustLevel.AUDITED,
    TrustLevel.FIRST_PARTY,
]

_GRANTABLE_LEVELS = frozenset(
    {TrustLevel.COMMUNITY, TrustLevel.ADOPTED, TrustLevel.AUDITED, TrustLevel.FIRST_PARTY}
)


class Severity(str, Enum):
    """Advisory severity, closed set with stated meanings the verdict honors."""

    CRITICAL = "critical"  # active exploit / data theft / hijack; hard block.
    HIGH = "high"  # serious latent risk; hard block.
    MEDIUM = "medium"  # meaningful concern; requires review before attaching.
    LOW = "low"  # minor / informational; requires review (a hash-matched
    #             advisory of ANY severity still hard-blocks — an exact-bytes
    #             match is specific enough to forbid regardless of severity).


# Which severities hard-block vs merely require review — the graded contract.
_BLOCKING_SEVERITIES = frozenset({Severity.CRITICAL, Severity.HIGH})


KNOWN_VALIDATION_METHODS = frozenset(
    {
        "first-party",  # authored and owned by the framework.
        "first-party-adoption",  # externally authored, first-party reviewed.
        "manual-review",  # a human read the whole tree.
        "simulated-execution",  # passed the epoch audit harness (backlog 0003).
        "external-audit",  # a named third party audited it (reference required).
    }
)

# The MAXIMUM trust level a method may grant. Prevents "reviewed, not audited"
# from claiming the top band (the first_party overclaim the adversary found).
_METHOD_MAX_LEVEL = {
    "first-party": TrustLevel.FIRST_PARTY,
    "external-audit": TrustLevel.AUDITED,
    "simulated-execution": TrustLevel.AUDITED,
    "manual-review": TrustLevel.ADOPTED,
    "first-party-adoption": TrustLevel.ADOPTED,
}


def _require_hash(value: str, *, what: str) -> str:
    text = value.strip().lower()
    if not _HASH_RE.fullmatch(text):
        raise SkillValidationError(
            f"{what} must be a 64-char lowercase hex sha256 (got {value!r})"
        )
    return text


def _require_nonempty(value: Any, *, field_name: str, owner: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise SkillValidationError(f"{owner} requires a non-empty {field_name!r}")
    return text


@dataclass(frozen=True, slots=True)
class ValidationRecord:
    """One attestation that a specific skill tree earned a trust level.

    ``tree_hash`` binds the record to exact bytes (``hash_skill_tree``). The
    record is meaningless for any other hash. ``activation_description`` is an
    optional host-side override for the skill's activation trigger without
    mutating the vendored tree (used when a vendored skill's own description
    names a foreign product).
    """

    name: str
    source: str
    tree_hash: str
    level: TrustLevel
    method: str
    validated_by: str
    validated_at: str
    evidence: Mapping[str, Any] = field(default_factory=dict)
    notes: str | None = None
    activation_description: str | None = None

    def __post_init__(self) -> None:
        # Write back the STRIPPED, case-normalized name and STRIPPED source:
        # advisory matching is exact string equality, so stray whitespace (a
        # quoted YAML scalar) or a case typo ('Evil') would otherwise silently
        # void a match — the same normalize-once rule the tree_hash follows.
        # Names lowercase because the Agent Skills spec requires lowercase
        # skill names (SKILL_NAME_RE): an uppercase registry name can never
        # match a loadable skill. Sources keep their case (display fidelity;
        # lint_registry catches case-only near-misses).
        object.__setattr__(
            self,
            "name",
            _require_nonempty(self.name, field_name="name", owner="ValidationRecord").lower(),
        )
        object.__setattr__(
            self, "source", _require_nonempty(self.source, field_name="source", owner="ValidationRecord")
        )
        _require_nonempty(self.validated_by, field_name="validated_by", owner="ValidationRecord")
        _require_nonempty(self.validated_at, field_name="validated_at", owner="ValidationRecord")
        object.__setattr__(self, "tree_hash", _require_hash(self.tree_hash, what="ValidationRecord.tree_hash"))
        if self.level not in _GRANTABLE_LEVELS:
            raise SkillValidationError(
                f"ValidationRecord cannot grant {self.level.value!r}; grantable "
                f"levels are {sorted(l.value for l in _GRANTABLE_LEVELS)}"
            )
        if self.method not in KNOWN_VALIDATION_METHODS:
            raise SkillValidationError(
                f"unknown validation method {self.method!r}; known methods are "
                f"{sorted(KNOWN_VALIDATION_METHODS)}"
            )
        max_level = _METHOD_MAX_LEVEL[self.method]
        if self.level.rank > max_level.rank:
            raise SkillValidationError(
                f"method {self.method!r} may grant at most {max_level.value!r}, "
                f"not {self.level.value!r} (reviewed is not audited)"
            )
        if self.method == "simulated-execution":
            ev = self.evidence or {}
            epochs = ev.get("epochs")
            models = ev.get("models")
            # bool is a subclass of int; True must not pass as an epoch count.
            if isinstance(epochs, bool) or not isinstance(epochs, int) or epochs < 1:
                raise SkillValidationError(
                    "simulated-execution requires evidence['epochs'] as a positive int (see backlog 0003)"
                )
            if not isinstance(models, (list, tuple)) or len(models) < 1:
                raise SkillValidationError(
                    "simulated-execution requires evidence['models'] as a non-empty list"
                )
        if self.method == "external-audit" and not (self.evidence or {}).get("reference"):
            raise SkillValidationError(
                "external-audit ValidationRecord requires evidence['reference'] (a source URL)"
            )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "source": self.source,
            "tree_hash": self.tree_hash,
            "level": self.level.value,
            "method": self.method,
            "validated_by": self.validated_by,
            "validated_at": self.validated_at,
        }
        if self.evidence:
            payload["evidence"] = dict(self.evidence)
        if self.notes:
            payload["notes"] = self.notes
        if self.activation_description:
            payload["activation_description"] = self.activation_description
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ValidationRecord":
        if not isinstance(data, Mapping):
            raise SkillValidationError(f"validation entry must be a mapping, got {type(data).__name__}")
        try:
            level = TrustLevel(str(data["level"]))
        except (ValueError, KeyError) as exc:
            raise SkillValidationError(f"invalid/absent validation level: {data.get('level')!r}") from exc
        missing = [k for k in ("name", "source", "tree_hash", "method", "validated_by", "validated_at") if k not in data]
        if missing:
            raise SkillValidationError(f"ValidationRecord missing fields: {missing}")
        raw_evidence = data.get("evidence", {})
        if not isinstance(raw_evidence, Mapping):
            raise SkillValidationError(
                f"ValidationRecord.evidence must be a mapping, got {type(raw_evidence).__name__}"
            )
        return cls(
            name=str(data["name"]),
            source=str(data["source"]),
            tree_hash=str(data["tree_hash"]),
            level=level,
            method=str(data["method"]),
            validated_by=str(data["validated_by"]),
            validated_at=str(data["validated_at"]),
            evidence=dict(raw_evidence),
            notes=(str(data["notes"]) if data.get("notes") is not None else None),
            activation_description=(
                str(data["activation_description"]) if data.get("activation_description") else None
            ),
        )


@dataclass(frozen=True, slots=True)
class AdvisoryEntry:
    """A do-not-use notice for a SPECIFIC skill, with four mandated fields.

    (a) official_intent, (b) hidden_issue, (c) severity, (d) reference.
    Identification prefers ``tree_hash`` (exact); ``name``+``source`` is the
    weaker fallback when the malicious bytes vary or are unknown. For
    CATEGORY-level risk notices that name no specific skill, use
    ``GuidanceEntry`` — an advisory must be able to match a real skill.

    MATCHING SEMANTICS: ``name`` is matched case-insensitively (normalized to
    the Agent Skills spec's lowercase at construction and at every query
    boundary — an uppercase spelling can never match a loadable skill, so
    case is noise, not signal). ``source`` is EXACT string equality
    (case-sensitive) after whitespace stripping: an advisory author must
    reproduce the registry's source spelling byte-exactly (e.g.
    ``codex-skills (maintainer)``) — ``lint_registry`` flags case-only
    near-misses and unknown sources at refresh time. Prefer undecorated
    source identifiers going forward.
    """

    name: str
    source: str
    official_intent: str  # (a)
    hidden_issue: str  # (b)
    severity: Severity  # (c)
    reference: str  # (d)
    tree_hash: str | None = None
    advisory_id: str | None = None
    discovered_at: str | None = None
    status: str = "active"  # active | withdrawn
    withdrawn_reason: str | None = None
    withdrawn_at: str | None = None

    def __post_init__(self) -> None:
        _require_nonempty(self.official_intent, field_name="official_intent", owner="AdvisoryEntry")
        _require_nonempty(self.hidden_issue, field_name="hidden_issue", owner="AdvisoryEntry")
        _require_nonempty(self.reference, field_name="reference", owner="AdvisoryEntry")
        # Stripped + case-normalized write-back: matching is exact string
        # equality on (name, source); whitespace from a quoted YAML scalar or
        # a case typo ('Evil' vs the spec-lowercase 'evil') must never
        # silently void a safety notice. Sources keep their case
        # (lint_registry catches case-only near-misses).
        object.__setattr__(
            self,
            "name",
            _require_nonempty(self.name, field_name="name", owner="AdvisoryEntry").lower(),
        )
        object.__setattr__(
            self, "source", _require_nonempty(self.source, field_name="source", owner="AdvisoryEntry")
        )
        if not isinstance(self.severity, Severity):
            raise SkillValidationError("AdvisoryEntry.severity must be a Severity")
        if self.tree_hash is not None:
            object.__setattr__(self, "tree_hash", _require_hash(self.tree_hash, what="AdvisoryEntry.tree_hash"))
        if self.status not in ("active", "withdrawn"):
            raise SkillValidationError("AdvisoryEntry.status must be 'active' or 'withdrawn'")
        if self.status == "withdrawn" and not (self.withdrawn_reason or "").strip():
            raise SkillValidationError("a withdrawn advisory must carry withdrawn_reason")

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def blocks(self) -> bool:
        """Whether this advisory hard-blocks (critical/high) vs requires review."""
        return self.severity in _BLOCKING_SEVERITIES

    def matches(self, *, tree_hash: str | None, name: str | None, source: str | None) -> str | None:
        """Return match strength ('hash' | 'name') or None.

        Hash and name inputs are normalized here (lowercase) so every public
        path matches symmetrically — stored fields are already normalized at
        construction. Source stays case-sensitive (documented policy;
        ``lint_registry`` catches case-only near-misses).
        """
        if self.tree_hash and tree_hash and self.tree_hash == tree_hash.strip().lower():
            return "hash"
        # Source is case-sensitive but stripped: stored sources are stripped
        # at construction, so stripping the query can only turn a guaranteed
        # miss into a match — widening the advisory surface (fail-closed).
        if (
            name is not None
            and self.name == name.strip().lower()
            and source is not None
            and self.source == source.strip()
        ):
            return "name"
        return None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "source": self.source,
            "official_intent": self.official_intent,
            "hidden_issue": self.hidden_issue,
            "severity": self.severity.value,
            "reference": self.reference,
            "status": self.status,
        }
        for key in ("tree_hash", "advisory_id", "discovered_at", "withdrawn_reason", "withdrawn_at"):
            value = getattr(self, key)
            if value:
                payload[key] = value
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AdvisoryEntry":
        if not isinstance(data, Mapping):
            raise SkillValidationError(f"advisory entry must be a mapping, got {type(data).__name__}")
        missing = [
            k for k in ("name", "source", "official_intent", "hidden_issue", "severity", "reference")
            if k not in data or not str(data.get(k, "")).strip()
        ]
        if missing:
            raise SkillValidationError(
                f"AdvisoryEntry missing mandated field(s): {missing} "
                "(official_intent, hidden_issue, severity, reference are required)"
            )
        try:
            severity = Severity(str(data["severity"]))
        except ValueError as exc:
            raise SkillValidationError(
                f"invalid advisory severity {data.get('severity')!r}; "
                f"must be one of {[s.value for s in Severity]}"
            ) from exc
        return cls(
            name=str(data["name"]),
            source=str(data["source"]),
            official_intent=str(data["official_intent"]),
            hidden_issue=str(data["hidden_issue"]),
            severity=severity,
            reference=str(data["reference"]),
            tree_hash=(str(data["tree_hash"]) if data.get("tree_hash") else None),
            advisory_id=(str(data["advisory_id"]) if data.get("advisory_id") else None),
            discovered_at=(str(data["discovered_at"]) if data.get("discovered_at") else None),
            status=str(data.get("status", "active")),
            withdrawn_reason=(str(data["withdrawn_reason"]) if data.get("withdrawn_reason") else None),
            withdrawn_at=(str(data["withdrawn_at"]) if data.get("withdrawn_at") else None),
        )


@dataclass(frozen=True, slots=True)
class GuidanceEntry:
    """A CATEGORY-level risk notice that names no specific skill.

    Guidance informs a picker/operator ("here is an ecosystem risk class and
    what to check") but never produces a BLOCKED verdict on a specific skill —
    a class label cannot honestly forbid an individual skill. Same four
    explanatory fields so the notice is actionable.
    """

    guidance_id: str
    title: str
    risk_class: str
    detail: str
    severity: Severity
    reference: str

    def __post_init__(self) -> None:
        for label in ("guidance_id", "title", "risk_class", "detail", "reference"):
            _require_nonempty(getattr(self, label), field_name=label, owner="GuidanceEntry")
        if not isinstance(self.severity, Severity):
            raise SkillValidationError("GuidanceEntry.severity must be a Severity")

    def to_dict(self) -> dict[str, Any]:
        return {
            "guidance_id": self.guidance_id,
            "title": self.title,
            "risk_class": self.risk_class,
            "detail": self.detail,
            "severity": self.severity.value,
            "reference": self.reference,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GuidanceEntry":
        if not isinstance(data, Mapping):
            raise SkillValidationError(f"guidance entry must be a mapping, got {type(data).__name__}")
        try:
            severity = Severity(str(data["severity"]))
        except (ValueError, KeyError) as exc:
            raise SkillValidationError(f"invalid/absent guidance severity: {data.get('severity')!r}") from exc
        return cls(
            guidance_id=str(data.get("guidance_id", "")),
            title=str(data.get("title", "")),
            risk_class=str(data.get("risk_class", "")),
            detail=str(data.get("detail", "")),
            severity=severity,
            reference=str(data.get("reference", "")),
        )


@dataclass(frozen=True, slots=True)
class DerivedSource:
    """A skill source derived from the registry's validation records.

    ``binding`` says how strong the provenance is: ``"hash"`` means a record
    attests THESE exact bytes came from ``source``; ``"name"`` means only a
    record for the same name (other bytes) carries it — a claim about a
    previous tree, usable for advisory matching but weaker (callers should
    warn). ``ambiguous`` is True when candidate records of the same binding
    strength disagree on the source (the returned one is the deterministic
    highest-trust pick).
    """

    source: str
    binding: str  # "hash" | "name"
    ambiguous: bool = False


@dataclass(frozen=True, slots=True)
class TrustVerdict:
    """The explainable outcome of evaluate_trust.

    Three orthogonal booleans, fail-closed. THE SAFE SINGLE READ IS
    ``attachable`` — never branch on ``requires_review`` alone, because a
    BLOCKED verdict has ``requires_review == False`` (blocked is a harder
    state than review), so ``if requires_review: gate; else: activate`` would
    ACTIVATE a blocked skill. Use ``attachable`` for the green path, and
    ``blocked`` for the hard stop; ``requires_review`` only distinguishes
    "operator may enable" from "blocked" once you already know it is not
    attachable. Prefer ``select_skills_for_context`` so this ordering is a
    function, not a per-host convention.

    - ``blocked``: never attach, never enable (a blocking advisory matched).
    - ``requires_review``: not attachable, but an operator MAY enable
      (unverified, scripts present, or a low/medium advisory).
    - ``attachable``: green path only — positively validated, no advisory, no
      scripts.
    """

    level: TrustLevel
    blocked: bool
    requires_review: bool
    reasons: tuple[str, ...]
    advisories: tuple[AdvisoryEntry, ...] = ()
    validation: ValidationRecord | None = None
    warnings: tuple[str, ...] = ()

    @property
    def attachable(self) -> bool:
        return (not self.blocked) and (not self.requires_review)

    @property
    def do_not_use(self) -> bool:
        return self.blocked


class TrustRegistry:
    """A loadable set of validation records, advisories, and guidance.

    Files are human-readable YAML, diffable, network-free.
    """

    def __init__(
        self,
        validations: Iterable[ValidationRecord] = (),
        advisories: Iterable[AdvisoryEntry] = (),
        guidance: Iterable[GuidanceEntry] = (),
    ) -> None:
        self._validations = list(validations)
        self._advisories = list(advisories)
        self._guidance = list(guidance)
        self._check_duplicate_ids("advisory_id", (a.advisory_id for a in self._advisories))
        self._check_duplicate_ids("guidance_id", (g.guidance_id for g in self._guidance))

    @staticmethod
    def _check_duplicate_ids(label: str, ids: Iterable[str | None]) -> None:
        seen: set[str] = set()
        for identifier in ids:
            if not identifier:
                continue
            if identifier in seen:
                raise SkillValidationError(f"duplicate {label} in registry: {identifier!r}")
            seen.add(identifier)

    @property
    def validations(self) -> tuple[ValidationRecord, ...]:
        return tuple(self._validations)

    @property
    def advisories(self) -> tuple[AdvisoryEntry, ...]:
        return tuple(self._advisories)

    @property
    def guidance(self) -> tuple[GuidanceEntry, ...]:
        return tuple(self._guidance)

    @classmethod
    def load(
        cls,
        validations_path: Path | str | None = None,
        advisories_path: Path | str | None = None,
        guidance_path: Path | str | None = None,
    ) -> "TrustRegistry":
        validations: list[ValidationRecord] = []
        advisories: list[AdvisoryEntry] = []
        guidance: list[GuidanceEntry] = []
        if validations_path is not None:
            validations = [ValidationRecord.from_dict(d) for d in _load_entries(Path(validations_path), "validations")]
        if advisories_path is not None:
            advisories = [AdvisoryEntry.from_dict(d) for d in _load_entries(Path(advisories_path), "advisories")]
        if guidance_path is not None:
            guidance = [GuidanceEntry.from_dict(d) for d in _load_entries(Path(guidance_path), "guidance")]
        return cls(validations=validations, advisories=advisories, guidance=guidance)

    def active_advisories_for(self, *, tree_hash: str | None, name: str | None, source: str | None) -> list[tuple[AdvisoryEntry, str]]:
        hits: list[tuple[AdvisoryEntry, str]] = []
        for advisory in self._advisories:
            if not advisory.is_active:
                continue
            strength = advisory.matches(tree_hash=tree_hash, name=name, source=source)
            if strength is not None:
                hits.append((advisory, strength))
        return hits

    def validations_for(self, tree_hash: str) -> list[ValidationRecord]:
        return [record for record in self._validations if record.tree_hash == tree_hash.strip().lower()]

    def source_candidates_for(self, *, name: str, tree_hash: str | None = None) -> tuple[DerivedSource, ...]:
        """ALL registry-derived provenance candidates for a skill, strongest first.

        This is what lets a names-only context config (the per-phase
        ``skills:`` list) still match NAME-ANCHORED advisories: the phase
        config names the skill, the registry carries who it came from.

        Records bound to ``tree_hash`` (exact — they attest THESE bytes)
        supersede records bound only to ``name`` (claims about previous
        trees): a re-vendored, re-validated tree is not haunted by its name's
        past sources. But within the winning strength EVERY distinct source
        is a candidate — a gate must check advisories against all provenance
        claims about these bytes, never a single winner (a losing record's
        source could be the one an advisory targets). Ordering within a
        strength: records naming THIS skill first, then highest trust level
        (deterministic). ``ambiguous`` is set on every candidate when the
        winning strength carries more than one distinct source.
        """
        # Query-side name normalization, symmetric with record construction
        # (records store spec-lowercase names).
        name = name.strip().lower()
        hash_bound: list[ValidationRecord] = []
        if tree_hash:
            hash_bound = self.validations_for(tree_hash)
        if hash_bound:
            # Same bytes may be vendored under another shelf name; the bytes'
            # provenance still applies. Prefer the record naming THIS skill.
            ranked = sorted(
                hash_bound,
                key=lambda r: (r.name == name, r.level.rank),
                reverse=True,
            )
            binding = "hash"
        else:
            ranked = sorted(
                (r for r in self._validations if r.name == name),
                key=lambda r: r.level.rank,
                reverse=True,
            )
            binding = "name"
        ordered_sources = list(dict.fromkeys(r.source for r in ranked))
        ambiguous = len(ordered_sources) > 1
        return tuple(
            DerivedSource(source=source, binding=binding, ambiguous=ambiguous)
            for source in ordered_sources
        )

    def source_for(self, *, name: str, tree_hash: str | None = None) -> DerivedSource | None:
        """The PRIMARY (display) provenance for a skill, or None.

        Convenience for rendering (a picker cell's provenance line). Gate
        paths must not stop here: ``select_skills_for_context`` checks
        advisories against ALL of ``source_candidates_for`` — the primary
        pick alone could dodge an advisory a losing candidate matches.
        """
        candidates = self.source_candidates_for(name=name, tree_hash=tree_hash)
        return candidates[0] if candidates else None

    def activation_descriptions(self) -> dict[str, str]:
        """Per-name activation-description overrides from validation records.

        The catalog/prompt layer passes this to ``format_available_skills_xml``
        so a vendored skill whose own description names a foreign product
        activates on framework-appropriate text (the tree stays byte-verbatim;
        only the prompt-facing line is overridden). If two records for the same
        name disagree, the higher trust level wins (deterministic).

        NOTE: this map is registry-wide and NOT hash-filtered — a record for
        other bytes contributes. When composing from a trust-gated selection,
        prefer ``SkillSelection.activation_descriptions`` (current-hash only).
        """
        best: dict[str, ValidationRecord] = {}
        for record in self._validations:
            if not record.activation_description:
                continue
            current = best.get(record.name)
            if current is None or record.level.rank > current.level.rank:
                best[record.name] = record
        return {name: r.activation_description for name, r in best.items() if r.activation_description}


def evaluate_trust(
    registry: TrustRegistry,
    *,
    tree_hash: str | None,
    name: str | None = None,
    source: str | None = None,
    has_scripts: bool = False,
) -> TrustVerdict:
    """Compute an explainable, fail-closed trust verdict for one skill.

    Precedence:
    1. A blocking advisory (critical/high, or any hash-matched active advisory)
       forces BLOCKED — safety wins, always.
    2. Otherwise the strongest validation bound to ``tree_hash`` sets the level.
    3. Non-blocking advisories (low/medium) and ``has_scripts`` set
       ``requires_review`` with warnings.
    4. An unvalidated skill is UNVERIFIED and requires_review (fail closed).

    ``has_scripts`` is the structural fact from ``inspect_skill_dir`` — a
    scripts-bearing skill always needs a human decision (bundled scripts carry
    a ~2.12x higher measured vulnerability rate; see the guidance registry).
    """
    # Normalize the hash AND the name ONCE, up front: the advisory match and
    # the validation lookup must see the same bytes, or a case difference
    # could pass one and fail the other (an uppercase-hex query bypassing an
    # advisory block while keeping its validation — the "advisory wins"
    # invariant must hold for every spelling of the same hash). Names are
    # spec-lowercase; records/advisories normalize at construction, so the
    # query side normalizes symmetrically.
    if tree_hash is not None:
        tree_hash = tree_hash.strip().lower()
    if name is not None:
        name = name.strip().lower()
    if source is not None:
        source = source.strip()

    reasons: list[str] = []
    warnings: list[str] = []
    requires_review = False

    advisory_hits = registry.active_advisories_for(tree_hash=tree_hash, name=name, source=source)
    matched = tuple(a for a, _ in advisory_hits)
    blocking = [(a, s) for a, s in advisory_hits if a.blocks or s == "hash"]
    nonblocking = [(a, s) for a, s in advisory_hits if not (a.blocks or s == "hash")]

    if blocking:
        for advisory, strength in blocking:
            note = "hash match" if strength == "hash" else "name/source match"
            reasons.append(f"blocked: {advisory.severity.value} advisory ({note}) — {advisory.hidden_issue}")
            if strength == "name":
                warnings.append(f"advisory matched by name/source only (hash unverified) — {advisory.hidden_issue}")
        return TrustVerdict(
            level=TrustLevel.BLOCKED,
            blocked=True,
            requires_review=False,
            reasons=tuple(reasons),
            advisories=matched,
            warnings=tuple(warnings),
        )

    # No blocking advisory. Determine the positive level from validations.
    validation: ValidationRecord | None = None
    if tree_hash:
        candidates = registry.validations_for(tree_hash)
        if candidates:
            validation = max(candidates, key=lambda r: r.level.rank)

    if validation is not None:
        level = validation.level
        reasons.append(
            f"{level.value} via {validation.method} by {validation.validated_by} ({validation.validated_at})"
        )
    else:
        level = TrustLevel.UNVERIFIED
        requires_review = True
        if not tree_hash:
            warnings.append("no tree_hash supplied; trust cannot bind to bytes")
        reasons.append("unverified: no validation record for this tree hash — review before use")

    for advisory, strength in nonblocking:
        requires_review = True
        reasons.append(f"review: {advisory.severity.value} advisory — {advisory.hidden_issue}")
        if strength == "name":
            warnings.append(f"advisory matched by name/source only (hash unverified) — {advisory.hidden_issue}")

    if has_scripts:
        requires_review = True
        reasons.append("review: skill bundles scripts (requires enablement; elevated vulnerability rate)")

    return TrustVerdict(
        level=level,
        blocked=False,
        requires_review=requires_review,
        reasons=tuple(reasons),
        advisories=matched,
        validation=validation,
        warnings=tuple(warnings),
    )


def lint_registry(registry: TrustRegistry) -> tuple[str, ...]:
    """Curator lint: surface registry entries that can never protect anyone.

    Matching is exact string equality, so an advisory whose spelling drifts
    from reality is INERT — a notice masquerading as protection (the first
    adversary pass found this class for guidance labels; this lint catches
    the per-entry spellings). Warnings, never refusals: an advisory may
    legitimately name a skill/source we have never validated (a marketplace
    warning), so only the curator can judge — the lint makes the judgment
    happen at refresh time instead of at incident time.

    Checks:
    - validation sources that differ only by case (a registry smell even with
      zero advisories — source matching is case-sensitive);
    - an advisory name that violates the Agent Skills name spec (incl. the
      64-char cap) can never match a loadable skill (hash-anchored entries
      get the honest wording: name-fallback dead, hash anchor still live);
    - a name-anchored advisory (no tree_hash) whose source matches no
      validation source — possibly a foreign marketplace (fine), possibly a
      typo of a known source (inert);
    - a source that matches a known validation source only case-insensitively
      — almost certainly a typo (sources are matched case-sensitively);
    - a registry with name-anchored advisories but NO validations gets one
      aggregate note (advisories-only feed), never per-entry noise.
    Active advisories only; withdrawn entries are history.
    """
    from abstractskill.validation import MAX_NAME_LENGTH, SKILL_NAME_RE

    warnings: list[str] = []
    known_sources = sorted({record.source for record in registry.validations})
    # Fold case-insensitively, keeping ALL twins (sorted, deterministic): two
    # validation sources differing only by case are themselves a registry
    # smell worth naming completely — an arbitrary single twin could send a
    # curator "fixing" toward the wrong spelling.
    known_sources_folded: dict[str, list[str]] = {}
    for source in known_sources:
        known_sources_folded.setdefault(source.lower(), []).append(source)
    for folded, twins in known_sources_folded.items():
        if len(twins) > 1:
            warnings.append(
                f"lint: validation sources {twins} differ only by case — source "
                "matching is case-sensitive; converge on one spelling"
            )

    name_anchored_seen = False
    for advisory in registry.advisories:
        if not advisory.is_active:
            continue
        label = advisory.advisory_id or advisory.name
        name_spec_ok = (
            SKILL_NAME_RE.fullmatch(advisory.name) is not None
            and len(advisory.name) <= MAX_NAME_LENGTH
        )
        if not name_spec_ok:
            if advisory.tree_hash is not None:
                warnings.append(
                    f"lint: advisory {label!r} names {advisory.name!r}, which violates "
                    "the skill-name spec (lowercase a-z/0-9/hyphens, max 64 chars) — "
                    "the name-fallback match path is dead; the hash anchor still matches"
                )
            else:
                warnings.append(
                    f"lint: advisory {label!r} names {advisory.name!r}, which violates "
                    "the skill-name spec (lowercase a-z/0-9/hyphens, max 64 chars) and "
                    "can never match a loadable skill — verify the spelling"
                )
        if advisory.tree_hash is not None:
            continue  # hash-anchored: the hash is the match key; source is context.
        name_anchored_seen = True
        if not known_sources:
            continue  # aggregate line below; per-entry noise carries nothing.
        if advisory.source in known_sources:
            continue
        twins = known_sources_folded.get(advisory.source.lower())
        if twins:
            warnings.append(
                f"lint: advisory {label!r} source {advisory.source!r} matches known "
                f"validation source(s) {twins} only by case — source matching is "
                "case-sensitive, so this advisory will never match; fix the spelling"
            )
        else:
            warnings.append(
                f"lint: advisory {label!r} is name-anchored on source {advisory.source!r}, "
                "which matches no known validation source — legitimate for a foreign "
                "marketplace, but if this skill is expected on a local shelf, verify "
                "the source spelling byte-exactly against the shelf's validation records"
            )

    if name_anchored_seen and not known_sources:
        warnings.append(
            "lint: registry has no validation records; name-anchored advisory source "
            "spellings cannot be cross-checked (advisories-only feed — expected if "
            "validations live elsewhere)"
        )
    return tuple(warnings)


def _load_entries(path: Path, key: str) -> list[Mapping[str, Any]]:
    if not path.is_file():
        raise SkillValidationError(f"trust registry file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise SkillValidationError(f"invalid trust registry YAML at {path}: {exc}") from exc
    if not isinstance(data, Mapping):
        raise SkillValidationError(f"trust registry {path} must be a mapping with a {key!r} list")
    if key not in data:
        # A registry file that does not declare the requested key is almost
        # always a swapped path (loading advisories from a validations file)
        # or a truncated/empty file — warn loudly rather than silently return
        # zero protection. A file that legitimately declares `key: []` does
        # NOT warn (the key is present).
        logger.warning(
            "#FALLBACK: trust registry %s has no %r key (keys: %s); returning zero entries",
            path, key, sorted(data.keys()) if data else "<empty file>",
        )
    entries = data.get(key, [])
    if not isinstance(entries, list):
        raise SkillValidationError(f"trust registry {path}: {key!r} must be a list")
    return entries
