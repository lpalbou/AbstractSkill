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
start: it adds what is missing, refreshes only what a previous seed wrote and
nobody edited since, and never overwrites an operator's changes.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from abstractskill.errors import SkillError, SkillValidationError
from abstractskill.tree import OS_JUNK_FILES, hash_skill_tree

SEED_MANIFEST = ".seeded.json"
"""File name, inside the seeded directory, recording what the last seed wrote."""

_MANIFEST_SCHEMA = 1
_STAGING_DIR = ".seed-staging"
_SKILLS = "skills"
_LICENSES = "licenses"
_CATALOG = "catalog.yaml"


@dataclass(frozen=True, slots=True)
class SeedReport:
    """Outcome of one :func:`seed_registry` call.

    Every bundled item appears in exactly one of the four tuples, named by
    its path relative to ``dest`` (``skills/<name>``, ``licenses/<file>``,
    ``validations.yaml``, ...):

    - ``added``: absent at ``dest``, copied from the bundle;
    - ``updated``: byte-identical to what a previous seed wrote, replaced
      with the newer bundled content;
    - ``kept_user_modified``: differs from both the bundle and the last
      seeded content (an operator edit, or an item the seed never wrote);
      left untouched;
    - ``unchanged``: already byte-identical to the bundle.

    ``previous_version`` is the bundle version recorded by the last seed of
    ``dest`` (``None`` on the first seed).
    """

    dest: Path
    bundled_version: str
    previous_version: str | None
    added: tuple[str, ...]
    updated: tuple[str, ...]
    kept_user_modified: tuple[str, ...]
    unchanged: tuple[str, ...]

    @property
    def changed(self) -> bool:
        """True when this seed wrote anything under ``dest``."""
        return bool(self.added or self.updated)


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
    """Return the ``version`` declared in the bundled ``catalog.yaml``."""
    catalog = bundled_registry_dir() / _CATALOG
    data = yaml.safe_load(catalog.read_text(encoding="utf-8"))
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise SkillValidationError(f"{catalog} must declare a non-empty string 'version'")
    return version.strip()


def seed_registry(dest: Path | str) -> SeedReport:
    """Copy the bundled registry into ``dest`` without overwriting operator edits.

    ``dest`` is created when missing and ends up with the same layout as the
    bundle (``skills/``, ``licenses/`` and the four yaml files), which is what
    a host reads as its skill shelf.

    Policy, applied to each skill folder (compared by
    :func:`abstractskill.hash_skill_tree`) and each file (compared by
    sha256 of its bytes):

    - missing at ``dest``: added;
    - identical to the bundle: unchanged;
    - identical to what the previous seed wrote (recorded in
      ``dest/.seeded.json``): replaced by the bundled content;
    - anything else: kept as it is. An operator's edit is never overwritten,
      and an item the seed never wrote is never claimed.

    Items at ``dest`` that are not in the bundle are left alone. Seeding is
    idempotent: a second call with the same bundle writes nothing and reports
    every item as unchanged (or kept). No network access is involved.
    """
    source = bundled_registry_dir()
    bundled_version = bundled_registry_version()
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)

    manifest_path = root / SEED_MANIFEST
    manifest = _read_manifest(manifest_path)
    previous_version = manifest.get("bundled_version")
    seeded: dict[str, str] = dict(manifest.get("items", {}))

    added: list[str] = []
    updated: list[str] = []
    kept: list[str] = []
    unchanged: list[str] = []

    staging = root / _STAGING_DIR
    try:
        for key, src in _bundled_items(source):
            is_dir = src.is_dir()
            bundled_hash = _hash_item(src, is_dir)
            target = root / key
            current_hash = _hash_existing(target, is_dir)

            if current_hash is None and not _exists(target):
                _install(src, target, is_dir, staging)
                seeded[key] = bundled_hash
                added.append(key)
            elif current_hash == bundled_hash:
                seeded[key] = bundled_hash
                unchanged.append(key)
            elif current_hash is not None and current_hash == seeded.get(key):
                _install(src, target, is_dir, staging)
                seeded[key] = bundled_hash
                updated.append(key)
            else:
                kept.append(key)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    new_manifest = {
        "schema": _MANIFEST_SCHEMA,
        "bundled_version": bundled_version,
        "items": dict(sorted(seeded.items())),
    }
    if new_manifest != manifest:
        _write_json_atomic(manifest_path, new_manifest)

    return SeedReport(
        dest=root,
        bundled_version=bundled_version,
        previous_version=previous_version if isinstance(previous_version, str) else None,
        added=tuple(added),
        updated=tuple(updated),
        kept_user_modified=tuple(kept),
        unchanged=tuple(unchanged),
    )


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


def _exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _hash_existing(target: Path, is_dir: bool) -> str | None:
    """Hash what sits at ``target``; ``None`` when absent or not comparable."""
    if target.is_symlink() or not target.exists():
        return None
    if is_dir != target.is_dir():
        return None
    try:
        return _hash_item(target, is_dir)
    except (OSError, SkillValidationError):
        return None


def _install(src: Path, target: Path, is_dir: bool, staging: Path) -> None:
    """Copy ``src`` to ``target`` via a staged copy and a rename."""
    staging.mkdir(parents=True, exist_ok=True)
    staged = staging / target.name
    if is_dir:
        if staged.exists():
            shutil.rmtree(staged)
        shutil.copytree(src, staged, ignore=shutil.ignore_patterns(*OS_JUNK_FILES))
    else:
        shutil.copy2(src, staged)
    target.parent.mkdir(parents=True, exist_ok=True)
    if is_dir and target.is_dir() and not target.is_symlink():
        retired = staging / f"{target.name}.previous"
        os.replace(target, retired)
        os.replace(staged, target)
        shutil.rmtree(retired)
    else:
        os.replace(staged, target)


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SkillError(
            f"cannot read seed manifest {path}: {exc}; delete it to re-seed "
            "(every existing item is then kept as operator content)"
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("items", {}), dict):
        raise SkillError(f"seed manifest {path} is malformed; delete it to re-seed")
    return data


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)
