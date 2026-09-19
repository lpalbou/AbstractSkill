#!/usr/bin/env python3
"""Vendor a CURATED skill onto the shelf — the only install path.

Usage:
    python scripts/vendor_skill.py <name> [--catalog registry/catalog.yaml]
    python scripts/vendor_skill.py --list

Curated-only by construction: the skill must have a reviewed entry in
``registry/catalog.yaml`` (pinned owner/repo + 40-hex commit). Anything else
is refused — there is no URL argument to smuggle a source through.

What it does, in order (fail-closed at every step):
1. load + validate the catalog entry (library contract, network-free);
2. fetch EXACTLY the pinned commit into a temp dir via git (no tarball
   extraction surface; ``git fetch --depth 1 origin <sha>``);
3. byte-copy the skill subtree (symlinks refused — same rule as
   ``hash_skill_tree``) into a staging dir named by the skill's FRONTMATTER
   name (the spec key; must equal the catalog name);
4. parse + validate the staged skill with the shipped parser;
5. recompute the whole-tree hash and VERIFY it against the catalog's
   ``expected_tree_hash`` when present (re-vendor must be byte-identical —
   an upstream force-push cannot silently change the shelf). First vendoring
   prints the hash for the curator to pin after human diff review;
6. move the staged tree into ``registry/skills/<name>/`` (refuses to
   overwrite unless the bytes are identical or --force is given);
7. print the SHELF_POLICY / validations line the curator adds, then run
   ``refresh_shelf.py`` guidance. Trust stays fail-closed: third-party
   entries mint at most manual-review/adopted; scripts-present skills stay
   requires_review at the gate no matter what the catalog says.

The network/git code lives HERE deliberately — the abstractskill library
stays network-free; this script is curator tooling.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHELF = REPO / "registry" / "skills"
DEFAULT_CATALOG = REPO / "registry" / "catalog.yaml"

sys.path.insert(0, str(REPO / "src"))

from abstractskill import (  # noqa: E402
    hash_skill_tree,
    inspect_skill_dir,
    load_catalog,
    lint_catalog,
    parse_skill_md,
)
from abstractskill.catalog import CatalogEntry  # noqa: E402
from abstractskill.errors import SkillError  # noqa: E402


def _run_git(args: list[str], cwd: Path) -> None:
    # Defense in depth beyond the catalog contract's slug/sha validation:
    # git runs with ambient config NEUTRALIZED (no user hooks, filters, or
    # alternates can act during fetch/checkout) — a supply-chain vendor step
    # must not depend on the curator's global git configuration being benign.
    env = dict(os.environ)
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "",
        "GIT_TERMINAL_PROMPT": "0",
    })
    try:
        result = subprocess.run(
            ["git", "-c", f"core.hooksPath={os.devnull}", *args],
            cwd=str(cwd), capture_output=True, text=True, timeout=300, env=env,
        )
    except FileNotFoundError:
        raise SystemExit("git is required for vendoring and was not found on PATH")
    except subprocess.TimeoutExpired:
        raise SystemExit(
            f"git {' '.join(args)} timed out after 300s — check network/proxy and retry"
        )
    if result.returncode != 0:
        hint = ""
        if "fetch" in args and ("not our ref" in result.stderr or "upload-pack" in result.stderr):
            hint = (
                "\nhint: the server may refuse unadvertised-object fetches "
                "(uploadpack.allowAnySHA1InWant); GitHub allows them — verify the "
                "pinned SHA exists in the repo"
            )
        raise SystemExit(
            f"git {' '.join(args)} failed ({result.returncode}):\n{result.stderr.strip()}{hint}"
        )


def _fetch_pinned(entry: CatalogEntry, workdir: Path) -> Path:
    """Fetch exactly the pinned commit; return the checked-out repo root."""
    checkout = workdir / "repo"
    checkout.mkdir()
    _run_git(["init", "-q"], checkout)
    _run_git(["remote", "add", "origin", entry.clone_url], checkout)
    _run_git(["fetch", "-q", "--depth", "1", "origin", entry.upstream_ref], checkout)
    _run_git(["checkout", "-q", "FETCH_HEAD"], checkout)
    return checkout


def _copy_tree_no_symlinks(src: Path, dst: Path) -> None:
    """Byte-copy a tree, refusing symlinks loudly (tamper/escape surface).

    VCS dirs and OS junk are EXCLUDED so the copy set equals the hash set
    (`hash_skill_tree` skips OS junk; an unhashed file at rest would be an
    unverified byte surface) — and a nested `.git` must never reach the shelf.
    """
    from abstractskill.tree import OS_JUNK_FILES  # single exclusion source

    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if any(part in {".git", ".svn", ".hg"} for part in rel.parts):
            continue
        if path.name in OS_JUNK_FILES:
            continue
        if path.is_symlink():
            raise SystemExit(
                f"refusing to vendor: symlink in upstream skill tree: "
                f"{rel} (same rule as hash_skill_tree)"
            )
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)  # copyfile never follows dst symlinks


def _trees_identical(a: Path, b: Path) -> bool:
    """Byte identity via the SAME whole-tree hash trust binds to.

    Never a stat-shallow compare: size+mtime equality must not pass for
    byte-different files (trust binds to bytes, everywhere).
    """
    return hash_skill_tree(a) == hash_skill_tree(b)


def _vendor_license(entry: CatalogEntry, skill_src: Path, repo_root: Path) -> None:
    """Copy the upstream license text to registry/licenses/<name>.LICENSE.

    Per-skill license files (Anthropic's per-dir LICENSE.txt) win over the
    repo-root license. Out-of-tree deliberately: adding a license INSIDE the
    vendored dir would change the pinned tree hash.
    """
    licenses_dir = REPO / "registry" / "licenses"
    candidates = [
        skill_src / "LICENSE.txt", skill_src / "LICENSE",
        repo_root / "LICENSE", repo_root / "LICENSE.txt", repo_root / "LICENSE.md",
    ]
    for candidate in candidates:
        if candidate.is_file() and not candidate.is_symlink():
            licenses_dir.mkdir(parents=True, exist_ok=True)
            target = licenses_dir / f"{entry.name}.LICENSE"
            header = (
                f"# License for registry/skills/{entry.name}/ — vendored from "
                f"{entry.repo} @ {entry.upstream_ref}\n"
                f"# Source file: {candidate.relative_to(repo_root)}\n\n"
            )
            target.write_text(header + candidate.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  license:     registry/licenses/{entry.name}.LICENSE ({candidate.name})")
            return
    print(
        f"  #FALLBACK: no LICENSE file found upstream for {entry.name!r} — "
        "verify redistribution terms manually and record them",
        file=sys.stderr,
    )


def vendor(entry: CatalogEntry, *, force: bool = False) -> int:
    with tempfile.TemporaryDirectory(prefix="abstractskill-vendor-") as tmp:
        workdir = Path(tmp)
        print(f"fetching {entry.repo} @ {entry.upstream_ref[:12]}…")
        repo_root = _fetch_pinned(entry, workdir)
        src = (repo_root / entry.subdir).resolve()
        # Containment: the catalog validated subdir as traversal-free, but
        # resolve() re-checks against the real filesystem (defense in depth).
        if src == repo_root.resolve():
            raise SystemExit(
                "subdir must name a skill directory INSIDE the repo, never the repo "
                "root ('.') — a root vendor would carry the whole repository"
            )
        if not src.is_dir() or repo_root.resolve() not in src.parents:
            raise SystemExit(f"subdir {entry.subdir!r} not found inside the fetched repo")

        staged = workdir / "staged" / entry.name
        _copy_tree_no_symlinks(src, staged)

        skill_md = staged / "SKILL.md"
        if not skill_md.is_file():
            raise SystemExit(f"no SKILL.md at {entry.subdir!r} — wrong subdir or upstream moved it")
        try:
            document = parse_skill_md(skill_md.read_text(encoding="utf-8"))
        except SkillError as exc:
            raise SystemExit(f"upstream SKILL.md fails the spec validator: {exc}") from exc
        if document.metadata.name != entry.name:
            raise SystemExit(
                f"frontmatter name {document.metadata.name!r} != catalog name {entry.name!r} — "
                "the catalog name must be the spec name (fix the catalog, never the bytes)"
            )

        tree_hash = hash_skill_tree(staged)
        inventory = inspect_skill_dir(staged)
        if entry.expected_tree_hash and tree_hash != entry.expected_tree_hash:
            raise SystemExit(
                "TREE HASH MISMATCH — refusing to vendor.\n"
                f"  expected: {entry.expected_tree_hash}\n"
                f"  fetched:  {tree_hash}\n"
                "Upstream bytes changed at the pinned commit's path (or the pin was "
                "edited). Re-review the diff, then update expected_tree_hash deliberately."
            )

        dest = SHELF / entry.name
        already_identical = dest.exists() and _trees_identical(staged, dest)
        if dest.exists() and not already_identical:
            if not force:
                raise SystemExit(
                    f"{dest.relative_to(REPO)} exists with DIFFERENT bytes — re-vendors must "
                    "be reviewed; rerun with --force after reviewing the diff"
                )
            shutil.rmtree(dest)
        if not already_identical:
            shutil.copytree(staged, dest)

        # License text travels with vendored byte-copies (MIT/Apache require
        # the notice to accompany copies) — written OUT-OF-TREE so the
        # whole-tree hash covers only upstream skill bytes.
        _vendor_license(entry, src, repo_root)
        if already_identical:
            print(f"shelf copy already identical: {dest.relative_to(REPO)} (nothing to do)")
            return 0

        print(f"vendored {entry.name} -> {dest.relative_to(REPO)}")
        print(f"  tree_hash:   {tree_hash}")
        print(f"  has_scripts: {inventory.has_scripts}"
              + ("  (requires_review at the gate until operator-enabled)" if inventory.has_scripts else ""))
        if not entry.expected_tree_hash:
            print(
                "\nFIRST VENDORING — after reviewing the vendored diff, pin it in "
                "registry/catalog.yaml:\n"
                f"  [{entry.name}] expected_tree_hash: {tree_hash}\n"
                f"  [{entry.name}] vendored: true"
            )
        # The validation record DERIVES from the catalog entry — never add a
        # SHELF_POLICY entry for a catalog skill (refresh_shelf refuses the
        # collision; a hand-written policy would drop the pin cross-check).
        print(
            "\nNEXT: python scripts/refresh_shelf.py  (the validation record derives "
            "from the catalog entry; manual-review → adopted)\n"
            "THEN: update the admission pins in tests/test_shelf.py (EXPECTED_SHELF/"
            "EXPECTED_LEVELS — they are the review's second signature) and run pytest."
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", nargs="?", help="catalog entry name to vendor")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--list", action="store_true", help="list catalog entries")
    parser.add_argument("--force", action="store_true",
                        help="replace an existing differing shelf copy (after review)")
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    shelf_names = [p.name for p in SHELF.iterdir() if p.is_dir()] if SHELF.is_dir() else []
    for warning in lint_catalog(catalog, shelf_names):
        print(warning, file=sys.stderr)

    if args.list or not args.name:
        for entry in catalog.entries:
            state = "vendored" if entry.vendored else "not vendored"
            print(f"{entry.name:32} {entry.risk:8} {entry.license:12} {state}  ({entry.source})")
        return 0

    entry = catalog.get(args.name)
    if entry is None:
        raise SystemExit(
            f"{args.name!r} is not in the curated catalog — curated-only is structural; "
            "add a reviewed entry to registry/catalog.yaml first"
        )
    return vendor(entry, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
