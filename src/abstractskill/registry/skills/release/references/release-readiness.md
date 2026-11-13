# Release Readiness

Use this reference before changing version metadata, changelog, docs, or validation gates.

## Version And Scope

- Identify the canonical version source: `pyproject.toml`, `package.json`, Cargo workspace
  metadata, language-specific manifests, a generated package manifest, or project release docs.
- Before bumping, compare the current metadata version against existing local tags, remote tags,
  GitHub Releases, and target registries. If the metadata already contains an unpublished version,
  treat that as the pending release version instead of inventing another bump.
- Use the repository's existing versioning convention. If none exists, prefer SemVer for packages
  and `vX.Y.Z` tags for public releases.
- For monorepos, decide whether one version controls all packages or each package releases
  independently. Do not assume one tag can safely publish every package.
- For prereleases, verify the registry dist-tag or release channel (`alpha`, `beta`, `rc`, nightly,
  canary) before publish.
- Check whether the target version or tag already exists locally, on the remote, and in registries.

## Worktree Completeness Gate

Before any real publish, create a release-scope inventory from `git status --short`. The release
cannot proceed while relevant work is only in the local checkout.

Inventory local-only commits as well as files. Query live remote refs, compare local HEAD and the
proposed release commit with remote main, and inspect existing branches/worktrees for code that
belongs to the requested work. Use patch and source equivalence to distinguish already-shipped
work from omitted changes. Ask about ambiguous ownership or conflicting scope before merging;
record each disposition and preserve its source. A published version number alone does not prove
that newer source or required consumer integrations shipped.

Block publishing if any modified, staged, deleted, renamed, or untracked file is release-scope:

- package metadata, lockfiles, generated manifests, schemas, or version files;
- `CHANGELOG.md`, release notes, README, docs, `llms.txt`, or `llms-full.txt`;
- source code, integrations, package modules, CLIs, SDKs, or runtime files;
- tests, fixtures, examples, scripts, workflows, Dockerfiles, docs config, or build config;
- any file the agent created while preparing the release.

If pending changes are claimed to be unrelated, state that classification explicitly with paths. Do
not publish with vague language such as "there are unrelated files" when any untracked or modified
file could plausibly affect the package, docs, tests, or release process.

Use `scripts/release_pending_gate.py` from this skill when available. It is conservative: it blocks
on release-relevant paths and requires explicit allowance even for unrelated pending changes.

## Changelog And Release Notes

`CHANGELOG.md` should have a non-empty entry for the release version before publishing. Keep it
front-facing:

- added, changed, fixed, deprecated, removed, security, or migration notes when relevant;
- affected package names, commands, APIs, or configuration when useful;
- compatibility or migration impact;
- links to full docs or release notes when the entry would otherwise become too large.

Avoid internal repair narrative:

- do not explain failed investigations, blame, or temporary implementation mistakes;
- do not copy backlog completion reports into the changelog;
- do not mention old behavior unless users need it for migration or interpreting older output.

Use release notes generated from the changelog entry unless the repo has a stronger release-notes
source.

## Documentation Gate

Use `coredoc` when any release-visible behavior changed. Check at least:

- `README.md` for install and quick-start accuracy;
- `CHANGELOG.md` for the release entry;
- `docs/getting-started.md` for setup or first-run changes;
- `docs/api.md` for API, CLI, config, or command changes;
- `docs/troubleshooting.md` for known setup, runtime, registry, integration, or migration failures;
- `docs/faq.md` for recurring conceptual questions or limitations;
- topic docs for changed deployment, provider, auth, memory, plugin, or release behavior;
- `llms.txt` and `llms-full.txt` when included docs changed.

Do not block a release on decorative documentation cleanup. Do block it on docs that would cause
users or tools to install, configure, call, migrate, or debug the release incorrectly.

## Validation Gate

Prefer the repo's documented validation commands. Common gates include:

- unit, integration, smoke, and compatibility tests relevant to the release;
- lint, format, typecheck, or static analysis required by the repo;
- package builds such as `python -m build`, `twine check`, `npm pack --dry-run`, `cargo package`,
  or language-specific equivalents;
- docs builds such as MkDocs, Sphinx, mdBook, Docusaurus, or project-specific scripts;
- install smoke tests from the built artifact when practical;
- workflow syntax checks such as `actionlint` when workflow files changed.

If a check cannot be run locally, say why and rely on the remote release rehearsal only when the
workflow actually runs an equivalent gate.

## Release Commit Contents

A normal release commit may include:

- version metadata and lockfiles;
- changelog and release notes;
- updated user-facing docs and AI-readable indexes;
- release-relevant source code, tests, integration files, examples, and scripts;
- generated package metadata or schemas;
- release workflow fixes required for this release;
- backlog or ADR updates only when the repo uses them and the release materially changes their
  state.

Keep unrelated feature work, speculative cleanup, and private local files out of the release
commit. If a file was created or modified to make the release pass, it is not unrelated; commit it
or stop the release.
