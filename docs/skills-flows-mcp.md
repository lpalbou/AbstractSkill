# Skills, Workflows, and MCP — which one, when

AbstractFramework has three ways to extend what an agent can do. They look
similar from a distance ("all three add capabilities") but they live at
different layers, travel differently, and fail differently. This page is the
decision guide.

**TL;DR: skills for judgment, flows for execution, MCP for reach.**

One sentence each:

- A **skill** is a portable procedure pack — versioned expertise (a folder
  with a `SKILL.md`) that any agent, in any agentic framework, can load into
  its context and follow. Skills ACTIVATE: they shape how an agent thinks
  and works. A skill is a higher-level view over capabilities and tools — a
  subpart of a cognition.
- A **workflow (flow)** is a durable executable graph — nodes, edges, waits,
  and effects that AbstractRuntime executes and AbstractGateway serves, with
  an append-only ledger, resumability, and replay. Flows RUN: they are the
  execution unit of this framework, and only this framework.
- **MCP (Model Context Protocol)** is a wire protocol for tool servers —
  a standard way to reach tools that live in another process or on a remote
  machine, from this framework or any MCP-speaking client. MCP CONNECTS:
  it is transport for capabilities, not the capability's logic or judgment.

## The comparison

| | Skill | Workflow (flow) | MCP server |
|---|---|---|---|
| Reach for it when | The agent needs judgment, method, or knowledge — or must work outside AbstractFramework | The work must survive crashes, wait for humans, or be audited step by step | The tool lives behind a network/process boundary you connect to |
| What it is | Markdown procedure pack (`SKILL.md` + optional resources) | Executable graph in a versioned bundle (`.flow`) | Protocol endpoint exposing tools/resources |
| Unit of | Expertise / method | Execution / orchestration | Tool transport |
| Runs where | Inside the agent's own reasoning (prompt context) | On AbstractRuntime, served by AbstractGateway | On the server that hosts it (local or remote) |
| Portability | Any agent, any framework (the ecosystem compatibility layer — Claude Code, Codex, abstractcode, others) | AbstractFramework only | Any MCP client, any framework |
| Durability | None of its own — the hosting agent's run is durable, not the skill | Native: ledger, waits, resume, crash-replay | None of its own — calls are request/response |
| Enforcement | None — the model may ignore or misread it | Structural — the framework guarantees the steps, order, and typed data; LLM/tool outputs inside nodes still vary | Per-call — the protocol is precise; the server's behavior is its own |
| State | Stateless content (byte-pinned, hash-verified) | Durable run state (vars, waits, artifacts) | Server-side — treat as outside your trust boundary, even for local servers (a separate process you must gate) |
| Trust model | Content trust: tree hash + validation records + advisories (the abstractskill gate) | Code trust: immutable published bundle versions, tool grants + approval policies at run time | Boundary trust: authentication, allowlists, per-tool approval; treat as external |
| Composition | Skills can only narrow the operator's tool grant, never widen beyond it (multi-skill bound is shared: `grant ∩ union(declared)`) | Calls tools, spawns subflows/agents; skill activation inside runs is the designed composition (hosts adopt it progressively) | Its tools enter the SAME grant/approval lanes as native tools |
| Fails by | Being ignored or misread by the model | A failed or waiting run, visible in the ledger | Network/server errors, or a lying tool result |
| Cost of adding one | Write markdown, curate, pin to exact bytes | Author a graph, test, publish a bundle | Stand up/point at a server, declare and gate its tools |

One boundary note: skills may ship `scripts/`, but scripts never run
implicitly — script-bearing skills require operator review at the gate, and
script execution additionally requires an explicit tool grant.

## Decision rules

1. **Is it knowledge or method — "how to think about X"?** Skill. Review
   checklists, API usage patterns, process discipline, teaching an entity
   its own faculties: none of these need an executor; they need to be READ
   at the right moment. If it must also work outside AbstractFramework
   (Claude Code, Codex, any SKILL.md-aware agent), it can only be a skill.
2. **Must it survive a crash, wait for a human, run for hours, or be
   audited step by step?** Workflow. Durability, waits, approvals, replay,
   and per-step ledgers are flow properties; no amount of skill prose gives
   you them.
3. **Does the capability live in another service or on another machine —
   something you connect to rather than spawn?** MCP. Remote browsers,
   corporate databases, third-party SaaS tools — protocol first, then gate
   its tools like any other grant. (A capability in your own process, or a
   program the host can simply run, is a NATIVE TOOL — none of the three;
   this page only arbitrates the three extension mechanisms above the
   native tool baseline.)
4. **Mixed?** Compose. The common shapes:
   - An external agent reads the `abstractframework-gateway` skill and
     drives flows over HTTP — the skill is the bridge INTO the framework;
     the flow does the durable work once inside. This pattern is fully
     live today.
   - A skill instructs the agent to use MCP-served tools well — the skill
     provides judgment, MCP provides reach.
   - A flow's agent node activates skills for judgment inside a durable
     run — the DESIGNED pairing (the flow provides durability, the skill
     provides method); hosts adopt it progressively, abstractcode first.
     A live in-framework example of the same pattern: AbstractFlow's
     authoring assistant rides a 600+-line method document (its
     workflow-authoring skill) on the planner prompt of a gateway-hosted
     durable run — the skill teaches how to think about workflow
     structure, the run executes the authoring cycles.

One vocabulary neighbor worth separating: flows also declare INTERFACES
(e.g. `abstractcode.agent.v1`) — a skill declares METHOD to models, while
an interface declares a flow's CONTRACT to hosts (which inputs/outputs make
it runnable in a given slot). Interface declarations are self-declared and
not yet machine-validated (the governance registry is designed, not built),
so treat them as claims a host checks, not guarantees.

Rule of thumb: **skills for judgment, flows for execution, MCP for reach.**
When someone proposes a new capability, ask which of the three failure
modes you can least afford — misreading (skill), losing progress (flow), or
crossing a network boundary blind (MCP) — and anchor the design there.

## Why a workflow is not "a better skill" everywhere

A workflow encodes procedure as executable structure: the framework, not the
model, guarantees the steps happen, in order, with typed data and durable
waits. That is strictly stronger *inside* AbstractFramework — and worthless
outside it, because nothing else executes the graph. A skill encodes
procedure as language: any capable agent anywhere can follow it, but nothing
enforces it. They are the same intent at two trust levels, and the
portability/enforcement trade is exactly why both exist. Skills are
necessary regardless of how good flows get: they are the compatibility layer
with the ecosystem outside the framework, the way MCP is the compatibility
layer with tools outside the process.

## Responsibilities by package

- **abstractskill** owns the skill contract: parsing/validation of
  `SKILL.md`, filesystem discovery with progressive disclosure, byte-exact
  tree hashing, the trust registry (validations, advisories, the
  activation gate `select_skills_for_context`), the curated catalog +
  vendoring pipeline, and `allowed-tools` composition semantics.
- **abstractflow** owns workflow authoring (editor + assistant) and the
  VisualFlow format; **abstractruntime** owns the compiler + the `.flow`
  bundle format and executes flows durably; **abstractgateway** serves them
  (bundles, runs, ledgers, waits, commands) and is the one HTTP door —
  including for external agents.
- **MCP integration** is served at the boundary that executes tools: MCP
  tools are declared and gated beside native tools (grant lanes, approval
  policies), never as a separate privilege system.
- Hosts (abstractcode, gateway-served agents, entity runtimes) are where
  the three MEET: a host selects skills through the trust gate, runs flows
  through the runtime, and reaches MCP tools through its tool executor.
  Honest adoption state: skill selection ships in abstractskill today and
  abstractcode consumes it (its `/skills` command); the gateway-served and
  entity-runtime activation lanes are designed and being adopted
  progressively.

## Getting started with each

- Skills: [getting-started.md](getting-started.md) for the library,
  [skills-catalog.md](skills-catalog.md) for what to vendor and why.
- Workflows: author in the AbstractFlow editor, publish bundles through the
  gateway (see the AbstractGateway repository's `docs/api.md`).
- MCP: configure servers at the tool-executing boundary (see the
  AbstractRuntime repository's MCP worker documentation); their tools then
  gate like any native tool.

## See also

- The shelf's `abstractframework-gateway` skill — the practical entrance
  guide this page's theory points at.
- [skills-catalog.md](skills-catalog.md) — every curated skill, with trust
  rationale.
