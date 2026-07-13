"""Filesystem discovery and loading for Agent Skills."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable

from abstractskill.errors import SkillNotFoundError, SkillParseError, SkillValidationError
from abstractskill.models import LoadedSkill, SkillMetadata
from abstractskill.parser import parse_skill_md
from abstractskill.validation import SKILL_FILENAME, validate_skill_name

logger = logging.getLogger("abstractskill")

WarningCallback = Callable[[str], None]


def _warn(message: str, on_warning: WarningCallback | None) -> None:
    # Degraded paths are loud by default (framework rule: no silent fallbacks);
    # hosts that surface warnings themselves pass on_warning.
    logger.warning(message)
    if on_warning is not None:
        on_warning(message)


def _read_skill_text(skill_file: Path) -> tuple[str, str]:
    """Read SKILL.md, returning (text, sha256 of the RAW BYTES read).

    Bytes are read first and hashed before decoding, so the digest attests
    exactly the bytes this load parsed — the selection pipeline compares it
    against the tree hash's per-file digest to detect a swap between load
    and hash on user-writable roots (TOCTOU). Decoding from bytes also
    skips the text layer's newline translation, so the digest (and the
    document's ``raw``/``content_hash``) reflect true file bytes on every
    platform.

    UnicodeDecodeError is a ValueError, not a SkillError — unmapped, one
    binary/mis-encoded SKILL.md in a user-writable root would fly past the
    skip-and-fall-back machinery and crash the whole discovery/selection
    (adversary-found when multi-root selection made user dirs a designed
    configuration).
    """
    raw = skill_file.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SkillParseError(f"SKILL.md at {skill_file} is not valid UTF-8: {exc}") from exc
    return text, hashlib.sha256(raw).hexdigest()


class FilesystemSkillLoader:
    """Discover and load skills from one or more directory roots.

    Later roots override earlier ones when skill names collide. A broken
    skill copy never shadows a valid one: both ``discover`` and ``load``
    skip invalid copies with a ``#FALLBACK`` warning, so the skill a host
    lists is always the skill it can load.
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

    def discover(self, *, on_warning: WarningCallback | None = None) -> list[SkillMetadata]:
        """Return metadata for all valid skills, sorted by name.

        Invalid skill folders are skipped with a ``#FALLBACK`` warning
        (logged, and delivered to ``on_warning`` when provided).
        """
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
                    text, _digest = _read_skill_text(skill_file)
                    document = parse_skill_md(
                        text,
                        source_path=skill_file,
                        directory_name=child.name,
                    )
                except (SkillParseError, SkillValidationError) as exc:
                    _warn(f"#FALLBACK: skipping invalid skill at {skill_file}: {exc}", on_warning)
                    continue
                by_name[document.metadata.name] = document.metadata
        return [by_name[name] for name in sorted(by_name)]

    def load(self, name: str, *, on_warning: WarningCallback | None = None) -> LoadedSkill:
        """Load the full SKILL.md document for a skill by name.

        Resolution matches ``discover``: the highest-precedence VALID copy
        wins; broken copies are skipped with a ``#FALLBACK`` warning. If
        only broken copies exist, the highest-precedence parse error is
        raised (never a misleading "not found").
        """
        # Reject separator/traversal-shaped names before touching the
        # filesystem; also guarantees `root / name` stays a direct child.
        validate_skill_name(name)

        first_error: SkillParseError | SkillValidationError | None = None
        for root in reversed(self._roots):
            if not root.is_dir():
                continue
            candidate = root / name
            skill_file = candidate / SKILL_FILENAME
            if not skill_file.is_file():
                continue
            try:
                text, digest = _read_skill_text(skill_file)
                document = parse_skill_md(
                    text,
                    source_path=skill_file,
                    directory_name=candidate.name,
                )
            except (SkillParseError, SkillValidationError) as exc:
                if first_error is None:
                    first_error = exc
                _warn(f"#FALLBACK: skipping invalid skill at {skill_file}: {exc}", on_warning)
                continue
            return LoadedSkill(document=document, root_dir=candidate, skill_md_sha256=digest)
        if first_error is not None:
            raise first_error
        raise SkillNotFoundError(f"skill not found: {name}")
