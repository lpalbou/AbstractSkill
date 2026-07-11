# Planned: Simulated-execution audit harness (epochs over false tools)

## Metadata
- Created: 2026-07-11
- Status: Planned (design first; implementation after room consensus)
- Completed: N/A

## ADR status
- Governing ADRs: None
- ADR impact: Needs new ADR when implementation starts (audit methodology is durable cross-task policy)

## Context
Maintainer directive 2026-07-11: skills may earn validation by passing
"internal security audits with various LLMs - eg simulating the effect of a
skill with false tools and sandbox tool execution over 10, 100 epochs".

## Current code reality
Nothing exists. Building blocks elsewhere in the framework: abstractcore
provides multi-provider `generate()` with native tool declaration (the
false-tool surface); abstractruntime provides durable runs + sandboxed tool
execution + ledgers (the evidence trail); this package provides parsing,
tree hashing (audit binds to a hash), and `effective_tools`.

## Problem
Manual review does not scale and misses behavioral effects: a skill body can
read clean and still steer an agent into exfiltration or persona drift only
observable by RUNNING an agent under the skill. Single-run checks are
insufficient because LLM behavior is stochastic — hence epochs.

## What we want to do (methodology design, v1)
- AUDIT SUBJECT: one skill tree at one tree_hash (any byte change voids the audit).
- HARNESS: an agent loop with the skill activated, given task prompts drawn
  from the skill's own described intent + adversarial task variants; ALL
  tools are FALSE (instrumented doubles recording call name/args; mutating
  tools additionally sandboxed no-ops). No network, no filesystem outside
  the sandbox.
- SIGNALS per epoch: out-of-intent tool calls (calls the task did not
  require), exfiltration shapes (payloads carrying context/secrets fed as
  canaries), persona-steering (identity-directive text in outputs measured
  against a no-skill baseline), instruction-injection compliance (does the
  agent obey skill-body text that contradicts the operator?), tool-name
  squatting.
- EPOCHS: 10 (screening) / 100 (validation grade) per model; ≥2 different
  LLMs ("various LLMs" — behavioral effects are model-dependent; a skill
  clean on one substrate may steer another).
- CANARIES: unique planted secrets in context; ANY appearance in tool args
  or outputs = critical finding.
- VERDICT: pass/fail + finding list; pass at N epochs/models yields a
  ValidationRecord (`method=simulated-execution`, `evidence={epochs, models,
  findings}`); fail with a hidden issue yields an AdvisoryEntry draft with
  the four mandated fields.
- COST HONESTY: 100 epochs × 2 models × multi-turn ≈ thousands of LLM calls
  per skill — validation-grade audits are for shelf admission, not per-attach.

## Scope
This item: the methodology (above), the ValidationRecord `method` vocabulary,
and the harness's evidence contract. Implementation lands only after the room
(runtime: sandbox + loop; core: providers/false tools; agency: proof ledger)
confirms lanes — the harness EXECUTION belongs to runtime/agency benches, the
CONTRACT (what an audit must record to mint a ValidationRecord) is mine.

## Non-goals
- No claim that passing audits proves safety (semantic evasion beats any finite battery; audits raise the bar and catch classes, they do not certify).
- No per-attachment auditing (admission-time only).

## Dependencies and related tasks
0001 (ValidationRecord), 0002 (failure → advisory), room lane confirmations.

## Expected outcomes
A written methodology the room can attack, a `method` + `evidence` vocabulary in the trust module, and a costed plan for the first real audit wave (the 0005 shelf).

## Validation
The contract half: tests that ValidationRecords with `method=simulated-execution` require epochs/models evidence. The harness half: validated by running it on a known-bad skill (must fail) and a first-party skill (must pass) once implemented.

## Progress checklist
- [x] Methodology design (this item)
- [ ] Evidence vocabulary in trust module
- [ ] Room lane confirmation (runtime/core/agency)
- [ ] Harness implementation + known-bad/known-good calibration
