# Documentation And Container Deployment

Use this reference when adding docs deployment or optional container publishing.

## Documentation Website

Deploy a documentation website by default unless:

- a custom docs deployment already exists;
- the user explicitly disables docs deployment.

If docs content is missing or stale, use the `coredoc` skill before wiring the docs deployment. A new
repo should get a docs site by default, not a release pipeline that silently omits documentation.

Detect the docs generator:

- `mkdocs.yml`: build with `mkdocs build`, deploy the generated `site/`;
- Sphinx: build with `sphinx-build` or the repo's docs command;
- Docusaurus, VitePress, Next, Astro, or Vite: use package scripts and deploy the configured output
  directory;
- plain `docs/`: create a minimal static site only when that fits the repo and user request.

Prefer GitHub Pages custom workflows over committing generated docs to `gh-pages`, unless the repo
already uses `mkdocs gh-deploy` or another established branch deployment.

Recommended Pages deployment job:

```yaml
deploy-docs:
  name: Deploy docs to GitHub Pages
  runs-on: ubuntu-latest
  needs: [build]
  if: needs.build.outputs.should_publish == 'true'
  permissions:
    contents: read
    pages: write
    id-token: write
  environment:
    name: github-pages
    url: ${{ steps.deployment.outputs.page_url }}
  steps:
    - uses: actions/checkout@<current-major>
    - name: Build docs
      run: <repo docs build command>
    - uses: actions/configure-pages@<current-major>
    - uses: actions/upload-pages-artifact@<current-major>
      with:
        path: <docs output directory>
    - id: deployment
      uses: actions/deploy-pages@<current-major>
```

One-time GitHub setup:

- Pages source should be GitHub Actions for custom workflow deployment.
- If using the REST API, create or update Pages with `build_type: workflow`.

## Docker And GHCR

Add container publishing when requested or advisable from repo evidence:

- `Dockerfile` exists;
- the repo is a service, API server, CLI runtime, worker, or deployable app;
- users are likely to consume prebuilt images;
- container release is documented or requested.

Default registry is GitHub Container Registry (`ghcr.io`) unless the user requests Docker Hub or
another registry.

Recommended container job:

```yaml
publish-container:
  name: Publish container
  runs-on: ubuntu-latest
  needs: [build]
  if: needs.build.outputs.should_publish == 'true'
  permissions:
    contents: read
    packages: write
    id-token: write   # add attestations: write ONLY with an attest step
  steps:
    - uses: actions/checkout@<current-major>
    - uses: docker/login-action@<current-major>
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    - id: meta
      uses: docker/metadata-action@<current-major>
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=ref,event=tag
          type=raw,value=latest,enable={{is_default_branch}}
    - uses: docker/build-push-action@<current-major>
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
```

If adding attestations, ensure the action and registry support the chosen attestation path.

## Sources

- GitHub Pages custom workflow docs: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- GitHub Pages REST API: https://docs.github.com/en/rest/pages
- GitHub Container Registry docs: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry
- GitHub Docker image publishing docs: https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images
- Docker GitHub Actions docs: https://docs.docker.com/build/ci/github-actions/

Action version policy: `<current-major>` placeholders mean check the action's
current major (and prefer SHA-pinning third-party actions like docker/*)
before writing the workflow — copied version pins go stale.
