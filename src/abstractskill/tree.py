"""Whole-tree hashing and structural inventory for skill folders.

The content hash of a single SKILL.md (``content_hash``) tracks document
evolution; hosts that VENDOR a skill folder (copy it into an entity home or
registry) need tamper detection over the WHOLE tree. ``hash_skill_tree``
provides that with a stated canonicalization:

- files are identified by their POSIX-style relative path;
- the manifest is sorted by that path (codepoint order), one entry per file;
- each entry hashes the file's RAW BYTES (sha256) — EOL normalization is
  deliberately NOT applied: vendoring copies bytes, so byte-identical trees
  hash identically on every platform, and two byte-different trees must
  never share a hash (that would defeat tamper detection);
- OS junk files (.DS_Store, Thumbs.db) are excluded so an operator merely
  browsing a folder cannot change its hash;
- symlinks are refused loudly: a link can point outside the tree, and a
  tamper hash must never cover bytes it does not contain.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from abstractskill.errors import SkillValidationError
from abstractskill.validation import SKILL_FILENAME

OS_JUNK_FILES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})

# Spec-conventional resource directories (agentskills.io): scripts/ holds
# executable helpers; references/ and assets/ hold passive resources.
SCRIPTS_DIR = "scripts"


@dataclass(frozen=True, slots=True)
class SkillResource:
    """One file inside a skill folder."""

    rel_path: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class SkillInventory:
    """Structural truth about a skill folder (never derived from frontmatter).

    ``has_scripts`` is a structural fact — any file under ``scripts/`` —
    so a console can badge "requires enablement" honestly even when the
    frontmatter claims otherwise.
    """

    root_dir: Path
    files: tuple[SkillResource, ...]
    tree_hash: str
    total_bytes: int
    has_scripts: bool

    @property
    def script_files(self) -> tuple[SkillResource, ...]:
        prefix = f"{SCRIPTS_DIR}/"
        return tuple(item for item in self.files if item.rel_path.startswith(prefix))


def _iter_skill_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(skill_dir.rglob("*")):
        if path.is_symlink():
            raise SkillValidationError(
                f"skill tree contains a symlink at {path}; symlinks are not "
                "allowed inside skill folders (they can point outside the tree)"
            )
        if not path.is_file():
            continue
        if path.name in OS_JUNK_FILES:
            continue
        files.append(path)
    return files


def _file_digest(path: Path) -> bytes:
    # Stream in chunks: a vendored tree may carry large resources and the
    # hasher must not need the whole file in RAM.
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.digest()


def hash_skill_tree(skill_dir: Path | str) -> str:
    """Return a deterministic sha256 over every file in a skill folder.

    The manifest is length-prefixed binary, not text: a delimiter-joined
    text manifest is forgeable by filenames containing the delimiter
    (POSIX permits ``\\n`` in filenames), which would let a crafted tree
    collide with an audited one. Length prefixes make the serialization
    injective, so byte-different trees can never share a hash.
    """
    root = Path(skill_dir)
    if not root.is_dir():
        raise SkillValidationError(f"skill directory not found: {root}")

    entries: list[tuple[bytes, bytes]] = []
    for path in _iter_skill_files(root):
        rel_path = path.relative_to(root).as_posix().encode("utf-8")
        entries.append((rel_path, _file_digest(path)))
    entries.sort()

    manifest = hashlib.sha256()
    for rel_path, digest in entries:
        manifest.update(len(rel_path).to_bytes(8, "big"))
        manifest.update(rel_path)
        manifest.update(digest)
    return manifest.hexdigest()


def inspect_skill_dir(skill_dir: Path | str) -> SkillInventory:
    """Return the structural inventory of a skill folder."""
    root = Path(skill_dir)
    if not root.is_dir():
        raise SkillValidationError(f"skill directory not found: {root}")
    skill_file = root / SKILL_FILENAME
    if not skill_file.is_file():
        raise SkillValidationError(f"skill directory has no {SKILL_FILENAME}: {root}")

    resources: list[SkillResource] = []
    total = 0
    has_scripts = False
    scripts_prefix = f"{SCRIPTS_DIR}/"
    for path in _iter_skill_files(root):
        rel_path = path.relative_to(root).as_posix()
        size = path.stat().st_size
        resources.append(SkillResource(rel_path=rel_path, size_bytes=size))
        total += size
        if rel_path.startswith(scripts_prefix):
            has_scripts = True

    resources.sort(key=lambda item: item.rel_path)
    return SkillInventory(
        root_dir=root,
        files=tuple(resources),
        tree_hash=hash_skill_tree(root),
        total_bytes=total,
        has_scripts=has_scripts,
    )


def read_skill_resource(
    skill_dir: Path | str,
    rel_path: str,
    *,
    max_bytes: int,
) -> bytes:
    """Read one resource file from a skill folder, strictly inside the tree.

    Oversized resources are refused honestly (naming the size) rather than
    silently truncated; traversal-shaped paths and symlinks are refused.
    """
    root = Path(skill_dir).resolve()
    if not root.is_dir():
        raise SkillValidationError(f"skill directory not found: {root}")

    candidate = (root / rel_path).resolve()
    if not candidate.is_relative_to(root):
        raise SkillValidationError(
            f"resource path {rel_path!r} escapes the skill directory"
        )
    # Re-check the unresolved chain for symlinks: resolve() above hides them.
    walk = root / rel_path
    for parent in [walk, *walk.parents]:
        if parent == root:
            break
        if parent.is_symlink():
            raise SkillValidationError(
                f"resource path {rel_path!r} crosses a symlink; refused"
            )
    if not candidate.is_file():
        raise SkillValidationError(f"resource not found: {rel_path!r}")

    size = candidate.stat().st_size
    if size > max_bytes:
        raise SkillValidationError(
            f"resource {rel_path!r} is {size} bytes, over the {max_bytes}-byte "
            "cap; refusing to read (no silent truncation)"
        )
    return candidate.read_bytes()
