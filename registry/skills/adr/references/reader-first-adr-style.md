# Reader-First ADR Style

Use this reference when writing ADRs from scratch, bootstrapping a repo, or repairing ADRs that feel
like audit worksheets.

## Good ADR Shape

A strong ADR starts by making the reader understand the decision:

```markdown
# ADR 0001: Engineering guardrails

Status: Accepted.

## Context

What recurring risk, failure mode, or design pressure makes this decision necessary?
Why does it matter now? What has gone wrong before, or what would go wrong without a rule?

## Decision

What rule or boundary is now accepted? Make it explicit enough to constrain future work.

## Consequences

What gets better, what gets harder, and what remains outside this decision?

## Enforcement

How future agents, reviewers, tests, docs, or backlog hygiene should catch drift.

## Validation

What proves compliance or lets a future agent audit the decision.

## Related

Relevant ADRs, backlog items, docs, or code symbols.
```

This order is intentional. `Context` and `Decision` are the ADR. Metadata supports them; it should
not stand in front of them.

## Opening Rules

- Put `Context` immediately after status unless the local repo already has a stricter format.
- Put `Decision` directly after `Context`.
- Make the first `Context` paragraph explain the actual problem in plain language.
- Use concrete examples when they clarify the failure mode.
- Treat `Consequences`, `Enforcement`, and `Validation` as required for accepted ADRs.
- Keep optional metadata such as dates, affected packages, owner, importance, adoption state, and
  current code reality after the main decision or in the ADR index.

## What To Avoid

- Do not open with `Importance`, `Packages affected`, `Authority owner`, `Adoption state`, or
  `Current code reality`.
- Do not make the index a ranked control dashboard before it is a readable ADR catalog.
- Do not present a decision only as a table.
- Do not bury a one-sentence decision behind implementation inventory.
- Do not accept an ADR whose title could be understood but whose first page does not explain why
  the ADR exists.

## Portable Style From The Local Examples

The strong local ADRs share a pattern:

- `0001-ai-engineering-guardrails`: starts with the risk of silent fallbacks, hidden truncation,
  vague abstractions, and weak tests, then turns those risks into concrete rules.
- `0004-code-first-backlog-process`: starts from a real failure where backlog text drifted from
  code reality, then defines a code-first process.
- `0007-root-cause-first-no-workaround-fallbacks`: starts from the danger of hidden fallback
  behavior, then defines when fallback is acceptable.
- `0012-evidence-based-results-reporting`: starts from why unexplained tables are not evidence,
  then defines the reporting contract.
- `0015-source-first-quality-fixes`: starts from concrete downstream cleanup mistakes, then
  requires fixes at the producer or data-flow boundary.

The reusable lesson is not their exact wording. The reusable lesson is that the ADR earns the
decision with a real problem statement before adding policy detail.

## ADR Index Style

An index should answer these first:

- What ADRs exist?
- Which are accepted, proposed, superseded, or deprecated?
- What is each ADR for?
- Which backlog items or docs are materially linked?

Importance tiers, risk rankings, adoption notes, and improvement pressure can be useful, but they
belong after the catalog or in a separate audit section. If they come first, future agents may copy
the dashboard shape into the ADR files themselves.
