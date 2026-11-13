#!/usr/bin/env python3
"""Conservative release pending-change gate.

Block pending files and commits that have not reached the live release branch.
Read-only Git operations; the remote query may use network access. This cannot
decide branch ownership, feature scope or whether consumers were integrated.
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


@dataclass(frozen=True)
class PendingFile:
    status: str
    path: str
    original_path: str | None = None

    @property
    def release_relevant(self) -> bool:
        return any(
            path in RELEASE_RELEVANT_NAMES
            or Path(path).name in RELEASE_RELEVANT_NAMES
            or path.startswith(RELEASE_RELEVANT_PREFIXES)
            for path in (self.path, self.original_path) if path is not None
        )


def git_status() -> list[PendingFile]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"],
        check=True,
        capture_output=True,
        text=True,
    )
    pending: list[PendingFile] = []
    entries = iter(result.stdout.split("\0"))
    for line in entries:
        if not line:
            continue
        status = line[:2]
        path = line[3:]
        original_path = next(entries) if "R" in status or "C" in status else None
        pending.append(PendingFile(status=status, path=path, original_path=original_path))
    return pending


def verify_published_commit(remote: str, branch: str, pending: list[PendingFile]) -> int:
    """Check the live ref, rather than trusting a possibly stale tracking ref."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", "--", remote, f"refs/heads/{branch}"],
        capture_output=True, text=True, timeout=45,
    )
    refs = [line.split() for line in result.stdout.splitlines()]
    after_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True,
    ).stdout.strip()
    if after_head != head or git_status() != pending:
        print("Refusing release: checkout changed during remote verification.", file=sys.stderr)
        return 6
    if (result.returncode or len(refs) != 1 or len(refs[0]) != 2
            or refs[0][1] != f"refs/heads/{branch}"):
        print("Refusing release: live release branch could not be verified.", file=sys.stderr)
        return 4
    if head != refs[0][0]:
        print(
            f"Refusing release: local HEAD {head} differs from live release branch "
            f"{refs[0][0]}. Integrate and push the complete release scope first.",
            file=sys.stderr,
        )
        return 5
    print("release-pending-gate: HEAD equals the live release branch")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Block unsafe releases with pending changes.")
    parser.add_argument(
        "--allow-unrelated-pending",
        action="store_true",
        help="Allow pending changes only if none match conservative release-relevant paths.",
    )
    parser.add_argument("--remote", default="origin", help="Git remote to query (default origin).")
    parser.add_argument("--branch", default="main", help="Integrated release branch (default main).")
    args = parser.parse_args()

    pending = git_status()
    if not pending:
        print("release-pending-gate: no pending changes")
        return verify_published_commit(args.remote, args.branch, pending)

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
    return verify_published_commit(args.remote, args.branch, pending)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, StopIteration):
        print("Refusing release: Git state could not be verified.", file=sys.stderr)
        raise SystemExit(4)
