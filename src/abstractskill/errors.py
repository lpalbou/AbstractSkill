"""Skill-specific exceptions."""


class SkillError(Exception):
    """Base error for AbstractSkill operations."""


class SkillParseError(SkillError):
    """Raised when SKILL.md content cannot be parsed."""


class SkillValidationError(SkillError):
    """Raised when a skill document or directory layout is invalid."""


class SkillNotFoundError(SkillError):
    """Raised when a requested skill cannot be resolved."""
