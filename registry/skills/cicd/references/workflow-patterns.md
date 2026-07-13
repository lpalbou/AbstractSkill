# GitHub Actions Workflow Patterns

Use this reference when creating or repairing `.github/workflows`.

## Source Pattern

The reusable baseline is modeled on AbstractRuntime's `.github/`:

- `ci.yml` runs on `push` to the default branch and on pull requests;
- CI uses least-privilege `contents: read`;
- tests run in a version matrix;
- build and docs jobs prove distributions and docs before release;
- `release.yml` runs on version tags and manual dispatch;
- release jobs validate version, changelog, tag, and duplicate-publish risk before publishing;
- publish jobs use environments and consume uploaded artifacts.

Do not copy project-specific dependencies or test file lists. Re-detect them from the target repo.

## Repository Inventory

Before writing workflows, inspect:

- default branch and existing workflow files;
- `pyproject.toml`, `setup.cfg`, `setup.py`, `requirements*.txt`, `uv.lock`, `poetry.lock`;
- `package.json`, lockfiles, workspaces, build scripts, test scripts, `private`;
- docs config such as `mkdocs.yml`, `docs/`, `docusaurus.config.*`, `vitepress`, `sphinx`;
- `Dockerfile`, `docker-compose.yml`, service entrypoints, exposed ports;
- `CHANGELOG.md`, release notes, version source, package names;
- existing repository docs that mention release or deployment.

## Default Workflow Set

For a normal repo, prefer:

- `.github/workflows/ci.yml` for PR and push validation;
- `.github/workflows/release.yml` for package publishing, GitHub Releases, docs deploy, and optional
  container publish;
- `.github/dependabot.yml` for GitHub Actions and detected package ecosystems unless the repo
  already uses another dependency-update service or the user declines it.

Small repos can merge docs build into CI. Avoid merging package publication into CI unless there is
no release workflow and no registry publishing.

## Dependency Update Automation

For new repos, create a lightweight `.github/dependabot.yml` unless an equivalent updater already
exists. Include:

- `github-actions` for `.github/workflows`;
- `pip` for Python repos when dependency files exist;
- `npm` for Node repos when `package.json` exists;
- `docker` when Dockerfiles are published or security-sensitive.

Keep schedules modest, usually weekly. Do not add noisy update automation for ecosystems the repo
does not use.

## CI Workflow Rules

CI should:

- trigger on pull requests and pushes to the default branch;
- use `concurrency` with `cancel-in-progress: true`;
- set `permissions: contents: read`;
- run tests before build-only checks where practical;
- build distributions or bundles when the repo is publishable;
- build docs on every PR unless the docs build is too expensive and a separate docs workflow exists.

Language-specific defaults:

- Python: matrix supported Python versions, install with the repo's chosen tool, run tests, build
  with `python -m build`, and run `twine check` for distributions.
- Node/npm: use the repo's package manager, run install, lint/test/build scripts if present, and
  avoid release-only caching shortcuts in publish jobs.
- Rust/Go/Swift/etc.: follow the repo's local commands and keep publish-specific logic in release.

Compact CI skeleton:

```yaml
name: CI

on:
  push:
    branches: ["<default-branch>"]
  pull_request:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<current-major>
      - name: Set up project toolchain
        run: <repo-specific setup>
      - name: Test
        run: <repo-specific test command>

  build:
    name: Build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<current-major>
      - name: Build
        run: <repo-specific build command>

  docs:
    name: Build docs
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<current-major>
      - name: Build docs
        run: <repo-specific docs build command>
```

## Release Workflow Rules

Release should:

- trigger on `v*.*.*` tags and optionally `workflow_dispatch`;
- use `concurrency` with `cancel-in-progress: false`;
- run CI-quality tests or depend on a validated build job;
- validate version source, changelog entry, tag, and publish confirmation;
- upload build artifacts once;
- publish PyPI/npm/container artifacts from downloaded artifacts where possible;
- create a GitHub Release from generated release notes;
- deploy docs only after the release artifact has been validated.

If a repo already implements these release rules cleanly, do not rewrite the workflow before
triggering a release. Operate the existing workflow and reserve edits for real gaps, broken gates,
or user-requested CI/CD changes.

Manual publish inputs should include:

- `version`;
- `publish` boolean;
- project-specific confirmation such as `publish-<package>-<version>`.

The `publish=false` path should still run validation and build artifacts, but must not create tags,
publish packages, deploy docs, create GitHub Releases, or push containers.

Compact release skeleton:

```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"
  workflow_dispatch:
    inputs:
      version:
        required: true
        type: string
      publish:
        required: true
        type: boolean
        default: false
      publish_confirmation:
        required: false
        type: string

permissions:
  contents: read

concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    name: Validate and build release artifacts
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.release-meta.outputs.version }}
      tag: ${{ steps.release-meta.outputs.tag }}
      should_publish: ${{ steps.release-meta.outputs.should_publish }}
    steps:
      - uses: actions/checkout@<current-major>
        with:
          fetch-depth: 0
      - id: release-meta
        name: Validate version, changelog, tag, and publish guard
        run: <repo-specific validation script>
      - name: Build release artifacts
        run: <repo-specific build command>
      - uses: actions/upload-artifact@<current-major>
        with:
          name: release-artifacts
          path: <artifact paths>
```

## Release Validation

Before publishing, check:

- the requested version matches `pyproject.toml`, `package.json`, or the repo's version source;
- the changelog contains a non-empty entry for the version;
- a tag either matches the current commit or can be safely created;
- the target registry does not already contain the same package version;
- package repository metadata matches the GitHub repository for npm trusted publishing;
- docs build succeeds.

## Action Version Policy

Use current maintained official actions when writing new workflows. If unsure, check official docs
or the action repository before pinning a major version. Avoid stale copied versions from old repos
unless the target repo intentionally pins them.

## Sources

- GitHub Actions deployment docs: https://docs.github.com/actions/deployment/about-deployments/deploying-with-github-actions
- GitHub Pages custom workflow docs: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
