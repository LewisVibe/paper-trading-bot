# VPS Setup Checklist

This checklist is for a possible future Windows Server VPS setup. It is not a
deployment plan, and it does not approve scheduling, paper execution, live
trading, or any order-submission workflow.

The first VPS phase should run safe report, display, and preview commands only.

## Purpose

- Prepare a Windows Server VPS environment for future manual testing.
- Keep the project paper-only and dry-run-first.
- Verify local repository, Python, package, and safety readiness before running
  any report or preview commands.
- Keep execution-capable commands manually gated and out of automation except
  the explicitly approved autonomous paper route.

## Safety Boundary

- Never live trade.
- Keep `alpaca.paper=true`.
- Keep `dry_run=true` unless a separately reviewed paper-execution workflow is
  explicitly being tested.
- Keep `allow_shorting=false`.
- Do not schedule execution-capable commands except
  `--run-vol-targeted-growth-auto-paper` under its dedicated runbook.
- Do not commit `config.json`, `.env` files, logs, databases, CSV outputs, or
  chart files.
- Keep API keys, Discord webhooks, account IDs, and all secrets private.
- Do not paste secrets into ChatGPT, Codex, GitHub issues, commits, logs, or
  screenshots.
- Research, report, preview, and display commands do not approve execution.

## Initial VPS Prerequisites

- Windows Server VPS.
- Git installed and available from PowerShell or CMD.
- Python 3.11 or newer installed.
- Project cloned from GitHub:
  `https://github.com/LewisVibe/paper-trading-bot.git`
- Python virtual environment created.
- `requirements.txt` installed.

## Safe Clone And Setup Steps

Future setup example:

```powershell
git clone https://github.com/LewisVibe/paper-trading-bot.git
cd "paper-trading-bot"
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

These commands prepare the project only. They do not schedule anything and do
not approve execution.

## Local Config Setup

- Copy `config.example.json` to `config.json`.
- Add Alpaca paper credentials locally only.
- Add a Discord webhook locally only if needed.
- Keep `alpaca.paper=true`.
- Keep `dry_run=true`.
- Keep `allow_shorting=false`.
- Never commit `config.json`.
- Never paste secrets into ChatGPT, Codex, GitHub, terminal transcripts, or docs.

## First Safety Checks On VPS

Run these manually after setup:

```powershell
python scripts\verify_repo_safety.py
python bot.py --deployment-readiness-report
python bot.py --vps-operations-readiness-report
python scripts\verify_v2_baseline.py --timeout-seconds 180
```

Expected caveat:

- Network-backed yfinance or Discord checks may fail if the VPS firewall,
  network, DNS, or webhook configuration blocks them.
- If Alpaca API hosts time out while normal HTTPS sites work, run
  `python bot.py --alpaca-connectivity-diagnostics` for DNS/TCP 443 diagnostics
  only. This does not use credentials, call authenticated Alpaca APIs, read
  positions, create orders, or approve execution.
- No-network verifiers are still useful for code safety and repository hygiene.
- Treat any new failure, traceback, or warning as something to investigate
  before scheduling or relying on the VPS.

## Safe Commands For Future Scheduling Review

These are safe VPS manual monitoring commands for review only. They are
report/refresh/display only, and they are not execution approval or automatic
scheduling approval:

```powershell
.venv\Scripts\python.exe bot.py --vps-monitoring-status
.venv\Scripts\python.exe bot.py --monitor-lockfile-readiness-report
.venv\Scripts\python.exe bot.py --refresh-promoted-review
.venv\Scripts\python.exe bot.py --refresh-defensive-research
python bot.py --show-promoted-decision
python bot.py --show-crypto-monitor
python bot.py --deployment-readiness-report
python bot.py --vps-operations-readiness-report
python scripts\verify_repo_safety.py
```

Scheduling any command should be treated as a separate reviewed task. A command
being listed here does not mean it is approved for automatic scheduling today.

## Hermes Cron Plan For Safe Monitoring Only

Hermes cron preferred for future monitoring scheduling if configured. Once
Hermes is running on the VPS, Hermes cron is preferred for monitoring-only,
chat-delivered reports. Windows Task Scheduler remains an alternative, not the
default assumption, and may be used only to start or keep the Hermes gateway
running on boot, not for execution-capable trading commands.

No refresh cron job is currently approved, and the existing status job remains
read-only. Do not paste config/API keys/webhooks/account IDs into Hermes prompts.

The approved exception is the separate autonomous paper command documented in
`docs/HERMES_AUTO_PAPER_EXECUTION_CRON.md`. It may be scheduled only after the
private VPS config explicitly sets `auto_paper_trading_enabled=true`; it does
not approve normal bot execution, manual ticket commands, retries, or live trading.

Initial cron candidate should probably be a status/checkpoint job before refresh
jobs. The initial future candidate set is limited to
`--vps-monitoring-status`, `--market-monitor-scheduling-readiness-report`,
`--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and
`--refresh-defensive-research`. All jobs should run from
`C:\dev\paper-trading-bot`, use `.venv\Scripts\python.exe`, include a
repo-safety check, use concise output capture, avoid recursive cron creation,
and use restricted `enabled_toolsets` where Hermes supports them.

Refresh jobs should remain protected by lockfile/no-overlap. A stale lock
requires manual review. Lockfile protection does not make execution-capable
commands schedulable. Scheduling cadence is a separate future decision. A
future manual review must approve exact cadence, exact command list, enabled
toolsets, output destination, and failure behaviour before any Hermes cron job
is created.

The current status-job checkpoint is `docs/HERMES_CRON_JOB_DESIGN.md`. It records
the verified `paper-bot-vps-status-check` job and confirms it remains
status-only: repo safety, Hermes cron readiness, and VPS daily monitoring
summary. It excludes refresh commands until a later separate review. Verify it with
`python scripts\verify_hermes_cron_job_design.py`.

The current daily Hermes status cron exists as `paper-bot-vps-status-check`
with job ID `345188fbb60c`. It runs daily at 10:10am UK local time using cron
expression `10 10 * * *`, delivers to Telegram, uses script-only / no-agent
mode, runs from `C:\dev\paper-trading-bot`, and executes `.venv\Scripts\python.exe
scripts\verify_repo_safety.py`, `.venv\Scripts\python.exe
scripts\verify_hermes_cron_readiness.py`, `.venv\Scripts\python.exe bot.py
--vps-daily-monitoring-summary`. Verified output is repo_safety PASS,
hermes_cron_readiness PASS, vps_daily_monitoring_summary PASS,
final_monitoring_status `healthy_monitoring_state`,
action_required `no_action_required`, execution_approved false,
scheduling_approved false, and freshness_warnings: none. It does not run refresh
commands, trade, approve scheduling beyond this one status job, approve
execution, pull/commit/push code, or inspect/print config contents, secrets,
logs, databases, or full generated CSV contents.

The summary and `--vps-monitoring-status` freshness labels are monitoring
diagnostics only: `fresh`, `warning_stale`, `stale`, and `missing`. Missing or
stale saved outputs are prerequisites/status issues, not trading approval.

No promoted-review refresh cron job is currently created. A possible future
second job is documented in
`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md`; verify the design with
`python scripts\verify_hermes_promoted_review_refresh_cron_design.py` before any
separate manual scheduling review.
`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` is canonical;
`docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` is a legacy pointer only.

Use `docs/HERMES_CRON_MONITORING_RUNBOOK.md` to interpret Telegram output from
`paper-bot-vps-status-check`. It covers `healthy_monitoring_state`,
`monitoring_warning`, `monitoring_stale_or_missing_inputs`, and failed-step
responses without approving execution or creating a second cron. Verify it with
`python scripts\verify_hermes_cron_monitoring_runbook.py`.

Prerequisites before any scheduling review:

```powershell
python scripts\verify_repo_safety.py
python scripts\verify_hermes_cron_job_design.py
python scripts\verify_hermes_cron_readiness.py
python bot.py --market-monitor-scheduling-readiness-report
python bot.py --monitor-lockfile-readiness-report
python bot.py --vps-operations-readiness-report
```

The scheduling-readiness report assesses only the VPS-safe monitoring set:
`--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and
`--refresh-defensive-research`. It can report
`ready_for_future_manual_scheduling_review` only as a checkpoint for a separate
future review; it never approves scheduling or execution.

Only continue to a separate scheduling review after the manual VPS refresh run
succeeds and generated CSV/cache files remain ignored by git.

Stop if any candidate schedule tries to load `config.json`, call Alpaca, read
positions, write SQLite `trade_log`, send Discord alerts, create orders, or
approve execution.

## Current No-Overlap / Lockfile Checkpoint

The monitor lockfile prevents overlapping safe refresh/report commands only.
It is currently applied exactly to:

```powershell
python bot.py --monitor-lockfile-readiness-report
python bot.py --refresh-promoted-review
python bot.py --refresh-defensive-research
```

These locks are transient report-only guards. They do not approve scheduling or
execution, do not make report output executable, and do not make any command
safe for automatic scheduling by themselves. Stale lockfiles require manual
review, not automatic deletion.

Lock metadata may include command name, `started_at`, host, pid,
`lock_version`, and optional `stale_after_seconds` if safe. The lock must not
contain secrets, account IDs, config contents, order IDs, webhook URLs, API
keys, logs, database contents, generated CSV contents, generated trading data,
trading history, positions, or report contents.

VPS manual update flow:

```powershell
git pull
py -3 scripts\verify_repo_safety.py
py -3 scripts\verify_monitor_lockfile_final_state.py
```

Safe VPS manual monitoring commands:

```powershell
.venv\Scripts\python.exe bot.py --monitor-lockfile-readiness-report
.venv\Scripts\python.exe bot.py --refresh-promoted-review
.venv\Scripts\python.exe bot.py --refresh-defensive-research
```

Generated CSVs/charts/logs/databases/secrets/config must not be committed or
pasted. Generated CSV/chart outputs remain ignored and should not be committed.

## VPS Monitoring Prerequisites Checkpoint

Terminal monitoring is the chosen VPS route for now. Do not add a dashboard, web
server, public hosting, open ports, loop mode, scheduling, or execution controls
for this workflow.

After the first manual VPS safe-command test, separate environment readiness
from missing local prerequisites:

- `.venv\Scripts\python.exe` working means dependencies are available for
  manual verifier/report commands.
- `config.json` may be absent. That is
  `config_missing_for_readonly_promoted_review`, not a safety failure. Do not
  fix it by printing, reading, or creating secrets from Codex.
- `python bot.py --refresh-promoted-review` may refuse without local config
  because it includes the explicitly read-only paper-position preview context.
  That refusal does not approve execution.
- `python bot.py --refresh-defensive-research` may report
  `missing_saved_research_inputs` when saved defensive CSV/chart prerequisites
  are absent. Do not run heavy market-data backtests automatically just to fill
  those inputs.
- Generated outputs staying ignored and git status staying clean are expected.

Run the static prerequisite checkpoint:

```powershell
.venv\Scripts\python.exe scripts\verify_vps_monitoring_prerequisites.py
```

Run the terminal status command:

```powershell
.venv\Scripts\python.exe bot.py --vps-monitoring-status
```

This command is report-only. It does not call Alpaca, yfinance, Discord, SQLite
`trade_log`, read paper positions, create orders, schedule anything, or approve
execution. When saved promoted review outputs exist, it reads only
`data/promoted_review_refresh_summary.csv` and `data/promoted_decision_preview.csv`
to show compact step-status and decision-state counts; it does not print full CSV
contents or tickers. High-risk/manual-only boundaries are shown in prose instead
of copy-paste command strings.

Safe next manual VPS steps are to keep using report/refresh/display commands
only, resolve local config privately if the read-only promoted preview needs it,
and rebuild saved defensive research inputs only through separately reviewed
research tasks. Lockfile protection does not approve scheduling or execution.
Execution-capable commands remain manual-only and out of scope for VPS-safe
monitoring scheduling review.

Keep the project paper-only: no live trading, `dry_run=true`, `alpaca.paper=true`,
and `allow_shorting=false`. Do not read or commit config, secrets, logs,
databases, generated CSVs, generated charts, or other private/generated outputs
unnecessarily. Normal `python bot.py`, paper-order tests, and slow-SMA paper
execution must not be scheduled.

## Future MCP Feasibility

MCP may be useful later as a tiny local/custom safe operations adapter for
Hermes or Desktop, but it is not part of the initial VPS setup and is not
approved for implementation yet.

Any future MCP proof of concept must expose only whitelisted report, display,
monitoring, and maintenance tools such as `repo_safety_check`,
`refresh_market_monitor`, `market_monitor_scheduling_readiness`,
`vps_operations_readiness`, `deployment_readiness_report`,
`fetch_news_risk_report`, `write_news_risk_veto_report`,
`show_news_risk_veto`, and `show_safe_command_list`.

It must not expose tools for `submit_order`, `cancel_order`, `run_normal_bot`,
`run_paper_order_test`, `run_slow_sma_paper_execution`,
`generate_buy_signal_from_news`, `generate_sell_signal_from_news`,
`approve_trade_from_news`, `read_config`, `read_env`, `read_logs`,
`read_database`, `expose_tokens`, `schedule_execution`, or
`approve_execution`.

Future news support must be a risk veto only. It may fetch market and financial
news to write ticker-level report labels such as `block_new_entries_today`,
`manual_review_required`, or `no_news_block`. It may block or flag new long
entries for major negative or event-risk news, but it must not generate buy
signals, sell signals, order instructions, position sizing, or execution
approval.

Security boundary:

- Use a tiny local/custom MCP server only if implemented later.
- Do not use third-party MCP servers by default.
- Use a hardcoded allowlist of exact commands and deny by default.
- Use fixed working directory `C:\dev\paper-trading-bot`.
- Do not expose arbitrary shell access.
- Do not access secrets or generated data by default.
- News output must include source, observed time, confidence, and reason.
- Stale news vetoes must expire automatically.
- Return `execution_approved=False` and `scheduling_approved=False` where
  applicable.

Do not consider MCP until the VPS readiness/report chain is stable and
no-overlap or lockfile protection exists for monitor refresh. Add a
docs/report-only news-veto design and saved-data-only news-veto report command
before considering news in MCP. A first MCP proof of concept should expose only
`repo_safety_check` and `refresh_market_monitor`.

## Commands Never To Schedule Automatically

Do not schedule:

```powershell
python bot.py
python bot.py --paper-order-test ... --confirm-paper-order
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

Normal python bot.py remains high-risk/manual-only and must not be scheduled.

Also do not schedule:

- Any future execution command.
- Any command that submits, cancels, or creates orders.
- Any command that writes SQLite `trade_log` rows as part of an execution path.
- Any command that mutates positions.
- Any command that bypasses preview, risk checks, or explicit manual review.

## Update Workflow

When updating the VPS copy later:

```powershell
git pull
python scripts\verify_repo_safety.py
python bot.py --deployment-readiness-report
```

Then run the relevant verifier for the area being changed. Only after those
checks pass should safe report, preview, or display commands be run manually.

## Troubleshooting

- Git not recognised: install Git for Windows, restart the terminal, and confirm
  `git --version` works.
- Python not recognised: install Python 3.11+, enable PATH during install, or
  use the full Python path.
- Virtual environment activation issue: run PowerShell as a normal user and, if
  needed, review the local execution policy for script activation.
- Missing package: activate `.venv`, then rerun
  `python -m pip install -r requirements.txt`.
- Alpaca credential issue: confirm `config.json` exists locally and contains
  paper credentials only. Do not print or paste the values.
- Alpaca API TCP timeout from the VPS: compare
  `paper-api.alpaca.markets:443` and `api.alpaca.markets:443` against general
  HTTPS controls using `--alpaca-connectivity-diagnostics`; if a laptop can
  reach Alpaca but the VPS cannot, review VPS firewall/provider routing/DNS
  before any paper smoke-test discussion.
- yfinance or network issue: check VPS firewall, DNS, outbound HTTPS access, and
  whether the data provider is temporarily unavailable.
- Discord webhook issue: confirm webhook presence locally if alerts are needed,
  but do not paste the webhook into logs or chat.
- OneDrive or Git object lock issue: keep the VPS repo outside OneDrive or other
  synced folders.

## Current Non-Goals

- No loop mode.
- No automatic execution.
- No crypto execution.
- No short execution.
- No live trading.
- No automatic scheduling of execution-capable commands.

## References

- `docs/CURRENT_STATE.md` is the current project handoff and research state.
- `docs/CODEX_WORKFLOW.md` describes Codex task safety and prompt structure.
- `docs/V2_REFACTOR_INVENTORY.md` lists extracted modules and high-risk areas.
- `python bot.py --deployment-readiness-report` checks local deployment
  readiness without deploying.
- `python scripts\verify_repo_safety.py` checks for dangerous tracked or staged
  files before commits.
