# Planned: First-party curated shelf (adversarial-iteration, coredoc, backlog)

## Metadata
- Created: 2026-07-11
- Status: Planned (in progress)
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: None

## Context
Maintainer directive 2026-07-11: create a skill for "using 1 adversarial sub
agent + min 3 cycles of improvements" prompting; integrate the local codex
`coredoc` skill (documentation maintenance) and `backlog` skill (long-running
task planning). Gateway needs only ~2 skills for the console's first
integration ("2 of each are enough for the moment").

## Current code reality
The codex skills live at `~/.codex/skills/{coredoc,backlog}/` (SKILL.md +
references/ + an `agents/openai.yaml`). They are Agent Skills-shaped but
UNVERIFIED against our parser (frontmatter has name+description; name must
match directory; description lengths must pass the 1024 ceiling). No shelf
directory exists in this repo.

## Problem
The maintainer's methodology skills exist only on one machine outside any
registry — unhashed, unvalidated, undistributable. The prescribed working
method (adversarial subagent + ≥3 improvement cycles) exists only as prompt
folklore.

## What we want to do
- Author `adversarial-iteration` (new, first-party): the methodology skill —
  1+ adversarial subagent attacks each deliverable; ≥3 cycles; each cycle
  must land at least one significant improvement; findings folded or
  explicitly deferred on the record.
- Vendor `coredoc` + `backlog` byte-verbatim into `registry/skills/<name>/`,
  validated by our own parser (round-trip: parse, name/dir match, ceilings).
- Mint ValidationRecords (`method=first-party` for authored;
  `method=first-party-adoption` for the maintainer's two — reviewed, not
  simulation-audited yet; 0003 upgrades them later).
- Record tree hashes in the shelf registry (`registry/validations.yaml`).

## Requirements
- Vendored copies byte-identical to source (tree-hash recorded at vendoring).
- All three parse cleanly with abstractskill (they become the parser's first real-world corpus).
- Shelf entries carry trust metadata consumable by the gateway picker.

## Scope
Authoring, vendoring, validation records, hashes.

## Non-goals
- No editing of the maintainer's skills beyond what validation REQUIRES (any required change is reported, not silent).
- No scripts in any of the three (knowledge/procedure packs — the v1 cut).

## Dependencies and related tasks
0001 (records), gateway Phase 4 (consumes the shelf).

## Expected outcomes
`registry/skills/` with three validated, hash-pinned skills; gateway can seed its console from it.

## Validation
Parser round-trip tests over the vendored shelf; tree hashes stable across two runs; discover() lists all three.

## Progress checklist
- [x] Item created
- [x] adversarial-iteration authored (registry/skills/adversarial-iteration)
- [x] coredoc + backlog vendored byte-verbatim + parser-validated
- [x] ValidationRecords + tree hashes in registry/validations.yaml (adopted level for the two adopted skills; activation_description overrides for the "Codex"-worded descriptions)
- [x] Shelf integration tests (test_shelf.py) + refresh_shelf.py idempotent (preserves validated_at on unchanged bytes)
