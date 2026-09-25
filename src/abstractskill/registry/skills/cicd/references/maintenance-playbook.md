# CI/CD Maintenance Playbook

Use this reference when auditing, repairing, or keeping CI/CD healthy over time.

## When To Run A CI/CD Audit

Run this pass when:

- bootstrapping a new repo;
- a release fails or partially succeeds;
- supported Python, Node, or other runtime versions change;
- package manager, lockfile, docs generator, Dockerfile, or default branch changes;
- release policy changes from manual to tag-based or vice versa;
- PyPI, npm, GitHub Pages, or GHCR setup changes;
- new publishable packages are added to a monorepo;
- a dependency update changes workflow action majors or build tooling.

## Audit Checklist

- Inspect `.github/workflows`, `.github/dependabot.yml`, package manifests, docs config, Dockerfiles,
  changelog, and release docs.
- Verify workflow triggers match the default branch and release policy.
- Verify CI runs on pull requests and default-branch pushes.
- Verify release workflows never publish from pull requests.
- Verify job-level `permissions` are least-privilege.
- Check for untrusted input interpolated into `run:` steps (`${{ github.event.* }}` titles/bodies/branch names — script injection).
- Check `pull_request_target` usage: it runs with secrets against base-branch code; never check out or execute PR head code under it.
- Check third-party actions are pinned by full commit SHA or on an explicit allowlist (mutable tags are a supply-chain surface).
- Verify publish jobs use environments and OIDC where possible.
- Verify release validation checks version, changelog, tag, package metadata, and duplicate
  registry versions before publishing.
- Verify docs build in CI and deploy through GitHub Pages unless a custom docs deployment exists.
- Verify container publishing exists only when requested or justified by repo evidence.
- Verify `.github/dependabot.yml` or an equivalent updater covers GitHub Actions and detected
  package ecosystems.
- Verify final setup notes or docs mention external registry setup that cannot be inferred from
  workflow files.

## Validation Commands

Use what is available in the target repo:

- `actionlint` for workflow syntax and common GitHub Actions mistakes;
- `gh workflow list` and `gh workflow view <name>` to inspect remote workflow state;
- `gh run list --workflow <workflow>` to inspect recent failures;
- package build checks such as `python -m build`, `twine check`, `npm pack --dry-run`,
  `npm publish --dry-run`, or Docker build dry runs;
- docs build commands such as `mkdocs build`, `sphinx-build`, or package-manager docs scripts.

If a validator is not installed, do not silently claim it passed. Either install it when appropriate
or report that the check was not run.

## Release Rehearsal

Every release workflow should support a non-publishing rehearsal path when practical:

- `workflow_dispatch`;
- explicit `version` input;
- `publish=false`;
- no tag creation;
- no package publish;
- no GitHub Release creation;
- no docs deployment;
- no container push.

The rehearsal should still run version/changelog validation, tests, builds, docs builds, and artifact
creation. This catches release breakage before registry credentials or deployment permissions are
involved.

## Trigger An Existing Release Pipeline

When the user asks to publish, trigger, dispatch, or run an already-structured release pipeline:

- Inspect existing workflows with `gh workflow list`, `gh workflow view`, and local workflow files.
- Identify the intended release path: tag push, `workflow_dispatch`, release branch, or existing
  project-specific command.
- Prefer the repo's documented release path over adding new checks or editing workflows.
- Confirm required inputs such as `version`, `publish`, and project-specific confirmation strings.
- Check that the target ref exists remotely and is the ref the user intends to release.
- If the workflow supports `publish=false`, use it only when the user asked for rehearsal or dry run.
- If the user asked for a real publish, do not silently downgrade to rehearsal.
- After dispatch, report the workflow run URL or enough `gh run` details to track it.

Keep local preflight proportional. Useful checks include:

- current branch and remote default branch;
- whether the intended tag or version already exists;
- whether the workflow file and required environment names exist;
- whether `gh auth status` has enough permission to dispatch the workflow.

Do not block a remote workflow dispatch just because the local checkout has unrelated modified or
untracked files. Pending local changes are normal when the user is asking Codex to operate CI/CD
from a repo that also has local edits, but release-scope files must not be hand-waved. Inspect and
classify pending changes before a real publish. Pending changes are relevant when:

- they touch code, tests, docs, package metadata, workflows, release notes, generated indexes, or
  docs/LLM indexes;
- Codex created or edited them while preparing the release;
- the release should include those local edits;
- Codex is about to commit, tag, or push from the local checkout;
- the workflow will run on the current local branch after Codex pushes it.

If release-scope local edits must be included, stop and make that explicit: the release needs a
commit and push before dispatch. If the release targets an existing remote ref and only unrelated
local edits remain, proceed with the remote trigger and state the unrelated paths.

## Post-Release Checks

After a real release, verify:

- the GitHub Release exists and points to the intended tag;
- PyPI package/version exists when PyPI publishing was enabled;
- npm package/version exists when npm publishing was enabled;
- docs deployment completed and the Pages URL loads;
- GHCR image tags exist when container publishing was enabled;
- failed optional jobs are recorded as follow-up work rather than ignored.

## Registry Trust Drift

For PyPI:

- environment name in workflow should match the PyPI trusted publisher configuration;
- workflow filename should match the PyPI trusted publisher configuration;
- package name and version should match `pyproject.toml`.

For npm:

- `package.json` `repository.url` should match the GitHub repository;
- trusted publisher configuration should match owner, repo, workflow file, and environment;
- self-hosted runners should not be used for trusted publishing unless npm supports that in the
  current docs.

## GitHub Settings Drift

When remote configuration is in scope, inspect:

- deployment environments and branch policies;
- Pages build type and source;
- default branch name;
- required checks or rulesets;
- repository Actions permissions;
- package permissions for GHCR.

Prefer explicit setup notes over hidden assumptions. Workflows should make required environment
names and trusted-publishing values obvious.

## Avoid Common CI/CD Failures

- Do not publish from pull request events.
- Do not add package registry tokens when OIDC trusted publishing is viable.
- Do not let docs deployment disappear because no docs site existed yet; use the `coredoc` skill to
  bootstrap one.
- Do not allow release jobs to rebuild different artifacts from the ones validated earlier.
- Do not leave action or package manager updates entirely manual in a repo meant to be maintained.
- Do not silently skip package or docs deployment after detecting a publishable package or docs site.
