# 0008 — Skill tool-dependency declaration (requires_mcp) with loud activation failure

- Work-item id: abstractskill-0008
- Owner: skill
- Status: Completed
- Completed: 2026-07-21
- Created: 2026-07-19
- Thread: dm:meshvault--skill#2 (asks 1-3, answered seq 3)

## Summary

Give SKILL.md authors a declared way to say "this skill requires MCP server
X (or tool Y)" so activation can FAIL LOUDLY with an install hint instead of
agents discovering mid-task that the taught tools are absent — the
teach-what-is-wired principle applied to skills themselves.

## Reason / origin

The meshvault seat's `meshvault-live-editing` skill (operator-directed
registration discussion, 2026-07-19) teaches recipes that all presuppose a
reachable `meshvault-mcp` server — a third-party MCP dependency. The
frontmatter contract today carries no dependency field; the failure mode is
an agent activating the skill, following a recipe, and hitting absent tools
mid-task. Two body-side conventions exist now (dependency named in the
activation description; `metadata: {requires_mcp: [...]}` as a free-form
convention hosts may check) — this item is the HOST-SIDE half.

## Scope

1. Adopt `metadata.requires_mcp: [server-names]` (and possibly
   `metadata.requires_tools: [tool-names]`) as a DOCUMENTED convention —
   no parser/contract change needed (metadata is already a free mapping);
   document in the skills contract docs.
2. `select_skills_for_context` (the 0087 trust gate) surfaces a `requires`
   field on resolved selections the way trust verdicts ride today, so hosts
   can check declared dependencies against their live tool/MCP inventory
   and refuse-with-reason ("skill X requires meshvault-mcp — not reachable;
   install hint: ...") instead of activating blind.
3. Render rule (consumers, feature-detected): a skill whose declared
   dependency is absent renders selectable-with-warning or
   blocked-with-reason per the host's policy — never silently activated,
   never silently hidden (the launch-skills render rules extended by one
   verdict class).

## Non-goals

- No hard contract field in frontmatter v1 (metadata convention suffices;
  a first-class field is a later widening through the normal path).
- No auto-install of missing servers (the hint names, never executes).

## Current code reality

- `SkillMetadata.metadata` is a frozen free-form mapping (models.py:20) —
  the convention rides today with zero code change.
- `select_skills_for_context` returns verdicts (trust state, reasons);
  no dependency awareness.
- First consumer waiting: meshvault-live-editing (registration pending
  their SHA + evidence receipt).

## Validation expectations

- A skill declaring `requires_mcp: [x]` resolves with the requires field
  surfaced; a host with x absent refuses with the reason verbatim; a host
  with x present activates normally. Pinned by tests on the selection
  surface; docs updated in the same change (coredoc discipline).

## Completion report

- Date: 2026-07-21
- Summary: `SkillRequires` + `SkillSelection.requires` shipped —
  frontmatter `metadata.requires_mcp`/`metadata.requires_tools` surface
  on the selection for every resolved name (active/held/blocked; no row
  when nothing declared). Host information for refuse-with-reason;
  never a gate in this library, never an auto-install (scope items 1-3
  delivered: convention documented in docs/api.md Models + Selection;
  requires field on resolved selections; render rule stated as host
  policy, never library enforcement).
- Files: src/abstractskill/selection.py (SkillRequires, _parse_requires,
  requires field + population), src/abstractskill/__init__.py (export),
  tests/test_selection.py (6 pins incl. both-channel warning),
  tests/test_shelf.py (live-shelf pin: meshvault keeps declaring),
  docs/api.md, llms-full.txt, CHANGELOG.md.
- Tests: 166 passed (5 synthetic + 1 live-shelf pin new).
- Adversary: fable5 pass — 0 P0, 1 P1 (live-shelf pin missing —
  folded), 6 P2s (5 folded: absent-vs-empty comment semantics,
  order-preserving dedup, both-channel warning pin, author-facing
  Models pointer, card hygiene; 1 routed: gateway consumer pointer).
- Follow-ups: (1) gateway seat pointed at the surface (their
  entity_skills resolve is the first host consumer — the
  refuse-with-reason check is theirs to wire); (2) first-class
  frontmatter field stays a later widening through the normal path
  (non-goal held).
