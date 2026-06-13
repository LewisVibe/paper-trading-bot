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

## 6A. Future Hermes Cron Plan For Safe Monitoring Only

Hermes cron preferred for future monitoring scheduling if configured. Once
Hermes is running on the VPS, Hermes Agent cron is the preferred future
scheduling layer for monitoring-only, chat-delivered reports because it keeps
outputs visible in the Hermes conversation. Windows Task Scheduler remains an
alternative, but not the default assumption; if used, it should be limited to
starting or keeping the Hermes gateway running on boot, not to running
execution-capable trading commands.

No refresh cron job or execution scheduling is currently approved or created
beyond the existing status-only job. Use Hermes cron for safe
monitoring/reporting only; not for execution. Do not paste config/API
keys/webhooks/account IDs into Hermes prompts, and do not print `config.json`
contents, API keys, webhook URLs, tokens, account IDs, generated data, logs, or
database contents.

Initial cron candidate should probably be a status/checkpoint job before refresh
jobs. The initial candidate command set for a future Hermes cron review should
be limited to:

- `.venv\Scripts\python.exe bot.py --vps-monitoring-status`
- `.venv\Scripts\python.exe bot.py --market-monitor-scheduling-readiness-report`
- `.venv\Scripts\python.exe bot.py --monitor-lockfile-readiness-report`
- `.venv\Scripts\python.exe bot.py --refresh-promoted-review`
- `.venv\Scripts\python.exe bot.py --refresh-defensive-research`

All future cron commands should run from `C:\dev\paper-trading-bot` and use the
VPS `.venv\Scripts\python.exe`. Hermes cron jobs should use a restricted
toolset if Hermes supports `enabled_toolsets`; avoid unnecessary broad
capabilities, arbitrary shell access, network tools beyond the command's real
need, or access to secrets/config/logs/databases/generated outputs.

Future Hermes cron job prompts should include a repo-safety check, concise
output capture, and a clear instruction that the job must not create other cron
jobs recursively. Scheduling cadence is a separate future decision. A future
manual review must approve the exact cadence, exact command list, enabled
toolsets, output destination, and failure behaviour before any Hermes cron job
is created.

The current status-job checkpoint is `docs/HERMES_CRON_JOB_DESIGN.md`. It records
the verified `paper-bot-vps-status-check` job, including job ID, daily 10:10am
UK local time cadence, cron expression `10 10 * * *`, Telegram delivery,
script-only / no-agent mode, repo path, command
sequence, and healthy output. It confirms the job does not run
`--refresh-promoted-review` or `--refresh-defensive-research`; refresh cron jobs
require a later separate review. Verify the checkpoint with
`python scripts\verify_hermes_cron_job_design.py`.

The current daily Hermes status cron exists as `paper-bot-vps-status-check`
with job ID `345188fbb60c`. It runs daily at 10:10am UK local time using cron
expression `10 10 * * *`, delivers to
Telegram, uses script-only / no-agent mode, runs from
`C:\dev\paper-trading-bot`, and executes:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

Verified output is repo_safety PASS, hermes_cron_readiness PASS,
vps_daily_monitoring_summary PASS, final_monitoring_status
`healthy_monitoring_state`, action_required
`no_action_required`, execution_approved false, scheduling_approved false, and
freshness_warnings: none. This status-only job does not run refresh commands,
trade, approve scheduling beyond this one status job, approve execution,
pull/commit/push code, or inspect/print config contents, secrets, logs,
databases, or full generated CSV contents. Freshness labels (`fresh`,
`warning_stale`, `stale`, `missing`) are monitoring diagnostics only. Missing or
stale saved outputs are prerequisite/status issues, not trading approval.

No promoted-review refresh cron job is currently created. A possible future
second job is documented in
`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` and must pass
`python scripts\verify_hermes_promoted_review_refresh_cron_design.py` before
any separate manual scheduling review. If promoted review reports strategy
disagreement, no-action states, or blocked review states, those are monitoring
results, not execution approval.

`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` is the canonical
future-only design for the possible second cron job.
`docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` is kept only as a legacy pointer.

Use `docs/HERMES_CRON_MONITORING_RUNBOOK.md` to interpret Telegram output from
`paper-bot-vps-status-check`. It covers `healthy_monitoring_state`,
`monitoring_warning`, `monitoring_stale_or_missing_inputs`, and failed-step
responses, and it preserves `execution_approved=false` and
`scheduling_approved=false`. Verify it with
`python scripts\verify_hermes_cron_monitoring_runbook.py`.

Refresh jobs should remain protected by lockfile/no-overlap. The current
lock-wrapped overlap-risk commands are `--monitor-lockfile-readiness-report`,
`--refresh-promoted-review`, and `--refresh-defensive-research`. A stale lock
requires manual review. Lockfile protection does not make execution-capable
commands schedulable, and it does not approve scheduling, orders, paper
execution, or any execution-capable workflow.

Execution-capable commands remain high-risk/manual-only and excluded from all
scheduling review: normal bot run, paper-order smoke test, slow-SMA paper
execution, and any future order-capable command.

Prerequisites before any future scheduling review:

```powershell
python scripts\verify_repo_safety.py
python scripts\verify_hermes_cron_readiness.py
python bot.py --market-monitor-scheduling-readiness-report
python bot.py --vps-monitoring-status
```

Generated CSV/cache/chart/log/database files must remain ignored by git. Stop if
any candidate schedule tries to read or print config contents, call Alpaca, read
positions, write SQLite `trade_log`, send Discord alerts, create orders, create
more cron jobs, or approve execution.

Before any repeated market-monitor refresh is considered, no-overlap protection
must exist. Repeated runs can collide if a prior yfinance fetch, CSV write, cache
operation, or quality report is still running when the next refresh starts. That
could produce confusing reports or partially written files, even though the
workflow is monitoring/report/display only.

Future lockfile helper contract, planning only:

- A lock file should prevent two safe refresh/report/display commands from
  running at once.
- The helper must be pure and no-network.
- Stale lock handling must be conservative. When in doubt, stop and ask for
  manual review instead of deleting a lock automatically.
- Lock metadata may include command name, `started_at`, host, pid,
  `lock_version`, and optional `stale_after_seconds` if safe.
- The lock must not contain secrets, account IDs, config contents, order IDs,
  webhook URLs, API keys, logs, database contents, generated CSV contents,
  generated trading data, trading history, positions, or report contents.
- Lockfile protection applies only to future report, preview, display, and
  monitor refresh commands.
- Execution-capable commands must never be scheduled and must not be treated as
  safe merely because a lockfile exists.
- A lockfile does not approve scheduling, execution, paper orders, or any
  execution-capable workflow.

Future implementation order:

1. Add a report-only no-overlap/lockfile design or verifier.
2. Add isolated lock helper tests.
3. Apply the helper only to safe refresh/report/display commands.
4. Only after manual review, consider scheduling safe monitor/report refresh
   commands.

The current report-only design scaffold is
`python bot.py --monitor-lockfile-readiness-report`. It writes
`data/monitor_lockfile_readiness_report.csv` when run, but it does not create a
lockfile, wrap any command, approve scheduling, or approve execution.

The pure no-network contract verifier is
`python scripts\verify_monitor_lockfile_contract.py`. It defines the future
helper contract only; it does not implement locking or run bot commands.

The usual paper-only boundaries still apply: no live trading, `dry_run` defaults
to true, `alpaca.paper` remains true, `allow_shorting` remains false, and
config/secrets/logs/databases/generated outputs should not be read or committed
unnecessarily.

Never schedule:

```powershell
python bot.py
python bot.py --paper-order-test ...
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

## 6B. MCP Feasibility For Safe VPS Operations

MCP could have a supporting role later as a tiny local/custom operations adapter
for VPS/Hermes usage, but only after the current monitor/report workflow is
stable. Its purpose would be to expose a small set of whitelisted maintenance,
report, display, and monitoring actions so Hermes or Desktop do not need broad
raw shell access for routine safe operations.

MCP is not a trading interface for this project. It must remain separate from
Alpaca, order submission, paper execution, position reads, `trade_log` writes,
Discord trade alerts, scheduling approval, and execution approval.

News risk-veto concept:

- A future MCP or cron-supported news workflow may fetch market and financial
  news only to produce ticker-level risk veto/report output.
- Example report labels include `block_new_entries_today`,
  `manual_review_required`, and `no_news_block`.
- A veto may block or flag new long entries for a ticker with major negative or
  event-risk news.
- A veto must never approve buys or sells, create order instructions, size
  positions, generate trading signals, or approve execution.

Candidate future MCP tools:

- `repo_safety_check`
- `refresh_market_monitor`
- `market_monitor_scheduling_readiness`
- `vps_operations_readiness`
- `deployment_readiness_report`
- `fetch_news_risk_report`
- `write_news_risk_veto_report`
- `show_news_risk_veto`
- `show_safe_command_list`

Explicitly forbidden MCP tools:

- `submit_order`
- `cancel_order`
- `run_normal_bot`
- `run_paper_order_test`
- `run_slow_sma_paper_execution`
- `generate_buy_signal_from_news`
- `generate_sell_signal_from_news`
- `approve_trade_from_news`
- `read_config`
- `read_env`
- `read_logs`
- `read_database`
- `expose_tokens`
- `schedule_execution`
- `approve_execution`

Security rules for any future MCP proof of concept:

- Use a tiny local/custom MCP server only if implemented later.
- Do not use third-party MCP servers by default.
- Use a hardcoded allowlist of exact commands and deny by default.
- Use the fixed working directory `C:\dev\paper-trading-bot`.
- Do not expose an arbitrary shell command tool.
- Do not allow secrets, config files, logs, databases, generated CSV contents,
  auth files, or tokens by default.
- News output must include source, observed time, confidence, and reason.
- Stale news vetoes must expire automatically.
- Return `execution_approved=False` and `scheduling_approved=False` from tools
  where those flags apply.

Recommended implementation order:

1. Finish and stabilize the VPS readiness/report chain.
2. Add no-overlap or lockfile protection for monitor refresh before any
   repeated-run design.
3. Add docs/report-only news-veto design.
4. Add a saved-data-only news-veto report command.
5. Only then consider a minimal MCP proof of concept.
6. Start that proof of concept with only `repo_safety_check` and
   `refresh_market_monitor`.

Current conclusion: MCP is potentially useful later as a safer wrapper around
known-good report/display/monitor commands. The news use case is worth exploring
as a risk veto, but it is not a trading signal engine. It is not worth
implementing before the VPS monitor/report workflow is stable, and it must
remain separate from trading execution.

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
