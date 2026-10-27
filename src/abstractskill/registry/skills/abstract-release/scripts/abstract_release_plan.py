#!/usr/bin/env python3
"""Plan an AbstractFramework release wave from local package metadata.

Read-only. Discovers the workspace's Python, npm and Rust packages, extracts the
internal dependencies between them, checks git status per package, and prints a
deterministic release order, the dirty/downstream release wave, the dependency
floors to review, root profile pin drift, and inventory gaps.

Discovery:
- When the workspace has scripts/lib/packages.txt (the inventory the workspace
  scripts read), the packages are the inventory rows: one manifest per row at
  <repo>/<path>. Manifests tracked in the inventory's repositories but missing
  from the inventory, and sibling AbstractFramework repositories the inventory
  does not list, are reported as inventory gaps.
- Without the inventory, the planner walks the workspace (skipping untracked/,
  virtualenvs, node_modules, build output) and fails on duplicate package names
  instead of silently picking one copy.

Release signals per package: uncommitted changes, commits touching the package
since its last local release tag, a version with no local tag, and with
--registry a version missing from PyPI / npm / crates.io.

Runs from any working directory. Needs Python 3.11+ (tomllib) or the tomli
backport on older interpreters.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - depends on the interpreter
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


IGNORE_PARTS = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site",
    "site-packages",
    "target",
    "untracked",
    "venv",
}

IGNORE_SUFFIXES = ("-backup", "-gh-pages")

# Local experiment folders that are not released with the framework.
TEST_PROJECT_KEYS = {
    "abstractaudio",
    "abstractsound",
    "abstractvideo",
    "abstractcognition",
    "abstractgeometry",
    "abstractspatial",
}

# Tie-break rank inside the dependency order (ADR-0034 tiers). The real order
# comes from the dependency edges; the rank only orders packages that are ready
# at the same time.
ADR_RANK = {
    # Tier 0: capability plugins, the skill shelf, AbstractUIC packages, TUI kit.
    "abstractvoice": 10,
    "abstractmusic": 10,
    "abstractvision": 10,
    "abstractcamera": 10,
    "abstract3d": 15,
    "abstractskill": 10,
    "abstracttui": 10,
    "abstracttuigraph": 10,
    "abstracttuimermaid": 10,
    "abstractframeworkabstractuicmonorepo": 10,
    "abstractframeworkuikit": 10,
    "abstractframeworkappserver": 10,
    "abstractframeworkmonitoractivememory": 10,
    "abstractframeworkmonitormemory": 10,
    "abstractframeworkmonitorflow": 10,
    "abstractframeworkmonitorgpu": 10,
    "abstractframeworkpanelchat": 10,
    # Schema, vocabulary, memory graph.
    "abstractsemantics": 20,
    "abstractmemory": 20,
    # Core execution layers.
    "abstractcore": 30,
    "abstractcoreconsole": 30,
    "abstractruntime": 40,
    "abstractagent": 50,
    "abstractgateway": 60,
    "abstractgatewayconsole": 60,
    # Apps on the gateway.
    "abstractassistant": 80,
    "abstractcode": 80,
    "abstractframeworkcode": 80,
    "abstractflow": 80,
    "abstractframeworkflow": 80,
    "abstractobserver": 80,
    "abstractframeworkobserver": 80,
    "abstractentity": 80,
    "abstractframeworkentity": 80,
    "abstractcontinuum": 80,
    "abstractframeworkcontinuum": 80,
    "abstractnote": 80,
    "abstractframeworknote": 80,
    # Root meta-package: pins the released matrix, so it comes last.
    "abstractframework": 90,
}

REQ_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.@/-]+)"
    r"(?:\[[^\]]+\])?"
    r"\s*(?P<op>===|==|~=|>=|<=|>|<|\^|~)?"
    r"\s*(?P<version>[A-Za-z0-9_.!+*~-]+)?"
)

SOURCE_SUFFIXES = {".cjs", ".cts", ".js", ".jsx", ".mjs", ".mts", ".ts", ".tsx"}
MANIFEST_NAMES = ("pyproject.toml", "package.json", "Cargo.toml")
INVENTORY_REL = Path("scripts") / "lib" / "packages.txt"


@dataclass
class InternalRequirement:
    target: str
    raw: str
    group: str
    operator: Optional[str] = None
    version: Optional[str] = None


@dataclass
class Package:
    name: str
    key: str
    ecosystem: str
    path: Path
    manifest: Path
    version: Optional[str]
    private: bool = False
    git_root: Optional[Path] = None
    git_status: List[str] = field(default_factory=list)
    internal_requirements: List[InternalRequirement] = field(default_factory=list)
    inventory_id: Optional[str] = None
    last_tag: Optional[str] = None
    commits_since_tag: Optional[int] = None
    version_tagged: Optional[bool] = None
    published: Optional[bool] = None  # None = not checked (--registry not given)

    @property
    def dirty(self) -> bool:
        return bool(self.git_status)

    def change_reasons(self) -> List[str]:
        """Why this package needs a release (empty = nothing pending)."""
        reasons = []
        if self.dirty:
            reasons.append(f"{len(self.git_status)} uncommitted change(s)")
        if self.commits_since_tag:
            reasons.append(f"{self.commits_since_tag} commit(s) since {self.last_tag}")
        if self.version_tagged is False:
            reasons.append(f"version {self.version} has no local tag")
        if self.published is False:
            reasons.append(f"version {self.version} is not on its registry")
        return reasons


class PlanError(Exception):
    pass


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def compact_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def load_toml(path: Path) -> Dict[str, Any]:
    if tomllib is None:
        raise PlanError("reading TOML needs Python 3.11+ (tomllib) or `pip install tomli`")
    with path.open("rb") as fh:
        return tomllib.load(fh)


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, check=False)


def should_skip(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    for part in rel.parts:
        if part in IGNORE_PARTS or part.endswith(IGNORE_SUFFIXES):
            return True
    return False


def find_workspace_root(start: Path) -> Optional[Path]:
    """Nearest ancestor of `start` (inclusive) holding scripts/lib/packages.txt."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / INVENTORY_REL).is_file():
            return candidate
    return None


def resolve_root(arg: Optional[str]) -> Path:
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("ABSTRACTFRAMEWORK_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    found = find_workspace_root(Path.cwd())
    if found is None:
        raise PlanError(
            f"no AbstractFramework workspace above {Path.cwd()} (no scripts/lib/packages.txt); "
            "pass the workspace root, or set ABSTRACTFRAMEWORK_ROOT"
        )
    return found


# --------------------------------------------------------------------------
# Git
# --------------------------------------------------------------------------
_GIT_ROOTS: Dict[Path, Optional[Path]] = {}
_REPO_FILES: Dict[Path, List[str]] = {}


def git_root_for(path: Path) -> Optional[Path]:
    path = path.resolve()
    if path not in _GIT_ROOTS:
        proc = run(["git", "rev-parse", "--show-toplevel"], path)
        out = proc.stdout.strip() if proc.returncode == 0 else ""
        _GIT_ROOTS[path] = Path(out).resolve() if out else None
    return _GIT_ROOTS[path]


def repo_files(git_root: Path) -> List[str]:
    """Tracked plus untracked-but-not-ignored files of a repository (relative paths)."""
    if git_root not in _REPO_FILES:
        proc = run(["git", "ls-files", "-co", "--exclude-standard", "-z"], git_root)
        files = [f for f in proc.stdout.split("\0") if f] if proc.returncode == 0 else []
        _REPO_FILES[git_root] = files
    return _REPO_FILES[git_root]


def git_origin(repo_dir: Path) -> Optional[str]:
    proc = run(["git", "remote", "get-url", "origin"], repo_dir)
    if proc.returncode != 0:
        return None
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", proc.stdout.strip())
    return match.group(1) if match else proc.stdout.strip()


def git_status_for(path: Path, git_root: Optional[Path], ignored_prefixes: Set[str]) -> List[str]:
    if git_root is None:
        return []
    try:
        rel = path.resolve().relative_to(git_root)
    except ValueError:
        rel = Path(".")
    target = "." if str(rel) == "." else str(rel)
    proc = run(["git", "status", "--short", "--", target], git_root)
    if proc.returncode != 0:
        return [f"?? git-status-failed: {proc.stderr.strip()}"]
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if not ignored_prefixes:
        return lines
    rel_prefix = "" if target == "." else target.rstrip("/") + "/"
    filtered = []
    for line in lines:
        status_path = line[3:] if len(line) > 3 else line
        inner = status_path[len(rel_prefix):] if rel_prefix and status_path.startswith(rel_prefix) else status_path
        if any(inner == p or inner.startswith(p + "/") for p in ignored_prefixes):
            continue
        filtered.append(line)
    return filtered


# --------------------------------------------------------------------------
# Manifests
# --------------------------------------------------------------------------
def resolve_dynamic_version(project_root: Path, data: Dict[str, Any]) -> Optional[str]:
    dynamic = (data.get("tool") or {}).get("setuptools", {}).get("dynamic", {})
    attr = (dynamic.get("version") or {}).get("attr")
    if not isinstance(attr, str) or "." not in attr:
        return None
    module_name, attr_name = attr.rsplit(".", 1)
    module_path = Path(*module_name.split("."))
    candidates = [
        project_root / f"{module_path}.py",
        project_root / module_path / "__init__.py",
        project_root / "src" / f"{module_path}.py",
        project_root / "src" / module_path / "__init__.py",
    ]
    pattern = re.compile(rf"^\s*{re.escape(attr_name)}\s*(?::\s*str\s*)?=\s*['\"]([^'\"]+)['\"]", re.M)
    for candidate in candidates:
        if candidate.exists():
            match = pattern.search(candidate.read_text(encoding="utf-8", errors="replace"))
            if match:
                return match.group(1)
    return None


def package_from_manifest(manifest: Path) -> Optional[Package]:
    manifest = manifest.resolve()
    if manifest.name == "pyproject.toml":
        data = load_toml(manifest)
        project = data.get("project") or {}
        name = project.get("name")
        if not isinstance(name, str) or not name.strip():
            return None
        version = project.get("version")
        if not isinstance(version, str):
            version = resolve_dynamic_version(manifest.parent, data)
        return Package(name.strip(), compact_name(name), "python", manifest.parent, manifest, version)
    if manifest.name == "package.json":
        data = read_json(manifest)
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            return None
        version = data.get("version")
        return Package(
            name.strip(), compact_name(name), "npm", manifest.parent, manifest,
            version if isinstance(version, str) else None, private=bool(data.get("private")),
        )
    if manifest.name == "Cargo.toml":
        data = load_toml(manifest)
        pkg = data.get("package") or {}
        name = pkg.get("name")
        if not isinstance(name, str) or not name.strip():
            return None
        version = pkg.get("version")
        return Package(
            name.strip(), compact_name(name), "crates", manifest.parent, manifest,
            version if isinstance(version, str) else None,
        )
    return None


# --------------------------------------------------------------------------
# Inventory (scripts/lib/packages.txt)
# --------------------------------------------------------------------------
@dataclass
class InventoryRow:
    id: str
    repo: str
    github: str
    kind: str
    path: str
    registry: str
    name: str
    deps: List[Tuple[str, str]] = field(default_factory=list)

    def directory(self, root: Path) -> Path:
        base = root if self.repo == "." else root / self.repo
        return base if self.path == "." else base / self.path

    def manifest(self, root: Path) -> Path:
        filename = {"python": "pyproject.toml", "meta": "pyproject.toml", "npm": "package.json", "rust": "Cargo.toml"}
        return self.directory(root) / filename[self.kind]


def load_inventory(root: Path) -> Optional[List[InventoryRow]]:
    path = root / INVENTORY_REL
    if not path.is_file():
        return None
    rows: List[InventoryRow] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) != 9:
            raise PlanError(f"{path}:{lineno}: expected 9 '|'-separated columns, got {len(cols)}")
        pid, repo, github, kind, ppath, registry, name, _tier, deps = cols
        if kind not in ("python", "meta", "npm", "rust"):
            raise PlanError(f"{path}:{lineno}: unknown kind {kind!r}")
        edges = [] if deps == "-" else [tuple(item.strip().partition(":")[::2]) for item in deps.split(",")]
        rows.append(InventoryRow(pid, repo, github, kind, ppath, registry, name, edges))
    return rows


def discover_from_inventory(root: Path, rows: List[InventoryRow]) -> Tuple[List[Package], List[Dict[str, Any]]]:
    packages: List[Package] = []
    gaps: List[Dict[str, Any]] = []
    listed_manifests: Set[Path] = set()
    for row in rows:
        manifest = row.manifest(root)
        listed_manifests.add(manifest.resolve() if manifest.exists() else manifest)
        if not manifest.is_file():
            gaps.append({"kind": "not_cloned", "id": row.id, "detail": f"{manifest} is missing (run scripts/clone.sh)"})
            continue
        pkg = package_from_manifest(manifest)
        if pkg is None:
            gaps.append({"kind": "unreadable", "id": row.id, "detail": f"{manifest} has no package name"})
            continue
        if compact_name(pkg.name) != compact_name(row.name):
            gaps.append({
                "kind": "name_mismatch", "id": row.id,
                "detail": f"{manifest} declares {pkg.name!r}, packages.txt says {row.name!r}",
            })
        pkg.inventory_id = row.id
        packages.append(pkg)

    # Manifests tracked in the inventory's repositories that no row lists.
    repos = sorted({row.repo for row in rows})
    for repo in repos:
        repo_dir = root if repo == "." else root / repo
        git_root = git_root_for(repo_dir) if repo_dir.is_dir() else None
        if git_root is None or git_root != repo_dir.resolve():
            continue
        for rel in repo_files(git_root):
            rel_path = Path(rel)
            if rel_path.name not in MANIFEST_NAMES:
                continue
            manifest = (git_root / rel_path).resolve()
            if manifest in listed_manifests or should_skip(manifest, git_root):
                continue
            if any(part in ("tests", "test", "fixtures", "examples", "docs") for part in rel_path.parts[:-1]):
                continue
            try:
                pkg = package_from_manifest(manifest)
            except (PlanError, ValueError, json.JSONDecodeError):
                pkg = None
            if pkg is None or pkg.private:
                continue
            gaps.append({
                "kind": "package_not_in_inventory", "id": None,
                "detail": f"{pkg.name} {pkg.version or ''} ({pkg.ecosystem}) at {manifest.parent} is not in packages.txt",
            })

    # Sibling AbstractFramework repositories the inventory does not list.
    listed_repos = {row.repo for row in rows}
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name in listed_repos or child.name.endswith(IGNORE_SUFFIXES):
            continue
        if not (child / ".git").exists():
            continue
        origin = git_origin(child) or ""
        if re.match(r"(?i)^lpalbou/abstract", origin):
            gaps.append({
                "kind": "repo_not_in_inventory", "id": None,
                "detail": f"{child.name}/ (origin {origin}) is an AbstractFramework repository missing from packages.txt",
            })
    return packages, gaps


def discover_by_walking(root: Path) -> List[Package]:
    found: Dict[str, List[Package]] = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [d for d in dirnames if d not in IGNORE_PARTS and not d.endswith(IGNORE_SUFFIXES)]
        for filename in MANIFEST_NAMES:
            if filename in filenames:
                pkg = package_from_manifest(current / filename)
                if pkg and pkg.key not in TEST_PROJECT_KEYS:
                    found[pkg.key].append(pkg)
    duplicates = {k: v for k, v in found.items() if len(v) > 1}
    if duplicates:
        lines = [f"  {v[0].name}: " + ", ".join(str(p.path) for p in v) for v in duplicates.values()]
        raise PlanError(
            "several copies of the same package were found; pass the workspace root that holds "
            "scripts/lib/packages.txt, or remove the stray copies:\n" + "\n".join(lines)
        )
    return [v[0] for v in found.values()]


# --------------------------------------------------------------------------
# Dependencies
# --------------------------------------------------------------------------
def known_dependency_keys(packages: List[Package]) -> Dict[str, str]:
    known: Dict[str, str] = {}
    for pkg in packages:
        known[pkg.key] = pkg.key
        if pkg.ecosystem == "npm" and pkg.name.startswith("@"):
            _, _, scoped_name = pkg.name.partition("/")
            if scoped_name:
                known.setdefault(compact_name(scoped_name), pkg.key)
    return known


def parse_requirement(raw: str, group: str, known: Dict[str, str]) -> Optional[InternalRequirement]:
    match = REQ_RE.match(raw)
    if not match:
        return None
    dep_name = match.group("name")
    target = known.get(compact_name(dep_name))
    if not target and "/" in dep_name:
        target = known.get(compact_name(dep_name.split("/")[-1]))
    if not target:
        return None
    return InternalRequirement(target, raw, group, match.group("op"), match.group("version"))


def add_internal_requirement(pkg: Package, req: Optional[InternalRequirement]) -> None:
    if not req or req.target == pkg.key:
        return
    if (req.target, req.group, req.raw) not in {(r.target, r.group, r.raw) for r in pkg.internal_requirements}:
        pkg.internal_requirements.append(req)


def package_source_files(pkg: Package) -> List[Path]:
    git_root = pkg.git_root
    if git_root is not None:
        try:
            prefix = pkg.path.relative_to(git_root)
        except ValueError:
            prefix = None
        if prefix is not None:
            files = []
            for rel in repo_files(git_root):
                rel_path = Path(rel)
                if rel_path.suffix not in SOURCE_SUFFIXES:
                    continue
                if str(prefix) != "." and prefix not in rel_path.parents:
                    continue
                full = git_root / rel_path
                if not should_skip(full, pkg.path):
                    files.append(full)
            return sorted(files)
    files = []
    for dirpath, dirnames, filenames in os.walk(pkg.path):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_PARTS and not d.endswith(IGNORE_SUFFIXES)]
        files.extend(Path(dirpath) / f for f in filenames if Path(f).suffix in SOURCE_SUFFIXES)
    return sorted(files)


def source_import_requirements(pkg: Package, packages: List[Package]) -> List[InternalRequirement]:
    if pkg.ecosystem != "npm":
        return []
    others = [o for o in packages if o.ecosystem == "npm" and o.key != pkg.key]
    if not others:
        return []
    matched: Dict[str, str] = {}
    for source in package_source_files(pkg):
        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for other in others:
            if other.name in text:
                matched[other.name] = other.key
    return [
        InternalRequirement(target, f"{name} (source import or build alias)", "source")
        for name, target in sorted(matched.items())
    ]


def collect_requirements(
    packages: List[Package], rows: Optional[List[InventoryRow]] = None, root: Optional[Path] = None
) -> None:
    """Internal requirements from the manifests.

    Source-level dependencies (a Vite alias to a sibling AbstractUIC checkout) are
    not in any manifest. With the inventory, they come from its `alias` edges,
    which `scripts/deps.sh check` verifies against the vite configs; without it,
    from a text scan of the package sources for sibling npm package names.
    """
    known = known_dependency_keys(packages)
    by_id = {p.inventory_id: p for p in packages if p.inventory_id}
    for pkg in packages:
        raw_groups: List[Tuple[str, str]] = []
        if pkg.ecosystem == "python":
            project = load_toml(pkg.manifest).get("project") or {}
            raw_groups.extend(("dependencies", dep) for dep in project.get("dependencies") or [])
            for extra, deps in (project.get("optional-dependencies") or {}).items():
                raw_groups.extend((f"optional:{extra}", dep) for dep in deps or [])
        elif pkg.ecosystem == "npm":
            data = read_json(pkg.manifest)
            for group in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                deps = data.get(group) or {}
                if isinstance(deps, dict):
                    raw_groups.extend((group, f"{name}{spec}") for name, spec in deps.items())
        elif pkg.ecosystem == "crates":
            data = load_toml(pkg.manifest)
            for name, spec in (data.get("dependencies") or {}).items():
                version = spec if isinstance(spec, str) else (spec.get("version") if isinstance(spec, dict) else None)
                raw_groups.append(("dependencies", f"{name}{'>=' + version if version else ''}"))
        for group, raw in raw_groups:
            req = parse_requirement(raw, group, known)
            # A crate only depends on crates; a Python/npm name that compacts to a
            # crate name (or the reverse) is a different package.
            if req and (pkg.ecosystem == "crates") != (by_key_ecosystem(packages, req.target) == "crates"):
                continue
            add_internal_requirement(pkg, req)
        if rows is None:
            for req in source_import_requirements(pkg, packages):
                add_internal_requirement(pkg, req)
    # The root meta-package also pins npm apps and crates in abstractframework/__init__.py;
    # those pins are edges too (an app release must reach the root profile).
    framework = next((p for p in packages if p.key == "abstractframework"), None)
    if framework is not None:
        init_path = framework.path / "abstractframework" / "__init__.py"
        by_key = {p.key: p for p in packages}
        for var in ("NPM_RELEASE_VERSIONS", "CRATE_RELEASE_VERSIONS"):
            for key, version in parse_version_dict(init_path, var).items():
                if key in by_key:
                    add_internal_requirement(
                        framework, InternalRequirement(key, f"{by_key[key].name}=={version}", var, "==", version)
                    )
    if rows is None:
        return
    for row in rows:
        pkg = by_id.get(row.id)
        if pkg is None:
            continue
        for dep_id, edge_kind in row.deps:
            target = by_id.get(dep_id)
            if edge_kind == "alias" and target is not None:
                add_internal_requirement(
                    pkg, InternalRequirement(target.key, f"{target.name} (Vite source alias)", "alias")
                )


def by_key_ecosystem(packages: List[Package], key: str) -> Optional[str]:
    for pkg in packages:
        if pkg.key == key:
            return pkg.ecosystem
    return None


def collect_git_status(packages: List[Package]) -> None:
    for pkg in packages:
        pkg.git_root = git_root_for(pkg.path)
    for pkg in packages:
        if not pkg.git_root:
            continue
        # Changes inside another package's directory (or another repository nested
        # under this one) belong to that package, not this one.
        ignored: Set[str] = set()
        for other in packages:
            if other is pkg:
                continue
            try:
                rel = other.path.relative_to(pkg.path)
            except ValueError:
                continue
            if rel.parts:
                ignored.add(str(rel))
        pkg.git_status = git_status_for(pkg.path, pkg.git_root, ignored)


def _tag_patterns(pkg: Package) -> List[str]:
    """Release tags that cover this package, most specific first.

    A package in a sub-directory may have its own tag family (`web-v*` for
    AbstractCode's web app); otherwise the repository's `v*` tags cover it.
    """
    patterns = []
    if pkg.git_root and pkg.path != pkg.git_root:
        patterns.append(f"{pkg.path.name}-v*")
    patterns.append("v*")
    return patterns


def collect_tag_signals(packages: List[Package]) -> None:
    """Commits touching the package since its last release tag (local tags only)."""
    for pkg in packages:
        if not pkg.git_root:
            continue
        rel = pkg.path.relative_to(pkg.git_root)
        tag = None
        for pattern in _tag_patterns(pkg):
            proc = run(["git", "describe", "--tags", "--abbrev=0", "--match", pattern, "HEAD"], pkg.git_root)
            if proc.returncode == 0 and proc.stdout.strip():
                tag = proc.stdout.strip()
                break
        excludes = []
        for other in packages:
            if other is pkg or other.git_root != pkg.git_root:
                continue
            try:
                sub = other.path.relative_to(pkg.path)
            except ValueError:
                continue
            if sub.parts:
                excludes.append(f":(exclude){(rel / sub).as_posix()}")
        pathspec = [rel.as_posix() if str(rel) != "." else "."] + excludes
        if tag:
            proc = run(["git", "rev-list", "--count", f"{tag}..HEAD", "--", *pathspec], pkg.git_root)
            pkg.last_tag = tag
            pkg.commits_since_tag = int(proc.stdout.strip() or 0) if proc.returncode == 0 else None
        if pkg.version and pkg.path == pkg.git_root:
            prefix = "v"
            proc = run(["git", "tag", "-l", f"{prefix}{pkg.version}"], pkg.git_root)
            pkg.version_tagged = bool(proc.stdout.strip()) if proc.returncode == 0 else None


def registry_has_version(pkg: Package, timeout: float = 15.0) -> Optional[bool]:
    import urllib.error
    import urllib.parse
    import urllib.request

    if not pkg.version or pkg.private:
        return None
    if pkg.ecosystem == "python":
        url = f"https://pypi.org/pypi/{urllib.parse.quote(pkg.name)}/{urllib.parse.quote(pkg.version)}/json"
    elif pkg.ecosystem == "npm":
        url = f"https://registry.npmjs.org/{urllib.parse.quote(pkg.name, safe='@').replace('/', '%2F')}/{urllib.parse.quote(pkg.version)}"
    else:
        url = f"https://crates.io/api/v1/crates/{urllib.parse.quote(pkg.name)}/{urllib.parse.quote(pkg.version)}"
    req = urllib.request.Request(url, headers={"User-Agent": "abstract-release-plan/2", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout):  # noqa: S310 (fixed https hosts)
            return True
    except urllib.error.HTTPError as exc:
        return False if exc.code == 404 else None
    except Exception:  # network down: unknown, never "unpublished"
        return None


def collect_registry_signals(packages: List[Package]) -> None:
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for pkg, published in zip(packages, pool.map(registry_has_version, packages)):
            pkg.published = published


def changes_outside_packages(packages: List[Package]) -> List[Dict[str, Any]]:
    """Uncommitted changes in a package repository that no package directory owns
    (for example AbstractUIC's root package.json and lockfile)."""
    out = []
    roots = sorted({p.git_root for p in packages if p.git_root})
    for git_root in roots:
        owners = [p.path for p in packages if p.git_root == git_root]
        if git_root in owners:
            continue  # the repository root is itself a package: it owns the rest
        lines = []
        for line in git_status_for(git_root, git_root, set()):
            rel = line[3:].split(" -> ")[-1]
            full = git_root / rel
            if not any(full == o or o in full.parents for o in owners):
                lines.append(line)
        if lines:
            out.append({"repository": str(git_root), "changes": lines})
    return out


def discover(root: Path) -> Tuple[List[Package], List[Dict[str, Any]], str]:
    root = root.resolve()
    rows = load_inventory(root)
    if rows is not None:
        packages, gaps = discover_from_inventory(root, rows)
        source = str(root / INVENTORY_REL)
    else:
        packages, gaps = discover_by_walking(root), []
        source = "filesystem walk (no scripts/lib/packages.txt)"
    keys: Dict[str, Package] = {}
    for pkg in packages:
        if pkg.key in keys:
            raise PlanError(f"duplicate package {pkg.name}: {keys[pkg.key].path} and {pkg.path}")
        keys[pkg.key] = pkg
    collect_git_status(packages)
    collect_tag_signals(packages)
    collect_requirements(packages, rows, root)
    return sorted(packages, key=lambda p: (rank(p.key), p.name.lower(), str(p.path))), gaps, source


# --------------------------------------------------------------------------
# Ordering and the wave
# --------------------------------------------------------------------------
def rank(key: str) -> int:
    return ADR_RANK.get(key, 90)


def topological_order(packages: List[Package]) -> List[Package]:
    by_key = {p.key: p for p in packages}
    dependents: Dict[str, Set[str]] = defaultdict(set)
    indegree: Dict[str, int] = {p.key: 0 for p in packages}
    for pkg in packages:
        for req in pkg.internal_requirements:
            if req.target in by_key and pkg.key not in dependents[req.target]:
                dependents[req.target].add(pkg.key)
                indegree[pkg.key] += 1

    def sort_key(k: str) -> Tuple[int, str]:
        return (rank(k), by_key[k].name.lower())

    ready = sorted((k for k, deg in indegree.items() if deg == 0), key=sort_key)
    ordered: List[str] = []
    while ready:
        key = ready.pop(0)
        ordered.append(key)
        for dep in sorted(dependents.get(key, ()), key=sort_key):
            indegree[dep] -= 1
            if indegree[dep] == 0:
                ready.append(dep)
                ready.sort(key=sort_key)
    if len(ordered) != len(packages):  # a cycle: append the rest by rank
        ordered.extend(sorted((k for k in indegree if k not in ordered), key=sort_key))
    return [by_key[k] for k in ordered]


def release_wave(ordered: List[Package]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    by_key = {p.key: p for p in ordered}
    direct_dependents: Dict[str, Set[str]] = defaultdict(set)
    for pkg in ordered:
        for req in pkg.internal_requirements:
            direct_dependents[req.target].add(pkg.key)

    selected: Dict[str, str] = {}
    changed: Set[str] = set()
    for p in ordered:
        reasons = p.change_reasons()
        if reasons:
            selected[p.key] = "; ".join(reasons)
            changed.add(p.key)
    queue = list(selected)
    while queue:
        key = queue.pop(0)
        for dep in sorted(direct_dependents.get(key, ())):
            if dep not in selected:
                selected[dep] = f"floor review only: downstream of {by_key[key].name}"
                queue.append(dep)

    wave = [
        {
            "order": index,
            "package": pkg.name,
            "key": pkg.key,
            "inventory_id": pkg.inventory_id,
            "ecosystem": pkg.ecosystem,
            "version": pkg.version,
            "path": str(pkg.path),
            "reason": selected[pkg.key],
            "changed": pkg.key in changed,
            "dirty": pkg.dirty,
        }
        for index, pkg in enumerate(ordered, 1)
        if pkg.key in selected
    ]

    floor_reviews = []
    seen: Set[Tuple[str, str, str, str]] = set()
    for pkg in ordered:
        if pkg.key not in selected:
            continue
        for req in pkg.internal_requirements:
            if req.target not in selected:
                continue
            review_key = (pkg.key, req.target, req.group, req.raw)
            if review_key in seen:
                continue
            seen.add(review_key)
            target = by_key.get(req.target)
            floor_reviews.append({
                "package": pkg.name,
                "depends_on": target.name if target else req.target,
                "declared": req.raw,
                "group": req.group,
                "target_local_version": target.version if target else None,
                "action": "raise or confirm dependency floor after lower package is published",
            })
    return wave, floor_reviews


def parse_version_dict(init_path: Path, var: str) -> Dict[str, str]:
    if not init_path.exists():
        return {}
    text = init_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf"^{var}\s*(?::\s*dict\[.*?\])?\s*=\s*\{{(?P<body>.*?)\n\}}", text, re.S | re.M)
    if not match:
        return {}
    pairs = re.findall(r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]+)['\"]", match.group("body"))
    return {compact_name(name): version for name, version in pairs}


def profile_pin_reviews(root: Path, ordered: List[Package]) -> List[Dict[str, Any]]:
    by_key = {p.key: p for p in ordered}
    framework = by_key.get("abstractframework")
    if not framework:
        return []
    reviews: List[Dict[str, Any]] = []
    for req in framework.internal_requirements:
        target = by_key.get(req.target)
        if not target or req.operator not in {"==", "==="} or req.group.endswith("RELEASE_VERSIONS"):
            continue
        reviews.append({
            "source": str(framework.manifest),
            "field": req.group,
            "package": target.name,
            "declared": req.raw,
            "declared_version": req.version,
            "local_version": target.version,
            "status": "ok" if req.version == target.version else "drift",
        })
    init_path = root / "abstractframework" / "__init__.py"
    for var in ("RELEASE_VERSIONS", "NPM_RELEASE_VERSIONS", "CRATE_RELEASE_VERSIONS"):
        for key, version in sorted(parse_version_dict(init_path, var).items()):
            target = by_key.get(key)
            if not target:
                continue
            reviews.append({
                "source": str(init_path),
                "field": var,
                "package": target.name,
                "declared": f"{target.name}=={version}",
                "declared_version": version,
                "local_version": target.version,
                "status": "ok" if version == target.version else "drift",
            })
    return reviews


def to_data(
    root: Path, packages: List[Package], gaps: List[Dict[str, Any]], source: str, registry_checked: bool = False
) -> Dict[str, Any]:
    ordered = topological_order(packages)
    wave, floor_reviews = release_wave(ordered)
    names = {p.key: p.name for p in ordered}
    return {
        "workspace": str(root.resolve()),
        "inventory": source,
        "registry_checked": registry_checked,
        "package_count": len(ordered),
        "ordered_packages": [
            {
                "order": i,
                "package": p.name,
                "key": p.key,
                "inventory_id": p.inventory_id,
                "ecosystem": p.ecosystem,
                "version": p.version,
                "private": p.private,
                "path": str(p.path),
                "manifest": str(p.manifest),
                "rank": rank(p.key),
                "git_root": str(p.git_root) if p.git_root else None,
                "dirty": p.dirty,
                "git_status": p.git_status,
                "last_tag": p.last_tag,
                "commits_since_tag": p.commits_since_tag,
                "version_tagged": p.version_tagged,
                "published": p.published,
                "change_reasons": p.change_reasons(),
                "internal_dependencies": [
                    {"target": r.target, "name": names.get(r.target, r.target), "raw": r.raw, "group": r.group,
                     "operator": r.operator, "version": r.version}
                    for r in p.internal_requirements
                ],
            }
            for i, p in enumerate(ordered, 1)
        ],
        "release_wave": wave,
        "dependency_floor_reviews": floor_reviews,
        "profile_pin_reviews": profile_pin_reviews(root.resolve(), ordered),
        "inventory_gaps": gaps,
        "changes_outside_packages": changes_outside_packages(ordered),
    }


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------
def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def render_markdown(data: Dict[str, Any]) -> str:
    lines = [
        "# AbstractFramework Release Plan",
        "",
        f"- Workspace: `{data['workspace']}`",
        f"- Inventory: `{data['inventory']}`",
        f"- Packages: {data['package_count']}",
        "- Registry versions: " + ("checked (--registry)" if data.get("registry_checked")
                                    else "not checked (add --registry to flag local versions missing from PyPI/npm/crates.io)"),
        "- Release signals: uncommitted changes, commits since the package's last local release tag "
        "(run `git fetch --tags` first), a version with no local tag, a version missing from its registry.",
        "",
        "## Release Wave",
        "",
    ]
    wave = data["release_wave"]
    if not wave:
        lines.append("No dirty packages or downstream dependents were detected.")
    else:
        lines += ["| Order | Package | Version | Kind | Dirty | Reason | Path |", "|---:|---|---|---|---|---|---|"]
        for item in wave:
            lines.append(
                f"| {item['order']} | {md_escape(item['package'])} | {md_escape(item['version'])} | "
                f"{item['ecosystem']} | {'yes' if item['dirty'] else 'no'} | {md_escape(item['reason'])} | "
                f"`{md_escape(item['path'])}` |"
            )

    lines += ["", "## Dependency Floor Reviews", ""]
    reviews = data["dependency_floor_reviews"]
    if not reviews:
        lines.append("No internal dependency floor reviews were detected for the current wave.")
    else:
        lines += ["| Package | Group | Depends On | Declared | Target Local Version |", "|---|---|---|---|---|"]
        for item in reviews:
            lines.append(
                f"| {md_escape(item['package'])} | {md_escape(item['group'])} | {md_escape(item['depends_on'])} | "
                f"`{md_escape(item['declared'])}` | {md_escape(item['target_local_version'])} |"
            )

    lines += ["", "## Root Profile Pin Reviews", ""]
    profile_reviews = data.get("profile_pin_reviews") or []
    if not profile_reviews:
        lines.append("No root profile pin reviews were detected.")
    else:
        drift = sum(1 for r in profile_reviews if r["status"] == "drift")
        lines.append(f"{drift} of {len(profile_reviews)} root pins differ from the local package versions.")
        lines += ["", "| Status | Field | Package | Declared | Local Version |", "|---|---|---|---|---|"]
        for item in profile_reviews:
            lines.append(
                f"| {md_escape(item['status'])} | {md_escape(item['field'])} | {md_escape(item['package'])} | "
                f"`{md_escape(item['declared'])}` | {md_escape(item['local_version'])} |"
            )

    lines += ["", "## Changes Outside Any Package", ""]
    outside = data.get("changes_outside_packages") or []
    if not outside:
        lines.append("None.")
    else:
        for item in outside:
            lines.append(f"- `{item['repository']}`: " + ", ".join(f"`{md_escape(c)}`" for c in item["changes"][:8])
                         + (" ..." if len(item["changes"]) > 8 else ""))

    lines += ["", "## Inventory Gaps", ""]
    gaps = data.get("inventory_gaps") or []
    if not gaps:
        lines.append("None: every package found in the framework repositories is in the inventory.")
    else:
        for gap in gaps:
            lines.append(f"- {gap['kind']}: {md_escape(gap['detail'])}")

    lines += ["", "## Ordered Package Inventory", ""]
    lines += ["| Order | Package | Version | Kind | Dirty | Internal Dependencies |", "|---:|---|---|---|---|---|"]
    for item in data["ordered_packages"]:
        deps = ", ".join(sorted({dep["name"] for dep in item["internal_dependencies"]})) or "-"
        lines.append(
            f"| {item['order']} | {md_escape(item['package'])} | {md_escape(item['version'])} | "
            f"{item['ecosystem']} | {'yes' if item['dirty'] else 'no'} | {md_escape(deps)} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic AbstractFramework release plan (read-only).")
    parser.add_argument(
        "root", nargs="?", default=None,
        help="Workspace root. Default: $ABSTRACTFRAMEWORK_ROOT, else the nearest ancestor of the current "
             "directory holding scripts/lib/packages.txt.",
    )
    parser.add_argument("--registry", action="store_true",
                        help="Also check each local version on PyPI / npm / crates.io (network, read-only)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    parser.add_argument("--output", "-o", help="Write output to a file instead of stdout")
    args = parser.parse_args(argv)

    try:
        root = resolve_root(args.root)
        if not root.is_dir():
            raise PlanError(f"root does not exist: {root}")
        packages, gaps, source = discover(root)
    except PlanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.registry:
        collect_registry_signals(packages)
    data = to_data(root, packages, gaps, source, registry_checked=args.registry)
    text = json.dumps(data, indent=2, sort_keys=True) + "\n" if args.json else render_markdown(data)
    if args.output:
        Path(args.output).expanduser().write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
