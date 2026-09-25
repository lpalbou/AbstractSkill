---
name: adr
description: Create, audit, update, and enforce ADRs as durable cross-task engineering policy. Use when Codex needs to write a new ADR, revise or deprecate an existing ADR, derive an ADR baseline for a project, check whether a code or design change conflicts with accepted decisions, or keep backlog, docs, and validation aligned with architecture and process rules. Do not use ADRs for ordinary task sequencing or one-off implementation details; keep those in backlog unless they establish a rule that should outlive the task.
---

# ADR System

Use ADRs for decisions that outlive one ticket or one conversation. An ADR should constrain future
design, implementation, testing, and reporting; if it cannot change behavior later, it may not
need to be an ADR.

## Start With The Right Pass

- If asked to change design or architecture, read the ADR index and the most relevant ADRs before
  proposing code or backlog changes.
- If asked to create a new ADR system or bootstrap ADRs for a new repo, read
  `references/adr-template-and-workflow.md`, `references/reader-first-adr-style.md`, and
  `references/default-adr-catalog.md` first, then create a concrete starter set instead of
  stopping at a catalog or brainstorm.
- If asked to add or update a single ADR, inspect current code, docs, and backlog first so the ADR
  reflects reality rather than speculation.
- If a code change appears to conflict with accepted ADRs, stop and surface the drift. Recommend
  whether to revise the ADR, change the design, or create follow-up backlog work.
- If the user asks for one ADR, write one ADR. Seed a wider baseline only when the user asks for an
  ADR system, governance baseline, or default catalog.
- When no repo convention exists and the task is to bootstrap ADRs, create `docs/adr/README.md`
  plus numbered ADR files under `docs/adr/`.

## Apply The Operating Rules

- Keep ADRs short enough to scan but strong enough to enforce.
- Make ADRs reader-first. After the title and status, the next substantive section should explain
  the problem in `Context`, followed by the actual `Decision`.
- Write ADRs only for durable decision boundaries: architecture, safety and quality contracts,
  compatibility promises, provenance rules, testing and reporting baselines, operating policies,
  and explicit non-goals.
- Prefer one ADR per durable decision boundary. Split mixed ADRs when they hide separate policies.
- Treat accepted ADRs as live policy. Reference them from backlog items, implementation notes,
  completion reports, and user-facing recommendations when relevant.
- `adr` owns durable cross-task rules. `backlog` owns execution planning, task state, and
  completion history.
- Add `Enforcement` and `Validation` sections. A decision without enforcement is advice; a
  decision without validation is hard to audit.
- Prefer explicit ownership and scope metadata when useful: affected packages or areas, authority
  owner, and readiness or release gates. Put this metadata after `Decision` or near the end unless
  the repo's established ADR format requires otherwise.
- Surface tradeoffs and limits explicitly. Silent tradeoffs create future drift.
- Update the ADR index and related backlog or docs when status changes.
- When current behavior violates a desired rule, say whether the ADR is aspirational for new work
  only or whether current code already conforms.
- Do not silently weaken policies with hidden fallbacks, silent truncation, silent timeout
  behavior, or downstream cleanup that masks source problems. Prefer explicit warnings, root-cause
  fixes, and fail-closed behavior on correctness-critical paths.
- When a contract crosses multiple layers, name the authoritative producer and prohibit downstream
  layers from quietly compensating for broken upstream behavior.

## Decide Whether To Create, Update, Or Skip

- Create a new ADR when the decision will govern multiple future changes or multiple packages,
  modules, or surfaces.
- Update an existing ADR when the boundary is the same but the policy, status, or evidence changed.
- Deprecate or supersede an ADR instead of editing history away when a later design replaces it.
- Skip an ADR when the matter is local implementation detail, a one-off experiment, or already
  fully governed by an accepted ADR.
- In mixed cases, use ADR first when the primary job is to establish or revise a rule that should
  constrain future work beyond the current item. Use backlog first when the primary job is to plan,
  sequence, execute, or close a task.

## Write Strong ADRs

- State the triggering problem and why it matters now.
- Make the decision explicit, not implied.
- Do not start an ADR with a dashboard of importance, packages, adoption state, code reality, or
  improvement pressure. Those details can be useful later, but they must not delay `Context` and
  `Decision`.
- Spell out consequences, especially added operator burden, reduced convenience, failure modes, or
  deferred work.
- State enforcement points: code review rules, lint or search tags, completion-report
  requirements, runtime warnings, gating tests, docs updates, or recurrent hygiene.
- State validation: what tests, harnesses, audits, or reproducible checks prove compliance.
- Link to backlog items, docs, symbols, or examples that anchor the decision in real work.
- When an ADR comes from real implementation work, link the originating backlog item and any
  adoption, enforcement, or open-drift items instead of relying on prose alone.
- For consequential recommendations, do not rely on a summary table alone. Provide decision-grade
  explanation, boundaries, risks, and at least one concrete before or after example.

## Preserve A Default Guardrail Baseline

- When a project lacks ADRs and the user asks for an ADR system, create a concrete default starter
  pack from `references/default-adr-catalog.md`. Start with the universal day-0 ADRs, then add
  only the feature-triggered ADRs that match real repo behavior or risk.
- Do not stop at advisory lists when bootstrapping a new repo. Produce real ADR files and the ADR
  index so future work has something enforceable to cite.
- Treat explicit truncation, timeout, fallback, provenance, validation, and reporting contracts as
  first-class policy candidates, not incidental implementation notes.
- Prefer category-specific contracts when the failure mode is risky: separate ADRs for truncation,
  timeout, responsibility boundaries, release gates, or provenance usually age better than one
  overloaded "quality" ADR.
- Keep backlog and ADR maintenance connected. New invariants discovered during implementation or
  completion review may require ADR updates even when the code task is done.

## Use References Selectively

- Read `references/adr-template-and-workflow.md` when drafting, revising, or superseding ADRs.
- Read `references/reader-first-adr-style.md` before writing ADRs from scratch, bootstrapping ADRs
  in a repo, or repairing ADRs that feel like compliance worksheets.
- Read `references/default-adr-catalog.md` when bootstrapping a project or when a repo is missing
  stable guardrails.
