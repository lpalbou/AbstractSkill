"""AbstractSkill — Agent Skills parsing and discovery for AbstractFramework."""

import logging

# Library-standard practice: never emit to stderr via the last-resort
# handler; hosts configure logging (or pass on_warning callbacks).
logging.getLogger("abstractskill").addHandler(logging.NullHandler())

from abstractskill.catalog import (
    CatalogEntry,
    SkillCatalog,
    lint_catalog,
    load_catalog,
)
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
from abstractskill.policy import EffectiveTools, effective_tools, effective_tools_for_skill
from abstractskill.prompt import format_available_skills_xml
from abstractskill.selection import SkillSelection, select_skills_for_context
from abstractskill.tree import (
    SkillInventory,
    SkillResource,
    hash_skill_tree,
    inspect_skill_dir,
    read_skill_resource,
)
from abstractskill.trust import (
    AdvisoryEntry,
    DerivedSource,
    GuidanceEntry,
    Severity,
    TrustLevel,
    TrustRegistry,
    TrustVerdict,
    ValidationRecord,
    evaluate_trust,
    lint_registry,
)
from abstractskill.validation import (
    MAX_COMPATIBILITY_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_NAME_LENGTH,
    SKILL_FILENAME,
    SKILL_NAME_RE,
    validate_compatibility,
    validate_description,
    validate_skill_name,
)

__all__ = [
    "AdvisoryEntry",
    "CatalogEntry",
    "DerivedSource",
    "EffectiveTools",
    "FilesystemSkillLoader",
    "GuidanceEntry",
    "LoadedSkill",
    "MAX_COMPATIBILITY_LENGTH",
    "MAX_DESCRIPTION_LENGTH",
    "MAX_NAME_LENGTH",
    "SKILL_FILENAME",
    "SKILL_NAME_RE",
    "Severity",
    "SkillDocument",
    "SkillError",
    "SkillInventory",
    "SkillMetadata",
    "SkillCatalog",
    "SkillNotFoundError",
    "SkillParseError",
    "SkillResource",
    "SkillSelection",
    "SkillValidationError",
    "TrustLevel",
    "TrustRegistry",
    "TrustVerdict",
    "ValidationRecord",
    "content_hash",
    "effective_tools",
    "effective_tools_for_skill",
    "evaluate_trust",
    "format_available_skills_xml",
    "hash_skill_tree",
    "inspect_skill_dir",
    "lint_catalog",
    "lint_registry",
    "load_catalog",
    "parse_skill_md",
    "read_skill_resource",
    "select_skills_for_context",
    "validate_compatibility",
    "validate_description",
    "validate_skill_name",
]

__version__ = "0.1.0"
