# Package Inventory

What exists, in which order it releases, and how each package releases. The workspace's
`scripts/lib/packages.txt` is the machine-readable inventory (`./scripts/deps.sh` prints the tiers,
`./scripts/deps.sh check` verifies them against the real manifests, `./scripts/deps.sh rdeps <id>`
lists what must follow a bump). This page adds the release mechanics. Facts were read from the
repositories and their GitHub settings on 2026-10-27; re-check a row before relying on it for an
irreversible step.

## Tiers

Tier = dependency depth from `packages.txt`. A package releases only after every package it
depends on is published and visible.

| Tier | Python (PyPI) | npm | Rust (crates.io) |
|---|---|---|---|
| 0 | abstractskill, abstractsemantics, AbstractMemory, abstractvision, abstractvoice, abstractmusic, abstractcamera | ui-kit, app-server, monitor-flow, monitor-gpu, monitor-memory, monitor-active-memory | abstracttui |
| 1 | abstract3d (needs abstractvision) | panel-chat (peer of ui-kit) | abstracttui-graph, abstractcore-console, abstractcode (CLI) |
| 2 | abstractcore (needs voice, vision, music, 3d) | flow, observer, continuum, entity, code (web), note (web) | abstracttui-mermaid, abstractgateway-console |
| 3 | AbstractRuntime (needs core, memory, semantics) | | |
| 4 | abstractagent, abstractassistant | | |
| 5 | abstractgateway | | |
| 6 | abstractnote, abstractframework (root meta-package) | | |

Roles worth knowing when you order a wave:

- **AbstractMemory** owns the memory graph (temporal assertions, the graph store and its
  operations). AbstractRuntime, AbstractGateway and AbstractNote build on it, so a memory change
  can ripple to all three.
- **AbstractCore** depends on the media plugins (voice, vision, music, 3d). Avoid a Core release in
  the middle of a wave unless the change needs it; its floor propagation is the slow path.
- **AbstractGateway** is the one HTTP door; the apps are thin clients of it.
- **AbstractNote** is a notes app on the gateway: a Python package (`abstractnote`, depends on
  AbstractMemory, AbstractSemantics, AbstractRuntime and AbstractCore; reaches the gateway through
  its `gateway` extra) plus a web app (`@abstractframework/note`). The gateway imports
  `abstractnote` lazily as an optional seam, so it is not a gateway dependency; AbstractNote
  releases after the gateway it needs.
- **abstractframework** (root) pins exact versions of the released matrix and releases last.

Not released with the framework: the local test projects `abstractaudio`, `abstractsound`,
`abstractvideo`, `abstractcognition`, `abstractgeometry`, `abstractspatial` (the planner skips
them).

## Release mechanics per package

Trigger: **tag** = push `vX.Y.Z` (`release.yml` on tag push); **dispatch** = `gh workflow run
release.yml --ref main ...` with the inputs named in the row. Most Python workflows accept both:
dispatched with `-f version=X.Y.Z`, they build, publish and create the tag themselves (an
`ensure-tag` job), which also satisfies an environment that admits only `main`. Dispatch inputs
differ per workflow and gh refuses unknown inputs ("Unexpected inputs"), so read the row, and read
the publish jobs' `if:` conditions before dispatching a workflow the table does not cover.
Environment policy = the deployment branch/tag policy of the publishing environment: a tag-push
release needs a tag rule there.

| Dispatch inputs | Packages |
|---|---|
| `-f version=X.Y.Z` | abstractvoice, abstractvision, abstractcamera, abstractskill, abstractsemantics, AbstractMemory, abstractcore, abstractagent, abstractassistant, abstractgateway, abstractflow |
| `-f version=X.Y.Z -f publish=true -f publish_confirmation=publish-<package>-X.Y.Z` | AbstractRuntime, abstractmusic |
| `-f version=X.Y.Z` (`-f dry_run=true` rehearses) | abstractnote |
| `-f target=web` or `-f target=cli` (default `all`) | AbstractCode |
| `-f publish=true` | abstracttui (and its extension crates) |
| none | abstractuic, abstractobserver, abstractentity, abstractcontinuum, root abstractframework (check the workflow's publish conditions first) |
| none, and dispatch publishes nothing | abstract3d: publishes only from a `v*` tag |

### Python

| Package | Repo | Version source | Trigger | `pypi` env policy | llms generator | Notes |
|---|---|---|---|---|---|---|
| abstractvoice | lpalbou/AbstractVoice | `abstractvoice/_version.py` (single source; pyproject reads it) | tag | main, tag `v*.*.*` | none (edit by hand) | PR CI: tests 3.9-3.12, Qwen3-TTS/ASR transformers floor and latest, build, docs (10 checks). release.yml publishes to PyPI with trusted publishing, creates the GitHub release, deploys docs. |
| abstractvision | lpalbou/AbstractVision | `src/abstractvision/__init__.py` | tag | no restriction | `scripts/generate_llms_full.py` | |
| abstractmusic | lpalbou/AbstractMusic | `src/abstractmusic/_version.py` | tag or dispatch (`-f publish=true -f publish_confirmation=publish-abstractmusic-X.Y.Z`) | main, tag `v*.*.*` | none | |
| abstractcamera | lpalbou/AbstractCamera | `src/abstractcamera/__init__.py` | tag | main, tag `v*` | `scripts/generate_llms_full.py` | Ships a package agent skill (`skills/camera-piloting/`). |
| abstract3d | lpalbou/Abstract3D | `pyproject.toml` and `src/abstract3d/__init__.py` | tag `v*` only (the publish jobs run only on `refs/tags/v*`; a dispatch publishes nothing) | main, tag `v*` | none | AbstractCore depends on it: release before Core. |
| abstractskill | lpalbou/AbstractSkill | `pyproject.toml` and `src/abstractskill/__init__.py` | tag | main, tag `v*` | `scripts/generate_llms_full.py` | Shelf changes: `scripts/refresh_shelf.py`, bump `catalog.yaml` `version`, update the pins in `tests/test_bundled.py` and `tests/test_shelf.py`. |
| abstractsemantics | lpalbou/AbstractSemantics | `pyproject.toml` | tag | main, tag `v*.*.*` | `scripts/generate_llms_full.py` | |
| AbstractMemory | lpalbou/AbstractMemory | `pyproject.toml` | tag | main, tag `v*.*.*` | none | Memory graph owner. |
| abstractcore | lpalbou/AbstractCore | `abstractcore/utils/version.py` | tag | main, tag `v*.*.*` | `scripts/update_llms.py` | Also publishes the `abstractcore-console` crate and GHCR images. Ships `skills/abstractcore/`. |
| AbstractRuntime | lpalbou/AbstractRuntime | `pyproject.toml` | dispatch: `gh workflow run release.yml --ref main -f version=X.Y.Z -f publish=true -f publish_confirmation=publish-abstractruntime-X.Y.Z` (the run creates the tag); a tag push also works | main, tag `v*.*.*` (tag rule added 2026-10-27) | `scripts/generate_llms_full.py` (commit the output) | PR CI: 7 checks. |
| abstractagent | lpalbou/AbstractAgent | `pyproject.toml` | tag | main, tag `v*.*.*` | none | |
| abstractassistant | lpalbou/AbstractAssistant | `pyproject.toml` and `abstractassistant/_version.py` (a test keeps them equal) | dispatch: `gh workflow run release.yml --ref main -f version=X.Y.Z` (creates the tag) | **main only**: a tag-push run is refused at the publish job; dispatch from main, or ask the operator to add a tag rule | `scripts/update_llms_full.py` | Desktop app plus iPhone (`phone/iphone`, xcodegen, `iphone.yml`) and watch (`watch.yml`) workflows. |
| abstractgateway | lpalbou/AbstractGateway | `pyproject.toml` and `src/abstractgateway/__init__.py` | tag | main, tag `v*` | `scripts/generate-llms-full.py` | release.yml: tests 3.10-3.13, build, docs, the `abstractgateway-console` crate to crates.io when `console-tui/Cargo.toml` has a new version, GHCR images. See the floor rules below. |
| abstractnote | lpalbou/AbstractNote | `pyproject.toml`, `src/abstractnote/__init__.py` and `web/package.json` (the release validates the tag against pyproject and web) | tag, or dispatch with `-f version=X.Y.Z` (`-f dry_run=true` rehearses) | no restriction (`npm` env: main, tag `v*`) | `scripts/build_llms_full.py` | One release publishes the Python package and the web app. Needs the gateway release that carries the AbstractNote seam (`abstractgateway>=0.15.11`). |
| abstractframework | lpalbou/AbstractFramework | `pyproject.toml` and `abstractframework/__init__.py` (`__version__`, `RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS`, `CRATE_RELEASE_VERSIONS`) | tag | main, tag `v*` | `scripts/gen_llms_full.py` (`--check`) | Last. Also `docs/installers/install-manifest.json`, `scripts/install.sh`, `scripts/install.ps1`, install docs; `scripts/tests/test_inventory.sh` checks they agree. |

### npm

| Package | Repo / path | Version source | Trigger | `npm` env policy | Notes |
|---|---|---|---|---|---|
| ui-kit, app-server, monitor-flow, monitor-gpu, monitor-memory, monitor-active-memory, panel-chat | lpalbou/AbstractUIC, `<pkg>/package.json` | each package's `package.json`; the root `package.json` version names the release tag; root `package-lock.json` entries must match (`npm install --package-lock-only`) | PR, merge on green (one job "Test, build, and pack"), then tag `vX.Y.Z` = root version | main, tag `v*` | release.yml publishes each changed package with `npm publish --provenance`. Verify with `npm view @abstractframework/ui-kit version`. llms: `scripts/generate-llms-full.py`. |
| @abstractframework/flow | lpalbou/AbstractFlow | `package.json` | tag | main, tag `v*` | `npm run check:lock` fails until the pinned ui-kit is on npm; after it is, `npm install` and commit the lockfile. |
| @abstractframework/observer | lpalbou/AbstractObserver | `package.json` | tag | main, tag `v*` | same lockfile rule |
| @abstractframework/entity | lpalbou/AbstractEntity | `package.json` | tag | no restriction | same lockfile rule |
| @abstractframework/continuum | lpalbou/AbstractContinuum | `package.json` | tag | no restriction | same lockfile rule |
| @abstractframework/code | lpalbou/AbstractCode, `web/` (`npm --prefix web`) | `web/package.json` (versioned independently of the crate) | tag `web-vX.Y.Z` (a `vX.Y.Z` tag publishes only the crate), or dispatch `-f target=web` | main, tag `v*`, tag `web-v*` | same lockfile rule; the repository also holds the `abstractcode` crate |
| @abstractframework/note | lpalbou/AbstractNote, `web/` | `web/package.json` (equal to the Python version) | with abstractnote | main, tag `v*` | |

### Rust

| Crate | Repo / path | Trigger | `crates-io` env policy |
|---|---|---|---|
| abstracttui | lpalbou/AbstractTUI | tag `v*`, or dispatch `-f publish=true` (without it the run only verifies) | no restriction |
| abstracttui-graph, abstracttui-mermaid | lpalbou/AbstractTUI, `extensions/graph`, `extensions/mermaid` | with abstracttui: the `publish-family` job publishes graph, then mermaid (mermaid depends on graph) | no restriction |
| abstractcore-console | lpalbou/AbstractCore, `console-tui/` | with AbstractCore | no restriction |
| abstractgateway-console | lpalbou/AbstractGateway, `console-tui/` | with AbstractGateway, when `console-tui/Cargo.toml` has a new version | no restriction |
| abstractcode | lpalbou/AbstractCode, `tui/` (versioned independently of the web app) | tag `vX.Y.Z` only: its `crates-io` environment admits only `v*` tags, so a dispatch with `target=cli` or `all` is refused at `publish-crate` | tag `v*` |

Check a policy before a tag push:

```bash
gh api repos/lpalbou/<Repo>/environments/<pypi|npm|crates-io>/deployment-branch-policies \
  --jq '.branch_policies[]|"\(.type):\(.name)"'
```

A 404 means the environment has no custom policy (any ref may deploy).

## Cross-package floor rules

- **Gateway install profiles.** `abstractgateway/tests/test_gateway_install_profiles.py` pins the
  gateway's dependency floors literally. Update it in the same change as any floor.
- **Gateway AbstractVoice floor ≤ Core's.** The same test requires the gateway's `abstractvoice`
  floor to be at most AbstractCore's own `abstractvoice` floor, so the gateway never pins a newer
  AbstractVoice than Core declares. Release Core with the new floor first, or document "install
  the latest AbstractVoice" instead of pinning it.
- **Runtime floor constant.** `abstractgateway.live_deltas.ABSTRACTRUNTIME_FLOOR` must equal the
  gateway's pyproject `abstractruntime` floor (the startup "runtime too old" check reads it).
- **AbstractNote gateway extra.** `abstractnote[gateway]` requires the first gateway release with
  the AbstractNote seam; raise it when the seam changes.
- **Root pins.** The root pins exact versions (`==`); every release that should reach
  `pip install abstractframework[...]` needs a root release.
- **npm apps and AbstractUIC.** Apps pin AbstractUIC packages with a caret range; raise the range
  and refresh the lockfile after the AbstractUIC publish is visible.
