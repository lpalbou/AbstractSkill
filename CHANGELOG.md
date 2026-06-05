# Changelog

All notable changes to this package are documented in this file.

## [0.1.0] - 2026-06-05

### Added

- Initial release of the `abstractskill` PyPI package.
- `SKILL.md` parser with YAML frontmatter and markdown body extraction.
- Skill name validation aligned with the Agent Skills spec (lowercase alphanumeric + hyphens).
- `FilesystemSkillLoader` for metadata-only discovery and full document loading.
- `content_hash` helper for stable skill evolution and replay snapshots.
- `format_available_skills_xml` for progressive-disclosure prompt blocks.
- GitHub Actions CI (Python 3.10–3.12) and trusted-publishing release workflow.
