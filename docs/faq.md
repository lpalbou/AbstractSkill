# FAQ

## What is a skill, and how does it differ from a flow?

A skill is a portable procedure/knowledge pack (`SKILL.md` + optional
resources). Flows run; skills are activated/loaded. AbstractSkill owns the
skill contract so `abstractruntime`, `abstractgateway`, and thin clients share
identical semantics.

## Does AbstractSkill run skill scripts?

No. It parses, validates, hashes, discovers, composes, and classifies. It
executes nothing. `inspect_skill_dir().has_scripts` reports whether a folder
contains `scripts/`, so a host can badge "requires enablement" honestly, but
enablement and execution are the host's concern, and the v1 shelf ships
knowledge/procedure packs only.

## Why do CRLF and LF copies of the same skill hash differently?

Hash = bytes, parse = meaning. The hashes are byte-exact so tamper detection
never calls two different byte-trees "the same". A CRLF-authored skill parses
identically to its LF twin but hashes differently. Vendor skills from archives
or byte-copies, not through EOL-rewriting checkouts (git `autocrlf`), or hash
verification will honestly report the rewrite as a mismatch.

## Why is `registry/advisories.yaml` empty?

The do-not-use advisory registry names **specific** skills, and AbstractSkill
does not assert a specific malicious skill on its own authority before its own
behavioral audit or a leveraged external feed identifies a real one. Class-
level protection is active now via `registry/guidance.yaml`, the fail-closed
`unverified` default, and the `has_scripts` review gate. See the
[trust model](trust.md).

## Can a skill grant an agent more tools than the operator allowed?

No. `effective_tools` intersects a skill's `allowed-tools` with the operator
grant and can only narrow it. A skill with no `allowed-tools` contributes
nothing. Ecosystem-flavored tokens map to framework tool names through a
host-owned table; unmapped or ungranted tokens drop with a `#FALLBACK`
warning and never relax policy.

## Is a `first_party` or `attachable` verdict a safety guarantee?

No. Trust classification raises the bar and makes the judgment explicit; it
does not certify safety. See "What trust does NOT guarantee" in the
[trust model](trust.md).

## What are `coredoc` and `backlog` in the shelf?

Two maintainer-authored methodology skills (documentation maintenance and
backlog planning), vendored byte-verbatim and first-party reviewed. They are
`adopted` (reviewed, not yet behaviorally audited). `adversarial-iteration`
is the framework's first-party skill for the "one adversarial reviewer plus at
least three improvement cycles" method.
