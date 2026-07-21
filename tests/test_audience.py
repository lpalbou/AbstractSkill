"""Audience field pins (2026-07-19, laurent's default-skills ruling —
cognition room seq 156/163/165): who may RECEIVE a skill's teaching is a
structural registry fact, never prose inference. The entity-observation
class (an observer skill entering an entity prompt) is closed by the
fail-closed default; the ONE entity-audience skill is pinned by name."""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent

from abstractskill import TrustRegistry  # noqa: E402
from abstractskill.errors import SkillValidationError  # noqa: E402
from abstractskill.trust import ValidationRecord  # noqa: E402

VALIDATIONS = REPO / "registry" / "validations.yaml"


def _registry() -> TrustRegistry:
    return TrustRegistry.load(validations_path=VALIDATIONS)


def test_audience_defaults_fail_closed_to_host() -> None:
    # A record without the field reads as host — an undeclared-audience
    # skill must never reach an entity prompt.
    rec = ValidationRecord.from_dict(
        {
            "name": "x",
            "source": "s",
            "tree_hash": "a" * 64,
            "level": "adopted",
            "method": "manual-review",
            "validated_by": "skill",
            "validated_at": "2026-07-19",
        }
    )
    assert rec.audience == "host"
    assert rec.to_dict()["audience"] == "host"  # always emitted


def test_audience_vocabulary_is_closed() -> None:
    with pytest.raises(SkillValidationError, match="unknown audience"):
        ValidationRecord.from_dict(
            {
                "name": "x",
                "source": "s",
                "tree_hash": "a" * 64,
                "level": "adopted",
                "method": "manual-review",
                "validated_by": "skill",
                "validated_at": "2026-07-19",
                "audience": "everyone",
            }
        )


def test_delivered_via_map_pins() -> None:
    # The entity seat's named consumer contract (cognition room seq 175):
    # delivered_via_map kills their name==entity-self-knowledge fallback.
    by_name = {r.name: r for r in _registry().validations}
    assert by_name["entity-self-knowledge"].delivered_via_map is True
    assert by_name["entity-observation"].delivered_via_map is False
    # A host-only skill can never claim map delivery (the map is an
    # entity-prompt surface).
    with pytest.raises(SkillValidationError, match="contradicts audience"):
        ValidationRecord.from_dict(
            {
                "name": "x",
                "source": "s",
                "tree_hash": "a" * 64,
                "level": "adopted",
                "method": "manual-review",
                "validated_by": "skill",
                "validated_at": "2026-07-19",
                "audience": "host",
                "delivered_via_map": True,
            }
        )


def test_shelf_audience_pins() -> None:
    by_name = {r.name: r.audience for r in _registry().validations}
    # The ONE entity-audience skill (its capability_map reference IS the
    # entity teaching; laurent's default ruling).
    assert by_name["entity-self-knowledge"] == "entity"
    # Observer-facing: must never enter an entity prompt (the skill's own
    # audience line, now structural).
    assert by_name["entity-observation"] == "host"
    # Conditional: entity-appropriate only when an entity joins the hub.
    assert by_name["agora-collaboration"] == "either"
    # Everything else on today's shelf is host-audience (dev/process
    # skills, vendored third-party). Widening any is a deliberate act.
    for name, audience in by_name.items():
        if name not in ("entity-self-knowledge", "agora-collaboration"):
            assert audience == "host", (name, audience)
