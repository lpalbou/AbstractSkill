"""Production drive: use abstractskill the way a HOST does, against the REAL shelf.

Operator directive 2026-07-13 15:06 ("test your package beyond the unit
tests — use it the way the operator does, find what breaks, fix it, show
the evidence"). A green unit suite is the floor; this script is the bar:
every stage below is a real host journey over the real registry, real
vendored bytes, and a real user-writable root, printing PASS/FAIL evidence.
Exit code is non-zero on any failure. No network required (vendoring is
exercised by its own offline suite; the fetch path needs a live remote).

Stages:
 1. discovery over the real shelf (what an agent lists at startup);
 2. names-only trust-gated selection of EVERY shelf skill (the per-phase
    config shape) — verdicts must match the registry's recorded levels;
 3. multi-root with a user dir: shadow never inherits trust; broken shadow
    falls back loudly; the winning copy is named;
 4. the operator enable journey: held skill -> read resolved_tree_hashes
    -> write a hash pin -> re-select -> active via the pinned grant;
    wrong pin stays held;
 5. progressive disclosure with digest attestation (read_skill_resource
    expected_sha256 from the same inventory the verdict covered);
 6. prompt rendering (format_available_skills_xml + activation overrides)
    — no "Codex" leakage, no unshipped-faculty words;
 7. catalog load + lint over the real catalog.yaml.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from abstractskill import (  # noqa: E402
    FilesystemSkillLoader,
    TrustRegistry,
    format_available_skills_xml,
    inspect_skill_dir,
    lint_catalog,
    load_catalog,
    select_skills_for_context,
)

SHELF = REPO / "registry" / "skills"
VALIDATIONS = REPO / "registry" / "validations.yaml"
ADVISORIES = REPO / "registry" / "advisories.yaml"
GUIDANCE = REPO / "registry" / "guidance.yaml"
CATALOG = REPO / "registry" / "catalog.yaml"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def main() -> int:
    registry = TrustRegistry.load(
        validations_path=VALIDATIONS,
        advisories_path=ADVISORIES,
        guidance_path=GUIDANCE,
    )

    # -- 1. discovery ------------------------------------------------------
    metas = FilesystemSkillLoader(SHELF).discover()
    names = [m.name for m in metas]
    # The registry's validated names are the shelf's roster of record —
    # discovery must list exactly them (a magic count here would rot).
    recorded = {r.name for r in registry.validations}
    check(
        "discovery lists exactly the validated roster",
        set(names) == recorded,
        f"{len(names)} skills",
    )
    check("discovery is sorted and unique", names == sorted(set(names)))

    # -- 2. names-only selection of the whole shelf ------------------------
    sel = select_skills_for_context(registry, SHELF, names)
    active = set(sel.active_names)
    held = {n for n, _ in sel.held}
    check(
        "whole-shelf selection: no skill blocked or missing",
        not sel.blocked and not sel.missing,
        f"active={len(active)} held={len(held)}",
    )
    # Scripts-bearing skills must be HELD (requires_review), never silently
    # active; pure-knowledge validated skills must be ACTIVE.
    for meta in metas:
        inv = inspect_skill_dir(SHELF / meta.name)
        if inv.has_scripts:
            check(f"scripts-bearing {meta.name!r} held without enable", meta.name in held)
        else:
            check(f"clean validated {meta.name!r} active", meta.name in active)
    check(
        "resolved mappings cover every attested name",
        set(sel.resolved_paths) == active | held
        and set(sel.resolved_tree_hashes) == active | held,
    )

    # -- 3. multi-root shadow behavior --------------------------------------
    with tempfile.TemporaryDirectory() as td:
        user_root = Path(td) / "user-skills"
        (user_root / "backlog").mkdir(parents=True)
        (user_root / "backlog" / "SKILL.md").write_text(
            "---\nname: backlog\ndescription: A user-modified shadow copy.\n---\n\nShadow.\n",
            encoding="utf-8",
        )
        warnings: list[str] = []
        sel_shadow = select_skills_for_context(
            registry, [SHELF, user_root], ["backlog"], on_warning=warnings.append
        )
        check(
            "user shadow of a curated name is HELD (never inherits trust)",
            [n for n, _ in sel_shadow.held] == ["backlog"] and not sel_shadow.active_names,
        )
        check(
            "shadow's winning copy is the USER path in resolved_paths",
            sel_shadow.resolved_paths.get("backlog") == user_root / "backlog",
        )

        # Broken shadow (invalid bytes) must fall back loudly to curated.
        (user_root / "backlog" / "SKILL.md").write_bytes(b"\xff\xfe broken")
        warnings.clear()
        sel_broken = select_skills_for_context(
            registry, [SHELF, user_root], ["backlog"], on_warning=warnings.append
        )
        check(
            "broken shadow falls back to the curated copy loudly",
            sel_broken.resolved_paths.get("backlog") == SHELF / "backlog"
            and any("#FALLBACK" in w for w in warnings),
        )

        # -- 4. operator enable journey (hash pin) --------------------------
        (user_root / "backlog" / "SKILL.md").write_text(
            "---\nname: backlog\ndescription: A user-modified shadow copy.\n---\n\nShadow.\n",
            encoding="utf-8",
        )
        sel_held = select_skills_for_context(registry, [SHELF, user_root], ["backlog"])
        pin = sel_held.resolved_tree_hashes["backlog"]
        sel_pinned = select_skills_for_context(
            registry, [SHELF, user_root], ["backlog"], enabled=[f"backlog@{pin}"]
        )
        check(
            "hash-pinned enable activates the reviewed bytes",
            sel_pinned.active_names == ("backlog",),
        )
        wrong = "0" * 64
        sel_wrong = select_skills_for_context(
            registry, [SHELF, user_root], ["backlog"], enabled=[f"backlog@{wrong}"]
        )
        check(
            "wrong pin stays held (grant does not apply)",
            not sel_wrong.active_names and [n for n, _ in sel_wrong.held] == ["backlog"],
        )

    # -- 5. progressive disclosure with digest attestation ------------------
    from abstractskill import read_skill_resource

    arch_inv = inspect_skill_dir(SHELF / "architect")
    resource = next(r for r in arch_inv.files if r.rel_path != "SKILL.md")
    data = read_skill_resource(
        SHELF / "architect",
        resource.rel_path,
        max_bytes=1 << 20,
        expected_sha256=resource.sha256,
    )
    check(
        "attested resource read returns bytes matching the inventory digest",
        len(data) == resource.size_bytes,
        resource.rel_path,
    )
    try:
        read_skill_resource(
            SHELF / "architect", resource.rel_path,
            max_bytes=1 << 20, expected_sha256="f" * 64,
        )
        check("wrong resource digest refuses", False)
    except Exception as exc:
        check("wrong resource digest refuses", "does not match" in str(exc))

    # -- 6. prompt rendering -------------------------------------------------
    overrides = registry.activation_descriptions()
    block = format_available_skills_xml(metas, descriptions=overrides)
    check("prompt block renders every shelf skill", all(n in block for n in names))
    check("no vendored-harness name leaks into the prompt", "Codex" not in block)
    check("no unshipped faculty advertised", "probe" not in block.lower())

    # -- 7. catalog ----------------------------------------------------------
    catalog = load_catalog(CATALOG)
    warnings = list(lint_catalog(catalog, shelf_names=set(names)))
    check("catalog loads", len(catalog.entries) >= 8, f"{len(catalog.entries)} entries")
    check("catalog lints clean against the shelf", not warnings, "; ".join(warnings))

    print()
    if FAILURES:
        print(f"DRIVE FAILED: {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("DRIVE GREEN: every host journey passed against the real shelf.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
