"""The release guard must reject local-only code even in a clean checkout."""

from pathlib import Path
import os
import shutil
import subprocess
import sys

import pytest


GATE = (Path(__file__).resolve().parents[1] / "src/abstractskill/registry/skills/release"
        / "scripts/release_pending_gate.py")


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    checkout = tmp_path / "checkout"
    subprocess.run(["git", "init", "-b", "main", str(checkout)], check=True, capture_output=True)
    git(checkout, "config", "user.email", "release-test@example.invalid")
    git(checkout, "config", "user.name", "Release test")
    git(checkout, "config", "commit.gpgsign", "false")
    git(checkout, "remote", "add", "origin", str(remote))
    (checkout / "app.py").write_text("value = 1\n")
    git(checkout, "add", "app.py")
    git(checkout, "commit", "-m", "Initial")
    git(checkout, "push", "-u", "origin", "main")
    return checkout


def gate(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GATE), *args], cwd=repo,
                          capture_output=True, text=True)


def test_clean_pushed_commit_passes(repo: Path) -> None:
    assert gate(repo).returncode == 0


def test_clean_local_only_code_blocks_release(repo: Path) -> None:
    (repo / "app.py").write_text("value = 2\n")
    git(repo, "commit", "-am", "Pending product change")
    assert git(repo, "status", "--porcelain") == ""
    assert gate(repo).returncode == 5
    git(repo, "push", "origin", "main")
    assert gate(repo).returncode == 0


def test_live_remote_movement_is_not_hidden_by_cached_refs(repo: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-b", "main", str(tmp_path / "remote.git"), str(other)],
                   check=True, capture_output=True)
    (other / "app.py").write_text("value = 3\n")
    git(other, "-c", "user.name=Other", "-c", "user.email=other@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-am", "Remote moved")
    git(other, "push", "origin", "main")
    assert git(repo, "rev-parse", "HEAD") == git(repo, "rev-parse", "origin/main")
    assert gate(repo).returncode == 5


def test_pending_source_cannot_be_allowed_as_unrelated(repo: Path) -> None:
    (repo / "src").mkdir()
    (repo / "src/new.py").write_text("value = 4\n")
    assert gate(repo, "--allow-unrelated-pending").returncode == 2


def test_missing_release_branch_fails_closed(repo: Path) -> None:
    assert gate(repo, "--branch", "missing").returncode == 4


def test_nested_untracked_metadata_cannot_hide_in_collapsed_directory(repo: Path) -> None:
    (repo / "plugin").mkdir()
    (repo / "plugin/package.json").write_text('{}\n')
    assert gate(repo, "--allow-unrelated-pending").returncode == 2


def test_rename_out_of_source_keeps_original_classification(repo: Path) -> None:
    (repo / "src").mkdir()
    (repo / "src/module.txt").write_text("source\n")
    git(repo, "add", "src/module.txt")
    git(repo, "commit", "-m", "Source")
    git(repo, "push", "origin", "main")
    git(repo, "mv", "src/module.txt", "personal notes.txt")
    assert gate(repo, "--allow-unrelated-pending").returncode == 2


def test_untracked_metadata_with_newline_name_is_classified(repo: Path) -> None:
    directory = repo / 'plugin\n"quoted"'
    directory.mkdir()
    (directory / "package.json").write_text('{}\n')
    assert gate(repo, "--allow-unrelated-pending").returncode == 2


def test_mutation_while_querying_remote_fails_closed(repo: Path, tmp_path: Path) -> None:
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    shim = executable_dir / "git"
    shim.write_text(
        f"#!{sys.executable}\n"
        "import pathlib, subprocess, sys\n"
        f"result = subprocess.run([{shutil.which('git')!r}, *sys.argv[1:]])\n"
        "if sys.argv[1] == 'ls-remote':\n"
        "    pathlib.Path('app.py').write_text('value = 9\\n')\n"
        "sys.exit(result.returncode)\n"
    )
    shim.chmod(0o755)
    result = subprocess.run([sys.executable, str(GATE)], cwd=repo, capture_output=True,
                            text=True, env={**os.environ, "PATH": str(executable_dir) + os.pathsep + os.environ['PATH']})
    assert result.returncode == 6
