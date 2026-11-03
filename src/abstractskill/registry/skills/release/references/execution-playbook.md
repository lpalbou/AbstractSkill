# Release Execution Playbook

Use this reference before triggering, publishing, tagging, or verifying a release.

## Pick The Release Path

Prefer the repository's documented release path:

- tag push, usually an annotated tag such as `v1.2.3`;
- `workflow_dispatch` with explicit `version`, `publish`, and confirmation inputs;
- release branch merge;
- project-specific release script or command.

If the path is unclear, inspect `.github/workflows`, release docs, package metadata, and recent
tags. Use `cicd` when the workflow itself needs repair.

## Existing Remote Workflow Trigger

When triggering an already-healthy remote workflow:

- verify the workflow exists and is enabled;
- verify the target branch, tag, or ref exists remotely;
- verify required inputs and confirmation strings;
- check duplicate version/tag risk;
- inspect and classify local pending changes before a real publish;
- do not block on unrelated local pending changes only after the classification is explicit and no
  release-scope files remain uncommitted;
- report the workflow run URL or enough `gh run` information for tracking.

Use rehearsal mode only when the user asks for dry run, staging, or validation. If the user asks
for real publish, set publish inputs accordingly and do not silently choose `publish=false`.

## Local Commit, Push, And Tag

When the release must include local changes:

1. Inspect `git status --short` and separate release changes from unrelated edits.
2. Include every release-scope source, test, docs, workflow, package metadata, generated index, and
   release-note file in the release commit.
3. Run the required local gates or explain which gates are delegated to CI.
4. Re-run `git status --short`; stop if release-scope changes are still pending or untracked.
5. Commit the release changes with a message that names the version.
6. Push the commit to the intended branch.
7. Create the tag on that exact commit.
8. Push the tag or dispatch the release workflow.

Prefer annotated tags for public releases unless the repo uses lightweight tags consistently.
Never retag or force-push a release tag unless the user explicitly asks and the registry/release
immutability consequences are clear.

## Common Commands

Use the repo's real tools, but these checks are often useful:

```bash
git status --short
python3 <skill-dir>/scripts/release_pending_gate.py
git branch --show-current
git fetch --tags origin
git tag --list 'v*'
gh workflow list
gh workflow view <workflow>
gh run list --workflow <workflow> --limit 5
```

Duplicate package checks:

```bash
npm view <package>@<version> version
python -m pip index versions <package>
gh release view <tag>
```

Publishing triggers:

```bash
git tag -a v<version> -m "Release v<version>"
git push origin HEAD
git push origin v<version>
gh workflow run <workflow> --ref <branch-or-tag> -f version=<version> -f publish=true
```

These are examples, not universal commands. Do not run them blindly when the repository has a
different documented release path.

## Post-Release Verification

After a real release, verify the destinations that apply:

- GitHub Release exists, points to the intended tag, and contains expected notes and artifacts;
- PyPI package version exists and can be installed when applicable;
- npm package version and dist-tag exist when applicable;
- docs deployment completed and the published site reflects the new version;
- container images and tags exist when applicable;
- generated checksums, signatures, provenance, or SBOMs exist when the repo promises them;
- basic install or invocation works from the published artifact when practical.

If one publish destination fails after another succeeded, do not hide the partial release. State
what shipped, what failed, whether retry is safe, and what follow-up is needed.

## Avoid Common Release Failures

- Do not tag before version, changelog, docs, and validation are ready.
- Do not tag or publish while release-scope files are uncommitted or untracked.
- Do not publish packages from pull request events or unreviewed branches.
- Do not publish a version that already exists unless the registry and project explicitly support
  rebuilds.
- Do not let release notes drift from the changelog or generated GitHub Release body.
- Do not leave docs deployment or package publishing silently skipped.
- Do not rely on local pending changes being present in CI; only committed and pushed files release.
