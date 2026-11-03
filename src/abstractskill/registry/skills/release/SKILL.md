---
name: release
description: Prepare, validate, and execute software releases, including version bumps, changelog and release notes, user-facing documentation updates via coredoc, test/build gates, CI/CD readiness via cicd, tag or workflow dispatch, package publishing, docs deployment, and post-release verification. Use when an agent needs to cut, stage, publish, rehearse, trigger, or audit a repository release. For a release wave across many dependent packages, the AbstractFramework `abstract-release` skill orchestrates and uses this one per package.
---

# Release

Use this skill to move a repository from completed work to a traceable, validated, published
release. The release process should be explicit, reproducible, and boring: version is clear,
documentation matches the shipped behavior, tests and builds pass, CI/CD is ready, and the exact
tag or workflow run is auditable.

## Start With The Right Pass

- Inspect the repository before changing release state. Check package manifests, lockfiles,
  changelog, docs, release docs, CI/CD workflows, tests, current branch, remotes, tags, and the full
  `git status --short` output.
- If the repo already documents a release path, follow it unless it is unsafe, stale, or missing a
  required gate.
- If user-facing docs, changelog, migration notes, troubleshooting, or `llms.txt` files need work,
  use the `coredoc` skill.
- If workflows, publish jobs, environments, registry trust, docs deployment, or package publishing
  are missing or suspect, use the `cicd` skill before releasing.
- If release work closes backlog items, creates follow-up work, or changes durable policy, use
  backlog or ADRs when available.
- For an existing healthy release pipeline, prefer operating it over redesigning it. Keep local
  preflight proportional and let the remote workflow enforce its release gates.

## Apply The Operating Rules

- Never make a silent release. State the target version, release type, target commit/ref, publish
  destinations, and trigger path before pushing tags or dispatching publishing workflows.
- Before choosing or bumping a version, check whether package metadata was already bumped and not
  yet published. If the current metadata version has no matching tag or registry release, use that
  pending version unless the user explicitly asks to change it.
- A real release must publish a package version that is new to the target registries unless the
  repo's release model explicitly allows rebuild-only artifact releases.
- Keep version sources consistent: package metadata, lockfiles, docs, changelog, generated
  package manifests, release notes, and tags must agree.
- Keep `CHANGELOG.md` user-facing. It should describe what changed, who is affected, and migration
  or compatibility notes. Do not put root-cause narratives or internal repair history there.
- Update core docs before release when behavior, install commands, API/CLI surface, configuration,
  troubleshooting, deployment, or support boundaries changed.
- Regenerate or repair `llms.txt` and `llms-full.txt` when release-visible docs changed.
- Run the repo's relevant tests, linters, builds, package checks, and docs build before creating a
  release tag from local commits.
- Prefer a non-publishing rehearsal or dry run when the pipeline supports it, unless the user
  explicitly asked for a real publish.
- Do not downgrade a requested real publish to a rehearsal without saying so.
- Never publish a half release. Before tagging, pushing, or dispatching a real publish, classify
  every modified, deleted, staged, and untracked file. Any release-scope file must be committed and
  pushed, or explicitly removed from release scope, before publishing.
- Do not treat unrelated pending local changes as a blocker for triggering a release from an
  existing remote ref only after classification proves they are unrelated. Pending local changes
  matter when the release must include them, when they touch code, tests, docs, package metadata,
  workflows, release notes, generated indexes, or when the agent is about to commit, tag, or push from
  the local checkout.
- Push release commits before pushing tags. A tag should point at the exact commit whose docs,
  changelog, tests, and version metadata were validated.
- Fail loudly on version mismatch, missing changelog entry, missing docs update, failed tests,
  duplicate registry version, ambiguous target ref, or uncertain publish destination.

## CI Is Green Before It Is Pushed

Why: one release wave (2026-11-03) produced 22 failed CI runs in 24 hours. 10 were red by design:
branches that needed an unpublished dependency, pushed again and again. 7 were red mains, all flaky
timing tests. A CI failure must be the exception, never the normal path (AbstractFramework ADR 0050).

- **Gate every push.** Before ANY push, run the repository's local CI gate when it has one. In
  AbstractFramework this is the root `scripts/ci_local.sh <repo>`:
  - it merges the commit into a freshly fetched `origin/main`;
  - it runs every job of the workflows in a fresh environment installed from the registries;
  - its options are `--job <name>`, `--allow-skipped`, `--release-tag vX.Y.Z` and `--no-merge`.

  Otherwise run what the workflows run, read from `.github/workflows/*.yml`:
  - every step of every job of the PR and push-to-main workflows (build, lint, type-check, test, pack);
  - the push-to-main matrix;
  - a fresh venv per Python version, installed with the job's own install line;
  - scratch `HOME`, and pytest's temporary files under scratch.

  Push only on green. Report jobs that cannot run on this machine as skipped, never as green. Put
  the commands and their results in the PR body.
- **Never open a PR that is red by design.** If its CI installs a version that is not on its registry yet,
  the branch stays local until that version is visible. Push to a branch whose last run is red
  only with the fix for that failure.
- **Release branches resolve dependencies from the registry**, not from editable sibling checkouts.
  Before a release PR, also run the release workflow's own validate / build / sdist / test-the-wheel
  steps locally: they otherwise run only on the tag.
- **A red main is an incident.** Whoever merged fixes or reverts it within the hour and tells the
  maintainer. A re-run that passes is not a fix.
- **Flaky tests.**
  - No wall-clock assertion by default: timing bounds run only behind an explicit opt-in.
  - A real-server test waits until the server answers HTTP.
  - A test that flakes once is fixed or quarantined before the next merge.

## Release Workflow

1. Classify the release.
   Determine whether this is a rehearsal, prerelease, stable release, patch/hotfix, docs-only
   release, package publish, container publish, or existing workflow trigger.
   Also classify the worktree: no pending changes, release-scope pending changes, or unrelated
   pending changes.
2. Prepare release metadata.
   Resolve whether the current metadata version is an unpublished pending version or whether a new
   bump is required. Update package metadata and lockfiles, write the changelog entry, refresh
   release notes, and update docs with `coredoc` when user-visible behavior changed.
3. Validate locally where local validation is relevant.
   Run targeted tests first, then package builds, docs builds, and project-specific release checks,
   then the CI gate above. If a job cannot run locally, say so; delegate to CI only what the workflow
   runs and this machine cannot.
4. Check CI/CD readiness.
   Confirm the release workflow, publish destinations, environments, registry trust, docs deploy,
   and duplicate-version guards. Use `cicd` for repairs instead of embedding workflow design here.
5. Commit and push release changes when needed.
   Include version, changelog, docs, generated indexes, and lockfile changes in the release commit.
   Include release-relevant code, tests, integrations, workflow, and package changes. Do not
   include unrelated local edits.
6. Trigger the release.
   Use the repo's documented path: annotated tag push, `workflow_dispatch`, release branch, or
   project-specific command. Capture the tag, run URL, or release URL.
7. Verify after publish.
   Check GitHub Release, package registries, docs site, container tags, install commands, and any
   project-specific smoke tests. Record failed optional jobs as follow-up work.

## Use References Selectively

- Read `references/release-readiness.md` before preparing version, changelog, docs, or local
  validation changes.
- Read `references/execution-playbook.md` before pushing tags, dispatching workflows, publishing,
  or doing post-release verification.
- Run `scripts/release_pending_gate.py` or an equivalent manual `git status --short`
  classification before any real tag push or publish dispatch from a checkout with pending changes.
