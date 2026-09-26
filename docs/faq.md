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

## Why is `advisories.yaml` empty?

The do-not-use advisory registry names **specific** skills, and AbstractSkill
does not assert a specific malicious skill on its own authority before its own
behavioral audit or a leveraged external feed identifies a real one. Class-
level protection comes from the bundled `guidance.yaml`, the fail-closed
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

## Which skills ship with the package, and how does a host use them?

The wheel carries the curated registry: 14 skills, the upstream licenses of
vendored third-party skills, and four yaml files (`catalog.yaml`,
`validations.yaml`, `advisories.yaml`, `guidance.yaml`). A host copies it
into a directory it owns with `seed_registry` and serves that copy; the
[curated skills catalog](skills-catalog.md) lists the skills, and
[Getting started](getting-started.md#seed-the-bundled-shelf-into-a-host-directory)
shows the call.

## Will seeding overwrite my edits to a shelf skill?

No. An item is refreshed only while it is byte-identical to what an earlier
seed wrote. An edited item is kept and reported as `kept_user_modified`.
Because trust binds to bytes, an edited skill no longer matches its
validation record and evaluates as `unverified` until it is re-validated.
To go back to the bundled version, see
[Troubleshooting](troubleshooting.md#a-bundled-skill-is-not-refreshed-after-an-upgrade).

## Does seeding remove skills that leave the bundle?

No. Seeding never deletes. Items an earlier seed wrote that the bundle no
longer contains are reported in `SeedReport.not_in_bundle`; removing them is
the host's or operator's decision.

## Does the tree hash cover file permissions and empty folders?

No. `hash_skill_tree` covers file paths and bytes only. A seed refresh of an
unmodified skill therefore does not preserve a changed executable bit or an
empty folder you added.
