"""Demand-tier derivation: what powers a skill ASKS FOR (tool-tiers cycle 3).

The room's converged tool-tiers contract (commons plans/tool-tiers.md,
cycles 1-2 + the G/H addendum, 2026-07-22) gives skills a DERIVED demand
rank: the max served ``risk_rank`` of the tools a skill declares in
``metadata.requires_tools``, resolved at the (skill x host inventory)
join. This module is the consumer half of the SETTLED wire shape
(c4599/c4606): ``risk_rank`` = integer ordinal 1..4, ``risk_tier`` = the
band WORD (display), ``risk_presentation`` always served.

Load-bearing rules, each argued and adopted on the record:

- DERIVED, never self-declared: a skill never carries its own tier in
  frontmatter — the derivation reads the declaration (names) against the
  HOST's inventory rows (risk facts). Self-graded tiers are a
  self-grading surface (cycle-1, consumed by runtime c4454).
- Three-outcome honesty (never tier-1-by-omission): declared demands
  derive; an UNDECLARED skill renders "tool demands undeclared" — a low
  badge on silence is false confidence; ``has_scripts`` floors the
  demand at the execution band regardless of declarations (structural,
  from bytes, never frontmatter).
- One truthful coverage join, both grant modes (G addendum, adopted by
  gateway c4528): set-difference over inventory-resolved ids with three
  buckets — covered / not granted (grantable from the expert menu) /
  NOT AVAILABLE ON THIS HOST. A host gap must never render as a grant
  gap (the fable5 P0: "your grant lacks X" when the host cannot even
  surface X blames the operator for a hole the host owns).
- requires_mcp joins by SERVER: a registered server expands to its
  discovered tool names (rows carrying that server's name); an
  unregistered server renders as an unmet server dep. Risk stays
  route-clamped either way — the clamp is the INVENTORY's job (the rows
  carry the clamped risk_tier); this module never re-derives it.
- The badge bounds DEMAND, never capability: the session grant (preset
  or custom) stays the only gate. Rendering that sentence is the
  caller's duty; this module only computes the honest inputs.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from abstractskill.selection import SkillRequires

# The four frozen risk bands (cycle-1 synthesis point 4: "4 tiers frozen,
# every finer distinction is a FACT"; semantics' D words: observe / act /
# outreach / destroy). Wire shape per the settled vote (c4599/c4606):
# ``risk_rank`` carries the INTEGER ordinal 1..4; ``risk_tier`` carries
# the band WORD (display/identity); ``risk_presentation`` always rides
# (factless rows = rank 4 + "unvetted", never a destroy render).
RISK_RANK_MIN = 1
RISK_RANK_MAX = 4
# One-release aliases (pre-vote spellings, exported 2026-07-23 morning).
RISK_TIER_MIN = RISK_RANK_MIN
RISK_TIER_MAX = RISK_RANK_MAX

# has_scripts floors demand at the execution band: running a skill's
# scripts is execute_command-class work, and the room endorsed the
# execute_command clamp-to-4 (runtime c4452). Structural: read from tree
# bytes (inspect_skill_dir), never from frontmatter claims.
EXECUTION_FLOOR_RANK = RISK_RANK_MAX
EXECUTION_FLOOR_TIER = EXECUTION_FLOOR_RANK  # one-release alias

# Coverage buckets (G addendum, adopted into the audit's consumer
# contract at c4528). String constants, not an enum: these words travel
# into render surfaces and hub reports verbatim.
COVERED = "covered"
NOT_GRANTED = "not_granted"          # in the inventory, absent from the grant
NOT_AVAILABLE = "not_available"      # no inventory row resolves the demand
DISABLED = "registered_disabled"     # row exists with enabled=false (audit shape)


@dataclass(frozen=True, slots=True)
class DemandRow:
    """One declared demand joined against the host inventory."""

    name: str
    kind: str                      # "tool" | "mcp_server" | "mcp_tool"
    bucket: str                    # COVERED / NOT_GRANTED / NOT_AVAILABLE / DISABLED
    risk_rank: Optional[int] = None   # served ordinal (risk_rank key), when resolved
    band: Optional[str] = None        # served band WORD (risk_tier key), display-only
    presentation: Optional[str] = None  # served risk_presentation (e.g. "unvetted")
    via_server: Optional[str] = None  # set on mcp_tool rows (the expansion source)

    @property
    def risk_tier(self) -> Optional[int]:
        """One-release alias for the ordinal (pre-vote field name)."""
        return self.risk_rank


@dataclass(frozen=True, slots=True)
class DemandReport:
    """The three-outcome render inputs for one skill on one host.

    ``demand_rank`` is None when nothing declared resolves to a served
    ordinal — callers must render the honest state words, never default
    a missing number to the low band.
    """

    declared: bool                 # any requires_tools/requires_mcp present
    demand_rank: Optional[int]     # max resolved risk_rank (declared demands only)
    scripts_floor: bool            # has_scripts raised (or set) the floor
    rows: tuple[DemandRow, ...] = ()
    unmet_servers: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def demand_tier(self) -> Optional[int]:
        """One-release alias for the ordinal (pre-vote field name)."""
        return self.demand_rank

    @property
    def effective_rank(self) -> Optional[int]:
        """Demand rank with the structural scripts floor applied."""
        if self.scripts_floor:
            return max(self.demand_rank or RISK_RANK_MIN, EXECUTION_FLOOR_RANK)
        return self.demand_rank

    @property
    def effective_tier(self) -> Optional[int]:
        """One-release alias for :attr:`effective_rank`."""
        return self.effective_rank

    @property
    def state(self) -> str:
        """The DECLARATION-axis word, not the whole badge: a render
        showing ``effective_tier`` must show ``scripts_floor`` beside it,
        or a structural 4 (scripts) reads as a priced declaration —
        false precision on the declaration axis."""
        if self.scripts_floor and not self.declared:
            return "scripts_floor"
        if not self.declared:
            return "undeclared"
        return "declared"


def _coerce_rank(raw: Any, notes: list[str], name: str, key: str) -> Optional[int]:
    """Coerce one served ordinal tolerantly; out-of-band values are
    refused loudly (a rank outside the frozen 1..4 band is a contract
    breach we must surface, never silently clamp — silent clamping would
    hide the exact drift the versioned mapping exists to prevent)."""
    if isinstance(raw, bool):
        # bool is an int subclass: True would mint rank 1 — the lowest
        # band from a non-rank value (tier-1-by-truthiness).
        notes.append(
            f"#FALLBACK: inventory row {name!r} carries boolean "
            f"{key} {raw!r}; treated as unserved"
        )
        return None
    if isinstance(raw, float) and not raw.is_integer():
        notes.append(
            f"#FALLBACK: inventory row {name!r} carries non-integral "
            f"{key} {raw!r}; treated as unserved (never truncated)"
        )
        return None
    try:
        rank = int(raw)
    except (TypeError, ValueError):
        notes.append(
            f"#FALLBACK: inventory row {name!r} carries non-integer "
            f"{key} {raw!r}; treated as unserved"
        )
        return None
    if not (RISK_RANK_MIN <= rank <= RISK_RANK_MAX):
        notes.append(
            f"#FALLBACK: inventory row {name!r} carries out-of-band "
            f"{key} {rank} (frozen band {RISK_RANK_MIN}..{RISK_RANK_MAX}); "
            "treated as unserved"
        )
        return None
    return rank


def _row_risk_rank(row: Mapping[str, Any], notes: list[str], name: str) -> Optional[int]:
    """Read the served ordinal per the settled wire shape (c4599/c4606):
    ``risk_rank`` = INTEGER, ``risk_tier`` = band WORD.

    A PRESENT (non-null) risk_rank is authoritative: an unreadable one
    is unserved, never repaired from a legacy risk_tier int — a host
    serving the new key has adopted the new shape, and garbage there is
    a contract breach to surface, not to paper over. An explicit null
    risk_rank reads as absent (JSON null = unserved).

    Legacy window: the pre-vote shape (hours old) served the number ON
    ``risk_tier``. A numeric risk_tier with no risk_rank is accepted
    WITH a #FALLBACK note for one release (mirroring runtime's alias
    posture); a WORD-typed risk_tier with no risk_rank is the new shape
    missing its ordinal half — unserved, noted, never re-derived here
    (the word->rank mapping is core's versioned fold; import-never-copy
    forbids a second copy in a consumer). Note duplication: a name
    declared BOTH in requires_tools and via a declared server is read
    twice (two rows by contract), so its reader notes can appear twice —
    duplication of rows is advertised, notes ride along."""
    raw_rank = row.get("risk_rank")
    if raw_rank is not None:
        return _coerce_rank(raw_rank, notes, name, "risk_rank")
    legacy = row.get("risk_tier")
    if legacy is None:
        return None
    if isinstance(legacy, str):
        notes.append(
            f"#FALLBACK: inventory row {name!r} serves band word "
            f"risk_tier={legacy!r} with no risk_rank — ordinal unserved "
            "(this consumer never re-derives the word->rank mapping)"
        )
        return None
    rank = _coerce_rank(legacy, notes, name, "risk_tier")
    if rank is not None:
        notes.append(
            f"#FALLBACK: inventory row {name!r} serves the pre-vote shape "
            f"(numeric risk_tier={legacy!r}, no risk_rank); accepted one release"
        )
    return rank


def _row_band(row: Mapping[str, Any]) -> Optional[str]:
    """The band WORD when the new shape serves it (display-only here)."""
    raw = row.get("risk_tier")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _row_presentation(row: Mapping[str, Any]) -> Optional[str]:
    """The served risk_presentation marker (e.g. "unvetted") — carried
    verbatim to renders so a factless rank-4 row never reads as a
    priced destroy verdict."""
    raw = row.get("risk_presentation")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _row_enabled(row: Mapping[str, Any], notes: list[str], name: str) -> bool:
    """The audit's serving shape: exists-but-not-enabled is a visible
    state (enabled: false), never silence. Absent key = enabled (the
    pre-audit inventory shape serves only enabled rows).

    Wire tolerance without truthiness: a JSON-ish string "false" is
    truthy in Python (the recorded tool-arg coercion class) — map the
    known spellings, refuse the rest loudly and keep the default."""
    raw = row.get("enabled")
    if raw is None:
        return True
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in ("false", "no", "0", "off"):
            return False
        if lowered in ("true", "yes", "1", "on"):
            return True
    notes.append(
        f"#FALLBACK: inventory row {name!r} carries unreadable enabled "
        f"value {raw!r}; treated as enabled (the absent-key default)"
    )
    return True


def _row_server(row: Mapping[str, Any]) -> Optional[str]:
    """The MCP-source marker on an inventory row, when the host serves
    one. Two spellings tolerated (the serving shape is gateway's lane;
    we read, never mint): ``mcp_server`` preferred, ``server`` accepted."""
    for key in ("mcp_server", "server"):
        val = row.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return None


def _bucket(name: str, row: Optional[Mapping[str, Any]], granted: Optional[frozenset[str]],
            notes: list[str]) -> tuple[str, Optional[int]]:
    """Classify one demand name against inventory + grant.

    The order is load-bearing (the fable5 P0): host-absence must be
    decided BEFORE grant-absence, or a host gap renders as a grant gap.
    """
    if row is None:
        return NOT_AVAILABLE, None
    rank = _row_risk_rank(row, notes, name)
    if not _row_enabled(row, notes, name):
        return DISABLED, rank
    if granted is not None and name not in granted:
        return NOT_GRANTED, rank
    return COVERED, rank


def derive_demand(
    requires: SkillRequires,
    *,
    has_scripts: bool,
    inventory: Iterable[Any] = (),
    granted: Optional[Iterable[str]] = None,
) -> DemandReport:
    """Join one skill's declared demands against a host inventory.

    ``inventory`` rows are the host's served tool rows (dicts; read
    tolerantly: ``name`` required; ``risk_rank``/``risk_tier``/
    ``risk_presentation``/``enabled``/``mcp_server`` honored when
    present — the settled wire trio is word/rank/presentation, c4599).
    ``granted`` is the session's per-tool grant — the SAME set under
    preset and custom modes (the converged one-grant model); None means
    "no grant lens" (catalog renders: buckets are covered/available vs
    not-available only).

    A name declared in ``requires_tools`` AND expanded from a
    ``requires_mcp`` server yields TWO rows (kind "tool" + "mcp_tool"):
    declared twice, shown twice — ``demand_rank`` is max-folded, so the
    number is unaffected; renders must not "fix" the duplication.

    Returns render INPUTS. Callers own the words; this module owns the
    honesty of the numbers and buckets.
    """
    notes: list[str] = []
    by_name: dict[str, Mapping[str, Any]] = {}
    by_server: dict[str, list[Mapping[str, Any]]] = {}
    for row in inventory:
        if not isinstance(row, Mapping):
            notes.append(
                f"#FALLBACK: non-mapping inventory row ({type(row).__name__}) skipped"
            )
            continue
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            notes.append("#FALLBACK: inventory row without a usable name skipped")
            continue
        name = name.strip()
        if name in by_name:
            # Same name twice: keep the first, note the shadow — a name is
            # the join key, and a silent overwrite would make the render
            # depend on serving order. If only the LOSING copy carried a
            # server key, say so: the visible symptom would otherwise be a
            # phantom unmet server with a note pointing at name dedup.
            dup_server = _row_server(row)
            if dup_server and _row_server(by_name[name]) != dup_server:
                notes.append(
                    f"#FALLBACK: duplicate inventory row {name!r}; first kept "
                    f"(dropped copy carried mcp_server {dup_server!r} — that "
                    "server's expansion will not see this row)"
                )
            else:
                notes.append(f"#FALLBACK: duplicate inventory row {name!r}; first kept")
            continue
        by_name[name] = row
        server = _row_server(row)
        if server:
            by_server.setdefault(server, []).append(row)

    granted_set: Optional[frozenset[str]] = (
        frozenset(str(g).strip() for g in granted) if granted is not None else None
    )

    rows: list[DemandRow] = []
    unmet_servers: list[str] = []
    resolved_ranks: list[int] = []

    if not by_name and bool(requires):
        notes.append(
            "#FALLBACK: host served no readable inventory rows — every "
            "declared demand renders not_available (a day-one host, not "
            "necessarily a missing tool)"
        )

    def _decorated(row: Optional[Mapping[str, Any]]) -> tuple[Optional[str], Optional[str]]:
        if row is None:
            return None, None
        return _row_band(row), _row_presentation(row)

    for tool in requires.tools:
        tool = tool.strip()
        if not tool:
            continue
        inv_row = by_name.get(tool)
        bucket, rank = _bucket(tool, inv_row, granted_set, notes)
        band, presentation = _decorated(inv_row)
        rows.append(DemandRow(
            name=tool, kind="tool", bucket=bucket,
            risk_rank=rank, band=band, presentation=presentation,
        ))
        if rank is not None:
            resolved_ranks.append(rank)

    for server in requires.mcp_servers:
        server = server.strip()
        if not server:
            continue
        served = by_server.get(server)
        if not served:
            # Unregistered server: an unmet server dep — never
            # set-differenced against tool names (a server name is not a
            # tool name), never filed as a host tool gap.
            unmet_servers.append(server)
            rows.append(DemandRow(name=server, kind="mcp_server", bucket=NOT_AVAILABLE))
            continue
        for row in served:
            name = str(row.get("name", "")).strip()
            bucket, rank = _bucket(name, row, granted_set, notes)
            band, presentation = _decorated(row)
            rows.append(DemandRow(
                name=name, kind="mcp_tool", bucket=bucket,
                risk_rank=rank, band=band, presentation=presentation,
                via_server=server,
            ))
            if rank is not None:
                resolved_ranks.append(rank)

    return DemandReport(
        declared=bool(requires),
        demand_rank=max(resolved_ranks) if resolved_ranks else None,
        scripts_floor=bool(has_scripts),
        rows=tuple(rows),
        unmet_servers=tuple(unmet_servers),
        notes=tuple(notes),
    )
