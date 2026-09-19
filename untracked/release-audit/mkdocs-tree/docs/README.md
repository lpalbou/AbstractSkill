# AbstractSkill documentation

AbstractSkill is the Agent Skills (`SKILL.md`) contract library for the
AbstractFramework ecosystem: parse and validate skills, discover them on disk
with progressive disclosure, hash them for evolution and tamper detection,
compose their tool declarations with an operator grant, and classify their
trust.

## Start here

- [Getting started](getting-started.md) — install, parse a skill, discover a
  directory, compose tools, evaluate trust.
- [Architecture](architecture.md) — the components, how they connect, and the
  data flow (with diagrams).
- [API reference](api.md) — the public functions and types.
- [FAQ](faq.md) — common questions and limitations.
- [Troubleshooting](troubleshooting.md) — symptoms, diagnostics, and fixes.

## Deep dives

- [Trust model](trust.md) — validated skills, the do-not-use advisory registry,
  guidance, and the fail-closed verdict.
- [Curated skills catalog](skills-catalog.md) — the reviewed, pinned list of
  third-party skills worth vendoring, the tiers (top/watch/excluded with
  reasons), and the curated-only install path.
- [Skills vs workflows vs MCP](skills-flows-mcp.md) — the decision guide for
  the framework's three extension mechanisms: comparison table, when to use
  which, composition patterns, and package responsibilities.
- [Trust-network position](trust-network-position.md) — how AbstractSkill
  relates to the wider skill-trust ecosystem (join / leverage / build).

## Project docs

- [Security policy](../SECURITY.md) — reporting and the trust guarantees this
  library does and does not make.
- [Changelog](../CHANGELOG.md) — release history.
- [Backlog](backlog/overview.md) — planning memory and the skill-trust track.

## Related

- [Knowledge base](KnowledgeBase.md) — durable contract decisions and lessons.
