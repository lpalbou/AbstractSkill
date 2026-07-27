"""Demand-tier derivation contract (tool-tiers cycle 3, skill's build half).

These tests pin the room's converged contract as THIS package reads it:
three-outcome honesty, the one truthful coverage join with its three
buckets, server-expansion for MCP deps, and the frozen 1..4 band.
"""

from __future__ import annotations

import pytest

from abstractskill.demand import (
    COVERED,
    DISABLED,
    EXECUTION_FLOOR_RANK,
    NOT_AVAILABLE,
    NOT_GRANTED,
    derive_demand,
)
from abstractskill.selection import SkillRequires


def _inv(*rows):
    return list(rows)


def test_demand_undeclared_never_renders_a_low_tier():
    report = derive_demand(SkillRequires(), has_scripts=False, inventory=_inv(
        {"name": "web_search", "risk_rank": 1},
    ))
    assert report.declared is False
    assert report.demand_rank is None
    assert report.effective_rank is None
    assert report.state == "undeclared"


def test_demand_derives_max_over_resolved_tools():
    req = SkillRequires(tools=("web_search", "fetch_url"))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "web_search", "risk_rank": 1},
        {"name": "fetch_url", "risk_rank": 2},
    ))
    assert report.declared is True
    assert report.demand_rank == 2
    assert report.state == "declared"


def test_scripts_floor_is_structural_and_tops_the_band():
    # Scripts floor applies with or without declarations (from bytes,
    # never frontmatter) and never lowers a higher resolved demand.
    undeclared = derive_demand(SkillRequires(), has_scripts=True)
    assert undeclared.state == "scripts_floor"
    assert undeclared.effective_tier == EXECUTION_FLOOR_RANK

    declared = derive_demand(
        SkillRequires(tools=("read_file",)), has_scripts=True,
        inventory=_inv({"name": "read_file", "risk_rank": 1}),
    )
    assert declared.demand_tier == 1
    assert declared.effective_tier == EXECUTION_FLOOR_RANK


def test_coverage_buckets_host_gap_never_renders_as_grant_gap():
    # The fable5 P0: a demand the host cannot surface must land in
    # NOT_AVAILABLE even when a grant lens is present.
    req = SkillRequires(tools=("web_search", "fetch_url", "send_telegram"))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "web_search", "risk_rank": 1},
        {"name": "fetch_url", "risk_rank": 2},
    ), granted=["web_search"])
    buckets = {r.name: r.bucket for r in report.rows}
    assert buckets["web_search"] == COVERED
    assert buckets["fetch_url"] == NOT_GRANTED       # grantable from the expert menu
    assert buckets["send_telegram"] == NOT_AVAILABLE  # host gap, not a grant gap


def test_enabled_false_rows_render_registered_disabled():
    # The audit's serving shape: exists-but-not-enabled is a visible
    # state distinct from both "not granted" and "not available".
    req = SkillRequires(tools=("send_email",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "send_email", "risk_rank": 3, "enabled": False},
    ), granted=["send_email"])
    assert report.rows[0].bucket == DISABLED
    assert report.rows[0].risk_rank == 3
    # A disabled row still resolves its risk fact for the badge.
    assert report.demand_rank == 3


def test_no_grant_lens_yields_catalog_buckets_only():
    req = SkillRequires(tools=("web_search",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "web_search", "risk_rank": 1},
    ))
    assert report.rows[0].bucket == COVERED


def test_mcp_registered_server_expands_to_its_tools():
    req = SkillRequires(mcp_servers=("meshvault-mcp",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "sculpt", "risk_rank": 2, "mcp_server": "meshvault-mcp"},
        {"name": "paint", "risk_rank": 2, "server": "meshvault-mcp"},
        {"name": "web_search", "risk_rank": 1},
    ))
    kinds = {(r.name, r.kind) for r in report.rows}
    assert ("sculpt", "mcp_tool") in kinds
    assert ("paint", "mcp_tool") in kinds
    assert report.demand_rank == 2
    assert report.unmet_servers == ()


def test_mcp_unregistered_server_is_an_unmet_dep_not_a_tool_gap():
    req = SkillRequires(mcp_servers=("ghost-mcp",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "web_search", "risk_rank": 1},
    ))
    assert report.unmet_servers == ("ghost-mcp",)
    assert report.rows[0].kind == "mcp_server"
    assert report.rows[0].bucket == NOT_AVAILABLE
    assert report.demand_rank is None


def test_out_of_band_risk_rank_refused_loudly_never_clamped():
    req = SkillRequires(tools=("weird",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "weird", "risk_rank": 9},
    ))
    assert report.demand_rank is None
    assert any("out-of-band" in n for n in report.notes)


def test_unserved_risk_rank_resolves_bucket_but_no_rank():
    # Pre-build inventories (no risk_tier field yet) still classify
    # coverage honestly; the badge simply has no number to show.
    req = SkillRequires(tools=("web_search",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "web_search"},
    ))
    assert report.rows[0].bucket == COVERED
    assert report.rows[0].risk_rank is None
    assert report.demand_rank is None


def test_duplicate_inventory_names_keep_first_and_note():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 1},
        {"name": "t", "risk_rank": 4},
    ))
    assert report.demand_rank == 1
    assert any("duplicate" in n for n in report.notes)


def test_boolean_risk_rank_never_mints_rank_one():
    # bool is an int subclass: True would read as tier 1 — the exact
    # tier-1-by-truthiness failure the refuse-loudly rule exists for.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": True},
    ))
    assert report.demand_rank is None
    assert any("boolean" in n for n in report.notes)


def test_non_integral_float_risk_rank_refused_never_truncated():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 4.5},
    ))
    assert report.demand_rank is None
    assert any("non-integral" in n for n in report.notes)


def test_string_false_enabled_reads_disabled_not_truthy():
    # The recorded tool-arg coercion class: "false" is truthy in Python.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 2, "enabled": "false"},
    ), granted=["t"])
    assert report.rows[0].bucket == DISABLED


def test_non_mapping_inventory_row_skipped_never_crashes():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=[
        {"name": "t", "risk_rank": 1},
        "garbage",
    ])
    assert report.rows[0].bucket == COVERED
    assert any("non-mapping" in n for n in report.notes)


def test_empty_grant_is_a_lens_not_no_lens():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 1},
    ), granted=[])
    assert report.rows[0].bucket == NOT_GRANTED


def test_ungranted_and_disabled_tiers_still_count_toward_demand():
    # Demand is what the skill ASKS, independent of grant/enable state —
    # the badge bounds demand, the grant stays the gate.
    req = SkillRequires(tools=("a", "b"))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "a", "risk_rank": 2},
        {"name": "b", "risk_rank": 3, "enabled": False},
    ), granted=[])
    assert report.demand_rank == 3


def test_mcp_expansion_with_disabled_rows_is_not_an_unmet_server():
    req = SkillRequires(mcp_servers=("mv",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "sculpt", "risk_rank": 2, "mcp_server": "mv", "enabled": False},
    ))
    assert report.unmet_servers == ()
    assert report.rows[0].bucket == DISABLED
    assert report.demand_rank == 2


def test_scripts_floor_never_lowers_a_resolved_top_demand():
    req = SkillRequires(tools=("rm_like",))
    report = derive_demand(req, has_scripts=True, inventory=_inv(
        {"name": "rm_like", "risk_rank": 4},
    ))
    assert report.effective_rank == 4
    assert report.state == "declared"
    assert report.scripts_floor is True


def test_declared_plus_scripts_with_nothing_resolved_floors_effective():
    # state stays the declaration-axis word; the badge must render
    # scripts_floor beside effective_tier (docstring contract).
    req = SkillRequires(tools=("ghost",))
    report = derive_demand(req, has_scripts=True)
    assert report.state == "declared"
    assert report.demand_rank is None
    assert report.effective_rank == EXECUTION_FLOOR_RANK
    assert report.scripts_floor is True


def test_empty_inventory_with_demands_notes_the_day_one_host():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=[])
    assert report.rows[0].bucket == NOT_AVAILABLE
    assert any("no readable inventory" in n for n in report.notes)


def test_package_exports_the_demand_surface():
    import abstractskill

    assert abstractskill.derive_demand is derive_demand
    assert "DemandReport" in abstractskill.__all__


def test_legacy_int_on_risk_tier_accepted_one_release_with_note():
    # The pre-vote shape (hours old): integer on risk_tier, no risk_rank.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_tier": 2},
    ))
    assert report.demand_rank == 2
    assert any("pre-vote shape" in n for n in report.notes)


def test_band_word_without_rank_is_unserved_never_rederived():
    # New shape missing its ordinal half: the word->rank mapping is
    # core's versioned fold — a consumer must not carry a second copy.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_tier": "destroy"},
    ))
    assert report.demand_rank is None
    assert any("band word" in n for n in report.notes)


def test_settled_trio_threads_band_and_presentation_to_rows():
    # Word/rank/presentation (c4599): rank folds, word + presentation
    # ride the row for renders — a factless rank-4 row must carry its
    # "unvetted" marker or it renders as a priced destroy verdict.
    req = SkillRequires(tools=("mcp_thing",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "mcp_thing", "risk_rank": 4, "risk_tier": "destroy",
         "risk_presentation": "unvetted"},
    ))
    row = report.rows[0]
    assert row.risk_rank == 4
    assert row.band == "destroy"
    assert row.presentation == "unvetted"
    assert report.demand_rank == 4


def test_rank_wins_over_legacy_key_when_both_serve():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 3, "risk_tier": "outreach"},
    ))
    assert report.demand_rank == 3
    assert not any("pre-vote" in n for n in report.notes)


def test_alias_surface_carries_one_release():
    # Pre-vote spellings stay readable: report.demand_tier/effective_tier
    # and row.risk_tier alias the rank values. Removal next release
    # deletes exactly this test.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 2},
    ))
    assert report.demand_tier == report.demand_rank == 2
    assert report.effective_tier == report.effective_rank == 2
    assert report.rows[0].risk_tier == report.rows[0].risk_rank == 2


def test_garbage_risk_rank_never_falls_back_to_legacy_int():
    # A present risk_rank is authoritative: unreadable = unserved,
    # never repaired from a coexisting legacy int (chimera row).
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 9, "risk_tier": 2},
    ))
    assert report.demand_rank is None
    assert any("out-of-band" in n for n in report.notes)


def test_rank_wins_over_disagreeing_legacy_int_quietly():
    # Sanctioned migration overlap (both keys numeric): rank wins, no
    # pre-vote note spam.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_rank": 3, "risk_tier": 2},
    ))
    assert report.demand_rank == 3
    assert not any("pre-vote" in n for n in report.notes)


def test_legacy_bool_on_risk_tier_still_refused():
    # tier-1-by-truthiness guard holds on the legacy path too.
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_tier": True},
    ))
    assert report.demand_rank is None
    assert any("boolean" in n for n in report.notes)


def test_legacy_integral_float_accepted_with_pre_vote_note():
    req = SkillRequires(tools=("t",))
    report = derive_demand(req, has_scripts=False, inventory=_inv(
        {"name": "t", "risk_tier": 2.0},
    ))
    assert report.demand_rank == 2
    assert any("pre-vote" in n for n in report.notes)
