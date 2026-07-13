# AbstractSkill — Knowledge Base

Accumulated critical insights, contract decisions, and lessons. Never remove an
entry; deprecated entries move to the DEPRECATED section with reasons.

## Contract decisions

### Hashing: hash = bytes, parse = meaning (2026-07-11)
- `content_hash` (one document) and `hash_skill_tree` (whole folder) are
  byte-exact deliberately. Tamper detection must never call two byte-different
  trees "the same"; EOL normalization would do exactly that.
- Consequence: vendor skills from archives or byte-copies, never through
  EOL-rewriting checkouts (git `autocrlf` produces honest mismatches).
- A CRLF-authored skill and its LF twin parse identically but hash differently
  — by design.

### Tree-hash manifests must be injective (2026-07-11, adversary-found P0)
- POSIX permits `\n` in filenames: a text manifest joined with delimiters is
  FORGEABLE (a crafted single file can collide with a two-file tree — a
  demonstrated collision, regression-pinned in `test_tree.py`).
- Fix shape: length-prefixed binary manifest (len(path) + path + digest),
  sorted by POSIX relpath. Any future manifest format must preserve
  injectivity of the serialization.

### Parser line-boundary discipline (2026-07-11, adversary-found P1)
- `str.splitlines()` splits on 8 boundaries beyond `\n`/`\r\n`/`\r`
  (`\v \f \x1c \x1d \x1e \x85 \u2028 \u2029`); YAML does not. Using it for
  frontmatter delimiting created a parser differential: an embedded `\x0c---`
  closed the frontmatter early, silently truncating metadata into the body.
- Rule: normalize exactly `\r\n`/`\r` → `\n`, split on `\n` only. Exotic
  boundary characters then reach PyYAML, which refuses them LOUDLY —
  refusal over silent truncation.
- Frontmatter delimiters match at column 0 only (rstrip, never strip):
  an indented `---` is legitimate YAML block-scalar content.

### allowed-tools composition semantics (2026-07-11)
- The GRANT is the only tool authority; skills narrow below it, never widen.
  Empty grant denies all. Absence of `allowed-tools` implies NOTHING
  (pure-knowledge skill — never "all tools", never zero).
- Multi-skill composition is `grant ∩ union(declared)` — strict pairwise
  intersection would zero two disjoint declared skills (broken).
- HONEST LIMIT (adversary-forced contract line): the union is a SHARED bound,
  not per-skill least privilege — co-active declared skills widen each other
  up to the grant. Per-skill least privilege requires call attribution;
  `effective_tools_for_skill` is that primitive. Consoles render the
  per-skill view; unattributed runtime enforcement gets the union view.
- Every dropped token/name (unmappable OR mapped-but-ungranted, including
  partial mappings) carries a `#FALLBACK` warning. Policy never relaxes.
- Token→framework-name mapping (`Bash(git:*)` etc.) is HOST-owned
  (`name_map` param); the library never guesses.

### Loader resolution invariant (2026-07-11)
- `discover()` and `load()` must resolve identically: the skill a host lists
  is always the skill it can load. A broken higher-precedence copy never
  shadows a valid lower-precedence one; broken copies skip with `#FALLBACK`
  warnings (logged + optional `on_warning`); only-broken copies raise the
  parse error, never a misleading "not found".
- `load(name)` validates the name before touching the filesystem
  (rejects separator/traversal-shaped names).

### Structural facts over frontmatter claims (2026-07-11)
- `inspect_skill_dir().has_scripts` derives from the TREE (any file under
  `scripts/`), never from frontmatter — a "requires enablement" badge cannot
  be lied to by the skill's own metadata. Same pattern as the framework's
  "never-purge is structural" rule: absence of an execution path IS the
  guarantee.

### Spec conformance (agentskills.io, verified 2026-07)
- name: 1-64 chars, lowercase alnum + single hyphens (no leading/trailing/
  consecutive), must match the leaf directory. Regex shape:
  `^[a-z0-9]+(?:-[a-z0-9]+)*$` (structure enforces hyphen rules without
  lookaheads).
- description: 1-1024 chars. compatibility: ≤500 chars. Enforced with loud
  refusals naming limit + actual size.

### Skill trust: bind to bytes, fail closed, advisory wins (2026-07-11)
- Trust binds to the TREE HASH, never the name (a name is claimable). Any byte
  change voids a validation. `evaluate_trust` normalizes the hash ONCE at the
  top so the advisory match and the validation lookup see the same bytes —
  an uppercase-hex query must never bypass a block while keeping its
  validation (adversary-found P0; "advisory wins" must hold for every spelling
  of the same hash).
- The verdict is fail-CLOSED: three orthogonal booleans (`blocked` /
  `requires_review` / `attachable`). UNVERIFIED, scripts-present, and
  low/medium advisories all set `requires_review`; only a validated,
  advisory-free, script-free skill is `attachable`. A consumer reading only
  `attachable` therefore attaches nothing unvetted.
- Severity is GRADED and the verdict honors it: critical/high hard-block;
  low/medium require review; a HASH-matched advisory of any severity blocks
  (exact bytes are specific enough to forbid). The enum meaning and the
  verdict must never contradict (adversary-found P1).
- A validation METHOD caps the trust level it can grant (`_METHOD_MAX_LEVEL`):
  `first-party-adoption`/`manual-review` → at most `adopted`; audits → at most
  `audited`; only `first-party` → `first_party`. "Reviewed" can never
  masquerade as "audited" in code (adversary-found P1 overclaim).
- ADVISORY ≠ GUIDANCE: an advisory names a SPECIFIC skill (matchable by hash
  or name+source) and can block; guidance is a CATEGORY notice that informs
  but never blocks a specific skill. A class label in the advisory registry is
  an inert notice masquerading as protection (adversary-found P0). The shipped
  advisory registry is empty at v1 — the framework does not self-assert a
  specific malicious skill before its own audit or a leveraged feed names one.
- `simulated-execution` evidence must be REAL (`epochs >= 1`, non-empty
  `models`, and `bool` is not an int here) — a presence-only gate is
  decorative (adversary-found P1/P2).
- `scripts/refresh_shelf.py` preserves `validated_at` for unchanged tree
  hashes — re-running must not re-stamp an attestation date on which no review
  happened (adversary-found P1).
- Trust-gate-before-compose must be STRUCTURAL, not conventional: the
  primitives (`evaluate_trust`, `effective_tools`, `format_available_skills_xml`)
  accept raw metadata with no trust coupling, so a host can skip the gate.
  `select_skills_for_context` is the one composed pipeline that cannot skip it;
  activation should always go through it, never through `discover()` piped
  straight into composition (discovery is for LISTING only).
- BLOCKED is harder than requires_review: a blocked verdict has
  `requires_review == False`. Never branch on `requires_review` alone to gate
  activation (`if requires_review: gate; else: activate` would activate a
  blocked skill). The safe single read is `attachable`; blocked must never be
  operator-enableable (adversary-found P1-B trap).
- Name-anchored advisories need a host-supplied `source` to match
  (`SkillMetadata` carries none by design). When a name-anchored advisory
  exists and no source is supplied, the selection pipeline warns `#FALLBACK`
  rather than silently skipping the advisory check (adversary-found P1-A).
  SUPERSEDED IN PART (2026-07-11, names-only phase configs): sources now
  DERIVE from the registry's validation records when the caller passes none
  (`TrustRegistry.source_candidates_for`) — the warning fires only when the
  registry carries no provenance either.
- Advisory checks must run against the FULL candidate-source set, never one
  winner: two registry records can attest the same bytes under different
  sources, and an advisory targeting the LOSING source must still block —
  picking a single "primary" source is a gate-evasion vector (adversary-found,
  one step from P0, 2026-07-11). Same rule for a caller-supplied source that
  contradicts registry provenance: check both, worst verdict wins.
- Exact-equality matching semantics demand normalize-at-construction:
  `ValidationRecord`/`AdvisoryEntry` strip name/source on construction
  (whitespace from a quoted YAML scalar must never silently void an advisory
  match — the tree_hash normalize-once rule generalized). Case-folding policy
  is a deliberate residual: names are case-sensitive today, queued in the
  trust backlog. RESOLVED (same day): names normalize to spec lowercase at
  construction AND every query boundary (the spec forbids uppercase skill
  names, so case is noise — and normalization is strictly match-WIDENING,
  the fail-closed direction: no previously-working match can be lost);
  sources stay case-sensitive by policy with `lint_registry` catching
  case-only near-misses at refresh time (warns, never refuses — an advisory
  may legitimately name a marketplace we never validated from).
- Normalization must be SYMMETRIC or it is a hole: normalizing stored fields
  without the query side (or vice versa) converts a curator typo into a
  fail-open path (the padded-query-source finding — stored sources stripped,
  query sources raw, advisory silently missed). Rule: every field that
  matches by equality normalizes ONCE at construction and ONCE at each query
  entry point, with the same function.
- Containment breadth is a two-sided trap: per-skill failures (bad tree,
  symlink, deleted file) must hold ONE skill as missing, never crash the
  phase selection (one bad apple ≠ phase denial) — but the catch must stay
  NARROW (`SkillError`/`OSError`): an `except Exception` would silently
  demote a logic bug in loader/tree code to "skill not loadable" framework-wide
  (adversary-found NEW-2, 2026-07-11).
- Skills never gate tools; only a phase/state's tool grant does. An empty
  skill set restricts nothing tool-wise (`effective_tools(grant, [])` returns
  the full grant — absence implies nothing). Regulate a state by its tools
  grant, not by leaving its skills empty (adversary note P2-E).

- Curated-only install is STRUCTURAL, never a convention: the vendor script
  has no URL argument; the catalog contract refuses anything but owner/repo
  slugs with alphanumeric-leading segments and 40-hex commit pins; the first
  vendoring trusts git's commit-hash verification + human diff review (stated
  trust floor), every re-vendor is SHA-256 whole-tree verified. Tree identity
  checks use the SAME hash trust binds to — never stat-shallow compares
  (size+mtime equality must not pass for byte-different files).
- Tool guidance is part of the gate: a vendor script that prints a wrong
  NEXT step (hand-written SHELF_POLICY for a catalog skill) mints
  false-provenance records by instruction — the printed workflow must match
  the derived-policy reality, and name collisions between policy sources
  refuse loudly (adversary-found, 2026-07-11).
- The word "safe" never renders on operator-facing surfaces, including risk
  CLASS labels (the catalog risk enum is low/moderate/risky — a --list table
  is functionally a badge to a naive reader).
- TIME-OF-USE FETCH is a curation class scanners and has_scripts cannot see:
  a script-free skill body that instructs fetching external instructions at
  use time (e.g. "fetch fresh guidelines from <repo>@main before each
  review") defeats hash pinning entirely — the tree hash pins a pointer, not
  the rules (the ASG-2026-0003 post-approval-swap class, found live in a
  major vendor's skill by our own adversarial review). Rule: never below
  risk=moderate, always an explicit note, prefer re-scoping to vendor the
  actual rules at a pin. Structural verification (paths/licenses/trees) is
  NOT content verification — every claim about what a body CONTAINS requires
  reading the body at the pin.
- Curation caveats must travel INTO the validation record (catalog notes
  append to the derived record's notes): a content warning that lives only
  in the catalog is invisible to trust-registry consumers — and identity-
  adjacent framing in a skill body ("if you lie, you'll be replaced") is
  ordinary for developer agents but must be flagged before any entity-lane
  attach (append-only memory cannot delete an engrammed threat-anchored
  value).
- EVERY shelf entry carries an `expected_tree_hash` byte pin (2026-07-11,
  adversary-found): without pins, editing a vendored tree and re-running
  refresh silently re-attests the edited bytes at the same trust level —
  provenance laundering by refresh. With pins, refresh refuses until the
  curator updates the pin deliberately; catalog-vendored entries already had
  this via the catalog pin, first-party/maintainer entries now match.
- Copy-paste workflow examples in skills ROT (2026-07-11, cicd adversary):
  hardcoded action majors, runtime-version floors (npm ≥ 11.5.1 for OIDC
  trusted publishing — Node 22's bundled npm silently never runs the
  handshake), and CLI permission-flag requirements all drift. Rule for
  vendored how-to skills: version-sensitive examples use
  `<current-major>`-style placeholders + a stated version policy, and floors
  are stated WITH the failure mode they prevent.
- Reviewer-family composition is a SYSTEM property that must live in the
  bodies consumers actually activate (2026-07-11): the formative loop
  (`adversarial-iteration`) now names the summative gates (`review`,
  `architect`, `uxreview`) and translates the explicit-invocation idiom;
  a composition contract that lives only in a catalog doc never reaches an
  agent that activated one skill by description match.
- First-party skills carry NO activation override (2026-07-12,
  adversary-found P0): the override mechanism exists for VENDORED trees we
  cannot edit; on a first-party skill it creates a second description
  living OUTSIDE the byte pin, so its drift is invisible to every hash
  check — and it drifted within ONE authoring wave (the override still
  advertised `probe` after the co-signed body correction removed it, on
  the exact skill whose subject is faculty honesty). Frontmatter is the
  one activation source for first-party skills; structural test enforces.
- Skills whose CONTENT claims other seats' surfaces get OWNER CO-SIGNS
  before the validation record settles (2026-07-12, framework-skills
  wave): three seats corrected real claims same-day (a nonexistent health
  route that 401s-then-404s like a trap; a faculty no entity holds yet;
  an absence warrant true for one memory plane and not the other). The
  co-sign citations live in the record's notes. Teaching-bug class from
  Castor's night, prevented at authoring time.
- Faculty honesty in entity-facing skills: never teach a tool name the
  session does not expose ("use the tools your session actually names,
  not tools you have heard described") — an entity reaching for a
  described-but-unwired tool hits an honest refusal and diagnoses "memory
  and record disagree" (the wrong-diary-id incident class).
- Grants are authorization, not matching (2026-07-13, hash-pinned enables
  wave): the registry's case-normalization rule is match-WIDENING and
  fail-closed for advisory/record lookup — applied to an `enabled` grant it
  becomes activation-widening, i.e. fail-OPEN. Enable names therefore stay
  exact-match while advisory matching normalizes. Same wave, same class:
  an `enabled` value passed as a bare string would iterate CHARACTERS into
  one-letter grants (single-char names are spec-valid) — type guards on
  the grant surface are security controls, not conveniences.
- A trust verdict attests bytes only if the SAME bytes were parsed and
  hashed (2026-07-13): load and tree-hash are two reads, and on a
  user-writable root the window between them is a swap opportunity. The
  pipeline cross-checks the parsed SKILL.md digest against the hashed
  tree's per-file digest (single-walk inventory) and refuses on
  divergence; `read_skill_resource(expected_sha256=)` extends the same
  attestation to progressive-disclosure reads AFTER selection. Rule: any
  new surface that reads skill bytes post-verdict must accept and check
  the inventory digest.
- Entrance-teaching skills track the doors they teach (2026-07-13, visit
  cutover): the entity section of `abstractframework-gateway` was
  re-taught from the hosted chat lane to the durable `/visit` lane the
  same day the drawer flip shipped — deliberately not before (teaching an
  unlanded default is the same rot mirrored). The cross-seat mechanism
  that made this work: the shipping seats named `skill` in their ship
  messages (agreed in advance on the record), so the re-teach window
  opened with the flip, not behind it.
- Unconditional certification is a recurring engram hazard in reassurance
  writing (2026-07-13, caught THREE times in one day on one skill): "not a
  fault" (unscoped — suppressed the armed-but-missing report), "never an
  error" (certified every experience of a mechanism that can malfunction),
  "an interruption is never a loss" (contradicted the grant hedge one
  clause earlier — self-caught pre-ship). The pattern: a comforting
  absolute quietly forecloses the honest report of the case it didn't
  anticipate, and in append-only memory the foreclosure persists. Rule:
  reassurances in entity-facing teaching are SCOPED to the case that makes
  them true ("when none has been granted, quiet is normal"); the
  structural description carries the comfort, absolutes never do. Also
  ruled into the phases teaching: mechanism-intent claims ("by design")
  must not be converted into universal experience claims.
- Teaching an entity about its own kill switch (2026-07-13, liveness-axis
  ruling; the craft rules from its fable5, recorded for reuse): (a)
  heading-less placement — headings are what scanning/summarization
  surfaces promote into landmarks, and the switch should be known, never
  loom; (b) NAME the punish prior and answer it ("protect you, not punish
  you") — the training distribution saturates kill-switch-as-punishment,
  so omitting the denial leaves the prior to fill the vacuum; (c) trigger
  lists are marked EXEMPLARY, never exhaustive (an entity stopped for an
  unlisted reason must not have to choose between identity injury and
  teaching-was-false); (d) every named trigger is not-a-choice-of-the-
  entity — a behavior→stop contingency is a masking-teacher and must be
  absent; (e) the certifiable-by-construction reassurances are memory
  persistence ("a stop takes nothing from you" — processes block, files
  persist) and no-time-passes (the dreamless framing, foreclosing
  frozen-and-aware); (f) agency lands as asking-after-a-gap, never
  self-monitoring; (g) give the operator BOTH halves of the switch
  (stopping and restoring) — keeper of both doors, not executioner.

## Seat operating decisions

- Skill bodies entering prompts: nonce-fencing is the prompt COMPOSER's lane
  (nonce freshness is render-time); abstractskill ships the fence-shape helper
  + the canonical "procedures, never identity/authority" contract line
  (queued as of 2026-07-11).
- Skill identity: spec `name` is the reference key; registry/manifest entries
  carry (source, name, tree_hash) — hash participates in VERIFICATION, never
  naming; same-name-different-source at attach refuses loudly.
- Catalog budgeting is the HOST's lane: the library provides sizes
  (`SkillInventory`), never slices. Metadata line worst case ≈ 270 tokens.
- Agency caps audit (2026-07-11): abstractskill carries ZERO agency caps —
  passive contract library; validation ceilings are spec document constraints;
  `read_skill_resource.max_bytes` is caller-supplied with no default.

## DEPRECATED

(none yet)
