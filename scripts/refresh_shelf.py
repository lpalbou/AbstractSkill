#!/usr/bin/env python3
"""Regenerate the first-party shelf's validation registry from real tree hashes.

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
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        "activation_description": None,
    },
    "backlog": {
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


def build_records() -> list[dict]:
    # Imported lazily so the script works from a source checkout without install.
    sys.path.insert(0, str(REPO / "src"))
    from abstractskill import FilesystemSkillLoader, inspect_skill_dir

    loader = FilesystemSkillLoader([SHELF])
    discovered = {meta.name for meta in loader.discover(on_warning=lambda m: print(m, file=sys.stderr))}
    absent = sorted(set(SHELF_POLICY) - discovered)
    if absent:
        raise SystemExit(f"SHELF_POLICY names skills not on disk: {absent}")

    today = _dt.date.today().isoformat()
    prior_dates = _existing_dates_by_hash()
    records: list[dict] = []
    for name in sorted(discovered):
        if name not in SHELF_POLICY:
            raise SystemExit(f"shelf skill {name!r} has no SHELF_POLICY entry; add one")
        policy = SHELF_POLICY[name]
        inventory = inspect_skill_dir(SHELF / name)
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
            "notes": (
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
    VALIDATIONS.write_text(
        HEADER + yaml.safe_dump({"validations": records}, sort_keys=False),
        encoding="utf-8",
    )
    print(f"wrote {len(records)} validation record(s) to {VALIDATIONS.relative_to(REPO)}")
    for record in records:
        print(f"  {record['name']}: {record['tree_hash'][:16]}… ({record['method']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
