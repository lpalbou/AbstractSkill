"""AbstractSkill — Agent Skills parsing and discovery for AbstractFramework."""

from abstractskill.errors import (
    SkillError,
    SkillNotFoundError,
    SkillParseError,
    SkillValidationError,
)
from abstractskill.hash import content_hash
from abstractskill.loader import FilesystemSkillLoader
from abstractskill.models import LoadedSkill, SkillDocument, SkillMetadata
from abstractskill.parser import parse_skill_md
from abstractskill.prompt import format_available_skills_xml
from abstractskill.validation import SKILL_FILENAME, SKILL_NAME_RE, validate_skill_name

__all__ = [
    "FilesystemSkillLoader",
    "LoadedSkill",
    "SKILL_FILENAME",
    "SKILL_NAME_RE",
    "SkillDocument",
    "SkillError",
    "SkillMetadata",
    "SkillNotFoundError",
    "SkillParseError",
    "SkillValidationError",
    "content_hash",
    "format_available_skills_xml",
    "parse_skill_md",
    "validate_skill_name",
]

__version__ = "0.1.0"
