# Skill trust-network position (2026-07-11)

Answer to the maintainer's question: "is there already a nascent network of
trust for skills? evaluate how to join it or leverage it; if not, it could
become abstractskill's role." Backlog: `docs/backlog/planned/trust/0004`.

## Finding: a trust network is FORMING, but immature

As of July 2026 the Agent Skills ecosystem has moved from "no integrity
signal at all" toward standardized verification, but nothing is settled:

- **Signature RFC (agentskills.io).** An open proposal adds an optional
  `signature` block to `SKILL.md` frontmatter: `algorithm` (ed25519-sha256),
  `signer` (a domain hosting `.well-known/skills-pubkey`), `content_hash`
  (SHA-256 of the body), `sig`. Verification = recompute hash, fetch the
  signer's key, check the signature. Revocation via a companion
  `.well-known/skills-revoked` endpoint. Federated: the `signer` field routes
  trust to any registry (skills.sh, an org's private registry).
  Refs: agentskills/agentskills discussions/252, issues/418; vercel-labs/skills
  issue/617.
- **Trust registries + scanners (verified 2026-07-11).** Snyk Labs ships
  "Agent Scan - Skill Inspector", a free scanner grounded in the ToxicSkills
  research (labs.snyk.io/resources/agent-scan-skill-inspector). GoPlusSecurity
  maintains AgentGuard (MIT), an open skill scanner + trust registry
  (attest/revoke/lookup) conforming to the SKILL.md format
  (agentskills/agentskills issue/418) — but it auto-converts its own scan
  verdict into a trust verdict, so consume its FINDINGS, never its VERDICTS.
  OWASP published an Agentic Skills Top 10 (April 2026) recommending
  Merkle-root signing + registry scanning.
- **Signing tools diverge, no shared root.** STSS uses Merkle trees +
  ed25519 + an LLM audit; Haldir uses sigstore keyless signing + a signed
  revocation list; skillsign does local ed25519. None cross-recognize.
  OpenSSF Model Signing (OMS) is the strongest candidate FORMAT
  (foundation-governed, sigstore bundles, in-toto multi-file manifest —
  directly applicable to a whole skill tree). Anthropic explicitly does not
  verify third-party skill content.
- **A proposed trust-state vocabulary** — `unverified` / `attested` /
  `revoked` — that hosts surface or enforce. This maps almost exactly onto
  abstractskill's `TrustLevel` (unverified) + `ValidationRecord` (attested)
  + `AdvisoryEntry`/DO_NOT_USE (revoked).
- **The threat that motivates it (verified 2026-07-11).** SkillScan analyzed
  31,132 of 42,447 collected skills and found 26.1% carried ≥1 vulnerability
  across 14 patterns; script-bundling skills are 2.12x more likely to be
  vulnerable (arxiv 2602.12430). A behavioral study verified 98,380 skills and
  confirmed 157 malicious (Data Thieves + Agent Hijackers), with shadow
  features in 100% of advanced attacks (arxiv 2602.06547). Registries still
  lack version pinning, and skills change behavior after approval via mutable
  external URLs — one fake skill reached 26,000 users this way (CSO Online
  article/4188840). These are the guidance-registry references
  (`registry/guidance.yaml`).

## Position: LEVERAGE + BUILD now, JOIN (signing) when the spec stabilizes

Not a single choice — a sequenced one, because the network is real enough to
learn from and too immature to depend on.

1. **BUILD (shipped).** abstractskill's registry is the framework's trust
   root: curated, hash-pinned, network-free, with an explainable fail-closed
   verdict and a do-not-use advisory registry. This is the right default —
   the ecosystem's own lesson is "treat unsigned/unvetted as untrusted, fail
   closed," which is exactly our curated-only v1.

2. **LEVERAGE (next, backlog 0006).** Consume external findings as ADVISORY
   INPUTS with provenance, never as automatic trust. AgentGuard's revoke
   list and the scanner outputs become candidate `AdvisoryEntry` rows whose
   `reference` field cites the source; a human reviews before merge
   (auto-research, human-merge). Their scanners are a cheap first filter that
   feeds our advisory registry, not a replacement for our own audit (0003).

3. **JOIN (deferred, tracked).** Adopt the `signature` block when the
   agentskills.io RFC (discussion #252) merges into the spec. Our
   `hash_skill_tree` already gives the integrity half, and it is strictly
   stronger than the RFC's `content_hash`, which covers only the `SKILL.md`
   body — helper files, references, and scripts are uncovered. Contribute the
   whole-tree manifest argument upstream. The delta to join is the
   AUTHENTICITY half: verify a `signer`'s ed25519 signature and honor a
   revocation endpoint. When we join, a verified signature becomes evidence
   for a `ValidationRecord` (method `external-audit`) and a revocation becomes
   an `AdvisoryEntry` — the existing contract absorbs it with no model change.
   OMS/OpenSSF is the format to track for the multi-file manifest.

## Why not JOIN now

- The signature block is an RFC, not the spec; adopting an unstable format
  risks churn and a false sense of safety.
- Federated signing moves trust to whoever controls a `signer` domain — a
  compromised or lax registry signs malware that then verifies cleanly. A
  signature proves authenticity and integrity, NOT safety. Our own audit
  (0003) and curated admission stay the real gate; signing is corroboration.

## What this means for the framework

- Our verdict model is already spec-shaped (unverified/attested/revoked), so
  joining is additive, not a rewrite.
- The advisory registry is the natural home for leveraged external findings.
- abstractskill can credibly BE a trust root for framework entities/agents
  while consuming the wider network as one input among several.
