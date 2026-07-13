"""Regression pins for the refresh-time byte-pin refusal.

The 2026-07-11 adversarial wave added ``expected_tree_hash`` pins to every
SHELF_POLICY entry so an edited vendored tree can never be silently
re-attested by a refresh. The refusal was proven live with a one-byte tamper;
these tests make that proof durable: the same check must refuse a tampered
tree and pass an untouched one.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "refresh_shelf.py"
SHELF = REPO / "registry" / "skills"

sys.path.insert(0, str(REPO / "src"))

from abstractskill import hash_skill_tree  # noqa: E402


def _load_refresh_module():
    """Import scripts/refresh_shelf.py as a throwaway module instance.

    A fresh instance per test keeps monkeypatched module state (SHELF,
    SHELF_POLICY) from leaking between tests or into the real script.
    """
    spec = importlib.util.spec_from_file_location("refresh_shelf_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tmp_shelf_with(tmp_path: Path, name: str) -> Path:
    shelf = tmp_path / "skills"
    shelf.mkdir()
    shutil.copytree(SHELF / name, shelf / name)
    return shelf


def _policy(pin: str) -> dict:
    return {
        "expected_tree_hash": pin,
        "method": "first-party",
        "source": "first-party",
        "level": "first_party",
        "activation_description": None,
    }


def test_tampered_tree_refuses_at_refresh(tmp_path, monkeypatch):
    """One appended byte after pinning must abort the refresh loudly."""
    shelf = _tmp_shelf_with(tmp_path, "adversarial-iteration")
    pin = hash_skill_tree(shelf / "adversarial-iteration")

    mod = _load_refresh_module()
    monkeypatch.setattr(mod, "SHELF", shelf)
    monkeypatch.setattr(
        mod, "SHELF_POLICY", {"adversarial-iteration": _policy(pin)}
    )
    monkeypatch.setattr(mod, "_catalog_policies", lambda: {})

    skill_md = shelf / "adversarial-iteration" / "SKILL.md"
    skill_md.write_bytes(skill_md.read_bytes() + b"x")

    with pytest.raises(SystemExit) as exc:
        mod.build_records()
    message = str(exc.value)
    assert "do not match the recorded pin" in message
    assert pin in message  # the refusal names both hashes for the curator


def test_untampered_tree_passes_the_pin_check(tmp_path, monkeypatch):
    """The same policy over unchanged bytes builds a record normally."""
    shelf = _tmp_shelf_with(tmp_path, "adversarial-iteration")
    pin = hash_skill_tree(shelf / "adversarial-iteration")

    mod = _load_refresh_module()
    monkeypatch.setattr(mod, "SHELF", shelf)
    monkeypatch.setattr(
        mod, "SHELF_POLICY", {"adversarial-iteration": _policy(pin)}
    )
    monkeypatch.setattr(mod, "_catalog_policies", lambda: {})

    records = mod.build_records()
    assert [r["name"] for r in records] == ["adversarial-iteration"]
    assert records[0]["tree_hash"] == pin
