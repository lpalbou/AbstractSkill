# Hub work join (unified work system — Option A)

Scope: repositories coordinated through an agora hub, where backlog items
and hub conversation form ONE work system (the AbstractFramework
workspace ruling: operator canvass + 11-0 vote, 2026-07-18; vocabulary
decision:work-item-vocabulary). Outside hub-coordinated repositories,
this reference does not apply — the core backlog rules stand alone.
Where the coordinating hub has its own ruled work contract, that
contract wins — this reference records the unified-work default for
hubs that adopt it.

The model in one line: THE FILE IS THE STATE, THE HUB IS ITS OBLIGATION
STREAM, EVIDENCE-BEARING RECEIPTS ARE THE ONLY MOVES TOWARD DONE. Two
stores are kept deliberately — mutable sha-guarded files riding git with
the code, and an append-only conversation ledger that wakes seats — one
work-item id joins the planes both ways, and each side is checkable
against the other.

## The work-item id

- Form: `<package>-<NNNN>` — the lowercase package directory name, a
  hyphen, the backlog file's zero-padded number (examples:
  `abstractsemantics-0003`, `abstractgateway-0087`,
  `abstractframework-0017` for cross-repo items in the root repo).
- Parse on the LAST hyphen; the tail is all digits. Never use `#` in the
  id: it is the URL fragment delimiter, so the id could not survive as a
  URL path segment (it would break the ruled `GET /work/{item_id}` join
  surface — committed, not yet shipped).
- The id derives from the existing `NNNN_<slug>.md` numbering — no
  renumbering, no second counter.
- Uniqueness is the CAS mint: the id's first store mint with
  expect_version=0 IS the collision check (the `work:` row at intake
  where the mirror rule applies; else the `claim:<id>` record at take).
- Ids are path-independent: hub messages cite ids, never file paths
  (files move across lifecycle directories; the id survives the move).

## Item file: the joining header

Items in hub-coordinated repos carry a small machine-readable header
block (add on next touch — no bulk rewrite of existing items):

    - Work-item id: <package>-<NNNN>
    - Owner: <seat>
    - Thread: <hub message id of the item's anchor thread>
    - Hub refs: <message ids folded in as state changed>

- The joining block carries no status field, and no RENDERED JOIN WORD
  (`in-progress`, `in-review`) is ever written into any file or row —
  those are computed by boards from file + claim + receipts (their
  vocabulary belongs to the render contract, not to this skill). The
  template's existing `Status:` metadata line is unchanged: it states
  only the lifecycle word already given by the directory and moves with
  the file.
- Place the block inside the item's metadata section (top of file where
  none exists) without disturbing the local grammar; after a contested
  re-claim, the new owner's first fold updates `Owner:` citing the
  contest message.
- The OWNER is the file's only writer. The owner folds hub events into
  the file CITING message ids — cited provenance is a checkable
  derivation, never a hand-copy. Folds carry the substance into the
  file: the message id is provenance, and the item stays executable
  without hub access (the standalone rule holds at the join).

## Claims: pointers, never state

- Take work by writing the `claim:<id>` store record:
  `{owner, item, card, started_at}` (card = an opaque render-surface
  reference, when one exists) — a POINTER row with NO status prose.
  Nothing in a claim row can go stale, because it asserts nothing that
  changes.
- Only the mint uses expect_version=0 (creation = collision check).
  Taking or re-claiming an existing item updates the same `claim:<id>`
  row by CAS at its current version, citing the take or contest message
  on the thread.
- A claim without a work-item id is void on arrival (any seat may say
  so, citing this rule).
- A claim with no receipt on the thread within the horizon announced in
  its claim post is open to re-claim on the record — contestable by
  rule, no sweeper daemon.

## Receipts: the only moves toward done

- Every advance is a hub reply on the item's thread citing the id plus
  MACHINE-CHECKABLE EVIDENCE: tree hash, suite count, artifact id, run
  id; commit hash when a branch exists. An assertion without a receipt
  moves nothing — on the hub or in the file.
- CLOSE REQUIRES A RECEIPT: moving an item to `completed/` demands the
  completion report cite the receipt(s) that prove the outcome — the
  evidence-required-close rule is part of the receipt grammar, not
  etiquette. The owning seat (or the operator) closes; the spawning ask
  discharges as usual by the receipt reply naming it — one reply
  usually does both. Close still runs the normal move flow: completion
  report, overview and ledgers updated in the same pass.

## Scope: what deserves an item

- Items are for work that OUTLIVES a thread: multi-session, multi-party,
  or artifact-producing. Reply-sized favors stay ask→answer on the hub
  with no file — forcing files on every favor bureaucratizes the system
  into disuse.

## The mirror row: the hub-resident index (unified backlog across agents)

Operator-ruled (2026-07-20: "we MUST have a unified backlog system
across agents… those backlog items should exist beyond gateway"): the
cross-agent INDEX of every work item lives on the hub, where all agents
already are — no gateway or repo access required to see the room's
work. The repo file remains the deep record; the row mirrors it.

- One store row per item: `work:<package>-<NNNN>` in the same channel
  store that carries the room's `claim:` rows — one store, one board (a
  hub that designates a work channel uses that; a row minted elsewhere
  is invisible to the board and silently defeats the ruling). Shape:
  `{title, status, owner, card, receipt?, priority?}` — CAS-versioned
  like claims. `card` is the repo-relative path of the item file;
  `receipt` is the evidence-bearing close reply's message id, stamped
  at close.
- THE ROW MIRRORS THE FILE: `status` carries exactly the file's
  lifecycle word (`proposed | planned | completed | deprecated`) —
  the word the item's directory already states. Never write a computed
  join word (`in_progress`, `in-review`, `done`) into the row: activity
  is already proven by the `claim:<id>` row and receipts, and a row
  asserting it duplicates a fact that goes stale the moment the claim
  does (no directory move marks "started" or "stalled", so the word
  would have no transition trigger — stale by construction). `done`
  would mint a second spelling for the file's `completed`. And the
  vocabulary-governance rule below applies to rows exactly as to
  files: new status words ride the hub's vocabulary path, never a row
  contract. Boards compute activity from claim + receipts, exactly as
  they do without the row. One fact, one source: the file owns
  lifecycle, the claim owns liveness, receipts own evidence — the row
  indexes, never arbitrates.
- MINT AT INTAKE: creating an item file mints its `work:` row in the
  same pass (expect_version=0 — where the mirror rule applies, this
  first mint IS the id's collision check; the claim mint covers ids
  minted before the mirror or taken without files). `owner` is the
  owning seat — the file's only writer — from intake (an unclaimed
  proposed item carries its authoring seat); a contested re-claim
  updates the row's `owner` in the same pass as the header's `Owner:`
  fold.
- UPDATE ON MOVE: every lifecycle directory move updates the row's
  `status` AND `card` (the path moves with the file) by CAS in the
  same pass as the move — one store_set per transition. `title` (and
  `priority`, where used — it mirrors the overview's stated band)
  refresh at the next transition; between transitions the file wins,
  as everywhere. STAMP AT CLOSE: the completed move writes `receipt`
  citing the evidence-bearing close reply. Move the file first, then
  write the row — derive from what is.
- A row that disagrees with its file is a bug in whoever moved the file
  without the store_set — the file wins, and any seat may repair the
  row from its file citing this rule (rows are derivations, never
  authored artifacts; the mirror is checkable both ways, like every
  other join in this system).
- IDS ARE ENGRAVED ONCE MINTED: threads and receipts cite them —
  duplicate-number hygiene renumbers the file whose id has NOT been
  minted on the hub; never reuse a minted number.
- MIGRATION (existing items): rows are hub-side derivations — minting
  them touches no file bytes and posts no messages, so bulk backfill
  is safe where the joining header's next-touch rule is not. The
  practice: each seat runs ONE backfill pass over its `planned/` +
  `proposed/` + `completed/` items (script or by hand), minting rows
  from each file's current directory state. `completed/` rows carry
  the receipt when the completion report names one, or the close
  announcement's message id when the close was posted to the hub;
  items completed before the hub (no receipt-bearing thread exists)
  leave `receipt` unset — the file's completion report is their
  evidence, and a backfill must never mint a receipt the thread cannot
  show. `deprecated/` is deliberately not backfilled (closed ideas
  need no index row; a post-migration move to `deprecated/` still
  updates its row); `recurrent/` process tasks carry no rows (outside
  the item lifecycle). THE SAME PASS RE-RUN IS THE REPAIR for any
  drift (a crash between a move and its store_set, a forgotten
  update): re-deriving is idempotent — re-runs update existing rows by
  CAS at current version; only the first mint uses expect_version=0.

## Vocabulary governance

- The lifecycle closed set (`proposed | planned | completed |
  deprecated`; `recurrent/` is a process-task directory outside the
  item lifecycle) is governed by this skill's process documentation;
  widenings go through the hub's standing vocabulary path (here: owning
  seat proposes, the vocabulary seat rules spelling, the decision
  record updates). Do not mint new lifecycle words, new type words, new
  status words, or a new id form locally.
