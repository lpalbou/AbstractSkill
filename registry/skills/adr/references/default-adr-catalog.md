# Default ADR Catalog

Use this catalog when a project needs a portable starter set of ADRs. Tailor names, status, and
examples to the repo; do not copy every ADR verbatim.

Bootstrap in two layers:

- day-0 ADRs for failure semantics, architecture boundaries, ownership, reporting, and operator
  control;
- feature-triggered ADRs for risky behaviors such as truncation, timeout, tool execution,
  durability, memory, or audit.

Only use this catalog when the user asks to bootstrap an ADR system or governance baseline. If the
user asks for one specific ADR, write that ADR only.

When bootstrapping a new repo, create real ADR files from the day-0 starter pack below. Do not
stop at a prose summary of the catalog. Each starter ADR should use the reader-first template:
title, status, `Context`, then `Decision` before optional metadata.

## Default Day-0 Starter Pack

Create these ADRs by default for a new repo unless the user asks for a smaller baseline. These are
meant to be project-independent good-practice ADRs, not app-specific architecture decisions:

### 0001. Engineering Guardrails And No Silent Degradation

Suggested file: `docs/adr/0001-engineering-guardrails.md`

Decision intent:

- no silent fallback when behavior, evidence, or output quality changes;
- no silent truncation on user-visible, model-visible, or correctness-critical paths;
- explicit warnings or markers for degraded behavior;
- fail closed on correctness-critical paths unless the user explicitly accepts degraded mode.

### 0002. Validation And Testing Requirements

Suggested file: `docs/adr/0002-validation-and-testing.md`

Decision intent:

- every meaningful change declares its expected validation level;
- testing must be proportional to risk and surface area;
- new behavior, bug fixes, and safety-sensitive paths need reproducible checks, not only prose;
- completion reports or change notes state what was validated and what remains unverified.

### 0003. Responsibility Boundaries And Source Of Truth

Suggested file: `docs/adr/0003-responsibility-boundaries.md`

Decision intent:

- each contract has an authoritative owner;
- downstream layers do not quietly repair upstream contract violations;
- code is the operational source of truth, while ADRs, backlog, and docs explain and constrain it;
- configuration and compatibility shims stay explicit and auditable.

### 0004. Evidence-Based Reporting And Documentation Discipline

Suggested file: `docs/adr/0004-evidence-reporting-and-documentation.md`

Decision intent:

- consequential recommendations include scope, evidence, limits, and tradeoffs;
- docs, ADRs, and backlog items cross-link when one materially governs another;
- observed facts are kept distinct from inference or aspiration;
- durable process or architecture changes are recorded in ADRs instead of disappearing into chat or
  PR prose.

### 0005. Source-First And Root-Cause-First Quality Fixes

Suggested file: `docs/adr/0005-source-first-quality-fixes.md`

Decision intent:

- fix quality, correctness, routing, parsing, and generated-output problems at the producer or
  data-flow boundary first;
- downstream cleanup is allowed only when the source is external, untrusted, or not fully
  controllable;
- fallback behavior must not make broken state look healthy;
- validation should prove the source invariant, not only the downstream normalization.

## Reusable Policy Themes

### 1. AI Engineering Guardrails

Capture the core quality bar:

- no silent fallback when behavior or evidence changes;
- no silent truncation on model-visible, user-visible, or correctness-critical paths;
- explicit warnings or markers for degraded behavior;
- clean abstractions over broad orchestration rewrites;
- a documented validation ladder such as A/B/C or unit/integration/e2e.

Typical enforcement:

- fallback and truncation checks in review;
- searchable code markers near truncation or timeout decisions;
- completion reports that state validation levels.

### 2. Code-First Backlog And Planning Process

State that backlog items are planning memory, not code truth. Require code and doc inspection
before writing or implementing backlog items, and require stale backlog text to be fixed before
coding against it.

### 3. Evidence-Based Reporting And Decision-Grade Recommendations

Require reports, benchmarks, and completion notes to define metrics, parameters, limits, and the
decision boundary. For consequential recommendations, require more than a scan table: plain
language, examples, risks, and what is out of scope.

### 4. Root-Cause-First And Source-First Quality Fixes

Require quality problems to be fixed at the producer, data-flow boundary, or contract boundary
before downstream cleanup. Allow downstream cleanup only when the source is external, untrusted, or
not fully controllable.

### 5. Truncation Policy And Contract

Forbid silent lossy truncation. Require explicit warnings, markers, or metadata, and fail loudly
on correctness-critical paths that cannot tolerate partial content.

Good triggers:

- response slicing;
- context clipping;
- memory or artifact previews;
- schema or extraction outputs with budget caps.

### 6. Timeout Policy And Contract

Forbid silent timeouts. Require the surfaced duration, responsible component, and configured source
when possible. Use conservative defaults on correctness-critical paths and treat timeouts as
observable safeguards rather than hidden performance knobs.

### 7. Architecture Boundaries And Dependency Direction

Define layering, ownership boundaries, or package responsibilities so future changes do not create
hidden coupling. This is especially important for multi-package repos, runtimes, gateways, or
plugin systems.

### 8. Provenance, Scope, And Access Boundaries

Define how memories, context, artifacts, attachments, user data, or cross-project information keep
source provenance and scope boundaries. Prefer faithful storage plus explicit retrieval or display
controls over silent distortion of underlying truth.

### 9. Operator Control, Configuration Precedence, And Compatibility

Define who controls runtime-affecting behavior, how config layers override each other, and how
compatibility shims or provider-specific behavior stay explicit and auditable.

### 10. Responsibility Boundaries And Single Source Of Truth

Define which layer or component owns each contract and prohibit downstream layers from quietly
repairing upstream failures. This is especially important for tool pipelines, parsers, runtimes,
gateways, and derived metadata.

### 11. Deprecation, Supersession, And Release Gates

Define how major design reversals are recorded, how old decisions stay discoverable, and what
minimum validation or documentation updates are required before release or migration.

## Common Conditional Additions

Add these only when the repo behavior actually triggers them:

### 0006. Code-First Backlog And Planning Process

Suggested file: `docs/adr/0006-code-first-backlog-process.md`

Create when the repo uses backlog files or durable planning artifacts.

### 0007. Truncation Contract

Suggested file: `docs/adr/0007-truncation-contract.md`

Create when the system clips, slices, previews, summarizes, or token-budgets content.

### 0008. Timeout And Cancellation Contract

Suggested file: `docs/adr/0008-timeout-and-cancellation.md`

Create when requests, jobs, background work, tools, or agent workflows have time budgets or
interrupt semantics.

### 0009. Fallback And Degraded-Mode Contract

Suggested file: `docs/adr/0009-fallback-and-degraded-mode.md`

Create when the system retries, falls back to alternate providers or code paths, or has
intentionally degraded operation.

### 0010. Provenance, Data Scope, And Access Boundaries

Suggested file: `docs/adr/0010-provenance-and-data-scope.md`

Create when the repo stores, retrieves, or reuses user data, artifacts, memories, cross-project
context, or sensitive metadata.

### 0011. Operator Control And Configuration Precedence

Suggested file: `docs/adr/0011-operator-control-and-config-precedence.md`

Create when multiple config layers, feature flags, provider shims, environment overrides, or
deployment modes can materially change behavior.

### 0012. Release, Migration, And Deprecation Gates

Suggested file: `docs/adr/0012-release-and-deprecation-gates.md`

Create when the repo has public APIs, releases, migrations, plugin ecosystems, or user-visible
breaking changes.

## Strong Additions For Agentic Systems

Add these when the system has agents, tools, memory, or long-running workflows:

- explicit active versus passive memory behavior;
- tool-calling responsibility boundaries;
- observability and audit contracts;
- durable execution, pause, resume, or cancellation semantics;
- participant-aware provenance and disclosure controls;
- labeled inference versus observed fact in memory or world-model outputs.

## Heuristics For Promoting A Rule Into An ADR

Create an ADR when the rule:

- affects multiple future tasks;
- changes operator trust or failure semantics;
- changes architecture, routing, storage, provenance, or security boundaries;
- needs enforcement and validation beyond one PR;
- would be costly to rediscover from chat history alone.

Leave it as a backlog or implementation note when it is:

- a one-off bug fix;
- a purely local refactor;
- an experiment without durable acceptance yet.
