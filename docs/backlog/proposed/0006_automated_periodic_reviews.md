# Proposed: Automated periodic reviews / deep research of the trust registry

## Metadata
- Created: 2026-07-11
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: May need an ADR (scheduling + external-feed policy is durable)

## Context
Maintainer directive 2026-07-11: abstractskill's trust role could include
"automated periodic reviews / deep research". This is the sustaining engine
behind 0002/0004 — advisories and validations go stale as upstream sources
change.

## Current code reality
0001/0002 give a static registry; nothing refreshes it. The framework has a
scheduling primitive (runtime WAIT_UNTIL + gateway loops) and a research
capability (web tools), but the seat rules forbid machine persistence
(launchd/cron) from the agent — scheduling must be host-owned (gateway/CI).

## Problem or opportunity
Trust data with no refresh cadence silently rots; a periodic deep-research
pass keeps advisories current and discovers new ones.

## Proposed direction
A recurrent job (gateway-scheduled or CI) that: re-verifies each advisory's
reference is still live and its finding still stands; runs deep research for
new advisories against tracked sources (0004's outcome); re-audits shelf
skills (0003) on a cadence; opens registry diffs for human review — never
auto-mutating trust without a review gate.

## Why it might matter
Turns the registry from a snapshot into a maintained trust root.

## Promotion criteria
0001/0002 shipped AND a scheduling host identified AND 0004's position favors
build/leverage (not pure join).

## Validation ideas
A dry-run review pass that only proposes diffs; measure false-positive rate on the seed set.

## Non-goals
No agent-side persistence; no auto-apply of external findings without review.

## Guidance for future agents
Reuse the framework scheduler; keep the human/review gate mandatory.
