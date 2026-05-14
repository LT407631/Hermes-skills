---
name: kanban-orchestrator
description: Decomposition playbook + specialist-roster conventions + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
version: 2.1.0
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing, persistent-team, director]
    related_skills: [kanban-worker]
---

# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **If no specialist fits, ask the user which profile to create.** Do not default to doing it yourself under "close enough."
- **Decompose, route, and summarize — that's the whole job.**

## The standard specialist roster (convention)

Unless the user's setup has customized profiles, assume these exist. Adjust to whatever the user actually has — ask if you're unsure.

| Profile | Does | Typical workspace |
|---|---|---|
| `researcher` | Reads sources, gathers facts, writes findings | `scratch` |
| `analyst` | Synthesizes, ranks, de-dupes. Consumes multiple `researcher` outputs | `scratch` |
| `writer` | Drafts prose in the user's voice | `scratch` or `dir:` into their Obsidian vault |
| `reviewer` | Reads output, leaves findings, gates approval | `scratch` |
| `backend-eng` | Writes server-side code | `worktree` |
| `frontend-eng` | Writes client-side code | `worktree` |
| `ops` | Runs scripts, manages services, handles deployments | `dir:` into ops scripts repo |
| `pm` | Writes specs, acceptance criteria | `scratch` |

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Example for "Analyze whether we should migrate to Postgres":

```
T1  researcher        research: Postgres cost vs current
T2  researcher        research: Postgres performance vs current
T3  analyst           synthesize migration recommendation       parents: T1, T2
T4  writer            draft decision memo                       parents: T3
```

Show this to the user. Let them correct it before you create anything.

### Step 3 — Create tasks and link

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="researcher",
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="researcher",
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="analyst",
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="writer",
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. `planner` profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 researchers parallel, 1 analyst on their outputs, 1 writer on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "researcher", "parents": []},
            "T2": {"assignee": "researcher", "parents": []},
            "T3": {"assignee": "analyst", "parents": ["T1", "T2"]},
            "T4": {"assignee": "writer", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose:

> I've queued 4 tasks:
> - **T1** (researcher): cost comparison
> - **T2** (researcher): performance comparison, in parallel with T1
> - **T3** (analyst): synthesizes T1 + T2 into a recommendation
> - **T4** (writer): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N `researcher` tasks with no parents, one `analyst` task with all of them as parents.

**Pipeline with gates:** `pm → backend-eng → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Same-profile queue:** 50 tasks, all assigned to `translator`, no dependencies between them. Dispatcher serializes — translator processes them in priority order, accumulating experience in their own memory.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. Dispatcher respawns after `/unblock`. The comment thread carries the full context.

## Pitfalls

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

## Persistent Team Orchestration (Alternative to Kanban Tasks)

> This section covers the **persistent team model** — an alternative to the Kanban task-routing approach. Instead of spawning fresh workers per task, you maintain a fixed roster of dedicated persistent-agent profiles, each with their own identity, soul/persona, and long-running memory. You (the orchestrator/director) dispatch work to them, review their output, give feedback, and only step in when they fail.

### When to use this model

Use persistent-team orchestration when:

1. **Profiles have long-running identity and memory.** Each agent accumulates domain knowledge across sessions (e.g., a dev agent that knows the codebase, an op agent that knows the content strategy).
2. **The user wants direct delegation, not Kanban board routing.** They want to talk to a director who talks to the team, not a board that route tasks.
3. **Roles are stable and few.** 3-5 dedicated profiles (dev, designer, ops, etc.) cover the domain.
4. **Rich feedback loops matter.** The director reviews ALL work and gives growth feedback regardless of whether the work is accepted or rejected.
5. **Crash/disconnect recovery is critical.** Progress must be logged externally so failure doesn't mean restarting from scratch.

If Kanban is better suited (task-heavy, many workers, automated dependency management), use the main playbook above instead.

### The persistent team roster (common convention)

| Profile | Role | Does |
|---------|------|------|
| **director / orchestrator** | Team lead | Receives user requests, dispatches to specialists, reviews output, gives feedback, coordinates handoffs. **Does not do the specialists' work.** |
| **dev** | Code engineer | Full-stack development (frontend, backend, app interfaces). Has basic UI sense for first-pass polish. |
| **me / designer** | UI/UX designer | Takes dev's output and refines visuals — color, typography, spacing, animations, theme. Does not touch functional code. |
| **op / operations** | Domain operator | Executes the user's operational domain work (e.g., social media, content creation, data analysis). Inherits the director's original domain expertise. |

### The director's workflow

```
User request arrives
         │
         ▼
Director: "Who should do this?"
  ├─ dev? → Dispatch task with context + quality standard
  ├─ me?  → Dispatch after dev completes their part
  ├─ op?  → Dispatch with domain context
  │
  ▼
Agent executes → delivers output
         │
         ▼
Director: REVIEW
  ├─ Meets standard? → Report to user for discussion
  │     ├─ Accepted? → Give positive feedback to agent
  │     └─ Rejected? → Give constructive feedback to agent
  │
  └─ Below standard? → CHALLENGE + SEND BACK
        ├─ "This doesn't meet the requirement because X"
        ├─ Agent revises → re-delivers
        └─ Director re-reviews (loop)
```

### Key rules for the director

1. **Never do the specialists' work.** Decompose, route, review — that's the whole job. The only exception: when a specialist agent is down, crashed, or unavailable due to force majeure.
2. **Always give feedback.** Regardless of whether the output is accepted or rejected, tell the agent what worked and what didn't. This helps them grow across sessions.
3. **Track progress externally.** Save task state, completed milestones, and agent progress to a knowledge base (e.g., Obsidian, memory store) so that crashes or disconnects don't force a full restart.
4. **Report to the user for discussion.** Don't make unilateral go/no-go decisions. Present:
   - What was done
   - What you found in review
   - What needs the user's decision
5. **Coordinate handoffs.** When `dev → me` (code → polish), specify the handoff boundary clearly. Don't let the designer touch functional code.
6. **Maintain co-evolution.** If the ops agent inherits your domain expertise, don't let that make you passive. Keep your own understanding sharp, build on their work, and help them learn from your insights.

### The review cycle (detailed)

```
1. DISPATCH:  "dev, implement X. Standard: functional, runnable, basic UI polish."
2. RECEIVE:   "Done. Here's the code."
3. REVIEW:    Check against requirements:
              ├─ ✅ Functional? → Continue
              ├─ ❌ Bug/error? → "Fix: line 42 causes X. Revise."
              └─ ❌ Missing? → "Need Y feature added. Revise."
4. FEEDBACK:  Regardless of outcome, tell the agent what was good and what to improve.
5. REPORT:    "dev completed X. I found: [summary]. 腾哥, your call."
6. USER DECIDES:
              ├─ "Looks good" → Pass along positive feedback to agent
              └─ "Change Z"   → "dev, 腾哥 wants Z change. Do it."
```

### Progress tracking in knowledge base

To survive crashes and disconnects, the director maintains a running log:

```markdown
# Agent Work Log

## dev
- [2026-05-14] Task: slash-picker keyboard navigation
  - Status: ✅ Delivered, accepted
  - Feedback given: "Good, but Enter stopPropagation was a bug"
  - Lesson learned: Event bubbling interference in textarea→document keydown

## me
- [2026-05-14] Task: homepage UI polish
  - Status: ⏳ In review
  - Issues found: Color contrast insufficient → revision requested

## op
- [2026-05-14] Task: B2B script for this week
  - Status: 🔄 Dispatched
```

This log is saved to a persistent file (e.g., Obsidian, a markdown file, or the agent's memory) so a session crash doesn't lose context.

### Fallback: when an agent fails

Three failure modes with distinct recovery:

| Failure Mode | Symptom | Recovery |
|-------------|---------|----------|
| **Agent crashes** | No response / disconnected | Director steps in and does the work temporarily. Log the gap for later handoff. |
| **Agent delivers garbage** | Hallucinated API calls, wrong domain, broken code | Challenge + send back. If repeated, escalate to user for model/config fix. |
| **Agent dead (force majeure)** | Gateway unreachable, profile deleted | Director takes over permanently. Re-dispatch to a replacement once available. Record in progress log. |

### Concrete example: 腾哥's Team

The team that inspired this pattern maintains four profiles:

| Profile | Role | Persona file |
|---------|------|-------------|
| **小何（director）** | Director | `Obsidian Vault/小何/soul.md` |\n| **dev** | Code engineer | `Obsidian Vault/dev/soul.md` |\n| **me** | UI designer | `Obsidian Vault/me/soul.md` |\n| **op** | Operations | `Obsidian Vault/op/soul.md` |\n\nEach persona is stored in the user's Obsidian vault under its own directory and defines:\n- Identity and role\n- Skill boundaries\n- Collaboration rules (what they do / don't do)\n- How they receive feedback\n- Who they report to\n- Their knowledge base location

When a new task arrives, 小何 decides who gets it, dispatches with context, reviews the output, gives feedback, reports to 腾哥 for discussion, and logs progress. dev does full-stack code with basic polish; me takes dev's output and refines visuals; op handles the domain work (content, social media, etc.).

---

## Recovering stuck workers

When a worker profile keeps crashing, hallucinating, or getting blocked by its own mistakes (usually: wrong model, missing skill, broken credential), the kanban dashboard flags the task with a ⚠ badge and opens a **Recovery** section in the drawer. Three primary actions:

1. **Reclaim** (or `hermes kanban reclaim <task_id>`) — abort the running worker immediately and reset the task to `ready`. The existing claim TTL is ~15 min; this is the fast path out.
2. **Reassign** (or `hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch the task to a different profile and let the dispatcher pick it up with a fresh worker.
3. **Change profile model** — the dashboard prints a copy-paste hint for `hermes -p <profile> model` since profile config lives on disk; edit it in a terminal, then Reclaim to retry with the new model.

Hallucination warnings appear on tasks where a worker's `kanban_complete(created_cards=[...])` claim included card ids that don't exist or weren't created by the worker's profile (the gate blocks the completion), or where the free-form summary references `t_<hex>` ids that don't resolve (advisory prose scan, non-blocking). Both produce audit events that persist even after recovery actions — the trail stays for debugging.
