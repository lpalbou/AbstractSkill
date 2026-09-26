# AbstractSkill

AbstractSkill is the shared Python library for [Agent Skills](https://agentskills.io/) (`SKILL.md`) in the
[AbstractFramework](https://github.com/lpalbou/AbstractFramework) ecosystem.

It provides a small, dependency-light foundation for:

- parsing and validating `SKILL.md` frontmatter and instructions
- discovering skills on disk (progressive disclosure: metadata first)
- computing stable content hashes for skill evolution and replay safety
- formatting compact `<available_skills>` prompt blocks for hosts and agents
- composing a skill's tool declarations with an operator grant (never widening)
- classifying skill trust: validated skills, do-not-use advisories, and a
  fail-closed verdict ([trust model](trust.md))

**Flows run; skills activate.** AbstractSkill owns the portable skill contract so
`abstractruntime`, `abstractgateway`, and thin clients can share identical semantics
without duplicating parsers.

## Install

```bash
pip install abstractskill
```

The wheel also carries the curated skill registry (14 reviewed skills and
their trust files). Hosts copy it into a directory they own with
`seed_registry`.

## Next steps

- [Getting started](getting-started.md) — parse, discover, compose tools, evaluate trust
- [Architecture](architecture.md) — components and data flow
- [API reference](api.md) — public functions and types
- [FAQ](faq.md) and [Troubleshooting](troubleshooting.md) — common questions and fixes
- [Curated skills catalog](skills-catalog.md) — the reviewed shelf shipped in the package

## Project links

- [GitHub repository](https://github.com/lpalbou/AbstractSkill)
- [PyPI package](https://pypi.org/project/abstractskill/)
- [Changelog](changelog.md)
- [Security policy](security.md)
