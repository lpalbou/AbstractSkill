---
name: architect
description: Force rigorous architecture exploration before settling on a design. Use when Codex must evaluate platform architecture, package boundaries, service ownership, data/control-plane responsibility, security or scalability tradeoffs, multi-agent design discussions, or any task where premature consensus would be harmful and multiple valid designs should be compared.
---

# Architect

Use this skill to force real architecture competition before committing to a
design. The goal is not endless divergence; it is to prevent premature
consensus, weak boundaries, and decisions that look simple only because the
tradeoffs stayed implicit.

Read `references/reviewer-memory.md` when the decision touches ownership,
package boundaries, source-of-truth questions, or platform migration.

## Mandatory Independence

- If the user explicitly invokes this skill by name (for example
  `$architect` or "use the architect skill"), spawn independent architecture
  subagents whenever tooling allows.
- Default explicit swarm: three distinct charters.
- Recommended default charters:
  - `minimalist`: smallest reversible change that meets the need;
  - `platform`: shared contract and long-term coherence;
  - `security-operations`: authority, isolation, observability, and recovery.
- Swap one charter for `user-workflow` when the main tension is product/process
  design rather than security or operations.
- Minimum fallback only when capacity is unavailable: two materially different
  charters. Mark that downgrade as `#FALLBACK`.
- `#FALLBACK` is allowed only when subagent tooling is unavailable in the
  environment or repeated spawn attempts fail.
- Each charter must argue for its own design, state its own objections, and
  issue its own recommendation before synthesis.
- Charters are perspectives, not automatically separate design candidates. By
  default they should critique a shared candidate set. A charter may introduce
  a new candidate only when it is materially different and improves the set.

## Evidence Contract

- Inspect the current system before proposing alternatives: code, ADRs, docs,
  package boundaries, APIs, storage, operational shape, and existing UX.
- Cite current-reality evidence, not just ideal architecture language.
- Verify each load-bearing premise against the current tree or running state
  before arguing from it, and date-stamp the verification. Designs argued
  from stale or inherited premises ("that file exists", "that default is X",
  "that path is already wired") are a common, expensive failure class;
  premises decay while discussions run.
- When tree and running state can differ (served processes, built bundles,
  installed copies), verify the copy the user actually runs, and name which
  copy you verified.
- Name unknowns explicitly.
- Do not recommend a boundary change without mapping ownership and migration.

## Decision Protocol

1. State the decision question in one sentence.
2. Record constraints, non-goals, current reality, and unknowns.
3. Generate at least three materially different alternatives.
   `keep current` and `defer or split the decision` are valid alternatives when
   they are genuine options, not filler.
4. Steelman each alternative: when it is the right answer.
5. Critique each alternative: failure modes, coupling, migration burden,
   security risk, operability, user impact, and reversibility.
6. Surface tensions explicitly.
7. Recommend, defer, or split the decision only after comparison.
8. State what evidence would change the recommendation.
9. Include a compact comparison matrix across ownership, migration cost,
   user impact, operational burden, reversibility, and evidence gaps.

## Architecture Gates

Check these explicitly:

- ownership and source of truth;
- bounded context and terminology fit;
- control-plane versus data-plane placement;
- authority and least-privilege model;
- operational load, observability, and failure isolation;
- migration path and rollback/reversibility;
- engraving: names, keys, or formats reaching append-only or at-rest state
  are effectively irreversible — decide spellings before the first real
  write;
- user workflow consequences, not just package cleanliness.

## Verdicts

Use one verdict per charter and one final synthesized verdict:

- `Recommend`
- `Recommend With Reservations`
- `Not Ready To Recommend`

Do not produce `Recommend` if alternatives were strawmen, current reality was
not inspected, or major tensions remain unnamed.
These are decision-quality verdicts, not ship-readiness verdicts.
If the skill was explicitly named and the mandatory subagent contract did not
run, the best possible verdict is `Recommend With Reservations` with
`#FALLBACK`. If the fallback minimum was also not met, the final verdict must
be `Not Ready To Recommend`.

## Output Format

Use concise sections:

- `Execution Mode`
- `Planned Reviewer Set`
- `Actual Reviewer Set`
- `Subagents Used`
- `Fallback Reason`
- `Contract Degradation`
- `Decision Question`
- `Current Reality`
- `Observed Evidence`
- `Inference Or Unknowns`
- `Alternatives`
- `Comparison Matrix`
- `Charter Verdicts`
- `Tensions`
- `Recommendation`
- `Evidence Needed`

If all reviewers converge, still report the tensions and why the losing
alternatives lost.

## Field Memory

- `references/reviewer-memory.md` stores compact durable lessons for this skill.
- Update it only during skill-maintenance work and only with reusable lessons.

## Anti-Patterns

- Do not let "simpler" stand in for unexplained tradeoffs.
- Do not accept package ownership by inertia.
- Do not use strawman alternatives.
- Do not hide user or operator impact behind backend language.
- Do not collapse "server", "runtime", "workspace", or similar terms unless the
  authority model is truly the same.
- Do not encode an implementation workaround into a name or structure when
  the fix belongs in a contract: one concept gets one name, and a second name
  minted to route around a flawed writer or reader outlives the flaw and
  becomes permanent vocabulary debt.
- Do not downgrade to fewer subagents for convenience, speed, or token economy
  without labeling `#FALLBACK` and naming the blocked capability.
