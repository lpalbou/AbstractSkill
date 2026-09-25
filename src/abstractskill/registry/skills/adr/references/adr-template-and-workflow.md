# ADR Template And Workflow

Use this file when creating or maintaining ADRs.

## Core Template

```markdown
# ADR <NNNN>: <title>

Status: Accepted.

## Context
What problem, constraint, failure mode, or recurring confusion triggered this ADR?

## Decision
What rule, boundary, contract, or design is being adopted?

## Consequences
### Positive
- Benefits

### Negative
- Tradeoffs and new costs

### Neutral
- Other impacts or follow-up implications

## Enforcement
How future work must comply: code review, warnings, searchable tags, backlog requirements,
completion reports, docs, harnesses, or recurrent hygiene.

## Validation
What tests, audits, or reproducible checks prove compliance.

## Backlog links
- Originating backlog items
- Adoption or enforcement backlog items
- Open drift backlog items

## Related
- Related ADRs
- Key docs or code symbols
```

Adapt the exact headings to local repo style when needed, but preserve the core ideas:

- status;
- context;
- explicit decision;
- consequences;
- enforcement;
- validation;
- explicit backlog linkage;
- related documents or code.

Optional fields that are often useful:

- `Dates`;
- `Packages affected` or `Areas affected`;
- `Authority owner` or `Source of truth`;
- `Superseded by` or `Deprecated`;
- `Before / after example`;
- `Readiness`, `Release gates`, or `Adoption state`;
- `Decision boundaries` when the ADR is easy to over-generalize.

Put optional metadata after `Decision`, after `Validation`, or in the index. Do not put a block of
metadata between `Status` and `Context` unless the existing repo format already requires it.

## Reader-First Gate

Before accepting or delivering an ADR, check the first screen:

- title and status are visible;
- `Context` appears before optional metadata;
- `Decision` appears soon after `Context`;
- a reader can say what problem the ADR solves before seeing packages, importance, or adoption
  state;
- no table or dashboard is the only explanation of the decision.

If an ADR fails this gate, rewrite the opening before adding more detail.

## ADR Index Schema

Keep one canonical ADR index or README. At minimum, track:

- id;
- title;
- status;
- supersedes or superseded-by when relevant;
- linked backlog items;
- last validation or hygiene touch if the repo already tracks that kind of state.

Keep the index as a map first. A short list of ADRs with titles, statuses, and one-line purposes is
usually better than a ranked governance dashboard. Add importance tiers or audit columns only after
the catalog is readable.

## Bootstrap A New ADR Set

When a repo has no ADR system and the user asks to set one up:

1. Create `docs/adr/README.md` when no other ADR index convention exists.
2. Create the numbered day-0 starter ADRs from `default-adr-catalog.md`.
3. Accept the day-0 starter ADRs by default unless the user asks for a proposed-only baseline.
4. Add only the conditional ADRs that are clearly triggered by the repo's actual behavior, public
   surface, or failure modes.
5. Cross-link backlog and docs as part of the same bootstrap pass when those systems already exist.
6. Keep feature-specific ADRs after the universal guardrail baseline unless the user asked for one
   specific feature ADR.

## Create A New ADR

1. Inspect the current code, docs, and backlog first.
2. Confirm the issue is broader than one local implementation detail.
3. Check whether an existing ADR already governs the issue.
4. Choose a narrow, durable decision boundary.
5. Write the ADR with concrete enforcement and validation, not vague aspirations.
6. Update the ADR index or README.
7. Cross-link originating, adoption, or drift-tracking backlog items and docs.

## Update Or Supersede An ADR

Use an update when the boundary is unchanged and the same ADR should keep its identity.

Use supersession or deprecation when a later design meaningfully replaces the older decision. In
that case:

1. Leave the historical ADR intact.
2. Mark its new status clearly.
3. Point to the replacement ADR.
4. Update index entries and related backlog items.

## Handle ADR Drift

When code, backlog, and ADRs disagree:

1. Stop assuming the ADR still matches reality.
2. Inspect what the code actually does.
3. Tell the user whether the code drifted from policy, the ADR became stale, or both.
4. Recommend one of:
   - fix the code to match the ADR;
   - revise the ADR to match the accepted new design;
   - add backlog work because the drift is known but not fixed yet.
5. Update docs and backlog together if the change affects process or operator expectations.

## Use Strong Enforcement Patterns

Prefer enforcement that can be checked later:

- searchable code tags for sensitive behaviors such as truncation or timeout sites;
- explicit warnings for fallback, truncation, timeout, or degraded-mode behavior;
- fail-closed behavior on correctness-critical paths;
- layer ownership rules that forbid downstream repair of upstream contract violations;
- backlog requirements that cite the governing ADR;
- completion reports that state how the ADR was validated;
- recurrent hygiene tasks that sample ADR compliance.
