---
name: review
description: Run independent, evidence-based reviews across code quality, architecture fit, and user experience. Use when Codex is asked to review changes, validate an implementation, inspect a design, prepare a final quality pass, run critical reviewers, or ensure naive-user and expert-user expectations are met before finishing work.
---

# Review

Use this skill to produce a real approval gate. A review is not a summary of
changes; it is an evidence-based decision about whether the current state is
safe, coherent, and usable enough for the requested scope.

Read `references/reviewer-memory.md` when the task spans code, UX, operations,
or package boundaries, or when maintaining this skill itself.

When multiple reviewer skills are explicitly invoked together, `review` owns the
final ship-readiness verdict unless the user explicitly asks for an
architecture-only or UX-only judgment. `architect` owns decision-quality
recommendations. `uxreview` owns specialist human-usable verdicts. `review`
must synthesize their delivery impact, not silently replace them.

## Mandatory Independence

- If the user explicitly names `$review`, spawn independent review subagents
  whenever tooling allows.
- Default explicit swarm when no specialist reviewer skill is also named:
  `correctness`, `architecture-fit`, and `user-and-operations`.
- If `$uxreview` or `$architect` are also named, the added `review` lens is an
  `integrator` lens plus any technical lens not already covered by the named
  specialist swarms.
- Minimum fallback only when capacity is unavailable: two independent lenses,
  one technical and one user/operational. Mark that downgrade as `#FALLBACK`.
- `#FALLBACK` is allowed only when subagent tooling is unavailable in the
  environment or repeated spawn attempts fail.
- If `$uxreview` or `$architect` are also named, keep their swarms distinct and
  add at least one dedicated `review` integrator lens instead of silently
  substituting them away.
- If `$uxreview` is also named, consume the UX swarm's findings and decide
  ship or release impact. Do not run a second parallel generic UX verdict path
  unless the UX swarm is unavailable and `#FALLBACK` is declared.
- If `$architect` is also named, consume its structure and ownership findings
  and decide delivery risk. Do not rerun architecture exploration as generic
  review unless `#FALLBACK` is declared.
- Each reviewer must return findings, missing evidence, and a verdict before
  synthesis.

## Evidence Contract

- Inspect the real artifact before judging: code, diff, docs, tests, screenshots,
  browser state, or runtime behavior.
- Cite concrete evidence: file/line, endpoint, schema, failing scenario, test,
  UI state, command, or missing validation.
- Separate observed behavior from inference.
- If a key claim was not validated, say so directly.
- Do not approve because the implementation "looks reasonable".
- If a required artifact was not inspectable, the highest allowed verdict is
  `Conditional Approval` unless the scope explicitly excluded that artifact by
  design.

## Required Lenses

Apply the lenses that fit the task. For significant platform or UI work, use
all of them in synthesis even if some are delegated to named specialist skills.

- `correctness`: bugs, edge cases, error handling, security, performance,
  data loss, concurrency, and missing tests.
- `architecture-fit`: ownership, boundaries, source of truth, coupling,
  migration burden, compatibility, and ADR alignment.
- `user-and-operations`: default path clarity, labels, recovery, diagnostics,
  observability, approval burden, scale, and supportability.

## Verdicts

Use one verdict per reviewer and one final synthesized verdict:

- `Blocking`
- `Conditional Approval`
- `Approved`

Do not mark `Approved` when blocking evidence is missing, a required lens was
not covered, or the review skipped the artifact that users or operators will
actually touch.
If the skill was explicitly named and the mandatory subagent contract did not
run, the best possible verdict is `Conditional Approval` with `#FALLBACK`.
If the fallback minimum was also not met, the final verdict must be `Blocking`.

## Output Format

For code-heavy work, lead with findings:

- severity;
- file and line;
- behavior or risk;
- required fix or validation.

Then include:

- `Execution Mode`
- `Planned Reviewer Set`
- `Actual Reviewer Set`
- `Subagents Used`
- `Fallback Reason`
- `Contract Degradation`
- `Observed Evidence`
- `Inference Or Unverified Claims`
- `Reviewer Verdicts`
- `Open Questions Or Missing Evidence`
- `Residual Risk`
- `Final Verdict`

For design-heavy work, keep the same verdict structure but group issues by
blocking/non-blocking plus architecture-fit and user/operations impact.

If there are no findings, say so plainly and state what was actually checked.

## Field Memory

- `references/reviewer-memory.md` stores compact durable lessons for this skill.
- Update it only during skill-maintenance work and only with reusable lessons.

## Anti-Patterns

- Do not turn review into a changelog.
- Do not let clean code override bad UX or bad ownership boundaries.
- Do not call something "minor" if it can mislead a user or operator.
- Do not hide uncertainty behind broad confidence language.
- Do not collapse independent reviewer disagreement into fake consensus.
- Do not downgrade to fewer subagents for convenience, speed, or token economy
  without labeling `#FALLBACK` and naming the blocked capability.
