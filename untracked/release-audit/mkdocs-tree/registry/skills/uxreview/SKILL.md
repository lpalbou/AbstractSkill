---
name: uxreview
description: "Run focused human user-experience reviews of products, apps, websites, workflows, dashboards, forms, modals, navigation, and frontend designs. Use when Codex is asked for a UX review, usability review, design review, product workflow critique, naive/intermediate/expert user review, accessibility/usability pass, or when a frontend implementation must be checked for whether users can do what they need simply, confidently, and pleasantly."
---

# UX Review

Use this skill as a user-protection failsafe. It exists to catch confusing,
redundant, jargon-heavy, inaccessible, or misleading interfaces before they
ship or before they are approved.

Read `references/reviewer-memory.md` when the task is UI-heavy, when labels or
workflow complexity are in question, or when maintaining this skill itself.

## Mandatory Independence

- If the user explicitly names `$uxreview`, spawn independent UX-review
  subagents whenever tooling allows.
- Default explicit swarm: `naive`, `intermediate`, and `expert`.
- Minimum fallback only when capacity is unavailable: `naive` plus `expert`.
  Mark that downgrade as `#FALLBACK`.
- `#FALLBACK` is allowed only when subagent tooling is unavailable in the
  environment or repeated spawn attempts fail.
- Keep persona prompts independent. Do not tell one persona what another found.
- Each persona must issue its own findings and verdict before synthesis.
- If `$review` or `$architect` are also named, keep UX reviewers distinct. They
  may inform the larger review, but they are not optional.
- If `$review` is also named, `uxreview` remains the specialist human-usable
  verdict. `review` may synthesize release impact, but it should not silently
  replace or duplicate the UX swarm unless `#FALLBACK` is declared.
- If persona verdicts disagree, treat that disagreement as a product-risk
  signal. Do not smooth it away in synthesis.

## Evidence Contract

- Prefer a live UI, screenshot, prototype, or browser inspection over code-only
  inference.
- If only implementation is available, say `implementation-only` and treat
  UI-sensitive claims as unverified until a visible artifact is inspected.
- For UI-heavy work, `Approved` requires direct inspection of a visible
  artifact. Code-only or spec-only review caps the best verdict at
  `Conditional Approval`.
- Cite concrete evidence: visible label, control, focus path, state change,
  error text, empty state, responsive layout, or keyboard behavior.
- Do not approve a UI because the code is clean.

## Review Gates

Check these explicitly:

- Task clarity: does the user know what this screen/workflow is for?
- Next-step clarity: is the obvious action visible and named well?
- Labeling and terminology: plain language, no internal ids, no duplicate
  concepts with different names, no different concepts with the same name.
- Critical distinctions: source, ownership, permanence, scope, and consequence
  are visible where the decision is made.
- Recognition over recall: the UI should show choices and consequences instead
  of making the user remember them.
- Workflow simplicity: minimal steps, minimal mode switching, minimal guessing.
- Feedback and recovery: success, waiting, failure, and blocked states explain
  what happened and what to do next.
- Accessibility: keyboard reachability, focus visibility, semantic controls,
  readable contrast, motion restraint, and usable target sizes.
- Scale and supervision: provenance, filters, diagnostics, batch actions, and
  large-state usability for operational surfaces.
- False confidence: polished styling must not hide ambiguous behavior, silent
  failure, or missing consequences.

Run these explicit passes:

- Primary walkthrough: entry point -> orientation -> decision -> action ->
  feedback -> completion.
- Misuse pass: likely wrong click, wrong source, wrong scope, wrong expectation,
  and wrong recovery path.
- Hidden-consequence test: what will the user think happens, what actually
  happens, what persists, what changes scope, and what is externally visible.
- State coverage: inspect or explicitly mark uninspected `entry`, `happy path`,
  `waiting`, `empty`, `error`, `permission/approval`, `responsive`, and
  `keyboard-only` states where applicable.

## Persona Charters

Use these default charters:

- `naive`: first-time or occasional user. Prioritize plain language, obvious
  next steps, fear/confusion triggers, and whether the happy path is clear.
- `intermediate`: familiar with the domain but not product internals.
  Prioritize workflow efficiency, terminology consistency, and recovery.
- `expert`: technical or operational user. Prioritize provenance, overrides,
  diagnostics, auditability, scale, and trustworthy advanced behavior.

Each persona should answer:

- what they think the screen/workflow does;
- what they would do next;
- what confused or slowed them down;
- what would make them mistrust the system;
- the top changes required before approval;
- their verdict.

## Verdicts

Use one verdict per persona and one final synthesized verdict:

- `Blocking`: users are likely to fail, misinterpret, or take unsafe action.
- `Conditional Approval`: usable with specific fixes or missing validation.
- `Approved`: no blocking UX risk found in the reviewed scope.

Do not mark `Approved` if labels are misleading, critical distinctions are
hidden, keyboard/accessibility behavior is broken, or a visible artifact was
available but not inspected.
If the skill was explicitly named and the mandatory subagent contract did not
run, the best possible verdict is `Conditional Approval` with `#FALLBACK`.
If the fallback minimum was also not met, the final verdict must be `Blocking`.

## Output Format

Use this structure:

- `Execution Mode`
- `Planned Reviewer Set`
- `Actual Reviewer Set`
- `Subagents Used`
- `Fallback Reason`
- `Contract Degradation`
- `Observed Evidence`
- `Inference Or Unverified Claims`
- `Blocking UX Issues`
- `Terminology And Meaning Risks`
- `Critical Distinctions`
- `State Coverage`
- `High-Value Improvements`
- `Persona Verdicts`
- `Workflow Recommendations`
- `Accessibility And Visual Notes`
- `Validation Status`
- `Final Verdict`

If no serious UX findings are discovered, say so plainly and state what was
actually inspected.

## Field Memory

- `references/reviewer-memory.md` stores durable, generalizable lessons for
  this skill.
- Update it only when skill maintenance is in scope and the lesson is likely to
  matter again across products.
- Keep additions terse and principle-level, not project-specific.

## Anti-Patterns

- Do not accept raw type ids, internal jargon, or implementation terms in
  user-facing controls when clearer labels exist.
- Do not accept invisible tabs, unlabeled icon-only controls, or color-only
  state changes.
- Do not let a nice layout compensate for unclear workflow meaning.
- Do not merge multiple personas into one "user view".
- Do not smooth away persona disagreement when it reveals real user risk.
- Do not report polish feedback before blocking clarity or trust failures.
- Do not approve "simple" flows that hide consequences or provenance.
- Do not downgrade to fewer subagents for convenience, speed, or token economy
  without labeling `#FALLBACK` and naming the blocked capability.
