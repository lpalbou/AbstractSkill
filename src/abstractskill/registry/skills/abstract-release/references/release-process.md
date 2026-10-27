# Release Process

The full procedure for an AbstractFramework release wave. `SKILL.md` is the short version; this
page carries the detail, the recipes and the pitfalls. Per-package facts (version source, trigger,
environment) live in `package-inventory.md`.

## 1. Plan

1. Fetch tags in each repository (`git -C <repo> fetch --tags`), then run the planner from any
   directory:
   `python3 "$SKILL_DIR/scripts/abstract_release_plan.py" "$AF_ROOT" --registry --json -o "$AF_ROOT/untracked/release-plan.json"`
   and its Markdown form for reading.
2. Treat `release_wave` as the queue. `changed: true` rows are release candidates, with their
   reasons (uncommitted changes, commits since the last release tag, an untagged version, a version
   missing from its registry); "floor review only" rows are downstream packages to check, not
   necessarily to release. A committed but unpublished version is a candidate even with a clean
   tree.
3. Read `changes_outside_packages` (repository-root files such as AbstractUIC's `package.json`
   belong to a release you assign by hand) and `inventory_gaps`: a package on disk that
   `scripts/lib/packages.txt` does not list will be missed by the workspace scripts (clone, build,
   status). Report it; fix the inventory in the root repository when that is in scope.
4. For each package, classify the dirty files: release scope (ship in this wave), operator work in
   progress (leave alone, never stage), generated noise. Ask when unsure.
5. Decide the target version per package (patch for fixes, minor for new capabilities). Check the
   target is not already published (`pip index versions <name>`, `npm view <name> versions`).

Release by published dependency floors, not by local workspace availability. A package that passes
its tests against an editable sibling can still fail in CI, which installs the published floor.

## 2. Release order

`ADR-0034` in the root repository sets the rule (release tier by tier, never above a lower
published floor; registry visibility is the gate) and names `scripts/lib/packages.txt` as
authoritative where it is more precise than the ADR's own list. Follow the inventory's tiers
(restated in `package-inventory.md`): the ADR's "Standard Order" list predates them (it puts
AbstractCore and AbstractRuntime in one tier and the npm UI repositories after the root).

1. Tier 0, independent: `abstractvoice`, `abstractvision`, `abstractmusic`, `abstractcamera`,
   `abstractskill`, and the AbstractUIC npm packages. They can go in parallel.
2. `abstractsemantics`, `abstractmemory`.
3. `abstractcore` (depends on the media plugins and `abstract3d`).
4. `abstractruntime`.
5. `abstractagent`.
6. `abstractgateway`.
7. Apps: `abstractassistant`, `abstractcode`, `abstractobserver`, `abstractentity`,
   `abstractflow`, `abstractcontinuum`, `abstractnote`. npm apps go after the AbstractUIC versions
   they pin are visible on npm.
8. Root `abstractframework`, its install manifest and installers.

Avoid needing an AbstractCore release in the middle of a wave: propagating a Core floor upward is
the slow path (runtime, agent, gateway, apps, root). When a Core change is not essential to the
wave, file a backlog item for the next wave instead (the 2026-10-27 wave deferred its Core voice
work this way, as AbstractCore backlog 0857).

## 3. Per-package loop

For each package of the wave, lowest first:

1. **Branch.** `git switch -c release/<package>-X.Y.Z` (or the feature branch the work is on). If
   the checkout holds someone else's uncommitted work, create a worktree in a scratch directory
   (`git worktree add <scratch>/<package> -b <branch> origin/main`) instead of touching it.
2. **Backlog.** The work has a `backlog` item in this package. Close it with evidence (commands
   run, results, PR and run links). A rule that should bind later work becomes an ADR (example:
   AbstractRuntime ADR 0008 and AbstractGateway ADR 0001, no direct lower-level imports; a missing
   capability is surfaced by the runtime, never a reason to import a lower package).
3. **Version and changelog.** Bump the version source(s) named in `package-inventory.md`. Fold
   `Unreleased` into `## [X.Y.Z] - YYYY-MM-DD`; one dated section per released version. Keep the
   changelog user-facing: what changed, who is affected, migration notes. Root-cause narratives
   stay in backlog. Reference backlog ids briefly where useful (`Backlog: 0139`).
4. **Docs.** Run `coredoc`'s release checklist: version source, README (version and registry
   badges, install snippet, what's-new pointer), package metadata (pyproject `[project]`,
   package.json), llms files regenerated with the package's generator and committed, docs index.
5. **Tests.** Run the package's suite. Then the end-to-end proof (section 4).
6. **Adversarial review.** Before merge, a reviewer that did not write the change reads the diff
   read-only and looks for what breaks: isolation between users or accounts, double work (weights
   loaded twice), overwritten routes, limits that disagree with the docs, missing skip guards for
   CI. Fix confirmed findings, re-run the proofs, note the findings in the PR. Findings this caught
   in practice: one account seeing another account's voices, weights loaded twice, a route
   overwritten by a later registration, a 10 MB cap in code against 25 MB in the docs.
7. **PR and CI.** Open the PR; wait for checks; merge only when the guard prints exactly `pass`:
   `gh pr checks <N> | awk -F'\t' '{print $2}' | sort -u`. A `skipping` line needs a reason
   (a path filter, a platform job); `fail` or `pending` means stop.
8. **Merge.** Run `gh pr merge <N> --merge` as its own command. Never chain it after or before
   other commands that would run on a failed merge. Then `gh pr view <N> --json state,mergeCommit`
   and confirm `MERGED`.
9. **Publish.** Per the package's row in `package-inventory.md`, in this order:
   - Check the environment's deployment policy admits the ref you publish from:
     `gh api repos/lpalbou/<Repo>/environments/<env>/deployment-branch-policies --jq '.branch_policies[]|"\(.type):\(.name)"'`.
     A tag-triggered run against an environment that allows only `main` is refused at the publish
     job after the build has passed. Either dispatch from main instead or ask the operator to add
     the tag policy (a repository-settings change).
   - `git switch main && git pull --ff-only`; `git rev-parse HEAD` must equal the PR's
     `mergeCommit.oid` (`gh pr view <N> --json mergeCommit`).
   - Tag push: `git tag -a vX.Y.Z -m "<package> X.Y.Z"` and `git push origin vX.Y.Z`.
   - workflow_dispatch: `gh workflow run release.yml --ref main` with exactly the inputs that
     workflow declares (the dispatch table in `package-inventory.md`; gh refuses unknown inputs).
     The run validates, publishes and creates the tag.
10. **Follow the run.** `gh run list --workflow release.yml --branch vX.Y.Z -L 1` (tag push) or
    `--event workflow_dispatch -L 1` (dispatch; check the run's head SHA), then
    `gh run watch <id> --exit-status`. On failure, read the failing job
    (`gh run view <id> --log-failed`) before re-running anything.
11. **Visibility.** `pypi_visibility_gate.py --wait 900 <name>==X.Y.Z` (PyPI) or
    `npm:@abstractframework/<pkg>==X.Y.Z` (npm). The gate checks the index pip and npm resolve
    from, not only the project page.
12. **Floors.** For each dependent in `dependency_floor_reviews`, raise the floor (or confirm the
    old one is still right and say why), update the tests that pin floors, refresh lockfiles,
    rerun the planner, continue.

Do not publish a higher package until every lower version it needs is visible on its registry and
the lower package's release run is green for the released commit.

## 4. End-to-end proofs

Mocks do not catch what breaks releases. Before merge:

- **Engines (voice, vision, music, core providers):** load the real weights on this machine and
  run the changed path end to end (generate, transcribe, clone). Models are loaded and warmed in
  the loading phase, never on the first request; a proof that only works on a second call is a
  failure. Tests that need torch, transformers or a downloaded model are skip-guarded for CI,
  which has none of them.
- **Gateway routes:** start a scratch gateway with its own data dir and token, and drive it over
  HTTP:

```bash
SCRATCH=$(mktemp -d); mkdir -p "$SCRATCH/home"
TOKEN=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
HOME="$SCRATCH/home" ABSTRACTGATEWAY_AUTH_TOKEN="$TOKEN" \
  abstractgateway serve --no-tray --no-runner --host 127.0.0.1 --port 18080 \
  --data-dir "$SCRATCH/data" &
GW_PID=$!
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:18080/api/health   # 200 within seconds
# ... drive the changed routes over HTTP ...
kill "$GW_PID"
```

  `--no-runner` is split mode: the gateway serves the HTTP API only and forwards `/v1` (runs, the
  model, mail, feeds, push) to `abstractgateway runner --data-dir "$SCRATCH/data"`, which you
  start next to it with the same environment when the change touches those routes. The gateway
  refuses a short or guessable token, and without `--host 127.0.0.1` it can bind
  0.0.0.0, where the weak-token refusal applies. The redirected `HOME` keeps the machine's own
  gateway pointer (`~/.abstractframework/gateway.json`) and voice store untouched. For multi-user
  routes add `ABSTRACTGATEWAY_USER_AUTH=1` to the same command.

  Use the default configuration (no extra keys in the shell, a neutral working directory) unless
  the change is about configuration, so the proof matches what users run.

## 5. Changelog, llms, backlog and ADR duties

- One dated `CHANGELOG.md` section per released version; `Unreleased` folded at release.
- `llms.txt` and `llms-full.txt` regenerated in the same change as the docs, with the package's
  generator (named in `package-inventory.md`), and committed. Some generators have `--check`.
- The package's backlog item closed with evidence; follow-ups filed as new items (proposed or
  planned) rather than left in prose.
- A durable rule discovered in the wave becomes an ADR in the package (or the root repository when
  it spans packages), linked from the backlog item.
- The root backlog gets one item for the wave (what was released, in which order, what was
  deferred).

## 6. Root `abstractframework` and partial releases

Release the root last. Before it:

- root `pyproject.toml` exact pins match the released versions;
- `abstractframework.RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS` and `CRATE_RELEASE_VERSIONS` match;
- `docs/installers/install-manifest.json`, `scripts/install.sh` (`AF_GATEWAY_PIN_DEFAULT`,
  `AF_FRAMEWORK_VERSION`, `AF_PY_MATRIX`, `AF_NPM_APPS`) and `scripts/install.ps1` agree
  (`scripts/tests/test_inventory.sh` checks this);
- install docs and app-facing auth and default examples describe the released matrix.

If the approved wave stops before the root, do the drift check anyway and either release the root
in the same wave or file a backlog item. Never report that `pip install abstractframework[...]`
delivers a lower-package change while the root pins still point at the old matrix.

The root repository's `main` can be diverged from `origin` (local release commits not yet pushed)
and can hold the operator's uncommitted changes. Do not rebase it, do not push it, and commit only
your own files.

## 7. Approval packet

Before any irreversible action (push, tag, dispatch, publish, merge), present: package, target
version, repository path, current commit and branch, the registry and workflow, the dirty-file
classification, the floor changes it triggers, and the plan JSON path. If the commit or the dirty
state changes afterwards, regenerate the plan before acting.

## 8. Stop conditions

Stop the wave and report the blocker when:

- a lower package version is not visible on its registry, or its release run is red or unknown;
- a target package has uncommitted release-scope changes;
- a floor or exact pin still points below a just-released lower version;
- a pin test (install profiles, runtime floor constant) disagrees with the new floor;
- root pins, `RELEASE_VERSIONS`, install manifest or installers disagree with the released matrix
  and the report would claim users get the change;
- package metadata, changelog, docs or release notes disagree;
- the release workflow, its environment policy, or the publish destination is unclear;
- the version source is unclear or the target version already exists.

## 9. Pitfalls seen in practice

- **Pin tests block floor bumps.** A test that pins dependency floors literally (AbstractGateway
  `tests/test_gateway_install_profiles.py`) fails the moment a floor moves. Update it in the same
  change as the floor.
- **Cross-package floor ceilings.** AbstractGateway's AbstractVoice floor must not exceed
  AbstractCore's own AbstractVoice floor (the gateway test enforces it). When users need a newer
  AbstractVoice than Core declares, document "install the latest AbstractVoice" rather than
  pinning it in the gateway, or release Core first.
- **Runtime floor constant.** `abstractgateway.live_deltas.ABSTRACTRUNTIME_FLOOR` must equal the
  gateway's pyproject AbstractRuntime floor; it drives the startup "runtime too old" check.
- **Version files.** AbstractVoice reads its version from `abstractvoice/_version.py`; packages
  with two version locations (AbstractGateway, AbstractNote) must agree in both. Never write a
  version file with a tool that truncates before reading it back.
- **Registry lag.** A version can be on the project page before pip or npm resolves it. Wait with
  the visibility gate before raising a floor.
- **Stale local venvs.** Local environments carry older siblings (an old `abstractagent`, no
  `abstractflow`). "Fails locally" is not "fails in CI"; classify each failure.
- **npm lockfiles.** Apps that pin `@abstractframework/ui-kit` fail `npm run check:lock` until the
  pinned version is on npm. After the publish: `npm install`, commit the lockfile, then release.
  AbstractUIC's root `package-lock.json` must match the per-package versions
  (`npm install --package-lock-only`).
- **Environment policies.** A tag-push release needs the publishing environment to admit the tag
  pattern. AbstractRuntime's `pypi` environment gained its `v*.*.*` tag policy on 2026-10-27; see
  `package-inventory.md` for the policies observed then.
- **Chained merges.** Never chain `gh pr merge` with commands that would still run when the
  merge fails (a tag, a push, a dispatch). Run it alone and check the PR state afterwards.
- **Someone else's work.** Operator checkouts hold uncommitted work; never stage it. Use a
  scratch worktree when you need a clean tree.
