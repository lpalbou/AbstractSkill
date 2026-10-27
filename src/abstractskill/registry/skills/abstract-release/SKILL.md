---
name: abstract-release
description: Plan and run an AbstractFramework release wave across its packages in dependency order. Covers which packages changed, the release order, the per-package mechanics (tag push or workflow_dispatch, the PyPI/npm/crates.io GitHub environments), the gates (adversarial review before merge, real-weights or real-gateway end-to-end checks, merge only on all-green, registry visibility, dependency-floor propagation with the install-profile pin tests), and the final report. Use when releasing one or more AbstractFramework packages, raising inter-package floors, publishing the root `abstractframework` profile, or auditing whether a release wave is complete. For a single package with no dependents, the package-level `release` skill is enough.
---

# Abstract Release

AbstractFramework is 34 packages in 22 repositories on 2026-10-27 (Python on PyPI, npm packages
and apps, Rust crates on crates.io; `./scripts/deps.sh` in the workspace lists them). A release
wave publishes the changed ones from the bottom of the dependency graph upward, so every package
a parent depends on is already published, green, and visible on its registry before the parent
raises its floor and publishes.

This skill orchestrates the wave. Inside each package, use the `release` skill (version, changelog,
tag, publish), `coredoc` (README, docs, llms files, version source), `backlog` (the work item and
its evidence) and `adr` (durable rules). This skill adds what only shows up across packages: the
order, the gates between packages, floor propagation, and the root profile.

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
   tier-0 media plugins), `abstractskill`, and the AbstractUIC npm packages (`ui-kit`,
   `app-server`, `monitor-*`, `panel-chat`).
2. `abstractsemantics` and `abstractmemory` (AbstractMemory owns the memory graph).
3. `abstractcore`.
4. `abstractruntime`.
5. `abstractagent`.
6. `abstractgateway`.
7. Apps on the gateway: `abstractassistant`, `abstractcode`, `abstractobserver`, `abstractentity`,
   `abstractflow`, `abstractcontinuum`, `abstractnote` (Python on the gateway and AbstractMemory,
   plus its web app).
8. Root `abstractframework`: pins, `RELEASE_VERSIONS`, install manifest, installers, install docs.

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
3. **Local proof.** Run the package tests. For anything that touches an engine, run a real-weights
   end-to-end check on the machine, not a mock. For gateway routes, go through a scratch gateway
   over HTTP (recipe in `references/release-process.md`). A local failure can be the stale venv,
   not the code: CI installs from the published pins, so decide per failure whether it is a code
   bug or the environment (keys in the shell, CLIs on PATH, missing extras, older siblings).
4. **Adversarial review before merge.** A read-only reviewer that did not write the diff reviews
   it. Fix the confirmed findings, re-verify, and record what was found.
5. **Pull request, merge only on all-green.**

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

8. **Floor propagation.** Raise the floor in each direct dependent the plan lists under
   `dependency_floor_reviews`. Update the tests that pin floors literally in the same change
   (for example AbstractGateway's `tests/test_gateway_install_profiles.py` and
   `live_deltas.ABSTRACTRUNTIME_FLOOR`), respect the cross-package floor rules in
   `references/package-inventory.md`, and refresh npm lockfiles after an AbstractUIC publish.
   Rerun the planner and continue with the updated wave.

## Gates (never skipped without the operator's approval)

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
destination, a red or unknown check, a version not visible on its registry, or a floor that still
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
