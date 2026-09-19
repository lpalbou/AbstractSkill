# Recurrent: Advisory & validation registry review

## Metadata
- Created: 2026-07-11
- Status: Recurrent
- Completed: N/A (runs repeatedly)

## Purpose
Keep the trust registry (advisories + validations) faithful: references stay
live, findings stay accurate, validation records stay bound to current hashes.

## Run conditions
- On any change to `registry/advisories.yaml` or `registry/validations.yaml`.
- On a periodic cadence once 0006 lands (host-scheduled, not agent-persisted).
- Whenever a shelf skill's tree hash changes (re-validation required).

## Scope
`registry/*.yaml`, shelf hashes, advisory reference liveness.

## Checklist
- [ ] Every advisory has all four mandated fields and a resolvable reference.
- [ ] Severity values are in the closed set.
- [ ] Each ValidationRecord's tree_hash matches the current shelf tree.
- [ ] Withdrawn advisories retain a reason + date (never deleted).
- [ ] overview.md counts/ledgers match the registry.

## Expected output
A clean registry or a diff proposed for review; drift reported, never silently fixed by auto-import.

## Non-goals
No auto-apply of external findings; no agent-side scheduler.
