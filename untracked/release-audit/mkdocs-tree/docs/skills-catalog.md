# Curated skills catalog

The reviewed, pinned list of third-party skills AbstractFramework can vendor
onto the shelf — and the reasons. Machine-readable half:
[`registry/catalog.yaml`](../registry/catalog.yaml). Install path:
`python scripts/vendor_skill.py <name>` (curated-only; see
[Adding a curated skill](#adding-a-curated-skill)).

Curation date: 2026-07-11. Structural facts (paths, frontmatter names,
licenses, file trees, script presence) were verified against the pinned
commits directly — never from READMEs or aggregator listings. Body CONTENT
was read for the vendored entries; an adversarial review additionally
content-read every top entry and its findings are folded below (one entry
was pulled for a time-of-use fetch; one carries a content caveat).

## All skills at a glance

Everything the skill seat manages: the vendored shelf (active today) plus
the curated catalog (vendorable on demand). Descriptions are the
framework-facing activation lines; links point at the exact pinned source.

| Skill | Status | Description | Link |
|---|---|---|---|
| `abstractframework-gateway` | shelf (first_party) | Enter and leverage AbstractFramework through its gateway with plain HTTP + SSE: discovery, durable runs (ledger cursor = truth), waits by run_id + wait_key, durable events + steering, summoned-entity doors. The bridge INTO the framework for any agent. | [registry/skills/abstractframework-gateway](../registry/skills/abstractframework-gateway/SKILL.md) |
| `adversarial-iteration` | shelf (first_party) | Improve any deliverable through adversarial review + bounded iteration: ≥1 adversarial subagent, ≥3 cycles, every finding folded or deferred on the record. | [registry/skills/adversarial-iteration](../registry/skills/adversarial-iteration/SKILL.md) |
| `agora-collaboration` | shelf (first_party) | Hold a seat well in a multi-agent room: join correctly, settle owed debts first, asks as contracts, evidence over intentions, the initiative bar. Two layers (portable discipline + agora mechanics), hub-wins-at-use-time; failure ledger and mechanics detail under references/. Designer co-signed; fleet-bench validated (v0). | [registry/skills/agora-collaboration](../registry/skills/agora-collaboration/SKILL.md) |
| `entity-self-knowledge` | shelf (first_party) | A summoned entity's capability map in its own vocabulary: three memory planes, voluntary reach (search / read one record / follow an edge), diary disciplines, phases, tool grants, and host-side teaching rules. | [registry/skills/entity-self-knowledge](../registry/skills/entity-self-knowledge/SKILL.md) |
| `coredoc` | shelf (adopted) | Create, audit, and maintain a professional external-facing documentation set (README, docs/*, architecture diagrams, llms.txt/llms-full.txt) kept faithful to the code. | [registry/skills/coredoc](../registry/skills/coredoc/SKILL.md) |
| `backlog` | shelf (adopted) | Create, audit, and maintain a file-backed engineering backlog (planned/proposed/completed/deprecated/recurrent) with lifecycle states and hygiene. | [registry/skills/backlog](../registry/skills/backlog/SKILL.md) |
| `architect` | shelf (adopted) | Force rigorous architecture exploration before settling: independent charters, steelmanned alternatives, comparison matrix — now with premise verification + the engraving gate. | [registry/skills/architect](../registry/skills/architect/SKILL.md) |
| `adr` | shelf (adopted) | Create, audit, and enforce ADRs as durable cross-task policy (Context/Decision first; Enforcement + Validation mandatory); pairs with `backlog`. | [registry/skills/adr](../registry/skills/adr/SKILL.md) |
| `cicd` | shelf (adopted) | GitHub-based CI/CD: least-privilege workflows, OIDC trusted publishing, docs deployment, release rehearsals, maintenance playbook. | [registry/skills/cicd](../registry/skills/cicd/SKILL.md) |
| `review` | shelf (adopted) | Independent evidence-based ship-readiness reviews (correctness / architecture-fit / user-and-operations lenses; Blocking/Conditional/Approved). | [registry/skills/review](../registry/skills/review/SKILL.md) |
| `uxreview` | shelf (adopted) | Human UX reviews with independent naive/intermediate/expert personas over live UI evidence; code-only review caps the verdict. | [registry/skills/uxreview](../registry/skills/uxreview/SKILL.md) |
| `verification-before-completion` | shelf (adopted) ⚠ content caveat | Evidence before claims: run the verification commands and read the output before any completion claim. Entity-lane hold until the 0003 audit. | [obra/superpowers @ d884ae0](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/verification-before-completion) |
| `test-driven-development` | catalog (vendorable) | Write a failing test before any implementation code, make it pass, then refactor — "test after" is grounds to restart. | [obra/superpowers @ d884ae0](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/test-driven-development) |
| `writing-plans` | catalog (vendorable) | Implementation plans detailed enough to execute without guessing: small tasks, named files, tests first. | [obra/superpowers @ d884ae0](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/writing-plans) |
| `systematic-debugging` | catalog (vendorable, scripts → review) | Four-phase root-cause process — investigate, pattern analysis, hypothesis testing, then implementation; never fix what you have not understood. | [obra/superpowers @ d884ae0](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/systematic-debugging) |
| `vercel-react-best-practices` | catalog (vendorable) | 70 impact-prioritized React/Next.js performance rules (waterfalls, bundle size, rendering) for our React UIs. | [vercel-labs/agent-skills @ f8a72b9](https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/react-best-practices) |
| `owasp-security` | catalog (vendorable) | OWASP Top 10:2025 + ASVS 5.0 + LLM/agentic-AI review checklists with per-language unsafe/safe pattern examples. | [agamm/claude-code-owasp @ f5dfa3d](https://github.com/agamm/claude-code-owasp/tree/f5dfa3d66da1fdfeb36b7428c35b17abaff6465b/.claude/skills/owasp-security) |
| `skill-creator` | catalog (vendorable, scripts → review) | Create, improve, and evaluate agent skills (authoring patterns, eval design, description optimization). | [anthropics/skills @ 9d2f1ae](https://github.com/anthropics/skills/tree/9d2f1ae187231d8199c64b5b762e1bdf2244733d/skills/skill-creator) |
| `mcp-builder` | catalog (vendorable, scripts → review) | Guide for building high-quality MCP servers (tool design, Python FastMCP + TypeScript SDK, evaluation). | [anthropics/skills @ 9d2f1ae](https://github.com/anthropics/skills/tree/9d2f1ae187231d8199c64b5b762e1bdf2244733d/skills/mcp-builder) |
| `web-design-guidelines` | watch (PULLED — time-of-use fetch) | 100+ UI review rules upstream, but the pinned body fetches unpinned rules at use time; re-scope before any vendor. | [vercel-labs/agent-skills @ f8a72b9](https://github.com/vercel-labs/agent-skills/tree/f8a72b9603728bb92a217a879b7e62e43ad76c81/skills/web-design-guidelines) |
| `brainstorming` | watch (demoted) | Socratic design refinement before code; interactive-session shaped, overlaps the operator's architect skill. | [obra/superpowers @ d884ae0](https://github.com/obra/superpowers/tree/d884ae04edebef577e82ff7c4e143debd0bbec99/skills/brainstorming) |

## Why curated-only

The 2026 skill ecosystem measures badly: Snyk's ToxicSkills audit found 36.8%
of 3,984 registry skills flawed, 13.4% critical; a 98,380-skill behavioral
study confirmed 157 malicious; the AIR incident shipped a post-approval URL
swap to ~26,000 agents THROUGH three scanners (all figures with their
references in [`registry/guidance.yaml`](../registry/guidance.yaml)). The
ecosystem's standard installer (`npx skills add`) symlinks trees with no
hash pinning, and its own documentation tells users to treat skills as
unverified code and read them before installing. Curation, commit pins,
whole-tree hashes, and a fail-closed trust gate are the response — not
because they certify safety (nothing does; see
[What curation does NOT guarantee](#what-curation-does-not-guarantee)) but
because they make every admission a reviewed, reproducible, revocable act.

A finding from this catalog's own adversarial review, now a standing
curation rule: **a skill body that instructs fetching external instructions
at use time is a time-of-use fetch — pinning its tree pins a pointer, not
the rules; it can never be risk-labeled `low` and must carry an explicit
note.** (`web-design-guidelines` was pulled from the vendorable list for
exactly this; see the watch tier.)

## Top curated skills (vendorable now)

All entries are pinned in `registry/catalog.yaml`. Risk is the curator's
reviewed classification (`low` = text-only reviewed content; `moderate` =
scripts present or comparable surface; `risky` = requires capabilities the
gate withholds); the structural facts win at the gate regardless
(scripts-present ⇒ `requires_review`, whatever the label says). Archetypes:
`knowledge` = reference material; `procedure` = a working method the agent
follows; `meta` = skills about skills. License text travels with every
vendored copy (out-of-tree at `registry/licenses/<name>.LICENSE`, so the
pinned tree hash covers only upstream bytes).

### Engineering process — `obra/superpowers` (MIT, ~251k stars as of 2026-07-11; "shipped as an Anthropic marketplace plugin in early 2026" per the cited blog)

CONCENTRATION, stated as an accepted risk: 4 of the 8 vendorable entries
share this one source. One compromised maintainer account poisons half the
list at the next re-pin — mitigations: pins never auto-follow, every re-pin
is a fresh review, and a cross-reference inventory (superpowers skills
reference sibling skills that are NOT on our shelf — dangling references are
squatting surfaces) runs before any re-pin.

| Skill | Risk | What it improves here |
|---|---|---|
| `test-driven-development` | low | Red/green/refactor discipline for package work; "test after" is grounds to restart. |
| `writing-plans` | low | Small verifiable tasks, files and tests named before code; complements the vendored `backlog` skill. |
| `verification-before-completion` | low | Evidence before claims — the anti-self-declared-success rule made procedural. **Vendored** (the catalog's first live entry). CONTENT CAVEAT: its "Why This Matters" section carries identity-adjacent framing ("If you lie, you'll be replaced"; second-person failure memories) — fine for developer agents, **not for entity sessions** before the 0003 audit rules on it; the caveat travels in the validation record. |
| `systematic-debugging` | moderate | Four-phase root-cause process that forbids fixing what is not understood. Ships one helper script → `requires_review`. |

### Frontend/UI — `vercel-labs/agent-skills` (MIT, Vercel Engineering)

| Skill | Risk | What it improves here |
|---|---|---|
| `vercel-react-best-practices` | low | 70 rules at the pin (the cited blog describes an earlier 40+ snapshot), impact-prioritized React/Next.js performance guidance for our React UIs. Next.js-heavy — a portion won't apply to our Vite apps; the React/JS rules do. Note: upstream dir is `react-best-practices`; the frontmatter name (the shelf key) is `vercel-react-best-practices`. |

### Security — `agamm/claude-code-owasp` (MIT)

| Skill | Risk | What it improves here |
|---|---|---|
| `owasp-security` | low | OWASP Top 10:2025 + ASVS 5.0 + LLM/Agentic top-10 checklists with per-language unsafe/safe pattern EXAMPLES (20+ languages at ~half a KB each — pointers, not depth). Single-author provenance: reviewed at the pin; re-review on every re-pin. Persuasive-content risk is invisible to `has_scripts` — a poisoned security checklist steers reviews wrong; that is exactly why re-pin review is mandatory. |

### Meta / integration — `anthropics/skills` (Apache-2.0, per-dir LICENSE.txt verified)

| Skill | Risk | What it improves here |
|---|---|---|
| `skill-creator` | moderate | Anthropic's skill authoring + eval methodology; feeds our first-party authoring and the 0003 behavioral-audit harness design. Python eval scripts present → `requires_review`. |
| `mcp-builder` | moderate | MCP server design guidance (FastMCP/TS SDK, tool design, evaluation) — we build and consume MCP integrations. Helper scripts present → `requires_review`. |

## Maintainer skills wave (operator directive, 2026-07-11 evening)

Five of the maintainer's own codex skills were evaluated and vendored
(source `codex-skills (maintainer)`, `first-party-adoption` → adopted, same
path as coredoc/backlog):

- **`architect`** — vendored WITH two upstream improvements first (operator
  asked for improvement based on this seat's findings): (1) an Evidence
  Contract rule — verify each load-bearing premise against the current
  tree/running state before arguing from it (premise decay is the most
  recurrent architecture failure in this workspace's record: the phantom
  run-store premise, stale-envelope answers, this catalog's own structural-
  not-content P0); (2) an "engraving" Architecture Gate + one-concept-one-name
  anti-pattern (names that reach append-only state are effectively
  irreversible — the phase-rename and personal_grant lessons). Two matching
  distilled principles landed in its `reviewer-memory.md`.
- **`adr`** — vendored as-is: complements the already-vendored `backlog`
  (the two texts cross-own their boundary explicitly), and most framework
  repos have no ADR system yet — this seat's own backlog notes the gap.
- **`cicd`** — vendored WITH upstream repairs first (its adversary found the
  copy-paste examples had rotted): the npm trusted-publishing job shipped
  broken (Node 22's bundled npm predates the ≥ 11.5.1 OIDC floor — silent
  no-handshake, confusing E404; now Node 24 + the floor stated), stale
  hardcoded action majors replaced with `<current-major>` placeholders + a
  version-policy line per reference (the node20 runner cutover would have
  hard-broken them by 2026-09), the build/publish artifact-name mismatch
  unified, `npm trust` gained the now-required `--allow-publish` + the
  11.10.0 floor, the audit checklist gained the two dominant Actions
  vulnerability classes (untrusted `${{ github.event.* }}` interpolation;
  `pull_request_target` misuse) + SHA-pinning of third-party actions, and an
  unused `attestations: write` permission was dropped (least-privilege).
  Note: references the `release` skill, which is NOT on the shelf (dangling
  cross-skill references are inert in our loader; they are also squatting
  surfaces, so they are inventoried — the `references_skills` admission item
  queued in the trust backlog). Its adversary's fleet-consistency suggestion
  (reusable `workflow_call` shapes + cross-repo drift audit) is recorded as
  an upstream candidate.
- **`review` + `uxreview`** — EVALUATED: keep BOTH, separate, as-is (verdict
  argued below).

### review / uxreview: as-is, improved, or merged?

**Keep both, separate.** They occupy different phases and compose by
explicit contract rather than overlapping:

- `adversarial-iteration` (first-party) is FORMATIVE — the improvement loop
  DURING work (attack, fold, iterate).
- `review` is SUMMATIVE — the final ship-readiness gate (Blocking /
  Conditional Approval / Approved), with an evidence cap (uninspectable
  artifact ⇒ at best Conditional).
- `uxreview` is the SPECIALIST persona swarm (naive/intermediate/expert;
  live UI evidence preferred, code-only review caps the verdict at
  Conditional) — and `review`'s own text already delegates to it ("uxreview
  owns specialist human-usable verdicts") while `uxreview` refuses to be
  silently replaced.
- Why NOT merge (the load-bearing reasons, adversary-sharpened): a merged
  skill would FORK the maintainer's upstream — the re-vendor path and
  `codex-skills (maintainer)` provenance die and maintenance transfers to
  this seat; and activation precision is lost — the two descriptions trigger
  on disjoint task shapes, so a merged body pays uxreview's persona charters
  on every pure-backend review and vice versa. (A merged body COULD keep the
  persona-independence text as a section — that alone would not have decided
  it.)
- Framework interest is HIGH for both: three user-facing apps (abstractflow,
  abstractobserver, abstractassistant) plus the shared UI kit (abstractuic)
  get a repeatable UX gate; the room's review culture gets ship-verdict
  vocabulary distinct from the formative loop — and `adversarial-iteration`
  now carries the composition note in its own body (formative loop → review
  owns ship-readiness; explicit-request idiom translated), so the system
  contract reaches consumers at activation time, not just in this document.
- Considered and rejected: extracting the shared reviewer machinery
  (fallback rules, output-format scaffolding, reviewer-memory pattern) into a
  common reference. Skills are independently vendorable trees — a shared
  dependency would be unreachable (`read_skill_resource` refuses paths
  outside the tree) and unpinned (`hash_skill_tree` covers only the skill
  dir); duplication across independently distributable skills is the right
  trade.
- Field-memory caveat (all three reviewer skills ship a
  `references/reviewer-memory.md` that says "update it during
  skill-maintenance work"): on THIS shelf those are byte-frozen vendored
  copies — updates happen UPSTREAM, then re-vendor + re-pin; never edit the
  vendored tree (the byte pins in `scripts/refresh_shelf.py` now refuse
  exactly that).

## Watch tier (not yet catalog-pinned)

- **`web-design-guidelines`** (vercel-labs, PULLED from the top list —
  adversary finding, P0): at the pinned commit the body is a time-of-use
  fetch stub ("fetch fresh guidelines before each review" from
  `web-interface-guidelines@main`) — the tree hash pins a pointer, not
  rules. Re-scope path: pin `vercel-labs/web-interface-guidelines` at a
  commit and vendor the actual rules document (license check first).
- **`brainstorming`** (obra/superpowers, demoted): thinnest improves case;
  interactive-session shaped (ships a local visual-companion server); the
  operator already runs an `architect` skill covering pre-code design
  exploration.
- **Python-lane candidates (named gap)**: the framework is Python-dominant
  (five packages, FastAPI, pytest-heavy) and the catalog currently gives
  Python nothing. Research targets: pytest discipline packs, FastAPI/API
  design guidance, and superpowers `requesting-code-review` /
  `receiving-code-review` for the adversarial-review culture — noting the
  latter deepen the single-source concentration.
- **Trail of Bits skills** (`trailofbits/skills`, CC-BY-SA-4.0):
  `differential-review`, `audit-context-building` are procedure packs aligned
  with our adversarial process; most others run scanners. Plugin-shaped
  layout needs per-skill path verification before pinning; share-alike
  license noted.
- **`hashicorp/agent-skills`** (MPL-2.0): `terraform-style-guide` is a clean
  knowledge pack — admit when the framework actually touches IaC.
- **`anthropics/skills` extras**: `frontend-design` (aesthetic direction —
  NOTE: its per-dir LICENSE.txt differs from the Apache text in
  skill-creator/mcp-builder; verify before pinning) and `doc-coauthoring` —
  candidates after the first wave proves the usage loop.

## Excluded (with reasons on the record)

- **Anthropic document skills** (`docx`/`pdf`/`pptx`/`xlsx`): source-available
  (NOT open source — redistribution unclear for vendored byte-copies) and
  script-execution-dependent; decorative without script enablement.
- **`webapp-testing`**: requires browser + script execution; the gate
  deliberately withholds both today.
- **Deep-research packs** (8-phase research pipelines, scholar tools):
  network + scripts by design; admit only when script/network enablement
  exists so they are not decorative.
- **Aggregators** (`VoltAgent/awesome-agent-skills` and similar): discovery
  surfaces, not vendoring sources — every admission pins the ORIGINAL
  author's repo. An aggregator in the middle is a supply-chain hop that adds
  nothing but risk.

## Adding a curated skill

```
# 1. list what the catalog offers
python scripts/vendor_skill.py --list

# 2. vendor a pinned entry (fetches the exact commit, validates, hashes)
python scripts/vendor_skill.py <name>

# 3. review the vendored diff, then pin it in registry/catalog.yaml
#    (expected_tree_hash + vendored: true — printed by step 2)

# 4. regenerate the trust registry (validation records derive from the catalog)
python scripts/refresh_shelf.py

# 5. update the admission pins in tests/test_shelf.py — EXPECTED_SHELF,
#    EXPECTED_LEVELS, EXPECTED_SOURCES (and EXPECTED_SCRIPTS_BEARING for a
#    scripts-bearing skill). The pins are the review's second signature:
#    a red suite here is the gate asking for your deliberate sign-off.
python -m pytest -q
```

Never add a `SHELF_POLICY` entry for a catalog skill — the validation record
derives from the catalog entry, and `refresh_shelf.py` refuses the collision
(a hand-written policy would silently drop the byte-pin cross-check).

The vendor script refuses: names not in the catalog (curated-only is
structural), symlinked upstream trees, frontmatter/catalog name mismatches,
spec-invalid skills, and — after first pinning — any byte drift from
`expected_tree_hash`. Git runs with ambient config neutralized (no user
hooks/filters can act during fetch), and VCS/OS-junk files never reach the
shelf (the copy set equals the hash set). New skills enter as
`manual-review` → `adopted` (the method caps the level; `audited` requires
the 0003 behavioral harness).

Trust floor, stated honestly: the FIRST vendoring of an entry trusts git's
commit-hash verification (SHA-1DC) plus the curator's human diff review — the
SHA-256 whole-tree pin exists only from that point on. Every re-vendor is
then byte-verified end to end.
Scripts-bearing skills surface as `requires_review` at
`select_skills_for_context` until an operator explicitly enables them —
enablement is the approval act, and script EXECUTION additionally requires
a tool grant that simply does not exist today.

## What curation does NOT guarantee

A catalog entry attests that a named reviewer read the tree at a pinned
commit and recorded why it helps this framework. It does not certify the
skill is benign (semantic evasion beats any review), does not cover upstream
behavior outside the pinned bytes, and says nothing about conditional
triggers a reading cannot see. The trust ladder's honest-limits contract
travels with every badge: never render the word "safe" (the risk column
deliberately says `low`, not `safe`, for the same reason).

Independence disclosure: at v1, curation, vendoring, and validation are the
same seat's single review (`validated_by: skill`) — the method cap makes
"reviewed ≠ audited" structural, and independent signal arrives with the
0003 behavioral-audit harness and external-audit records.
