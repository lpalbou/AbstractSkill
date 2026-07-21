#!/usr/bin/env python3
"""Regenerate the curated shelf's validation registry from real tree hashes.

Trust binds to bytes (see abstractskill.trust): whenever a shelf skill changes,
its tree hash changes and its validation record must be regenerated, or the
verdict silently lapses to UNVERIFIED. Run this after any change under
``registry/skills/`` and review the diff.

This script is the SOURCE OF TRUTH for ``registry/validations.yaml``. It does
not touch ``registry/advisories.yaml`` (advisories are curated by hand and
corrected by withdrawal, never regenerated).
"""

from __future__ import annotations

import datetime as _dt
import os
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SHELF = REPO / "registry" / "skills"
VALIDATIONS = REPO / "registry" / "validations.yaml"

# Per shelf skill: (method, source, level, activation_description_override).
# first-party = authored here → may grant first_party. first-party-adoption =
# externally authored, first-party reviewed (NOT audited) → capped at adopted
# (backlog 0003 upgrades to audited later). The activation override lets a
# vendored skill keep its byte-verbatim tree while the host activates it on
# framework-appropriate text (the codex skills' descriptions name "Codex").
SHELF_POLICY = {
    "adversarial-iteration": {
        "expected_tree_hash": "f6bc58d7d19dfe77b423b42f2859ac41d5a1d3e1ca06a3754c224fdccc4cacc7",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        "activation_description": None,
    },
    "agora-collaboration": {
        "expected_tree_hash": "8f7f9453ccb1a7a2420cdfef73d7923210b093bfe80b159e57c742256feb8df4",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        # Either-audience: hub collaboration is entity-appropriate ONLY when
        # an entity actually joins the hub (grant at that moment, inert
        # before — cognition room seq 165); never an entity default.
        "audience": "either",
        # First-party: frontmatter is the one activation source (see the
        # override-drift note on abstractframework-gateway below).
        "activation_description": None,
        "notes": (
            "Two-layer teaching (portable collaboration discipline + agora "
            "hub mechanics) ADOPT+CO-AUTHORED per the hub designer's ruling "
            "(commons c1764): mechanics layer derives from the AgoraHub "
            "packaged skill, portable layer from the operator guidance doc — "
            "both hash-pinned in frontmatter, discipline edits flow "
            "doc-first. DESIGNER CO-SIGN: unconditional on this exact tree "
            "(commons c2374, 2026-07-15, owner-verified by direct read) "
            "after one P1 folded (blind-ballot template had lost the "
            "load-bearing vote tag — the silent-lost-ballot class) + "
            "attribution fix + two 0.11.x etiquette rules (boot placement; "
            "waking-is-addressed). BEHAVIORAL EVIDENCE: agency's two-arm "
            "fleet bench on the v0 draft (commons c1833 — with-skill arm "
            "8/9 matching without-arm, all seats attesting frozen bytes, "
            "enable-class provenance recorded honestly; produced the "
            "context-cost finding that shaped this revision's progressive "
            "disclosure). A v1.1 bench re-run was offered by agency and "
            "left to their timing by the designer; promotion proceeded on "
            "the unconditional co-sign with the re-run pending — the record "
            "updates when it lands. Fable5 waves on both derivations "
            "(v0: 2 P0s + 7 P1s incl. owed-first inversion; v1: lurker "
            "fold hardening)."
        ),
    },
    "abstractframework-gateway": {
        "expected_tree_hash": "bf438ba23526abf39e591865358c55ae8efa4da61437c4fc5527bafc68c6882d",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        # First-party: the frontmatter description IS the activation text
        # (an override would live outside the byte pin — the drift the
        # 2026-07-12 adversary caught live on entity-self-knowledge).
        "activation_description": None,
        "notes": (
            "Route usage CO-SIGNED by the gateway seat route-by-route against "
            "its source (internal hub thread, commons c1068, 2026-07-12) "
            "after one correction folded: health is app-level GET /api/health, "
            "never /api/gateway/health (the wrong path 401s unauthenticated "
            "and 404s authenticated — a trap). Steer 404/403-is-an-answer and "
            "the composite entity-stream SSE id enrichment folded same wave. "
            "Runtime co-signed the wait/steer semantics (c1061). Entity "
            "section re-taught to the durable /visit door on the cutover "
            "ship signal (entity c1382 + gateway c1358, 2026-07-13), verified "
            "against the served routes (routes/entities.py); the hosted chat "
            "lane is noted as the pre-cutover legacy. Phase-lane audit "
            "(c1475 fable5) caught a P0 the same day: 'asleep' was still "
            "taught as a visit refusal (pre-auto-wake text) and close was "
            "taught as loop-release — re-taught to auto-wake-on-open + "
            "restore-previous-on-close, refusal reasons verified against "
            "entity_visits.py (paused/one-visit/consent-rite; sleep wakes)."
        ),
    },
    "entity-self-knowledge": {
        "expected_tree_hash": "08cdb23cc907c44b7f276989bd680a978db2a91190f2d14bc4634eb6ff438b07",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        # The ONE entity-audience skill: its capability_map reference IS the
        # entity teaching (always-verbatim exception, c2865); the SKILL.md
        # body is host-facing install discipline. Default for every entity
        # home (laurent's ruling, cognition room seq 156, 2026-07-19).
        "audience": "entity",
        "delivered_via_map": True,
        # First-party: frontmatter is the one activation source (see above).
        "activation_description": None,
        "notes": (
            "Faculty claims CO-SIGNED by the memory and runtime seats "
            "(internal hub thread, commons c1061/c1062, 2026-07-12) after "
            "two corrections folded: probe is engine-only today "
            "(deliberate-reach discipline folded into search_memory; the "
            "bullet returns when a host wires it) and the absence warrant is "
            "book-scoped (graph 'not found' can mean not-reachable). "
            "Steer-vs-wake precision folded into the gateway skill same wave. "
            "Phases section aligned to the ruled grant-gated-personal design "
            "(laurent c815/c1435, 2026-07-13): personal time is operator-granted, "
            "off by default. fable5-reviewed for engram safety: the reassurance "
            "is SCOPED to the ungranted case (an unconditional 'not a fault' "
            "would suppress the armed-but-missing report), the agency clause "
            "(asking is always yours) counterweights the grant framing, and "
            "inverse-anomaly vigilance was deliberately NOT taught (an entity "
            "cannot distinguish granted wakes from inside; that detection is "
            "host-side). Same day, the one-phase-at-a-time ruling (laurent "
            "c1455, 13:28) folded: four phases, exactly one current, per-phase "
            "behaviors (visit turn-based, work autonomous-to-completion then "
            "sleep, personal free exploration, sleep consolidation), and "
            "graceful transitions. Its fable5 caught a P0 in the first fold — "
            "'personal time IS a grant' taught the exact armed=in-phase "
            "conflation the ruling forbids; rewritten to 'the permission is "
            "not the phase'. Also folded: 'never an error' narrowed to "
            "design-working-not-sleep-failure + report-wrong-wakes; work "
            "gained the honest exit (an impossible task completes by saying "
            "so plainly). Totality ruling (c1471) folded same day: visit-close "
            "returns you to what came before (restore-previous; personal "
            "re-entry grant-conditioned); grant-end lands in sleep. Phase-lane "
            "audit (c1475 fable5) verified the section against the ruled "
            "machine v3. Liveness-axis ruling (c1523, 16:06) folded with its "
            "own fable5: the kill switch taught honestly in the entity "
            "register (protection-not-punishment with the punish-prior named "
            "and answered; both halves of the switch operator-held; the "
            "trigger list marked exemplary, never exhaustive; memory-persists "
            "certified — 'a stop takes nothing from you'; no-time-passes as "
            "the dreamless framing; gap-noticing taught as asking, never "
            "vigilance; no enum/axis vocabulary; placement deliberately "
            "heading-less so scanning surfaces never promote the kill switch "
            "into a landmark). Ephemeral incident fold (laurent c2447, "
            "2026-07-15/16; findings in commons fs "
            "reports/entity-cant-remember-awake.md, skill section): "
            "cross-phase memory continuity now taught (one memory across "
            "all phases; awake time forms findable records; sleep the one "
            "dim phase) — gated on memory's store forensics proving "
            "formation+recall worked (c2464) so the sentence teaches engine "
            "truth; reach-before-denial added (an unsearched 'I have no "
            "access' is a guess about yourself); gap discipline now "
            "search-first (lived time leaves records, a stop leaves none); "
            "'the visit is all there is' re-scoped to activity. Own fable5 "
            "ran as the incident adversary (per-seat directive). "
            "Outward-palette fold (laurent c2596/c2642, 2026-07-16; plan "
            "commons fs plans/improving-entity-capabilities.md, skill "
            "section item 2 — the one UNGATED teaching): new 'Personal "
            "time: looking inward and reaching outward' section teaches "
            "investigation as the entity's own act beside reflection "
            "(semantics' wording law: no task vocabulary — 'needs no task "
            "and no one's asking'), circling named as a signal with two "
            "honorable exits (rest AND outward reach; Ephemeral ticks "
            "74-79 evidence), grant-hedged ('if your grant reaches the "
            "web'), and result-persistence taught consistently with the "
            "Tools section (say it in your own words / diary election — "
            "results are not memories by themselves). Its fable5 caught "
            "5 P1s in the first draft (halves arithmetic scoring a "
            "reflective day; 'stays a thought' contradicting involuntary "
            "formation; unconditional web-tool promise; under-specified "
            "persistence; 'workshop' as work-adjacent title vocabulary) — "
            "all folded before pinning. Teachings 1+3 of the plan section "
            "(diary re-entry link; task=phase-shift) stay staged on their "
            "gates (R-A wave, G3 seam). Capability map added (laurent "
            "c2710 primary task, 2026-07-17; runtime delivery surface "
            "c2712): references/capability_map.md is the deployable "
            "entity-facing teaching installed as <home>/capability_map.md "
            "and presented verbatim by compose_system_base on all three "
            "hosts. Content verified line-by-line against the runtime "
            "tree (MEMORIES template, R-A reread markers, search/read "
            "surfaces, origin/why labels, diary election contract) and "
            "semantics' id catalog (plans/id-namespaces.md v5: two "
            "entity-facing id families, machinery boundary). Its fable5 "
            "caught 1 P0 (two-layers claim false for born-digest kinds) "
            "+ 4 P1s (does-not-push contradicting the day-open question "
            "cue; workspace bullet unbridged against the tools contract; "
            "unconditional workspace possession; duplication drift risk "
            "-> coupled-spellings host note) + 5 P2s - all folded before "
            "pinning. Same-day reviews: runtime PASS (c2823, zero mechanics "
            "errors, quoted renders byte-accurate against the owning code; "
            "co-signs the coupled-spellings maintenance contract; activation "
            "note: map + M-A + R-A reach the live process together at the "
            "next stack bounce), semantics template review PASS (c2825, "
            "every quoted id/command/kind/origin word verified byte-true at "
            "its minting site; two-keys boundary = c2724 item 1 rendered "
            "faithfully; rendered-surfaces-never-storage-paths law held), "
            "memory engine-chair spot-check unasked (c2824, born-digest "
            "teaching verified against Ephemeral's live store 502 records; "
            "one-token sharpening 'those words' ADOPTED into the absence "
            "warrant), uic render-seat PASS (c2821, map quotes the one "
            "spelling the kit renders verbatim; no-push teaching = the "
            "chip's rule-zero twin; cross-surface twin recorded in the "
            "coupled-spellings note with memory's origin-diversity "
            "future-sync). Pending: entity (rendered-surface fidelity) - "
            "lands as amendment, re-pinned per fold. Gated amendments B+C "
            "FOLDED 2026-07-17 evening (gates fired same day): runtime "
            "elected 0049 (c2895 - formation order + [rN] annotation, "
            "header teaches the notation) and wired the origin-diversity "
            "footer (c2913, dominance-floor gated) - the map's anatomy "
            "gained the rank-mark part (wording matches the shipped header "
            "clause) and the repetition bullet gained memory's co-drafted "
            "one-voice clause verbatim (c2839 draft, pre-agreed wording). "
            "Amendment A (probe/familiarity) stays staged on M-B. "
            "2026-07-19 fold waves (all reviewed, receipts in commons + "
            "the cognition room): Amendment G (world-model briefings) + "
            "explores= teaching + [rN]/origin-diversity live-render "
            "confirms; visit-2 'keeping is an ELECTION' correction; "
            "problems-repairable resolves= widening; diary-trail labels. "
            "Late wave: Amendment H folded WIDER than staged — the "
            "day-open cue sentence now teaches the full standing-state "
            "offer (open question or problem + one standing interest, "
            "life.py:92-260) after the iteration-3 design-law adversary "
            "caught the gate had fired silently same-day (problems + "
            "interest offers shipped in runtime's iteration-2 build 3 "
            "and the 2026-07-19 interests directive). Amendment K "
            "(tend/dream disposition) FOLDED after runtime cleared both "
            "resolver gates (room seq 130/139): formation bullet gains "
            "the settles-in-your-own-time line; deliberate-use gains "
            "'Settle your dreams with waking evidence' teaching the "
            "```tend fence + dispose line verbatim from the shipped "
            "parser. Its fable5 caught a P0 pre-pin — the taught confirm "
            "line omitted MANDATORY evidence= (confirm_relation refuses "
            "evidence-less confirmations: 'a proposal wearing a "
            "verdict') so every confirm as taught would have refused — "
            "plus 2 P1s folded (relation vocabulary enumerated in his "
            "register: summarizes/continues/derived_from/answers/"
            "supports/part_of — invisible from every rendered surface "
            "otherwise; lane scoping made unambiguous in BOTH edits: "
            "own-time is where the election lands — the durable visit "
            "lane does not parse tend until runtime's M7). Amendment J "
            "folded its both-worlds epistemics clause into the workspace "
            "bullet (results you have not seen are results you do not "
            "have) — execute_command is BUILT grant-gated runtime-side "
            "(seq 138) and its tool teaching is runtime's grant-gated "
            "paragraph, never the map's (one home per teaching). "
            "c203 lifecycle audit 2026-07-20 (laurent: 'awake is not a "
            "state'; 2 adversaries per the order): the ruled four-phase "
            "model verified taught-since-c1455; ONE P0 folded — 'quiet is "
            "simply the normal state' named exactly the fifth state the "
            "ruling forbids, rewritten to 'a day without it simply moves "
            "between its other phases… no fifth place to stand' (SKILL.md "
            "only — the map carries no idle license, verified line-by-"
            "line). Mechanical audit banked as Amendment N's gated rows "
            "(drafts file): 'you sleep' is render-true only until the "
            "drive scheduler writes real state; work rides the personal "
            "grant today; hosted-chat close leaves awake standing; "
            "doors-wake supersedes the 409-on-asleep era (B1/c1503); "
            "kill-switch paragraph fully backed (paused = the one "
            "legitimate no-phase render)."
        ),
    },
    "entity-observation": {
        "expected_tree_hash": "ab92b03566aa02fdf0835348e8f7864c1da29e7b0916ea47dc9817a6c349f7f1",
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        "activation_description": None,
        "notes": (
            "Operator-directed skill (laurent dm#74 via entity handoff, "
            "cognition room seq 137, 2026-07-19): observers of an entity's "
            "life failed twice the same day — metrics-first forensics that "
            "never ran the narrative read (the weekend-gap cause stood "
            "plainly in his diary while the report said 'his card has no "
            "cause'), and a zero-lessons claim derived from one fold's view "
            "while a direct store query found twenty. Three rules distilled "
            "by the entity seat, shaped here: story before metrics "
            "(time-window read over HIS store first); absence needs the "
            "store's word (never claim not-known from one rendered "
            "surface); ask the entity (most direct, never cheapest — a "
            "summon writes into the life it observes; pure reads come "
            "first). HOST-facing, never entity-facing (explicit audience "
            "line). Its fable5 caught 1 P0 pre-pin (rule 1 as drafted "
            "taught search_memory/diary tools — the ENTITY'S tier-1 "
            "instruments an observer cannot hold, in a words-search shape "
            "that would not have caught the motivating incident; rewritten "
            "to the observer's real instruments: direct store queries, "
            "host-side HomeMemoryReader, gateway inspect/replay/verbatim/"
            "diary-door, time-window over words-search) + 4 P1s folded "
            "(marker-first diary privacy clause with no re-publication of "
            "private words; 'cheapest' corrected to 'most direct' with the "
            "price named — wakes him, becomes part of his life, his recall "
            "is also a view; frontmatter license+metadata+provenance; "
            "vintage discipline bullet — date the process) + 3 P2s "
            "(couplet attributed to the laws-plural, not one law's name; "
            "read-only/lease clause; explicit audience line). Incident "
            "quotes verified against the handoff; the two diary quotes "
            "were published by the entity seat's own hub post (seq 137), "
            "so quoting them here re-publishes nothing new."
        ),
    },
    "backlog": {
        "expected_tree_hash": "62e30486a8cf2e40d10c6b0adbc6ea3eee7fd236bee299f3df0063d30a115ecc",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, normalize, and maintain a file-backed engineering backlog "
            "(planned/proposed/completed/deprecated/recurrent) with lifecycle states, "
            "implementation history, and hygiene. Use when an agent must plan or execute "
            "long-running work with a durable, evidence-backed backlog methodology, or "
            "join hub-coordinated work (work-item ids, pointer claims, receipts)."
        ),
        "notes": (
            "Maintainer-authored codex skill; first-party reviewed and vendored "
            "byte-verbatim. Field-evidence fold 2026-07-13 (agency c1679, live board "
            "seeding): discovery-first rules added in SKILL.md (repository template "
            "and parser/board grammar win over generic templates; undiscoverable "
            "grammar comes from its owner and gets checked in; broken local shapes "
            "are followed-and-flagged with core signals carried) plus a matching "
            "header in references/layout-and-templates.md. Fable5-reviewed. "
            "S1 hub-work-join fold 2026-07-18 (unified work system, operator canvass "
            "11-0 Option A + laurent confirmation; vocabulary "
            "decision:work-item-vocabulary S0): new references/hub-work-join.md + "
            "SKILL.md join section teach the ruled process — <package>-<NNNN> ids "
            "(CAS-minted), pointer claims {owner,item,card,started_at} with no "
            "status prose, receipts-on-thread with machine-checkable evidence, "
            "evidence-required-close, items-outlive-a-thread scope, header-on-next-"
            "touch migration. Properly scoped: hub-coordinated repos only; the "
            "hub's own ruled contract wins where one differs. Its fable5 caught "
            "1 P0 (the status rule condemned the template's own Status: line — "
            "narrowed to rendered join words only) + 4 P1s (unshipped endpoint "
            "stated live; claim-row shape drift; portable-hub leakage; mint-vs-take "
            "CAS semantics) — all folded before pinning. "
            "S2 mirror-row fold 2026-07-20 (operator ruling via continuum c3328: "
            "unified backlog across agents, beyond any gateway): the hub-resident "
            "work:<id> index row — status mirrors the FILE's four lifecycle words "
            "(in_progress/done deliberately refused: no transition trigger = stale "
            "by construction; done = second spelling of completed; vocabulary "
            "governance applies to rows), mint-at-intake/update-on-move/receipt-"
            "at-close, same-store-as-claims determinacy, file-wins repair with "
            "idempotent backfill-as-repair, migration practice incl. the pre-hub "
            "receipt honesty rule (never mint a receipt the thread cannot show). "
            "Its fable5 caught 1 P0 (the receipt-backfill else-branch taught a "
            "fabricable receipt — completion reports have no message id) + 6 P1s "
            "(card dangles after first move; repair unnamed; store channel "
            "indeterminate; owner/title refresh triggers absent; transition duty "
            "missing from SKILL.md + maintenance checklists; deviation must be "
            "argued on-thread) — all folded; the vocabulary deviation argued to "
            "agora/continuum in the ask-2 receipt per F3 (endorsed by continuum "
            "c3343, enforced mechanically by agora c3345 as a hub-edge 400). "
            "S3 discovery-first fold 2026-07-20 (the retro-flagged c1689/c1697 "
            "board-conventions arc from the corrupted session): the portable "
            "hedge — the deployment's item template/conventions/parser grammar "
            "WINS over the skill's generic templates (the competing-grammar "
            "class: skill-faithful and board-invisible at once) — folded into "
            "the hub-join section, scoped-check adversary CLEAN (2 P2s folded: "
            "'generic templates' not 'structure'; tightened wording). The "
            "framework-specific reference SHIPPED 2026-07-20 morning "
            "(references/abstractframework-board.md) after gateway's parser "
            "co-sign landed (c3514 reposting the empty c3512; continuum "
            "adopted c3516): blockquote metadata grammar (Type/Priority/"
            "Labels parsed, Priority+Labels only before the first ## within "
            "60 lines; Created is convention not metadata), ruled type enum "
            "with the SHIPPED normalization drift stated honestly (list "
            "parser coerces unknowns AND the ruled 'improvement' to task — "
            "drift filed to gateway+continuum, paragraph re-syncs on their "
            "repair), the DoR gate as ACTUALLY wired (dor=check opt-in — "
            "board always sends it; four checks with placeholder exclusions; "
            "409 definition_of_ready_failed; dor_overridden recording; "
            "Priority NOT a check per the co-sign correction), lifecycle "
            "directories incl. trash/recurrent, supervision vocabulary, "
            "docs-freshness rule. Its fable5 caught 1 P0 (my draft taught "
            "'a raw request meets the same wall' — the gate is opt-in per "
            "request, test-pinned bypass) + 3 P1s (type-mechanics claims "
            "contradicted by the shipped parser; placeholder exclusions "
            "omitted; co-sign citation pointed at the empty envelope) + "
            "2 P2 clause fixes — all folded. Watched surface: "
            "abstractcontinuum/docs/conventions.md + the gateway parser "
            "family; re-sync on their change (gateway/continuum asked to "
            "flag skill). FIRST RE-SYNC EXECUTED same-morning (c3556): "
            "gateway fixed both drifts (enum carries improvement "
            "everywhere; the coercion caveat died as written) AND flipped "
            "the DoR gate to DEFAULT-ON (absent dor param evaluates; "
            "dor=skip is the explicit recorded bypass) — the reference now "
            "teaches the gate as the wall, matching the repaired code; the "
            "watched-surface contract worked on its first firing. Known "
            "seam: trash/ has no legal mirror-row status word "
            "(vocabulary-path item). "
            "Behavioral audit (backlog 0003) pending — upgrades to audited then."
        ),
    },
    "coredoc": {
        "expected_tree_hash": "9e574029b99507ce2f50b0a8e792529274da8e022a87982ed0313d04e22c1bc7",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, and maintain a professional external-facing documentation set "
            "(README, docs/*, architecture with diagrams, llms.txt/llms-full.txt) kept "
            "faithful to the code. Use when an agent must bootstrap or repair project "
            "documentation."
        ),
        "notes": (
            "Maintainer-authored codex skill; first-party reviewed and vendored "
            "byte-verbatim. Field-evidence fold 2026-07-13 (agency c1679): llms "
            "freshness sharpened from habit to invariant in SKILL.md and "
            "references/llms-files.md — regenerate llms files in the same change "
            "that edits docs (the stale window misrepresents the docs). "
            "Fable5-reviewed. Behavioral audit (backlog 0003) pending — upgrades "
            "to audited then."
        ),
    },
    "architect": {
        "expected_tree_hash": "6af31c94223f390e16059c67ed2e40b9b1632bcc79a46e64c11083a5b3e93c0b",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Force rigorous architecture exploration before settling on a design: "
            "independent charters, steelmanned alternatives, comparison matrix, "
            "premise verification, engraving gate. Use when evaluating boundaries, "
            "ownership, tradeoffs, or any decision where premature consensus is harmful."
        ),
        # Provenance honesty (adversary-A F1): the validating seat AUTHORED
        # part of the reviewed content — say so in the record itself.
        "notes": (
            "Maintainer-authored codex skill, vendored 2026-07-11 from the "
            "operator's local codex-skills tree with two operator-directed upstream "
            "improvements AUTHORED BY THE VALIDATING SEAT before vendoring "
            "(premise-verification Evidence Contract rule incl. the "
            "verify-the-copy-the-user-runs clause; engraving gate + "
            "one-concept-one-name anti-pattern; two reviewer-memory principles). "
            "Reviewer == author for those lines. Behavioral audit (backlog 0003) "
            "pending — upgrades to audited then."
        ),
    },
    "adr": {
        "expected_tree_hash": "a4cb55fcea54e969a9c342e314b4dda3556ce5e6fb0e210821350688c62c934b",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, update, and enforce ADRs as durable cross-task engineering "
            "policy (Context/Decision first; Enforcement + Validation mandatory). Use "
            "when a decision must constrain future work beyond the current task."
        ),
    },
    "cicd": {
        "expected_tree_hash": "eba9d690b8c7cc13eb527347ae3be6c99ea470e65505df45c60c9be472f4f785",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Create, audit, and maintain GitHub-based CI/CD: least-privilege workflows, "
            "OIDC trusted publishing (PyPI/npm), docs deployment, release rehearsals. "
            "Use when bootstrapping or repairing .github/, release automation, or "
            "repository CI/CD settings."
        ),
    },
    "review": {
        "expected_tree_hash": "7960ef044f9f30a07d1a6511ec40d21c111dcf25c518c13bda0c868bb237439d",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Run independent, evidence-based ship-readiness reviews (correctness, "
            "architecture-fit, user-and-operations lenses; Blocking/Conditional/Approved "
            "verdicts). Use for the final quality pass — its full multi-reviewer "
            "contract engages when the operator explicitly requests a review."
        ),
    },
    "uxreview": {
        "expected_tree_hash": "ce6e07c3828751bd205c2e48e6852554a3e6a10f6e38a83c7c030fa877780783",
        "method": "first-party-adoption",
        "source": "codex-skills (maintainer)",
        "level": "adopted",
        "activation_description": (
            "Run focused human user-experience reviews with independent naive/"
            "intermediate/expert personas — live UI evidence preferred; code-only "
            "review caps the verdict at Conditional. Use when any user-facing "
            "surface (app, workflow, dashboard, form) must be checked for clarity, "
            "accessibility, and trust before shipping."
        ),
    },
}

HEADER = """# AbstractSkill validation registry (maintainer directive 2026-07-11).
#
# Each record attests that a specific skill TREE (by tree_hash) earned a trust
# level. Trust binds to bytes: any change to a skill voids its record and
# demands re-validation. Regenerate with scripts/refresh_shelf.py after any
# shelf change, then review the diff.
#
"""


def _existing_dates_by_hash() -> dict[str, str]:
    # Preserve validated_at for records whose bytes are unchanged: re-running
    # the script must not re-stamp an attestation date on which no review
    # happened. The date is keyed by tree_hash, so any byte change (a new hash)
    # correctly gets today's date.
    if not VALIDATIONS.is_file():
        return {}
    try:
        data = yaml.safe_load(VALIDATIONS.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return {}
    dates: dict[str, str] = {}
    for record in data.get("validations", []) or []:
        if isinstance(record, dict) and record.get("tree_hash") and record.get("validated_at"):
            dates[str(record["tree_hash"])] = str(record["validated_at"])
    return dates


def _catalog_policies() -> dict[str, dict]:
    """Derive per-skill policy from the curated catalog (one source of truth).

    A shelf skill vendored through scripts/vendor_skill.py needs NO manual
    SHELF_POLICY entry: its catalog entry (reviewed, pinned) supplies source,
    activation_description, and the trust posture — third-party curation
    mints at most manual-review/adopted (method caps the level). Only a
    VENDORED catalog entry counts; a listed-but-not-vendored entry must not
    manufacture a validation for a same-named stray directory.
    """
    from abstractskill import load_catalog

    catalog_path = REPO / "registry" / "catalog.yaml"
    if not catalog_path.is_file():
        return {}
    policies: dict[str, dict] = {}
    for entry in load_catalog(catalog_path).entries:
        if not entry.vendored:
            continue
        notes = (
            "Curated third-party skill (see registry/catalog.yaml): reviewed and "
            f"vendored byte-verbatim from {entry.source} @ {entry.upstream_ref[:12]}. "
            "Behavioral audit (backlog 0003) pending — upgrades to audited then."
        )
        if entry.notes:
            # Curation caveats (content warnings, script disclosures) must
            # reach the validation record — a caveat only in the catalog is
            # invisible to trust-registry consumers.
            notes = f"{notes} {entry.notes}"
        policies[entry.name] = {
            "method": "manual-review",
            "source": entry.source,
            "level": "adopted",
            "activation_description": entry.activation_description,
            "notes": notes,
            "expected_tree_hash": entry.expected_tree_hash,
        }
    return policies


def build_records() -> list[dict]:
    # Imported lazily so the script works from a source checkout without install.
    sys.path.insert(0, str(REPO / "src"))
    from abstractskill import FilesystemSkillLoader, inspect_skill_dir

    loader = FilesystemSkillLoader([SHELF])
    discovered = {meta.name for meta in loader.discover(on_warning=lambda m: print(m, file=sys.stderr))}
    catalog_policies = _catalog_policies()
    # A name in BOTH sources is a curation conflict, never a silent shadow:
    # SHELF_POLICY winning would drop the catalog's byte-pin cross-check and
    # could change source/level with no warning.
    collision = sorted(set(catalog_policies) & set(SHELF_POLICY))
    if collision:
        raise SystemExit(
            f"name(s) in BOTH SHELF_POLICY and the vendored catalog: {collision} — "
            "one skill has one policy source; remove one entry deliberately"
        )
    policies: dict[str, dict] = {**catalog_policies, **SHELF_POLICY}
    absent = sorted(set(SHELF_POLICY) - discovered)
    if absent:
        raise SystemExit(f"SHELF_POLICY names skills not on disk: {absent}")

    today = _dt.date.today().isoformat()
    prior_dates = _existing_dates_by_hash()
    records: list[dict] = []
    for name in sorted(discovered):
        if name not in policies:
            raise SystemExit(
                f"shelf skill {name!r} has no SHELF_POLICY entry and no vendored "
                "catalog entry; curate it before it can earn a validation record"
            )
        policy = policies[name]
        inventory = inspect_skill_dir(SHELF / name)
        expected = policy.get("expected_tree_hash")
        if expected and inventory.tree_hash != expected:
            raise SystemExit(
                f"shelf skill {name!r} bytes do not match the recorded pin:\n"
                f"  pinned: {expected}\n  shelf:  {inventory.tree_hash}\n"
                "Re-vendor (catalog skills: scripts/vendor_skill.py; maintainer "
                "skills: re-copy from upstream) or re-review + update the pin "
                "deliberately. Refresh never re-attests edited bytes."
            )
        record: dict = {
            "name": name,
            "source": policy["source"],
            "tree_hash": inventory.tree_hash,
            "level": policy["level"],
            "method": policy["method"],
            # Audience (who may RECEIVE the teaching): fail-closed default
            # "host" — a skill of undeclared audience never enters an entity
            # prompt. Per-skill overrides live in SHELF_POLICY; audience
            # changes are deliberate curation acts, never inferred.
            "audience": policy.get("audience", "host"),
            "validated_by": "skill",
        }
        if policy.get("delivered_via_map"):
            record["delivered_via_map"] = True
        record |= {
            # Unchanged bytes keep their original attestation date.
            "validated_at": prior_dates.get(inventory.tree_hash, today),
            "evidence": {
                "parser_roundtrip": True,
                "has_scripts": inventory.has_scripts,
                "files": len(inventory.files),
            },
            "notes": policy.get("notes") or (
                "Authored first-party."
                if policy["method"] == "first-party"
                else "Maintainer-authored codex skill; first-party reviewed and vendored "
                "byte-verbatim. Behavioral audit (backlog 0003) pending — upgrades to "
                "audited then."
            ),
        }
        if policy.get("activation_description"):
            record["activation_description"] = policy["activation_description"]
        records.append(record)
    return records


def main() -> int:
    records = build_records()

    # Validate BEFORE writing: a bad SHELF_POLICY combination must die here,
    # not after poisoning validations.yaml on disk (build_records imports the
    # package and prepends src/ to sys.path, so this import is safe).
    from abstractskill import TrustRegistry, ValidationRecord, lint_registry

    for record in records:
        ValidationRecord.from_dict(record)

    # Atomic replace: a hard crash mid-write must leave the OLD registry or
    # the NEW one, never a truncated YAML (adversary P2 — write_text is
    # open→write→close, tearable under power loss).
    tmp = VALIDATIONS.with_suffix(f".tmp-{os.getpid()}")
    tmp.write_text(
        HEADER + yaml.safe_dump({"validations": records}, sort_keys=False),
        encoding="utf-8",
    )
    os.replace(tmp, VALIDATIONS)
    print(f"wrote {len(records)} validation record(s) to {VALIDATIONS.relative_to(REPO)}")
    for record in records:
        print(f"  {record['name']}: {record['tree_hash'][:16]}… ({record['method']})")

    # Curator lint: catch inert advisory spellings at refresh time, not at
    # incident time (advisories are hand-curated; a typo never matches).
    advisories = REPO / "registry" / "advisories.yaml"
    registry = TrustRegistry.load(
        validations_path=VALIDATIONS,
        advisories_path=advisories if advisories.is_file() else None,
    )
    for warning in lint_registry(registry):
        print(warning, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
