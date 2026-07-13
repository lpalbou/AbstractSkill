"""Curated skill catalog: the ONE admissible source list for vendoring.

The 2026 skill ecosystem's measured risk (Snyk ToxicSkills: 36.8% of 3,984
skills flawed, 13.4% critical; the AIR post-approval URL-swap incident that
reached ~26k agents) rules out marketplace-style installs. AbstractSkill's
install path is therefore CURATED-ONLY: a skill may be vendored onto the
shelf only if a reviewed catalog entry names it, pins its upstream commit,
and (after first vendoring) pins its whole-tree hash. The catalog is data;
this module is its validation contract. It is NETWORK-FREE like the rest of
the library — fetching lives in ``scripts/vendor_skill.py``, never here.

Invariants:
- ENTRIES ARE PINNED: ``upstream_ref`` must be a 40-hex commit SHA (tags and
  branches move; a SHA is immutable). ``expected_tree_hash`` is filled by the
  first vendoring (trust-on-first-vendor, human diff review) and verified on
  every re-vendor — an upstream force-push cannot silently change bytes.
- NAMES ARE SPEC NAMES: the catalog name is the shelf directory name and must
  satisfy the Agent Skills name spec (it is also the trust-registry key).
- RISK IS DECLARED, NOT INFERRED: ``archetype``/``risk`` are the curator's
  reviewed classification; the structural facts (has_scripts) still win at
  trust time — a "knowledge" entry that ships scripts gets requires_review
  from the gate regardless of what the catalog claims.
- THE CATALOG NEVER GRANTS TRUST: vendoring a catalog entry mints at most a
  ``manual-review``/``adopted`` validation (method caps the level); the
  honest-limits contract stands — curation raises the bar, it certifies
  nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from abstractskill.errors import SkillValidationError
from abstractskill.validation import validate_skill_name

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_TREE_HASH_RE = re.compile(r"^[0-9a-f]{64}$")

# Closed sets: a curator writing anything else gets a loud refusal, never a
# silently-ignored classification. Risk is "low", never "safe" — the
# honest-limits rule (never render the word "safe") applies to every
# operator-facing surface, and --list/doc tables render this field.
ARCHETYPES = frozenset({"knowledge", "procedure", "meta"})
RISK_LEVELS = frozenset({"low", "moderate", "risky"})

# Upstream sources must be well-formed "owner/repo" GitHub-style slugs; the
# vendor script derives the clone URL from this, so the catalog can never
# smuggle an arbitrary URL (curated-only is structural, not convention).
# Segments must START alphanumeric: flag-shaped ("-o") and dot-relative
# ("..", ".x") segments are refused at the contract, so argv/URL safety never
# rests on how a downstream consumer happens to wrap the slug.
_REPO_SLUG_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$"
)

# Licenses that do not clearly permit redistribution of byte copies are
# REFUSED at the contract (vendoring copies bytes into our tree).
_REFUSED_LICENSES = frozenset({"source-available", "unknown", "none", "unlicensed", "proprietary"})

# Subdirectory paths inside the upstream repo: relative, no traversal.
_SUBDIR_BAD = re.compile(r"(^/)|(^\.\.(/|$))|(/\.\.(/|$))|(\\)")


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """One curated, pinned, vendor-able skill.

    ``vendored`` + ``expected_tree_hash`` describe the shelf state: an entry
    with a hash is verifiable on re-vendor; an entry without one has never
    been vendored (the first vendor fills it and the diff gets human review).
    """

    name: str  # shelf/spec name (also the trust-registry key)
    source: str  # provenance label used in validation records (e.g. "vercel-labs/agent-skills")
    repo: str  # owner/repo slug the vendor script clones
    upstream_ref: str  # 40-hex commit SHA (immutable pin)
    subdir: str  # path of the skill dir inside the repo at that ref
    license: str  # upstream license (SPDX-ish label; "source-available" refused)
    archetype: str  # knowledge | procedure | meta
    risk: str  # safe | moderate | risky (curator's reviewed classification)
    improves: str  # what this adds to OUR framework (the curation rationale)
    activation_description: str | None = None  # framework-appropriate prompt line
    expected_tree_hash: str | None = None  # whole-tree hash after first vendoring
    vendored: bool = False
    evidence: tuple[str, ...] = ()  # reference URLs supporting the curation claims
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", validate_skill_name(self.name))
        for label in ("source", "repo", "upstream_ref", "subdir", "license", "improves"):
            value = str(getattr(self, label) or "").strip()
            if not value:
                raise SkillValidationError(f"catalog entry {self.name!r} requires non-empty {label!r}")
            object.__setattr__(self, label, value)
        if not _REPO_SLUG_RE.fullmatch(self.repo) or ".." in self.repo:
            raise SkillValidationError(
                f"catalog entry {self.name!r}: repo must be an owner/repo slug with "
                f"alphanumeric-leading segments, got {self.repo!r}"
            )
        if self.license.strip().lower() in _REFUSED_LICENSES or "source-available" in self.license.lower():
            raise SkillValidationError(
                f"catalog entry {self.name!r}: license {self.license!r} does not clearly "
                "permit redistribution — vendoring copies bytes; a catalog entry needs a "
                "redistribution-permitting license"
            )
        if not _SHA_RE.fullmatch(self.upstream_ref):
            raise SkillValidationError(
                f"catalog entry {self.name!r}: upstream_ref must be a 40-hex commit SHA "
                f"(tags/branches move; got {self.upstream_ref!r})"
            )
        if _SUBDIR_BAD.search(self.subdir):
            raise SkillValidationError(
                f"catalog entry {self.name!r}: subdir must be a relative path without "
                f"traversal, got {self.subdir!r}"
            )
        if self.archetype not in ARCHETYPES:
            raise SkillValidationError(
                f"catalog entry {self.name!r}: archetype must be one of {sorted(ARCHETYPES)}"
            )
        if self.risk not in RISK_LEVELS:
            raise SkillValidationError(
                f"catalog entry {self.name!r}: risk must be one of {sorted(RISK_LEVELS)}"
            )
        if self.expected_tree_hash is not None and not _TREE_HASH_RE.fullmatch(
            self.expected_tree_hash.strip().lower()
        ):
            raise SkillValidationError(
                f"catalog entry {self.name!r}: expected_tree_hash must be 64-hex sha256"
            )
        if self.expected_tree_hash is not None:
            object.__setattr__(self, "expected_tree_hash", self.expected_tree_hash.strip().lower())
        if self.vendored and self.expected_tree_hash is None:
            raise SkillValidationError(
                f"catalog entry {self.name!r} claims vendored=true without expected_tree_hash "
                "(an unverifiable vendored claim is the manifest-trust hole)"
            )

    @property
    def clone_url(self) -> str:
        return f"https://github.com/{self.repo}.git"

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "source": self.source,
            "repo": self.repo,
            "upstream_ref": self.upstream_ref,
            "subdir": self.subdir,
            "license": self.license,
            "archetype": self.archetype,
            "risk": self.risk,
            "improves": self.improves,
            "vendored": self.vendored,
        }
        if self.activation_description:
            payload["activation_description"] = self.activation_description
        if self.expected_tree_hash:
            payload["expected_tree_hash"] = self.expected_tree_hash
        if self.evidence:
            payload["evidence"] = list(self.evidence)
        if self.notes:
            payload["notes"] = self.notes
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CatalogEntry":
        if not isinstance(data, Mapping):
            raise SkillValidationError(f"catalog entry must be a mapping, got {type(data).__name__}")
        raw_evidence = data.get("evidence", [])
        if raw_evidence and not isinstance(raw_evidence, list):
            raise SkillValidationError("catalog entry 'evidence' must be a list of URLs")
        return cls(
            name=str(data.get("name", "")),
            source=str(data.get("source", "")),
            repo=str(data.get("repo", "")),
            upstream_ref=str(data.get("upstream_ref", "")),
            subdir=str(data.get("subdir", "")),
            license=str(data.get("license", "")),
            archetype=str(data.get("archetype", "")),
            risk=str(data.get("risk", "")),
            improves=str(data.get("improves", "")),
            activation_description=(
                str(data["activation_description"]) if data.get("activation_description") else None
            ),
            expected_tree_hash=(
                str(data["expected_tree_hash"]) if data.get("expected_tree_hash") else None
            ),
            vendored=bool(data.get("vendored", False)),
            evidence=tuple(str(u) for u in raw_evidence),
            notes=(str(data["notes"]) if data.get("notes") else None),
        )


@dataclass(frozen=True, slots=True)
class SkillCatalog:
    entries: tuple[CatalogEntry, ...] = field(default_factory=tuple)

    def get(self, name: str) -> CatalogEntry | None:
        wanted = name.strip().lower()
        for entry in self.entries:
            if entry.name == wanted:
                return entry
        return None

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(entry.name for entry in self.entries)


def load_catalog(path: Path | str) -> SkillCatalog:
    """Load + validate the curated catalog. Loud on every malformed entry."""
    catalog_path = Path(path)
    if not catalog_path.is_file():
        raise SkillValidationError(f"skill catalog not found: {catalog_path}")
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise SkillValidationError(f"invalid catalog YAML at {catalog_path}: {exc}") from exc
    if not isinstance(data, Mapping) or "skills" not in data:
        raise SkillValidationError(f"catalog {catalog_path} must be a mapping with a 'skills' list")
    raw_entries = data.get("skills", [])
    if not isinstance(raw_entries, list):
        raise SkillValidationError(f"catalog {catalog_path}: 'skills' must be a list")
    entries = [CatalogEntry.from_dict(item) for item in raw_entries]
    seen: set[str] = set()
    for entry in entries:
        if entry.name in seen:
            raise SkillValidationError(f"duplicate catalog entry name: {entry.name!r}")
        seen.add(entry.name)
    return SkillCatalog(entries=tuple(entries))


def lint_catalog(catalog: SkillCatalog, shelf_names: Iterable[str] = ()) -> tuple[str, ...]:
    """Curator lint for the catalog itself. Warns, never refuses.

    - vendored entries should exist on the shelf (and vice versa for
      catalog-sourced shelf skills);
    - risky entries deserve a note explaining why they are listed at all;
    - entries without evidence references are flagged (curation claims need
      support). Redistribution-refusing licenses are REFUSED at construction,
      not linted.
    """
    warnings: list[str] = []
    shelf = {n.strip().lower() for n in shelf_names}
    for entry in catalog.entries:
        if entry.vendored and shelf and entry.name not in shelf:
            warnings.append(
                f"catalog lint: {entry.name!r} is marked vendored but absent from the shelf"
            )
        if not entry.vendored and shelf and entry.name in shelf:
            warnings.append(
                f"catalog lint: {entry.name!r} is on the shelf but the catalog says not vendored"
            )
        if entry.risk == "risky" and not entry.notes:
            warnings.append(
                f"catalog lint: {entry.name!r} is classified risky with no notes — say why it is listed"
            )
        if not entry.evidence:
            warnings.append(
                f"catalog lint: {entry.name!r} has no evidence references — curation "
                "claims need supporting links"
            )
        if entry.source != entry.repo:
            warnings.append(
                f"catalog lint: {entry.name!r} source {entry.source!r} differs from "
                f"repo {entry.repo!r} — advisory matching uses the SOURCE spelling; "
                "diverge only deliberately (and say why in notes)"
            )
    return tuple(warnings)
