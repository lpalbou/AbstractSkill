"""Tool-policy composition for skills: grant intersection semantics.

ONE helper family, called by every surface (console preview, runtime
enforcement, gateway door), so the semantics can never fork per consumer.
The ruled semantics:

- The GRANT is the only tool authority. Skill declarations can only ever
  NARROW below it; nothing here can widen beyond the grant. Empty grant
  denies all.
- ABSENCE IMPLIES NOTHING: a skill without ``allowed-tools`` contributes
  no tokens — it is pure knowledge. It never reads as "all tools".
- ``allowed-tools`` tokens are ecosystem-flavored (e.g. Claude Code's
  ``Bash(git:*)``); the HOST owns the token→framework-name mapping table.
  Tokens that resolve to nothing granted are dropped with ``#FALLBACK``
  warnings and NEVER relax policy.

Two composition views, honestly distinct:

- ``effective_tools_for_skill(grant, skill)`` is the LEAST-PRIVILEGE bound
  while one skill's procedure runs — the enforcement primitive.
- ``effective_tools(grant, skills)`` composes several ACTIVE skills as
  ``grant ∩ union(declared)``. The union is the only workable multi-skill
  shape (strict pairwise intersection zeroes disjoint skills), but it is a
  SHARED bound, not a per-skill boundary: co-active declared skills widen
  each other up to the grant. Callers needing per-skill least privilege
  must attribute calls to a skill and use the per-skill view.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from abstractskill.models import SkillMetadata

# Host-owned mapping from ecosystem allowed-tools tokens to framework tool
# names. One token may map to several framework names (e.g. "Edit" →
# read_file + write_file).
ToolNameMap = Mapping[str, str | Sequence[str]]


@dataclass(frozen=True, slots=True)
class EffectiveTools:
    """Result of composing a tool grant with active skills' declarations.

    ``allowed`` — the effective toolset (never wider than the grant).
    ``declared_bound_active`` — at least one skill declared allowed-tools
    (a declared bound exists even when it happens to equal the grant).
    ``narrowed_by_skills`` — the effective set is strictly smaller than
    the grant.
    ``out_of_grant_names`` — (skill, framework_name) pairs that MAPPED
    cleanly but are not granted (dropped, warned).
    ``unresolved_tokens`` — (skill, token) pairs with no mapping entry and
    no granted framework tool of that name (dropped, warned; the library
    cannot tell an unknown ecosystem token from an ungranted framework
    name without the host's full tool inventory).
    """

    allowed: frozenset[str]
    declared_bound_active: bool
    narrowed_by_skills: bool
    declared_skills: tuple[str, ...]
    undeclared_skills: tuple[str, ...]
    out_of_grant_names: tuple[tuple[str, str], ...]
    unresolved_tokens: tuple[tuple[str, str], ...]
    warnings: tuple[str, ...]


def effective_tools(
    grant: Iterable[str],
    skills: Iterable[SkillMetadata],
    *,
    name_map: ToolNameMap | None = None,
) -> EffectiveTools:
    """Compose a tool grant with the active skills' ``allowed-tools``.

    ``grant`` is the operator's tool authority for the current phase.
    ``skills`` are the ACTIVE skills (metadata view). ``name_map`` is the
    host's token→framework-name table for ecosystem-flavored tokens.
    """
    grant_set = frozenset(grant)
    declared_names: list[str] = []
    undeclared_names: list[str] = []
    union_declared: set[str] = set()
    out_of_grant: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str]] = []
    warnings: list[str] = []

    for skill in skills:
        if not skill.allowed_tools:
            undeclared_names.append(skill.name)
            continue
        declared_names.append(skill.name)
        for token in skill.allowed_tools:
            if name_map is not None and token in name_map:
                mapped = name_map[token]
                names = (mapped,) if isinstance(mapped, str) else tuple(mapped)
                for name in names:
                    if name in grant_set:
                        union_declared.add(name)
                    else:
                        # Partial mappings must degrade loudly too: the token
                        # mapped fine, but this name is not granted.
                        out_of_grant.append((skill.name, name))
                        warnings.append(
                            f"#FALLBACK: skill {skill.name!r} token {token!r} maps to "
                            f"{name!r}, which is not granted; dropped (policy never relaxes)"
                        )
            elif token in grant_set:
                union_declared.add(token)
            else:
                unresolved.append((skill.name, token))
                warnings.append(
                    f"#FALLBACK: skill {skill.name!r} allowed-tools token {token!r} "
                    "has no mapping and matches no granted tool; dropped "
                    "(policy never relaxes)"
                )

    if declared_names:
        allowed = frozenset(union_declared)
    else:
        allowed = grant_set

    return EffectiveTools(
        allowed=allowed,
        declared_bound_active=bool(declared_names),
        narrowed_by_skills=allowed != grant_set,
        declared_skills=tuple(declared_names),
        undeclared_skills=tuple(undeclared_names),
        out_of_grant_names=tuple(out_of_grant),
        unresolved_tokens=tuple(unresolved),
        warnings=tuple(warnings),
    )


def effective_tools_for_skill(
    grant: Iterable[str],
    skill: SkillMetadata,
    *,
    name_map: ToolNameMap | None = None,
) -> EffectiveTools:
    """Least-privilege bound while THIS skill's procedure runs.

    This is the enforcement primitive: a host that can attribute a tool
    call to a skill enforces this view, not the multi-skill union.
    """
    return effective_tools(grant, [skill], name_map=name_map)
