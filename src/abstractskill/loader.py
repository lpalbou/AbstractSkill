"""Filesystem discovery and loading for Agent Skills."""

from __future__ import annotations

from pathlib import Path

from abstractskill.errors import SkillNotFoundError, SkillParseError, SkillValidationError
from abstractskill.models import LoadedSkill, SkillMetadata
from abstractskill.parser import parse_skill_md
from abstractskill.validation import SKILL_FILENAME, validate_directory_name_match


class FilesystemSkillLoader:
    """Discover and load skills from one or more directory roots.

    Later roots override earlier ones when skill names collide.
    """

    def __init__(self, roots: Path | str | list[Path | str]) -> None:
        if isinstance(roots, (str, Path)):
            root_list = [roots]
        else:
            root_list = list(roots)
        self._roots = [Path(root).expanduser() for root in root_list]

    @property
    def roots(self) -> tuple[Path, ...]:
        return tuple(self._roots)

    def discover(self) -> list[SkillMetadata]:
        """Return metadata for all valid skills, sorted by name."""
        by_name: dict[str, SkillMetadata] = {}
        for root in self._roots:
            if not root.is_dir():
                continue
            for child in sorted(root.iterdir()):
                if not child.is_dir():
                    continue
                skill_file = child / SKILL_FILENAME
                if not skill_file.is_file():
                    continue
                try:
                    document = parse_skill_md(
                        skill_file.read_text(encoding="utf-8"),
                        source_path=skill_file,
                        directory_name=child.name,
                    )
                except (SkillParseError, SkillValidationError):
                    continue
                by_name[document.metadata.name] = document.metadata
        return [by_name[name] for name in sorted(by_name)]

    def load(self, name: str) -> LoadedSkill:
        """Load the full SKILL.md document for a skill by name."""
        for root in reversed(self._roots):
            if not root.is_dir():
                continue
            candidate = root / name
            skill_file = candidate / SKILL_FILENAME
            if not skill_file.is_file():
                continue
            text = skill_file.read_text(encoding="utf-8")
            document = parse_skill_md(
                text,
                source_path=skill_file,
                directory_name=candidate.name,
            )
            if document.metadata.name != name:
                raise SkillValidationError(
                    f"skill at {skill_file} declares name {document.metadata.name!r}, "
                    f"expected {name!r}"
                )
            validate_directory_name_match(document.metadata.name, candidate.name)
            return LoadedSkill(document=document, root_dir=candidate)
        raise SkillNotFoundError(f"skill not found: {name}")
