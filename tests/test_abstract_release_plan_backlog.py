"""abstract-release planner: the --backlog scope sweep (planned items per package of the wave)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PLANNER = REPO / "src" / "abstractskill" / "registry" / "skills" / "abstract-release" / "scripts" / "abstract_release_plan.py"


@pytest.fixture(scope="module")
def plan():
    # No bytecode next to the planner: a __pycache__ inside the shelf skill would change its
    # pinned tree hash (test_shelf / test_bundled check those bytes).
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("abstract_release_plan_under_test", PLANNER)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    assert not (PLANNER.parent / "__pycache__").exists()
    return module


def _pkg(plan, root: Path, repo: str, key: str, name: str, inventory_id: str | None = None):
    path = root / repo
    path.mkdir(parents=True, exist_ok=True)
    return plan.Package(name=name, key=key, ecosystem="python", path=path, manifest=path / "pyproject.toml",
                        version="1.0.0", git_root=path, inventory_id=inventory_id)


def _item(repo_dir: Path, name: str, text: str) -> None:
    planned = repo_dir / "docs" / "backlog" / "planned"
    planned.mkdir(parents=True, exist_ok=True)
    (planned / name).write_text(text, encoding="utf-8")


def test_package_line_names_packages_by_key_short_name_and_npm_segment(plan, tmp_path: Path) -> None:
    core = _pkg(plan, tmp_path, "abstractcore", "abstractcore", "abstractcore")
    runtime = _pkg(plan, tmp_path, "abstractruntime", "abstractruntime", "AbstractRuntime")
    gateway = _pkg(plan, tmp_path, "abstractgateway", "abstractgateway", "abstractgateway")
    flow = _pkg(plan, tmp_path, "abstractflow", "abstractframeworkflow", "@abstractframework/flow", "flow")
    pkgs = [core, runtime, gateway, flow]
    line = "AbstractCore (mechanism), AbstractRuntime (relay), AbstractGateway (setting, flag, UI, lock persistence)"
    assert plan.packages_named(line, pkgs) == ["abstractcore", "abstractruntime", "abstractgateway"]
    assert plan.packages_named("runtime, gateway, flow", pkgs) == ["abstractruntime", "abstractgateway",
                                                                   "abstractframeworkflow"]
    assert plan.packages_named("framework", pkgs) == []


def test_sweep_groups_planned_items_per_wave_package(plan, tmp_path: Path) -> None:
    core = _pkg(plan, tmp_path, "abstractcore", "abstractcore", "abstractcore")
    runtime = _pkg(plan, tmp_path, "abstractruntime", "abstractruntime", "AbstractRuntime")
    gateway = _pkg(plan, tmp_path, "abstractgateway", "abstractgateway", "abstractgateway")
    _item(tmp_path, "1115_idle_unload.md",
          "# 1115 — Idle unload\n\n> Package: AbstractCore (mechanism), AbstractRuntime (relay), AbstractGateway (UI)\n")
    _item(tmp_path, "1200_no_package.md", "# 1200 — A root item\n\n> Type: task\n")
    _item(tmp_path, "README.md", "# Backlog\n")
    _item(core.path, "0900_core_only.md", "# 0900 — In Core's own backlog\n")
    _item(gateway.path, "0950_gateway_item.md", "# 0950 — Gateway\n")
    (tmp_path / "docs" / "backlog" / "completed").mkdir(parents=True)
    (tmp_path / "docs" / "backlog" / "completed" / "0001_done.md").write_text("> Package: abstractcore\n")

    # Gateway is NOT in the wave: its repository is not swept, but root items naming it are listed apart.
    sweep = plan.backlog_sweep(tmp_path, [core, runtime, gateway], ["abstractcore", "abstractruntime"])
    per = {g["key"]: [i["title"] for i in g["items"]] for g in sweep["per_package"]}
    assert per["abstractcore"] == ["1115 — Idle unload", "0900 — In Core's own backlog"]
    assert per["abstractruntime"] == ["1115 — Idle unload"]
    assert [g["key"] for g in sweep["outside_wave"]] == ["abstractgateway"]
    assert [i["title"] for i in sweep["outside_wave"][0]["items"]] == ["1115 — Idle unload"]
    assert [i["title"] for i in sweep["unassigned"]] == ["1200 — A root item"]
    assert sweep["item_count"] == 3  # README skipped, completed/ not read, gateway repo not in the wave


def test_markdown_lists_the_sweep_only_when_asked(plan, tmp_path: Path) -> None:
    core = _pkg(plan, tmp_path, "abstractcore", "abstractcore", "abstractcore")
    _item(tmp_path, "1115_idle_unload.md", "# 1115 — Idle unload\n\n> Package: AbstractCore\n")
    data = {"workspace": str(tmp_path), "inventory": "test", "package_count": 1, "registry_checked": False,
            "release_wave": [], "dependency_floor_reviews": [], "profile_pin_reviews": [], "inventory_gaps": [],
            "changes_outside_packages": [], "ordered_packages": []}
    assert "Backlog Scope Sweep" not in plan.render_markdown(data)
    data["backlog_sweep"] = plan.backlog_sweep(tmp_path, [core], ["abstractcore"])
    text = plan.render_markdown(data)
    assert "## Backlog Scope Sweep (planned items)" in text
    assert "1115 — Idle unload" in text
