"""Data models for Agent Skills."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
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

    def __post_init__(self) -> None:
        # frozen=True blocks rebinding, not in-place mutation: the Mapping
        # annotation is a promise a plain dict does not keep (a host mutating
        # a cached instance would corrupt every holder). Seal it.
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

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
    """A skill resolved from disk with its root directory.

    ``skill_md_sha256`` is the digest of the exact SKILL.md BYTES this load
    parsed (None when constructed outside the filesystem loader). The
    selection pipeline compares it to the tree hash's per-file digest so a
    verdict always attests the bytes that were actually composed.
    """

    document: SkillDocument
    root_dir: Path
    skill_md_sha256: str | None = None
