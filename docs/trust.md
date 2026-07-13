# Trust model

AbstractSkill classifies how much a specific skill should be trusted, whether
it is forbidden, and whether it needs review before use. This supports a
system of validated skills and a do-not-use notice for skills that should not
be used.

## What trust binds to

Trust binds to the **tree hash**, never the name. A name is claimable; the
bytes are not. A validation of one tree hash says nothing about a different
one — any byte change (an edit, a tampered vendored copy, an upstream update)
voids the validation and demands re-validation. `hash_skill_tree` provides a
byte-exact, injective whole-tree hash for this.

## Trust levels

`TrustLevel`, from least to most trusted:

- `unverified` — no validation record for this tree hash. Requires review.
- `community` — validated by a community process.
- `adopted` — externally authored, first-party reviewed (not behaviorally
  audited). Granted by `first-party-adoption`/`manual-review`.
- `audited` — passed a behavioral/simulation audit or a named external audit.
- `first_party` — authored and owned by the framework.

`blocked` is not a level a validation grants; it is a verdict an advisory
forces. A validation method can only grant up to its cap (adoption can never
claim `first_party`), so "reviewed" can never masquerade as "audited".

## Validation records

A `ValidationRecord` attests that a tree hash earned a level, by a method,
with evidence:

- `simulated-execution` requires real evidence (`epochs ≥ 1`, non-empty
  `models`) — see the [audit methodology](backlog/planned/trust/0003_simulated_execution_audit_harness.md).
- `external-audit` requires a reference URL.
- Provenance fields (name, source, validated_by, validated_at) must be
  non-empty; the tree hash must be valid hex.

## Do-not-use advisories

An `AdvisoryEntry` names a **specific** skill that should not be used and
carries four mandated fields:

- **official_intent** — what the skill claims to do;
- **hidden_issue** — the actual problem;
- **severity** — `critical`/`high`/`medium`/`low`;
- **reference** — a link to understand the problem.

Identification prefers the tree hash (exact); name+source is a weaker fallback
that surfaces a warning. Severity is graded: critical/high hard-block; a
hash-matched advisory always blocks; low/medium force review. Advisories are
corrected by **withdrawal** (status + reason + date), never deletion.

The shipped `registry/advisories.yaml` is intentionally empty at v1:
AbstractSkill does not assert a specific malicious skill on its own authority
before its own audit (0003) or a leveraged external feed (0004) identifies a
real one. Asserting a specific skill wrongly is itself harmful.

## Guidance

A `GuidanceEntry` is a **category-level** risk notice (e.g. "unvetted
marketplace skills are a supply-chain surface"). Guidance informs a picker or
operator and carries a reference, but never produces a blocked verdict on an
individual skill — a class label cannot honestly forbid a specific skill.
`registry/guidance.yaml` ships three notices grounded in published 2026
research (Snyk ToxicSkills, the 98,380-skill behavioral study, the SkillScan
script-bundling finding).

## The verdict

`evaluate_trust(...)` returns a `TrustVerdict` with three orthogonal,
fail-closed signals:

- `blocked` — never attach (a blocking advisory matched);
- `requires_review` — an operator must decide (unverified, scripts present, or
  a low/medium advisory);
- `attachable` — the green path only: positively validated, advisory-free,
  script-free.

A consumer that reads only `attachable` therefore attaches nothing unvetted.
Every verdict lists `reasons` naming the records it rests on, so a UI shows
**why**, not just a colored badge.

## Source derivation (names-only configs)

Name-anchored advisories match on the `(name, source)` pair — names
case-insensitively (normalized to the spec's lowercase at construction and
at query boundaries; an uppercase spelling can never match a loadable
skill), sources by **exact string equality** after whitespace stripping
(`lint_registry` flags case-only near-misses and unknown sources at refresh
time). A per-phase config stores skill NAMES only; provenance lives in the
registry's validation records. `select_skills_for_context` therefore derives
each skill's candidate sources when the caller supplies none:

- **hash-bound** records (records for THESE exact bytes) are exact provenance
  and supersede everything;
- **name-bound** records (same name, other bytes) are prior-tree claims —
  used, but loudly `#FALLBACK`-warned;
- advisories are checked against **every** candidate (a caller-supplied
  source included) and the WORST verdict wins — neither a wrong caller
  string nor a losing registry record can evade an advisory;
- blank/non-string caller sources demote to derivation with a loud note;
- with no source anywhere and a same-name name-anchored advisory active, the
  pipeline warns that name/source matching is disabled for that skill
  (hash-anchored advisories always apply regardless).

`TrustRegistry.source_for` returns the primary (display) candidate for
picker/provenance rendering; gate paths always use the full candidate set.

## What trust does NOT guarantee

Trust classification raises the bar; it does not certify safety. A validation
attests a review or an audit happened, not that the skill is provably benign
(semantic evasion beats any finite battery). A signature (when JOIN lands)
proves authenticity and integrity, not safety. Curation, behavioral audit
(0003), and the fail-closed default remain the real gate; the registries make
the judgment explicit, explainable, and byte-bound.

## Maintaining the registries

- `scripts/refresh_shelf.py` regenerates `validations.yaml` from the vendored
  shelf's real hashes; a test fails if a checked-in record drifts from the
  bytes.
- The same script runs `lint_registry` after regeneration: inert advisory
  spellings (spec-invalid names, sources that match no known validation
  source or match only by case) surface at refresh time, not incident time.
  Lint warns, never refuses — an advisory may legitimately name a
  marketplace we never validated from; the curator judges.
- The [advisory-registry review](backlog/recurrent/advisory-registry-review.md)
  recurrent task keeps references live and hashes current.
