"""Data models for Agent Skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    """Metadata-only skill view used for discovery and progressive disclosure."""

    name: str
    description: str
    license: str | None = None
    compatibility: str | None = None
    allowed_tools: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    source_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
        }
        if self.license is not None:
            payload["license"] = self.license
        if self.compatibility is not None:
            payload["compatibility"] = self.compatibility
        if self.allowed_tools:
            payload["allowed_tools"] = list(self.allowed_tools)
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        if self.source_path is not None:
            payload["source_path"] = str(self.source_path)
        return payload


@dataclass(frozen=True, slots=True)
class SkillDocument:
    """Full SKILL.md content: frontmatter metadata plus markdown instructions."""

    metadata: SkillMetadata
    body: str
    raw: str
    content_hash: str

    @property
    def name(self) -> str:
        return self.metadata.name


@dataclass(frozen=True, slots=True)
class LoadedSkill:
    """A skill resolved from disk with its root directory."""

    document: SkillDocument
    root_dir: Path
