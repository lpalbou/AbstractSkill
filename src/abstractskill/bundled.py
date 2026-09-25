"""The curated skill registry bundled inside the abstractskill package.

The wheel ships the reviewed shelf as package data under
``abstractskill/registry/``::

    registry/skills/<name>/      one folder per curated skill (SKILL.md + resources)
    registry/licenses/*.LICENSE  upstream licenses for catalog-vendored skills
    registry/catalog.yaml        vendoring catalog; carries the bundle ``version``
    registry/validations.yaml    trust records, bound to skill tree hashes
    registry/advisories.yaml     do-not-use advisories
    registry/guidance.yaml       class-level curation guidance

Hosts should not serve the installed package directory itself (it is
replaced on every upgrade and may be read-only). They copy it into a
directory they own with :func:`seed_registry`, which is safe to run on every
start and from several processes at once: it adds what is missing, refreshes
only what a previous seed wrote and nobody edited since, and never overwrites
an operator's changes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterator

import yaml

from abstractskill.errors import SkillError, SkillValidationError
from abstractskill.tree import OS_JUNK_FILES, hash_skill_tree

try:  # POSIX
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]
    import msvcrt

SEED_MANIFEST = ".seeded.json"
"""File name, inside the seeded directory, recording what seeds wrote."""

SEED_LOCK = ".seed.lock"
"""Lock file, inside the seeded directory, serialising concurrent seeds."""

_MANIFEST_SCHEMA = 1
_STAGING_PREFIX = ".seed-staging"
_SKILLS = "skills"
_LICENSES = "licenses"
_CATALOG = "catalog.yaml"
_VERSION_RE = re.compile(r"\d+(\.\d+)*")


@dataclass(frozen=True, slots=True)
class SeedReport:
    """Outcome of one :func:`seed_registry` call.

    Items are named by their path relative to ``dest`` (``skills/<name>``,
    ``licenses/<file>``, ``validations.yaml``, ...). Every bundled item lands
    in exactly one of these buckets:

    - ``added``: absent at ``dest``, copied from the bundle;
    - ``updated``: still byte-identical to what a previous seed wrote,
      replaced with the newer bundled content;
    - ``unchanged``: already byte-identical to the bundle;
    - ``kept_user_modified``: a previous seed wrote it and it was edited since;
    - ``kept_foreign``: present at ``dest`` but never written by a seed
      (the manifest has no record of it), or of the wrong type;
    - ``kept_unknown_provenance``: ``dest`` has no seed manifest, so only
      items byte-identical to the bundle can be adopted; the rest are kept;
    - ``kept_symlink``: the item at ``dest`` is a symlink (never followed);
    - ``kept_unreadable``: the item cannot be hashed (unreadable file, a
      symlink inside a skill folder, ...);
    - ``kept_newer``: the bundle is OLDER than the last seed of ``dest``
      (``bundled_version < previous_version``); seeded content is never
      replaced by older content.

    ``not_in_bundle`` lists items a previous seed wrote that the bundle no
    longer contains and that still exist at ``dest``. They are left in place;
    deciding to remove them is the host's call.

    ``previous_version`` is the bundle version recorded by earlier seeds of
    ``dest`` (``None`` when ``dest`` has no manifest).
    """

    dest: Path
    bundled_version: str
    previous_version: str | None
    added: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()
    kept_user_modified: tuple[str, ...] = ()
    kept_foreign: tuple[str, ...] = ()
    kept_unknown_provenance: tuple[str, ...] = ()
    kept_symlink: tuple[str, ...] = ()
    kept_unreadable: tuple[str, ...] = ()
    kept_newer: tuple[str, ...] = ()
    not_in_bundle: tuple[str, ...] = ()

    @property
    def changed(self) -> bool:
        """True when this seed wrote any item under ``dest``."""
        return bool(self.added or self.updated)

    @property
    def kept(self) -> dict[str, str]:
        """Every kept item mapped to its reason (the bucket name)."""
        reasons: dict[str, str] = {}
        for bucket in (
            "kept_user_modified",
            "kept_foreign",
            "kept_unknown_provenance",
            "kept_symlink",
            "kept_unreadable",
            "kept_newer",
        ):
            for key in getattr(self, bucket):
                reasons[key] = bucket
        return reasons


def bundled_registry_dir() -> Path:
    """Return the directory holding the registry shipped with this package.

    Works from an installed wheel and from a source checkout (where it is
    ``src/abstractskill/registry``). Treat it as read-only; use
    :func:`seed_registry` to obtain a copy a host may serve and edit.
    """
    resource = files("abstractskill") / "registry"
    if not isinstance(resource, Path):
        raise SkillError(
            "the bundled skill registry is not on the filesystem "
            f"({resource!r}); install abstractskill as a regular (unzipped) package"
        )
    if not (resource / _SKILLS).is_dir():
        raise SkillError(
            f"the bundled skill registry is missing or incomplete at {resource}; "
            "reinstall abstractskill"
        )
    return resource


def bundled_registry_version() -> str:
    """Return the ``version`` declared in the bundled ``catalog.yaml``.

    The version is dotted-numeric (``2026.09.25``) so bundles order: seeding
    never replaces content written by a newer bundle with an older one.
    """
    catalog = bundled_registry_dir() / _CATALOG
    data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not _VERSION_RE.fullmatch(version.strip()):
        raise SkillValidationError(
            f"{catalog} must declare a dotted-numeric string 'version' (e.g. \"2026.09.25\")"
        )
    return version.strip()


def seed_registry(dest: Path | str) -> SeedReport:
    """Copy the bundled registry into ``dest`` without overwriting operator edits.

    ``dest`` is created when missing and ends up with the same layout as the
    bundle (``skills/``, ``licenses/`` and the four yaml files), which is what
    a host reads as its skill shelf.

    Each skill folder is compared by :func:`abstractskill.hash_skill_tree`,
    each file by the sha256 of its bytes, against the bundle and against the
    hashes earlier seeds recorded in ``dest/.seeded.json``:

    - missing at ``dest``: added;
    - identical to the bundle: unchanged (and recorded as seeded);
    - identical to what a previous seed wrote: replaced by the bundled
      content, unless the bundle is older than that seed (``kept_newer``);
    - anything else is kept as it is, with its reason (see
      :class:`SeedReport`). An operator's edit is never overwritten, and an
      item the seed never wrote is never claimed.

    Without a manifest (first seed, or a manifest lost), items at ``dest``
    that are byte-identical to the bundle are adopted and recorded; every
    other existing item is kept as ``kept_unknown_provenance`` because the
    seed cannot tell an old seeded copy from an operator edit.

    Items at ``dest`` that are not in the bundle are never deleted. Seeding is
    idempotent (a second call with the same bundle writes nothing) and safe
    to run from several processes at once: the whole call holds an exclusive
    lock on ``dest/.seed.lock``. No network access is involved.

    Raises :class:`SkillError` when the manifest is unreadable or of an
    unknown schema, when ``dest`` lies inside the bundled registry, or when a
    staging entry in ``dest`` is a symlink.
    """
    source = bundled_registry_dir()
    bundled_version = bundled_registry_version()
    root = Path(dest)
    if _is_within(root, source):
        raise SkillError(f"refusing to seed into the bundled registry itself ({root})")
    root.mkdir(parents=True, exist_ok=True)

    with _exclusive_lock(root / SEED_LOCK):
        _clear_stale_staging(root)
        return _seed_locked(source, bundled_version, root)


def _seed_locked(source: Path, bundled_version: str, root: Path) -> SeedReport:
    manifest_path = root / SEED_MANIFEST
    manifest = _read_manifest(manifest_path)
    has_manifest = bool(manifest)
    previous_version: str | None = manifest.get("bundled_version") if has_manifest else None
    seeded: dict[str, str] = dict(manifest.get("items", {}))
    downgrade = previous_version is not None and _vkey(bundled_version) < _vkey(previous_version)

    buckets: dict[str, list[str]] = {
        name: []
        for name in (
            "added", "updated", "unchanged", "kept_user_modified", "kept_foreign",
            "kept_unknown_provenance", "kept_symlink", "kept_unreadable", "kept_newer",
        )
    }

    bundled_items = _bundled_items(source)
    staging = Path(tempfile.mkdtemp(prefix=f"{_STAGING_PREFIX}-", dir=root))
    try:
        for key, src in bundled_items:
            is_dir = src.is_dir()
            bundled_hash = _hash_item(src, is_dir)
            target = root / key

            if target.is_symlink():
                buckets["kept_symlink"].append(key)
                continue
            if not target.exists():
                _install(src, target, is_dir, staging)
                seeded[key] = bundled_hash
                buckets["added"].append(key)
                continue

            current: str | None = None
            if is_dir == target.is_dir():
                try:
                    current = _hash_item(target, is_dir)
                except (OSError, SkillValidationError):
                    buckets["kept_unreadable"].append(key)
                    continue

            if current == bundled_hash:
                seeded[key] = bundled_hash
                buckets["unchanged"].append(key)
            elif not has_manifest:
                buckets["kept_unknown_provenance"].append(key)
            elif key not in seeded:
                buckets["kept_foreign"].append(key)
            elif current == seeded[key]:
                if downgrade:
                    buckets["kept_newer"].append(key)
                else:
                    _install(src, target, is_dir, staging)
                    seeded[key] = bundled_hash
                    buckets["updated"].append(key)
            else:
                buckets["kept_user_modified"].append(key)
    finally:
        _remove_staging(staging)

    bundled_keys = {key for key, _ in bundled_items}
    not_in_bundle: list[str] = []
    for key in sorted(set(seeded) - bundled_keys):
        target = root / key
        if target.exists() or target.is_symlink():
            not_in_bundle.append(key)
        else:
            del seeded[key]

    recorded_version = previous_version if downgrade else bundled_version
    new_manifest = {
        "schema": _MANIFEST_SCHEMA,
        "bundled_version": recorded_version,
        "items": dict(sorted(seeded.items())),
    }
    if new_manifest != manifest:
        _write_json_atomic(manifest_path, new_manifest)

    return SeedReport(
        dest=root,
        bundled_version=bundled_version,
        previous_version=previous_version,
        not_in_bundle=tuple(not_in_bundle),
        **{name: tuple(keys) for name, keys in buckets.items()},
    )


def _vkey(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _is_within(path: Path, parent: Path) -> bool:
    try:
        return path.resolve().is_relative_to(parent.resolve())
    except OSError:
        return False


@contextmanager
def _exclusive_lock(path: Path) -> Iterator[None]:
    """Hold an exclusive advisory lock on ``path`` (created if missing)."""
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o644)
    except OSError as exc:
        raise SkillError(f"cannot open seed lock {path}: {exc}") from exc
    try:
        if fcntl is not None:
            fcntl.flock(fd, fcntl.LOCK_EX)
        else:  # pragma: no cover - Windows
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(fd, fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    finally:
        os.close(fd)


def _clear_stale_staging(root: Path) -> None:
    """Remove staging folders left by an interrupted seed (called under the lock)."""
    for entry in sorted(root.glob(f"{_STAGING_PREFIX}*")):
        if entry.is_symlink():
            raise SkillError(
                f"{entry} is a symlink; seed staging must be a real folder inside "
                f"{root}. Remove the symlink and seed again."
            )
        if entry.is_dir():
            shutil.rmtree(entry)


def _remove_staging(staging: Path) -> None:
    if staging.is_symlink():
        raise SkillError(f"seed staging {staging} was replaced by a symlink; not removing it")
    if staging.exists():
        shutil.rmtree(staging)


def _bundled_items(source: Path) -> list[tuple[str, Path]]:
    """Enumerate seedable items: top-level yaml files, licenses, skill folders."""
    items: list[tuple[str, Path]] = []
    for path in sorted(source.glob("*.yaml")):
        items.append((path.name, path))
    licenses = source / _LICENSES
    if licenses.is_dir():
        for path in sorted(licenses.iterdir()):
            if path.is_file() and path.name not in OS_JUNK_FILES:
                items.append((f"{_LICENSES}/{path.name}", path))
    for path in sorted((source / _SKILLS).iterdir()):
        if path.is_dir():
            items.append((f"{_SKILLS}/{path.name}", path))
    return items


def _hash_item(path: Path, is_dir: bool) -> str:
    if is_dir:
        return hash_skill_tree(path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _install(src: Path, target: Path, is_dir: bool, staging: Path) -> None:
    """Copy ``src`` to ``target`` via a staged copy and renames.

    Replacing a folder takes two renames (old out, new in). If the second one
    fails, the old folder is moved back before the error propagates, so a
    failed refresh never loses the skill.
    """
    staged = staging / target.name
    if is_dir:
        shutil.copytree(src, staged, ignore=shutil.ignore_patterns(*OS_JUNK_FILES))
    else:
        shutil.copy2(src, staged)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not (is_dir and target.is_dir()):
        os.replace(staged, target)
        return
    retired = staging / f"{target.name}.previous"
    os.replace(target, retired)
    try:
        os.replace(staged, target)
    except BaseException:
        os.replace(retired, target)
        raise
    shutil.rmtree(retired)


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SkillError(
            f"cannot read seed manifest {path}: {exc}. Restore it from a backup; "
            "without it, seeding can only adopt items identical to the bundle and "
            "keeps every other item unrefreshed"
        ) from exc
    if not isinstance(data, dict):
        raise SkillError(f"seed manifest {path} is malformed (not a JSON object)")
    if data.get("schema") != _MANIFEST_SCHEMA:
        raise SkillError(
            f"seed manifest {path} has schema {data.get('schema')!r}; this abstractskill "
            f"understands schema {_MANIFEST_SCHEMA} only (a newer abstractskill wrote it?)"
        )
    items = data.get("items")
    version = data.get("bundled_version")
    if (
        not isinstance(items, dict)
        or not all(isinstance(k, str) and isinstance(v, str) for k, v in items.items())
        or not isinstance(version, str)
        or not _VERSION_RE.fullmatch(version)
    ):
        raise SkillError(f"seed manifest {path} is malformed (items/bundled_version)")
    return data


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(data, indent=2) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
