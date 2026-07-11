from __future__ import annotations

from abstractskill.models import SkillMetadata
from abstractskill.policy import effective_tools, effective_tools_for_skill


def _skill(name: str, allowed: tuple[str, ...] = ()) -> SkillMetadata:
    return SkillMetadata(name=name, description="d", allowed_tools=allowed)


GRANT = ("read_file", "write_file", "web_search")


def test_absence_implies_nothing_grant_stands() -> None:
    result = effective_tools(GRANT, [_skill("knowledge-only")])
    assert result.allowed == frozenset(GRANT)
    assert result.narrowed_by_skills is False
    assert result.undeclared_skills == ("knowledge-only",)
    assert result.warnings == ()


def test_declared_skills_narrow_to_union_intersect_grant() -> None:
    result = effective_tools(
        GRANT,
        [_skill("reader", ("read_file",)), _skill("searcher", ("web_search",))],
    )
    # Union of declared sets, intersected with the grant — two disjoint
    # skills must not zero the set (strict pairwise intersection would).
    assert result.allowed == frozenset({"read_file", "web_search"})
    assert result.narrowed_by_skills is True


def test_skills_never_widen_beyond_grant() -> None:
    result = effective_tools(
        ("read_file",),
        [_skill("greedy", ("read_file", "execute_command"))],
    )
    assert result.allowed == frozenset({"read_file"})
    assert ("greedy", "execute_command") in result.unresolved_tokens
    assert any("#FALLBACK" in warning for warning in result.warnings)


def test_empty_grant_denies_all() -> None:
    result = effective_tools((), [_skill("reader", ("read_file",))])
    assert result.allowed == frozenset()


def test_name_map_translates_ecosystem_tokens() -> None:
    result = effective_tools(
        GRANT,
        [_skill("editor", ("Edit",))],
        name_map={"Edit": ("read_file", "write_file")},
    )
    assert result.allowed == frozenset({"read_file", "write_file"})
    assert result.unresolved_tokens == ()
    assert result.out_of_grant_names == ()


def test_unmapped_token_drops_with_fallback_never_relaxes() -> None:
    result = effective_tools(
        GRANT,
        [_skill("claude-flavored", ("Bash(git:*)",))],
    )
    # The only declared skill's tokens all failed to map: the declared
    # bound is empty — nothing is sanctioned, policy is never relaxed.
    assert result.allowed == frozenset()
    assert ("claude-flavored", "Bash(git:*)") in result.unresolved_tokens
    assert any("#FALLBACK" in warning for warning in result.warnings)


def test_partial_mapping_narrows_loudly_not_silently() -> None:
    # Edit maps to two names but only one is granted: the dropped half
    # must surface as out-of-grant with a #FALLBACK, never vanish.
    result = effective_tools(
        ("read_file",),
        [_skill("editor", ("Edit",))],
        name_map={"Edit": ("read_file", "write_file")},
    )
    assert result.allowed == frozenset({"read_file"})
    assert ("editor", "write_file") in result.out_of_grant_names
    assert any("write_file" in warning for warning in result.warnings)


def test_declared_bound_active_even_when_union_equals_grant() -> None:
    result = effective_tools(GRANT, [_skill("full", GRANT)])
    assert result.allowed == frozenset(GRANT)
    assert result.declared_bound_active is True
    assert result.narrowed_by_skills is False


def test_per_skill_view_is_the_least_privilege_bound() -> None:
    # Co-active declared skills widen each other up to the grant in the
    # union view; the per-skill view stays the tight bound.
    tight = _skill("tight", ("read_file",))
    wide = _skill("wide", GRANT)
    union_view = effective_tools(GRANT, [tight, wide])
    assert union_view.allowed == frozenset(GRANT)

    per_skill = effective_tools_for_skill(GRANT, tight)
    assert per_skill.allowed == frozenset({"read_file"})
    assert per_skill.declared_bound_active is True


def test_mixed_declared_and_undeclared_keeps_narrowing() -> None:
    result = effective_tools(
        GRANT,
        [_skill("reader", ("read_file",)), _skill("knowledge-only")],
    )
    assert result.allowed == frozenset({"read_file"})
    assert result.declared_skills == ("reader",)
    assert result.undeclared_skills == ("knowledge-only",)
