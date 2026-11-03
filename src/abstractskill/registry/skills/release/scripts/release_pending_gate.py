#!/usr/bin/env python3
"""Conservative release pending-change gate.

The script intentionally blocks on pending changes unless they are explicitly allowed. It is a
helper for agents, not a replacement for release judgment.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


RELEASE_RELEVANT_PREFIXES = (
    ".github/",
    "docs/",
    "src/",
    "lib/",
    "app/",
    "packages/",
    "tests/",
    "test/",
    "examples/",
    "scripts/",
)

RELEASE_RELEVANT_NAMES = {
    "CHANGELOG.md",
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "ACKNOWLEDGEMENTS.md",
    "CODE_OF_CONDUCT.md",
    "llms.txt",
    "llms-full.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "uv.lock",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "Dockerfile",
    "docker-compose.yml",
    "mkdocs.yml",
}


@dataclass
class PendingFile:
    status: str
    path: str

    @property
    def release_relevant(self) -> bool:
        clean_path = self.path.strip()
        name = Path(clean_path).name
        return (
            clean_path in RELEASE_RELEVANT_NAMES
            or name in RELEASE_RELEVANT_NAMES
            or clean_path.startswith(RELEASE_RELEVANT_PREFIXES)
        )


def git_status() -> list[PendingFile]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        check=True,
        capture_output=True,
        text=True,
    )
    pending: list[PendingFile] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        pending.append(PendingFile(status=status, path=path))
    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description="Block unsafe releases with pending changes.")
    parser.add_argument(
        "--allow-unrelated-pending",
        action="store_true",
        help="Allow pending changes only if none match conservative release-relevant paths.",
    )
    args = parser.parse_args()

    pending = git_status()
    if not pending:
        print("release-pending-gate: no pending changes")
        return 0

    relevant = [entry for entry in pending if entry.release_relevant]
    unrelated = [entry for entry in pending if not entry.release_relevant]

    print("release-pending-gate: pending changes detected")
    for entry in pending:
        marker = "release-relevant" if entry.release_relevant else "unclassified"
        print(f"  {entry.status} {entry.path} [{marker}]")

    if relevant:
        print(
            "\nRefusing release: release-relevant files are modified or untracked. "
            "Commit and push them, or explicitly remove them from the release scope before tagging "
            "or publishing.",
            file=sys.stderr,
        )
        return 2

    if unrelated and not args.allow_unrelated_pending:
        print(
            "\nRefusing release: pending changes remain. Re-run with --allow-unrelated-pending "
            "only after explicitly confirming these files are unrelated to the release.",
            file=sys.stderr,
        )
        return 3

    print("release-pending-gate: only explicitly allowed unrelated pending changes remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
