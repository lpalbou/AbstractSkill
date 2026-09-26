# Acknowledgements

AbstractSkill builds on the work of others:

- **[Agent Skills](https://agentskills.io/)** — the open `SKILL.md` format
  this library parses and validates.
- **[PyYAML](https://pyyaml.org/)** — the library's only runtime dependency.

## Vendored skills

The bundled registry includes third-party skills, vendored byte-verbatim at
pinned upstream commits. Their licenses ship with the package under
`abstractskill/registry/licenses/`:

- `verification-before-completion` from
  [obra/superpowers](https://github.com/obra/superpowers) (MIT).
- `meshvault-live-editing` from
  [lpalbou/meshvault](https://github.com/lpalbou/meshvault) (MIT).

The [curated skills catalog](docs/skills-catalog.md) lists every catalog
source with its pin and license.

## Research

The trust model and the guidance registry draw on published skill-ecosystem
security research. Each source is cited with its reference in
`abstractskill/registry/guidance.yaml` and in
[docs/trust-network-position.md](docs/trust-network-position.md).
