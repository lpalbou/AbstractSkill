# Release readiness audit

An audit answers what is published, what changed, what must ship together, and what evidence is
still missing. It does not execute the wave. Preserve existing operator rules when refreshing
this skill from AbstractSkill: compare all files first, because the registry copy may be older
than the installed skill.

## Evidence to collect

- Record the observation time, local HEAD, branch and dirty state for every inventoried repo.
  Query live remote-main SHAs when available; cached `origin/main` alone cannot prove current
  ahead/behind. Do not pull or merge during the audit.
- Run the planner with registry checks. Compare published versions, matching release tags and
  the source changes beyond those tags. A published local version with newer source requires a
  fresh version; publication of the old version is not proof that HEAD shipped.
- Review open release-scope agent PRs as well as main. A clean checkout can still omit delivered
  work on a branch. Protect operator branches and do not infer ownership from branch names alone.
- Check CI for the proposed commit, not merely the latest successful run. Keep failed jobs,
  pending checks, environment failures and missing checks distinct. Inspect failed-job evidence
  before classifying a failure or recommending a rerun.
- Check root pins, installer matrix and per-package dependency floors. Internal consistency of
  the old root matrix does not show that it delivers the new capabilities.
- Reconcile backlog claims against code, completed records, registry data and CI. Count lifecycle
  files separately from unique tickets; planned/completed duplicates and old overview text are
  not reliable estimates of remaining work.

## Check the artifacts users install

Local packs, editable siblings and path dependencies can hide missing published APIs. For a
consumer using new shared UI exports, perform a clean source build in a temporary directory with
dependencies resolved from the registry. A version-only lockfile check can pass while the build
fails because a locally packed dependency reused an already-published version number.

Inspect planner `inventory_gaps` even when `deps.sh check` succeeds. A newly added public crate
can be absent from the inventory and release workflow. Cargo `path` plus `version` dependencies
must resolve from crates.io when packaged: release and verify the new lower crate before the
dependent package's `cargo publish --dry-run` verification job. Check its trusted publisher and
the workflow graph; adding a late publish job after verification does not solve this dependency.

Run applicable changelog fragment validation as a read-only check. Do not assemble fragments or
bump versions during an audit. A malformed fragment can block release preparation even when a
previous remote commit passed CI.

## Verdict and sequencing

Separate observed defects, missing required proof and later product work. A partial consumer
migration is a foundation delivered with integration pending, not a complete feature. Security
guards, registry-resolvable dependencies, required concurrency/isolation evidence and exact-commit
CI are release gates when applicable; unrelated proposals do not all become blockers.

Return a per-package release/skip/floor-review decision, proposed fresh versions (subject to a
new registry check), dependency order, and exit criteria. Give effort ranges as estimates with
assumptions, never promise a date without evidence. Preserve recorded release-scope obligations;
do not silently defer already-delivered main changes to manufacture a smaller green wave.
