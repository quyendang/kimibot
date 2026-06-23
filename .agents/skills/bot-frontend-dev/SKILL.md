---
name: bot-frontend-dev
description: "Frontend workflow for this ETH Signal Bot. Use for dashboard, admin UI, health/status pages, Telegram message preview screens, responsive UI polish, visual QA, and frontend implementation or review."
---

# Bot Frontend Dev

Use this skill when the bot gains a web, mobile, or message-preview UI.

## Workflow

1. Read `AGENTS.md`, `README.md`, and any existing frontend files.
2. Identify the UI surface:
   - Health/status page.
   - Admin dashboard.
   - Signal history or message preview.
   - Configuration editor.
3. Keep the first screen usable, not a marketing landing page.
4. Use restrained operational UI: dense but readable status, recent signals, runtime health, configuration state, and clear alert state.
5. Include explicit empty, loading, stale-data, error, and credential-missing states.
6. Verify responsive layout with browser screenshots for desktop and mobile. If this is iOS SwiftUI work, follow the iOS Simulator MCP workflow in `AGENTS.md`.

## UI Standards

- Prefer tables, lists, segmented controls, toggles, inputs, and compact charts over decorative cards.
- Keep cards to individual repeated items or framed tools. Do not nest cards.
- Use icons for common actions when an icon library exists.
- Ensure text fits in controls on mobile and desktop.
- Avoid one-note palettes and heavy decorative gradients.
- Do not expose secrets in the UI.

## Output Contract

For delegated frontend work, write `_workspace/01_frontend.md` with:

- UI scope and target files.
- Implementation summary or review findings.
- Screenshots or visual verification status.
- Accessibility and responsive-layout notes.
- Remaining blockers or follow-up tasks.
