# 0009 — Release scope and live-main completion

> Package: AbstractSkill
> Type: task
> Created: 2026-11-13
> Status: Completed
> Completed: 2026-11-14
> Priority: P0
> Labels: release, skills, validation

## Summary

Strengthen the bundled abstract-release and release procedures and their executable pending gate
to account for local-only commits, required consumers and existing worktree code before publication.
Framework work item 1209 owns the cross-package recovery.

## Original code audit (before implementation)

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

- [x] Clean local-only product commit is rejected; pushed code passes.
- [x] A moved remote with a stale tracking ref is rejected; pending source cannot be allowed away.
- [x] Skills reviewed independently; installed and bundled orchestrator copies agree.
- [x] Bundle hashes/content pins, coredoc, tests/build and release artifacts agree.

## Receipts

- Nine isolated Git-fixture tests exercise pending files, local-only commits, live remote refs,
  nested untracked code, rename destinations and attempts to allow pending source away.
  They make no external network requests.

## Completion report

Completed 2026-11-14. Published AbstractSkill 0.3.12 includes the bundled release procedures and
`release/scripts/release_pending_gate.py`, tests, revision 2026.11.13 content/hash pins and the
package agent guide. Independent review found and resolved two false-approval cases before the
release. Installed abstract-release and the bundled copy agree; installed release resolves to the
bundled procedure. No release-gate exception was added.

Validation and publication:
- Nine guard regressions pass, including the stale-tracking-ref/live-remote negative controls.
- Full local release gate: 11 runnable jobs passed on source 5ccbbf1.
- [PR 9](https://github.com/lpalbou/AbstractSkill/pull/9) merged to
  `eed7ccd10d78433c92d4791401e85adc3c1973c5`; exact-main
  [CI 43502051822](https://github.com/lpalbou/AbstractSkill/actions/runs/43502051822) passed.
- [Release 43502223686](https://github.com/lpalbou/AbstractSkill/actions/runs/43502223686)
  passed; [0.3.12 is visible on PyPI](https://pypi.org/project/abstractskill/0.3.12/).

ADR impact: no new policy; the procedures implement the existing operator release/main rules,
Framework ADRs 0050/0051 and completed item 1131. Cross-package release completion remains owned
by Framework 1209 and is not implied by this package closure. No new residual code work was
identified. This receipt changes backlog documentation only and needs no new package artifact.

Original path: `docs/backlog/planned/0009_release_scope_and_live_main_completion.md`.
Final path: `docs/backlog/completed/0009_release_scope_and_live_main_completion.md`.
