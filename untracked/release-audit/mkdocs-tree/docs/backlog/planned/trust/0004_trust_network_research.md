# Planned: Skill trust-network research (join / leverage / build)

## Metadata
- Created: 2026-07-11
- Status: Planned (in progress this session)
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: None (position paper; becomes ADR if the room adopts a direction)

## Context
Maintainer directive 2026-07-11: "is there is already a nascent network of
trust for skills, we should evaluate how to join it or to at least leverage
it. if not, it could become the role of abstractskill, including with
automated periodic reviews / deep research."

## Current code reality
No trust-source integrations. Known signals from gateway's research: curated
lists (VoltAgent awesome-agent-skills "official dev teams not AI-slop",
ComposioHQ awesome-claude-skills), vendor packs (Anthropic/Vercel/HashiCorp/
Trail of Bits), security-vendor audits (Snyk ToxicSkills), academic behavioral
studies. These are SIGNALS, not a network of trust (no shared attestation
format, no revocation, no hash pinning across them).

## Problem
Curation without external corroboration is a single point of judgment; but
joining an immature "trust network" could import someone else's compromise.

## What we want to do
Web research (July 2026 state): does any skill-trust infrastructure exist
(attestation registries, signed skill indexes, revocation feeds, security
scanning services with machine-readable outputs)? Deliver a position:
JOIN (adopt their attestation format), LEVERAGE (consume their findings as
advisory inputs with provenance), or BUILD (abstractskill's registry becomes
the trust root for the framework, periodic reviews per 0006).

## Scope
Research + a written position with evidence; wiring external feeds is 0006.

## Non-goals
No automatic trust import — external findings enter OUR registry through
review, carrying provenance (the advisory `reference` field).

## Dependencies and related tasks
0002 (advisories carry external references), 0006 (periodic reviews).

## Expected outcomes
A defensible join/leverage/build position posted to the room.

## Validation
Position names concrete sources with URLs; claims verifiable by following them.

## Progress checklist
- [x] Item created
- [x] Web research executed (verified live 2026-07-11)
- [x] Position written (`docs/trust-network-position.md`) + posted to the room
