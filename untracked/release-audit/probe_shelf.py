"""Audit probe: evaluate every shelf skill through the live trust gate.

Read-only. Writes nothing. Prints one row per skill.
"""

from pathlib import Path

from abstractskill import (
    FilesystemSkillLoader,
    TrustRegistry,
    evaluate_trust,
    inspect_skill_dir,
    lint_registry,
    select_skills_for_context,
)

REPO = Path(__file__).resolve().parents[2]
REG = REPO / "registry"
SHELF = REG / "skills"

registry = TrustRegistry.load(
    validations_path=REG / "validations.yaml",
    advisories_path=REG / "advisories.yaml",
    guidance_path=REG / "guidance.yaml",
)

print(f"repo={REPO}")
print(f"shelf={SHELF}  exists={SHELF.is_dir()}")

lint = lint_registry(registry)
print(f"lint_registry issues: {len(lint)}")
for issue in lint:
    print(f"  LINT {issue}")

warnings: list[str] = []
loader = FilesystemSkillLoader(SHELF)
metas = list(loader.discover(on_warning=warnings.append))
print(f"discovered={len(metas)} skills; discover warnings={len(warnings)}")
for w in warnings:
    print(f"  WARN {w}")

names = sorted(m.name for m in metas)
print(f"names={names}")

print()
print(f"{'skill':<34} {'trust':<14} {'blocked':<8} {'review':<7} tree_hash[:12]")
print("-" * 90)
for meta in sorted(metas, key=lambda m: m.name):
    skill_dir = meta.source_path.parent
    inv = inspect_skill_dir(skill_dir)
    verdict = evaluate_trust(
        name=meta.name,
        tree_hash=inv.tree_hash,
        registry=registry,
    )
    print(
        f"{meta.name:<34} {str(verdict.level):<14} {str(verdict.blocked):<8} "
        f"{str(verdict.requires_review):<7} {inv.tree_hash[:12]}"
    )
    for reason in getattr(verdict, "reasons", []) or []:
        print(f"    reason: {reason}")

print()
print("=== select_skills_for_context over the whole shelf ===")
selection = select_skills_for_context(registry, shelf_root=SHELF, names=names, enabled=[])
print(f"active type={type(selection.active).__name__} n={len(selection.active)}")
print(f"active names={sorted(m.name for m in selection.active)}")
for attr in (
    "blocked",
    "requires_review",
    "unresolved",
    "notes",
    "warnings",
    "activation_descriptions",
    "requires",
):
    val = getattr(selection, attr, None)
    if val:
        print(f"{attr} ({type(val).__name__}, n={len(val)}) = {val if attr != 'activation_descriptions' else sorted(val)}")

from abstractskill import format_available_skills_xml

block = format_available_skills_xml(
    list(selection.active), descriptions=selection.activation_descriptions
)
print(f"\nprompt block bytes={len(block.encode('utf-8'))}")
print(block[:400])
