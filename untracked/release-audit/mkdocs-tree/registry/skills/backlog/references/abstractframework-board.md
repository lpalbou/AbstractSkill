# AbstractFramework board grammar (deployment-specific)

Scope: work items in repositories served by the AbstractFramework
gateway's backlog surface and rendered by the AbstractContinuum board.
This is the DISCOVERY-FIRST rule's concrete instance for that
deployment — where this file and the skill's generic templates differ,
THIS file wins there. Sources (both co-signed on the hub record):
`abstractcontinuum/docs/conventions.md` (the board owner's canonical
reference, c1701) and the gateway seat's parser co-sign (c3514,
reposting the empty c3512; correction adopted by continuum c3516). The
deployment's parser is truth; when it changes, this reference re-syncs
against the shipped code, never against memory.

## Title line (H1)

```markdown
# 0123-package: [TYPE] Short imperative title
```

`0123` = the stable item id; `package` = the owning package
(`framework` for cross-cutting work); `[TYPE]` = the ruled enum,
UPPERCASE in the H1.

## Metadata: blockquote lines, never a section

The gateway parses BLOCKQUOTE lines in the file header. A
`## Metadata` section with `- Created:` bullets is NOT parsed — an
item written that way renders metadata-blind on the board (this is the
competing-grammar failure the discovery-first rule exists to prevent).

```markdown
> Created: 2026-07-13 21:00:00 +0200
> Type: bug
> Priority: P1
> Labels: ui, wave-doctoring, seat-memory
```

- `Priority`: `P0` (drop everything) … `P3` (someday). Absent =
  unranked (sorts last within its column).
- `Labels`: comma-separated free strings; sprints are labels
  (`sprint-N`).
- Parsed: Type, Priority, Labels — Priority and Labels only BEFORE the
  first `## ` section and within the first 60 lines. `Created` is
  template convention, not parsed metadata.

## Type vocabulary (ruled enum)

`bug | feature | improvement | task` — semantics'
`decision:workitem-type-enum`. Never invent types in items; propose
enum changes to the semantics seat. The parser accepts the ruled four
(gateway repair, c3556 — earlier builds coerced `improvement` to
`task`); unknown words outside the set still normalize at list time,
and the DoR gate refuses out-of-set values naming them as written.

## Definition of Ready: an execution GATE, not advice

Execute is gated BY DEFAULT (gateway c3556 — the wall both co-signed
sources teach is now the code): every execute request evaluates the
gate and refuses `409 definition_of_ready_failed` (with per-check
evidence) unless all checks pass; the ONLY bypasses are explicit and
RECORDED as `dor_overridden` — `override=true` (operator judgment) or
`dor=skip` (a bypass is a choice, never a silent default). The FOUR
server-side checks (quoted from the shipped gate,
`maintenance/backlog_dor.py`):

1. `type` — the item's type is in the ruled enum.
2. `summary` — a Summary section holds at least one non-placeholder
   line.
3. `acceptance` — at least one NON-PLACEHOLDER checkbox bullet under
   an "Acceptance Criteria" heading (the template's
   `Criterion 1 (clear, testable)` line does not count).
4. `tests` — at least one backticked command under a "Testing" heading
   (`` `...` `` and `` `n/a` `` do not count).

Section semantics are load-bearing: a section is the lines after a
matching heading of ANY depth (H1..H6) until the next heading of any
depth — `### Acceptance Criteria` counts, not only `##`.

Priority is NOT a server-side gate check (the gateway co-sign's
correction to an earlier revision of the conventions doc, which listed
"Priority set" as a fifth check — since corrected in place, c3516):
set it for ranking, but the 409 never fires on its absence.

## Definition of Done

Acceptance checkboxes ticked + QA review before promote. "Done" means
validated — the promote flow is the verification surface, and an
unreviewed promote carries its unconfirmed count on the button label.

## Lifecycle directories (board homes)

`proposed/` (Triage) · `planned/` (Ready — DoR applies) · `completed/`
(Done) · `deprecated/` (Backlog page only, restorable) · `trash/`
(Backlog page only, restorable) · `recurrent/` (Backlog page only — no
board home, ruled). Execution states (`queued`/`running`/
`awaiting_qa`/terminal) ride exec requests, never directories;
promotion archives the planned file to `completed/`.

## Supervision vocabulary (room coordination)

- `decision-gate` label = an OPERATOR decision — renders as an amber
  operator-gate card: never draggable, never promotable, never
  executable; resolved only by the operator's ruling.
- `wave-<slug>` = a room wave (directive fanned to N seats);
  `seat-<owner>` = the owning seat(s) — both are Supervision filters.
- Per-seat receipts inside a wave item are acceptance checkboxes
  carrying the hub message id:

```markdown
- [ ] gateway: writer wave shipped (c1608)
- [x] continuum: supervision view live (c1636)
```

## Docs freshness (the coredoc half, for context)

The board's conformance read flags a package red when
`llms.txt`/`llms-full.txt` is older than the newest `docs/*.md` —
regenerate the llms files in the same change that edits docs.
