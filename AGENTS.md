# Project Instructions

This repo is an ETH/USDT technical analysis signal bot. It fetches Binance market data, scores multi-timeframe technical signals, sends Telegram alerts, and exposes a lightweight HTTP health endpoint for deployment platforms.

## Working Rules

- Keep changes scoped and production-safe. This bot runs continuously and posts to Telegram, so avoid noisy alert behavior, unbounded loops, and broad refactors without a clear reason.
- Do not commit secrets. Runtime credentials belong in `.env` locally and platform variables in deployment.
- Prefer small, testable helpers for signal scoring, exchange clients, notification formatting, and health checks.
- Use ASCII in source files unless an existing user-facing Telegram message intentionally uses Vietnamese accents or symbols.
- When adding dependencies, update `requirements.txt` and keep Railway/runtime compatibility in mind.

## Project Commands

- Install dependencies: `pip install -r requirements.txt`
- Run locally: `python3 main.py`
- Health check while running: `curl -sS http://127.0.0.1:${PORT:-8080}/health`
- There is no formal test suite yet. For changes to signal logic or message formatting, add focused tests before widening behavior.

## Harness: ETH Signal Bot

**Goal:** Coordinate backend, signal logic, notification, deployment, and future frontend/dashboard work for the trading signal bot.

**Trigger:** For bot feature work, signal strategy changes, Telegram message changes, deployment fixes, health/admin UI, frontend/dashboard work, or multi-agent review, use `eth-signal-bot-orchestrator` in `.agents/skills/`. Answer directly for simple questions.

**Runtime:** Codex-native. Use `_workspace/` artifacts and explicit subagent orchestration. Do not use Claude-only TeamCreate/SendMessage/TaskCreate unless explicitly requested.

**Change History:**
| Date | Change | Target | Reason |
| --- | --- | --- | --- |
| 2026-06-23 | Initial Codex harness | all | Build bot development harness with frontend-dev coverage |

## iOS Simulator MCP Workflow

For iOS SwiftUI UI work:

- Use the `ios-simulator` MCP server when available.
- Use it to open Simulator, inspect screen, describe accessibility elements, tap, type, swipe, and capture screenshots.
- Prefer `make ui-review` for build + screenshot.
- Then use MCP `ui_view` and `ui_describe_all` to review the current UI.
- Do not claim UI work is complete until the screen was visually reviewed.

Required flow:

1. Implement scoped UI changes.
2. Run `make ui-review`.
3. Use iOS Simulator MCP to inspect the current screen.
4. Review visual hierarchy, spacing, typography, CTA, empty state, dark mode, and accessibility.
5. Apply one polish pass if needed.
