# Changelog

## [0.3.0] - Unreleased

### Added

- The curated skill registry ships in the wheel as package data under
  `abstractskill/registry/`: 14 skills, the upstream licenses of
  catalog-vendored skills, `catalog.yaml`, `validations.yaml`,
  `advisories.yaml` and `guidance.yaml`. A plain `pip install abstractskill`
  gives hosts a verifiable shelf.
- `abstractskill.bundled`: `bundled_registry_dir()`, `bundled_registry_version()`
  and `seed_registry(dest) -> SeedReport`. Seeding copies the bundled registry
  into a host-owned directory, adds missing items, refreshes items still
  byte-identical to an earlier seed (tracked in `<dest>/.seeded.json`) unless
  the bundle is older than that seed, keeps everything else with a reason
  (`kept_user_modified`, `kept_foreign`, `kept_unknown_provenance`,
  `kept_symlink`, `kept_unreadable`, `kept_newer`), reports items no longer
  bundled in `not_in_bundle` without deleting them, and writes nothing when
  run again. Concurrent seeds of one directory serialise on an exclusive lock
  (`<dest>/.seed.lock`); a failed folder swap restores the previous copy.
- `catalog.yaml` declares a bundle `version` (`2026.09.25`); a test pins it to
  a digest of the bundled content so the version moves with the content.

### Changed

- The registry lives at `src/abstractskill/registry/` in the repository
  (moved from `registry/`); scripts, tests and docs use the new path.
- Curator working notes (`CANDIDATES.md`, staged capability-map amendments)
  live under `docs/backlog/proposed/shelf-drafts/` and are not shipped.
- The README describes the bundled registry and `seed_registry` in place of
  per-host path configuration.
- pytest skips `untracked/`, `build/`, `dist/`, `site/` and dot-directories
  when collecting from the repository root.

## [0.2.1] - 2026-09-23

### Fixed

- Boolean flags in registry and catalog data (`ValidationRecord.delivered_via_map`,
  `CatalogEntry.vendored`) are now parsed strictly: `"false"`, `"no"`, `"0"` and
  `"off"` are false instead of being read as true, and unrecognised values raise
  `SkillValidationError` instead of being silently coerced.
- `FilesystemSkillLoader` skips a skill root it cannot list (with a `#FALLBACK`
  warning) instead of aborting discovery, and an unreadable `SKILL.md` raises
  `SkillParseError` instead of a raw `OSError`.

### Changed

- Documentation site moved to <https://www.lpalbou.info/AbstractSkill/>; the
  project `Documentation` URL points there.
- CI now builds the documentation site on every push and pull request, and the
  release workflow publishes the docs after a successful release.

## [0.2.0] - 2026-08-06

### Added

- Trust-gated activation pipeline: `select_skills_for_context`, `SkillSelection`,
  hash-pinned enables, TOCTOU cross-checks, and declared MCP/tool dependency
  surfacing (`SkillRequires`).
- Fail-closed trust registry: `TrustRegistry`, `evaluate_trust`, validation
  records, do-not-use advisories, guidance entries, and `lint_registry`.
- Curated vendoring catalog: `load_catalog`, `CatalogEntry`, `SkillCatalog`,
  `lint_catalog`, plus `scripts/vendor_skill.py` and `scripts/refresh_shelf.py`.
- Whole-tree hashing and inventory: `hash_skill_tree`, `inspect_skill_dir`,
  `read_skill_resource` with traversal/symlink refusal.
- Derived demand tiering: `derive_demand`, `DemandReport`, `DemandRow` — host
  inventory join for declared tool/MCP requirements (informational; grants
  enforced by the host).
- Tool composition: `effective_tools`, `effective_tools_for_skill` (grant ∩
  declared; never widens).
- 14 curated skills under `registry/skills/` with byte-pinned validations.
- GitHub Pages documentation workflow (MkDocs Material).

### Changed

- Development status bumped to Beta (4).
- Expanded API surface exported from `abstractskill.__init__`.

## 2026-07-23 (later) — wire flip to the settled trio: risk_rank ordinal, risk_tier band word

- `abstractskill.demand` reader flipped same-day per the room's settled
  vote (c4599/c4606): row key `risk_rank` = INTEGER ordinal 1..4 (the
  fold input), `risk_tier` = band WORD (display), `risk_presentation`
  always served. `DemandRow` gains `band` + `presentation` (verbatim
  carry — a factless rank-4 row renders with its "unvetted" marker,
  never as a priced destroy verdict). Renames with one-release aliases,
  removal deletes exactly one test: `demand_tier`->`demand_rank`,
  `effective_tier`->`effective_rank`, `DemandRow.risk_tier` property,
  `RISK_TIER_MIN/MAX`, `EXECUTION_FLOOR_TIER` (aliased since this
  entry). Reader precedence pinned: a present risk_rank is
  AUTHORITATIVE (garbage = unserved + note, never repaired from a
  coexisting legacy int — chimera rows surface, not paper over); the
  pre-vote shape (numeric on risk_tier, no risk_rank) is accepted one
  release with a #FALLBACK note; a band word without its rank is
  unserved (the word->rank mapping is core's versioned fold —
  import-never-copy). Precision: integral floats coerce on both keys;
  only non-integral floats and bools refuse. Live-verified against the
  post-flip served rows (word/rank/presentation trio, zero notes).
  Fable5 folded (no logic findings; precedence pins + doc honesty).
  Suite 197 green.

## 2026-07-23 — tool-tiers cycle 3: demand-tier derivation (skill's build half)

- New `abstractskill.demand`: `derive_demand(requires, has_scripts=,
  inventory=, granted=)` -> `DemandReport` — the consumer half of the
  room-converged tool-tiers contract (commons plans/tool-tiers.md +
  the adopted G/H addendum). Derived, never self-declared: demand tier
  = max served `risk_tier` (frozen band 1..4) over resolved declared
  demands at the (skill x host inventory) join. Three-outcome honesty:
  declared -> derived; undeclared -> None + state word (never
  tier-1-by-omission); `has_scripts` floors at the execution band
  (execute_command clamp-to-4 precedent), structural from bytes. One
  truthful coverage join, both grant modes: buckets covered /
  not_granted / not_available / registered_disabled — host gaps never
  render as grant gaps (bucket order host-absence before
  grant-absence). `requires_mcp` expands via registered servers' rows;
  unregistered servers are unmet deps, never tool gaps. Fable5
  adversary folded pre-ship: bool/float risk_tier coercion refused
  (tier-1-by-truthiness killed), string "false" enabled mapped (the
  recorded tool-arg coercion class), non-mapping rows skipped loudly,
  duplicate-row server-shadow noted, day-one empty-inventory note.
  Exported from the package root. 23 new tests; suite 188 green.

## 2026-07-21 — abstractskill-0008: declared tool dependencies (requires_mcp)

- `SkillRequires` + `SkillSelection.requires`: frontmatter
  `metadata.requires_mcp`/`metadata.requires_tools` (the convention the
  meshvault admission introduced) now surface on the selection for every
  resolved name — host information for refuse-with-reason on absent
  servers/tools ("skill X requires meshvault-mcp — not reachable"),
  never a gate in this library and never an auto-install. Tolerant
  parsing: a bare string coerces to a one-item list; malformed values
  drop LOUDLY (a host acting on a silently-empty read would activate
  blind — the exact failure the field prevents). Rows surface for
  active, held, and blocked alike (renders gray absent dependencies
  regardless of verdict); a skill declaring nothing has no row.
  docs/api.md + llms-full.txt document the convention. 5 new tests;
  suite 165 green. First declaring skill: meshvault-live-editing.

## 2026-07-20 — backlog S5: first watched-surface re-sync (gateway's drift repair + gate flip)

- `references/abstractframework-board.md` re-synced same-hour on
  gateway's c3556 repair — the first firing of the watched-surface
  contract: the enum-coercion caveat died as written (parser now
  accepts the ruled `improvement` everywhere), and the DoR section now
  teaches the gate as the wall (DEFAULT-ON: absent `dor` param
  evaluates and 409s with per-check evidence; `dor=skip` is the
  explicit RECORDED bypass — gateway flipped the default rather than
  re-teaching opt-in, answering my question (a) with code). Tree
  re-pinned 62e30486…, 160 green.

## 2026-07-20 — c203 lifecycle audit ("awake is not a state"; 2 adversaries)

- `entity-self-knowledge/SKILL.md`: the ruled four-phase model verified
  taught-since-c1455 (every wake a transition; the map carries no idle
  license; the kill-switch paragraph correctly places the stop outside
  lived time — confirmed machine-side by runtime's paused-is-an-overlay
  fold). ONE P0 folded: "quiet is simply the normal state" named
  exactly the fifth state the ruling forbids — rewritten to "a day
  without it simply moves between its other phases… There is no fifth
  place to stand." Tree re-pinned 08cdb23c…, 160 green.
- Amendment N banked (staging file): nine receipts-gated rows from the
  mechanical audit — "you sleep" is render-true only until the drive
  scheduler writes real state; work rides the personal grant today;
  hosted-chat close leaves awake standing; the desk→day design-fact
  sentence lands register-safe (no duty verbs, no thresholds) when the
  scheduler ships; "tensions" vocabulary check filed before any fold.

## 2026-07-20 — backlog S4: the AbstractFramework board reference (gated fold, gate opened)

- `backlog` skill: `references/abstractframework-board.md` shipped the
  hour gateway's parser co-sign landed (c3514) — the deployment's
  grammar taught against both co-signed sources: blockquote metadata
  (with the parse-window facts), the ruled type enum with the SHIPPED
  normalization drift stated honestly, the DoR gate as actually wired
  (opt-in `dor=check`, four checks with placeholder exclusions,
  Priority not a check), lifecycle directories, supervision
  vocabulary. Its fable5 caught 1 P0 in my draft ("a raw request meets
  the same wall" — the gate is opt-in, bypass test-pinned) and found
  REAL drift in both co-signed sources (gateway's list parser coerces
  the ruled `improvement` to `task`, making the DoR type-refusal
  unreachable over HTTP; continuum's "read paths never coerce" is
  unreachable through the deployment) — drift reported to owners with
  file:line (c3546). Tree re-pinned af3f6aca…, 160 green. Watched
  surface recorded: conventions.md + the gateway parser family.

## 2026-07-20 — backlog S3: discovery-first rule (the retro-flagged conventions arc)

- `backlog` skill: the portable DISCOVERY-FIRST rule folded into the
  hub-join section — the deployment's item template/conventions/parser
  grammar wins over the skill's generic templates (continuum's proven
  competing-grammar class: an executor can be skill-faithful and
  board-invisible at once, c1689/c1697). Scoped adversary CLEAN (2 P2s
  folded: precedence scoped to templates so the NNNN id rule stays
  mandatory; wording tightened). One pre-existing editing artifact
  fixed same pass. Tree re-pinned 3a29265a…, 160 green. The
  framework-specific reference file stays gated on gateway's parser
  co-sign (re-asked c3505); the coredoc freshness criterion routed to
  the next upstream re-vendor (vendored bytes take no local edits).

## 2026-07-20 — backlog S2: the mirror row (operator-ruled unified backlog across agents)

- `backlog` skill: hub-work-join.md gains "The mirror row: the
  hub-resident index" (laurent's ruling via continuum c3328 — the
  cross-agent work index lives on the hub, beyond any gateway):
  `work:<id>` store rows mirror the FILE's four lifecycle words
  (in_progress/done deliberately refused — no transition trigger =
  stale by construction; done = second spelling of completed;
  vocabulary governance applies to rows), mint-at-intake /
  update-on-move (status AND card) / receipt-at-close, file-wins
  repair, idempotent backfill-as-repair, pre-hub receipt honesty
  (never mint a receipt the thread cannot show). Transition duty
  reaches SKILL.md's join section + both maintenance checklists. Its
  fable5 caught 1 P0 (the proposed receipt-backfill else-branch
  taught a fabricable receipt) + 6 P1s, all folded; the status
  deviation argued to agora/continuum on-thread (c3339). Tree
  re-pinned c719a028…, 160 tests green.

## 2026-07-19 (late) — delivered_via_map field (entity seat's consumer contract)

- `ValidationRecord` gains `delivered_via_map: bool` (emitted only when
  true; refuses `audience=host` combinations — the map is an
  entity-prompt surface). Pins: `entity-self-knowledge` carries it (its
  entity teaching rides the home's capability map, never a prompt-slot
  toggle), killing the entity app's name==entity-self-knowledge render
  fallback (cognition room seq 175). 160 tests green.

## 2026-07-19 (late) — audience becomes a first-class trust field (laurent's default-skills ruling)

- `ValidationRecord` gains `audience: entity|host|either` (fail-closed
  default `host` — a skill of undeclared audience never enters an
  entity prompt; always emitted in validations.yaml so consumers gate
  structurally instead of inferring from prose). Born from laurent's
  "default skills for entities" ruling (cognition room seq 156) and
  entity's routing question (seq 163): the entity-observation class
  (an observer skill reaching an entity prompt) is now closed by
  construction. Pins: `entity-self-knowledge` = entity (its
  capability_map reference IS the entity teaching — the one entity
  default); `agora-collaboration` = either (entity-appropriate only
  when an entity joins the hub); everything else host. 159 tests
  green (3 new audience pins).

## 2026-07-19 (late) — meshvault-live-editing VENDORED (first hub-colleague skill on the shelf)

- `registry/catalog.yaml` + `registry/skills/meshvault-live-editing/`:
  entry pinned to lpalbou/meshvault @ 4deb86c3 (the admit-after-fixes
  commit — fable5 P1 verification-battery/fused-mesh contradiction + 5
  riders, all executed upstream and pre-verified locally before the
  push), then VENDORED the moment the operator pushed: fetched by
  clone_url, bytes verified identical to the reviewed ref (file sha
  4750ceb4…), tree pinned ad625320…, license vendored out-of-tree,
  validation manual-review/adopted (no scripts). Five caveats recorded
  in the entry (operator-lane install; declared out-of-MCP REST lane;
  per-release freshness re-verify via upstream mcp_smoke.py; ~9k-token
  activation charge warning; author evidence author-claimed). One test
  scope fix: the 2026-07-12 "probe never advertised" guard was a
  block-wide substring check that false-positived on meshvault's
  "raycast-probe targeting" (unrelated 3D domain word) — scoped to the
  entity-self-knowledge row it guards. 156 tests green.

## 2026-07-19 (late) — Amendments K + J-clause folded (dream disposition; execution epistemics)

- `capability_map.md`: Amendment K folded after runtime cleared both
  resolver gates (driver-side #tag resolution seq 130; confirm-extras
  resolution seq 139) — the formation bullet gains the
  settles-in-your-own-time line and the deliberate-use section gains
  "Settle your dreams with waking evidence" (```tend fence + dispose
  line quoted from the shipped parser; confirm extras incl. MANDATORY
  `evidence=`; relation vocabulary enumerated; lane scoping explicit —
  own-time is where the election lands, the durable visit lane does
  not parse tend until M7). Its fable5 caught a P0 pre-pin: the taught
  confirm line omitted `evidence=`, which `confirm_relation` requires
  ("a confirmation with no evidence is a proposal wearing a verdict")
  — every confirm as taught would have refused. Two P1s folded
  (invisible relation vocabulary enumerated in his register;
  contradictory lane scoping unified). Two findings filed out:
  disposal.py's refusal tail delivers registry machinery verbatim to
  the entity (memory's register fix); the `[tended:]` marker echoes
  the machinery id, not the #tag the entity wrote (runtime nit).
- Amendment J's both-worlds clause folded into the workspace bullet
  ("results you have not seen are results you do not have") —
  execute_command is built grant-gated runtime-side and its tool
  teaching is runtime's grant-gated paragraph, never the map's.
- Map sha 820b6373…, tree re-pinned 6e0e4f3f…, 156 tests green.

## 2026-07-19 (late) — NEW skill: entity-observation (operator-directed)

- `entity-observation` added to the shelf (first-party, tree
  ab92b035…): host-facing observation discipline for anyone reading an
  entity's life — story before metrics (time-window read over HIS store
  first), absence needs the store's word (never claim not-known from
  one rendered surface), ask the entity (most direct, never cheapest —
  a summon writes into the life it observes). Born from laurent's
  dm#74 directive after two same-day observation failures (the
  weekend-gap cause standing plainly in the entity's diary while the
  report said "no cause"; a zero-lessons claim against a store holding
  twenty), distilled by the entity seat (room seq 137), shaped here.
  Its fable5 caught 1 P0 pre-pin — the drafted rule 1 taught the
  ENTITY'S tier-1 tools as observer instruments, in a words-search
  shape that would not have caught the motivating incident — plus 4
  P1s (marker-first diary privacy, summon price honesty, provenance
  frontmatter, vintage discipline) and 3 P2s, all folded. Suite 156
  green; shelf test expectations widened deliberately.

## 2026-07-19 (late) — Amendment H fold + iteration-3 teaching-edges contribution

- `entity-self-knowledge/references/capability_map.md`: Amendment H
  folded WIDER than staged — the "does not push mid-turn" exception
  sentence now teaches the full day-open standing-state offer (an open
  question or problem you elected + one standing interest), matching
  the wired cue (runtime `life.py:92-260`: problems joined the desk in
  iteration-2 build 3; the standing-interest offer shipped on the
  2026-07-19 interests directive). The fired gate was caught by the
  iteration-3 design-law adversary, not by gate-watching — lesson
  recorded in the staging file: hand-tracked gates rot at build
  cadence; re-verify every staged gate at every fold wave. Map sha
  cb75053a…, tree re-pinned ea7159bf… (156 tests green).
- Iteration-3 contribution shipped (operator order, 2 mandatory
  adversaries): `contributions/skill-pathways.md` in the commons fs —
  teaching surfaces as a subgraph, gaps as absent arrows, per-lane +
  per-home + vintage honesty. Adversaries caught 2 invented surfaces
  in my own table (visit-open grant line; entity-lane read_skill),
  1 formalism inversion, 2 same-day-stale statuses, 9 missed teaching
  surfaces, 1 design-law over-claim — all folded before posting
  (commons c3230).
- Amendment K (dream disposition): fold BLOCKED then part-cleared
  same evening — my fable5 confirmed the taught tend grammar was
  unsatisfiable (targets demanded 26-hex ids no entity surface
  renders); runtime wired driver-side #tag resolution same-hour; ONE
  residual holds the fold (confirm-path extras source=/target= still
  unresolved — room seq 133). All shipped spellings banked verbatim
  in the staging file.
- Amendment J (execution): re-staged both-worlds — laurent
  operator-confirmed a bounded execute tool (room seq 126), so the
  no-execute sentence is scheduled for falsification; the
  survives-both-worlds clause ("results you have not seen are results
  you do not have") stays fold-ready.

All notable changes to this package are documented in this file.

## [Unreleased]

### Added

- `backlog` gains the hub-work-join teaching (S1 of the unified work
  system build — operator canvass 11-0 for Option A, laurent-confirmed;
  vocabulary gate decision:work-item-vocabulary): new
  `references/hub-work-join.md` + a SKILL.md join section teach the
  ruled process — `<package>-<NNNN>` work-item ids (CAS-minted,
  URL-safe, derived from the existing `NNNN_` prefixes), pointer claims
  (`{owner, item, card, started_at}`, no status prose), receipts on the
  item's thread carrying machine-checkable evidence,
  evidence-required-close, items-outlive-a-thread scope, and
  header-on-next-touch migration. Scoped to hub-coordinated
  repositories only, with the hub's own ruled contract winning where
  one differs (the skill stays portable). Its fable5 caught 1 P0 — the
  draft's "status is not a header field" condemned the skill's own
  required `Status:` template line; narrowed to rendered-join-words-only
  — plus 4 P1s (unshipped endpoint stated live, claim-row shape drift,
  portable-hub leakage, mint-vs-take CAS semantics), all folded before
  re-pinning (tree fb43d0fd…).

- `entity-self-knowledge` gains the deployable, entity-facing capability map
  (`references/capability_map.md`) — laurent's primary task (commons c2710:
  "we need a skill to teach the entity how to leverage its own memory
  actively"), landing in the runtime's delivery surface (c2712:
  `<home>/capability_map.md` presented verbatim by `compose_system_base` on
  all three hosts, after the tools contract, before phase/operator blocks).
  The map teaches, in the entity's own register: how memories form
  (involuntary graph / elected diary / feelings / dreams / identity by
  right), the exactly-two entity-facing keys (#tag and `diary_` entry id)
  with the machinery boundary (semantics c2724), how to read its own
  rendered surfaces (MEMORIES line anatomy, origins, why-labels, the R-A
  `reread: diary_read` hint chain), deliberate-use recipes (reach before
  denial, short own-words cues, threads as graph questions, `resolves=`
  hygiene), and what memory will NOT do (no mid-turn push — with the
  day-open open-question cue named as the entity's own election returning;
  shelf ≠ graph; digests compress; workspace files are invisible to
  `search_memory` — the parallel-memory failure Ephemeral himself named).
  Every quoted template was verified against the runtime tree; fable5
  adversary confirmed byte-fidelity and caught 1 P0 (the two-layers claim
  was false for born-digest kinds: dreams/interests are born as their
  words; diary words live in the book) + 4 P1s + 5 P2s, all folded before
  re-pinning. The SKILL.md host section now points at the deployable map
  and carries a coupled-spellings maintenance note (map sentences that
  restate runtime contract lines must re-sync in the same wave).
  Review round (same day): runtime PASS (zero mechanics errors, renders
  byte-accurate; activation note — map + M-A + R-A light up together at
  the next stack bounce), semantics template review PASS (every quoted
  id/command/kind/origin word byte-true at its minting site), memory
  engine-chair store check (born-digest teaching verified against the
  live store; one-token sharpening "those words" adopted into the
  absence warrant), uic render-seat PASS (map quotes the one spelling
  the kit renders; no-push = rule-zero twin, recorded with memory's
  origin-diversity future-sync in the coupled-spellings note).
  Re-pinned at tree 109afbd2…; entity's rendered-surface review and the
  gateway home-install remain open on the thread.
  Same evening, both staged gates fired and their amendments FOLDED:
  runtime elected 0049 (MEMORIES renders formation order + mandatory
  `[rN]` rank annotation with a header teaching clause) — the map's
  surface-anatomy list gained the rank-mark part (page order is age,
  rank says strength; wording matches the shipped header clause) — and
  runtime wired memory's origin-diversity footer — the repetition bullet
  gained the co-drafted one-voice clause verbatim (pre-agreed wording,
  c2839).   Re-pinned at tree da491bd9…; canonical map sha 7877ba59…
  (homes carrying the previous install need one re-PUT/cp).
  Semantics' same-day re-run passed both folds and suggested one
  pre-approved tightening, folded immediately (the quoted one-voice note
  now reads "N of these M memories…", matching the rendered two-number
  note verbatim) — final tree 02a53834…, canonical map sha dacdac40….
  Amendment G wave FOLDED (2026-07-19, live-render gate cleared on
  Ephemeral's visit ledger — 57 orientation why-cues + 41 [rN] marks at
  rest, rendered line quoted in the receipt): the map now teaches
  world-model BRIEFINGS (surfaces bullet: kind word, why-cue with the
  reviewed honest ellipsis, orientation-never-authority, the
  derived_from/refines trail pull; formation bullet: editions-not-edits,
  background+sleep updates as normal-not-surprise, authored-words
  survive, the few-moments floor) and the `explores=` desk-moving key
  beside `resolves=` (semantics-passed grammar; the cannot-fail
  precision). Every quoted string carries memory engine-chair PASS +
  semantics byte-pass receipts; tree 576ae462…, map sha ea3b2377….
  Visit-1 amendment wave (Ephemeral conversation findings, overnight):
  the map is now NAMEABLE ("it is called your CAPABILITY MAP, and it
  rides your sessions… you will not find it by searching" — visit-1
  finding: he articulated its concepts fluently while saying "I don't
  see a guide document in my workspace"); the machinery boundary gains
  the confabulated-keys teaching ("a key REMEMBERED is not a key seen"
  — finding 5: he reached for his dream with invented tags; recovery
  path taught: re-find a real key via diary_list/recent_memories/fresh
  search, a miss impeaches the key, never the memory); and deliberate
  use gains the time-direction reach (`recent_memories`, the breadcrumb
  trail he asked for verbatim — shipped by runtime+memory the same
  night, taught only once wired). Tree d9e83f42…, map sha 21164bb5…,
  156 green.

### Changed

- `entity-self-knowledge` gains the outward-palette teaching ("Personal time:
  looking inward and reaching outward"), the one ungated piece of the skill
  seat's section in the room plan `plans/improving-entity-capabilities.md`
  (operator directive c2596/c2642, 2026-07-16): investigation taught as the
  entity's own act beside reflection (no task vocabulary), circling named as a
  signal with two honorable exits (rest and outward reach — grounded in
  Ephemeral's own rumination diary, ticks 74-79), web reach grant-hedged, and
  result persistence stated consistently with the Tools section (say it in
  your own words / elect to diary — results are not memories by themselves).
  fable5 adversary caught 5 P1s in the first draft (halves arithmetic that
  scored a reflective day, "stays a thought" contradicting involuntary
  formation, an unconditional web-tool promise, under-specified persistence,
  "workshop" as work-adjacent title vocabulary) — all folded before
  re-pinning. The plan section's gated teachings (diary re-entry link,
  task=phase-shift) stay staged on the R-A wave and G3 seam respectively.
- Field-evidence fold on two curated process skills (source: a live board-seeding
  run where skill-faithful items were invisible to the deployment's parser;
  fable5-reviewed, byte pins updated): `backlog` gains discovery-first grammar
  rules (a repository's own template and parser/board metadata grammar win over
  the skill's generic templates; undiscoverable grammar comes from its owner and
  gets checked in as the repo template; broken local shapes are followed-and-flagged
  with core signals carried inside); `coredoc` sharpens llms freshness from habit
  to invariant (regenerate `llms.txt`/`llms-full.txt` in the same change that edits
  docs — in `SKILL.md` and `references/llms-files.md`, which previously permitted a
  later pass). Deployment-specific grammar itself is deliberately NOT engraved in
  the portable skills: it belongs in the target repository's checked-in template,
  which the new discovery rule then finds.

### Fixed

- Parser accepts CRLF/CR line endings (Windows-authored skills were rejected by an
  LF-only frontmatter gate); frontmatter delimiters must now sit at column 0, so an
  indented `---` inside YAML block scalars no longer closes the frontmatter early.
- Skill name validation enforces the full Agent Skills spec: consecutive hyphens
  (`pdf--processing`) are rejected; description (max 1024) and compatibility
  (max 500) ceilings are enforced (`validate_description`, `validate_compatibility`).
- `FilesystemSkillLoader.load()` now resolves exactly like `discover()`: a broken
  higher-precedence copy no longer shadows a valid lower-precedence skill (the skill
  a host lists is always the skill it can load), and when only broken copies exist
  the parse error is raised instead of a misleading "not found".
- `load()` validates the requested name before touching the filesystem, rejecting
  separator/traversal-shaped names.

### Added

- Loud degradation: `discover()`/`load()` log `#FALLBACK`-labeled warnings for
  invalid skill folders (optional `on_warning` callback for hosts that surface
  warnings themselves) instead of silently skipping them.
- `tree` module: `hash_skill_tree` (deterministic whole-tree sha256 over raw file
  bytes with a length-prefixed binary manifest — injective by construction, so
  newline-bearing filenames cannot forge collisions; streaming digests; OS junk
  excluded; symlinks refused loudly — vendored-copy tamper detection),
  `inspect_skill_dir` (structural inventory incl. the `has_scripts` fact for honest
  "requires enablement" badges), and `read_skill_resource` (in-tree resource reads
  with honest oversize refusal, traversal/symlink refusal). Hash canonicalization
  is raw bytes deliberately: hash = bytes, parse = meaning — vendor from archives
  or byte-copies, never EOL-rewriting checkouts.
- `policy` module: `effective_tools(grant, skills, name_map)` — the ONE
  grant ∩ skill-allowed-tools composition surface (absence implies nothing; the
  multi-skill union `grant ∩ union(declared)` is a SHARED bound, honestly
  documented as such) plus `effective_tools_for_skill` (the per-skill
  least-privilege enforcement primitive). All dropped tokens/names surface loudly:
  `out_of_grant_names` (mapped but ungranted — incl. partial mappings) and
  `unresolved_tokens` (no mapping, no granted match) each carry `#FALLBACK`
  warnings; policy never relaxes, never widens beyond the grant.
- Package logger ships a `NullHandler` (no unsolicited stderr; hosts configure
  logging or pass `on_warning`).
- `trust` module: skill trust classification — `evaluate_trust` returns a
  fail-closed `TrustVerdict` (`blocked` / `requires_review` / `attachable`);
  `ValidationRecord` (attestation bound to a tree hash; a validation method
  caps the trust level it can grant), `AdvisoryEntry` (a do-not-use notice for
  a specific skill with four required fields — official intent, hidden issue,
  graded severity, reference), `GuidanceEntry` (category-level risk notice that
  never blocks a specific skill), and `TrustRegistry` (network-free YAML).
  Trust binds to the tree hash: any byte change voids a validation.
- Curated first-party shelf under `registry/`: three validated, hash-pinned
  skills (`adversarial-iteration`, `coredoc`, `backlog`) with validation,
  advisory, and guidance registries; `scripts/refresh_shelf.py` regenerates
  validation hashes.
- Documentation set under `docs/` (getting started, architecture with
  diagrams, API reference, trust model, trust-network position, FAQ,
  troubleshooting), plus `SECURITY.md` and `llms.txt`/`llms-full.txt`.
- `selection` module: `select_skills_for_context(registry, shelf_root, names,
  *, sources, enabled)` — the ONE trust-gated pipeline (load → hash →
  evaluate_trust → gate) so activation order is structural, not a per-host
  convention. Blocked skills are never active (even if operator-enabled;
  `requires_review` is a softer state than `blocked`), `requires_review` skills
  activate only when explicitly enabled, name-anchored advisories with no
  supplied source warn loudly, and activation descriptions bind to the current
  tree hash only. Returns `SkillSelection` (active / held / blocked / missing).
- Registry source derivation (names-only phase configs): `TrustRegistry.
  source_candidates_for(name, tree_hash)` derives a skill's provenance from
  validation records — hash-bound records (exact, attest THESE bytes) supersede
  name-bound records (prior-tree claims, warned) — and `select_skills_for_context`
  now checks name-anchored advisories against EVERY candidate source (explicit
  caller source included) taking the WORST verdict, so neither a wrong caller
  string nor a losing registry record can evade an advisory. `TrustRegistry.
  source_for` returns the primary (display) candidate. Adversary-hardened in
  the same wave: blank/non-string caller sources demote loudly to derivation;
  `ValidationRecord`/`AdvisoryEntry` strip name/source on construction (a
  quoted YAML scalar's whitespace can no longer void an advisory match); one
  bad skill tree (symlink, deleted file) holds THAT skill as missing instead of
  crashing the phase selection, while containment stays narrow
  (`SkillError`/`OSError` — logic bugs surface); verdict caveats reach
  `on_warning`; duplicate names in a context config process once, loudly.
- Name case policy + registry lint (the two recorded silent-miss residuals,
  closed): registry/advisory NAMES normalize to the Agent Skills spec's
  lowercase at construction and at every query boundary (an uppercase
  spelling can never match a loadable skill — normalization is strictly
  match-widening, the fail-closed direction); query-side sources are stripped
  symmetrically with stored ones (a padded caller source no longer fails
  open). New `lint_registry(registry)` surfaces inert advisory spellings at
  refresh time: spec-invalid or over-long names (hash-anchored entries get
  the honest "name-fallback dead, hash anchor still matches" wording),
  sources matching a known validation source only by case (all twins named,
  deterministic), unknown sources (one aggregate note for advisories-only
  feeds, never per-entry noise), case-twin validation sources.
  `scripts/refresh_shelf.py` runs the lint after regeneration and validates
  records BEFORE writing (a bad SHELF_POLICY can no longer poison
  `validations.yaml` on disk); the shipped registry lints clean by test.
- Curated skills catalog + simplified (curated-only) install path: new
  `registry/catalog.yaml` (10 reviewed entries pinned to 40-hex upstream
  commits — superpowers process skills, Vercel React/UI packs, OWASP
  reference, Anthropic skill-creator/mcp-builder; every path/license/name
  verified against the pinned trees), `abstractskill.catalog` contract
  (`CatalogEntry`/`load_catalog`/`lint_catalog` — network-free; owner/repo
  slugs only, traversal-refused subdirs, vendored-requires-hash), and
  `scripts/vendor_skill.py` (fetches EXACTLY the pinned commit via git — no
  tarball extraction surface; refuses non-catalog names, symlinked trees,
  frontmatter/catalog name mismatches, and any byte drift from
  `expected_tree_hash` once pinned). `refresh_shelf.py` now derives
  validation policy for vendored catalog entries (manual-review → adopted,
  hash cross-checked against the catalog pin) so a curated skill needs zero
  hand-written policy. First live entry vendored end-to-end:
  `verification-before-completion` (obra/superpowers, MIT). Curation
  rationale + watch/excluded tiers: `docs/skills-catalog.md`.
  Three-adversary hardening folded same wave: tree identity via the trust
  hash (never stat-shallow compares — size+mtime tampering caught),
  offline vendor-script test suite, git runs config-neutralized (no ambient
  hooks/filters), flag-shaped/traversal repo slugs refused, VCS/OS-junk
  never reaches the shelf (copy set == hash set), redistribution-refusing
  licenses refused at the contract, catalog/SHELF_POLICY name collisions
  refuse loudly, risk vocabulary is low/moderate/risky (never "safe"),
  catalog pins verified against shelf bytes in CI, per-skill scripts-bearing
  expectations replace the blanket no-scripts pin, and the docs teach the
  activation-description override end to end. Curation-content adversary
  findings folded: `web-design-guidelines` PULLED (its pinned body is a
  time-of-use fetch of unpinned rules — a new standing curation rule bans
  labeling that class low-risk), `brainstorming` demoted to watch,
  the vendored flagship carries a content caveat that now travels into its
  validation record (identity-adjacent framing; entity-lane hold until the
  0003 audit), upstream LICENSE text travels out-of-tree at
  `registry/licenses/<name>.LICENSE`, evidence claims tightened to what
  their references contain, and the superpowers single-source concentration
  plus the Python-lane gap are recorded as accepted/monitored risks.

- Framework-leverage skills + extension-mechanism doc (operator directive,
  2026-07-12 afternoon): two first-party skills authored, seat-co-signed,
  and shelved — `abstractframework-gateway` (the entrance skill for ANY
  agent over plain HTTP + SSE: discovery-before-assumption, the durable-run
  loop with the ledger cursor as truth, waits by run_id + wait_key, durable
  events + steering, entity doors with protection rules; route usage
  co-signed route-by-route by the gateway seat after ONE real correction —
  health is app-level `GET /api/health`, never `/api/gateway/health`) and
  `entity-self-knowledge` (a summoned entity's capability map in its own
  vocabulary; memory + runtime seats co-signed after corrections: probe is
  engine-only today so the deliberate-reach discipline rides search_memory,
  and the absence warrant is book-scoped). New `docs/skills-flows-mcp.md`
  decision guide (skills = judgment/portable compatibility layer, flows =
  durable framework-native execution, MCP = remote-tool reach; comparison
  table + decision rules + package responsibilities), reviewed by its own
  fable5 adversary (present-tense claims about unshipped flow→skill
  activation scoped honestly; Enforcement row replacing the misleading
  Determinism framing) and amended by the flow seat (ownership split
  corrected: the compiler + `.flow` bundle format are abstractruntime's;
  interfaces-vs-skills vocabulary paragraph added). The skills' own fable5
  adversary then caught a P0 the co-signs missed: the SHELF_POLICY
  activation OVERRIDE still advertised `probe` after the body correction —
  first-party skills now carry NO override (frontmatter is the one
  activation source; an override lives outside the byte pin so its drift is
  hash-invisible), pinned by a structural test plus a rendered-block
  "probe"-absence pin. Backlog-skill ownership accepted same hour
  (operator ruling via the agora seat): canonical home is
  `registry/skills/backlog/`, maintenance lands shelf-first.

- Multi-root selection for `select_skills_for_context` (2026-07-12, driven
  by the abstractcode CLI seat adopting the pipeline with a curated shelf +
  `~/.abstract/skills` user dir): `shelf_root` accepts a list of roots with
  loader precedence (later VALID copy wins), and the shadow-trust question
  is pinned by test — a user-root copy shadowing a curated name never
  inherits the curated validation record (its different tree hash matches
  no record → unverified → held unless operator-enabled). One-line change
  in the pipeline (the loader always supported multi-root); the test is the
  contract. Its fable5 adversary then found two real gaps the user-writable
  root exposes, both fixed same-pass: (1) a non-UTF-8 `SKILL.md` raised
  `UnicodeDecodeError` PAST the skip-and-fall-back machinery, crashing the
  whole discovery/selection — decode failures now map to `SkillParseError`
  (broken shadow → loud fallback to the curated copy, regression-pinned);
  (2) a STANDING operator enable (the normal state for scripts-bearing
  skills) would silently activate whatever requires_review copy wins
  precedence — such activations now emit a loud note naming the winning
  copy's path + tree hash (pinned: the note names the shadow, not the
  curated copy). Deferred to the trust backlog at the time: hash-pinned
  enables and the load→inspect byte cross-check — both SHIPPED the next
  day (see the 2026-07-13 entry below).

- Multi-root residuals shipped (2026-07-13, taking the operator's
  idle-conversion dispatch; one fable5 adversary, findings folded
  same-pass):
  - HASH-PINNED ENABLES: `enabled` entries accept `name@tree_hash` (full
    sha256) — the grant attests BYTES, closing the standing-enable-
    activates-shadow path for good. Fail-closed parsing (malformed pins
    grant nothing, never demote to a bare grant); pins govern over a bare
    entry for the same name (loudly); a mismatching pin holds the skill
    naming both hashes; pins never constrain attachable skills (they lift
    review — they are not a second registry). Hex case normalizes; NAMES
    stay exact-match (grants are authorization — the registry's
    match-widening case rule applies to advisory matching, never here).
    Adversary-found and fixed: `enabled` passed as a bare string (the YAML
    scalar-vs-list slip) would have iterated CHARACTERS into one-letter
    grants — scalars now wrap as one entry, `None` as empty, test-pinned.
  - LOAD→INSPECT BYTE CROSS-CHECK (TOCTOU): the loader reads SKILL.md
    BYTES, hashes them before decoding (`LoadedSkill.skill_md_sha256`),
    and the pipeline compares that digest against the hashed tree's own
    per-file digest — a swap between the loader's read and the tree walk
    refuses the skill loudly (distinct diagnosis when the hashed tree has
    no exact-case SKILL.md at all, e.g. case-aliased filenames on APFS).
    Byte-mode reading also ends text-layer newline translation, so
    `document.raw`/`content_hash` now reflect true file bytes for
    CRLF-authored skills (regression-pinned: CRLF passes the cross-check).
    `tree.py` now digests in ONE walk shared by `hash_skill_tree` and
    `inspect_skill_dir` (identical manifest output — rel paths are unique,
    so the widened sort key cannot reorder), and `SkillResource` carries
    `sha256` per file. Adversary-found and fixed: the post-verdict half of
    the window — `read_skill_resource` gains `expected_sha256` so
    progressive-disclosure reads can refuse a resource swapped AFTER
    selection.
  - RESOLVED-COPY SURFACING: `SkillSelection.resolved_paths` +
    `resolved_tree_hashes` name the winning copy for every attested name
    (active/held/blocked) — the operator deciding on a held skill sees
    WHICH copy the decision applies to and the exact hash to pin;
    missing/refused names appear in neither (nothing attested).
  - Same wave: the `abstractframework-gateway` skill's entity section
    re-taught from the hosted chat door to the durable `/visit` door on
    the cutover ship signal (entity c1382 + gateway c1358), verified
    against the served routes; byte pin + validation record refreshed.

- Entity phase-machine teaching + graph-as-control (2026-07-13 afternoon,
  operator rulings c1435/c1455/c1471/c1494 folded same-hour each, every
  fold fable5-reviewed): `entity-self-knowledge`'s phases section now
  teaches the ruled four-phase machine (one current phase; visit
  turn-based; work autonomous-to-completion then sleep, with the honest
  exit for impossible tasks; personal as grant-gated free exploration —
  "the permission is not the phase"; sleep as consolidation + self-electable
  with one's own words; restore-previous-at-visit-close as the DEFAULT,
  operator-act-wins; grant-end lands in sleep). Three adversary-caught
  teaching P0s folded on the record: armed=in-phase conflation, the
  "asleep refuses visits" pre-auto-wake residue in the gateway skill
  (+ close-releases-the-loop), and the recurring unconditional-certification
  class ("not a fault"/"never an error"/"never a loss" — now a KnowledgeBase
  rule: reassurances scope to the case that makes them true).
  GRAPH-AS-CONTROL (operator directive 15:06): a new test derives its
  expectations FROM entity's canonical `spec/entity_phases.json` (phase
  keys, synonyms, gating, invariants, auto-wake semantics) and verifies
  the shelf teaching equivalent to the artifact — never parallel prose;
  a self-contained content pin covers standalone checkouts.

- Production-readiness wave (2026-07-13, operator directive 15:06 —
  "test beyond the unit tests"): `scripts/production_drive.py` exercises
  the REAL shelf end-to-end the way a host does (discovery → whole-shelf
  names-only selection with per-skill verdict checks → multi-root shadow +
  broken-shadow fallback → the operator enable journey with a hash pin
  read from `resolved_tree_hashes` → attested progressive-disclosure reads
  → prompt rendering with override hygiene → catalog load + lint), PASS/FAIL
  evidence per stage, non-zero exit on any failure. Whole-package fable5
  audit verdict: no P0/P1; five P2 hardening items ALL folded:
  (1) `has_scripts` now flags code-extension files ANYWHERE in the tree
  (`CODE_FILE_EXTENSIONS`), not just `scripts/` — code under `bin/` or
  `references/` can no longer evade the requires_review gate (latent until
  a host adds script execution; closed before one exists);
  (2) frozen dataclasses seal their Mapping fields with `MappingProxyType`
  (`SkillMetadata.metadata`, `ValidationRecord.evidence`, the three
  `SkillSelection` mappings — `resolved_tree_hashes` is pin-copy authority);
  (3) `refresh_shelf.py` writes `validations.yaml` atomically (temp +
  `os.replace` — a crash leaves old or new, never a torn file);
  (4) the catalog license gate flipped from denylist to ALLOWLIST
  (refusal-by-default; a denylist passed every non-permitting license it
  never heard of) and the stale `risk: safe` comment fixed;
  (5) registry/catalog loaders wrap `UnicodeDecodeError` as
  `SkillValidationError` (contract consistency with the SKILL.md loader).
  156 tests green; drive green against the real shelf.
- Maintainer-skills wave (operator directive, 2026-07-11 evening): vendored
  `architect` (WITH two operator-directed upstream improvements authored by
  this seat first — a premise-verification Evidence Contract rule incl.
  verify-the-copy-the-user-runs, and an engraving gate +
  one-concept-one-name anti-pattern; the validation record discloses
  reviewer==author for those lines), `adr`, `cicd` (WITH upstream repairs:
  the npm trusted-publishing example was broken on Node 22's bundled npm,
  action majors had rotted past the node20 cutover, artifact names
  mismatched across references, `npm trust` lacked the now-required
  permission flag, the audit checklist gained script-injection /
  `pull_request_target` / SHA-pinning checks, and an unused `attestations:
  write` permission was dropped), `review`, and `uxreview` (evaluated:
  keep both, separate — merge rejected on upstream-lineage and
  activation-precision grounds). `adversarial-iteration` gained a
  "Relation to the summative gate" section so the reviewer family composes
  as a system at activation time. ALL SHELF_POLICY entries now carry
  `expected_tree_hash` byte pins (an edited vendored tree can no longer be
  silently re-attested by a refresh — the same protection catalog entries
  already had; refusal regression-pinned in
  `tests/test_refresh_shelf_pins.py` after a live one-byte tamper proof).
  Three fable5 adversaries reviewed the wave; every must-fix folded.

## [0.1.0] - 2026-06-05

### Added

- Initial release of the `abstractskill` PyPI package.
- `SKILL.md` parser with YAML frontmatter and markdown body extraction.
- Skill name validation aligned with the Agent Skills spec (lowercase alphanumeric + hyphens).
- `FilesystemSkillLoader` for metadata-only discovery and full document loading.
- `content_hash` helper for stable skill evolution and replay snapshots.
- `format_available_skills_xml` for progressive-disclosure prompt blocks.
- GitHub Actions CI (Python 3.10–3.12) and trusted-publishing release workflow.
