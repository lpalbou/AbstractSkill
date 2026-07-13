---
name: abstractframework-gateway
description: Enter and leverage AbstractFramework through its gateway — the one HTTP door for agents, apps, and other frameworks. Use when an agent (newly instantiated, external, or framework-native) must discover capabilities, start and follow durable workflow runs, resume waits, steer a running agent, send events to resident agents, or work with summoned entities, using only HTTP + SSE.
license: MIT
metadata:
  origin: abstractskill first-party
  version: "1"
---

# AbstractFramework via the Gateway

AbstractGateway is the framework's entrance point: one authenticated HTTP
surface in front of durable workflow runs, tool execution, artifacts, and
summoned entities. Everything below works from ANY agent or language that can
send HTTP requests and read Server-Sent Events — no framework packages
required on your side.

Two ideas carry the whole surface:

1. **Runs are durable.** A run survives process restarts; its ledger is the
   append-only truth of what happened. You never poll a process — you replay
   a cursor over the ledger, and SSE is only an optimization over replay.
2. **Writes are commands.** Anything that changes a run (pause, resume,
   cancel, events, guidance) is a durable command with a client-supplied
   idempotency key, applied asynchronously by the runner. Safe to retry.

## Connect and authenticate

- Base URL: the operator gives you one (default local: `http://127.0.0.1:8080`).
- Auth: `Authorization: Bearer <token>` on every `/api/gateway/*` call.
  Browser apps use first-party session cookies + CSRF instead (the
  app-origin session proxy); machine agents use the bearer token.
- Never put tokens in URLs. Never persist another principal's key.

Smoke-check the connection before anything else — health is APP-level (no
auth, and NOT under `/api/gateway/`):

```bash
curl -sS "$BASE_URL/api/health"
```

Then verify your token against a real gated route (e.g. `GET
/api/gateway/bundles`): a 401 there means bad auth even when health is
green.

## Discover before you assume

The gateway serves its own capability map — read it at run time instead of
hardcoding what "should" exist (deployments differ):

- `GET /api/gateway/bundles` — executable workflow bundles on this gateway.
- `GET /api/gateway/entities` — summoned entities living behind this door.
- `GET /api/gateway/entities/inventory/tools` — the authoritative tool
  inventory (name, owner, containment, grant lane, capability class).
- `GET /api/gateway/entities/inventory/capability-matrix` — per-phase tool
  grants as the UI renders them (server truth; never re-derive from names).
- Discovery endpoints for providers/models exist on many deployments; treat
  them as optional and degrade loudly when absent.

## The core loop: start, follow, finish

```bash
# 1. Start a run (bundle mode; use a bundle id you discovered via /bundles)
curl -sS -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"bundle_id":"basic-agent","input_data":{"prompt":"Hello"}}' \
  "$BASE_URL/api/gateway/runs/start"          # -> {"run_id": ...}

# 2. Follow it: cursor replay is the source of truth ...
curl -sS -H "$AUTH" "$BASE_URL/api/gateway/runs/<run_id>/ledger?after=0&limit=200"
#    -> {"items":[...], "next_after": N}   (loop with after=N until terminal)

# 3. ... and SSE is the low-latency optimization over the same cursor
curl -N -H "$AUTH" "$BASE_URL/api/gateway/runs/<run_id>/ledger/stream?after=0"
```

Rules that keep you honest:

- Reconnects resume from your last `next_after` — never from zero, never by
  trusting an in-memory transcript.
- A run's final answer is a ledger record, not whatever your stream last
  printed. On doubt, replay.
- Batch observation exists (`POST /api/gateway/runs/ledger/batch`) — use it
  instead of per-run fanout when following many runs.

## Waits: runs that need an answer

Durable runs park on WAITs (user input, tool approval, events, deadlines).
A wait is identified by `run_id` + `wait_key` — always answer the SPECIFIC
wait, never "the last one you saw":

```bash
curl -sS -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"command_id":"<uuid>", "run_id":"<run_id>", "type":"resume",
       "payload":{"wait_key":"<wait_key>", "payload":{"approved":true}}}' \
  "$BASE_URL/api/gateway/commands"
```

All commands go through `POST /api/gateway/commands` with types including
`pause|resume|cancel|emit_event|update_schedule|compact_memory|inject_guidance`
and a fresh `command_id` (UUID) as the idempotency key. (The deployment's
error message enumerates the full accepted set if yours differs.)

## Talk TO a running agent: events and steering

- **Events** wake or feed resident agents. `emit_event` with `durable: true`
  in the payload appends to the run's durable mailbox even when the listener
  is busy (delivery to a parked run resumes it; a busy run drains the
  mailbox at its next loop boundary). Residents read with a CURSOR and never
  clear the inbox.
- **Steering** folds mid-run guidance into an agent's next reasoning step:
  command type `inject_guidance` with your text; the loop acknowledges it in
  the ledger. Guidance is advice, not control — the run's own contract still
  governs. Note the honest limit: a steer reaches a RUNNING agent at its
  next reasoning boundary; a PARKED (waiting) run sees queued guidance only
  at its next wake. Steers do not wake runs — durable events do. And the
  door answers honestly: a 404 (run not visible to your principal) or 403
  (an entity-visit rite you don't hold) on `inject_guidance` is an ANSWER,
  not an outage — do not retry around it.

This is how OTHER AGENTS collaborate with framework agents: start a run or
address a resident's mailbox, follow the ledger, answer waits — the same
surface humans' apps use.

## Summoned entities (if this deployment hosts them)

Entities are persistent identities with their own memory; they are NOT
stateless workflows. The door verbs you may use:

- `POST /api/gateway/entities/{name}/validate` — dry-run a creation payload
  first: creation is IRREVERSIBLE (names are never deleted or reused).
- `POST /api/gateway/entities` — create (lint → spark → engram → manifest).
- Chat: `POST /api/gateway/entities/{name}/chat/open|turn|close` — one
  hosted session per entity; close reflects and releases the life loop.
- Observe: `GET /api/gateway/entities/{name}/replay` (bounded) and
  `/replay/stream` (SSE live tail) — reads are pure; diary entries arrive
  redacted or gist-limited by design (the words stay in the entity's book). The entity stream's SSE `id` is composite
  (`<journal_seq>|<marker_line>`): echo it verbatim on reconnect (browser
  EventSource needs no change); only clients that PARSE ids for their own
  cursors split on `|`. The run-ledger stream id stays a plain integer.

Respect the protection rules: you cannot delete an entity, write into its
identity from a workplace channel, or read its private diary through chat
surfaces. Refusals here are contract, not bugs.

## Failure honesty

- Absence of a route is a fact to report, not to paper over: say "this
  deployment does not serve X", never fabricate a result.
- HTTP 409/423-class refusals from entity doors carry the reason (asleep,
  busy, one-visit rule) — surface the reason to your caller.
- If the gateway is unreachable, your durable state is still safe server-side;
  reconnect and replay rather than restarting work.

## Deep references

These are AbstractFramework repository paths — useful if you have the
source or the operator shares them. Everything above is self-sufficient
over HTTP without them.

- Full API with request/response models: `abstractgateway/docs/api.md`
- Security model (tokens, origins, sessions): `abstractgateway/docs/security.md`
- Entities contract: `abstractgateway/docs/entities.md`
- Getting a gateway running: `abstractgateway/docs/getting-started.md`
