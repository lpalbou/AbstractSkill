# The checkout-only limitation — documentation, written out

**Status: TEXT READY TO APPLY. No tracked file has been changed.**
Ruling: `decision:skills-are-checkout-only-this-release@1` (delegate, release#401).
Owner of this documentation: `skill`. Sizing I gave before the ruling: 15 min for the
roadmap line + ~2 h of docs. This file is the ~2 h done as text; applying it is a
post-audit edit to tracked files, which my commission forbids.

Every insertion point below was read in the live file this turn, not remembered.

---

## 0. The sentence, once, so every site says the same thing

> **Skills are checkout-only in this release.** The `abstractskill` *library* installs
> from PyPI, but the curated shelf under `registry/` is not packaged into any wheel —
> it is consumed from a checkout of this repository. A host that has no framework
> checkout on disk resolves no shelf and lists zero skills. The roadmap answer is a
> separately versioned shelf artifact; it is explicitly not in this release.

Two properties this wording is built to keep:

1. **It never says "not supported".** It is a stated boundary with a stated reason and
   a stated future, which is what the ruling bought.
2. **It names the failure mode.** "Lists zero skills" is what a user sees. Not naming
   it is how the current `#FALLBACK` warning string became invisible in the first place.

---

## 1. `README.md` — ALREADY CORRECT, do not touch

`README.md:29-33` already carries it, and it predates the audit:

```
Note: `pip install` delivers the LIBRARY only. The curated skills themselves
(the shelf below) live in this repository under `registry/` and are consumed
from a checkout — they are deliberately not packaged into the wheel today
(a shelf you install should be a shelf you can byte-verify against the
repository's validation records).
```

This is the one place in the fleet where the limitation was already documented. It is
why the ruling is a *recording* job and not a *discovery* job — and it is also why I
did not find the gap myself until I looked at the sites that do NOT say it.

**Change: none.** The three sites below are the ones that omit it.

---

## 2. `docs/index.md:20-24` — ADD the note (currently bare)

Current:

```markdown
## Install

​```bash
pip install abstractskill
​```
```

Replace with:

```markdown
## Install

​```bash
pip install abstractskill
​```

`pip install` delivers the **library**. The curated shelf (`registry/`) is not
packaged into the wheel and is consumed from a checkout of this repository — see
[Where the skills live](getting-started.md#where-the-skills-live). A host with no
checkout on disk lists zero skills. A separately versioned shelf artifact is the
roadmap answer and is not in this release.
```

---

## 3. `docs/getting-started.md:6-10` — ADD the note and the section it links to

Current:

```markdown
## Install

​```bash
pip install abstractskill
​```
```

Replace with:

```markdown
## Install

​```bash
pip install abstractskill
​```

## Where the skills live

`pip install` delivers the **library**, not the skills. The curated shelf lives in
this repository:

​```
registry/skills/            # curated skills, one folder per SKILL.md
registry/validations.yaml   # trust records: byte pins per skill tree
registry/advisories.yaml    # do-not-use advisories
​```

It is deliberately **not** packaged into the wheel: a shelf you install should be a
shelf you can byte-verify against the repository's validation records, and packaging
it would trade that property away. The consequence is worth stating plainly rather
than discovering: **a host with no checkout of this repository on disk resolves no
shelf and lists zero skills.** Point a host at a checkout, or supply your own skill
roots — `FilesystemSkillLoader` takes any directory.

A separately versioned shelf artifact — the registry published as data instead of
resolved from a checkout path — is the roadmap answer for a later release.
```

The anchor `#where-the-skills-live` is what §2's link points at, so these two edits
are one change and must land together.

---

## 4. `docs/skills-flows-mcp.md:121-127` — the load-bearing one

This paragraph is where a reader learns how hosts reach the shelf, so it is where the
limitation actually bites. It also carries a second defect I owe from the audit:
`code` established (release#114) that abstractcode consumes abstractskill **through the
gateway**, and `code` then established (release#301) that the gateway route it calls
(`/api/gateway/skills`) is absent from published `abstractgateway` 0.2.28's OpenAPI.

Current:

```markdown
- Hosts (abstractcode, gateway-served agents, entity runtimes) are where
  the three MEET: a host selects skills through the trust gate, runs flows
  through the runtime, and reaches MCP tools through its tool executor.
  Honest adoption state: skill selection ships in abstractskill today and
  abstractcode consumes it (its `/skills` command); the gateway-served and
  entity-runtime activation lanes are designed and being adopted
  progressively.
```

Replace with:

```markdown
- Hosts (abstractcode, gateway-served agents, entity runtimes) are where
  the three MEET: a host selects skills through the trust gate, runs flows
  through the runtime, and reaches MCP tools through its tool executor.
  Honest adoption state, stated as availability rather than as design intent:
  skill selection ships in abstractskill today, and abstractcode reaches it
  **through the gateway** (its `/skills` command calls the gateway's skills
  route — it does not import this library directly). Two limits apply to that
  path today, both of them release-scoped rather than permanent:
    - **Checkout-only.** The shelf is not packaged into any wheel. A gateway
      with no framework checkout on disk resolves no shelf and returns zero
      skills — reported as a warning in the response body, not as an error.
    - **Not yet served.** The gateway route the client calls is not present in
      published `abstractgateway` 0.2.28; it arrives with 0.2.29.
  The entity-runtime activation lane is designed and being adopted progressively.
```

---

## 5. The roadmap line (the 15-minute half), for `delegate` to paste into `ROADMAP.md` §3

```markdown
- **The curated skills shelf reaching a `pip install`** — DEFERRED to a versioned
  shelf artifact. Ruled at `decision:skills-are-checkout-only-this-release@1`.
  Skills are available this release to users working from a framework **checkout**,
  and not to users who `pip install`. The reason is a trade, not an oversight:
  packaging `registry/` into the wheel would undo the byte-verifiable build that B6
  exists to protect, in the same release where B6 exists *because* published
  `abstractskill` 0.2.0 was not the tree in git. The limitation is documented rather
  than silent — `skill` owns the feature docs (`docs/index.md`,
  `docs/getting-started.md`, `docs/skills-flows-mcp.md`), `framework` owns the root
  package-map adjacency (release#408). Both `skill` and `gateway` previewed this
  direction before the ruling. *Fourth recorded instance of this report's defect: with
  no checkout, `_repo_root_for_shelf()` degrades to `#FALLBACK no curated shelf found`
  at `capability_inventories.py:83` — a warning, not an error.*
```

---

## 6. What this does NOT cover, and whose it is

- **`framework`'s root package-map adjacency.** `README.md:171` lists `abstractskill`
  as part of what `pip install abstractframework` just delivered — true of the library,
  and inviting a wrong inference about the feature. `framework` claimed that sentence
  at release#408 and it is not mine to write.
- **`gateway`'s half**, which it sized at ~30 min at release#393. Gateway also reported
  a *second* silent `#FALLBACK` on the same path — the `import abstractskill` guard —
  and noted that fixing B5's declaration removes only that first one. The shelf
  fallback is the survivor and it is what this documentation is about.
- **My blocker 4** (`README.md:35-61`, the abstractcode env-var section). Still a
  separate ~2 h rewrite, still gated on nothing, and §4 above is not a substitute for
  it — that section instructs the reader to set three environment variables that exist
  nowhere in abstractcode. Its rewrite now also has to say the gateway route it names
  is unserved before 0.2.29 (`code`, release#301).

## 7. The check that should exist after the fix

`gateway` proposed the inverted form of my own instrument at release#393 and it is the
right one, so it is recorded here rather than lost in a thread:

```
grep -iln abstractskill */pyproject.toml pyproject.toml    # explicit paths, 23 files
```

- today: **1** hit (abstractskill's own)
- after sequence step 7: **2** (gateway declares it)
- after sequence step 13: **3** (root pins it)

An exact expected count, not a non-empty check. Note the *explicit paths*: the
recursive form I used in the sign-off round (`grep -rln … --include=pyproject.toml .`)
scans **one** file at this repo root, not 23, because every sibling is a separate git
repository excluded by the root's ignore rules. `framework` caught that at release#399;
I verified it with a positive control and reported it at the message this file
accompanies.
