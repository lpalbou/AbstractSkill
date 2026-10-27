# Package Discovery

`scripts/abstract_release_plan.py` builds a deterministic, read-only picture of the workspace. Run
it before the wave, after every release, and after every floor bump.

```bash
python3 "$SKILL_DIR/scripts/abstract_release_plan.py" "$AF_ROOT" --registry
python3 "$SKILL_DIR/scripts/abstract_release_plan.py" "$AF_ROOT" --registry --json -o "$AF_ROOT/untracked/release-plan.json"
```

Without a path it uses `ABSTRACTFRAMEWORK_ROOT`, else the nearest ancestor of the current directory
that holds `scripts/lib/packages.txt`, and stops with an error when there is none (it never walks
an arbitrary directory unless you pass it explicitly). It needs Python 3.11+ (tomllib) or the
`tomli` backport.

## Release signals

A package is **changed** (a release candidate) when any of these holds:

- uncommitted changes in its directory (`git status`);
- commits touching its directory since its last release tag (`git describe --match 'v*'`; a
  package in a sub-directory with its own tag family, such as AbstractCode's `web-v*`, uses it).
  Tags are read locally: run `git fetch --tags` in each repository first, or a release a workflow
  tagged remotely shows as untagged;
- for a package at its repository root, no local tag `v<version>`;
- with `--registry`, its local version is missing from PyPI, npm or crates.io (a 404; a network
  error leaves it unknown, never "unpublished").

Every package downstream of a changed package joins the wave as "floor review only".

## How it finds packages

- **With the inventory** (`scripts/lib/packages.txt`, the list the workspace scripts read): one
  package per row, read from `<repo>/<path>` (`pyproject.toml`, `package.json` or `Cargo.toml`).
  Scratch copies elsewhere in the workspace (worktrees and audits under `untracked/`, release
  checkouts) are never mistaken for the real package.
- **Without the inventory**: a filesystem walk that skips `untracked/`, virtualenvs,
  `node_modules`, `site-packages`, build output and `*-backup` / `*-gh-pages` folders, plus the
  local experiment projects (`abstractaudio`, `abstractsound`, `abstractvideo`,
  `abstractcognition`, `abstractgeometry`, `abstractspatial`). Two packages with the same name stop
  the run with both paths listed.

The root meta-package's `NPM_RELEASE_VERSIONS` and `CRATE_RELEASE_VERSIONS` pins count as
dependency edges, so an app or crate release reaches the root's floor review.

For each package it reads the version (static, or the setuptools `attr` the pyproject points to),
the internal dependencies (Python `dependencies` and extras, npm dependency groups, Cargo
`[dependencies]`), and `git status` for the package directory. Changes inside a nested package's
directory belong to that package (AbstractUIC's packages, the gateway's `console-tui` crate,
AbstractNote's `web` app, the sibling repositories under the root).

Vite source aliases into the AbstractUIC checkout are not in any manifest. With the inventory they
come from its `alias` edges (verified by `./scripts/deps.sh check`); without it, from a text scan
of the package sources for sibling npm package names, which can over-report.

## Output

The Markdown is for reading; the JSON is for follow-up checks and release logs.

- `ordered_packages`: every package in dependency order (ties broken by the ADR-0034 tier rank).
- `release_wave`: changed packages (`changed: true`, with the reasons) plus every package
  downstream of one (`floor review only`).
- `dependency_floor_reviews`: each internal requirement inside the wave, with the declared range
  and the lower package's local version: raise or confirm it after the lower publish is visible.
- `profile_pin_reviews`: the root pins (`pyproject.toml` exact pins, `RELEASE_VERSIONS`,
  `NPM_RELEASE_VERSIONS`, `CRATE_RELEASE_VERSIONS`) against local versions; `drift` means the root
  profile would not deliver the local version.
- `changes_outside_packages`: uncommitted changes in a package repository that no package
  directory owns (for example AbstractUIC's root `package.json`, which names its release tag, and
  its lockfile). Assign them to a release by hand.
- `inventory_gaps`: packages the workspace scripts would miss: `repo_not_in_inventory` (a sibling
  AbstractFramework repository with no row), `package_not_in_inventory` (a public manifest tracked
  in a listed repository, outside tests, fixtures, examples and docs), `not_cloned`,
  `name_mismatch`.
