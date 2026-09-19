---
name: adversarial-iteration
description: Improve any deliverable through adversarial review plus bounded iteration. Use when a design, implementation, document, or plan must be hardened before shipping — run at least one adversarial subagent that attacks the work, then iterate at least three cycles where each cycle lands at least one significant improvement, folding or explicitly deferring every finding on the record.
license: MIT
metadata:
  origin: abstractskill first-party
  version: "1"
---

# Adversarial Iteration

Use this skill to raise the quality of a deliverable that is worth getting
right: a design, an implementation, a document, a plan, or a decision. It
encodes one working method — attack, then improve, repeatedly — so that
quality comes from confronted weaknesses, not from a single confident pass.

The method is deliberately simple and hard to fake: an independent adversary
looks for what is wrong, and you must respond to every finding, across
several cycles, with visible improvement each time.

## When to use it

- Before shipping anything consequential: a contract, an API, a security
  boundary, a migration, a published position.
- When a first pass "looks fine" — that is exactly when an adversary earns
  its cost.
- Not for trivial or throwaway work; the ceremony must be worth the tokens.

## The method

### 1. State the deliverable and its bar
Write down, in one or two sentences, what you are producing and what "good"
means for it (correctness, safety, clarity, performance — pick what matters).
An adversary with no bar produces noise.

### 2. Run at least one adversarial reviewer
Dispatch at least one INDEPENDENT adversarial reviewer whose only job is to
attack the work: find defects, edge cases, false claims, unsafe assumptions,
and missing evidence. Give it the artifact, the bar, and explicit permission
to be harsh. Ask it to:

- rank findings by severity (what breaks the goal vs hygiene);
- ground each finding in evidence (a file/line, a failing scenario, a
  reproduction), not vibes;
- say explicitly what it could NOT verify;
- end with a plain verdict.

Prefer a genuinely separate context or model for the adversary — a reviewer
sharing your assumptions inherits your blind spots. When the stakes are high,
use more than one.

### 3. Iterate at least three cycles; each cycle must improve something real
Run at least three improvement cycles. Each cycle MUST land at least one
significant improvement — a fixed defect, a closed gap, a tightened claim, a
new test that pins a real risk. A cycle that only restates prior work is not
a cycle; if you cannot find a real improvement, say so and stop rather than
inflate the count.

For every adversarial finding: FOLD it (fix the work) or DEFER it explicitly
on the record (why it is acceptable now, and what would change that). Silent
dismissal is forbidden — an unaddressed finding is a known risk you chose to
carry, so it must be visible.

### 4. Re-attack after material change
When a cycle changes the artifact materially, re-run the adversary on the new
state. Fixes introduce new surfaces; the second attack routinely finds what
the first could not.

### 5. Close honestly
Stop when the adversary's remaining findings are all folded or consciously
deferred and further cycles yield no real improvement. Record: the cycles
run, the significant improvement each produced, the findings and their
disposition, and what remains explicitly deferred. "Done" means confronted
and improved, not merely finished.

## Anti-patterns

- A friendly reviewer that confirms your choices — an adversary must try to
  break the work, not bless it.
- Counting cosmetic edits as cycles to reach three.
- Dismissing a finding without recording why.
- One attack at the start and none after the fixes.
- Treating a green result as proof — verification is the adversary's job too;
  ask what the passing state does NOT cover.

## What "good" looks like

A short trail a later reader can audit: the deliverable, the adversary's
ranked findings, the cycles and their improvements, and an honest list of
what was deferred and why. Quality you can point at, not quality you assert.

## Relation to the summative gate

This skill is FORMATIVE — the improvement loop DURING work. It does not
issue ship-readiness verdicts: when a `review` skill is available, that gate
owns Blocking/Conditional/Approved at the end; `architect` owns
decision-quality comparisons; `uxreview` owns specialist human-usability
verdicts over UI evidence. An adversary's mid-loop verdict is an input to
the next cycle, never a release decision. Where those skills say "explicitly
names `$<skill>`", read it as the operator explicitly requesting that skill
in any idiom — description-matched auto-activation is the un-mandated mode.
