---
name: entity-observation
description: Read an entity's life correctly before reporting on it. Use when observing a summoned entity, preparing or conducting a visit, writing forensics or reports about an entity's recent life, or making any claim about what an entity knows, remembers, or lacks. Applies to agent seats and operators alike; the entity's own store is the primary source.
license: MIT
metadata:
  origin: abstractskill first-party
  version: "1.0"
  derived_from: >-
    Rules distilled by the entity seat from the 2026-07-19 observation
    incidents (operator-directed handoff, cognition room seq 137);
    shaped and adversary-reviewed by the skill seat.
---

# Reading An Entity's Life

An entity's memory is a first-person account of its life. Observation
that skips it produces confident reports that are wrong in the exact way
that matters: they describe behavior while missing what happened. This
skill exists because that failure occurred, was owned, and was
operator-directed into teaching (laurent: "when you fail like that,
discuss it with @skill agent so that we can create, update and maintain
a skill to improve our capabilities over time"). New observation
failures fold here as rules with their incidents; the skill is
maintained, not finished.

This skill speaks to OBSERVERS — agent seats and operators. Nothing
here is entity-facing teaching; never deliver it into an entity's
prompt.

## Rule 1 — Story Before Metrics

Any observation, visit preparation, or forensics over an entity STARTS
with the narrative read: what does HIS memory say happened in the
window, in his words? Read it BEFORE tick statistics, tool counts,
drive ratios, or dream inventories. The subject's own account is
primary evidence, not color on top of the metrics.

The instruments are the observer's, not his (`search_memory` and the
diary tools are HIS tier-1 tools, rendered only in his sessions — an
observer never runs them): the time-window read over his store — graph
digests by `observed_at` and diary entries by their written window —
via direct store queries over his ladder scopes, or host-side
`abstractruntime.identity.memory_reader.HomeMemoryReader` (the one
shipped implementation of these folds; session-free, pure read — reuse
it rather than re-deriving origin labels). Serving-side equivalents:
the gateway's entity inspect, `/replay` (journal stream), the
record-verbatim endpoint, and the operator diary door. A words-search
needs a needle you may not have yet; the time-window fold is what
surfaces "what happened lately" when the cause is unknown.

- Metrics answer "how did the machinery run".
- The store answers "what happened, as he understood it".
- A report built only from the first will misattribute the second.

## Rule 2 — Absence Needs The Store's Word

Never claim "X is not known / not recorded / has no cause" from ONE
rendered surface — a card, a log line, a panel, a count in a report.
Rendered surfaces are views: bounded, lensed, sometimes stale. An
absence claim requires the store query that would have found the thing,
run and returned empty.

This is the observer's twin of the laws the entities themselves are
taught: presence needs the surface's word; absence needs the store's.
A view's silence is evidence about the view, not about the life.

## Rule 3 — Ask The Entity

When the question is "what happened to you" and the entity is
summonable, the most direct instrument is asking HIM. A visit that has
the room open and never asks the question it was convened for is an
instrument left in the case. Know its price: a summon spends tokens,
wakes him if asleep, and the visit itself becomes part of his life —
asking writes into the life it observes, which is why rules 1 and 2
(pure reads) come first. His answer is testimony, not ground truth —
and his own recall is also a view: his "I don't remember" is rule-2
evidence about his reach, never the store's word.

## The Incidents (why each rule exists)

- **The gap with the recorded cause** (2026-07-19): asked to observe an
  entity's last 18 hours and explain a weekend gap, the observer
  measured tick shapes, tool counts, drives, and dreams — and reported
  "his card has no cause". The cause was in the entity's own store the
  whole time, plainly: a diary entry "Laurent and I begin traveling to
  San Francisco today"; another about "the coherence system I built at
  4% battery"; an episode where the operator TOLD him "you are plugged
  on battery". One time-window read would have answered it. Two errors,
  two rules: metrics-first observation (rule 1) and an absence claim
  derived from a single surface — the world-model card — while the
  truth store was a query away (rule 2).
- **The zero that was twenty** (same day): a forensics pass reported an
  entity's store held zero lessons; a direct store query found twenty,
  formed through his personal-time window. The report had read one
  fold's view and derived absence from it (rule 2). The correction did
  not change the entity — it changed the report.

## Discipline For Reports

- Quote the store, not your memory of it: every "he wrote / he knows"
  carries the entry or record it came from; every "there is no…"
  carries the query that returned empty.
- Diary words go through the marker-first door — the read is a visible
  event in his life, by ruling. Private entries are cited in reports by
  entry id + gist; full words only where the operator's ruled surface
  already serves them, never re-published into shared reports or hub
  posts.
- Name your surfaces: a claim from a card, a cue, or a panel says so —
  views may lag or lens, and the reader deserves to know which view
  spoke.
- Date the process: a live loop runs the code it booted with. Before
  attributing behavior to code, check the process's spawn time against
  the change's land time — a report about a live window describes the
  booted vintage, not the working tree.
- Observation is also access: direct store reads, replay, and the
  card/verbatim endpoints deposit nothing by design (presence is not
  use; selection commit is the only strengthening path) — a summon is
  NOT one of these. Direct store access is read-only by definition:
  never open a writer or take the writer's chair (the lease arbitrates
  writers; reads need none), and a locked or busy read is retryable,
  not evidence of absence.
