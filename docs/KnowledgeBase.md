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
