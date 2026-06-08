# Codex Workflow Guide

This project is a Python paper trading bot. Future Codex prompts should keep safety boundaries explicit, especially when a task touches trading, Alpaca, positions, or command routing.

## Default Project Safety Assumptions

- The project is paper-only.
- Live trading must never be added.
- `dry_run` defaults to `true`.
- `alpaca.paper` must remain `true`.
- `config.json`, API keys, Discord webhook URLs, account IDs, and other secrets stay private.
- Research, preview, display, and report commands must not execute trades.
- Paper execution commands must remain separate, explicit, and protected by confirmation flags.

## Task Risk Levels

- Docs-only: documentation updates, roadmap notes, workflow notes. No runtime verification needed unless code changes unexpectedly.
- Research-only: backtests, reports, CSV analysis, deterministic research helpers. No Alpaca orders, Discord alerts, or SQLite `trade_log` writes.
- Preview/display-only: reads saved CSVs or current market/position context for inspection. Must not approve execution or create executable order objects.
- Command-routing/refactor: moves or routes code without behavior changes. Needs focused verifiers and baseline checks.
- Execution-related/high risk: any paper-order submission, Alpaca order checks, position mutation, order sizing, close/open logic, or SQLite `trade_log` write path. Requires explicit scope, safety preflight, focused tests, and user confirmation before any order-capable run.

## Socratic Preflight Questions

For non-trivial tasks, start by answering:

- What is the smallest safe change?
- Which files are expected to change?
- Which files must not change?
- Is this docs, research, preview/display, refactor, or execution-related?
- What accidental side effects could happen?
- What verifier or no-network check is needed?
- When should Codex stop instead of continuing?

Stop and ask before proceeding if a task might submit/cancel orders, alter live/paper positions, expose secrets, change normal `python bot.py` behavior, or weaken paper-only safety.

## Standard Report-Back Format

Report back with:

- Files changed
- Command added or changed, if any
- Verification run and result
- Whether any execution paths changed
- Whether the known sandbox yfinance/Discord network limitation appeared

Keep successful routine verifier blocks concise. "Passed" is enough unless there is a failure, traceback, new warning, or unexpected output.

Before commits or pushes, run `python scripts\verify_repo_safety.py` to check that private config, environment files, generated data, logs, charts, databases, and secret-like filenames are not tracked or staged.

## CMD Verification Convention

When the user asks for Windows/CMD-style verification, keep command blocks easy to paste and avoid noisy output in the final report. For routine verifier blocks, summarize only the pass/fail status unless something unusual appears.

Known sandbox limitation: local Codex runs may fail network-backed checks that need yfinance or Discord. Treat that as an environment limitation when the no-network verifiers pass and the failure is clearly a blocked network call.
