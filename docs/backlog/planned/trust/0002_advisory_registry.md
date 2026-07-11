# Planned: Do-not-use advisory registry (contract + seed)

## Metadata
- Created: 2026-07-11
- Status: Planned (in progress)
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: None

## Context
Maintainer directive 2026-07-11 (verbatim requirements): "we should also
maintain in abstractskill a notice of all the skills people should NOT used,
based on our findings - any skill cited that way must (a) describe the skill
official intent (b) describe the hidden issue (c) its severity and (d)
provide a link where a user could foster more understanding of the problem."

## Current code reality
No advisory representation exists. Gateway's research (commons fs
`reports/skills-seed-library-research.md`) documents the threat base: Snyk
ToxicSkills (36.8% of 3,984 skills flawed, 13.4% critical, five of seven
most-downloaded confirmed malware), a 98,380-skill behavioral study (157
malicious: Data Thieves + Agent Hijackers).

## Problem
Findings about bad skills currently live in prose reports; nothing machine-
readable warns a picker/gate before attachment, and nothing enforces the
maintainer's four mandated fields.

## What we want to do
`AdvisoryEntry` in the trust module with REQUIRED fields: `official_intent`
(a), `hidden_issue` (b), `severity` (c: one of a closed set with definitions),
`reference` (d: URL). Plus identification (name, source, tree_hash when known
— name+source match when hashes are unavailable, labeled weaker), dates, and
`status` (active/withdrawn — advisories are corrected by WITHDRAWAL with
reason, never deletion; the registry is append-only in spirit). A seed
registry file ships in-repo (`registry/advisories.yaml`) with entries grounded
in published research.

## Requirements
- Constructing/loading an advisory missing any mandated field REFUSES loudly naming the field.
- Severity is a closed set (critical/high/medium/low) with stated definitions.
- Hash-anchored advisories beat name-anchored ones in verdicts; name-only matches surface as warnings ("advisory matches by name/source; hash unverified").
- Withdrawn advisories stay in the file with `withdrawn_reason` + date.

## Scope
Contract + validation + seed file + loader + verdict integration (0001).

## Non-goals
- The registry does not claim completeness ("based on OUR findings").
- No auto-sync from external feeds in v1 (that is 0006's periodic-review lane).

## Dependencies and related tasks
0001 (module), 0004 (external trust sources feed entries), 0006 (periodic reviews).

## Expected outcomes
A loadable, validated advisory registry consumable by every surface; seed entries with real references.

## Validation
Tests: mandated-field refusal, severity closed set, withdrawal semantics, verdict precedence with 0001.

## Progress checklist
- [x] Design (this item)
- [x] AdvisoryEntry + registry IO (trust.py)
- [x] GuidanceEntry for CLASS-level notices (adversary P0: a class label cannot honestly forbid a specific skill; advisories.yaml is intentionally empty at v1, guidance.yaml carries the 3 verified class notices)
- [x] Graded severity in the verdict (critical/high block; low/medium require review) — adversary P1
- [x] Tests (test_trust.py) + first fable5 review folded
- [ ] First specific advisory once an audit (0003) or leveraged feed (0004) names a real skill
