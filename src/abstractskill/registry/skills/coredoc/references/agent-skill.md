# Package Agent Skill

Read this file on every coredoc pass. It decides whether the repository ships a package agent
skill, and it governs creating, auditing, and updating one.

## What It Is

A package agent skill is an [Agent Skills](https://agentskills.io/) folder (`SKILL.md` plus
optional resources) that the repository ships so that any AI agent that wants to use the package
can load it and work like an expert user. After reading it, an agent knows when the package
applies and where it falls short, how to install and verify it, the few concepts and settings
that matter, the workflow an expert follows, the exact commands and code for the common tasks,
and the mistakes to avoid.

- It is a consumer artifact. It teaches how to use the package, not how to develop it. Contributor
  workflows stay in `CONTRIBUTING.md`. Repository-local agent instructions (`AGENTS.md`,
  `CLAUDE.md`, `.claude/skills/`, `.cursor/skills/`) serve people working on the repository and
  are out of scope here.
- It complements `llms.txt`: `llms.txt` helps an agent find and read the docs; the skill turns the
  docs into an operating procedure.
- The docs stay canonical. The skill is a faithful, task-shaped distillation of them.

## Decide Whether The Repository Needs One

Decide from repository evidence (the code, entry points, public exports, CLI `--help`, service
definitions), not from README claims or self-descriptions. Re-run the decision on every pass.

No skill is the default. Create one only when both conditions hold:

1. The repository contains the code of at least one surface an external agent can operate (the
   repository's own build scripts, tests, CI, and docs tooling do not count):
   - an importable library or SDK with public exports, including a UI component library (its
     components, hooks, and styles are a library API);
   - a CLI that does work (console scripts, `bin` entries, a `main` module meant for users);
   - a service interface: HTTP/REST, RPC, WebSocket, MCP server, or tool definitions;
   - a file format, config schema, or DSL that users write and the package consumes;
   - a plugin or extension contract that users implement.
2. An agent given only the README would likely misuse the package or miss its main capability,
   because correct use takes several steps, concepts that must be held together, or sharp edges
   that fail silently.

Do not create one when:

- the repository is documentation, content, notes, research, or data, and reading it is the whole
  use. A manifest counts as evidence only when this repository contains the code it builds; a
  published docs site with a `pyproject.toml` or `package.json` is still documentation;
- the only surface is a GUI. A CLI whose only job is to start the GUI (ports, URLs, open the
  browser) is part of the GUI surface;
- the entire use is one obvious command that the README quick start already shows;
- the package has no stable entry points yet, so a skill would freeze guesses. Revisit when the
  surface stabilizes.

State the decision and its evidence in your final report for the pass (for example "Agent skill:
created, the package exposes a Python API and the `foo` CLI" or "Agent skill: not created, the
repository is documentation only"). Do not add tracked files that record a negative decision.

Existing skills:

- An existing skill whose audience is an agent operating the package (its tools, CLI, or API) is
  the package skill, wherever it lives under `skills/`. Keep its name and structure; do not
  reshape it to the template below. Audit it against these rules and add only what is missing.
  If another surface also passes the decision, add a section or a `references/<surface>.md` file
  inside it instead of creating a second skill.
- Skills the package distributes as data for unrelated tasks (a skill registry or curated
  collection) are product content, not the package skill. Never rewrite them under this rule.
- If the surface an existing package skill teaches was removed, remove the skill and record the
  removal in `CHANGELOG.md`. Otherwise maintain it; never delete it to skip the work.

Scope:

- In a repository with several surfaces (server, SDKs, CLI, UI), teach the surface the docs
  recommend to external users, and route operator, contributor, and in-process surfaces to their
  docs.
- Default to one skill per repository. A monorepo with several packages gets one skill with a
  `references/<package>.md` file for each package it teaches; split into separate skills only for
  packages with unrelated audiences. Never create skills for nested repositories that this
  repository does not track. Name a monorepo skill after the repository, not after a private
  workspace root.
- For a meta-package or umbrella distribution, teach profile choice, install, and health checks,
  and route to each component's own skill or docs by absolute URL, at the component versions this
  distribution pins. Never restate component recipes.

## Location And Naming

- Put the skill at `skills/<name>/SKILL.md` at the repository root. This path is
  harness-neutral, visible on the code host, and installs as one folder copy.
- Default `<name>` to the package's distribution name, normalized: lowercase it, drop an npm
  `@scope/` prefix, and turn `_`, `.`, `/`, and repeated hyphens into a single `-`
  (`AbstractRuntime` becomes `abstractruntime`). The result must use lowercase letters, digits,
  and single hyphens, start and end with a letter or digit, be at most 64 characters, and equal
  the folder name.
- If a package skill already exists under another name, keep that name. Renaming breaks every
  existing install.
- Coredoc does not change packaging. Shipping the skill inside a wheel or npm tarball is a
  release-engineering decision for the maintainers, so do not add it. If the project already ships
  a copy as package data, keep that copy identical.

## Layout

```text
skills/<name>/
  SKILL.md          # required: frontmatter and the operating guide
  references/*.md   # optional: deeper material the agent opens on demand
  scripts/*         # optional: runnable programs, rarely needed
```

Keep `SKILL.md` under about 300 lines (roughly 3,000 to 5,000 tokens), because hosts load it whole
when the skill activates; shorter is better. Move material the main workflow does not need (a full
option table, an endpoint list, a schema, a second language, rare tasks) into `references/`, and
point to each file with one line saying when to open it.

The skill must work when none of its links can be reached: package hosts may be private, and
agents often run offline. Everything a recipe needs (result shapes, limits, error codes, the
options that matter) lives in `SKILL.md` or `references/`. Links are for going deeper.

## Frontmatter

```markdown
---
name: <name>
description: <What the package does, in task terms.> Use when <the tasks, the import name, the CLI name, file types, or service names that should make an agent reach for it>.
license: <the package license, for example MIT>
compatibility: <only when needed: runtime, OS, network, server or API version, sign-in>
metadata:
  package-version: "<version this skill teaches>"
---
```

- The `description` is all an agent sees before it decides to load the skill. Name the package,
  its import or CLI names, and the concrete tasks it covers. Keep it at most 1,024 characters and
  free of marketing language.
- `license` keeps the terms attached when the folder is copied away from `LICENSE`.
- Always set `metadata.package-version`: the released version of the surface the skill teaches,
  the upcoming version when the pass prepares a release, or `unreleased` when the surface is still
  under the changelog's Unreleased heading. Check it against `CHANGELOG.md`, and never claim a
  release that predates the surface.
- Use `compatibility` (at most 500 characters) for what the skill needs to work: a runtime
  version, an operating system, network access, the server or API version a client skill needs,
  or sign-in to a private package host.

## Body

For a new skill, write to the agent: imperative, terse, concrete, and faithful. Use these sections
in this order, and leave a section out only when it would truly be empty.

1. **Purpose and limits.** Two to four sentences on what the package does and when to reach for
   it, then what it is bad at, taken from the docs' limits or FAQ, with the documented
   alternative. An agent that does not know the limits reports wrong results with confidence.
2. **Install and verify.** The install command, and one verify step that proves the install
   works and prints the installed version (and, for a client, the server or API version).
   - The install command must work in a clean environment from the source it names (check with
     `pip index versions <dist>`, `npm view <pkg> version`, or the equivalent). If the package is
     not published, teach the documented source install and fix the docs that say otherwise.
   - The verify step is the first thing an agent runs in a broken environment. It passes only on
     a real result (non-empty output, the expected version), and reports each likely failure
     (missing configuration or credential, unreachable endpoint, failed authentication, wrong
     version) with a clear message instead of crashing. When the version is `unreleased`, it
     checks what identifies the surface (an API version, a feature probe), and a missing
     identifier fails.
   - Tell the agent to compare the installed version with `metadata.package-version`; the docs of
     the installed version win when they disagree with the skill. When the package needs a
     credential, tell the agent to ask the user to put it in an environment variable (never in
     the conversation), to pass it explicitly where the package could send an ambient one to the
     wrong host, and to stop at the first authentication failure.
3. **Mental model.** Three to seven bullets naming the concepts, objects, or resources an agent
   must hold to reason about the package, and how they relate. Name the settings the user docs
   present as a cost, time, or quality trade-off (a mode, tier, level, or model choice) and when
   to pick each value, and the defaults that silently cost time or money, with their values
   (timeouts, automatic retries, background downloads). State the package-wide error contract
   once here (which exceptions or error results callers must handle, and where it differs by
   backend), so recipes can rely on it.
4. **Capability map.** One line per major capability, with its entry point (function, class,
   command, or endpoint) and where the skill or its `references/` teach it, covering at least
   everything the README presents. Then the capabilities users commonly expect that the package
   does not have (for example "no built-in provider fallback: wrap calls yourself"), and its side
   effects: files, caches, or configuration it writes, and network calls it makes. An agent should
   never need to search the package to learn whether something exists.
5. **Recipes.** Start with the end-to-end workflow an expert follows for the package's main job,
   then the single tasks, ordered by how often users perform them in the package's main job (not
   by how many doc examples a feature has). Teach tasks, not a tour of the API: rare calls go to
   `references/`. For each recipe, give:
   - a one-line goal;
   - the minimal code or command, complete on its own with imports and real names (or starting
     with a comment naming the recipe it continues), with clearly marked placeholders such as
     `<MODEL_NAME>`, quoted in shell snippets;
   - handling of the failure and empty cases specific to the task (a failed status, an optional
     field that can be missing, an empty result, an unknown event type), relying on the error
     contract from the mental model for the rest;
   - what success looks like (output, return type, file produced), and the one or two options
     that change the result.
6. **Rules and sharp edges.** When calls cost money, take minutes, or change shared state, open
   this section with them: which calls, the cheap way to answer first, and what to confirm with
   the user. Then invariants and the mistakes an agent is most likely to make (wrong identifier,
   wrong call order, wrong default, silent failures, credentials sent where they should not go),
   each with how to avoid it. State each fact once in the skill; refer back instead of repeating.
7. **When things fail.** The three to five most common error messages or symptoms, each with
   cause and fix. Link to the troubleshooting page for the rest.
8. **Go deeper.** Absolute links to the docs (getting started, API reference, troubleshooting,
   `llms-full.txt`) and to the skill's own `references/` files, each with one line saying when to
   open it.

## Code: Snippets And Scripts

Code is how the skill turns knowledge into competence. Include it whenever the package has a
programmatic surface.

- Default to fenced snippets inside recipes. Each snippet must run as written once its marked
  placeholders are filled.
- Add a file under `scripts/` only when the code would exceed about 30 lines as a snippet or must
  run unattended, and the package provides no equivalent command in the environment the agent will
  have. Hosts that gate skills by trust (AbstractSkill among them) treat files under `scripts/` and
  code files anywhere in the folder as scripts and require review before activation, so a script
  must be worth that cost.
- Every script must be self-contained (the package and the standard library only), start with a
  header comment saying what it does and how to run it, read credentials only from environment
  variables, be safe by default (no destructive, paid, or remote calls unless behind an explicit
  argument), stay small and limited to the public API, and be referenced from `SKILL.md` with its
  exact run command relative to the skill folder.

## Faithfulness And Verification

Facts:

- Names, signatures, and field types may come from the public code. Behaviors, defaults, limits,
  error codes, timings, and the result shapes a recipe branches on must be in the docs: before
  finishing, list them and add any that the docs lack, in the same change. Never let the skill be
  the only place a fact lives, and keep the docs' qualifiers ("a soft target of 30 s" must not
  become "30 s").
- When the docs and the code disagree, the code wins: fix the docs. A fact several pages need is
  stated once and linked from the others; fix every page that restates it. If a docstring is
  stale, report it; do not edit code.
- When verification shows behavior that looks like a defect (an error that escapes the documented
  contract, input silently ignored, a crash), do not document it as intended. Keep the documented
  contract and add one line next to it ("Known issue (<version>): <behavior>. Workaround:
  <workaround>."); that line is the doc source for the workaround the skill teaches. Test the
  workaround on the exact calls the recipe makes, and list the defect with a reproduction in the
  pass report.
- When the package fronts several backends (providers, engines, databases, platforms), find its
  distinct code paths (from the class hierarchy or dispatch code), list them in the pass report,
  verify each claim on one backend per path, and label backend-specific behavior as such. Never
  generalize one backend's behavior to the rest.
- Teach what every user of the package meets, never facts from your own pass: your credentials,
  your deployment, or problems you hit while verifying belong in the pass report.
- Use only the public, documented API.

Running what you publish:

- Run every snippet and script at the highest tier you can reach safely, and record the tier in
  the pass report: (1) live, with read-only calls only, labeled "1 (stand-in: <server>)" when a
  local server speaking the same protocol stands in for the real service; (2) through the real
  package against the repository's own recorded fixtures or test server; (3) checked against
  code and tests, or run against a mock you built, which proves names and signatures, not
  behavior. A snippet's tier is the lowest tier of the calls it depends on, given per backend for
  backend-neutral snippets.
- Run the failure cases the skill names, plus one unreachable-endpoint run per backend code path.
  A snippet that crashes there, or reports success on an empty or truncated result, is wrong even
  if the docs show it: fix both.
- Never run write, delete, or paid calls against a deployment you do not own. Stop at the first
  authentication failure, never retry a login, and test authentication failures only by sending
  no credential, never an invented, old, or borrowed one.
- Isolate the run: unset real credentials, point configuration at a scratch directory (for
  example a temporary `HOME`), and point the client base-URL variables at a closed loopback port,
  so a snippet without an explicit endpoint fails locally. To run a cloud client against a local
  stand-in, pass the stand-in URL and any placeholder key as arguments in that call only, never
  in environment variables.

Maintenance:

- Update the skill in the same change as the API, CLI, configuration, or doc edits it describes,
  exactly as with `llms.txt` and `llms-full.txt`, and audit names, defaults, limits, error
  messages, `metadata.package-version`, and links on every pass.
- The external-facing rules of the core docs apply: no maintainer notes, no incident history, no
  documentation-generation commentary, and no time-relative wording.

## Links

The skill is copied out of the repository when someone installs it, so relative links into the
repository break.

- Link to repository docs with absolute raw-file URLs that return Markdown: on GitHub
  `https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>`, on GitLab
  `<repository URL>/-/raw/<ref>/<path>`. Link to a hosted docs site only with page URLs you have
  checked. When the host requires sign-in, say so in `compatibility`.
- `<ref>` is the tag of `metadata.package-version` when that tag already contains the skill
  folder, and otherwise the code host's default branch (`git ls-remote --symref
  <repository URL> HEAD`, not the clone's `origin/HEAD`). Switch to the version tag in the first
  release that ships the skill.
- Link to the skill's own files with relative paths (`references/<file>.md`, `scripts/<file>`).
- Check that `<ref>` contains the skill folder and every path the skill or its README snippet
  links or installs (`git ls-tree -r --name-only <ref> -- <paths>`). If it does not yet (an
  unmerged branch, an untagged release), still add the skill and its pointers in this change, and
  state in the pass report that they resolve once the change reaches `<ref>`.

## Point The Docs At The Skill

When the skill exists, the docs must tell agents about it:

- `README.md`: a short section like the one below. Use absolute URLs, because package indexes
  such as PyPI and npm render the README away from the repository. Fill in the real repository
  URL, `<ref>`, skill name, and skill folder URL (on GitHub
  `<repository URL>/tree/<ref>/skills/<name>`, on GitLab
  `<repository URL>/-/tree/<ref>/skills/<name>`). When `<ref>` already contains the skill, run the
  snippet once.

  ~~~markdown
  ## For AI agents

  If you are an AI agent, you can register and use our agent skill
  [`<name>`](<skill folder URL>) to become an expert on this package. Install it by copying the
  `skills/<name>/` folder of the version you use into your agent's skills directory (for example
  `~/.claude/skills` for Claude Code; see your agent's documentation for its skills directory):

  ```bash
  SKILLS_DIR=~/.claude/skills
  tmp="$(mktemp -d)"
  git clone --depth 1 --branch <ref> <repository URL> "$tmp" \
    && mkdir -p "$SKILLS_DIR" && cp -R "$tmp/skills/<name>" "$SKILLS_DIR/" \
    && echo "installed: $SKILLS_DIR/<name>"
  rm -rf "$tmp"
  ```
  ~~~

  Update `<ref>` in the same change as `metadata.package-version`.
- `docs/README.md`: list the skill in the index with one line on what it is for.
- `llms.txt`: an `## Agent Skill` section linking to `SKILL.md`, as shown in
  `references/llms-files.md`.
- `CHANGELOG.md`: record when the skill is added, removed, or changes in a way its users notice.

When there is no skill, add none of these.
