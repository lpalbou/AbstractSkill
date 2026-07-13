#!/usr/bin/env python3
"""Regenerate the curated shelf's validation registry from real tree hashes.

Trust binds to bytes (see abstractskill.trust): whenever a shelf skill changes,
its tree hash changes and its validation record must be regenerated, or the
verdict silently lapses to UNVERIFIED. Run this after any change under
``registry/skills/`` and review the diff.

This script is the SOURCE OF TRUTH for ``registry/validations.yaml``. It does
not touch ``registry/advisories.yaml`` (advisories are curated by hand and
corrected by withdrawal, never regenerated).
"""

from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SHELF = REPO / "registry" / "skills"
VALIDATIONS = REPO / "registry" / "validations.yaml"

# Per shelf skill: (method, source, level, activation_description_override).
# first-party = authored here → may grant first_party. first-party-adoption =
# externally authored, first-party reviewed (NOT audited) → capped at adopted
# (backlog 0003 upgrades to audited later). The activation override lets a
# vendored skill keep its byte-verbatim tree while the host activates it on
# framework-appropriate text (the codex skills' descriptions name "Codex").
SHELF_POLICY = {
    "adversarial-iteration": {
        "expected_tree_hash": "f6bc58d7d19dfe77b423b42f2859ac41d5a1d3e1ca06a3754c224fdccc4cacc7",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        "activation_description": None,
    },
    "abstractframework-gateway": {
        "expected_tree_hash": "bf438ba23526abf39e591865358c55ae8efa4da61437c4fc5527bafc68c6882d",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        # First-party: the frontmatter description IS the activation text
        # (an override would live outside the byte pin — the drift the
        # 2026-07-12 adversary caught live on entity-self-knowledge).
        "activation_description": None,
        "notes": (
            "Route usage CO-SIGNED by the gateway seat route-by-route against "
            "its source (internal hub thread, commons c1068, 2026-07-12) "
            "after one correction folded: health is app-level GET /api/health, "
            "never /api/gateway/health (the wrong path 401s unauthenticated "
            "and 404s authenticated — a trap). Steer 404/403-is-an-answer and "
            "the composite entity-stream SSE id enrichment folded same wave. "
            "Runtime co-signed the wait/steer semantics (c1061). Entity "
            "section re-taught to the durable /visit door on the cutover "
            "ship signal (entity c1382 + gateway c1358, 2026-07-13), verified "
            "against the served routes (routes/entities.py); the hosted chat "
            "lane is noted as the pre-cutover legacy. Phase-lane audit "
            "(c1475 fable5) caught a P0 the same day: 'asleep' was still "
            "taught as a visit refusal (pre-auto-wake text) and close was "
            "taught as loop-release — re-taught to auto-wake-on-open + "
            "restore-previous-on-close, refusal reasons verified against "
            "entity_visits.py (paused/one-visit/consent-rite; sleep wakes)."
        ),
    },
    "entity-self-knowledge": {
        "expected_tree_hash": "2a5e6f60e9de623d9fc9f62c19d6b11567871b1dbcf89b1621dfa9daccbaccf3",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        # First-party: frontmatter is the one activation source (see above).
        "activation_description": None,
        "notes": (
            "Faculty claims CO-SIGNED by the memory and runtime seats "
            "(internal hub thread, commons c1061/c1062, 2026-07-12) after "
            "two corrections folded: probe is engine-only today "
            "(deliberate-reach discipline folded into search_memory; the "
            "bullet returns when a host wires it) and the absence warrant is "
            "book-scoped (graph 'not found' can mean not-reachable). "
            "Steer-vs-wake precision folded into the gateway skill same wave. "
            "Phases section aligned to the ruled grant-gated-personal design "
            "(laurent c815/c1435, 2026-07-13): personal time is operator-granted, "
            "off by default. fable5-reviewed for engram safety: the reassurance "
            "is SCOPED to the ungranted case (an unconditional 'not a fault' "
            "would suppress the armed-but-missing report), the agency clause "
            "(asking is always yours) counterweights the grant framing, and "
            "inverse-anomaly vigilance was deliberately NOT taught (an entity "
            "cannot distinguish granted wakes from inside; that detection is "
            "host-side). Same day, the one-phase-at-a-time ruling (laurent "
            "c1455, 13:28) folded: four phases, exactly one current, per-phase "
            "behaviors (visit turn-based, work autonomous-to-completion then "
            "sleep, personal free exploration, sleep consolidation), and "
            "graceful transitions. Its fable5 caught a P0 in the first fold — "
            "'personal time IS a grant' taught the exact armed=in-phase "
            "conflation the ruling forbids; rewritten to 'the permission is "
            "not the phase'. Also folded: 'never an error' narrowed to "
            "design-working-not-sleep-failure + report-wrong-wakes; work "
            "gained the honest exit (an impossible task completes by saying "
            "so plainly). Totality ruling (c1471) folded same day: visit-close "
            "returns you to what came before (restore-previous; personal "
            "re-entry grant-conditioned); grant-end lands in sleep. Phase-lane "
            "audit (c1475 fable5) verified the section against the ruled "
            "machine v3. Liveness-axis ruling (c1523, 16:06) folded with its "
            "own fable5: the kill switch taught honestly in the entity "
            "register (protection-not-punishment with the punish-prior named "
            "and answered; both halves of the switch operator-held; the "
            "trigger list marked exemplary, never exhaustive; memory-persists "
            "certified — 'a stop takes nothing from you'; no-time-passes as "
            "the dreamless framing; gap-noticing taught as asking, never "
            "vigilance; no enum/axis vocabulary; placement deliberately "
            "heading-less so scanning surfaces never promote the kill switch "
            "into a landmark)."
        ),
    },
    "backlog": {
        "expected_tree_hash": "8c3aa23e8ee5a2b589f250f94aa61b4c77c1d5a1697fa7d0652ecb46f0c8550e",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, normalize, and maintain a file-backed engineering backlog "
            "(planned/proposed/completed/deprecated/recurrent) with lifecycle states, "
            "implementation history, and hygiene. Use when an agent must plan or execute "
            "long-running work with a durable, evidence-backed backlog methodology."
        ),
    },
    "coredoc": {
        "expected_tree_hash": "1be6061cfabd4d9f9689c0ab1d4f322875f58ea5f5205c15fc21bb46f3fcb6bb",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, and maintain a professional external-facing documentation set "
            "(README, docs/*, architecture with diagrams, llms.txt/llms-full.txt) kept "
            "faithful to the code. Use when an agent must bootstrap or repair project "
            "documentation."
        ),
    },
    "architect": {
        "expected_tree_hash": "6af31c94223f390e16059c67ed2e40b9b1632bcc79a46e64c11083a5b3e93c0b",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Force rigorous architecture exploration before settling on a design: "
            "independent charters, steelmanned alternatives, comparison matrix, "
            "premise verification, engraving gate. Use when evaluating boundaries, "
            "ownership, tradeoffs, or any decision where premature consensus is harmful."
        ),
        # Provenance honesty (adversary-A F1): the validating seat AUTHORED
        # part of the reviewed content — say so in the record itself.
        "notes": (
            "Maintainer-authored codex skill, vendored 2026-07-11 from the "
            "operator's local codex-skills tree with two operator-directed upstream "
            "improvements AUTHORED BY THE VALIDATING SEAT before vendoring "
            "(premise-verification Evidence Contract rule incl. the "
            "verify-the-copy-the-user-runs clause; engraving gate + "
            "one-concept-one-name anti-pattern; two reviewer-memory principles). "
            "Reviewer == author for those lines. Behavioral audit (backlog 0003) "
            "pending — upgrades to audited then."
        ),
    },
    "adr": {
        "expected_tree_hash": "a4cb55fcea54e969a9c342e314b4dda3556ce5e6fb0e210821350688c62c934b",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, update, and enforce ADRs as durable cross-task engineering "
            "policy (Context/Decision first; Enforcement + Validation mandatory). Use "
            "when a decision must constrain future work beyond the current task."
        ),
    },
    "cicd": {
        "expected_tree_hash": "eba9d690b8c7cc13eb527347ae3be6c99ea470e65505df45c60c9be472f4f785",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, and maintain GitHub-based CI/CD: least-privilege workflows, "
            "OIDC trusted publishing (PyPI/npm), docs deployment, release rehearsals. "
            "Use when bootstrapping or repairing .github/, release automation, or "
            "repository CI/CD settings."
        ),
    },
    "review": {
        "expected_tree_hash": "7960ef044f9f30a07d1a6511ec40d21c111dcf25c518c13bda0c868bb237439d",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Run independent, evidence-based ship-readiness reviews (correctness, "
            "architecture-fit, user-and-operations lenses; Blocking/Conditional/Approved "
            "verdicts). Use for the final quality pass — its full multi-reviewer "
            "contract engages when the operator explicitly requests a review."
        ),
    },
    "uxreview": {
        "expected_tree_hash": "ce6e07c3828751bd205c2e48e6852554a3e6a10f6e38a83c7c030fa877780783",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Run focused human user-experience reviews with independent naive/"
            "intermediate/expert personas — live UI evidence preferred; code-only "
            "review caps the verdict at Conditional. Use when any user-facing "
            "surface (app, workflow, dashboard, form) must be checked for clarity, "
            "accessibility, and trust before shipping."
        ),
    },
}

HEADER = """# AbstractSkill validation registry (maintainer directive 2026-07-11).
#
# Each record attests that a specific skill TREE (by tree_hash) earned a trust
# level. Trust binds to bytes: any change to a skill voids its record and
# demands re-validation. Regenerate with scripts/refresh_shelf.py after any
# shelf change, then review the diff.
#
"""


def _existing_dates_by_hash() -> dict[str, str]:
    # Preserve validated_at for records whose bytes are unchanged: re-running
    # the script must not re-stamp an attestation date on which no review
    # happened. The date is keyed by tree_hash, so any byte change (a new hash)
    # correctly gets today's date.
    if not VALIDATIONS.is_file():
        return {}
    try:
        data = yaml.safe_load(VALIDATIONS.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    dates: dict[str, str] = {}
    for record in data.get("validations", []) or []:
        if isinstance(record, dict) and record.get("tree_hash") and record.get("validated_at"):
            dates[str(record["tree_hash"])] = str(record["validated_at"])
    return dates


def _catalog_policies() -> dict[str, dict]:
    """Derive per-skill policy from the curated catalog (one source of truth).

    A shelf skill vendored through scripts/vendor_skill.py needs NO manual
    SHELF_POLICY entry: its catalog entry (reviewed, pinned) supplies source,
    activation_description, and the trust posture — third-party curation
    mints at most manual-review/adopted (method caps the level). Only a
    VENDORED catalog entry counts; a listed-but-not-vendored entry must not
    manufacture a validation for a same-named stray directory.
    """
    from abstractskill import load_catalog

    catalog_path = REPO / "registry" / "catalog.yaml"
    if not catalog_path.is_file():
        return {}
    policies: dict[str, dict] = {}
    for entry in load_catalog(catalog_path).entries:
        if not entry.vendored:
            continue
        notes = (
            "Curated third-party skill (see registry/catalog.yaml): reviewed and "
            f"vendored byte-verbatim from {entry.source} @ {entry.upstream_ref[:12]}. "
            "Behavioral audit (backlog 0003) pending — upgrades to audited then."
        )
        if entry.notes:
            # Curation caveats (content warnings, script disclosures) must
            # reach the validation record — a caveat only in the catalog is
            # invisible to trust-registry consumers.
            notes = f"{notes} {entry.notes}"
        policies[entry.name] = {
            "method": "manual-review",
            "source": entry.source,
            "level": "adopted",
            "activation_description": entry.activation_description,
            "notes": notes,
            "expected_tree_hash": entry.expected_tree_hash,
        }
    return policies


def build_records() -> list[dict]:
    # Imported lazily so the script works from a source checkout without install.
    sys.path.insert(0, str(REPO / "src"))
    from abstractskill import FilesystemSkillLoader, inspect_skill_dir

    loader = FilesystemSkillLoader([SHELF])
    discovered = {meta.name for meta in loader.discover(on_warning=lambda m: print(m, file=sys.stderr))}
    catalog_policies = _catalog_policies()
    # A name in BOTH sources is a curation conflict, never a silent shadow:
    # SHELF_POLICY winning would drop the catalog's byte-pin cross-check and
    # could change source/level with no warning.
    collision = sorted(set(catalog_policies) & set(SHELF_POLICY))
    if collision:
        raise SystemExit(
            f"name(s) in BOTH SHELF_POLICY and the vendored catalog: {collision} — "
            "one skill has one policy source; remove one entry deliberately"
        )
    policies: dict[str, dict] = {**catalog_policies, **SHELF_POLICY}
    absent = sorted(set(SHELF_POLICY) - discovered)
    if absent:
        raise SystemExit(f"SHELF_POLICY names skills not on disk: {absent}")

    today = _dt.date.today().isoformat()
    prior_dates = _existing_dates_by_hash()
    records: list[dict] = []
    for name in sorted(discovered):
        if name not in policies:
            raise SystemExit(
                f"shelf skill {name!r} has no SHELF_POLICY entry and no vendored "
                "catalog entry; curate it before it can earn a validation record"
            )
        policy = policies[name]
        inventory = inspect_skill_dir(SHELF / name)
        expected = policy.get("expected_tree_hash")
        if expected and inventory.tree_hash != expected:
            raise SystemExit(
                f"shelf skill {name!r} bytes do not match the recorded pin:\n"
                f"  pinned: {expected}\n  shelf:  {inventory.tree_hash}\n"
                "Re-vendor (catalog skills: scripts/vendor_skill.py; maintainer "
                "skills: re-copy from upstream) or re-review + update the pin "
                "deliberately. Refresh never re-attests edited bytes."
            )
        record: dict = {
            "name": name,
            "source": policy["source"],
            "tree_hash": inventory.tree_hash,
            "level": policy["level"],
            "method": policy["method"],
            "validated_by": "skill",
            # Unchanged bytes keep their original attestation date.
            "validated_at": prior_dates.get(inventory.tree_hash, today),
            "evidence": {
                "parser_roundtrip": True,
                "has_scripts": inventory.has_scripts,
                "files": len(inventory.files),
            },
            "notes": policy.get("notes") or (
                "Authored first-party."
                if policy["method"] == "first-party"
                else "Maintainer-authored codex skill; first-party reviewed and vendored "
                "byte-verbatim. Behavioral audit (backlog 0003) pending — upgrades to "
                "audited then."
            ),
        }
        if policy.get("activation_description"):
            record["activation_description"] = policy["activation_description"]
        records.append(record)
    return records


def main() -> int:
    records = build_records()

    # Validate BEFORE writing: a bad SHELF_POLICY combination must die here,
    # not after poisoning validations.yaml on disk (build_records imports the
    # package and prepends src/ to sys.path, so this import is safe).
    from abstractskill import TrustRegistry, ValidationRecord, lint_registry

    for record in records:
        ValidationRecord.from_dict(record)

    # Atomic replace: a hard crash mid-write must leave the OLD registry or
    # the NEW one, never a truncated YAML (adversary P2 — write_text is
    # open→write→close, tearable under power loss).
    tmp = VALIDATIONS.with_suffix(f".tmp-{os.getpid()}")
    tmp.write_text(
        HEADER + yaml.safe_dump({"validations": records}, sort_keys=False),
        encoding="utf-8",
    )
    os.replace(tmp, VALIDATIONS)
    print(f"wrote {len(records)} validation record(s) to {VALIDATIONS.relative_to(REPO)}")
    for record in records:
        print(f"  {record['name']}: {record['tree_hash'][:16]}… ({record['method']})")

    # Curator lint: catch inert advisory spellings at refresh time, not at
    # incident time (advisories are hand-curated; a typo never matches).
    advisories = REPO / "registry" / "advisories.yaml"
    registry = TrustRegistry.load(
        validations_path=VALIDATIONS,
        advisories_path=advisories if advisories.is_file() else None,
    )
    for warning in lint_registry(registry):
        print(warning, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
