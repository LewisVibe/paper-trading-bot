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

## Codex Commit/Push Policy

Codex may commit and push by itself only for small low-risk changes, such as docs-only updates, typo or formatting fixes, workflow notes, README or documentation clarifications, non-execution report text changes, and small verifier-script or documentation changes that do not touch trading logic.

Before Codex auto-commits or pushes, it must:

- Run `python scripts\verify_repo_safety.py`.
- Run any focused verifier relevant to the task if code changed.
- Confirm no Python execution paths changed unless explicitly scoped.
- Confirm no secrets or generated artefacts were touched.
- Show a `git status` summary in its report.
- Use a clear commit message.

Codex must not auto-push:

- Alpaca or order submission changes.
- Normal `python bot.py` runtime behaviour changes.
- Slow SMA paper execution changes.
- Paper-order smoke test changes.
- Command-routing changes touching execution paths.
- Config default changes.
- Scheduling, cron, or loop changes.
- Risk or kill-switch enforcement changes.
- Generated CSV, log, database, or chart changes.
- Anything involving credentials or secrets.

For medium/high-risk changes, Codex may make a local branch or local commit only if explicitly asked, but must not push until the user reviews the diff and approves.

## Towards Live Paper Monitoring

The staged direction is operational paper monitoring without jumping straight to automated order execution:

A. Expand ticker universe in research/preview only.
B. Add or improve ticker-universe validation and reporting.
C. Add more frequent market monitoring as preview, display, or report only.
D. Add loop or cron support only after single-run commands are stable.
E. Add lockfile/no-overlap protection before any repeated run.
F. Add portfolio risk controls before expanded paper execution.
G. Keep paper execution separate, explicit, confirmation-gated, and manually reviewed.
H. Do not treat monitoring signals as execution approval.

More frequent price checks do not mean more frequent trades. Daily strategies should not overtrade intraday noise unless a separate intraday strategy is researched and validated. For now, frequent monitoring means observe, report, and preview; it does not mean submit orders. Any execution-capable loop or scheduled order workflow remains not approved.

## More Tickers Rule

More tickers should start with liquid U.S. stocks and ETFs only. Universe expansion must land in research/preview first, with liquidity, price, and duplicate validation before any execution review.

Before expanded paper execution is considered, more tickers require portfolio risk limits, max open positions, max notional exposure, and concentration checks.

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
- Git status summary, if committing or pushing
- Whether Python code changed
- Whether any execution paths changed
- Whether secrets or generated artefacts were touched
- Whether Codex committed/pushed or only edited locally
- Whether the known sandbox yfinance/Discord network limitation appeared

Keep successful routine verifier blocks concise. "Passed" is enough unless there is a failure, traceback, new warning, or unexpected output.

Before commits or pushes, run `python scripts\verify_repo_safety.py` to check that private config, environment files, generated data, logs, charts, databases, and secret-like filenames are not tracked or staged.

## CMD Verification Convention

When the user asks for Windows/CMD-style verification, keep command blocks easy to paste and avoid noisy output in the final report. For routine verifier blocks, summarize only the pass/fail status unless something unusual appears.

Known sandbox limitation: local Codex runs may fail network-backed checks that need yfinance or Discord. Treat that as an environment limitation when the no-network verifiers pass and the failure is clearly a blocked network call.
