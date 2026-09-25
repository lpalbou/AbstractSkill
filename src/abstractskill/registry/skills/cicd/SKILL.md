---
name: cicd
description: Create, audit, normalize, and maintain GitHub-based CI/CD for repositories, including CI workflows, release workflows, GitHub Pages documentation deployment, PyPI trusted publishing, npm trusted publishing, optional Docker/GHCR publishing, and repository setup guidance for environments, branch rules, Pages, and package registry trust. Use when Codex needs to bootstrap or repair `.github/`, release automation, package publishing, docs deployment, or GitHub repository CI/CD settings.
---

# CI/CD

Use this skill to build a practical GitHub Actions CI/CD system that is safe by default, explicit
about releases, and adapted to the repository's actual package surfaces.

## Start With The Right Pass

- Inspect the repository before writing workflows. Check existing `.github/`, package manifests,
  lockfiles, docs configs, Dockerfiles, release notes, tests, and current branch names.
- If the repo already has CI/CD, preserve working local conventions and repair gaps rather than
  replacing everything blindly.
- If bootstrapping `.github/` from scratch, read `references/workflow-patterns.md` first.
- If publishing packages, read `references/package-publishing.md` before editing release workflows.
- If deploying docs or containers, read `references/docs-and-containers.md`.
- If the user asks to configure the GitHub repository itself, read `references/repository-setup.md`
  and prefer dry-run or explicit confirmation before mutating remote settings.
- If auditing, repairing, maintaining, or triggering existing CI/CD, read
  `references/maintenance-playbook.md` before editing workflows or remote settings.
- If the user is preparing, cutting, publishing, or verifying a specific software release, prefer
  the `release` skill when available. Use this skill for the CI/CD workflow and repository-setting
  parts of that release.

## Apply The Operating Rules

- Prefer GitHub Actions as the standard orchestration layer.
- Keep CI and release concerns separate unless the repo is intentionally tiny.
- Use least-privilege `permissions` at workflow and job level.
- Use OIDC trusted publishing for PyPI and npm when available. Avoid long-lived package tokens
  unless trusted publishing is impossible and the user accepts the tradeoff.
- Put publish jobs behind explicit release triggers: version tags, manual `workflow_dispatch`, or a
  documented release branch rule. Never publish from pull requests.
- Use GitHub environments for deployments such as `pypi`, `npm`, `github-pages`, and `ghcr` when
  they materially improve review, branch, or secret boundaries.
- Build and test before publishing. Release jobs should consume validated artifacts rather than
  rebuilding unrelated outputs in separate publish jobs.
- Validate version, tag, changelog, package metadata, and duplicate-publish risk before release.
- Deploy a documentation website by default unless the repo already has a custom docs deployment or
  the user explicitly disables it.
- Add Docker/GHCR publishing only when requested or when a `Dockerfile`, service entrypoint, or
  deployable runtime makes container distribution useful.
- Document any required one-time external setup that workflows cannot safely perform, especially
  PyPI trusted publisher setup, npm trusted publisher setup, GitHub Pages source, and environment
  protection rules.
- Treat CI/CD drift as a real maintenance problem. Re-check workflows when package managers,
  supported runtimes, docs tooling, default branches, release policy, or registry settings change.
- If the repository already has a healthy release pipeline and the user asks to trigger or publish
  a release, operate that pipeline instead of redesigning it. Keep preflight checks proportional and
  let the remote workflow enforce its own release gates.
- Do not treat pending local changes as a blocker for triggering an existing remote workflow only
  after every pending change has been classified and no release-scope file is left uncommitted.
  Pending local changes matter if they touch code, tests, docs, package metadata, workflows,
  release notes, or generated indexes; if Codex created them while preparing the release; if the
  release is supposed to include them; or if Codex is about to create commits/tags from the local
  checkout.

## Decide What To Generate

- Always consider `.github/workflows/ci.yml` for pull requests and pushes.
- Create a release workflow when the repo has a publishable package, GitHub Release artifacts, docs
  deployment, or container images.
- Create or update docs deployment when the repo has docs or should have project documentation.
  Use the `coredoc` skill when documentation content or `llms.txt` files also need to be created.
- Add PyPI publishing only when the repo has a Python package (`pyproject.toml`, package metadata,
  build backend) and publishing is appropriate.
- Add npm publishing only when the repo has a publishable `package.json`; skip packages marked
  `"private": true` unless the user explicitly asks for a private registry workflow.
- Add Docker publishing only when requested or clearly advisable from repository evidence.
- Add dependency/update automation for GitHub Actions and detected package ecosystems unless the
  repo already uses another update service or the user declines it.

## Keep Workflows Auditable

- Prefer named jobs and explicit dependencies via `needs`.
- Use `concurrency` to prevent overlapping release or docs deployments.
- Upload release artifacts from build jobs and download them in publish jobs.
- Keep manual release confirmations project-specific and hard to trigger accidentally.
- Fail loudly when version, changelog, tag, repository URL, package name, or registry state does
  not match expectations.
- Provide a non-publishing release rehearsal path, usually `workflow_dispatch` with
  `publish=false`, so release validation can be exercised without pushing to registries.
- Make registry and docs deployment setup visible in comments, docs, or final setup notes.

## Use References Selectively

- Read `references/workflow-patterns.md` for the default `.github/workflows` shape.
- Read `references/package-publishing.md` for PyPI and npm publishing rules.
- Read `references/docs-and-containers.md` for GitHub Pages and Docker/GHCR patterns.
- Read `references/repository-setup.md` for GitHub repository, environment, Pages, and package
  registry setup guidance.
- Read `references/maintenance-playbook.md` for drift audits, release rehearsals, dependency
  update automation, existing release triggering, and post-release checks.
