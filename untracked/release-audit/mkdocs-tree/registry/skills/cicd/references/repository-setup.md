# Repository Setup

Use this reference when the user asks Codex to configure GitHub repository settings or package
registry trust, not only write workflow files.

## General Rules

- Prefer inspecting first: `gh auth status`, `gh repo view --json owner,name,defaultBranchRef`.
- Require admin or maintainer permission for repository settings.
- Use dry-run or print intended changes before mutating remote settings unless the user explicitly
  requested direct configuration.
- Do not store package publishing secrets when OIDC trusted publishing is available.
- Record any setup that could not be automated in the final answer or repo docs.

## Recommended GitHub Environments

Use these names unless the repo already has conventions:

- `pypi` for PyPI publication;
- `npm` for npm publication;
- `github-pages` for GitHub Pages deployment;
- `ghcr` or `container-registry` for container publishing.

Environment setup should usually include:

- allowed deployment branches or protected branches;
- required reviewers for production-like publishes when appropriate;
- no unnecessary environment secrets for OIDC-based PyPI/npm publishing;
- URLs for deployment environments when GitHub can display them.

## GitHub API Patterns

Create or update an environment with the GitHub REST API through `gh api`:

```sh
gh api --method PUT repos/<owner>/<repo>/environments/pypi \
  --input environment-pypi.json
```

Use JSON input when setting branch policies or reviewers so nested fields are not mangled by shell
quoting.

For Pages custom workflows, set the repository Pages build type to workflow when needed:

```sh
gh api --method POST repos/<owner>/<repo>/pages \
  --input pages-workflow.json
```

Example `pages-workflow.json` shape:

```json
{
  "build_type": "workflow",
  "source": {
    "branch": "main",
    "path": "/"
  }
}
```

If the Pages site already exists, inspect the current API shape and update rather than blindly
creating a new site.

## PyPI Setup

PyPI trusted publishers are configured on PyPI, not only in GitHub.

For GitHub Actions, the trusted publisher must match:

- repository owner;
- repository name;
- workflow filename such as `release.yml`;
- environment name such as `pypi`.

If automation is not available, tell the user the exact PyPI publisher values to configure.

## npm Setup

npm trusted publishers can be configured through npmjs.com or the `npm trust` CLI when available.

CLI pattern:

```sh
npm trust github <package-name> --repo <owner>/<repo> --file release.yml --env npm
```

Prerequisites include a sufficiently recent npm CLI, package write access, account 2FA, and an
existing package. Use `npm trust list` before replacing existing trust.

## Branch Rules And Required Checks

When asked to configure branch protection or rulesets:

- make CI required for the default branch;
- require release workflows only for release branches or tags when appropriate;
- avoid rules that block the GitHub Actions bot from creating intended release tags unless the
  workflow design accounts for that;
- prefer rulesets for new GitHub repositories when they are the repo's existing standard, otherwise
  use branch protection conservatively.

## Sources

- GitHub deployments and environments: https://docs.github.com/actions/deployment/about-deployments/deploying-with-github-actions
- GitHub deployment environments REST API: https://docs.github.com/rest/deployments/environments
- GitHub Pages REST API: https://docs.github.com/en/rest/pages
- PyPI trusted publishers: https://docs.pypi.org/trusted-publishers/
- npm trust CLI: https://docs.npmjs.com/cli/v11/commands/npm-trust/
