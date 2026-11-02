---
name: abstractframework-website
description: Update the abstractframework.ai website after a release wave so it describes the framework that is actually published (versions, install commands, every app and capability, refreshed screenshots and llms mirrors), verify every claim against code and registries, serve the result locally and hand the operator a preview URL. The site is GATED - this skill never pushes gh-pages; the operator validates the preview and publishes. Use at the end of every abstract-release wave, when the operator asks whether the site is current, or when a page describes a package that moved.
---

# AbstractFramework website update (gated)

The site at https://abstractframework.ai is the `gh-pages` branch of lpalbou/AbstractFramework:
static HTML (`index.html`, one page per package and per persona, `llms*.txt` mirrors, screenshots
under `assets/`). Its job is to describe the framework a person can install TODAY. After every
release wave it must say the released versions, the install commands that resolve, every app that
exists (desktop, web, iPhone, watch, consoles), every capability (text, voice, vision, music, 3D,
camera, memory, decisions, entities, automations) and what changed, in the operator's voice.

**The gate.** This skill ends with a local preview URL and a branch, never with a push. The
operator reads the preview, asks for changes, and pushes `gh-pages` personally. A worker that
pushes, force-pushes, or rebases `gh-pages` has broken the operator's one rule for this surface.

## Paths

- Site worktree: `/Users/albou/tmp/abstractframework-ghpages` (a git worktree of the root repo on
  a site branch). Published ref: `origin/gh-pages`. Start every update from it:
  `git -C <worktree> fetch origin && git -C <worktree> switch -c site-<root version> origin/gh-pages`
  (one branch per root version; an existing branch for the same version is resumed, never recreated).
- Method and history: `/Users/albou/tmp/abstractframework/untracked/site-rethink/` (PLAN.md,
  REPORT.md with the operator's rounds, CLAIMS.md, examples/, deliver/, shots/). Read REPORT.md's
  operator rounds before changing copy: they are the record of what was accepted and refused.
- Preview server: `python3 references/preview_server.py <worktree> --port 56265` (Range-capable,
  needed for the videos). The URL to hand over is `http://127.0.0.1:56265/`.
- Workspace: `/Users/albou/tmp/abstractframework/<repo>` (each its own git repo; `git -C`).

## Invariants (operator decisions; keep them unless the operator changes them on the record)

- Identity: the original dark site; content changes, identity does not. Tagline
  "Write once. Generate everything. Run anywhere." Modality order voice, music, vision, 3D, camera.
- Install: exactly three profiles, `abstractframework`, `abstractframework[apple]`,
  `abstractframework[gpu]`, plus the short installer addresses (`abstractframework.ai/install.sh`,
  `/install.ps1`, `/uninstall.sh`). Never `[remote]`, `[mlx]` or a per-package pip line as the
  primary path. Provider badges list every provider the text names, never trimmed.
- Names: PascalCase package names in prose (AbstractCore, AbstractAssistant); "Consoles" is not
  a package; the Assistant is "One Click Away", never "Built for macOS" (OS-agnostic, tested most on
  Apple). Entities are "persistent, self-evolving agents ... we are defining the field here", the
  identity planted once; memory is reconstruction (passive / active / durable).
- The "Ledger Is the Record of the Run" animation stays as it is.
- Every code block is either RUN (a hermetic example under `untracked/site-rethink/examples/`,
  its `run.log` next to it, the HTML comment `E<n> PASS`) or carries a visible "not executed" note.
  No worker runs model generation for the site beyond what an example needs; one model process at
  a time on the machine (the live gateway owns the GPU).
- Screenshots come from a fresh scratch install of the RELEASED matrix (never from a dev tree),
  captured at the sizes the page uses, including a 400 px phone capture for every new page or
  redesigned interface. A pre-release capture is captioned as such.
- Claims are text-only when the code says so: the adversary of 2026-09-29 found the operator's own
  framings false in code (no hash-chained gateway ledgers, no re-execution on replay, `create_llm`
  needs a provider). Verify before writing, write what the code does.

## Procedure

1. **Inventory what is published.** `python3 ~/.codex/skills/abstract-release/scripts/abstract_release_plan.py <workspace> --registry`
   plus the root's `abstractframework/__init__.py` (`RELEASE_VERSIONS`, `NPM_RELEASE_VERSIONS`,
   `CRATE_RELEASE_VERSIONS`) and `pip download abstractframework==<v> --no-deps` for the pins.
   The site states the ROOT version and the versions the root pins; nothing "coming".
2. **Diff the site against reality.** For every page: the versions it names, the install lines,
   the package list, the apps and capabilities it describes, the screenshots' provenance, the
   llms mirrors' headers. `grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+" *.html | sort | uniq -c` finds stale
   numbers fast. Read each released package's CHANGELOG from the version the site names to the
   released one: that is the list of new features and fixes to tell.
3. **Write the update ledger first** (`untracked/site-<root version>/CLAIMS.md`, same shape as the
   2026-09-29 ledger): every factual claim to add or change, with the repository line, registry
   JSON, or example run that supports it; every page to touch; every screenshot to refresh and
   from which scratch install. New apps get their own section or page (the Assistant's web, iPhone
   and watch apps; a new console); a new capability gets its place in the home grid and on the
   package page that provides it (decision models on core.html, with the model family named as the
   package docs name it).
4. **Apply the changes** on the site branch, in commits named `site <root version>: <what>`.
   Refresh `llms.txt` / `llms-full.txt` mirrors from each released repository's main at the tag
   (headers kept). Regenerate `sitemap.xml` when pages are added.
5. **Check.** `python3 references/check_site.py <worktree>`: every local link and asset resolves,
   every page has one `<title>`, no leftover `TODO`/`PENDING` markers, every `<img>` exists and has
   `width`/`height`, no version string older than the root's pins unless the ledger explains it, no
   "coming soon". Open every changed page in the preview at desktop width and 400 px and look at it;
   record a screenshot of each under `untracked/site-<root version>/shots/`.
6. **Adversarial pass.** A reader that did not write the pages checks the ledger line by line
   against the code and the registries, and the copy against the invariants above; fix or
   withdraw every finding on the record (`REVIEW-<n>.md`).
7. **Serve and hand over.** Start the preview server on the worktree, confirm it answers, and
   end with the handover block below. Do not push. Do not merge into `gh-pages`. Leave the
   worktree on the site branch so the operator's rounds continue there.

## Handover block (the last thing a run prints)

```
Site branch: site-<root version> @ <sha> (worktree /Users/albou/tmp/abstractframework-ghpages)
Preview: http://127.0.0.1:56265/   (server pid <pid>; restart: python3 ~/.codex/skills/abstractframework-website/references/preview_server.py <worktree> --port 56265)
Changed pages: <list>   New pages: <list>   Screenshots refreshed: <n> (from abstractframework==<v> scratch install)
Ledger: untracked/site-<root version>/CLAIMS.md   Review: REVIEW-1.md (<n> findings, <m> fixed)
Not done / needs you: <anything the operator must decide or capture>
To publish (operator only): git -C <worktree> push origin site-<root version>:gh-pages
```

## Pitfalls

- A site built from the dev checkouts drifts from what `pip install` gives: scratch-install the
  released root profile for screenshots and example runs (`uv venv` + `uv pip install
  abstractframework[apple]==<v>` with `UV_CACHE_DIR=/Users/albou/.cache/uv`; delete the venv after).
- The home page is one 180 KB file with inline sections per package: edit the section, not the
  whole file; keep `assets/` names stable so the operator's cached screenshots stay valid.
- `llms-full.txt` mirrors are large; refresh them from the released tag, not from a working tree
  that carries unreleased docs.
- A page for an app that exists on one platform only says so plainly (the watch app is watchOS,
  the iPhone app iOS, the web app runs where the gateway runs).
