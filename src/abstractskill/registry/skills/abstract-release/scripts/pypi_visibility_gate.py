#!/usr/bin/env python3
"""Check that released package versions are installable from their registry.

A release upload shows on the project page before every index pip or npm reads
has it. Raise a dependency floor only after this gate passes.

Usage:
  pypi_visibility_gate.py abstractcore==2.30.0 abstractruntime==0.13.1
  pypi_visibility_gate.py npm:@abstractframework/ui-kit==0.8.9 crates:abstracttui==0.6.0
  pypi_visibility_gate.py --wait 900 abstractvoice==0.19.1
  pypi_visibility_gate.py --from-plan plan.json        # the plan's changed packages (not floor-review-only)

PyPI: the version must be on the project JSON API AND on the simple index
(PEP 691 JSON), which is what pip resolves from. npm: the version must be in the
registry document npm resolves from. crates.io: the version exists and is not
yanked. Versions compare by release number (2.30 == 2.30.0). Exit code 0 only when every spec is
visible. Standard library only; runs from any working directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

USER_AGENT = "abstract-release-visibility-gate/2"


def parse_spec(spec: str) -> Tuple[str, str, str]:
    """`name==version` (PyPI) or `npm:@scope/name==version` -> (registry, name, version)."""
    registry = "pypi"
    for prefix in ("npm", "crates", "pypi"):
        if spec.startswith(prefix + ":"):
            registry, spec = prefix, spec[len(prefix) + 1:]
            break
    if "==" not in spec:
        raise ValueError(f"expected name==version (or npm:name==version), got {spec!r}")
    name, version = (part.strip() for part in spec.split("==", 1))
    if not name or not version:
        raise ValueError(f"expected name==version, got {spec!r}")
    return registry, name, version


def specs_from_plan(path: Path) -> List[Tuple[str, str, str]]:
    """The plan's CHANGED packages at their local version.

    Packages in the wave only for a floor review are left out: their local
    version is usually an old release, and "visible" would say nothing.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read plan {path}: {exc}") from exc
    registry = {"python": "pypi", "npm": "npm", "crates": "crates"}
    specs = []
    for item in data.get("release_wave", []):
        name, version, ecosystem = item.get("package"), item.get("version"), item.get("ecosystem")
        if not item.get("changed", True):
            continue
        if not isinstance(name, str) or not isinstance(version, str) or not version:
            continue
        if ecosystem in registry:
            specs.append((registry[ecosystem], name, version))
    return specs


def _release_key(version: str) -> str:
    """Normalize the release segment so 2.30 and 2.30.0 compare equal (PEP 440)."""
    m = re.match(r"^v?(\d+(?:\.\d+)*)(.*)$", version.strip())
    if not m:
        return version.strip().lower()
    parts = [int(x) for x in m.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return ".".join(map(str, parts)) + m.group(2).lower()


def _get_json(url: str, accept: str = "application/json", timeout: float = 15.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https hosts)
        return json.loads(resp.read().decode("utf-8"))


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def check_pypi(name: str, version: str) -> Tuple[bool, str]:
    project_url = f"https://pypi.org/pypi/{urllib.parse.quote(name)}/{urllib.parse.quote(version)}/json"
    simple_url = f"https://pypi.org/simple/{_normalize(name)}/"
    try:
        _get_json(project_url)
    except urllib.error.HTTPError as exc:
        return False, ("missing on PyPI: " if exc.code == 404 else f"HTTP {exc.code}: ") + project_url
    try:
        simple = _get_json(simple_url, accept="application/vnd.pypi.simple.v1+json")
    except urllib.error.HTTPError as exc:
        return False, f"simple index HTTP {exc.code}: {simple_url}"
    versions = simple.get("versions")
    if isinstance(versions, list):
        visible = _release_key(version) in {_release_key(v) for v in versions}
    else:  # older index responses: look for the version in the file names
        visible = any(f"-{version}" in f.get("filename", "") for f in simple.get("files", []))
    if not visible:
        return False, f"on the project page, not yet on the simple index pip reads: {simple_url}"
    return True, project_url


def check_npm(name: str, version: str) -> Tuple[bool, str]:
    encoded = urllib.parse.quote(name, safe="@").replace("/", "%2F")
    url = f"https://registry.npmjs.org/{encoded}"
    try:
        doc = _get_json(url, accept="application/vnd.npm.install-v1+json")
    except urllib.error.HTTPError as exc:
        return False, ("missing on npm: " if exc.code == 404 else f"HTTP {exc.code}: ") + url
    if version in (doc.get("versions") or {}):
        return True, f"{url} ({name}@{version})"
    return False, f"{name}@{version} not yet in {url}"


def check_crates(name: str, version: str) -> Tuple[bool, str]:
    url = f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}/{urllib.parse.quote(version)}"
    try:
        doc = _get_json(url)
    except urllib.error.HTTPError as exc:
        return False, ("missing on crates.io: " if exc.code == 404 else f"HTTP {exc.code}: ") + url
    if (doc.get("version") or {}).get("yanked"):
        return False, f"yanked: {url}"
    return True, url


def check(registry: str, name: str, version: str) -> Tuple[bool, str]:
    try:
        if registry == "npm":
            return check_npm(name, version)
        if registry == "crates":
            return check_crates(name, version)
        return check_pypi(name, version)
    except Exception as exc:  # network down, DNS, timeout, bad JSON
        return False, f"{type(exc).__name__}: {exc}"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Check package version visibility on PyPI, npm and crates.io.")
    parser.add_argument("spec", nargs="*", help="name==version (PyPI), npm:@scope/name==version or crates:name==version")
    parser.add_argument("--from-plan", type=Path, help="JSON output of abstract_release_plan.py --json")
    parser.add_argument("--wait", type=float, default=0, metavar="SECONDS",
                        help="poll until every spec is visible or SECONDS have passed (default: check once)")
    parser.add_argument("--interval", type=float, default=20, metavar="SECONDS", help="poll interval (default 20)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    try:
        specs = [parse_spec(spec) for spec in args.spec]
    except ValueError as exc:
        parser.error(str(exc))
    if args.from_plan:
        try:
            specs.extend(specs_from_plan(args.from_plan))
        except ValueError as exc:
            parser.error(str(exc))
    if not specs:
        parser.error("give at least one spec or --from-plan")

    deduped: List[Tuple[str, str, str]] = []
    seen = set()
    for registry, name, version in specs:
        key = (registry, name.lower(), version)
        if key not in seen:
            seen.add(key)
            deduped.append((registry, name, version))

    deadline = time.monotonic() + max(args.wait, 0)
    results = {}
    while True:
        for spec in deduped:
            if spec in results and results[spec][0]:
                continue
            results[spec] = check(*spec)
        if all(ok for ok, _ in results.values()) or time.monotonic() >= deadline:
            break
        pending = ", ".join(f"{n}=={v}" for (r, n, v), (ok, _) in results.items() if not ok)
        print(f"waiting for: {pending}", file=sys.stderr)
        time.sleep(max(0.0, min(args.interval, deadline - time.monotonic())))

    rows = [
        {"registry": r, "package": n, "version": v, "visible": results[(r, n, v)][0], "detail": results[(r, n, v)][1]}
        for (r, n, v) in deduped
    ]
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        for row in rows:
            status = "visible" if row["visible"] else "missing"
            print(f"{status:7} {row['registry']:6} {row['package']}=={row['version']}  {row['detail']}")
    return 0 if all(row["visible"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
