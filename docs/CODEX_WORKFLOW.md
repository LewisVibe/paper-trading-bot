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

## No-Overlap / Lockfile Readiness Boundary

Before any repeated market-monitor refresh is considered, add no-overlap
protection as a separate reviewed effort. Overlapping report runs could collide
while fetching data, writing CSVs, updating caches, or producing quality reports,
so the future lockfile is for report integrity only.

The monitor lockfile helper is pure/no-network and now prevents overlapping safe
refresh/report commands only. It is applied exactly to
`python bot.py --monitor-lockfile-readiness-report`,
`python bot.py --refresh-promoted-review`, and
`python bot.py --refresh-defensive-research`.

Stale lock handling is conservative: stale lockfiles require manual review, not
automatic deletion. Lock metadata may include command name, `started_at`, host,
pid, `lock_version`, and optional `stale_after_seconds` if safe, but must not
include secrets, account IDs, config contents, order IDs, webhook URLs, API
keys, logs, database contents, generated CSV contents, generated trading data,
trading history, positions, or report contents.

This applies only to report, preview, display, and monitor refresh commands.
Execution-capable commands must never be scheduled and must not be protected
merely by a lockfile. A lockfile does not approve scheduling, execution, or paper
orders.

Use `python scripts\verify_monitor_lockfile_final_state.py` to verify the final
three-command lock boundary, stale-lock manual-review policy, false
execution/scheduling approval flags, and VPS handoff documentation.

For VPS monitoring, prefer terminal-only report/display commands. The
`python bot.py --vps-monitoring-status` command is safe to route before top-level
Alpaca imports so it can report environment status without requiring trading
dependencies at startup. The `python bot.py --market-monitor-scheduling-readiness-report`
checkpoint uses the same narrow report-only route and assesses only the three
VPS-safe lock-wrapped monitoring commands for future manual scheduling review.
Keep these exceptions narrow: do not weaken normal bot, paper-order-test,
slow-SMA paper execution, or any execution-capable dependency checks.

Hermes cron preferred for future monitoring scheduling if configured, but no
refresh cron job or execution scheduling is currently approved or created beyond
the existing status-only job. Use Hermes cron for safe
monitoring/reporting only; not for execution. Do not paste config/API
keys/webhooks/account IDs into Hermes prompts. Initial cron candidate should
probably be a status/checkpoint job before refresh jobs. Refresh jobs should
remain protected by lockfile/no-overlap, and a stale lock requires manual
review. Scheduling cadence is a separate future decision; a future review must
approve exact cadence, exact command list, enabled toolsets, output destination,
and failure behaviour before any Hermes cron job is created.

Use `docs/HERMES_CRON_JOB_DESIGN.md` and
`python scripts\verify_hermes_cron_job_design.py` for the current status-job
checkpoint. That checkpoint records the verified status-only Hermes cron and
confirms refresh commands still require a later separate review.

The current `paper-bot-vps-status-check` Hermes cron is status-only. Job ID is
`345188fbb60c`; cadence is once daily / every 1440m; delivery is Telegram; mode
is script-only / no-agent; working directory is `C:\dev\paper-trading-bot`; the
command sequence is repo safety, Hermes cron readiness, and
`--vps-daily-monitoring-summary`. Verified output is
`healthy_monitoring_state`, execution_approved false, scheduling_approved false,
and freshness_warnings: none. It does not run refresh commands, trade, approve
execution, approve scheduling beyond this one status job, pull/commit/push code,
or inspect/print config contents, secrets, logs, databases, or full generated
CSV contents. A possible promoted-review refresh cron remains a future
manual-review item documented in
`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md`; do not create or trigger it
during routine documentation or verifier work.
The older `docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` file is a legacy pointer
only. Use `docs/HERMES_CRON_MONITORING_RUNBOOK.md` and
`python scripts\verify_hermes_cron_monitoring_runbook.py` when interpreting
Telegram/status output from the existing status cron.

## Strategy Improvement Lab Boundary

`python bot.py --strategy-improvement-lab` is a research-only ETF allocation
lab for testing a fixed small set of more growth-aware variants. It may refresh
daily yfinance ETF history and write generated CSVs under `data/`, but it must
not load config, call Alpaca, read positions, submit/cancel/create orders, write
SQLite `trade_log`, send Discord alerts, schedule jobs, add shorting/leverage,
or approve execution.

`python bot.py --show-strategy-improvement-lab` is saved-CSV display only. Use
`python scripts\verify_strategy_improvement_lab.py` when changing the lab or
its command routing. Promising labels from the lab mean "research this further";
they are not buy/sell signals, order instructions, paper execution approval, or
scheduling approval.

`python bot.py --strategy-improvement-robustness` is the matching fixed
robustness layer for the same candidate set. It may refresh daily yfinance ETF
history and write generated robustness/cost/drawdown/comparison CSVs under
`data/`, but it must remain research-only and use fixed chronological splits and
fixed cost assumptions. Use
`python scripts\verify_strategy_improvement_robustness.py` when changing that
report. No cron, scheduling, or execution change is part of strategy
improvement research.

`python bot.py --strategy-improvement-diagnostics` is saved-CSV diagnostics for
the current best active strategy-improvement lead. It explains split
sensitivity, benchmark lag, cost stress, drawdown behaviour, cash drag, and
next fixed-hypothesis ideas without adding another strategy. Use
`python scripts\verify_strategy_improvement_diagnostics.py` when changing this
layer. Diagnostics are guidance for a later fixed research task, not tuning,
promotion, scheduling, or execution approval.

The first narrow refinement is `growth_biased_rotation_cost_aware_rebalance`.
It must preserve `growth_biased_rotation_crash_gate` unchanged and use the fixed
rebalance threshold documented in code. Judge it directly against the original
growth-biased strategy for turnover, cost sensitivity, split sensitivity, and
return drag before considering any further variant.

The next narrow refinement is `growth_biased_rotation_partial_defensive_sleeve`.
It must preserve `growth_biased_rotation_crash_gate` unchanged, use fixed
defensive-sleeve allocations only when breadth/regime weakens, and be judged
against the original growth-biased strategy, the cost-aware refinement, monthly
ETF rotation, and SPY. It is research-only and must not change scheduling,
execution, or strategy-to-order wiring.

## MCP Feasibility Boundary

MCP may be considered later as a tiny local/custom safe operations adapter for
VPS/Hermes report, display, and monitor commands only. It is not approved for
implementation yet, and it must not become a trading execution interface.

Any future MCP proof of concept must use a hardcoded allowlist, deny by default,
use fixed working directory `C:\dev\paper-trading-bot`, avoid arbitrary shell
access, avoid secrets and generated data by default, and return
`execution_approved=False` and `scheduling_approved=False` where applicable.
The first possible tools should be limited to `repo_safety_check` and
`refresh_market_monitor` only after VPS readiness reports are stable and
no-overlap or lockfile protection exists.

A future market/financial news layer may be researched only as a risk veto. It
may label tickers with `block_new_entries_today`, `manual_review_required`, or
`no_news_block`, and may block or flag new long entries for major negative or
event-risk news. It must not generate buy signals, sell signals, order
instructions, position sizing, or execution approval. News output must include
source, observed time, confidence, and reason, and stale vetoes must expire
automatically.

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
