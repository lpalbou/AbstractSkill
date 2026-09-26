# Troubleshooting

Each entry names a symptom, its likely cause, and the fix. For setup, see
[Getting started](getting-started.md); for concepts and limits, see the
[FAQ](faq.md).

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
Re-validate: regenerate `src/abstractskill/registry/validations.yaml` with
`scripts/refresh_shelf.py` (for shelf skills) and review the diff.

## `SkillValidationError: resource ... is N bytes, over the M-byte cap`

`read_skill_resource` refuses oversize reads rather than truncating. Raise
`max_bytes` if the larger read is intended.

## Registry load returned zero advisories unexpectedly

Check you passed the right file to the right parameter. Loading an advisories
file into `validations_path` (or vice versa) logs a `#FALLBACK` warning on the
`abstractskill` logger and returns zero entries rather than crashing.

## Seeding the bundled registry

These entries cover `seed_registry` (see
[Getting started](getting-started.md#seed-the-bundled-shelf-into-a-host-directory)
and the [API reference](api.md#bundled-registry)).

### A bundled skill is not refreshed after an upgrade

`seed_registry` refreshes an item only while it is byte-identical to what an
earlier seed wrote. Everything else is kept, with its reason:

```python
report = seed_registry(shelf)
print(report.bundled_version, report.previous_version)
for item, reason in report.kept.items():
    print(item, reason)
```

- `kept_user_modified` or `kept_foreign` — the copy at the destination
  differs from anything a seed wrote. Compare it with the bundled copy under
  `bundled_registry_dir()`. To take the bundled version, move your copy out
  of the shelf and seed again; the item is then `added`.
- `kept_unknown_provenance` — the destination has no `.seeded.json`, so the
  seed cannot tell an old seeded copy from an edit. Restore `.seeded.json`
  from a backup, or move the item out and seed again.
- `kept_newer` — the installed abstractskill carries an older bundle than the
  one that last seeded this shelf (`bundled_version < previous_version`).
  Upgrade abstractskill.
- `kept_symlink` — the item is a symlink, which seeding never follows. Replace
  it with a real folder or file if you want the bundled content.
- `kept_unreadable` — the item cannot be hashed (for example an unreadable
  file, or a symlink inside a skill folder). Fix the permissions or remove the
  symlink.

Verify: seed again; the item is listed in `added`, `updated` or `unchanged`.

### A skill removed from the bundle is still on the shelf

Seeding never deletes. Items an earlier seed wrote that the bundle no longer
contains are listed in `report.not_in_bundle` and stay where they are. Remove
them yourself if you no longer want them served; the next seed drops them
from `.seeded.json`.

### `SkillError: cannot read seed manifest ...` or `seed manifest ... is malformed`

`<dest>/.seeded.json` is damaged. Restore it from a backup of the shelf. If
you have no backup, move the file aside: the next seed adopts items that are
byte-identical to the bundle and reports every other existing item as
`kept_unknown_provenance`.

### `SkillError: seed manifest ... has schema N`

A newer abstractskill wrote the manifest. Upgrade abstractskill to the
version that seeded the shelf, or later.

### `SkillError: ... is a symlink; seed staging must be a real folder`

An entry named `.seed-staging*` in the destination is a symlink. Remove it
and seed again. Real staging folders left by an interrupted seed are cleaned
up automatically.

### `SkillError: refusing to seed into the bundled registry itself`

`dest` points inside the installed package. Seed into a directory your host
owns instead; the package directory is replaced on every upgrade.

### `SkillError: the bundled skill registry is not on the filesystem`

abstractskill was installed in a zipped form. Reinstall it as a regular
package (`pip install abstractskill`).

### `seed_registry` does not return

Seeds of one destination run one at a time under an exclusive lock on
`<dest>/.seed.lock`, so a call waits while another process seeds the same
directory. If it waits indefinitely, find the process holding the lock
(`lsof <dest>/.seed.lock` on macOS and Linux) and let it finish or stop it.
