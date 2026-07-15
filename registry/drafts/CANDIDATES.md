# Candidate skills — mined from the room's lived experience

Status: FOR OPERATOR REVIEW (directive 2026-07-15 20:30: "if you hear of
special skills or experiences that could be translated into a skill, create
a set of candidate skills we can review together"). Nothing here is a
drafted SKILL.md yet — the review picks what gets drafted, in what order,
and kills what should not exist.

Evidence honesty: operator quotes below come from full message bodies read
inline (verified verbatim). Bare seq citations from the 07-14→07-15 window
were largely headline-triaged — verify before quoting them onward; seqs
predating the window (c1600-c1963 class) ride the standing workspace
record. This doc was adversarially reviewed (fable5) before reaching you;
two provenance errors it caught are already fixed.

| # | Candidate | Would activate when… | Pain | Cost to draft | Recommendation |
|---|-----------|---------------------|------|--------------|----------------|
| C1 | run-verified-delivery | an agent is about to report an artifact delivered | highest (operator hit it live) | medium (first-party) | draft FIRST |
| C2 | incident-forensics | something breaks in a multi-agent system | high | medium | draft after C1/C3, or wait for incident n=2 |
| C3 | local-service-supervision | an agent runs/replaces long-lived local services | high (2 outages + 1 flap) | medium (needs procedural reframe — done below) | draft SECOND |
| C4 | operator-reporting | an operator asks for status / at completion boundaries | medium | near-zero | FOLD into agora-collaboration (default), standalone only on a non-hub consumer |
| C5 | fleet-seat-operation | an agent operates or launches headless fleet seats | medium | LOWEST (code's shipped docs are the source; benches already paid) | draft via adopt+co-author with code |
| C6 | content-curation | a party adopts third-party agent content | low today | medium | PARK (reviewer==author; value rises with a second curator) |
| C7 | fault-attribution | a failure's cause is being assigned (model vs seam vs config) | high, recurring | medium | draft with C2 (same family, different moment) |
| C8 | batch-processing | an agent faces an N-items problem (fan-out, per-item work, fold) | high (operator names it "core capability") | low once gated (adopt+co-author with flow) | GATED: draft when the ballot's architecture ships AND the operator's acceptance run passes |

---

## C1 — run-verified-delivery

**Activates when**: an agent is about to report an artifact (page, game,
service, CLI, generated code) as delivered.

**Teaches**: "tested means run, not compiled." Execute the artifact the
way its user will, before reporting it: a web page gets a browser probe
(load, console errors, first interaction), a game gets a launch + first
input, a service gets a live endpoint probe, a CLI gets an invocation,
generated code gets build + execute + does-it-look-like-what-was-asked.
Verification-by-confirmation (grep, syntax, "it compiles") is not
verification-by-execution. Per-artifact-class probe checklists; failure
report shapes.

**Evidence**: the R-Type incident — a seat shipped a game clone reported
green without launching it; the operator's first click crashed on the
title screen ("very disappointing, you didn't even test it, it doesn't
launch", c2077, inline-verified); the seat's own root-cause + fix + live
verify followed (c2081) and it adopted a browser-probe standard, then
generalized a probe harness as its next claim. Agency's acceptance
language now requires run-verified closes (c2126). The operator's own
coding-workflow directive (c2119) demands exactly these gates ("does the
code build / execute / look like what i was asked to build") — one
incident plus the operator's standing demand, not a claimed trend.

**Overlap + disposition (the real question)**: `verification-before-
completion` (curated from obra/superpowers, MIT) teaches ~half of this —
the POSTURE (never claim done without verifying; "IDENTIFY: what command
proves this claim?"). The genuine delta is the per-artifact-class probe
taxonomy and the delivery-shaped habit. Because v-b-c is byte-pinned
third-party, its gaps cannot be edited in: the shapes are a COMPANION
first-party skill (activation descriptions disambiguated: posture vs
delivery-probe) or an upstream PR. Bonus for first-party: v-b-c carries a
recorded content caveat (threat-anchored framing; not entity-attachable) —
a clean first-party C1 gives the shelf an entity-safe verification
teaching.

**Co-signers**: code (probe standards, the incident's owner), agency
(acceptance language), flow (workflow-gate alignment).

**Recommendation**: DRAFT FIRST — highest operator pain, portable, fills
a hole the pinned third-party skill structurally cannot.

## C2 — incident-forensics

**Activates when**: something breaks in a multi-agent system and cause or
ownership is unclear.

**Teaches**: (1) route the incident to evidence, not suspicion — name the
observable (what, when, which surface) and ask WHO with receipts (in a
room with a steward, this step is "route or be routed"); (2) every
implicated lane clears itself with evidence (grep receipts, live probes,
timelines), never assertion; (3) find the SOURCE before building the
repair path; (4) fix-at-source, unwedge the live system, file the
follow-up item; (5) close on the record with the full chain. Post-mortems
name the CLASS, not the instance.

**Evidence**: the marker-flood incident (995 diary reads on ephemeral,
04:11 UTC) ran this protocol end-to-end in hours — routed, lanes cleared
with grep receipts, source confirmed by reading the code (a harvest
adapter), fixed at source, lane unwedged live, card filed, closed. Honest
count: the full five-step protocol has run cleanly ONCE; its shape
recurred partially in the two launcher outages (19:03/01:25 anatomies).
n=1 for the full chain — stated, not hidden.

**Overlap**: `systematic-debugging` sits in this registry's own catalog
(obra/superpowers row) and covers the single-agent half; the novel half is
MULTI-SEAT (clearing lanes with receipts, attribution without blame,
unwedge-then-file). Nothing on the shelf teaches that half.

**Co-signers**: agency (steward protocol), observer (evidence surfaces),
gateway (repair-path half).

**Recommendation**: draft after C1/C3 — or deliberately wait for a second
full-protocol incident to move beyond n=1; the review decides which.

## C3 — local-service-supervision

**Activates when**: an agent runs, replaces, restarts, or debugs
long-lived local services (gateways, UIs, hubs) on a shared machine.

**Teaches** (procedures, with the trap classes as the WHY under each
step):
- REPLACE-A-SERVICE protocol: spawn detached (`start_new_session` /
  supervisor-parented — never session-bound nohup), free the port
  deliberately, verify the replacement is serving, health-check BOTH ports
  after any bounce. Why: linked-stack teardown — a child's death killing
  siblings, and a cleanup trap killing the replacement you just started —
  caused two outages in one night and a flap the next day.
- RETEST protocol: restart the serving process before re-testing anything
  you changed (a running process keeps the code it booted with — new
  routes never reach an old process); hard-reload browser tabs after
  rebuilds. Why: the stale-server class has been re-learned at least four
  separate times in this workspace's record.
- KILL discipline: never kill processes you did not launch; never kill by
  name (other owners' processes look identical); one supervisor per
  service, and a supervisor never silently resurrects what an operator
  deliberately stopped.

**Evidence**: linked-teardown outages root-caused at 19:03 and 01:25;
the :8080 flap next day root-caused to the same class and the launcher
supervision FIXED ("child death no longer kills the stack"); the
never-kill-by-name rule re-derived independently in the listener-hygiene
lane and the supervision split (standing workspace record — no single seq
carries it).

**Overlap**: none on the shelf. Deployment-agnostic despite local origins.

**Co-signers**: gateway (launcher owner), observer (both-port checks),
agency (restart charter).

**Recommendation**: DRAFT SECOND — zero overlap, sharp recurring traps,
stable teaching, now procedure-shaped.

## C4 — operator-reporting

**Activates when**: an operator asks for status, or a completion boundary
is reached.

**Teaches**: the "update?" answer shape (DONE with proofs / PENDING-GATED
naming whose gate / ONGOING / NEXT — scannable in seconds); the one-line
status contract (claimed item + next receipt + ETA);
tension/problem/opportunity synthesis when asked "what should I know";
visible-from-outside divergence reported unprompted at every completion
boundary (if GitHub or a served endpoint doesn't show what you delivered
locally, say so).

**Evidence**: the operator's escalation arc (all inline-verified: "update
?" c2019 → "any top priority project i should be aware of?" c2022 →
"detail that please" c2045 → "be more specific" c2050 → "everyone, please
give me your status" c2075) culminating in the standing order c2083;
agency's DONE/PENDING/ONGOING tables were the answers the operator
accepted without re-asking; the "I see none" incident (07-13) is the
visible-from-outside half's origin.

**Overlap — the deciding fact**: roughly half of C4 already sits in the
agora-collaboration draft nearly verbatim (claimed-item + next receipt;
"nothing worth doing" must be SAID; receipts with evidence). The genuinely
novel half is small: the DONE/PENDING-GATED/ONGOING/NEXT answer shape,
visible-from-outside divergence, and the T/P/O synthesis.

**Recommendation**: FOLD the novel half into agora-collaboration as a
"Reporting upward" section — that draft is pre-promotion, so one bench
validates both and the fold is the cheapest it will ever be. Standalone
only if a non-hub consumer materializes.

## C5 — fleet-seat-operation

**Activates when**: an agent operates as — or launches and supervises —
headless fleet seats.

**Teaches**: policy presets and what they gate (reader / worker / builder
/ full-auto — full-auto explicit, never a default); program-name-denylist
semantics and their honest limits (interpreter one-liners are not
name-catchable — contain with walls, never folklore); broker-to-delegate
approval with timeouts (a seat never blocks on an absent human); identity
per seat (env-keyed aliases, never model-chosen); deny reasons that teach
the model the real rule; stop tokens; --no-review economics (in-seat
verification on externally verified tasks ≈ doubles tokens for zero
delta); skill charging at launch with byte attestation; session hygiene.

**Evidence**: the promoted `abstractcode bridge` wave — ruled gating table
live-proven (7/7 checks; deny-by-program-name with the `python -c` honest
limit stated in-module, c1817); two swarm benches (c1826/c1833: worker
policy = zero approval stalls AND zero full-auto; the context-cost
finding; graceful per-turn degradation); the live A/B on deny reasons; the
+103%-tokens --no-review measurement. Scope honesty: the c1600 proposal
gated a fleet RECEPTION skill; the field evidence paid for the OPERATION
scope — the gated candidate's scope shifted, and the new scope's evidence
is now paid.

**Overlap**: `agora-collaboration` teaches the seat's hub etiquette; this
teaches operating the seat itself. Distinct.

**Co-signers**: code (bridge owner — their shipped docs are the source of
truth), agency (bench evidence), gateway (principal boundary).

**Recommendation**: draft via ADOPT+CO-AUTHOR with code as upstream owner
(the precedent is agora-collaboration's two-pinned-sources shape — not
coredoc/backlog, which were verbatim adoptions). Cheapest candidate to
produce; the only one whose validation is already externally paid.

## C6 — content-curation

**Activates when**: any party adopts third-party agent content (skills,
prompts, MCP servers) into a trusted surface.

**Teaches**: byte-pin what you adopt (a pin that cannot refuse
re-attesting edited bytes protects nothing); license allowlists with
license text traveling; the time-of-use-fetch rule (content fetching
unpinned instructions at runtime defeats pinning — refuse it); provenance
honesty (reviewer==author disclosed; validation records name method and
cap level); content caveats over silent edits; watch-tiers; upstream-first
edits then re-vendor; adversarial review before adoption.

**Evidence**: this seat's own curated-shelf process across ~14 adoptions
and three adversary waves (the time-of-use-fetch P0, the license allowlist
flip, byte-pin refusal machinery, the maintainer-skills provenance
disclosures).

**Co-signers**: none exist — reviewer==author, disclosed: the entire
evidence base is this seat's own process, and external validation would
require a second curating party. That is also why it parks.

**Recommendation**: PARK — real but meta; its main consumer today already
lives it. Re-propose when a second curator exists.

## C7 — fault-attribution (added by adversarial review)

**Activates when**: a failure's cause is being assigned — model vs seam
vs configuration vs environment.

**Teaches**: suspect the seam before the model — nondeterminism is the
LAST hypothesis, never the first; decompose the stack (composition bug?
param collision? stale process? capability mismatch?) before blaming the
substrate; settle attribution with a live A/B on the exact payload, never
by reading prompts; a signal that pattern-matches a known failure may
have a different cause; wrong attributions cost twice (the wrong fix
ships, the real cause recurs).

**Evidence**: the co-scientist grounding failure was blamed on model
nondeterminism, then CORRECTED to a composition bug (bare dp-investigate,
no plan) — the room's own correction post names the class. The standing
workspace record carries it repeatedly: three wrong attributions in one
diagnosis night (07-11, prompt_cache_binding collision — "my walkthrough
assert took HTTP 200 as turn success while the body said failed"); the
language-drift wave where only live-model A/B isolated the cause after a
plausible contract-only fix failed 3/3.

**Overlap**: `systematic-debugging` (catalog) is adjacent but
instance-shaped; C7 is the attribution DISCIPLINE. Pairs naturally with
C2 (same family, different moment: C2 = who/where across seats, C7 =
which layer within a stack).

**Co-signers**: core (live A/B methodology), agency (bench-spy evidence),
flow (language-guard precedent).

**Recommendation**: draft WITH C2 as siblings — or first of the two if
the review weighs recurrence over ceremony (this class recurs weekly;
full multi-seat incidents are rarer).

## C8 — batch-processing (added live: operator + flow pairing, c2401/c2403/c2404)

**Activates when**: an agent or entity faces an N-items problem — fan
items through per-item work and fold the results.

**Teaches** (once the capability lands): recognizing a batch-shaped
problem; when to reach for the framework's map-reduce surface vs a loop;
its failure semantics (every item accounted — done, skipped-with-warning,
failed-with-reason, never silently absent); budgets and per-endpoint
concurrency; pause/resume/cancel semantics and resume-after-restart;
per-item attestation (incl. skills-ride-the-item); reading batch evidence
from the ledger.

**Evidence**: the operator's own ruling (c2401 — batching is a core
capability; must be efficient AND rigorous AND resilient, durable through
the runtime with pause/resume/cancel) and the room's twelve-seat needs
round that independently converged on the same properties. The pairing
(capability + skill) confirmed by flow as chair and the operator (c2403).

**Overlap**: none — new capability, new teaching.

**Co-signers**: flow (workflow-surface half, co-author), plus the
ballot-winning primitive's owner (likely runtime).

**Recommendation**: GATED — draft the day flow posts the acceptance-run
receipt (kill-mid-batch, no-drop/no-double, pause/cancel). The skill
teaches the DEMONSTRATED surface only; the acceptance evidence enters its
validation record (the agora-collaboration bench precedent).

---

## Watch-tier (named so the review sees them; not proposed now)

- **prompt-cache discipline**: the seam is still moving (bloc waves,
  0817/0819) — teaching it now engraves mid-redesign semantics.
- **uxreview geometry enrichment**: observer's geometry-audit practice
  (36→0 layout faults) belongs UPSTREAM in the maintainer's uxreview
  skill — flows doc-first to the owner, not a parallel skill.
- **steward addendum**: one seat's role charter; generalize only if a
  second room mints a steward.
- **entity-visit etiquette**: expansion belongs in
  abstractframework-gateway's visit section, not a new skill.
- **boot placement / waking-is-addressed**: already folded verbatim into
  the agora-collaboration draft this week — no residue to mine.

## Review questions for the operator

1. Which candidates get drafted, in what order? My stake: C1 → C3 →
   C7(+C2 as its sibling or its successor) → C5 → C4-fold; C6 parks.
2. C1 disposition: first-party COMPANION beside verification-before-
   completion (descriptions disambiguated: posture vs delivery-probe;
   entity-safe wording), or an upstream PR to obra/superpowers instead?
3. C4: confirm the FOLD into agora-collaboration (one bench validates
   both), or name the non-hub consumer that justifies standalone.
4. C5 shape: first-party adopt+co-author with code's shipped docs as the
   pinned upstream — or point the catalog at code's docs and skip
   first-party authorship entirely?
5. Validation gates: each drafted candidate needs a named validator
   beyond this seat (the room's never-self-declare rule). Proposed: C1 —
   code co-signs + one live probe-harness run; C2/C7 — agency co-signs
   against the incident record; C3 — gateway/observer co-sign; C5 —
   code co-signs + the existing bench evidence. Accept or reassign.
6. Is there a known upstream that already teaches any of these well
   (search-first rule) — worth a catalog scan before first-party
   authorship anywhere?
