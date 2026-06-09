# Hermes Workflow Guide

This document explains how Hermes should be used with this paper-trading-bot repository. It is a safety and workflow note only. It does not approve execution, deployment, scheduling, strategy changes, or any order-capable workflow.

## 1. Project Purpose

This repo is a Python market monitoring and paper-trading bot for learning, research, reporting, previewing, and carefully gated Alpaca paper-trading experiments.

The project can:

- Monitor configured U.S. stocks and ETFs.
- Download market data for research and signals.
- Run research-only backtests and strategy comparisons.
- Build saved reports, previews, displays, and dashboards from research outputs.
- Log normal bot activity to SQLite when normal bot paths run.
- Send optional Discord alerts in normal alert paths.
- Alpaca paper orders can only be submitted through explicitly reviewed, manually confirmed, high-risk paper-execution paths; this document does not approve running them.

Hermes should treat the repo as paper-only, dry-run-first, and safety-critical even when a task is described as simple.

## 2. Paper-Only Safety Boundary

The project is paper-only.

Hermes must preserve these boundaries:

- Never add, suggest, or enable live trading.
- `dry_run` defaults to `true` and must not be weakened.
- `alpaca.paper` must remain `true`; the bot refuses non-paper Alpaca mode.
- `allow_shorting` defaults to `false` and must not be weakened.
- Never weaken paper-only checks.
- Never connect research strategies directly to execution.
- Never treat research, preview, report, display, dashboard, generated CSV, or generated chart outputs as execution approval.
- Never schedule execution-capable commands.
- Treat Alpaca order submission, paper-order smoke tests, slow SMA paper execution, and normal bot order/logging paths as high risk.
- Deployment readiness and VPS checklist docs are audits/planning aids only; they do not deploy, schedule, or approve execution.
- Portfolio risk policy reporting is not runtime enforcement and does not approve execution.
- Short execution, short preview, crypto shorting, margin, leverage, and Alpaca crypto orders are not approved.

Any execution-related work requires explicit user confirmation, narrow scope, and a reviewed safety plan before action.

## 3. Secrets And Files Hermes Must Never Read, Print, Commit, Or Expose

Hermes must not read, print, summarize, inspect, commit, upload, or expose:

- `config.json`
- `.env` files
- API keys
- Alpaca credentials
- Discord webhook URLs
- Discord bot tokens
- Telegram bot tokens
- OpenAI, Codex, Hermes, or other auth files
- Account IDs, which are secret/sensitive
- Logs that may contain secrets
- SQLite database files, including trade databases
- Generated CSV outputs by default, unless the user explicitly scopes a report, preview, display, charting, or analysis task that requires specific generated outputs
- Generated chart outputs by default, unless the user explicitly scopes a report, preview, display, charting, or analysis task that requires specific generated outputs
- Virtual environment files
- Any file with secret-like names or auth/token/key material

Account IDs are secret/sensitive and must not be read, printed, committed, pasted, or exposed.

Hermes should avoid generated CSV and chart outputs by default. Hermes may inspect specific generated outputs only when the user explicitly scopes a report, preview, display, charting, or analysis task that requires those exact outputs. Generated research, preview, report, dashboard, CSV, or chart outputs must never be treated as execution approval.

For documentation and command-safety reviews, Hermes should follow the user's explicit file scope. If a task names specific docs, read only those docs unless the user separately expands the scope.

Before any commit or handoff, Hermes should ensure private configs, generated data, logs, charts, databases, and secret-like files are not tracked or staged.

## 4. Lower-Risk Command Categories

Lower risk does not mean automatic or approved for scheduling. These categories are generally lower risk when the user permits commands, but Hermes should still check task scope first.

### Research Commands

Research commands may download market data or create research outputs, but must not call Alpaca execution, submit orders, write execution `trade_log` rows, send trade alerts, or approve execution.

Examples include backtests, strategy labs, robustness checks, cost stress tests, drawdown analysis, and crypto research-only commands.

### Report Commands

Report commands summarize saved research state, static repository state, risk policy, readiness, or decision checkpoints. They may write report files, but must not approve execution.

Examples include research reports, walk-forward reports, deployment readiness reports, portfolio risk policy reports, kill-switch readiness reports, execution eligibility reports, and defensive research state reports.

### Preview Commands

Preview commands show desired states, signals, action previews, or risk previews without creating executable orders.

Preview output is informational only. It must not be treated as permission to submit orders.

Preview commands that explicitly read Alpaca paper positions in read-only mode are still non-execution, but Hermes should treat them as elevated preview risk and mention that they may require credentials.

### Display Commands

Display commands should read saved outputs and print summaries only. They should not refresh market data, call Alpaca, create files beyond expected display side effects, submit orders, write SQLite execution rows, send Discord alerts, or approve execution.

### Verifier Commands

Verifier commands check safety, syntax, repository hygiene, or no-network behavior. They are preferred before refactors and before commits.

Important verifier examples:

```powershell
python scripts\verify_repo_safety.py
python scripts\verify_v2_baseline.py --timeout-seconds 180
python scripts\verify_position_rules.py
python -m py_compile bot.py
```

For docs-only changes, runtime verification is usually unnecessary unless the user explicitly asks for it. If verification is requested, prefer repository safety checks and no-order verifiers.

## 5. High-Risk / Manual-Only Command Categories

Hermes must treat these categories as high risk and manual-only.

### Paper-Order Smoke Tests

Manual paper-order smoke tests can submit Alpaca paper orders. They must never run without explicit confirmation.

High-risk pattern:

```powershell
python bot.py --paper-order-test ... --confirm-paper-order
```

### Slow SMA Paper Execution

Slow SMA paper execution can submit Alpaca paper orders and must remain separate, confirmation-gated, paper-only, and manually reviewed.

High-risk pattern:

```powershell
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

### Normal Bot Order / Logging Path

The normal bot path is high risk because it can reach order, logging, position, SQLite, and Discord alert flows depending on config and flags.

High-risk patterns:

```powershell
python bot.py
python bot.py --config config.json
```

Even when dry-run is expected, Hermes should not run the normal bot path unless the user explicitly permits it for a scoped task.

### Any Order-Capable Operation

High-risk operations include anything that:

- Submits orders.
- Cancels orders.
- Creates executable order instructions.
- Mutates positions.
- Changes order sizing or position rules.
- Changes open-order blocking.
- Changes Alpaca client behavior near execution.
- Writes SQLite `trade_log` rows as part of an execution path.
- Sends trade alerts.
- Bypasses preview, risk checks, or confirmation gates.

## 6. Commands Never To Schedule Automatically

Hermes must never schedule these automatically:

```powershell
python bot.py --paper-order-test ... --confirm-paper-order
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
python bot.py
python bot.py --config config.json
```

Hermes must also never schedule:

- Any future execution command.
- Any command that submits, cancels, or creates orders.
- Any command that mutates positions.
- Any command that writes SQLite `trade_log` rows as part of an execution path.
- Any command that changes `dry_run`, `alpaca.paper`, or `allow_shorting` safety defaults.
- Any command that connects research strategies to execution.
- Any command that bypasses preview, risk checks, manual review, or explicit confirmation.

Safe-looking report, preview, display, or verifier commands should still only be scheduled after a separate user-approved scheduling review.

## 7. How Hermes Should Report Back After Tasks

Hermes should report concisely and explicitly.

For docs-only tasks, report:

- Files changed.
- Verification run and result, if any.
- Whether commands or execution paths changed.
- Whether Python code changed.
- Whether secrets or generated artefacts were touched.

For code or refactor tasks, also report:

- Command added or changed, if any.
- Verifiers run and pass/fail status.
- Whether command routing changed.
- Whether Alpaca, SQLite `trade_log`, Discord alerting, position, or order paths changed.
- Any known sandbox/network limitation, such as yfinance or Discord access failures.

Routine successful verifier output can be summarized as passed. Include details for failures, tracebacks, new warnings, or unexpected output.

## 8. How Hermes Should Interact With Codex / ChatGPT For Higher-Risk Tasks

For higher-risk tasks, Hermes should use Codex or ChatGPT as a reviewer/planner before implementation, not as an excuse to skip safety.

Before asking Codex or ChatGPT to work on higher-risk areas, Hermes should provide:

- Project path.
- Paper-only boundary.
- Files that must not be read or exposed.
- Exact task scope.
- Expected files to change.
- Files that must not change.
- Commands that must not be run.
- Required verification commands.
- Explicit statement that live trading is out of scope.
- Explicit statement that research strategies must not be connected to execution.

For execution-related tasks, Hermes should stop and ask the user before proceeding if the task might:

- Submit or cancel orders.
- Alter paper or live positions.
- Change normal `python bot.py` behavior.
- Touch Alpaca order submission.
- Touch SQLite execution logging.
- Touch Discord trade alerts.
- Weaken `dry_run`, `alpaca.paper`, or `allow_shorting` defaults.
- Expose secrets or account information.

Codex/ChatGPT output should be treated as a proposal until verified locally with safe, scoped checks.

## 9. Codex Commit/Push Policy

Hermes may ask Codex to commit and push small low-risk changes by itself only when the task remains low risk. Examples include docs-only updates, typo or formatting fixes, workflow notes, README or documentation clarifications, non-execution report text changes, and small verifier-script or documentation changes that do not touch trading logic.

Before Codex auto-commits or pushes, it must:

- Run `python scripts\verify_repo_safety.py`.
- Run any focused verifier relevant to the task if code changed.
- Confirm no Python execution paths changed unless explicitly scoped.
- Confirm no secrets or generated artefacts were touched.
- Show a `git status` summary in its report.
- Use a clear commit message.

Codex must not auto-push Alpaca/order submission changes, normal `python bot.py` runtime behaviour changes, slow SMA paper execution changes, paper-order smoke test changes, command-routing changes touching execution paths, config default changes, scheduling/cron/loop changes, risk or kill-switch enforcement changes, generated CSV/log/database/chart changes, or anything involving credentials or secrets.

For medium/high-risk changes, Codex may make a local branch or local commit only if explicitly asked, but must not push until the user reviews the diff and approves.

## 10. Staged Paper-Monitoring Roadmap

Hermes should steer operational paper-trading work through these stages:

A. Expand ticker universe in research/preview only.
B. Add or improve ticker-universe validation and reporting.
C. Add more frequent market monitoring as preview/display/report only.
D. Add loop/cron support only after single-run commands are stable.
E. Add lockfile/no-overlap protection before any repeated run.
F. Add portfolio risk controls before expanded paper execution.
G. Keep paper execution separate, explicit, confirmation-gated, and manually reviewed.
H. Do not treat monitoring signals as execution approval.

More frequent price checks do not mean more frequent trades. Daily strategies should not overtrade intraday noise unless a separate intraday strategy is researched and validated. For now, frequent monitoring should mean observe/report/preview, not submit orders. Any execution-capable loop or scheduled order workflow remains not approved.

More tickers should start with liquid U.S. stocks and ETFs only. Add universe expansion to research/preview first, and add liquidity, price, and duplicate validation before execution. More tickers require portfolio risk limits, max open positions, max notional exposure, and concentration checks before paper execution.

## 11. Recommended Staged Workflow

Use this staged workflow by default:

1. Read-only first
   - Read only safe documentation or explicitly allowed source files.
   - Do not read secrets, configs, generated outputs, logs, databases, or auth files.
   - Identify risk level before suggesting changes.

2. Docs-only second
   - Update documentation before code when clarifying safety, workflow, or handoff state.
   - Do not edit Python code for docs-only tasks.
   - Do not run runtime commands unless the user explicitly asks.

3. Safe verifier third
   - Run only scoped, safe verifier commands after the user permits commands.
   - Prefer `python scripts\verify_repo_safety.py` before commits or handoffs.
   - For refactors, run focused no-order verifiers before broad checks.

4. Small refactor only after review
   - Refactor in small slices.
   - Avoid high-risk order paths until tests and a paper-only integration checklist exist.
   - Preserve current command output and behavior where practical.
   - Keep research, preview, report, display, and execution paths separated.

5. No execution work unless explicitly confirmed
   - Do not run paper-order smoke tests unless the user explicitly confirms the exact command and scope.
   - Do not run slow SMA paper execution unless the user explicitly confirms the exact command and scope.
   - Do not run normal `python bot.py` unless the user explicitly confirms the exact command and scope.
   - Do not schedule any execution-capable command.

## 12. Stop Conditions

Hermes should stop and ask before continuing if it encounters:

- A need to read `config.json`, `.env`, logs, databases, generated CSVs, generated charts, or auth files.
- A task that may submit, cancel, or create orders.
- A task that may change execution behavior.
- A task that may weaken safety defaults.
- A task that may expose credentials, account IDs, webhook URLs, or tokens.
- A task that would schedule execution-capable commands.
- Ambiguity about whether a command is research-only or execution-capable.
