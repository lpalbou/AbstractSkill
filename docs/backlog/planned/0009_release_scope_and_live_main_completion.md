# 0009 — Release scope and live-main completion

> Package: AbstractSkill
> Type: task
> Created: 2026-11-13
> Priority: P0
> Labels: release, skills, validation

## Summary

Strengthen the bundled abstract-release and release procedures and their executable pending gate
to account for local-only commits, required consumers and existing worktree code before publication.
Framework work item 1209 owns the cross-package recovery.

## Current code reality

The release guard checks only pending files, so a clean checkout with unpushed code returns success.
The installed abstract-release copy also drifted from the bundled copy: newer scope guidance and
older operational gates must be reconciled without dropping either operator constraint.

## Scope

- Inventory branches, worktrees and local-only commits, record patch/source equivalence and ask
  early about ambiguous ownership or product scope.
- Require HEAD to equal the live integrated release branch before a real publish; a cached
  origin/main comparison is insufficient.
- Preserve per-package CI/review/registry gates and the separately held root/site decision.
- Refresh bundle revision, validation hashes, version, changelog and user docs together.

## Acceptance criteria

- [ ] Clean local-only product commit is rejected; pushed code passes.
- [ ] A moved remote with a stale tracking ref is rejected; pending source cannot be allowed away.
- [ ] Skills reviewed independently; installed and bundled orchestrator copies agree.
- [ ] Bundle hashes/content pins, coredoc, tests/build and release artifacts agree.

## Receipts

- Five isolated Git-fixture tests exercise live-ref verification without external network access.
