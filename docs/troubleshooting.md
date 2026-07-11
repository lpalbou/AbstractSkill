# Troubleshooting

## `SkillParseError: SKILL.md must start with YAML frontmatter`

The file does not begin with a `---` frontmatter delimiter at column 0. A
byte-order mark is tolerated, but the first non-BOM line must be `---`. An
indented `---` is treated as YAML content, not a delimiter.

## `SkillValidationError: skill name must use lowercase letters, digits, and single hyphens`

The `name` violates the spec: use 1-64 lowercase alphanumeric characters and
single hyphens, with no leading, trailing, or consecutive hyphens (`pdf-tools`
is valid; `pdf--tools`, `-pdf`, `PDF` are not). The name must also match the
skill's directory name.

## `SkillValidationError: skill description must be at most 1024 characters`

Trim the `description` to the spec ceiling (1024). `compatibility` has a 500
ceiling.

## A skill I can see in `discover()` fails to `load()`

They resolve identically, so this should not happen for a valid skill. If a
higher-precedence root holds a broken copy, both surface a `#FALLBACK` warning
and fall back to the valid lower-precedence copy. Pass `on_warning=print` to
see the warnings.

## A trust verdict says `requires_review` for a skill I trust

The verdict is fail-closed. Common causes: no `ValidationRecord` matches the
skill's current tree hash (it was edited or never validated — run
`scripts/refresh_shelf.py` for shelf skills), the skill contains `scripts/`
(`has_scripts` forces review), or a low/medium advisory matched. The verdict's
`reasons` name the exact cause.

## A validation stopped applying after I edited a skill

Trust binds to bytes. Any edit changes the tree hash and voids the old record.
Re-validate: regenerate `registry/validations.yaml` with
`scripts/refresh_shelf.py` (for shelf skills) and review the diff.

## `SkillValidationError: resource ... is N bytes, over the M-byte cap`

`read_skill_resource` refuses oversize reads rather than truncating. Raise
`max_bytes` if the larger read is intended.

## Registry load returned zero advisories unexpectedly

Check you passed the right file to the right parameter. Loading an advisories
file into `validations_path` (or vice versa) logs a `#FALLBACK` warning on the
`abstractskill` logger and returns zero entries rather than crashing.
