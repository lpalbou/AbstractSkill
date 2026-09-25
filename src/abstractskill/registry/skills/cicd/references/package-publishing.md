# Package Publishing

Use this reference when a repo should publish to PyPI, npm, or both.

## PyPI

Use PyPI trusted publishing with GitHub Actions OIDC whenever possible.

Generate PyPI publishing when:

- `pyproject.toml` contains a publishable `[project]` or equivalent backend metadata;
- the package name and version are clear;
- publishing is requested or appropriate for the repo.

Workflow requirements:

- environment name should usually be `pypi`;
- job permissions must include `id-token: write`;
- publish with `pypa/gh-action-pypi-publish`;
- build distributions before publishing and run `twine check`;
- do not require `PYPI_API_TOKEN` when trusted publishing is configured.

One-time external setup:

- PyPI must trust the GitHub repository, workflow filename, and environment.
- If creating a new PyPI project through OIDC, follow the current PyPI trusted publisher flow.
- If adding a publisher to an existing project, configure it in the PyPI project settings.

Recommended release job shape:

```yaml
publish-pypi:
  name: Publish to PyPI
  runs-on: ubuntu-latest
  needs: [build]
  if: needs.build.outputs.should_publish == 'true'
  environment:
    name: pypi
    url: https://pypi.org/project/<package-name>/
  permissions:
    contents: read
    id-token: write
  steps:
    - uses: actions/download-artifact@<current-major>
      with:
        name: release-artifacts   # must match the build job's upload name
        path: dist
    # @release/v1 is PyPA's documented stable channel (a moving branch);
    # SHA-pin for a stricter supply-chain posture.
    - uses: pypa/gh-action-pypi-publish@release/v1
```

## npm

Use npm trusted publishing with GitHub Actions OIDC when available.

Generate npm publishing when:

- `package.json` exists;
- the package is not marked `"private": true`, unless the user asks for private registry publishing;
- package name, version, and repository URL are valid for the target registry.

Workflow requirements:

- use GitHub-hosted runners for trusted publishing;
- permissions must include `id-token: write`;
- use `actions/setup-node` with `registry-url: https://registry.npmjs.org`;
- run `npm ci`, build, and test before `npm publish`;
- do not add `NPM_TOKEN` for trusted publishing unless private dependency installation requires a
  separate read-only token.

Recommended release job shape:

```yaml
publish-npm:
  name: Publish to npm
  runs-on: ubuntu-latest
  needs: [build]
  if: needs.build.outputs.should_publish == 'true'
  environment:
    name: npm
    url: https://www.npmjs.com/package/<package-name>
  permissions:
    contents: read
    id-token: write
  steps:
    - uses: actions/checkout@<current-major>
    - uses: actions/setup-node@<current-major>
      with:
        # npm trusted publishing requires npm CLI >= 11.5.1; Node 22 bundles an
        # older npm and the OIDC handshake silently never runs (confusing E404).
        # Use a Node line whose bundled npm is recent enough, or add an explicit
        # `npm install -g npm@latest` step before publishing.
        node-version: "24"
        registry-url: https://registry.npmjs.org
    - run: npm ci
    - run: npm run build --if-present
    - run: npm test --if-present
    - run: npm publish
```

For scoped public packages, add `--access public` when needed.

One-time external setup:

- Configure trusted publishing on npmjs.com or with `npm trust github` when the package already
  exists and the installed npm version supports it.
- Ensure `package.json` `repository.url` exactly matches the GitHub repository.
- Consider requiring 2FA and disallowing long-lived tokens after trusted publishing works.

Useful npm trust pattern:

```sh
npm trust github <package-name> --repo <owner>/<repo> --file release.yml --env npm --allow-publish
```

Use `--dry-run` first when supported and do not assume the package exists.
`npm trust` requires npm >= 11.10.0 and interactive account-level 2FA; newer
configurations require an explicit permission flag (`--allow-publish` or
`--allow-stage-publish`).

## Mixed Python And npm Repos

For monorepos or dual packages:

- keep one CI workflow with language-specific jobs;
- keep one release workflow if one version and tag controls all artifacts;
- use separate publish jobs and environments for PyPI and npm;
- validate every package version before any publish job runs;
- fail before publishing anything if one package's release metadata is inconsistent.

## Sources

- PyPI trusted publishing: https://docs.pypi.org/trusted-publishers/
- PyPI trusted publishing with GitHub Actions: https://docs.pypi.org/trusted-publishers/using-a-publisher/
- npm trusted publishing: https://docs.npmjs.com/trusted-publishers
- npm trust CLI: https://docs.npmjs.com/cli/v11/commands/npm-trust/

Action version policy: `<current-major>` placeholders mean check the action's
current major (and prefer SHA-pinning third-party actions) before writing the
workflow — copied version pins go stale and node-runtime cutovers break them.
