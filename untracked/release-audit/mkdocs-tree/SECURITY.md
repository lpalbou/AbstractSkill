# Security policy

## Reporting

Report suspected vulnerabilities in AbstractSkill, or a malicious skill you
believe should carry a do-not-use advisory, to the AbstractFramework
maintainer (contact@abstractcore.ai). Include the skill's source, its tree
hash (`hash_skill_tree`), the observed behavior, and a reference where the
problem can be understood.

## What AbstractSkill protects

- **Integrity.** `content_hash` and `hash_skill_tree` are byte-exact. The
  whole-tree hash uses a length-prefixed injective manifest, so a crafted
  filename cannot forge a collision, and any post-approval byte change is
  detected.
- **Containment.** `read_skill_resource` reads strictly inside a skill tree
  (traversal and symlink crossings are refused); tree hashing refuses
  symlinks.
- **Tool confinement.** `effective_tools` can only narrow the operator's tool
  grant; a skill can never widen it.
- **Explicit trust.** `evaluate_trust` is fail-closed — unknown, script-
  bearing, and advisory-flagged skills require review; only a validated,
  clean skill is `attachable` — and every verdict is explainable.

## What AbstractSkill does NOT guarantee

- Trust classification raises the bar; it does **not** certify a skill is
  safe. A validation attests that a review or audit occurred, not that the
  skill is provably benign.
- The behavioral audit (backlog 0003) catches classes of malicious behavior
  over epochs; semantic evasion can defeat any finite battery.
- A future signature (spec JOIN) proves authenticity and integrity, not
  safety.

Curation, behavioral audit, and the fail-closed default remain the real gate.
See the [trust model](docs/trust.md) and
[trust-network position](docs/trust-network-position.md).

## Handling skills safely

- Prefer the curated first-party shelf (`registry/skills/`) over marketplace
  skills; the ecosystem's measured malware rates make unvetted marketplaces a
  live attack surface (`registry/guidance.yaml`).
- Vendor skills byte-verbatim and pin their tree hash; re-verify on load.
- Treat a persona-steering or identity-directive skill body as grounds for a
  do-not-use advisory — for a summoned entity such a body can be engrammed
  into an append-only life.
