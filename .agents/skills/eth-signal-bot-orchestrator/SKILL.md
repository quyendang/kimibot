---
name: eth-signal-bot-orchestrator
description: "ETH Signal Bot Codex harness. Use for bot feature work, signal strategy changes, Binance/Telegram integration, Railway deployment, health/admin UI, frontend dashboard work, multi-agent review, or rerunning prior bot work artifacts."
---

# ETH Signal Bot Orchestrator

Coordinate work on the ETH/USDT Telegram signal bot with explicit Codex subagents and `_workspace/` artifacts.

## Scope

Use this skill for substantial work involving:

- Binance market data fetching and retry behavior.
- Technical indicators, scoring thresholds, and alert strategy.
- Telegram message payloads, HTML escaping, and notification cadence.
- Runtime configuration, Railway deployment, health checks, and observability.
- Frontend/admin/dashboard work, including local web views for bot status or signal review.
- Independent review of risky changes before finalizing.

For one-line questions or tiny edits, answer directly and do not spawn agents.

## Phase 0: Context Check

1. Read `AGENTS.md`, `README.md`, `requirements.txt`, `Procfile`, and relevant files under `eth_signal_bot/`.
2. Inspect `.agents/skills/`, `.codex/agents/`, and `_workspace/` for prior artifacts.
3. If the user asks for a rerun or partial update, reuse existing `_workspace/` artifacts and rerun only affected roles.
4. If starting a new substantial task, create `_workspace/` if missing and write `_workspace/00_input.md` with the normalized request, date, scope, assumptions, and target files.

## Phase 1: Classify The Work

Choose the smallest useful path:

- Backend path: exchange client, scheduler, config, health server, runtime/deployment.
- Signal path: indicators, scoring, thresholds, market assumptions, alert semantics.
- Notification path: Telegram formatting, escaping, retries, alert cadence.
- Frontend path: dashboard, admin UI, health/status page, message preview UI, or visual design.
- Review path: bug hunt, risk review, regression audit, missing tests.

## Phase 2: Spawn Subagents When Useful

For multi-file work, risky behavior, or requested multi-agent execution, spawn only the roles that match the scope. Use custom agent configs in `.codex/agents/` as role guidance when available.

Suggested fan-out:

1. `bot-backend-dev`: inspect runtime, config, API clients, scheduler, and deployment. Write `_workspace/01_backend.md`.
2. `signal-strategy-reviewer`: inspect indicator math, scoring behavior, thresholds, and market assumptions. Write `_workspace/01_signal.md`.
3. `frontend-dev`: inspect or implement dashboard/admin/message-preview UI. Write `_workspace/01_frontend.md`.
4. `qa-reviewer`: inspect tests, edge cases, commands, and verification gaps. Write `_workspace/01_qa.md`.

Each subagent must include:

- Scope reviewed or files changed.
- Concrete findings or implementation summary.
- Commands run and results.
- Open risks, skipped areas, and exact follow-up recommendations.

## Phase 3: Implement

1. Parent Codex thread owns final edits unless a worker was explicitly assigned a disjoint write set.
2. Preserve existing bot behavior unless the request asks to change it.
3. Avoid calling real Telegram or exchange endpoints in tests unless the user explicitly wants live integration verification.
4. For frontend work, follow `bot-frontend-dev` and verify with browser screenshots or simulator tooling when applicable.

## Phase 4: Integrate

1. Read all `_workspace/01_*.md` artifacts produced for the task.
2. Resolve conflicts explicitly and preserve source attribution in `_workspace/02_integrated.md` for substantial runs.
3. Apply final patches in the parent thread.
4. Update `_workspace/tasks.md` if a task list exists.

## Phase 5: Validate

Run checks appropriate to the change:

- Syntax/import check: `python3 -m compileall main.py eth_signal_bot`
- Unit tests if present or added.
- For runtime health changes, start the app with safe test env values and check `/health`.
- For Telegram formatting changes, test message builders without sending live messages.
- For frontend/dashboard changes, run the local dev server and inspect the UI visually.

Record skipped checks and why in the final response.

## Failure Handling

- One subagent fails: retry once if the failure is transient; otherwise continue and mark the missing area.
- Multiple subagents fail: stop and ask whether to continue with partial evidence.
- Conflicting findings: keep both in `_workspace/02_integrated.md`, cite the artifact sources, and make the parent decision explicit.
- Live network or credential blocker: switch to mocks/fakes unless the user approves live verification.

## Trigger Tests

Should trigger:

- "Add a dashboard to monitor the bot."
- "Review the signal scoring logic."
- "Make Telegram alerts cleaner."
- "Fix Railway deployment and health check."
- "Use agents to review this bot end to end."

Should not trigger:

- "What does RSI mean?"
- "Show me the README."
- "What command runs the bot?"
- "Rename this one variable."
- "Is `.env` committed?"

## Dry Run Scenario

Request: "Add a local dashboard showing current bot status and last signal." Prepare `_workspace/00_input.md`, spawn `bot-backend-dev` for data/status shape, spawn `frontend-dev` for UI, optionally spawn `qa-reviewer`, integrate results, implement, run syntax checks and browser review.

## Partial Failure Scenario

If `frontend-dev` cannot run a browser due to missing dependencies, it still writes `_workspace/01_frontend.md` with static review and exact blocked command. Parent continues backend-safe work and reports visual verification as incomplete.
