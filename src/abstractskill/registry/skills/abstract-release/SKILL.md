---
name: abstract-release
description: Plan and run an AbstractFramework release wave across its packages in dependency order. Covers which packages changed, the release order, the per-package mechanics (tag push or workflow_dispatch, the PyPI/npm/crates.io GitHub environments), the gates (adversarial review before merge, real-weights or real-gateway end-to-end checks, merge only on all-green, registry visibility, dependency-floor propagation with the install-profile pin tests), and the final report. Use when releasing one or more AbstractFramework packages, raising inter-package floors, publishing the root `abstractframework` profile, or auditing whether a release wave is complete. For a single package with no dependents, the package-level `release` skill is enough.
---

# Abstract Release

AbstractFramework contains Python packages on PyPI, npm packages and apps, and Rust crates on
crates.io; `./scripts/deps.sh` lists the current workspace inventory. A release
wave publishes the changed ones from the bottom of the dependency graph upward, so every package
a parent depends on is already published, green, and visible on its registry before the parent
raises its floor and publishes.

This skill orchestrates the wave. Inside each package, use the `release` skill (version, changelog,
tag, publish), `coredoc` (README, docs, llms files, version source), `backlog` (the work item and
its evidence) and `adr` (durable rules). This skill adds what only shows up across packages: the
order, the gates between packages, floor propagation, and the root profile.

## Read-only readiness audits

When asked whether to release, produce evidence and a recommendation without executing a release.
The checkout synchronization, checkpoint commits, branch integration and final build rules below
apply when release execution is authorized; an audit does not authorize pulling, merging, staging
operator edits, dispatching workflows, rerunning CI, or publishing. Read remote refs and CI through
read-only GitHub APIs when needed and label cached tracking refs explicitly.

Read `references/readiness-audit.md` for the audit evidence contract, registry-only build checks,
missing-package discovery and the distinction between a release blocker and later roadmap work.

## Non-negotiable rules (operator, 2026-10-28; release execution)

1. **A release ships EVERY pending change of the work in scope.** Before cutting any package: every
   pending change ON `main` (local unpushed commits, uncommitted edits: an operator's edit is committed
   as `checkpoint` after a secret scan, never left aside) and every branch THE AGENTS CREATED to complete
   a task is merged into an up-to-date `main`, tested and released. NOT every branch: the operator's own
   branches (e.g. a private memory-block branch in AbstractCore) are theirs, are never merged, pushed or
   touched unless the operator says so; when in doubt about a branch's owner, ask. "Held because the operator has edits" or "held because local main has
   unpushed commits" is forbidden: fix the build, merge with origin, release. The only reasons to stop
   are secrets in the tree or a failing test that cannot be fixed without a decision: then ask, with
   the exact file and failure, and keep every other package moving.
2. **Always pull before starting any work**, in every repository, every time: `git -C <repo> fetch
   origin && git -C <repo> pull --ff-only origin main` before cutting a branch or a worktree; cut
   worktrees from `origin/main`. Pull the local `main` again right after every merge on GitHub.
3. **A release means every pending change has been merged into an up-to-date `main`.** The wave ends
   only when `./scripts/status.sh` shows every repository on `main`, clean, 0 ahead, 0 behind, and
   `./scripts/build.sh` passes from those checkouts. A checkout left on a feature branch, a merged PR
   not pulled, or a repo "N ahead" is a release defect, reported as such, not as a note.
4. A worker that cannot run `git merge` or `git rebase` or `git switch` asks the coordinator to do it
   immediately; it never leaves the branch unmerged and moves on.

## CI is green before it is pushed (AbstractFramework ADR 0050)

Why: on 2026-11-03, 22 CI runs failed in 24 hours. Ten were red by design: a branch that needed an
unpublished sibling, pushed two or three times anyway. Seven were red MAINs, all of them flaky timing
tests. The operator got ten failure e-mails overnight. A CI failure is the exception, never the normal path.

1. **The gate runs before ANY push.** Run root `scripts/ci_local.sh <repo>` (`docs/ci-local.md`). It
   merges the commit into a freshly fetched `origin/main`, runs every job of the repo's workflows
   (as the push to main where a workflow has one, so main's full matrix), each in a fresh environment
   installed from the registries, and exits 0 only when every runnable job passed. Jobs it cannot run
   here (Windows, Linux sandbox) are printed as SKIPPED and fail the gate unless `--allow-skipped`. Where
   the gate is absent, run the workflows' job commands yourself: every step of every job (build,
   lint, type-check, test, pack, not only the tests), the main-push Python matrix (main often tests
   more versions than a PR), a fresh venv per version, scratch `HOME`, `pytest --basetemp=<scratch>`.
   Push only on green. Put the commands and their results in the PR body.
2. **A PR is never red by design.** A branch whose CI needs a version not yet on its registry (a
   sibling symbol, a raised floor, `pip install "x>=N"`) stays LOCAL until
   `pypi_visibility_gate.py` says that version is visible. No PR is opened and nothing is pushed
   until then. A branch whose last run is red is pushed again only with the fix for that failure
   (`gh run list --branch <b> -L 1` first).
3. **Release branches are tested as CI installs them.** The gate builds every job's environment
   fresh from the registries, so siblings come at their published versions, never from editable
   checkouts, and a branch that needs an unpublished sibling fails it. In the manual fallback, use a
   fresh venv the same way.
4. **Release PRs also run the release workflow's own validate / build / sdist / wheel-test steps
   locally** before the PR (`scripts/ci_local.sh <repo> --release-tag vX.Y.Z`), because those jobs
   run only on the tag, when it is too late.
5. **A red main is an incident.** Whoever merged fixes or reverts it within the hour and tells the
   operator at once. Re-running until green is not a fix.
6. **Flaky tests.** No wall-clock assertion runs by default: timing bounds are opt-in (a
   `*_TIMING_STRICT=1` switch). A test of a real server waits until the server answers HTTP, never
   for a log line. A test that flaked once is fixed or quarantined, with a backlog item, before the
   next merge.

## Before you start

- Default to a read-only plan. Commits, pushes, tags, workflow dispatches, publishes, CI reruns and
  skipped gates need the operator's explicit approval (see the approval packet in
  `references/release-process.md`).
- Set the skill directory once; the scripts run from any working directory:

```bash
SKILL_DIR=~/.claude/skills/abstract-release        # or wherever this skill is installed
AF_ROOT=/path/to/abstractframework                 # the workspace root (holds scripts/lib/packages.txt)
git -C "$AF_ROOT/<repo>" fetch --tags      # per repository: the planner reads local release tags
python3 "$SKILL_DIR/scripts/abstract_release_plan.py" "$AF_ROOT" --registry
python3 "$SKILL_DIR/scripts/abstract_release_plan.py" "$AF_ROOT" --registry --json -o "$AF_ROOT/untracked/release-plan.json"
```

  Two packages may share a registry name across registries (AbstractAvatar's crate and Python
  package): the planner keys the crate as `<name>-crate`; a crate dependent's edge resolves to it.
  Without a path, the planner finds the workspace by walking up from the current directory
  (or reads `ABSTRACTFRAMEWORK_ROOT`). A package is in the wave when it has uncommitted changes,
  commits since its last release tag, a version with no tag, or (with `--registry`) a version not
  on its registry; packages downstream of one are added for a floor review only.
- Read `references/package-inventory.md` for the tiers and each package's version source,
  release trigger and registry environment. Read `references/release-process.md` before the first
  irreversible step.
- Operator checkouts can hold uncommitted work that is not yours. Never stage it, never rebase a
  diverged branch for the operator. When you need a clean tree, use a worktree in a scratch
  directory.

## The order

Release by published dependency floors, not by what happens to pass locally:

1. Independent lower packages: `abstractvoice`, `abstractvision`, `abstractmusic` (and the other
   tier-0 media plugins), `abstractskill`, `abstractavatar` (one repository, TWO packages: the
   crate `abstractavatar` on crates.io and the Python package `abstractavatar` on PyPI; the crate
   first: `abstracttui`'s `avatar` feature depends on it, and `abstractcore-console`,
   `abstractgateway-console` and `abstractcode` depend on `abstracttui` with that feature), and
   the AbstractUIC npm packages (`ui-kit`, `app-server`, `monitor-*`, `panel-chat`).
2. `abstractsemantics` and `abstractmemory` (AbstractMemory owns the memory graph).
3. `abstractcore`.
4. `abstractruntime`.
5. `abstractagent`.
6. `abstractgateway`.
7. Apps on the gateway: `abstractassistant`, `abstractcode`, `abstractobserver`, `abstractentity`,
   `abstractflow`, `abstractcontinuum`, `abstractnote` (Python on the gateway and AbstractMemory,
   plus its web app). AbstractAssistant is one repository with FOUR lanes: the Python package
   (PyPI, the desktop palette and the gateway seam), the web app (`web/`, `@abstractframework/assistant`,
   served by the gateway; not on npm yet), the iPhone app (`phone/iphone`, App Store / TestFlight
   through `scripts/release.py` and `scripts/upload-candidate.sh`, `iphone.yml`) and the watch app
   (`watch/apple`, `watch.yml`, `scripts/testflight.sh`). The registry wave releases the Python
   package; the Apple lanes release through App Store Connect with the operator's approval
   (`app-store` environment) and are reported as their own rows, never folded into the PyPI row.
8. Root `abstractframework`: pins, `RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS`,
   `CRATE_RELEASE_VERSIONS` (includes `abstractavatar` and `abstracttui`), install manifest,
   installers, install docs.
9. The website, last and gated: once the root profile is on PyPI, run the `abstractframework-website`
   skill — it updates the site branch locally (versions, install commands, new apps and
   capabilities, refreshed screenshots and llms mirrors), serves it locally and hands the operator
   the preview URL. The operator validates and pushes `gh-pages`; a wave never pushes the site.

The planner refines this from the real manifests: it skips packages with nothing to release and
adds every package downstream of a changed package for a floor review. `scripts/lib/packages.txt`
in the workspace is the inventory the workspace scripts use; the planner reports any package it
finds on disk that the inventory is missing.

## The per-package loop

Repeat for each package in the plan's `release_wave`, lowest order first.

1. **Work item.** Every change has a `backlog` item in its own package; close it with evidence.
   A rule that should outlive the task (for example "no direct lower-level imports; a missing
   capability is surfaced by the runtime") becomes an ADR.
2. **Version and docs.** Bump the package's version source (named per package in
   `references/package-inventory.md`; some packages keep it in two places that must agree). Fold
   `Unreleased` into one dated `CHANGELOG.md` section for the version. Run `coredoc`'s release
   checklist: version source, README badges and install snippets, package metadata, llms files
   regenerated with the package's generator and committed, backlog/ADR trace.
3. **Local proof.** Run the pre-push gate (`scripts/ci_local.sh <repo> --release-tag vX.Y.Z`, see "CI
   is green before it is pushed"). Then the package tests. For anything that touches an engine, run a real-weights
   end-to-end check on the machine, not a mock. For gateway routes, go through a scratch gateway
   over HTTP (recipe in `references/release-process.md`). A local failure can be the stale venv,
   not the code: CI installs from the published pins, so decide per failure whether it is a code
   bug or the environment (keys in the shell, CLIs on PATH, missing extras, older siblings).
4. **Adversarial review before merge.** A read-only reviewer that did not write the diff reviews
   it. Fix the confirmed findings, re-verify, and record what was found.
5. **Pull request, merge only on all-green.** Open it only after the gate passed, and only when every
   version its CI installs is already on its registry: otherwise the branch stays local. The PR body
   lists the gate's commands and results.

```bash
gh pr create --base main --head <branch> --title "<package> X.Y.Z: <summary>" --body-file <notes.md>
gh pr checks <N> --watch
gh pr checks <N> | awk -F'\t' '{print $2}' | sort -u     # must print exactly: pass
gh pr merge <N> --merge                                  # alone, never chained after other commands
gh pr view <N> --json state,mergeCommit                  # confirm MERGED before tagging
```

6. **Publish.** Read the package's row in `references/package-inventory.md` (trigger, dispatch
   inputs, environment policy) first. Then:
   - Confirm the publishing environment admits the ref you will publish from, or the publish job
     is refused after the build passed (a 404 means no policy: any ref may deploy):

```bash
gh api repos/lpalbou/<Repo>/environments/<pypi|npm|crates-io>/deployment-branch-policies \
  --jq '.branch_policies[]|"\(.type):\(.name)"'
```

   - Confirm you publish the merged commit:
     `git switch main && git pull --ff-only`, then `git rev-parse HEAD` must equal the PR's
     `mergeCommit.oid`.
   - Tag push (most packages; AbstractUIC tags its root `package.json` version, AbstractCode's
     web app tags `web-vX.Y.Z`):

```bash
git tag -a vX.Y.Z -m "<package> X.Y.Z" && git push origin vX.Y.Z
```

   - Or `workflow_dispatch` from main, with the inputs that workflow declares (the run builds,
     publishes and creates the tag; required where the environment admits only `main`, as for
     AbstractAssistant):

```bash
gh workflow run release.yml --ref main -f version=X.Y.Z                 # most Python packages
gh workflow run release.yml --ref main -f version=X.Y.Z -f publish=true \
  -f publish_confirmation=publish-<package>-X.Y.Z                       # AbstractRuntime, AbstractMusic
```

   - Follow the run: `gh run list --workflow release.yml --branch vX.Y.Z -L 1` for a tag push
     (`--event workflow_dispatch` for a dispatch), then `gh run watch <run-id> --exit-status`.
7. **Visibility gate.** The registry index lags the upload. Do not raise a floor upstream until
   the version resolves:

```bash
python3 "$SKILL_DIR/scripts/pypi_visibility_gate.py" --wait 900 abstractvoice==X.Y.Z
python3 "$SKILL_DIR/scripts/pypi_visibility_gate.py" --wait 900 npm:@abstractframework/ui-kit==X.Y.Z
python3 "$SKILL_DIR/scripts/pypi_visibility_gate.py" --wait 900 crates:abstractgateway-console==X.Y.Z
```

8. **Floor propagation.** Only after the visibility gate passed (a dependent's branch with the new floor
   stays local until then: its gate installs the new floor from the registry), raise the floor in each direct
   dependent the plan lists under
   `dependency_floor_reviews`. Update the tests that pin floors literally in the same change
   (for example AbstractGateway's `tests/test_gateway_install_profiles.py` and
   `live_deltas.ABSTRACTRUNTIME_FLOOR`), respect the cross-package floor rules in
   `references/package-inventory.md`, and refresh npm lockfiles after an AbstractUIC publish.
   Rerun the planner and continue with the updated wave.

## Gates (never skipped without the operator's approval)

0. The pre-push gate is green before every push; no PR is red by design; a red main is fixed or
   reverted within the hour (AbstractFramework ADR 0050).
1. Adversarial review of every diff before merge.
2. Real-weights (engines) or real-gateway (routes) end-to-end proof on the machine.
3. Merge only when every check is `pass`; check the PR state after merging.
4. A parent is released only after each lower version is visible on its registry and the lower
   package's release run is green.
5. Every dependent's floor or exact pin is raised or explicitly confirmed, with its pin tests.
6. One dated changelog section per released version; llms files regenerated; backlog item closed
   with evidence; durable rules recorded as ADRs.
7. No publish from a checkout with uncommitted release-scope changes.
8. Root `abstractframework` last, and only when its pins, `RELEASE_VERSIONS`, install manifest,
   installers and install docs match the released matrix. If the wave stops earlier, either
   release the root profile in the same approved wave or file a backlog item and say plainly that
   `pip install abstractframework[...]` still resolves the older matrix.

Stop and report on: an ambiguous version source, a duplicate target version, an unclear publish
destination, a red pre-push gate, a red main, a red or unknown check, a version not visible on its registry, or a floor that still
points below a just-released version.

## Final report

End the wave with this report (one row per package touched, including the ones you decided not
to release):

```markdown
# AbstractFramework release wave <date>

| Package | Released | Registry | Release run | Floors raised in dependents |
|---|---|---|---|---|
| abstractvoice | 0.19.1 (from 0.18.2) | PyPI, visible | <run URL>, green | abstractcore >=0.19.1 |
| ... | not released: <reason> | | | |

## New capabilities (per package, user-facing)
- abstractvoice 0.19.1: ...

## Gates
- Adversarial reviews: <package: findings fixed / none>
- End-to-end proofs: <package: what ran, on which weights or gateway>
- Root profile: released X.Y.Z | not released, backlog <id>, users of `abstractframework[...]` still get <old matrix>

## Remaining work and improvements
- <package>: <follow-up>, backlog <id>
- Process: <what slowed the wave, the fix proposed>
```

## Scripts

- `scripts/abstract_release_plan.py [ROOT] [--registry] [--json] [-o FILE]`: read-only
  inventory, dependency order, release signals per package, release wave, floor reviews, root pin
  drift (pyproject pins and `RELEASE_VERSIONS` / `NPM_RELEASE_VERSIONS` / `CRATE_RELEASE_VERSIONS`),
  changes outside any package, and packages missing from `scripts/lib/packages.txt`. Needs
  Python 3.11+ (or `tomli` installed).
- `scripts/pypi_visibility_gate.py SPEC... [--from-plan FILE] [--wait SECONDS]`: checks that each
  `name==version` (PyPI), `npm:@scope/name==version` or `crates:name==version` is installable from
  its registry; `--from-plan` checks the plan's changed packages; with `--wait` it polls until
  visible or the deadline passes. Exit code 0 only when all are visible. Python 3.9+.

## References

- `references/release-process.md`: the full process: order, per-package loop, gates in detail,
  the scratch-gateway recipe, changelog/llms/backlog/ADR duties, approval packet, stop conditions,
  partial releases, and the pitfalls seen in practice.
- `references/package-inventory.md`: the tiers, and per package its version source, release
  trigger, registry environment, llms generator, and package-specific rules.
- `references/package-discovery.md`: how the planner discovers packages and reads its output.

## Keep every checkout in step with GitHub (repo sync rule)

Observed 2026-10-27: several local `main` checkouts were dozens of commits behind their remotes
(abstractuic 86, the root 10) because PRs were merged on GitHub while nobody pulled the local
checkout, and new branches were then cut from the stale main. Rules, every time:

1. Before cutting a branch or a worktree: `git -C <repo> fetch origin && git -C <repo> pull --ff-only origin main`
   on the main checkout (a dirty checkout is left alone and reported; never stash someone else's work).
2. After merging a PR on GitHub: pull the local main checkout immediately (the merge watcher does it).
3. Worktrees are cut from `origin/main`, never from the local `main` ref.
4. A sweep before any release wave: for each repo, `rev-list --count main..origin/main` must be 0;
   `scripts/status.sh` at the root prints ahead/behind per repo.
5. A root `main` that diverged (local release commits made elsewhere) is merged, never rebased: the
   operator's commits keep their hashes; origin's pins and version win in conflicts, local docs and backlog
   additions are kept, duplicated release sections are dropped.

## Final gate: the local source build of the whole stack

After the root pins are released, run the operator's own developer path before the final report:
`./scripts/status.sh` (every repo on `main`, 0 behind, no checkout left on a feature branch by a worker)
and `./scripts/build.sh` (editable Python installs, every npm package built from local packs, every Rust
crate compiled tier by tier). A failure there is a release defect even when every registry install passes:
a crate that does not compile from a clean checkout, a pin that does not resolve locally, a checkout left
behind. Operator-modified files are reported, never built around: say which file fails and whose edit it is.

## Final report: the summary table, then "show me your work"

The per-package summary table (package | released | new capabilities | remaining work) is the right
visibility level and stays. It is NOT the report. For every track of the wave add a "show me your work"
section with exactly three parts, written for the operator who was not watching:

- **(a) What was tested:** the suites and counts per package, the end-to-end runs on real weights or a
  real gateway (what scenario, which model, which data), the mutation checks (which rule was removed and
  which test went red), the adversarial review rounds and verdicts, the conformance fixtures (how many,
  real vs synthetic).
- **(b) What it enables or fixes:** in the operator's words: the user-visible behaviour before and after,
  and which apps/clients actually consume it today versus which still have to migrate (name each client
  and its state: migrated / designed-for / untouched). Never present a served capability as integrated
  when no client reads it.
- **(c) Proofs:** numbers a human can read: latency and memory before/after, sizes, counts, run ids,
  PR links, registry versions, and one concrete example (a ledger, a run, a voice) walked end to end.

A track whose clients are not migrated is reported as "foundation released, integration pending" with the
migration list and an ETA, never folded into "done".

## Think like an architect before closing anything (operator, 2026-10-28)

Before a package is held, a track is called done, or a wave is closed, the coordinator (or its adversarial
reviewer) answers these questions in writing:

- What happens if I do not release all the pending changes I have been working on? What breaks for the
  person who installs or builds from source tomorrow?
- What happens if I do not release this package just yet? Which consumer is left on a stale floor?
- Did I fully implement AND reuse the functionality I just created in the consumers of that code?
  (A shared component in abstractuic or a gateway contract exists only when the apps consume it:
  AbstractCode, AbstractAssistant, AbstractObserver, AbstractContinuum, AbstractFlow, AbstractNote,
  the consoles.) List each consumer with migrated / pending.
- Is the result production-grade for a person, not only green for CI?

The goal is always a finished, production-grade solution that benefits from the change; the secondary goal
is the supervisor's visibility: a roadmap while work is ongoing, and at the end a report that shows the
work (what is new or fixed, what it enables now or later, why it is good). Keep it a dialogue: ask early
when a decision is genuinely the operator's, decide and say so when it is not.

## Backlog discipline for work left pending

When a task cannot be carried on now (time, credits, a blocker, a decision), write the backlog item
immediately, while the understanding is fresh: `proposed` when the need is likely, `planned` when it is
certain; it carries the analysis, the chosen route, the evidence so far and the open decision.
When an item is picked up later, start with an adversarial review of the item itself: is its knowledge
still current, is it still the best route (new research, superseded component, changed contract)?

## Changelog fragments (gateway, core, runtime; since 2026-10-29)

These repos no longer edit `CHANGELOG.md [Unreleased]` per PR. Each PR adds `changelog.d/<pr-or-slug>.md`; CI fails a PR that touches source without a fragment. At release time, before the version bump commit:

```
python scripts/changelog.py check            # every fragment well-formed
python scripts/changelog.py preview          # what the section will say
python scripts/changelog.py assemble X.Y.Z   # writes the [X.Y.Z] section, deletes the fragments
```

Commit the assembled section with the version bump. Never hand-edit `[Unreleased]` in these repos.

## A conflicting PR gets no CI run

GitHub creates `pull_request` runs from the merge ref; a PR whose `mergeStateStatus` is DIRTY has none, so pushes to it create no run and no error. Before pushing a fix: merge `origin/main` into the branch, then `gh pr view N --json mergeStateStatus` must say CLEAN/BLOCKED, never DIRTY.
