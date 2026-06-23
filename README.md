# Python Market Monitoring and Paper Trading Bot

This is a beginner-friendly Python bot for monitoring U.S. stocks and ETFs, researching daily strategies, recording activity in SQLite, sending Discord alerts, and optionally placing Alpaca paper trading orders.

It runs once and exits. Repeated runs require a separate scheduling review; for future market monitor reports, Hermes cron is preferred once Hermes runs on the VPS.

For the current V2 project checkpoint, see [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md).

## Safety First

This project is for learning and paper trading only. It is not financial advice and it does not guarantee profits.

The default config uses:

- `dry_run: true`
- `allow_shorting: false`
- Alpaca paper mode only

The bot refuses to run if `alpaca.paper` is set to `false`. The normal `python bot.py` run is monitoring-only: it may log intended trade actions as `monitor_only`, but it does not submit Alpaca orders or mutate position state. Paper orders remain limited to separate, explicitly confirmed commands such as the manual paper smoke test, slow-SMA paper execution, and QQQ100 paper execution.

Research and backtest modes do not submit Alpaca orders and do not send Discord alerts.

Short selling is riskier than normal long-only trading because losses can grow quickly if price rises. In this project, short selling is only simulated or sent to an Alpaca paper account, never live trading.

## What The Bot Does

- Tracks a list of U.S. stock and ETF tickers.
- Downloads price history with `yfinance`.
- Calculates moving-average signals.
- Creates `BUY`, `SELL`, or `HOLD` signals.
- Supports long-only trading by default.
- Supports optional paper shorting with `allow_shorting: true`.
- Prevents pyramiding.
- Tracks positions using signed quantity.
- Checks for open Alpaca orders before submitting new paper orders.
- Logs every signal and trade decision to SQLite.
- Sends Discord alerts for startup, trades, errors, and completion summary.
- Does not alert every `HOLD`.
- Includes a manual paper-order smoke test.
- Includes a research backtest for `regime_sma_vol_filter`.
- Includes strategy comparison backtesting.
- Exports strategy equity curves for visual inspection.
- Creates simple matplotlib charts from saved strategy comparison results.
- Includes SMA trend parameter sensitivity testing.
- Includes slow SMA trend stress testing across slippage assumptions.
- Includes slow SMA signal preview mode with no order execution.

## Files

- `bot.py` - the bot.
- `config.example.json` - safe example settings.
- `requirements.txt` - Python packages.
- `data/trades.db` - created automatically when the bot runs.
- `logs/bot.log` - created automatically when the bot runs.
- `data/backtest_results.csv` - created by `--backtest`.
- `data/backtest_trades.csv` - created by `--backtest`.
- `data/strategy_comparison_results.csv` - created by `--compare-strategies`.
- `data/strategy_comparison_trades.csv` - created by `--compare-strategies`.
- `data/strategy_portfolio_comparison.csv` - created by `--compare-strategies`.
- `data/strategy_robustness_summary.csv` - created by `--compare-strategies`.
- `data/strategy_portfolio_equity_curves.csv` - created by `--compare-strategies`.
- `data/strategy_ticker_equity_curves.csv` - created by `--compare-strategies`.
- `data/charts/` - created by `--plot-strategy-results`.
- `data/sma_sensitivity_results.csv` - created by `--sma-sensitivity`.
- `data/sma_sensitivity_portfolio.csv` - created by `--sma-sensitivity`.
- `data/trend_stress_test_results.csv` - created by `--trend-stress-test`.
- `data/trend_stress_test_portfolio.csv` - created by `--trend-stress-test`.
- `data/slow_sma_signal_preview.csv` - created by `--preview-slow-sma-signals`.
- `data/slow_sma_action_preview.csv` - created by `--preview-slow-sma-actions`.

## Windows Server 2022 Setup

Install Python 3.11 or newer from the official Python website:

[Python downloads](https://www.python.org/downloads/windows/)

During installation, select **Add python.exe to PATH**.

Open PowerShell in this project folder:

```powershell
cd "C:\dev\paper-trading-bot"
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Create Your Config

Copy the example config:

```powershell
Copy-Item config.example.json config.json
```

Open `config.json` and edit the ticker list:

```json
"tickers": ["AAPL", "MSFT", "SPY"]
```

Use only U.S. stocks and ETFs for version 1.

## Config Options

Important settings:

- `short_window` - shorter moving average window.
- `long_window` - longer moving average window.
- `order_quantity` - number of shares to paper trade.
- `dry_run` - when `true`, the bot does not submit Alpaca orders. The normal bot run remains monitoring-only even when `dry_run` is `false`.
- `paper_kill_switch_enabled` - optional future/dedicated paper-execution safety flag. The safe default is `false`; it does not make the normal bot order-capable.
- `allow_shorting` - when `false`, the bot only opens and closes long positions.
- `database_path` - where SQLite trade history is stored.
- `log_file` - where the text log is stored.
- `strategy` - research strategy settings for `regime_sma_vol_filter`.
- `backtest` - backtest cash, sizing, slippage, history, and output settings.

Keep this unless you know what you are changing:

```json
"alpaca": {
  "paper": true
}
```

If `alpaca.paper` is `false`, the bot refuses to run.

## Alpaca Paper Trading

You only need Alpaca keys when a separate, explicitly confirmed paper-execution command needs read/write Alpaca paper access. The normal `python bot.py` run remains monitoring-only and does not submit orders.

Create or log into an Alpaca account and use paper trading API keys, not live keys:

[Alpaca paper trading](https://alpaca.markets/)

Add the keys to `config.json`:

```json
"alpaca": {
  "paper": true,
  "api_key": "YOUR_PAPER_API_KEY",
  "secret_key": "YOUR_PAPER_SECRET_KEY"
}
```

Or set them as Windows environment variables:

```powershell
setx ALPACA_API_KEY "YOUR_PAPER_API_KEY"
setx ALPACA_SECRET_KEY "YOUR_PAPER_SECRET_KEY"
```

Open a new PowerShell window after using `setx`.

## Discord Alerts

Discord alerts are optional. The bot sends alerts only for:

- Startup.
- Simulated or submitted trades.
- Errors.
- Completion summary.

It does not send an alert for every `HOLD`.

To enable alerts, create a Discord webhook URL for a channel, then set:

```json
"discord": {
  "enabled": true,
  "webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
}
```

You can also use an environment variable:

```powershell
setx DISCORD_WEBHOOK_URL "YOUR_DISCORD_WEBHOOK_URL"
```

## Run the Bot

With the virtual environment activated:

```powershell
python bot.py
```

Use a different config file:

```powershell
python bot.py --config config.json
```

Force safe dry-run mode:

```powershell
python bot.py --dry-run
```

Run the manual paper-order smoke test:

```powershell
python bot.py --paper-order-test MSFT buy 1 --confirm-paper-order
```

The manual paper-order smoke test is explicitly confirmation-gated and performs an early paper kill-switch preflight before opening the database, creating an Alpaca client, checking open orders, or submitting an order. If the saved execution-eligibility/defensive-decision prerequisites or the explicit future kill-switch setting are not satisfied, it refuses before order work begins. This preflight does not change normal `python bot.py` behavior, open-order blocking, SQLite execution writes, or Discord alerts.

The manual `--paper-order-test` path also has a separate narrow connectivity-only smoke-test gate for the exact `AAPL buy 1 --confirm-paper-order` template. That gate can bypass broader strategy-execution blockers only for the one-share AAPL paper connectivity test when saved/read-only live preflight is ready, market status is open, Alpaca is paper mode, credentials are present, there are no open AAPL orders, and no recent matching AAPL buy 1 order is found. It writes `data/paper_order_smoke_test_gate_report.csv`, `data/paper_order_smoke_test_gate_summary.csv`, and `data/paper_order_smoke_test_gate_blockers.csv` when the manual path is run. It does not approve strategy execution, normal bot execution, slow-SMA execution, QQQ100 execution, scheduling, follow-up orders, live trading, shorting, or config-default changes.

Run the regime-filtered SMA volatility backtest:

```powershell
python bot.py --backtest
```

Compare research strategies:

```powershell
python bot.py --compare-strategies
```

Run SMA parameter sensitivity testing:

```powershell
python bot.py --sma-sensitivity
```

Run slow SMA trend stress testing:

```powershell
python bot.py --trend-stress-test
python bot.py --trend-stress-test --research-universe
python bot.py --trend-stress-test --etf-universe
```

Run the research-only monthly ETF momentum rotation backtest:

```powershell
python bot.py --etf-rotation-backtest
```

Run the research-only adaptive risk-on/off momentum backtest:

```powershell
python bot.py --adaptive-momentum-backtest
```

Create a consolidated research ranking report from saved CSV outputs:

```powershell
python bot.py --research-report
```

Create a walk-forward validation report from saved in/out-of-sample CSV outputs:

```powershell
python bot.py --walk-forward-report
```

Create a conservative strategy promotion checklist from saved research reports:

```powershell
python bot.py --strategy-promotion-report
```

Preview current signals for promoted research candidates without trading:

```powershell
python bot.py --preview-promoted-strategies
```

Compare promoted desired positions with current paper positions without trading:

```powershell
python bot.py --preview-promoted-actions
```

To explicitly read Alpaca paper positions for preview context while leaving `dry_run`
unchanged:

```powershell
python bot.py --preview-promoted-actions --use-paper-positions-readonly
```

This flag is read-only and only works with `--preview-promoted-actions`. It requires
Alpaca paper mode and paper API credentials, does not change `config.json`, and is
different from setting `dry_run=false`. If paper positions cannot be read, the preview
keeps using conservative `position_unavailable` rows.

Show the saved promoted action preview as a read-only terminal summary:

```powershell
python bot.py --show-promoted-actions
```

This display helper only reads `data/promoted_strategy_action_preview.csv`, which is created by
`python bot.py --preview-promoted-actions`. It does not refresh market data, call Alpaca, read
positions, submit or cancel orders, write SQLite rows, or send Discord alerts.

Create a research-only risk preview from saved promoted strategy CSVs:

```powershell
python bot.py --promoted-risk-preview
```

This report reads `data/promoted_strategy_preview.csv` and, when available,
`data/promoted_strategy_action_preview.csv`. It writes `data/promoted_risk_preview.csv`.
It reads saved CSV files only. It does not refresh market data, call yfinance, call Alpaca,
read live/current positions directly, submit/cancel/create orders, write SQLite `trade_log`
rows, send Discord alerts, or approve execution. Every output row is marked
`research_only=True` and `preview_only=True`.

When `latest_close` is available in `data/promoted_strategy_preview.csv`, the risk preview
also writes `latest_close`, `assumed_quantity`, and `estimated_desired_notional`.
`estimated_desired_notional` is calculated from the saved close price and
`assumed_quantity=1`. These are saved-data-only estimates, not order instructions, and
they do not refresh prices or positions.

Current risk checks include:

- desired long count versus a conservative `max_open_positions`
- duplicate ticker exposure across promoted strategy rows
- concentration risk where multiple promoted strategies want the same ticker long
- unavailable current position data from the action preview
- notional data quality for saved `latest_close` values

Show the saved promoted risk preview as a read-only terminal summary:

```powershell
python bot.py --show-promoted-risk
```

Run this after `python bot.py --promoted-risk-preview`. This display helper only reads
`data/promoted_risk_preview.csv`. It does not refresh market data, call yfinance, call
Alpaca, read live/current positions, submit/cancel/create orders, write files, write
SQLite `trade_log` rows, send Discord alerts, or approve execution.

It displays count by `risk_status`, count by `risk_check`, count by `desired_position`,
estimated desired notional by strategy, duplicated desired notional by ticker, unique
desired notional by ticker, unique account-style desired notional total,
blocked-for-review rows, warning rows, and a compact table of risk rows. Duplicated
desired notional by ticker intentionally counts overlapping promoted strategy rows, so
two promoted strategies wanting AAPL long can count AAPL twice. Unique desired notional
by ticker counts each desired-long ticker once, which is closer to an account-style
exposure view.

Create a research-only ticker-level consensus report from saved promoted strategy rows:

```powershell
python bot.py --promoted-consensus-preview
```

This report reads `data/promoted_strategy_preview.csv` and writes
`data/promoted_consensus_preview.csv`. It groups promoted strategy rows by ticker,
counts desired long/flat/other votes, and labels each ticker as `unanimous_long`,
`unanimous_flat`, `mixed_long_flat`, `no_supported_votes`, or `unknown`. It is
research-only and preview-only: every row has `execution_eligible=False`, and the
report does not refresh market data, call yfinance, call Alpaca, read live/current
positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts,
or approve execution.

Create a research-only decision policy preview from saved promoted reports:

```powershell
python bot.py --promoted-decision-preview
```

This report reads `data/promoted_consensus_preview.csv`,
`data/promoted_strategy_action_preview.csv`, and `data/promoted_risk_preview.csv`.
It writes `data/promoted_decision_preview.csv` and labels each ticker with a
non-executable `decision_state`, such as `blocked_strategy_disagreement`,
`blocked_risk_review`, `no_action_unanimous_flat`, `review_warning`, or
`research_only_unanimous_long`. Every row has `execution_approved=False`,
`research_only=True`, and `preview_only=True`. It is a policy preview only and does
not refresh market data, call yfinance, call Alpaca, read live/current positions,
create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve
execution.

Display the saved promoted decision preview without trading:

```powershell
python bot.py --show-promoted-decision
```

Run this after `python bot.py --promoted-decision-preview`. This display helper only
reads `data/promoted_decision_preview.csv`; it does not refresh market data, call
yfinance, call Alpaca, read positions, create/submit/cancel orders, write SQLite
`trade_log`, send Discord alerts, or approve execution.

Refresh the promoted review chain without approving execution:

```powershell
python bot.py --refresh-promoted-review
```

This convenience command runs the promoted review chain in order, including the
read-only paper-position action preview path, then prints a compact decision summary.
It writes `data/promoted_review_refresh_summary.csv`. It does not change `dry_run`,
create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve
execution. The command is protected by the monitor lockfile helper to prevent overlapping
promoted review refresh runs; that lock does not approve scheduling or execution.

The static verifier `python scripts\verify_refresh_promoted_review_lock_readiness.py`
checks that `--refresh-promoted-review` remains preview/report/display only, lock-wrapped
only for no-overlap protection, unscheduled, and separate from execution approval.

Preview slow SMA signals without trading:

```powershell
python bot.py --preview-slow-sma-signals
python bot.py --preview-slow-sma-signals --research-universe
python bot.py --preview-slow-sma-signals --etf-universe
```

Preview slow SMA target-position actions without trading:

```powershell
python bot.py --preview-slow-sma-actions
python bot.py --preview-slow-sma-actions --research-universe
python bot.py --preview-slow-sma-actions --etf-universe
```

Execute slow SMA target-position alignment in Alpaca paper trading:

```powershell
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper --research-universe
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper --etf-universe
```

Slow SMA paper execution is explicitly confirmation-gated and performs paper kill-switch preflight before cache setup, database initialization, Discord startup alert, Alpaca client creation, paper position reads, open-order checks, SQLite execution writes, or order submission. With the current saved prerequisites, it refuses early and does not create/submit/cancel orders, write execution `trade_log` rows, or send Discord alerts.

Create simple PNG charts from saved strategy comparison CSV files:

```powershell
python bot.py --plot-strategy-results
```

## V2 Baseline Verification

Before V2 refactors, run the baseline verifier:

```powershell
python scripts\verify_v2_baseline.py
```

The script runs safe command checks only. It does not run `--paper-order-test` or `--execute-slow-sma-paper`, so it does not submit Alpaca orders.

Before GitHub commits or pushes, run the repository safety verifier:

```powershell
python scripts\verify_repo_safety.py
```

It checks that private files, generated CSVs, database files, logs, charts, virtual environments, and obvious secret-like filenames are not tracked or staged.

Create a local deployment readiness audit before any future VPS/server handoff:

```powershell
python bot.py --deployment-readiness-report
```

This is a reporting-only check for future Windows Server VPS use. It may inspect local files and Git metadata, but it does not deploy, create Windows Task Scheduler tasks, refresh market data, call Alpaca, submit orders, send Discord alerts, or approve execution. Any future Windows Task Scheduler setup must start with report/display commands only and is not execution approval.

Create a VPS/Hermes operations readiness audit for monitoring/report/display commands only:

```powershell
python bot.py --vps-operations-readiness-report
```

This writes `data/vps_operations_readiness_report.csv` and checks static readiness for operating safe monitoring/report/display commands from the VPS/Hermes setup. It verifies the repo path, virtual-environment expectation, required project files, repo safety verifier, market monitor and deployment-readiness command availability, ignored generated outputs, untracked private files, Hermes market-monitor candidate documentation, and never-schedule command boundaries. It does not deploy, schedule, create Windows Task Scheduler tasks, create Hermes cron jobs, create services, load `config.json`, read secrets, call Alpaca, read positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, approve scheduling, or approve execution.

Create a research-only intraday monitoring snapshot for the fixed ticker universe:

```powershell
python bot.py --market-monitor-snapshot
```

This writes `data/market_monitor_snapshot.csv` using yfinance intraday data for the fixed ticker universe from the ticker universe readiness report. It does not load `config.json`, call Alpaca, read paper positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, schedule anything, or approve execution. More frequent price checks do not mean more frequent trades, and daily strategies should not become intraday trading strategies without separate research.

Display the saved market monitor snapshot without refreshing market data:

```powershell
python bot.py --show-market-monitor
```

This reads `data/market_monitor_snapshot.csv` only and prints a compact terminal summary of row counts, data status counts, strongest positive/negative intraday moves, and recorded data errors. It does not call yfinance, load `config.json`, call Alpaca, read paper positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, schedule anything, or approve execution.

Create a saved-CSV quality report for the market monitor snapshot:

```powershell
python bot.py --market-monitor-quality-report
```

This reads `data/market_monitor_snapshot.csv` only and writes `data/market_monitor_quality_report.csv`. It checks required columns, row count, duplicate tickers, missing prices or timestamps, stale timestamps, data errors, abnormal intraday moves, and the non-execution safety flags. It does not refresh yfinance data, load `config.json`, call Alpaca, read paper positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, schedule anything, or approve execution.

Refresh the safe market monitor chain:

```powershell
python bot.py --refresh-market-monitor
```

This runs the ticker universe readiness report, market monitor snapshot, saved market monitor display, and market monitor quality report in order. It prints a compact step summary and writes the same generated CSV outputs as the individual report commands. It does not change normal `python bot.py` behavior, load `config.json`, call Alpaca, read paper positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, schedule anything, connect monitoring to strategies, or approve execution.

Create a report-only scheduling readiness audit for the market monitor refresh chain:

```powershell
python bot.py --market-monitor-scheduling-readiness-report
```

This writes `data/market_monitor_scheduling_readiness_report.csv` and checks whether the current VPS-safe monitoring set is ready to be considered for a separate future scheduling review. The assessed set is limited to `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research`. It checks lockfile coverage, config presence without reading contents, saved promoted/defensive output presence, generated-output ignore policy, and false scheduling/execution approval flags. It does not create Windows Task Scheduler tasks, add cron/loop execution, approve scheduling, call Alpaca, call yfinance, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, connect monitoring output to strategy execution, or approve execution.

Create a static no-overlap/lockfile readiness design report:

```powershell
python bot.py --monitor-lockfile-readiness-report
```

This writes `data/monitor_lockfile_readiness_report.csv` and classifies future safe refresh/report/display candidates, blocked execution-capable commands, stale-lock policy requirements, metadata constraints, no-secret lock contents, future lock helper tests, and manual scheduling review requirements. This command, `--refresh-promoted-review`, and `--refresh-defensive-research` are the only commands currently protected by the monitor lockfile helper; the lock prevents overlapping safe refresh/report commands only and does not refresh market data, call yfinance, call Alpaca, read positions beyond existing read-only preview paths, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, create schedules, create services, approve scheduling, or approve execution.

The pure no-network contract verifier, `python scripts\verify_monitor_lockfile_contract.py`, defines what a future lock helper must satisfy before implementation. It does not implement locking, create lockfiles, schedule anything, run bot commands, and does not create schedules.

The pure helper verifier, `python scripts\verify_monitor_lockfile_helper.py`, checks the helper in `trading_bot/safety/monitor_lockfile.py`, including temp-directory lock acquire/release cleanup, fresh-lock blocking, malformed-lock blocking, and stale-lock manual review.

The integration-readiness checkpoint, `python scripts\verify_monitor_lockfile_integration_readiness.py`, verifies that exactly `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research` are lock-wrapped, `bot.py` is not using the helper directly, no other command is lock-wrapped, and future safe report/display/monitor refresh commands remain manual-review only.

The final lockfile checkpoint, `python scripts\verify_monitor_lockfile_final_state.py`, verifies the exact three-command lock boundary, blocked execution commands, false execution/scheduling approval flags, stale-lock manual review, and VPS handoff documentation. On the VPS, use `git pull`, `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, and `.venv\Scripts\python.exe scripts\verify_monitor_lockfile_final_state.py` before manual report/refresh/display review commands. Generated CSVs/charts/logs/databases/secrets/config must not be committed or pasted.

The VPS monitoring prerequisite checkpoint, `python scripts\verify_vps_monitoring_prerequisites.py`, separates environment readiness from missing local prerequisites. Missing `config.json` for read-only promoted preview is classified as `config_missing_for_readonly_promoted_review`, and missing saved defensive inputs are classified as `missing_saved_research_inputs`; neither classification approves scheduling or execution.

For VPS terminal monitoring, use:

```powershell
python bot.py --vps-monitoring-status
```

This is report/display-only. It summarizes repo-safety reminders, lock-wrapped
safe commands, config presence without reading `config.json`, saved defensive
input presence, generated-output ignore expectations, latest saved promoted
review step/decision counts when present, high-risk/manual-only boundaries in
prose, and next safe manual report actions. It avoids printing pasteable
high-risk command lines. It does not call Alpaca, yfinance, Discord, SQLite
`trade_log`, read paper positions, create orders, schedule anything, or approve
execution.

The status output also labels key saved outputs by modification-time freshness:
`fresh` for updated within 24 hours, `warning_stale` for older than 24 hours but
within 72 hours, `stale` for older than 72 hours, and `missing` when absent.
Freshness/staleness labels are monitoring diagnostics only. Missing or stale
saved outputs are prerequisites/status issues, not trading approval.

For a Telegram-friendly daily monitoring summary, use:

```powershell
python bot.py --vps-daily-monitoring-summary
```

This is report/display-only and terminal-only. It summarizes safety reminders,
lock-wrapped safe commands, promoted decision-state counts, defensive refresh
step counts, saved-output freshness labels, and a compact final status:
`healthy_monitoring_state`, `monitoring_warning`, or
`monitoring_stale_or_missing_inputs`. It also prints `action_required`,
`action_reason`, and `suggested_manual_action` so Telegram output says what to
do next without pasteable high-risk commands. It does not refresh promoted/defensive
reports, call Alpaca, call yfinance, send Discord alerts, write SQLite
`trade_log`, read config contents, create generated files, schedule anything, or
approve execution.

Future Hermes cron readiness plan for safe monitoring reports only:

Hermes cron preferred for future monitoring scheduling if configured. No
refresh cron job or execution scheduling is currently approved or created beyond
the existing status-only job. Use Hermes cron for safe
monitoring/reporting only; not for execution. Windows Task Scheduler remains an
alternative only for keeping the Hermes gateway running, not for trading
commands.

Do not paste config/API keys/webhooks/account IDs into Hermes prompts. Candidate
jobs should run from `C:\dev\paper-trading-bot`, use
`.venv\Scripts\python.exe`, include a repo-safety check, use concise output
capture, and use restricted `enabled_toolsets` where Hermes supports them.
Initial cron candidate should probably be a status/checkpoint job before refresh
jobs. Refresh jobs should remain protected by lockfile/no-overlap. A stale lock
requires manual review. Scheduling cadence is a separate future decision.

The initial future Hermes cron candidate command set is limited to
`--vps-monitoring-status`, `--market-monitor-scheduling-readiness-report`,
`--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and
`--refresh-defensive-research`. A future manual review must approve the exact
cadence, exact command list, enabled toolsets, output destination, and failure
behaviour before any Hermes cron job is created.

The current status-job checkpoint is in `docs/HERMES_CRON_JOB_DESIGN.md`. It
records the verified `paper-bot-vps-status-check` job and its status-only command
sequence: repo safety, Hermes cron readiness, and
`--vps-daily-monitoring-summary`. It explicitly confirms the job does not run
refresh commands. Verify the checkpoint with
`python scripts\verify_hermes_cron_job_design.py`.

Before any future scheduling review, run `python scripts\verify_repo_safety.py`,
run `python scripts\verify_hermes_cron_readiness.py`, run
`python bot.py --market-monitor-scheduling-readiness-report`, and confirm
generated CSV/cache files remain ignored. Stop if any scheduled candidate tries
to read or print `config.json` contents, call Alpaca, read positions, write
SQLite `trade_log`, send Discord alerts, create orders, create other cron jobs
recursively, or approve execution. Lockfile protection does not make
execution-capable commands schedulable.

Never schedule:

```powershell
python bot.py
python bot.py --paper-order-test ...
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

The current daily Hermes status cron exists as `paper-bot-vps-status-check`
with job ID `345188fbb60c`. It runs daily at 10:10am UK local time with cron
expression `10 10 * * *` in `Europe/London`, delivers to Telegram, uses
script-only / no-agent mode, runs from `C:\dev\paper-trading-bot`, and executes
repo safety, Hermes cron readiness, and `--vps-daily-monitoring-summary`.
Verified output is repo_safety PASS, hermes_cron_readiness PASS,
vps_daily_monitoring_summary PASS, final_monitoring_status `healthy_monitoring_state`,
action_required `no_action_required`, execution_approved false,
scheduling_approved false, and freshness_warnings: none. It does not run refresh
commands, trade, approve scheduling beyond this one status job, approve
execution, pull/commit/push code, or inspect/print config contents, secrets,
logs, databases, or full generated CSV contents.

No refresh cron job is currently created. A future promoted review refresh cron
requires a separate manual review; see
`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` and verify the design with
`python scripts\verify_hermes_promoted_review_refresh_cron_design.py`.
The older `docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` file is a legacy pointer
to the canonical refresh-specific design.

For interpreting Telegram output from `paper-bot-vps-status-check`, use
`docs/HERMES_CRON_MONITORING_RUNBOOK.md` and verify it with
`python scripts\verify_hermes_cron_monitoring_runbook.py`. The runbook covers
`healthy_monitoring_state`, `monitoring_warning`,
`monitoring_stale_or_missing_inputs`, and failed-step responses without
approving execution or creating a second cron.

Create a research-only portfolio risk policy audit before any future execution discussion:

```powershell
python bot.py --portfolio-risk-policy-report
```

This reads saved CSVs and `config.example.json` only, writes `data/portfolio_risk_policy_report.csv`, and documents conservative report-only policies such as paper-only mode, dry-run default, shorting disabled, proposed max open positions, desired notional review, duplicate ticker exposure, strategy disagreement, execution approval status, future kill switch work, and future daily summary work. It does not enforce risk checks, change order sizing, read live positions/account equity, call Alpaca, submit orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Display the saved portfolio risk policy report without rerunning it:

```powershell
python bot.py --show-portfolio-risk-policy
```

This is a read-only terminal display helper for `data/portfolio_risk_policy_report.csv`. It does not refresh data, read positions, enforce risk policy, submit orders, write files, or approve execution.

Create a reporting-only readiness audit for future paper kill-switch design:

```powershell
python bot.py --paper-kill-switch-readiness-report
```

This writes `data/paper_kill_switch_readiness_report.csv` and audits what would be required for a future paper-only kill switch. It does not add a config setting, enforce a kill switch, change order paths, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Create a design/report-only paper kill-switch gate scaffold:

```powershell
python bot.py --paper-kill-switch-gate-report
```

This writes `data/paper_kill_switch_gate_report.csv` and checks static/saved prerequisites for a future paper kill-switch gate, including safe config example defaults, confirmation-gated high-risk commands, isolated helper availability, the manual `--paper-order-test` preflight, the slow SMA paper-execution preflight, missing normal bot preflight work, existing readiness/eligibility reports, and whether defensive allocation remains blocked. It does not add order instructions, call Alpaca, write SQLite `trade_log`, send Discord alerts, promote strategies, or approve execution.

Create a saved-data/static paper execution protection checkpoint:

```powershell
python bot.py --paper-execution-protection-report
```

This writes `data/paper_execution_protection_report.csv` and summarizes which paper execution paths have kill-switch preflight, which path remains deliberately unchanged, and whether execution remains blocked. It recognizes the manual paper-order and slow SMA preflights, keeps normal `python bot.py` as future work, and does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, promote strategies, or approve execution.

Create a saved-data/static normal bot execution policy checkpoint:

```powershell
python bot.py --normal-bot-execution-policy-report
```

This writes `data/normal_bot_execution_policy_report.csv` and documents Option A: normal `python bot.py` stays original/dry-run-first and deliberately separate from defensive paper execution. Explicit paper execution stays in separate confirmation-gated and kill-switch-gated commands such as `--paper-order-test` and `--execute-slow-sma-paper`. The report does not add execution design, wire additional order paths, create order instructions, call Alpaca, write SQLite `trade_log`, send Discord alerts, promote strategies, or approve execution.

Verify the paper kill-switch enforcement contract and the limited manual preflight wiring:

```powershell
python scripts\verify_paper_kill_switch_enforcement_contract.py
```

This no-network verifier defines the contract that any future defensive paper-execution command would have to satisfy before execution design can continue. It checks paper-only/default boundaries, confirmation gates, report/preview non-approval, that the current gate remains blocked/future-work-required, and that the helper is wired only to the manual paper-order and slow SMA paper-execution preflights. It does not add a bot command, change order submission mechanics, or approve execution.

An isolated pure helper also exists at `trading_bot/safety/paper_kill_switch.py`. It can evaluate plain Python safety context values for paper kill-switch design tests. `--paper-order-test` and `--execute-slow-sma-paper` consult it as early refusal preflights only; the helper remains separate from normal `python bot.py` behavior, open-order blocking, SQLite execution writes, Discord sending, and the lower-level order submission helper.

Create a saved-data-only defensive execution readiness report:

```powershell
python bot.py --defensive-execution-readiness-report
```

This writes `data/defensive_execution_readiness_report.csv` and summarizes what still blocks future paper execution design for the defensive allocation path. It combines saved defensive allocation, kill-switch gate, contract-verifier presence, execution eligibility, and portfolio risk policy state. It recognizes that manual `--paper-order-test` and slow SMA paper execution now have preflight, while the normal bot path remains blocked/future work. It does not start execution design, add enforcement to additional order paths, create order instructions, call Alpaca, write SQLite `trade_log`, send Discord alerts, promote strategies, or approve execution.

Create a saved-data-only execution eligibility view:

```powershell
python bot.py --execution-eligibility-report
```

This writes `data/execution_eligibility_report.csv` and combines saved promoted decision, portfolio risk policy, paper kill-switch readiness, and deployment readiness reports into a final non-executable eligibility view. It does not refresh previews, enforce risk policy, implement a kill switch, create order instructions, call Alpaca, read positions, submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Build a static saved-CSV research dashboard:

```powershell
python bot.py --build-research-dashboard
```

This writes `data/dashboard/research_dashboard.html` from existing saved CSV reports and optional existing chart PNGs. When available, it also displays `data/defensive_research_state_report.csv`, `data/paper_execution_protection_report.csv`, `data/normal_bot_execution_policy_report.csv`, and a minimal Project Research State panel from `data/project_research_state_summary.csv`, `data/project_research_state_refresh.csv`, and `data/project_research_state_next_steps.csv`. The state panel consolidates current stock/ETF and crypto research state. It does not approve preview promotion, does not approve execution, and does not create a dashboard server or background service. It is a static HTML file only: no Flask, Streamlit, Dash, FastAPI, localhost server, network port, market-data refresh, Alpaca call, order action, SQLite `trade_log` write, Discord alert, risk enforcement, or execution approval is added.

The initial `trading_bot/` package skeleton now exists for V2 refactoring, but `bot.py` still owns the current behaviour for now.

See `docs/V2_REFACTOR_INVENTORY.md` for the current extraction inventory and recommended next refactor order.

See `docs/V2_RESEARCH_CHECKPOINT.md` for the current research conclusions and safety boundary before adding more strategy work.

See `docs/CODEX_WORKFLOW.md` for the recommended prompt and verification workflow for future Codex tasks.

## Research Backtesting

Backtest mode is research-only. It does not call Alpaca, does not submit orders, and does not send Discord alerts.

The current research strategy is `regime_sma_vol_filter`:

- Uses SPY as the market regime ticker.
- Enters long only when SPY is above its 200-day SMA.
- Requires the ticker to be above its 200-day SMA.
- Uses a 20-day SMA crossing above a 50-day SMA as the entry trigger.
- Skips new entries when recent realised volatility is unusually high.
- Exits on a bearish 20/50 crossover or when the ticker falls below its 200-day SMA.
- Uses next-day open execution with slippage to avoid look-ahead bias.

Outputs:

```text
data/backtest_results.csv
data/backtest_trades.csv
```

The normal research backtest uses the shared research-only cost model for the configured default slippage assumption. It does not connect to Alpaca execution.

Strategy comparison mode compares:

- `buy_and_hold_baseline`
- `sma_20_50_basic`
- `sma_20_50_regime`
- `sma_50_200_trend`
- `buy_above_200_exit_below_200`
- `fifty_two_week_high_breakout`

Buy-and-hold is included as a benchmark so active strategies can be compared against simply owning the ticker.

Outputs:

```text
data/strategy_comparison_results.csv
data/strategy_comparison_trades.csv
data/strategy_portfolio_comparison.csv
data/strategy_robustness_summary.csv
data/strategy_portfolio_equity_curves.csv
data/strategy_ticker_equity_curves.csv
data/charts/
```

Strategy comparison uses the shared research-only cost model for the configured default slippage assumption. The 52-week high breakout candidate is included here as research-only and is not connected to Alpaca execution.

SMA sensitivity mode tests whether the 50/200 trend strategy is robust across nearby parameter choices:

- `20 / 100`
- `30 / 150`
- `40 / 160`
- `50 / 200`
- `60 / 200`
- `100 / 200`

Outputs:

```text
data/sma_sensitivity_results.csv
data/sma_sensitivity_portfolio.csv
```

SMA sensitivity uses the shared research-only cost model for the configured default slippage assumption. It does not connect to Alpaca execution.

ETF rotation backtest mode tests a long-only monthly momentum rotation across a default liquid ETF universe. It uses SPY as the regime filter, holds the top 3 eligible ETFs by default, skips partial rebalance trades below `100.0`, reports SPY/QQQ/equal-weight buy-and-hold benchmarks, saves only research CSV files, and is not connected to Alpaca execution. `data/etf_rotation_results.csv` includes `full_period`, `in_sample`, and `out_of_sample` portfolio rows using a simple chronological 70% / 30% split so the walk-forward report can pair the strategy.

Outputs:

```text
data/etf_rotation_results.csv
data/etf_rotation_trades.csv
data/etf_rotation_equity_curve.csv
```

ETF rotation robustness mode reads saved ETF rotation equity/trade CSVs only and writes fixed chronological out-of-sample rows for `split_60_40`, `split_70_30`, and `split_80_20`. It does not rerun the strategy, change ETF rotation rules, download market data, call Alpaca, write SQLite `trade_log`, send Discord alerts, or approve execution. These rows let volatility-managed ETF robustness compare against matching monthly ETF rotation split metrics.

Command:

```text
python bot.py --etf-rotation-robustness
```

Output:

```text
data/etf_rotation_robustness_report.csv
```

ETF breadth regime backtest mode reads a saved ETF close-history CSV only and tests a fixed research-only breadth regime allocation. The expected saved input is `data/etf_breadth_price_history.csv` with `date,ticker,close` columns. It classifies regimes from ETF breadth versus 200-day SMA and SPY trend, then writes research CSVs without downloading market data, calling Alpaca, creating orders, writing SQLite `trade_log`, sending Discord alerts, changing existing strategy logic, or approving execution.

Build the saved ETF close-history input first when it is missing:

```text
python bot.py --build-etf-breadth-price-history
```

The builder uses the existing research market-data/yfinance pattern to write `data/etf_breadth_price_history.csv`. It is research data-prep only; it does not call Alpaca, read positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, change strategy logic, or approve execution.

Command:

```text
python bot.py --etf-breadth-regime-backtest
```

Outputs:

```text
data/etf_breadth_regime_backtest.csv
data/etf_breadth_regime_summary.csv
```

ETF breadth regime decision mode reads saved breadth backtest/summary rows and saved defensive comparison/robustness rows when available. It compares breadth regime metrics against `monthly_etf_momentum_rotation` and `volatility_managed_dual_momentum_etf`, then labels the idea conservatively as underperforming, diagnostic-only, promising-needs-robustness, or insufficient-data. It does not download market data, call Alpaca, create orders, change promotion logic, or approve execution.

Command:

```text
python bot.py --etf-breadth-regime-decision-report
```

Output:

```text
data/etf_breadth_regime_decision_report.csv
```

ETF breadth regime robustness mode reads the saved ETF breadth price history and evaluates the fixed breadth allocation across `split_60_40`, `split_70_30`, and `split_80_20` out-of-sample periods. It labels the idea conservatively as `robust_diagnostic_candidate`, `split_sensitive_diagnostic`, `not_robust`, or `insufficient_data`. It remains research/reporting only and does not download market data, call Alpaca, create orders, promote the strategy, or approve execution.

Command:

```text
python bot.py --etf-breadth-regime-robustness
```

Output:

```text
data/etf_breadth_regime_robustness_report.csv
```

Vol-managed ETF backtest mode tests the first advanced long-only ETF research idea from the deep research shortlist. The fixed strategy, `volatility_managed_dual_momentum_etf`, uses the ETF rotation universe, monthly rebalance, top 3 momentum selection, 200-day SMA asset and SPY regime filters, 63-day realised volatility, inverse-volatility sizing, and a 10% annual target-volatility cap with gross exposure capped at 100%. It does not use leverage, margin, shorting, Alpaca, SQLite `trade_log`, Discord alerts, or execution approval.

Command:

```text
python bot.py --vol-managed-etf-backtest
```

Outputs:

```text
data/vol_managed_etf_results.csv
data/vol_managed_etf_trades.csv
data/vol_managed_etf_equity_curve.csv
data/vol_managed_etf_iteration_log.csv
```

Vol-managed ETF robustness mode checks the same fixed strategy across fixed chronological splits: `split_60_40`, `split_70_30`, and `split_80_20`. It compares against matching monthly ETF rotation robustness rows from `data/etf_rotation_robustness_report.csv` when available, falling back to the existing 70/30 ETF rotation result if the fixed-split report has not been generated yet. It does not tune parameters, change strategy rules, call Alpaca, write SQLite `trade_log`, send Discord alerts, or approve execution.

Command:

```text
python bot.py --vol-managed-etf-robustness
```

Output:

```text
data/vol_managed_etf_robustness_report.csv
```

Strategy improvement lab mode tests a small fixed set of growth-aware ETF allocation variants meant to investigate whether current defensive ETF research is too cash-dragged. It uses daily yfinance ETF history, monthly rebalancing, fixed 126-day momentum and 200-day trend rules, fixed 52-week-high closeness scoring where relevant, fixed breadth thresholds, and fixed volatility diagnostics only. Variants include the existing monthly ETF rotation reference, balanced dual momentum with a defensive sleeve, breadth-aware risk-on rotation, growth-biased rotation with a crash gate, a cost-aware fixed-threshold refinement of that growth-biased crash gate, a partial defensive-sleeve refinement of that same crash gate, factor/style rotation with an absolute gate, sector 52-week-high continuation, and an ambitious fixed multi-sleeve growth allocator. It also includes SPY and equal-weight ETF buy-and-hold benchmarks. Promising labels are research labels only; they do not approve orders, paper execution, scheduling, cron, shorting, leverage, margin, or any strategy-to-execution wiring.

The cost-aware variant, `growth_biased_rotation_cost_aware_rebalance`, keeps the original `growth_biased_rotation_crash_gate` intact and adds only a fixed 5 percentage-point rebalance threshold plus a near-top holding preference. It is designed to test whether the current best active candidate can reduce turnover or cost sensitivity without giving up too much CAGR, Sharpe, or Calmar. Reduced turnover alone is not enough to promote the refinement if cost/split sensitivity is unchanged or headline performance drags. Judge it directly against the original growth-biased strategy, not just against SPY.

The partial defensive-sleeve variant, `growth_biased_rotation_partial_defensive_sleeve`, also keeps `growth_biased_rotation_crash_gate` intact. It uses the same growth/risk ETF ranking and softened crash-gate posture, but adds fixed defensive exposure only when breadth or regime weakens: 75/25 risk/defensive in mixed conditions, 50/50 in weak conditions when eligible risk ETFs remain, and mostly defensive/cash in stress conditions. The defensive sleeve uses fixed 126-day momentum and 200-day trend checks across SHY, IEF, TLT, GLD, XLU, XLP, and USMV. It should be judged against the original growth-biased strategy, the cost-aware refinement, monthly ETF rotation, and SPY. It is a research hypothesis for split stability and drawdown behaviour only, not execution approval. The cost-aware and partial defensive-sleeve refinements remain in the lab as tested/rejected candidates when diagnostics show return drag without cost/split improvement.

The remaining growth-biased fixed batch tested `growth_biased_rotation_reentry_filter`, `growth_biased_rotation_regime_recovery_filter`, `growth_biased_rotation_breadth_looser_gate`, and `growth_biased_rotation_breadth_stricter_gate`. The stricter breadth gate is now the active research lead because it improved CAGR, Sharpe, and Calmar versus the previous `growth_biased_rotation_crash_gate` baseline without worsening max drawdown, cash drag, cost sensitivity, or split sensitivity. It still remains research-only, does not approve execution, and should still be checked against SPY buy-and-hold.

Command:

```text
python bot.py --strategy-improvement-lab
```

Optional saved display:

```text
python bot.py --show-strategy-improvement-lab
```

Outputs:

```text
data/strategy_improvement_lab_results.csv
data/strategy_improvement_lab_trades.csv
data/strategy_improvement_lab_equity_curve.csv
data/strategy_improvement_lab_summary.csv
data/strategy_improvement_lab_iteration_log.csv
```

Strategy improvement robustness mode reruns the fixed strategy-improvement candidate set and writes combined chronological split, fixed cost, drawdown, and candidate comparison reports. It checks `split_60_40`, `split_70_30`, and `split_80_20`, uses fixed `low_cost`, `default_cost`, and `high_cost` one-way assumptions, and compares cash drag and drawdown tradeoffs against the monthly ETF rotation reference. A strategy does not need to beat SPY buy-and-hold to be labelled promising, but the report shows whether it still trails SPY. The ambitious multi-sleeve allocator remains aggressive research only.

Command:

```text
python bot.py --strategy-improvement-robustness
```

Optional saved display:

```text
python bot.py --show-strategy-improvement-robustness
```

Outputs:

```text
data/strategy_improvement_robustness_report.csv
data/strategy_improvement_cost_stress_report.csv
data/strategy_improvement_drawdown_report.csv
data/strategy_improvement_candidate_comparison.csv
```

Strategy improvement diagnostics mode reads the saved lab and robustness CSVs only. It now treats `growth_biased_rotation_breadth_stricter_gate` as the active research lead and `growth_biased_rotation_crash_gate` as the previous growth-biased baseline. It compares the cost-aware, partial defensive-sleeve, re-entry, recovery, and fixed breadth-gate refinements directly against that baseline. Rejected refinements remain labelled as tested history, while the next recommendation list moves to stricter-gate validation: split validation, cost-stress review, drawdown-period review, and a promotion checkpoint. It does not add another strategy, rerun yfinance-heavy backtests, call Alpaca, create orders, schedule anything, or approve execution.

Command:

```text
python bot.py --strategy-improvement-diagnostics
```

Optional saved display:

```text
python bot.py --show-strategy-improvement-diagnostics
```

Outputs:

```text
data/strategy_improvement_diagnostics.csv
data/growth_biased_rotation_diagnostics.csv
```

Growth-biased stricter validation mode reads saved strategy-improvement outputs only and validates the current active research lead, `growth_biased_rotation_breadth_stricter_gate`, against the previous `growth_biased_rotation_crash_gate` baseline. It writes deeper split validation, cost-stress review, drawdown-period review, benchmark comparison, and promotion-checkpoint CSVs. Split validation compares the stricter gate with the original growth-biased baseline, monthly ETF rotation, SPY buy-and-hold, and equal-weight ETF benchmark when saved rows exist. A validation pass means research-lead status or possible future preview-candidate discussion only; it does not approve orders, paper execution, promoted execution, scheduling, or cron.

Command:

```text
python bot.py --growth-biased-stricter-validation
```

Optional saved display:

```text
python bot.py --show-growth-biased-stricter-validation
```

Outputs:

```text
data/growth_biased_stricter_validation.csv
data/growth_biased_stricter_split_validation.csv
data/growth_biased_stricter_cost_review.csv
data/growth_biased_stricter_drawdown_review.csv
data/growth_biased_stricter_benchmark_comparison.csv
data/growth_biased_stricter_promotion_checkpoint.csv
```

Growth-biased stricter promotion-readiness mode reads saved validation and strategy-improvement outputs only and explains what still blocks the current active research lead from moving into future preview-candidate discussion. It writes a readiness summary and blocker rows for benchmark, split/robustness, cost, drawdown, saved-output freshness, and final preview-readiness status. This is a blocker report only: it does not approve execution, paper execution, preview promotion, scheduling, cron, order instructions, or strategy-to-execution wiring.

Command:

```text
python bot.py --growth-biased-stricter-promotion-readiness
```

Optional saved display:

```text
python bot.py --show-growth-biased-stricter-promotion-readiness
```

Outputs:

```text
data/growth_biased_stricter_promotion_readiness.csv
data/growth_biased_stricter_promotion_blockers.csv
```

Growth-biased stricter manual review pack mode reads saved validation and strategy-improvement outputs only and assembles a structural review pack for `growth_biased_rotation_breadth_stricter_gate`. It compares the stricter gate with the previous crash-gate lead, monthly ETF rotation reference, equal-weight ETF benchmark, and SPY benchmark where saved rows exist. It also writes saved regime/context rows for full-period, in/out-of-sample or fixed split rows, and the saved worst drawdown window when available. This is research/report-only manual review support; it does not approve preview promotion automatically and does not approve execution.

Command:

```text
python bot.py --growth-biased-stricter-manual-review-pack
```

Optional saved display:

```text
python bot.py --show-growth-biased-stricter-manual-review-pack
```

Outputs:

```text
data/growth_biased_stricter_manual_review_pack.csv
data/growth_biased_stricter_regime_context.csv
```

Growth-biased stricter threshold neighbourhood mode runs a small fixed research-only robustness check around the current stricter breadth gate. It tests fixed breadth gates at 40%, 45%, 50%, 55%, and 60%, using the same strategy-improvement lab simulation helpers, and compares the neighbourhood against the previous crash-gate lead, monthly ETF rotation reference, equal-weight ETF benchmark, and SPY buy-and-hold where available. The goal is to see whether the stricter-gate improvement looks like a credible nearby-threshold cluster or a one-threshold accident. It does not approve preview promotion automatically and does not approve execution.

Command:

```text
python bot.py --growth-biased-stricter-threshold-neighbourhood
```

Optional saved display:

```text
python bot.py --show-growth-biased-stricter-threshold-neighbourhood
```

Outputs:

```text
data/growth_biased_stricter_threshold_neighbourhood.csv
data/growth_biased_stricter_threshold_neighbourhood_summary.csv
```

Growth-biased stricter cost/turnover stress mode reads the saved threshold-neighbourhood output and stress-tests the current 55% stricter-gate cluster against fixed one-way cost assumptions of 0, 5, 10, 25, 50, and 100 bps. It applies a simple explicit research mapping of `turnover * one_way_cost_bps / 100` to CAGR, derives cost-adjusted Sharpe and Calmar, and compares the result with the original crash-gate baseline and SPY gap from the saved neighbourhood report. This is research/report-only manual review support; it does not approve preview promotion automatically and does not approve execution.

Command:

```text
python bot.py --growth-biased-stricter-cost-turnover-stress
```

Optional saved display:

```text
python bot.py --show-growth-biased-stricter-cost-turnover-stress
```

Outputs:

```text
data/growth_biased_stricter_cost_turnover_stress.csv
data/growth_biased_stricter_cost_turnover_stress_summary.csv
```

Growth-biased stricter persistence filter mode tests fixed turnover-control variants around the 55% stricter breadth gate: a 55% reference, 2-month and 3-month minimum holds, a 5 percentage-point momentum-gap switch rule, near-top-2 holding, and a combined persistence rule. It also includes one Codex-designed fixed research candidate, `codex_ambitious_concentrated_growth_persistence`, which uses a concentrated top-two growth ETF allocation with a 55% breadth gate, 2-month hold, 7.5 percentage-point momentum gap, and near-top-2 retention. This is research/report-only and does not approve preview promotion or execution.

Command:

```text
python bot.py --growth-biased-stricter-persistence-filter
```

Optional saved display:

```text
python bot.py --show-growth-biased-stricter-persistence-filter
```

Outputs:

```text
data/growth_biased_stricter_persistence_filter.csv
data/growth_biased_stricter_persistence_filter_summary.csv
```

Codex ambitious validation mode reads saved persistence-filter outputs only and creates a focused validation checkpoint for `codex_ambitious_concentrated_growth_persistence`. It writes summary, split, cost, and drawdown validation CSVs to help decide whether the candidate should become the new active research lead. Missing split or drawdown-window data is reported conservatively rather than inferred. This is research/report-only and does not approve preview promotion or execution.

Command:

```text
python bot.py --codex-ambitious-validation
```

Optional saved display:

```text
python bot.py --show-codex-ambitious-validation
```

Outputs:

```text
data/codex_ambitious_validation.csv
data/codex_ambitious_validation_summary.csv
data/codex_ambitious_validation_splits.csv
data/codex_ambitious_validation_costs.csv
data/codex_ambitious_validation_drawdowns.csv
```

Codex ambitious split/drawdown validation mode runs the focused fixed-split and drawdown-window checkpoint for `codex_ambitious_concentrated_growth_persistence`. It evaluates `split_60_40`, `split_70_30`, and `split_80_20` out-of-sample windows, computes the worst drawdown start/trough/recovery where market data is available, compares the drawdown window with SPY and the stricter-gate lead, and writes a lead-change checkpoint. This is a research label only; it does not approve preview promotion or execution.

Command:

```text
python bot.py --codex-ambitious-split-drawdown-validation
```

Optional saved display:

```text
python bot.py --show-codex-ambitious-split-drawdown-validation
```

Outputs:

```text
data/codex_ambitious_split_drawdown_validation.csv
data/codex_ambitious_split_validation.csv
data/codex_ambitious_drawdown_windows.csv
data/codex_ambitious_lead_change_checkpoint.csv
```

Codex ambitious lead decision mode reads saved validation, split/drawdown, persistence, threshold, cost/turnover, and manual-review reports where available and creates a final research-only lead-decision checkpoint for `codex_ambitious_concentrated_growth_persistence`. It decides whether the candidate should become the new active research lead as a research label only. If cost review remains open, the label keeps that blocker explicit. It does not approve preview promotion automatically and does not approve execution.

Command:

```text
python bot.py --codex-ambitious-lead-decision
```

Optional saved display:

```text
python bot.py --show-codex-ambitious-lead-decision
```

Outputs:

```text
data/codex_ambitious_lead_decision.csv
data/codex_ambitious_lead_decision_summary.csv
data/codex_ambitious_lead_decision_evidence.csv
```

Adaptive momentum backtest mode is research-only. It ranks risk ETFs by fixed multi-horizon momentum with a volatility penalty, uses SPY as the risk regime filter, and rotates to defensive ETFs when the regime is weak. It saves only research CSV files and is not connected to Alpaca execution. `data/adaptive_momentum_results.csv` includes `full_period`, `in_sample`, and `out_of_sample` portfolio rows using the same simple chronological 70% / 30% reporting split as ETF rotation so the walk-forward report can pair the strategy.

Outputs:

```text
data/adaptive_momentum_results.csv
data/adaptive_momentum_trades.csv
data/adaptive_momentum_equity_curve.csv
```

Research report mode reads existing research CSV files and creates a side-by-side ranked report. It does not rerun backtests, download data, submit orders, or send alerts. The report keeps all-row rankings for transparency, adds a decision-view ranking that prefers full-period portfolio-level rows, separates buy-and-hold benchmarks from active strategy candidates, and includes simple diagnostic columns explaining return gaps, drawdown tradeoffs, turnover, and likely underperformance reasons.

Output:

```text
data/research_report.csv
```

Walk-forward report mode reads existing research CSV files and compares matching `in_sample` and `out_of_sample` rows. It labels robustness conservatively, adds portfolio/single-ticker and benchmark/active classifications, keeps portfolio-level rows as the headline decision view, includes ETF rotation and adaptive momentum when their period rows have been generated, and does not rerun backtests, download data, submit orders, or send alerts.

Output:

```text
data/walk_forward_report.csv
```

Strategy promotion report mode combines `data/research_report.csv` and `data/walk_forward_report.csv` into a conservative checklist. A `preview_candidate` status means future preview-mode research only; it does not approve paper execution.

Output:

```text
data/strategy_promotion_report.csv
```

Defensive strategy report mode reads saved research and walk-forward reports and scores portfolio-level active strategies for defensive usefulness. It does not require beating buy-and-hold CAGR, and instead rewards lower drawdown, strong out-of-sample Sharpe/Calmar, and robust or improved walk-forward labels. It is research-only and does not approve execution.

Output:

```text
data/defensive_strategy_report.csv
```

Defensive candidate comparison mode reads saved walk-forward, defensive, promotion, and vol-managed ETF reports to compare `monthly_etf_momentum_rotation`, `volatility_managed_dual_momentum_etf`, and `adaptive_risk_on_off_momentum`. It separates raw metric rank from policy rank, focuses on out-of-sample Sharpe/Calmar, drawdown, fixed-split consistency, trade count, turnover burden, and strategy complexity. It is research-only and does not approve execution.

Command:

```text
python bot.py --defensive-candidate-comparison
```

Output:

```text
data/defensive_candidate_comparison.csv
```

Defensive research state report mode reads saved defensive comparison, ETF breadth, short research, promoted decision, portfolio risk, and execution eligibility CSVs where available. It consolidates the current stock/ETF defensive checkpoint into one saved report without rerunning backtests, refreshing market data, calling Alpaca, creating orders, writing SQLite `trade_log`, sending Discord alerts, promoting strategies, or approving execution.

Command:

```text
python bot.py --defensive-research-state-report
```

Output:

```text
data/defensive_research_state_report.csv
```

Defensive allocation preview mode reads the saved defensive research state report and writes a compact posture preview for the lead defensive reference, secondary/split-sensitive checks, breadth diagnostic context, adaptive monitoring, paused short research, and the execution gate. It is preview/reporting only: it creates no order instructions, promotes no strategy, and grants no execution approval.

Command:

```text
python bot.py --defensive-allocation-preview
```

Output:

```text
data/defensive_allocation_preview.csv
```

Defensive allocation risk preview mode reads `data/defensive_allocation_preview.csv` and checks whether the saved posture preview is complete and safely non-executable before any future defensive allocation decision report is considered. It checks expected components, execution approval flags, order-instruction style columns, split sensitivity, diagnostic-only breadth status, adaptive complexity, paused short research, and the blocked execution gate. It is saved-data-only and does not approve execution.

Command:

```text
python bot.py --defensive-allocation-risk-preview
```

Output:

```text
data/defensive_allocation_risk_preview.csv
```

Defensive allocation decision report mode combines the saved defensive allocation preview and risk preview into a final non-executable decision checkpoint. It answers whether the current defensive allocation posture can move toward paper-execution design; the current expected answer is no/not yet while execution remains blocked and future kill-switch, risk, and confirmation gates are not cleared. It does not create order instructions, promote strategies, or approve execution.

Command:

```text
python bot.py --defensive-allocation-decision-report
```

Output:

```text
data/defensive_allocation_decision_report.csv
```

ETF defensive drawdown comparison mode reads saved monthly ETF rotation and vol-managed ETF equity curves plus fixed-split robustness reports. It compares worst drawdown periods and the `split_80_20` out-of-sample drawdown tradeoff, including whether lower drawdown came with weaker CAGR/Sharpe/Calmar context. It is research-only and does not rerun backtests, refresh market data, call Alpaca, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.

Command:

```text
python bot.py --etf-defensive-drawdown-comparison
```

Output:

```text
data/etf_defensive_drawdown_comparison.csv
```

ETF defensive comparison charting reads saved ETF rotation and vol-managed ETF equity curves only and writes PNG diagnostics under `data/charts/`. It creates one equity comparison chart and one drawdown comparison chart. It does not rerun backtests, refresh market data, call Alpaca, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.

Command:

```text
python bot.py --plot-etf-defensive-comparison
```

Outputs:

```text
data/charts/etf_defensive_equity_comparison.png
data/charts/etf_defensive_drawdown_comparison.png
```

Defensive research refresh mode runs the current defensive saved-report/dashboard chain in order and writes a small step summary. It refreshes saved-data reports/charts where safe, checks the saved vol-managed robustness report as a prerequisite, and does not rerun market-data-backed backtests. It does not call Alpaca, read positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.

The static verifier `python scripts\verify_refresh_defensive_research_lock_readiness.py`
checks that `--refresh-defensive-research` remains research/report/chart only,
lock-wrapped only for no-overlap protection, unscheduled, and separate from execution
approval.

Command:

```text
python bot.py --refresh-defensive-research
```

Output:

```text
data/defensive_research_refresh_summary.csv
```

Drawdown period report mode reads saved equity-curve CSV files and identifies major portfolio drawdown periods for the main benchmark and active research candidates. It compares active drawdowns with matching benchmark windows where dates overlap, marks missing curves as `insufficient_data`, and remains research-only.

Command:

```text
python bot.py --drawdown-period-report
```

Output:

```text
data/drawdown_period_report.csv
```

Short-selling readiness report mode performs a static/local readiness audit for possible future short-selling research and preview work. It does not enable shorting, add short strategies, create orders, call Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, or approve execution.

Command:

```text
python bot.py --short-selling-readiness-report
```

Output:

```text
data/short_selling_readiness_report.csv
```

Short hedge backtest mode tests a synthetic SPY-only short hedge concept for research. It enters a research short when SPY closes below its 200-day SMA and returns flat when SPY closes at or above the 200-day SMA. It writes full-period, in-sample, and out-of-sample result rows, plus trades and an equity curve. Result rows include `research_status`, `research_conclusion`, and `required_next_step`; the initial simple rule is labelled not useful when CAGR, Sharpe, and Calmar are negative. It does not enable `allow_shorting`, create or submit orders, call Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, model borrow availability, or approve execution. Borrow fees are explicitly marked `not_modelled_initial_research`.

Command:

```text
python bot.py --short-hedge-backtest
```

Outputs:

```text
data/short_hedge_backtest_results.csv
data/short_hedge_backtest_trades.csv
data/short_hedge_equity_curve.csv
```

Short strategy lab mode tests one controlled multi-ticker ETF short-selling research hypothesis after the simple SPY short hedge failed. The fixed strategy, `research_weak_etf_short_momentum`, shorts the weakest two liquid ETFs by 126-day return only when SPY is below its 200-day SMA and each selected ETF is below its own 200-day SMA. It rebalances monthly, stays short/cash only, caps synthetic gross short exposure at 1x, and records a fixed placeholder borrow-fee assumption of `borrow_fee_bps_annual=300`. It does not run a parameter search, enable `allow_shorting`, add short preview or execution, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, add crypto shorting, or approve execution.

Command:

```text
python bot.py --short-strategy-lab
```

Outputs:

```text
data/short_strategy_lab_results.csv
data/short_strategy_lab_trades.csv
data/short_strategy_lab_equity_curve.csv
data/short_strategy_iteration_log.csv
```

Short/leverage research lab mode tests a small fixed set of synthetic hypotheses only: trend-gated SPY/QQQ leverage, saved stock/ETF lead leverage proxies when a saved equity curve exists, a weak-regime SPY short hedge, a fixed sector relative long/short spread, and a fixed defensive-versus-cyclical spread. It writes full-period, split, placeholder cost/borrow/financing, and drawdown CSVs. The cost rows use fixed placeholder assumptions only; they are not broker-specific margin, borrow, or financing terms. This lab does not enable `allow_shorting`, margin, leverage, crypto shorting, Alpaca execution, preview promotion, scheduling, or strategy-to-execution wiring.

Command:

```text
python bot.py --short-leverage-research-lab
```

Saved display:

```text
python bot.py --show-short-leverage-research-lab
```

Outputs:

```text
data/short_leverage_research_lab.csv
data/short_leverage_research_lab_summary.csv
data/short_leverage_research_lab_costs.csv
data/short_leverage_research_lab_splits.csv
data/short_leverage_research_lab_drawdowns.csv
```

QQQ leverage validation mode focuses the synthetic leverage branch on fixed QQQ trend-gated exposure levels: 1.0x, 1.25x, 1.5x, 1.75x, and 2.0x when QQQ is above its 200-day SMA, otherwise cash. It writes full-period, split, cost/financing, and drawdown validation CSVs, with QQQ buy-and-hold, SPY buy-and-hold, and cash benchmark context. Financing and trading-cost rows are placeholders only; they are not broker-specific terms and do not approve margin or leverage execution.

Command:

```text
python bot.py --qqq-leverage-validation-report
```

Saved display:

```text
python bot.py --show-qqq-leverage-validation-report
```

Outputs:

```text
data/qqq_leverage_validation_report.csv
data/qqq_leverage_validation_summary.csv
data/qqq_leverage_validation_costs.csv
data/qqq_leverage_validation_splits.csv
data/qqq_leverage_validation_drawdowns.csv
```

QQQ adaptive leverage lab mode compares the unlevered QQQ trend gate against a small fixed set of adaptive synthetic exposure candidates. The reference set is QQQ buy-and-hold, SPY buy-and-hold, `qqq_100_trend_gate`, `qqq_125_trend_gate`, and `qqq_150_trend_gate`. The first Codex-designed candidate, `codex_qqq_adaptive_trend_exposure`, holds cash below QQQ SMA200, uses 1.0x exposure in elevated volatility, 1.25x in normal positive trend, and 1.5x only when 20-day realised volatility is below 90% of its 252-day median. The second, `codex_qqq_drawdown_brake_trend`, holds cash below QQQ SMA200, uses 1.25x in positive trend, cuts to 0.75x after an 8% rolling 63-day drawdown, and requires 20-day recovery confirmation before re-leveraging. This is fixed research only: no optimisation loop, no machine learning, no intraday data, no options, no leveraged ETF product modelling, no margin execution, and no execution approval.

Command:

```text
python bot.py --qqq-adaptive-leverage-lab
```

Saved display:

```text
python bot.py --show-qqq-adaptive-leverage-lab
```

Outputs:

```text
data/qqq_adaptive_leverage_lab.csv
data/qqq_adaptive_leverage_lab_summary.csv
data/qqq_adaptive_leverage_lab_costs.csv
data/qqq_adaptive_leverage_lab_splits.csv
data/qqq_adaptive_leverage_lab_drawdowns.csv
```

QQQ lead decision report mode reads saved QQQ leverage/adaptive outputs and saved Codex ambitious lead-decision context to decide whether the QQQ branch should challenge or replace the current stock/ETF active research lead. It compares `codex_ambitious_concentrated_growth_persistence`, `qqq_100_trend_gate`, `codex_qqq_adaptive_trend_exposure`, high-drawdown QQQ leverage references, and SPY/QQQ benchmark rows where saved inputs exist. This is a saved-output checkpoint only: it does not refresh market data, call yfinance or Alpaca, approve preview promotion, approve leverage or margin, or connect any strategy to execution.

Command:

```text
python bot.py --qqq-lead-decision-report
```

Saved display:

```text
python bot.py --show-qqq-lead-decision-report
```

Outputs:

```text
data/qqq_lead_decision_report.csv
data/qqq_lead_decision_summary.csv
data/qqq_lead_decision_evidence.csv
```

QQQ trend-gate manual review pack mode reads saved QQQ lead-decision, leverage validation, adaptive leverage, project research state, and paper-readiness context where available. It explains why `qqq_100_trend_gate` is now the clean stock/ETF research lead, keeps `codex_qqq_adaptive_trend_exposure` as an ambitious alternative, keeps `qqq_150_trend_gate` as a rejected high-drawdown reference, and records remaining blockers before any future preview or execution discussion. This is research/report-only: it does not refresh market data, call yfinance or Alpaca, load config, read positions, write SQLite `trade_log`, send alerts, schedule anything, approve preview promotion, approve execution, or connect strategies to Alpaca or paper orders. Expected final status is `qqq_trend_gate_research_lead_confirmed_not_execution_ready`.

Command:

```text
python bot.py --qqq-trend-gate-manual-review-pack
```

Saved display:

```text
python bot.py --show-qqq-trend-gate-manual-review-pack
```

Outputs:

```text
data/qqq_trend_gate_manual_review_pack.csv
data/qqq_trend_gate_manual_review_summary.csv
data/qqq_trend_gate_manual_review_evidence.csv
data/qqq_trend_gate_manual_review_blockers.csv
```

QQQ preview-candidate readiness report mode reads the saved QQQ manual review pack, QQQ decision outputs, validation cost/split/drawdown rows, project research state, and paper-readiness context where available. It answers whether `qqq_100_trend_gate` is ready for manual preview-candidate discussion and what still blocks paper execution. Preview readiness is manual discussion only: it does not approve paper execution, does not approve execution, does not create order instructions, and does not connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --qqq-preview-candidate-readiness-report
```

Saved display:

```text
python bot.py --show-qqq-preview-candidate-readiness-report
```

Outputs:

```text
data/qqq_preview_candidate_readiness_report.csv
data/qqq_preview_candidate_readiness_summary.csv
data/qqq_preview_candidate_readiness_evidence.csv
data/qqq_preview_candidate_readiness_blockers.csv
```

QQQ100 preview-candidate readiness pack mode is the saved-output checkpoint for the clean `qqq_100_trend_gate` lead. It reads saved QQQ lead/manual/readiness, adaptive/leverage validation, high-growth branch, project research-state, and paper-readiness outputs where present. It asks whether manual preview-candidate discussion is reasonable while keeping `codex_qqq_adaptive_trend_exposure` as an ambitious alternative only, keeping `qqq_150_trend_gate` rejected as the higher-drawdown reference, and keeping the high-growth branch out of preview discussion. It does not add preview implementation, does not approve paper execution, does not approve execution, and does not connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --qqq100-preview-candidate-readiness-pack
```

Saved display:

```text
python bot.py --show-qqq100-preview-candidate-readiness-pack
```

Outputs:

```text
data/qqq100_preview_candidate_readiness_pack.csv
data/qqq100_preview_candidate_readiness_summary.csv
data/qqq100_preview_candidate_readiness_evidence.csv
data/qqq100_preview_candidate_readiness_blockers.csv
```

QQQ100 preview signal pack mode is the first non-execution preview signal for the clean `qqq_100_trend_gate` lead. It may fetch QQQ daily data, calculate latest close versus the fixed 100-day SMA trend gate, and write a saved preview signal with `desired_position=long` above SMA100 or `desired_position=flat` at or below SMA100. It also records the design checkpoint: high-growth is excluded, `codex_qqq_adaptive_trend_exposure` remains an ambitious alternative only, `qqq_150_trend_gate` remains rejected, action preview versus paper positions is not added, and paper execution remains blocked. This is a preview signal only; it does not approve execution, does not create order instructions, does not read positions, and does not connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --qqq100-preview-signal-pack
```

Saved display:

```text
python bot.py --show-qqq100-preview-signal-pack
```

Outputs:

```text
data/qqq100_preview_signal_pack.csv
data/qqq100_preview_signal_summary.csv
data/qqq100_preview_signal_design.csv
data/qqq100_preview_signal_blockers.csv
```

QQQ100 action preview mode is the saved-signal action-preview shell for `qqq_100_trend_gate`. Default mode reads only `data/qqq100_preview_signal_pack.csv`, does not call Alpaca, does not read positions, and records `current_position_status=position_not_read` with `current_position_source=saved_signal_only`. A separate read-only paper-position comparison can be requested only with both `--use-paper-positions-readonly` and `--confirm-readonly-alpaca-check`; that mode may load the existing paper config and read QQQ paper position context only, without printing secrets or account identifiers. The output uses manual-review/alignment language only, never order instructions. It does not approve preview promotion, paper execution, live execution, scheduling, or strategy-to-execution wiring.

Command:

```text
python bot.py --qqq100-action-preview
```

Optional read-only position context:

```text
python bot.py --qqq100-action-preview --use-paper-positions-readonly --confirm-readonly-alpaca-check
```

Saved display:

```text
python bot.py --show-qqq100-action-preview
```

Outputs:

```text
data/qqq100_action_preview.csv
data/qqq100_action_preview_summary.csv
data/qqq100_action_preview_blockers.csv
```

QQQ100 paper-readiness blocker report mode is the saved-output blocker checkpoint after the QQQ100 action preview. It reads saved preview-signal, action-preview, QQQ readiness, portfolio-risk, execution-eligibility, paper kill-switch, paper-order smoke-test, project research-state, and high-growth contrast outputs where present. It explains what still blocks any future manually confirmed QQQ100 paper execution design: the separate AAPL smoke test, QQQ100 execution design, sizing, portfolio risk limits, kill-switch enforcement, execution eligibility, open-order and duplicate-exposure handling, manual confirmation wording, postcheck design, scheduling, and strategy-to-execution integration. It is saved-output only; it does not call Alpaca, read positions, refresh market data, create order instructions, write SQLite `trade_log`, send alerts, schedule anything, or approve paper execution.

Command:

```text
python bot.py --qqq100-paper-readiness-blocker-report
```

Saved display:

```text
python bot.py --show-qqq100-paper-readiness-blocker-report
```

Outputs:

```text
data/qqq100_paper_readiness_blocker_report.csv
data/qqq100_paper_readiness_blocker_summary.csv
data/qqq100_paper_readiness_blocker_evidence.csv
data/qqq100_paper_readiness_blocker_blockers.csv
```

QQQ100 paper execution readiness report mode reads saved readiness evidence only and asks whether `qqq_100_trend_gate` is ready for a separately reviewed manual paper-execution command design. It can recognise the saved AAPL smoke-test postcheck, QQQ100 preview signal/action preview, promoted preview row, multi-strategy portfolio overlap warnings, portfolio-risk, execution eligibility, kill-switch, and paper-execution protection context. It may label the branch ready for manual execution-design review, but it does not itself submit orders or approve broad paper execution.

Command:

```text
python bot.py --qqq100-paper-execution-readiness-report
```

Saved display:

```text
python bot.py --show-qqq100-paper-execution-readiness-report
```

Outputs:

```text
data/qqq100_paper_execution_readiness_report.csv
data/qqq100_paper_execution_readiness_summary.csv
data/qqq100_paper_execution_readiness_evidence.csv
data/qqq100_paper_execution_readiness_blockers.csv
```

Paper-live promotion gate mode is the saved-output/report-only gate for the first paper-live candidate discussion. It is deliberately limited to `qqq_100_trend_gate` / `QQQ`: adaptive QQQ remains an ambitious alternative, `qqq_150_trend_gate` remains rejected, SMA/slow-SMA are excluded, and high-growth plus crypto remain research-only. The gate checks for static verifiers and saved QQQ100 research/preview/action/readiness, portfolio/risk, execution-readiness, and protection evidence where available. Missing required evidence becomes a blocked/manual-review row. `paper_live_candidate=True` means candidate-discussion status only; it does not approve preview implementation, paper execution, order instructions, scheduling, or strategy-to-execution wiring.

Command:

```text
python bot.py --paper-live-promotion-gate
```

Saved display:

```text
python bot.py --show-paper-live-promotion-gate
```

Outputs:

```text
data/paper_live_promotion_gate.csv
data/paper_live_promotion_gate_summary.csv
data/paper_live_promotion_gate_blockers.csv
data/paper_live_promotion_gate_evidence.csv
```

All rows preserve `execution_approved=false`, `paper_execution_approved=false`, and `scheduling_approved=false`. Explicit human approval is still required before any future manually confirmed paper execution command.

Paper-live readiness report mode is the saved-output/report-only Step 7 checkpoint for future manual QQQ100 paper-action discussion. It checks static verifier presence, normal bot monitoring-only boundaries, Alpaca paper-only/no-live boundaries, QQQ100 fixed ticker/strategy scope, exact zero/one-share alignment policy, excluded SMA/slow-SMA/high-growth/crypto paths, separate confirmation-gated paper execution, open-order and duplicate-order requirements, postcheck/position-readability evidence, portfolio/risk evidence, execution-readiness evidence, and the no-scheduling boundary. Missing saved evidence is listed as a blocker or warning. It does not call Alpaca, read positions, refresh market data, create order instructions, approve paper execution, approve live trading, or schedule anything.

Command:

```text
python bot.py --paper-live-readiness-report
```

Saved display:

```text
python bot.py --show-paper-live-readiness-report
```

Outputs:

```text
data/paper_live_readiness_report.csv
data/paper_live_readiness_summary.csv
data/paper_live_readiness_blockers.csv
data/paper_live_readiness_evidence.csv
```

Every summary row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, and `live_trading_approved=false`.

Paper-live state summary mode is the saved-output/report-only Step 10 daily checkpoint before anyone considers a future manually confirmed QQQ100 paper command. It reads saved QQQ100 preview/action/postcheck/order evidence, paper-live promotion gate output, paper-live readiness output, and saved paper-execution state files where available. It reports the active strategy, active ticker, desired state, saved current paper-position state, last saved QQQ100 order result, current saved alignment state, promotion gate status, readiness status, missing saved-evidence blockers, manual-discussion allowance, follow-up/repeat allowance, scheduling allowance, and live-trading allowance. Missing saved evidence is reported as blocked/manual-review or unavailable; it is not an exception.

Command:

```text
python bot.py --paper-live-state-summary
```

Saved display:

```text
python bot.py --show-paper-live-state-summary
```

Outputs:

```text
data/paper_live_state_summary.csv
data/paper_live_state_components.csv
data/paper_live_state_blockers.csv
data/paper_live_state_evidence.csv
```

This is not a readiness upgrade and does not approve execution, paper execution, follow-up orders, scheduling, live trading, or order instructions. Every summary row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

Paper-live evidence audit mode is the saved-output/report-only reconciliation checkpoint for the QQQ100 paper-live chain. It reads the same saved QQQ100 preview/action/postcheck/order/state evidence used by the promotion gate, readiness report, and state summary, then reports which saved files and fields are present, missing, contradictory, or sufficient for state reconciliation. It can show a reconciled saved state such as desired `long`, saved `paper_position_long`, saved quantity `1`, saved filled QQQ100 order result, and `aligned_long`; that still does not approve a follow-up order.

Command:

```text
python bot.py --paper-live-evidence-audit
```

Saved display:

```text
python bot.py --show-paper-live-evidence-audit
```

Outputs:

```text
data/paper_live_evidence_audit.csv
data/paper_live_evidence_audit_summary.csv
data/paper_live_evidence_audit_blockers.csv
data/paper_live_evidence_audit_evidence.csv
```

The audit lists exact missing saved files or fields through `exact_missing_saved_evidence` instead of a vague missing-evidence label. Every row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

Exact QQQ100 alignment requires saved quantity evidence. If the saved postcheck file or quantity field is missing, the state summary must report `qqq100_alignment_unverified_missing_saved_quantity` instead of treating a saved `paper_position_long` label as verified alignment.

QQQ100 manual paper execution is a separate high-risk, confirmation-gated command for the clean QQQ lead only. It reads `data/qqq100_preview_signal_pack.csv`, requires `--confirm-qqq100-paper`, requires Alpaca paper mode, refuses live mode, refuses shorting/leverage, checks the QQQ paper position, blocks on open QQQ orders or recent matching QQQ one-share broker orders, and can only align `qqq_100_trend_gate` / `QQQ` to exactly zero or one share. It does not use the normal config ticker universe and does not apply to high-growth, crypto, QQQ150, or adaptive QQQ alternatives. General `execution_approved`, `paper_execution_approved`, and `scheduling_approved` remain false; only the narrow `strategy_execution_approved` / `qqq100_one_share_alignment_approved` flags can be true for the exact manually confirmed QQQ100 path.

Command:

```text
python bot.py --execute-qqq100-paper --confirm-qqq100-paper
```

If the saved signal is `long` and the QQQ paper position is flat, the command may submit one paper `BUY 1 QQQ` order. If the saved signal is `long` and the position is exactly one QQQ share, it writes an already-aligned no-order-needed result. If the saved signal is `flat` and the position is exactly one QQQ share, it may submit one paper `SELL 1 QQQ` order without overselling. If the QQQ paper position is more than one QQQ share, the command must block/manual review rather than silently treating it as aligned, reducing to one, or selling all. Blocked, skipped, or submitted runs write:

```text
data/qqq100_paper_execution_result.csv
data/qqq100_paper_execution_summary.csv
data/qqq100_paper_execution_blockers.csv
```

Do not schedule this command. Do not use it as a template for normal `python bot.py`, `--paper-order-test`, slow-SMA paper execution, live trading, or any other strategy-to-execution path.

QQQ100 paper postcheck is a read-only verification report for the manual QQQ100 paper command. Default mode writes a blocked/static report; broker order and position reads require `--confirm-readonly-alpaca-check`. Confirmed read-only mode checks recent QQQ buy 1 paper order history and the current QQQ paper position, then compares the position with the saved `qqq100_preview_signal_pack` desired position. It never creates, submits, cancels, replaces, or prepares orders, never writes SQLite `trade_log`, never sends Discord/Telegram alerts, and approves no follow-up, repeat, scheduling, or general execution.

```text
python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check
python bot.py --show-qqq100-paper-postcheck
```

Outputs:

```text
data/qqq100_paper_postcheck.csv
data/qqq100_paper_postcheck_summary.csv
data/qqq100_paper_postcheck_blockers.csv
```

QQQ100 repeat/alignment workflow design is a saved-output-only design report for a future manual repeat/alignment review. It reads saved CSV context such as the QQQ100 preview signal, action preview, paper postcheck, paper execution state summary, readiness, portfolio preview/risk, and connectivity diagnostics where available. It does not call Alpaca, read positions, refresh yfinance, create/submit/cancel/replace orders, write SQLite `trade_log`, send Discord/Telegram alerts, change config defaults, create schedules, or approve repeat execution. The design is QQQ only, `qqq_100_trend_gate` only, max one paper share, no duplicate buy when already long one share, no scaling above one share, no shorting, no leverage, and no high-growth/crypto linkage.

```text
python bot.py --qqq100-repeat-alignment-workflow-design
python bot.py --show-qqq100-repeat-alignment-workflow-design
```

Outputs:

```text
data/qqq100_repeat_alignment_workflow_design.csv
data/qqq100_repeat_alignment_workflow_states.csv
data/qqq100_repeat_alignment_workflow_blockers.csv
data/qqq100_repeat_alignment_workflow_checklist.csv
```

The expected design status is `qqq100_repeat_alignment_design_created`. Allowed future states are limited to manual-review/no-action design labels such as `possible_manual_open_long_candidate`, `aligned_long_no_action`, and `aligned_flat_no_action`; blocked states include over-allocation, missing/stale desired position, open QQQ orders, recent-order cooldown, closed/unknown market status, and broker read failure. `followup_order_approved=false`, `repeat_execution_approved=false`, `execution_approved=false`, and `scheduling_approved=false` remain hard boundaries.

Multi-sleeve strategy monitor is a saved-output-only monitoring/design report that lets the active QQQ100 paper sleeve sit conceptually beside defensive ETF, high-growth stock, crypto, and cash/no-position sleeves without connecting those other sleeves to execution. It reads saved CSV context only, including paper execution state, QQQ100 postcheck/action preview/repeat design, multi-strategy portfolio preview, portfolio risk, high-growth checkpoints, crypto research summaries, and project research state where present. It does not call Alpaca, read live positions, refresh yfinance, create/submit/cancel/replace orders, write SQLite `trade_log`, send Discord/Telegram alerts, change config defaults, create Hermes/scheduler jobs, or approve execution.

```text
python bot.py --multi-sleeve-strategy-monitor
python bot.py --show-multi-sleeve-strategy-monitor
```

Outputs:

```text
data/multi_sleeve_strategy_monitor.csv
data/multi_sleeve_strategy_sleeves.csv
data/multi_sleeve_strategy_positions.csv
data/multi_sleeve_strategy_blockers.csv
data/multi_sleeve_strategy_next_steps.csv
```

The expected monitor status is `multi_sleeve_monitor_created`. The only active paper sleeve may be `qqq100_core_trend_sleeve` when saved evidence confirms QQQ long 1 and aligned. Defensive ETF, high-growth stock, and crypto sleeves remain research-only; cash/no-position remains design-only. Major warnings include `high_growth_and_qqq_overlap_risk`, `crypto_volatility_sleeve_not_ready`, `defensive_sleeve_not_validated_for_execution`, `sleeve_allocation_policy_missing`, `repeat_execution_not_approved`, and `scheduling_not_approved`.

Sleeve research scoreboard is a saved-output-only research ranking report for current and candidate sleeves. It reads saved CSV context only, scores QQQ100, defensive ETF, high-growth stock, crypto, and a Codex experimental research sleeve side by side, and labels missing metrics as `missing_saved_metrics` rather than inventing values. It does not call Alpaca, read live positions, refresh yfinance, create/submit/cancel/replace orders, write SQLite `trade_log`, send Discord/Telegram alerts, change config defaults, create Hermes/scheduler jobs, expand QQQ100 execution, add repeat execution, or wire any sleeve to execution.

```text
python bot.py --sleeve-research-scoreboard
python bot.py --show-sleeve-research-scoreboard
```

Outputs:

```text
data/sleeve_research_scoreboard.csv
data/sleeve_research_candidates.csv
data/sleeve_research_rankings.csv
data/sleeve_research_blockers.csv
data/sleeve_research_next_steps.csv
data/sleeve_research_codex_experimental_sleeve.csv
```

The expected scoreboard status is `sleeve_research_scoreboard_created`. `qqq100_core_trend_sleeve` remains the best active paper sleeve and the only active paper sleeve. The Codex experimental research sleeve is a research-only adaptive QQQ plus defensive crash-gate hypothesis, currently labelled `codex_qqq_defensive_crash_gate_research_sleeve`; it can score high on ambition but has `codex_experimental_execution_approved=false`. Defensive, high-growth, and crypto sleeves remain research-only, with blockers around validation, allocation policy, drawdown/concentration/split/cost, volatility, overlap, repeat execution, and scheduling.

Codex QQQ defensive crash-gate research pack is a saved-output-only targeted research pack for `codex_qqq_defensive_crash_gate_research_sleeve`. It uses QQQ100 as the reference and compares fixed defensive/crash-gate hypotheses: `qqq100_trend_gate_reference`, `codex_qqq_cash_crash_gate_sleeve`, `codex_qqq_spy_defensive_gate_sleeve`, `codex_qqq_partial_defensive_sleeve`, `codex_qqq_fast_crash_exit_reentry_sleeve`, and `codex_qqq_calmar_optimised_defensive_gate_sleeve`. It reads saved metrics where available and labels missing metrics as `missing_saved_metrics` or `missing_saved_data`; it does not fetch market data, call Alpaca, read live positions, create/submit/cancel/replace orders, write SQLite `trade_log`, send alerts, create schedules, expand QQQ100 execution, add repeat execution, or wire the Codex experimental sleeve to execution.

```text
python bot.py --codex-qqq-defensive-crash-gate-research-pack
python bot.py --show-codex-qqq-defensive-crash-gate-research-pack
```

Outputs:

```text
data/codex_qqq_defensive_crash_gate_research_pack.csv
data/codex_qqq_defensive_crash_gate_candidates.csv
data/codex_qqq_defensive_crash_gate_rankings.csv
data/codex_qqq_defensive_crash_gate_splits.csv
data/codex_qqq_defensive_crash_gate_blockers.csv
data/codex_qqq_defensive_crash_gate_next_steps.csv
```

The expected status is `codex_qqq_defensive_research_pack_created`. Candidate labels are research prompts only, with blockers for missing saved metrics, split validation, cost/turnover stress, reference underperformance, execution wiring, repeat execution, and scheduling. The recommended next step is `run_saved_or_research_data_backtest_for_codex_qqq_defensive_candidates`.

Sleeve return-stream mode is a research-only saved daily stream generator for the multi-sleeve portfolio backtest. It can generate `qqq100_core_trend_sleeve` / `qqq_100_trend_gate` rows, transparent defensive QQQ crash-gate rows, a cash/no-position stream, and a Codex experimental stream that points to the generated defensive QQQ candidate. If high-growth or crypto daily return streams are not available, it writes `missing_saved_return_stream` quality rows instead of inventing daily returns from summary metrics. QQQ100 metric alignment is labelled `approximate_or_needs_reconciliation` unless the saved source details can be matched exactly. It may use the project’s research-only yfinance pattern with a local cache, but it does not use Alpaca or broker data and does not approve execution.

```text
python bot.py --sleeve-return-streams
python bot.py --show-sleeve-return-streams
```

Outputs:

```text
data/sleeve_return_streams.csv
data/sleeve_return_streams_summary.csv
data/sleeve_return_streams_sleeves.csv
data/sleeve_return_streams_quality.csv
data/sleeve_return_streams_blockers.csv
data/sleeve_return_streams_next_steps.csv
```

The expected status is `sleeve_return_streams_partial_created` while high-growth and crypto streams are missing. These streams are research data only; all order, follow-up, repeat, scheduling, live, high-growth, crypto, and Codex-experimental execution approval flags remain false.

High-growth return-stream mode is a research-only saved daily stream generator for existing high-growth stock candidates. It reuses the fixed high-growth drawdown-control research logic and can write daily streams for `codex_broad_growth_balanced_breakout_control` plus the broad Top1 reference where research market data exists. These streams are for multi-sleeve research only; they do not approve preview promotion, paper execution, repeat execution, scheduling, or any Alpaca/order path.

```text
python bot.py --high-growth-return-streams
python bot.py --show-high-growth-return-streams
```

Outputs:

```text
data/high_growth_return_streams.csv
data/high_growth_return_stream_metrics.csv
data/high_growth_return_stream_summary.csv
data/high_growth_return_stream_blockers.csv
```

The expected status is `high_growth_return_streams_created` when enough research price data exists. If market data is unavailable, the report labels the data gap instead of inventing returns. High-growth remains research-only and `execution_approved=false`.

Crypto return-stream mode is a research-only saved daily stream generator for the BTC/ETH crypto sleeve used by multi-sleeve research. It reuses the existing `crypto_buy_above_200_with_vol_gate` BTC rule, `crypto_buy_above_200_exit_below_200` ETH rule, and fixed crypto research cost assumptions (`crypto_taker_fee_bps=10`, `crypto_spread_bps=5`, `crypto_slippage_bps=10`). LTC remains paused/not active. These streams are for research portfolio testing only and do not approve crypto execution, preview promotion, paper execution, scheduling, shorting, margin, leverage, or any Alpaca/order path.

```text
python bot.py --crypto-return-streams
python bot.py --show-crypto-return-streams
```

Outputs:

```text
data/crypto_return_streams.csv
data/crypto_return_stream_metrics.csv
data/crypto_return_stream_summary.csv
data/crypto_return_stream_blockers.csv
```

The expected status is `crypto_return_streams_created_research_only` when BTC, ETH, and the combined BTC/ETH research sleeve have usable daily rows. If market data is unavailable, the report labels the data gap instead of inventing returns. Crypto remains research-only and `execution_approved=false`.

QQQ100 stream reconciliation mode is a research-only checkpoint for comparing the generated `qqq_100_trend_gate` daily stream against the saved QQQ100 benchmark metrics. It tests the current saved generated stream, close/adjusted-close availability, same-day versus next-day signal timing, SMA100 warmup/date-alignment behaviour, cash/flat handling, and missing cost/slippage assumptions. It also includes one fixed recovered-inputs reconstruction candidate, `qqq100_recovered_inputs_sma200_close_to_close_10bps`, based on the documented QQQ 10-year daily, `auto_adjust=True`, SMA200, prior-close signal, next-bar close-to-close return, zero-cash, 10 bps cost assumptions. It applies fixed metric-gap thresholds before any candidate can be called close enough for research review. If a material CAGR, Sharpe, MaxDD, or Calmar gap remains, the report stays blocked/manual-review and does not update `--sleeve-return-streams`.

```text
python bot.py --qqq100-stream-reconciliation
python bot.py --show-qqq100-stream-reconciliation
```

Outputs:

```text
data/qqq100_stream_reconciliation.csv
data/qqq100_stream_reconciliation_candidates.csv
data/qqq100_stream_reconciliation_diagnostics.csv
data/qqq100_stream_reconciliation_blockers.csv
data/qqq100_stream_reconciliation_summary.csv
data/qqq100_recovered_reference_stream.csv
data/qqq100_recovered_reference_metrics.csv
```

This reconciliation is research/report-only. When the recovered-inputs candidate passes all fixed research-review thresholds, the command writes `data/qqq100_recovered_reference_stream.csv` and `data/qqq100_recovered_reference_metrics.csv` as a preferred research reference for multi-sleeve reports. When it does not pass, those files are refreshed as unavailable/blocked audit outputs so stale recovered-reference rows cannot be reused silently. Current saved outputs remain blocked as `qqq100_reconstruction_attempt_still_blocked` or `qqq100_reconciliation_still_blocked` while the generated or reconstructed QQQ100 stream trails the saved benchmark materially, price data is unavailable, or the original benchmark source stream/parameters remain unknown. QQQ100 remains the only active paper sleeve, repeat execution approval remains false, follow-up order approval remains false, scheduling approval remains false, and general execution approval remains false.

QQQ100 benchmark-input reconstruction is a saved-output/report-only checkpoint for documenting the likely source chain behind the saved `qqq_100_trend_gate` metrics (`CAGR=16.8429`, `Sharpe=1.0027`, `MaxDD=-23.4576`, `Calmar=0.718`) before any generated stream is changed.

```text
python bot.py --qqq100-benchmark-inputs-report
python bot.py --show-qqq100-benchmark-inputs
```

Outputs:

```text
data/qqq100_benchmark_inputs_report.csv
data/qqq100_benchmark_inputs_summary.csv
data/qqq100_benchmark_input_gaps.csv
```

The report currently labels the source as `source_partially_recovered`: tracked history points to the QQQ leverage validation path using QQQ daily data, a 10-year yfinance window, `auto_adjust=True`, a 200-day trend gate, prior-close signal timing, next-bar close-to-close returns, zero-return cash days, and 10 bps exposure-change cost. The original daily stream and exact yfinance snapshot/date range remain missing, so this report must not be used to force the generated QQQ100 stream to match the saved benchmark. It remains research-only with execution, paper execution, scheduling, and live-trading approval false.

Multi-sleeve portfolio backtest mode is a saved-output-only research checkpoint for testing portfolio combinations conceptually before any new preview/action/execution wiring. It keeps saved QQQ100 benchmark metrics separate from the old generated QQQ100 diagnostic stream and, when valid, uses `data/qqq100_recovered_reference_stream.csv` as the preferred generated QQQ100 research reference. It then defines QQQ100-only, QQQ100-plus-cash, QQQ100-plus-SPY-SMA200 defensive gate, QQQ100-plus-rolling-drawdown defensive gate, QQQ100-plus-combined defensive gate, Codex defensive QQQ research, high-growth, crypto, QQQ100-plus-high-growth-plus-crypto, balanced multi-sleeve, and Codex ambitious allocation candidates. When `data/sleeve_return_streams.csv` contains defensive and Codex streams, `data/high_growth_return_streams.csv` contains the high-growth stream, and `data/crypto_return_streams.csv` contains the combined BTC/ETH research stream, those candidates are consumed; otherwise missing daily return streams remain labelled explicitly. It does not fetch market data, call Alpaca, read live positions, create/submit/cancel/replace orders, write SQLite `trade_log`, send alerts, schedule anything, expand QQQ100 execution, add repeat execution, or wire any sleeve to execution.

```text
python bot.py --multi-sleeve-portfolio-backtest
python bot.py --show-multi-sleeve-portfolio-backtest
```

Outputs:

```text
data/multi_sleeve_portfolio_backtest.csv
data/multi_sleeve_portfolio_backtest_sleeves.csv
data/multi_sleeve_portfolio_backtest_allocations.csv
data/multi_sleeve_portfolio_backtest_rankings.csv
data/multi_sleeve_portfolio_backtest_splits.csv
data/multi_sleeve_portfolio_backtest_trades.csv
data/multi_sleeve_portfolio_backtest_blockers.csv
data/multi_sleeve_portfolio_backtest_summary.csv
```

The expected status is `multi_sleeve_candidate_needs_more_data` until saved daily return streams, split metrics, and trade/turnover streams exist. `qqq100_core_trend_sleeve` remains the only active paper sleeve, high-growth and crypto remain research-only, and all execution, follow-up, repeat, scheduling, and live-trading approval flags remain false.

Multi-sleeve robustness mode is the saved-output-only split validation checkpoint for `qqq100_plus_high_growth_research`. It reads saved QQQ100, high-growth, cash, and multi-sleeve backtest CSVs only, then tests fixed `split_60_40`, `split_70_30`, and `split_80_20` chronological out-of-sample windows against the preferred QQQ100 research reference, using the recovered reference when valid and retaining the old generated QQQ100 stream as diagnostic-only context. It does not refresh yfinance data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or label the candidate promotion-ready.

```text
python bot.py --multi-sleeve-robustness
python bot.py --show-multi-sleeve-robustness
```

Outputs:

```text
data/multi_sleeve_robustness_report.csv
data/multi_sleeve_robustness_summary.csv
```

The expected blocker is `multi_sleeve_robustness_blocked_qqq100_reconciliation` until a preferred QQQ100 reference is valid in the saved inputs. The report is research-only and keeps execution and scheduling approval false.

Multi-sleeve crypto review mode is the saved-output-only split, cost, and volatility checkpoint for `qqq100_plus_high_growth_plus_crypto_research`. It reads saved QQQ100 recovered-reference, high-growth, BTC/ETH crypto, cash, and multi-sleeve backtest CSVs only, then compares the crypto-inclusive candidate, `qqq100_plus_high_growth_research`, the recovered QQQ100 reference, and the crypto sleeve across fixed `split_60_40`, `split_70_30`, and `split_80_20` windows. It also applies fixed additional crypto turnover cost stresses of 0, 10, 25, 50, and 100 bps using saved crypto exposure-change state, and records crypto volatility/drawdown contribution. This is research-only: it does not refresh yfinance data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or label the candidate promotion-ready.

```bash
python bot.py --multi-sleeve-crypto-review
python bot.py --show-multi-sleeve-crypto-review
```

Outputs:

```text
data/multi_sleeve_crypto_review.csv
data/multi_sleeve_crypto_review_summary.csv
data/multi_sleeve_crypto_review_cost_stress.csv
data/multi_sleeve_crypto_review_split_robustness.csv
data/multi_sleeve_crypto_review_volatility.csv
```

Multi-sleeve crypto containment review mode is the saved-output-only follow-up for the 5% crypto sleeve inside the current `higher_growth_70_20_5_5` multi-sleeve research lead. It reads saved crypto return streams, saved crypto review rows, weight sensitivity, lead state, high-growth drawdown decomposition, and portfolio backtest context only. It asks whether 5% crypto exposure is contained enough, whether crypto materially worsened the lead's worst drawdown, whether no-crypto or higher-crypto nearby weights look better, and whether standalone BTC/ETH/combined crypto drawdowns require a blocker before any further candidate label change. It does not add strategies, optimise weights, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

```bash
python bot.py --multi-sleeve-crypto-containment-review
python bot.py --show-multi-sleeve-crypto-containment-review
```

Outputs:

```text
data/multi_sleeve_crypto_containment_review.csv
data/multi_sleeve_crypto_containment_summary.csv
data/multi_sleeve_crypto_containment_drawdowns.csv
data/multi_sleeve_crypto_containment_blockers.csv
```

Multi-sleeve allocation policy review mode is the saved-output-only allocation checkpoint for the current 75% QQQ100, 15% high-growth, 5% crypto, and 5% defensive cash/bond candidate. It reads saved multi-sleeve backtest, crypto review, high-growth, crypto, and recovered QQQ100 metrics only, then reviews component roles, concentration, small-sleeve sensitivity, blockers, and the next fixed weight-sensitivity step. It does not refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or label the candidate promotion-ready.

```bash
python bot.py --multi-sleeve-allocation-policy-review
python bot.py --show-multi-sleeve-allocation-policy-review
```

Outputs:

```text
data/multi_sleeve_allocation_policy_review.csv
data/multi_sleeve_allocation_policy_summary.csv
data/multi_sleeve_allocation_policy_components.csv
data/multi_sleeve_allocation_policy_blockers.csv
```

Multi-sleeve weight sensitivity mode is the saved-output-only fixed nearby-weight review for the current 75/15/5/5 crypto-inclusive candidate. It reads saved QQQ100 recovered-reference, high-growth, and crypto daily streams only, then tests the fixed variants `current_75_15_5_5`, `lower_crypto_77_15_3_5`, `no_crypto_80_15_0_5`, `lower_growth_80_10_5_5`, `balanced_lower_risk_85_10_0_5`, `higher_crypto_73_15_7_5`, and `higher_growth_70_20_5_5`. It does not optimise, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or label the candidate promotion-ready.

```bash
python bot.py --multi-sleeve-weight-sensitivity
python bot.py --show-multi-sleeve-weight-sensitivity
```

Outputs:

```text
data/multi_sleeve_weight_sensitivity.csv
data/multi_sleeve_weight_sensitivity_summary.csv
data/multi_sleeve_weight_sensitivity_blockers.csv
```

Multi-sleeve higher-growth review mode is the saved-output-only challenger review for `higher_growth_70_20_5_5` versus `current_75_15_5_5`. It reads saved QQQ100 recovered-reference, high-growth, and crypto daily streams only, then compares headline metrics, fixed 60/40, 70/30, and 80/20 splits, fixed high-growth turnover cost stresses, drawdown windows, and approximate sleeve contribution deltas. It does not optimise, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or label the candidate promotion-ready.

```bash
python bot.py --multi-sleeve-higher-growth-review
python bot.py --show-multi-sleeve-higher-growth-review
```

Outputs:

```text
data/multi_sleeve_higher_growth_review.csv
data/multi_sleeve_higher_growth_summary.csv
data/multi_sleeve_higher_growth_split_review.csv
data/multi_sleeve_higher_growth_cost_review.csv
data/multi_sleeve_higher_growth_drawdown_review.csv
data/multi_sleeve_higher_growth_blockers.csv
```

Multi-sleeve research lead decision mode is the saved-output-only decision checkpoint for whether `higher_growth_70_20_5_5` should replace `current_75_15_5_5` as the current research lead candidate. It reads saved higher-growth review, split, cost, drawdown, weight-sensitivity, allocation-policy, crypto-review, and portfolio context only, then applies fixed cautious rules around CAGR, Sharpe, Calmar, MaxDD, split wins, cost stress, and false execution/scheduling flags. It does not optimise, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or label the candidate promotion-ready.

```bash
python bot.py --multi-sleeve-research-lead-decision
python bot.py --show-multi-sleeve-research-lead-decision
```

Outputs:

```text
data/multi_sleeve_research_lead_decision.csv
data/multi_sleeve_research_lead_summary.csv
data/multi_sleeve_research_lead_blockers.csv
```

Multi-sleeve lead-state refresh mode is the saved-output-only canonical state layer for future multi-sleeve research displays. It reads the saved research-lead decision and adjacent saved review context only, then writes the selected research lead candidate, previous baseline, copied metrics/deltas, blockers, and false safety flags into one compact state file. It does not add a strategy, rerun backtests, optimise, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

```bash
python bot.py --multi-sleeve-lead-state-refresh
python bot.py --show-multi-sleeve-lead-state
```

Outputs:

```text
data/multi_sleeve_lead_state.csv
data/multi_sleeve_lead_state_summary.csv
data/multi_sleeve_lead_state_blockers.csv
```

Multi-sleeve high-growth drawdown decomposition mode is the saved-output-only blocker review for the selected `higher_growth_70_20_5_5` research lead candidate. It reads the saved lead state, research-lead decision, higher-growth review rows, and saved QQQ100/high-growth/crypto return streams only, then reconstructs current versus higher-growth drawdown windows, same-window sleeve contributions, incremental high-growth risk, and recovery/bounce-back context. It does not add strategies, rerun backtests, optimise weights, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

```bash
python bot.py --multi-sleeve-high-growth-drawdown-decomposition
python bot.py --show-multi-sleeve-high-growth-drawdown-decomposition
```

Outputs:

```text
data/multi_sleeve_high_growth_drawdown_decomposition.csv
data/multi_sleeve_high_growth_drawdown_summary.csv
data/multi_sleeve_high_growth_drawdown_periods.csv
data/multi_sleeve_high_growth_drawdown_blockers.csv
```

High-growth sleeve quality review mode is the saved-output-only quality checkpoint for the selected high-growth sleeve inside the current multi-sleeve research lead candidate. It reads saved high-growth return streams, lead-state context, drawdown decomposition, weight-sensitivity, and adjacent multi-sleeve review outputs only, then reviews the standalone high-growth sleeve metrics, fixed split stability, worst drawdown/recovery, contribution to `higher_growth_70_20_5_5`, and whether ticker-level concentration data is available. It does not add strategies, rerun backtests from market data, optimise weights, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

```bash
python bot.py --high-growth-sleeve-quality-review
python bot.py --show-high-growth-sleeve-quality-review
```

Outputs:

```text
data/high_growth_sleeve_quality_review.csv
data/high_growth_sleeve_quality_summary.csv
data/high_growth_sleeve_quality_splits.csv
data/high_growth_sleeve_quality_drawdowns.csv
data/high_growth_sleeve_quality_blockers.csv
```

High-growth component attribution mode is the saved-output-only readiness layer for the concentration blocker found by the high-growth sleeve quality review. It inspects existing saved high-growth outputs for real component ticker identifiers, holding dates, weights, component daily returns, weighted contributions, and drawdown-window contribution data. If those fields exist, it writes component attribution rows; if they do not, it writes blocker rows explaining that a future component-stream builder is needed. It does not invent ticker attribution, refresh market data, call yfinance, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or connect research to execution.

```bash
python bot.py --high-growth-component-attribution
python bot.py --show-high-growth-component-attribution
```

Outputs:

```text
data/high_growth_component_attribution.csv
data/high_growth_component_attribution_summary.csv
data/high_growth_component_attribution_blockers.csv
```

If real component data exists, it may also write:

```text
data/high_growth_component_contributions.csv
data/high_growth_component_drawdown_contributions.csv
```

High-growth component streams mode is that dedicated research-only component-stream builder. It reuses the existing high-growth return-stream price loader and `codex_broad_growth_balanced_breakout_control` drawdown-control simulation to reconstruct daily component ticker rows, weights, returns, and weighted contributions where the existing simulation exposes holdings. If market data or reconstructable holdings are unavailable, it writes blocked outputs instead of fake ticker rows. It may use the same safe research market-data pattern as the high-growth return-stream command, but it does not call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, optimise the sleeve, add variants, or connect research to execution.

```bash
python bot.py --high-growth-component-streams
python bot.py --show-high-growth-component-streams
```

Outputs:

```text
data/high_growth_component_streams.csv
data/high_growth_component_streams_summary.csv
data/high_growth_component_streams_blockers.csv
data/high_growth_component_drawdown_contributions.csv
```

High-growth sleeve concentration review mode is the saved-output-only manual-review checkpoint that uses `data/high_growth_component_streams.csv` to review whether `codex_broad_growth_balanced_breakout_control` is too dependent on a few tickers inside the `higher_growth_70_20_5_5` research lead. It reports headline active-component counts, top/bottom ticker contributions, top 1/3/5/10 dependency shares, Herfindahl concentration, and worst-drawdown component contribution context. It does not refresh yfinance data, add strategies, optimise weights, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

```bash
python bot.py --high-growth-sleeve-concentration-review
python bot.py --show-high-growth-sleeve-concentration-review
```

Outputs:

```text
data/high_growth_sleeve_concentration_review.csv
data/high_growth_sleeve_concentration_summary.csv
data/high_growth_sleeve_concentration_top_contributors.csv
data/high_growth_sleeve_concentration_drawdown.csv
data/high_growth_sleeve_concentration_blockers.csv
```

High-growth research checkpoint mode is the saved-output-only consolidator for the completed high-growth chain. It reads saved multi-sleeve lead state, weight sensitivity, high-growth drawdown decomposition, high-growth sleeve quality, component attribution, component stream summary, sleeve concentration review, and optional crypto containment context, then writes a compact checkpoint row plus blockers. It does not rerun market data, call yfinance, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

```bash
python bot.py --high-growth-research-checkpoint
python bot.py --show-high-growth-research-checkpoint
```

Outputs:

```text
data/high_growth_research_checkpoint.csv
data/high_growth_research_checkpoint_blockers.csv
```

Paper execution state summary mode records the saved milestone state after the AAPL smoke test and QQQ100 manual paper execution. It reads saved CSV outputs only, including the AAPL smoke-test postcheck, QQQ100 paper execution result or QQQ100 paper postcheck, QQQ100 action preview, QQQ100 signal, readiness, connectivity, execution-eligibility, portfolio-preview, and portfolio-risk context where present. It does not call Alpaca, read paper positions live, refresh yfinance, create/submit/cancel/replace orders, write SQLite `trade_log`, send Discord or Telegram alerts, change config defaults, schedule anything, or approve follow-up/repeat execution.

Command:

```text
python bot.py --paper-execution-state-summary
```

Saved display:

```text
python bot.py --show-paper-execution-state-summary
```

Outputs:

```text
data/paper_execution_state_summary.csv
data/paper_execution_state_positions.csv
data/paper_execution_state_milestones.csv
data/paper_execution_state_blockers.csv
```

The report can label historical milestones such as `aapl_smoke_test_filled_confirmed`, `qqq100_manual_paper_execution_filled_confirmed`, and `qqq100_aligned_long_confirmed` from saved evidence. Current approvals remain false: `execution_approved=false`, `general_execution_approved=false`, `qqq100_execution_approved=false`, `followup_order_approved=false`, `repeat_execution_approved=false`, and `scheduling_approved=false`.

High-growth stock lab mode tests a fixed high-risk, high-return individual-stock universe only: `AAPL`, `MSFT`, `NVDA`, `AMZN`, `META`, `GOOGL`, `AVGO`, `AMD`, `TSLA`, and `NFLX`. SPY and QQQ are allowed only as benchmark/regime references, not as traded holdings. The lab compares fixed monthly concentrated momentum variants, including top 1/top 2/top 3 composite 63/126/252-day momentum with own SMA200 and QQQ/SPY SMA200 regime gates, plus `codex_high_conviction_growth_persistence`, `codex_growth_drawdown_reentry`, `codex_high_growth_breakout_acceleration`, and `codex_high_growth_crash_rebound_leader`. The two Codex high-growth variants are fixed-rule ambitious stock-only candidates: one looks for breakout acceleration near 52-week highs, and one looks for crash-rebound leaders after recovery confirmation. This is research-only and deliberately flags concentration risk, survivorship bias, single-name event risk, stock-specific gap risk, cost/split sensitivity, and drawdown risk. It may use yfinance daily data through the research path, but it does not call Alpaca, load config, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve execution, or connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --high-growth-stock-lab
```

Saved display:

```text
python bot.py --show-high-growth-stock-lab
```

Outputs:

```text
data/high_growth_stock_lab.csv
data/high_growth_stock_lab_summary.csv
data/high_growth_stock_lab_trades.csv
data/high_growth_stock_lab_costs.csv
data/high_growth_stock_lab_splits.csv
data/high_growth_stock_lab_drawdowns.csv
data/high_growth_stock_lab_concentration.csv
```

High-growth stock universe expansion mode tests whether the concentrated high-growth stock momentum result survives broader fixed current-constituent universes. It compares `mega_cap_growth_10`, `expanded_growth_30`, and `broad_liquid_growth_50` using individual stocks only; SPY and QQQ remain benchmark/regime references only. The report keeps the same research-only boundary as the high-growth stock lab, explicitly flags survivorship bias and concentration risk, asks whether the edge improves or decays with breadth, and does not approve execution or connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --high-growth-stock-universe-expansion-report
```

Saved display:

```text
python bot.py --show-high-growth-stock-universe-expansion-report
```

Outputs:

```text
data/high_growth_stock_universe_expansion_report.csv
data/high_growth_stock_universe_expansion_summary.csv
data/high_growth_stock_universe_expansion_trades.csv
data/high_growth_stock_universe_expansion_costs.csv
data/high_growth_stock_universe_expansion_splits.csv
data/high_growth_stock_universe_expansion_drawdowns.csv
data/high_growth_stock_universe_expansion_concentration.csv
```

High-growth stock drawdown-control mode is the fixed follow-up for the broad 50-stock high-growth result. It tests `broad_growth_top2_reference`, `broad_growth_top3_reference`, `broad_growth_top1_drawdown_brake`, `broad_growth_top1_volatility_gate`, `broad_growth_top1_cooldown_after_crash`, and `codex_broad_growth_balanced_breakout_control` against the saved broad Top1 reference and `qqq_100_trend_gate`. This is research-only, keeps QQQ/SPY as benchmark/regime references only, flags survivorship bias, concentration risk, outlier dependence, split/cost sensitivity, and drawdown risk, and does not approve execution or connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --high-growth-stock-drawdown-control-report
```

Saved display:

```text
python bot.py --show-high-growth-stock-drawdown-control-report
```

Outputs:

```text
data/high_growth_stock_drawdown_control_report.csv
data/high_growth_stock_drawdown_control_summary.csv
data/high_growth_stock_drawdown_control_trades.csv
data/high_growth_stock_drawdown_control_costs.csv
data/high_growth_stock_drawdown_control_splits.csv
data/high_growth_stock_drawdown_control_drawdowns.csv
data/high_growth_stock_drawdown_control_concentration.csv
```

High-growth stock lead decision mode is a saved-output checkpoint that compares the clean `qqq_100_trend_gate` lead, `codex_qqq_adaptive_trend_exposure`, the small-universe high-growth Top3 baseline, the rejected broad Top1 extreme-drawdown reference, and `codex_broad_growth_balanced_breakout_control`. It does not refresh market data. The intended research label is that `qqq_100_trend_gate` remains the clean main stock/ETF lead while `codex_broad_growth_balanced_breakout_control` becomes the high-risk stock research lead candidate. This is saved-output research-only, does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --high-growth-stock-lead-decision-report
```

Saved display:

```text
python bot.py --show-high-growth-stock-lead-decision-report
```

Outputs:

```text
data/high_growth_stock_lead_decision_report.csv
data/high_growth_stock_lead_decision_summary.csv
data/high_growth_stock_lead_decision_evidence.csv
data/high_growth_stock_lead_decision_blockers.csv
```

High-growth stock manual review pack mode is the saved-output checkpoint for reviewing `codex_broad_growth_balanced_breakout_control` as the high-risk stock research lead candidate while keeping `qqq_100_trend_gate` as the clean main stock/ETF lead. It explains why the broad Top1 reference remains rejected, why the branch is still research-only, and what blocks preview-candidate and paper-execution discussion. It does not refresh market data, does not approve execution, and does not connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --high-growth-stock-manual-review-pack
```

Saved display:

```text
python bot.py --show-high-growth-stock-manual-review-pack
```

Outputs:

```text
data/high_growth_stock_manual_review_pack.csv
data/high_growth_stock_manual_review_summary.csv
data/high_growth_stock_manual_review_evidence.csv
data/high_growth_stock_manual_review_blockers.csv
```

High-growth stock risk review pack mode is the saved-output blocker review for `codex_broad_growth_balanced_breakout_control`. It focuses on cost sensitivity, split sensitivity, concentration risk, outlier dependence, survivorship/current-constituent bias, drawdown severity, drawdown improvement versus broad Top1, and drawdown worsening versus `qqq_100_trend_gate`. It keeps `qqq_100_trend_gate` as the clean main lead, keeps broad Top1 rejected, keeps the high-growth branch research-only, and does not approve preview promotion or execution.

Command:

```text
python bot.py --high-growth-stock-risk-review-pack
```

Saved display:

```text
python bot.py --show-high-growth-stock-risk-review-pack
```

Outputs:

```text
data/high_growth_stock_risk_review_pack.csv
data/high_growth_stock_risk_review_summary.csv
data/high_growth_stock_risk_review_evidence.csv
data/high_growth_stock_risk_review_blockers.csv
```

High-growth stock risk evidence review mode is the saved-output evidence checkpoint after the blocker review. It reads saved high-growth and QQQ research CSVs only, summarises return improvement versus `qqq_100_trend_gate`, drawdown worsening versus `qqq_100_trend_gate`, drawdown improvement versus the rejected broad Top1 reference, Calmar/Sharpe tradeoff, cost evidence, split evidence, concentration evidence, outlier dependence, and survivorship/current-constituent bias. It keeps `qqq_100_trend_gate` as the clean main lead, keeps `codex_broad_growth_balanced_breakout_control` high-risk research-only, keeps broad Top1 rejected, and does not approve execution, preview promotion, paper execution, or scheduling.

Command:

```text
python bot.py --high-growth-stock-risk-evidence-review
```

Saved display:

```text
python bot.py --show-high-growth-stock-risk-evidence-review
```

Outputs:

```text
data/high_growth_stock_risk_evidence_review.csv
data/high_growth_stock_risk_evidence_summary.csv
data/high_growth_stock_risk_evidence_details.csv
data/high_growth_stock_risk_evidence_blockers.csv
```

High-growth stock branch decision checkpoint mode is the saved-output decision layer after the risk evidence review. It converts saved evidence into a conservative branch decision: continue research-only, pause due to drawdown, require a final validation pack before preview discussion, or mark saved evidence insufficient. It keeps `qqq_100_trend_gate` as the clean main stock/ETF lead, keeps `broad_liquid_growth_50:concentrated_growth_momentum_top1` rejected as the extreme drawdown reference, keeps `codex_broad_growth_balanced_breakout_control` high-risk research-only unless paused, and does not approve execution, preview promotion, paper execution, or scheduling.

Command:

```text
python bot.py --high-growth-stock-branch-decision-checkpoint
```

Saved display:

```text
python bot.py --show-high-growth-stock-branch-decision-checkpoint
```

Outputs:

```text
data/high_growth_stock_branch_decision_checkpoint.csv
data/high_growth_stock_branch_decision_summary.csv
data/high_growth_stock_branch_decision_evidence.csv
data/high_growth_stock_branch_decision_blockers.csv
```

High-growth stock final validation pack mode is the saved-output validation checkpoint before any manual preview-candidate discussion. It reads saved high-growth branch-decision, risk-evidence, risk-review, manual-review, lead-decision, lab, universe-expansion, drawdown-control, QQQ, and project research-state CSVs where present. It checks return improvement versus `qqq_100_trend_gate`, drawdown worsening versus `qqq_100_trend_gate`, drawdown improvement versus broad Top1, Calmar/Sharpe tradeoff, cost sensitivity, split sensitivity, concentration risk, outlier dependence, survivorship/current-constituent bias, whether high drawdown is compensated by enough return/risk improvement, and whether the branch has a clear portfolio role separate from `qqq_100_trend_gate`. It does not approve execution, preview promotion, paper execution, or scheduling.

Command:

```text
python bot.py --high-growth-stock-final-validation-pack
```

Saved display:

```text
python bot.py --show-high-growth-stock-final-validation-pack
```

Outputs:

```text
data/high_growth_stock_final_validation_pack.csv
data/high_growth_stock_final_validation_summary.csv
data/high_growth_stock_final_validation_evidence.csv
data/high_growth_stock_final_validation_blockers.csv
```

Crypto research preview mode starts the crypto phase as a scaffold only. It writes the current research universe (`BTC/USD`, `ETH/USD`, `LTC/USD`) with execution, shorting, margin, and execution approval all disabled. It does not refresh data, call Alpaca, read positions, submit or cancel orders, write SQLite `trade_log`, or send Discord alerts.

Output:

```text
data/crypto_research_preview.csv
```

Crypto universe readiness mode expands the crypto research universe before any new strategy design. It uses yfinance-compatible daily symbols (`BTC-USD`, `ETH-USD`, `SOL-USD`, `BNB-USD`, `XRP-USD`, `ADA-USD`, `AVAX-USD`, `LINK-USD`, `DOT-USD`, `LTC-USD`, `BCH-USD`, `DOGE-USD`, `TRX-USD`, `ATOM-USD`, `POL-USD`, and `MATIC-USD`) and classifies data quality, history length, volatility, drawdown, momentum, and POL/MATIC transition risk. It is research/report-only, does not add a crypto strategy yet, and does not approve crypto execution.

Command:

```text
python bot.py --crypto-universe-readiness-report
```

Optional saved display:

```text
python bot.py --show-crypto-universe-readiness-report
```

Outputs:

```text
data/crypto_universe_readiness_report.csv
data/crypto_universe_readiness_summary.csv
```

Expanded crypto strategy lab mode tests expanded-universe strategy candidates using symbols marked eligible by the saved crypto universe readiness report where possible. It excludes `POL-USD` and `MATIC-USD` until a separate transition review approves one of them. The lab includes the planned `crypto_risk_on_momentum_persistence` strategy and one Codex-designed fixed-rule candidate, `codex_ambitious_crypto_btc_eth_core_alt_accelerator`, plus BTC, ETH, BTC/ETH 50/50, equal-weight eligible-crypto, and cash benchmarks. It includes fixed cost stress and fixed split validation. This is research/report-only and does not approve crypto execution or connect crypto to Alpaca or paper orders.

Command:

```text
python bot.py --expanded-crypto-strategy-lab
```

Optional saved display:

```text
python bot.py --show-expanded-crypto-strategy-lab
```

Outputs:

```text
data/expanded_crypto_strategy_lab.csv
data/expanded_crypto_strategy_lab_summary.csv
data/expanded_crypto_strategy_lab_trades.csv
data/expanded_crypto_strategy_lab_equity_curves.csv
data/expanded_crypto_strategy_lab_costs.csv
data/expanded_crypto_strategy_lab_splits.csv
```

Expanded crypto robustness mode challenges whether the static equal-weight eligible-crypto benchmark is robust or hindsight-biased. It checks inception-aware equal weight, BTC/ETH core-only equal weight, major-crypto-only equal weight, outlier exclusion, fixed splits, fixed cost stress, drawdown context, and asset contribution estimates. It compares `equal_weight_eligible_crypto_benchmark`, `crypto_risk_on_momentum_persistence`, `codex_ambitious_crypto_btc_eth_core_alt_accelerator`, BTC buy-and-hold, ETH buy-and-hold, BTC/ETH 50/50, and cash. It excludes `POL-USD` and `MATIC-USD` until transition review. This is research/report-only and does not approve crypto execution or connect crypto to Alpaca or paper orders.

Command:

```text
python bot.py --expanded-crypto-robustness-report
```

Optional saved display:

```text
python bot.py --show-expanded-crypto-robustness-report
```

Outputs:

```text
data/expanded_crypto_robustness_report.csv
data/expanded_crypto_robustness_summary.csv
data/expanded_crypto_robustness_splits.csv
data/expanded_crypto_robustness_costs.csv
data/expanded_crypto_robustness_drawdowns.csv
data/expanded_crypto_asset_contribution.csv
data/expanded_crypto_equal_weight_reality_check.csv
```

Crypto equal-weight crash-gate mode tests whether the robust static equal-weight eligible-crypto benchmark can keep much of its return while reducing catastrophic drawdown. It uses the saved eligible crypto universe where possible, continues to exclude `POL-USD` and `MATIC-USD` until transition review, and compares `equal_weight_eligible_crypto_benchmark`, `equal_weight_inception_aware`, `crypto_equal_weight_trend_crash_gate`, `crypto_equal_weight_btc_trend_gate`, `crypto_equal_weight_breadth_gate`, `crypto_equal_weight_drawdown_brake`, `crypto_risk_on_momentum_persistence`, `codex_ambitious_crypto_btc_eth_core_alt_accelerator`, BTC buy-and-hold, ETH buy-and-hold, BTC/ETH 50/50 monthly, and cash. This is research/report-only and does not approve crypto execution or connect crypto to Alpaca or paper orders.

Command:

```text
python bot.py --crypto-equal-weight-crash-gate
```

Optional saved display:

```text
python bot.py --show-crypto-equal-weight-crash-gate
```

Outputs:

```text
data/crypto_equal_weight_crash_gate.csv
data/crypto_equal_weight_crash_gate_summary.csv
data/crypto_equal_weight_crash_gate_trades.csv
data/crypto_equal_weight_crash_gate_equity_curves.csv
data/crypto_equal_weight_crash_gate_costs.csv
data/crypto_equal_weight_crash_gate_splits.csv
data/crypto_equal_weight_crash_gate_drawdowns.csv
```

Crypto equal-weight volatility-scaling mode is the next research-only follow-up after the hard crash-gate result showed too much return drag. It tests whether partial volatility/drawdown exposure scaling can improve equal-weight crypto's catastrophic drawdown without destroying returns. It includes fixed planned scalers (`crypto_equal_weight_volatility_scaled_allocator`, `crypto_equal_weight_drawdown_scaled_allocator`, and `crypto_equal_weight_combined_vol_drawdown_scaler`) plus one Codex-designed fixed-rule risk-control idea, `codex_ambitious_crypto_core_alt_volatility_throttle`, which uses a BTC/ETH core, capped alt sleeve, and volatility/drawdown/breadth throttles while staying long-only and no-leverage. It uses the saved eligible crypto universe where possible, continues to exclude `POL-USD` and `MATIC-USD` until transition review, and compares static equal weight, inception-aware equal weight, existing crypto candidates, BTC/ETH benchmarks, BTC/ETH 50/50, and cash. This is research/report-only and does not approve crypto execution or connect crypto to Alpaca or paper orders.

Command:

```text
python bot.py --crypto-equal-weight-volatility-scaling
```

Optional saved display:

```text
python bot.py --show-crypto-equal-weight-volatility-scaling
```

Outputs:

```text
data/crypto_equal_weight_volatility_scaling.csv
data/crypto_equal_weight_volatility_scaling_summary.csv
data/crypto_equal_weight_volatility_scaling_trades.csv
data/crypto_equal_weight_volatility_scaling_equity_curves.csv
data/crypto_equal_weight_volatility_scaling_costs.csv
data/crypto_equal_weight_volatility_scaling_splits.csv
data/crypto_equal_weight_volatility_scaling_drawdowns.csv
```

Crypto equal-weight capped-risk mode tests capped/equal-risk crypto allocation and outlier-dependence diagnostics after crash gates and volatility scaling did not meaningfully solve catastrophic drawdown. It keeps broad crypto exposure but tests fixed allocation variants: 10% and 15% capped equal weight, excluding the two highest-volatility assets, excluding the saved top-contributor pair (`BNB-USD` and `TRX-USD`), inverse-volatility weighting, and a simple equal-risk contribution proxy. It writes contribution diagnostics for ending weight, average weight, approximate return contribution, top contributors, Herfindahl concentration, max single-asset average weight, and top-contributor dependence. This is research/report-only and does not approve crypto execution or connect crypto to Alpaca or paper orders.

Command:

```text
python bot.py --crypto-equal-weight-capped-risk-report
```

Optional saved display:

```text
python bot.py --show-crypto-equal-weight-capped-risk-report
```

Outputs:

```text
data/crypto_equal_weight_capped_risk_report.csv
data/crypto_equal_weight_capped_risk_summary.csv
data/crypto_equal_weight_capped_risk_trades.csv
data/crypto_equal_weight_capped_risk_equity_curves.csv
data/crypto_equal_weight_capped_risk_costs.csv
data/crypto_equal_weight_capped_risk_splits.csv
data/crypto_equal_weight_capped_risk_drawdowns.csv
data/crypto_equal_weight_capped_risk_contributions.csv
```

Expanded crypto lead-decision mode consolidates the expanded crypto research branch and decides the current crypto research lead as a research label only. It reads saved crypto universe, expanded strategy lab, equal-weight robustness, hard crash-gate, volatility-scaling, and capped-risk contribution outputs where available, then writes decision, summary, and evidence CSVs. Any selected crypto lead remains high-drawdown/manual-review-only; this does not approve crypto execution or connect crypto to Alpaca or paper orders.

Command:

```text
python bot.py --expanded-crypto-lead-decision
```

Optional saved display:

```text
python bot.py --show-expanded-crypto-lead-decision
```

Outputs:

```text
data/expanded_crypto_lead_decision.csv
data/expanded_crypto_lead_decision_summary.csv
data/expanded_crypto_lead_decision_evidence.csv
```

Crypto lead split-sensitivity diagnosis mode is the saved-output follow-up for the current crypto research lead, `crypto_equal_weight_ex_highest_vol_2`. It reads saved crypto lead-decision, capped-risk, robustness, split, contribution, and universe-readiness CSVs where available, then writes a research/report-only diagnosis of split weakness, broad-market versus lead-specific decay, highest-volatility exclusion stability, and BNB-USD/TRX-USD or other top-contributor dependence. This does not approve crypto execution, paper execution, preview promotion, scheduling, order instructions, or strategy-to-execution wiring.

Command:

```text
python bot.py --crypto-lead-split-sensitivity-diagnosis
```

Optional saved display:

```text
python bot.py --show-crypto-lead-split-sensitivity-diagnosis
```

Outputs:

```text
data/crypto_lead_split_sensitivity_diagnosis.csv
data/crypto_lead_split_sensitivity_summary.csv
data/crypto_lead_split_sensitivity_periods.csv
data/crypto_lead_split_sensitivity_exclusions.csv
data/crypto_lead_split_sensitivity_contributions.csv
```

Expanded crypto manual review pack mode consolidates the current crypto research branch into a manual-review checkpoint for `crypto_equal_weight_ex_highest_vol_2`. It reads saved crypto universe, benchmark, risk-control, lead-decision, split-sensitivity, exclusion, and contribution CSVs where available, then writes a research/report-only manual review pack for the current crypto research lead. It summarises universe readiness, POL/MATIC transition blocks, equal-weight benchmark reality, current lead evidence, split sensitivity, exclusion-rule instability, outlier/top-contributor dependence, cost-review status, high-drawdown context, rejected hard crash gates, and downgraded volatility/drawdown throttles. This does not approve crypto execution, does not approve preview promotion, and does not connect crypto to Alpaca or paper orders; the current crypto research lead remains manual-review-only unless future review changes that.

Command:

```text
python bot.py --expanded-crypto-manual-review-pack
```

Optional saved display:

```text
python bot.py --show-expanded-crypto-manual-review-pack
```

Outputs:

```text
data/expanded_crypto_manual_review_pack.csv
data/expanded_crypto_manual_review_summary.csv
data/expanded_crypto_manual_review_evidence.csv
data/expanded_crypto_manual_review_blockers.csv
```

Project research state refresh mode consolidates the current stock/ETF and crypto research state into one saved checkpoint before choosing the next research/reporting direction. It reads saved research CSVs where available, then writes a research/report-only summary of the stock/ETF active research lead, crypto manual-review-only lead, blockers, rejected or downgraded branches, safety boundaries, and suggested next research options. It does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.

Command:

```text
python bot.py --project-research-state-refresh
```

Optional saved display:

```text
python bot.py --show-project-research-state-refresh
```

Outputs:

```text
data/project_research_state_refresh.csv
data/project_research_state_summary.csv
data/project_research_state_next_steps.csv
```

For quick terminal checks, use the compact saved-output-only current research state display helper:

```text
python bot.py --show-current-research-state
```

This reads saved CSV outputs for the current multi-sleeve research state, including QQQ100 recovered reference, high-growth return-stream metrics, crypto return-stream metrics, multi-sleeve portfolio backtest, multi-sleeve crypto review summaries, the canonical multi-sleeve lead state where available, and the high-growth drawdown decomposition where available. It shows the QQQ100 reference, high-growth sleeve, crypto sleeve, current multi-sleeve candidate, canonical research lead candidate, drawdown watch context, and safety state in one compact terminal view. It tolerates missing saved outputs as `missing_saved_output`, does not refresh market data, does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.

To check whether the saved project research state is fresh and internally usable, run:

```text
python bot.py --project-research-state-quality-report
```

This writes `data/project_research_state_quality_report.csv`. It reads saved project-state CSVs only, checks freshness, required fields, and false approval flags, and degrades to warning/blocker rows if files are missing or stale. It does not refresh market data, call Alpaca, read positions, load config, write SQLite `trade_log`, send alerts, approve scheduling, or approve execution.

To review whether the current stock/ETF research lead is ready even for a future manually reviewed paper-execution design discussion, run:

```text
python bot.py --stock-etf-paper-execution-readiness-report
```

This writes `data/stock_etf_paper_execution_readiness_report.csv`. It reads saved project/research/gate reports only and checks the current stock/ETF lead, cost-review blocker, split/drawdown context, preview readiness, execution eligibility, paper-execution protection, kill-switch, portfolio-risk prerequisites, broker boundary, crypto out-of-scope boundary, and scheduling boundary. The expected current interpretation remains conservative: `qqq_100_trend_gate` is the stock/ETF research lead, `codex_qqq_adaptive_trend_exposure` remains an ambitious alternative, `qqq_150_trend_gate` remains rejected as a high-drawdown reference, and no paper execution discussion is approved. This report does not read local credentials, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve paper execution.

To run an Alpaca paper readiness/preflight audit before any future manually confirmed paper smoke test discussion, use:

```text
python bot.py --alpaca-paper-readiness-report
```

This writes `data/alpaca_paper_readiness_report.csv`. Default mode is static and does not call Alpaca, read positions, submit/cancel/replace/create orders, write SQLite `trade_log`, send alerts, print config contents, or approve execution. A separate explicit read-only connectivity mode exists behind `--confirm-readonly-alpaca-check`; it may load local paper config and call only a read-only account/status endpoint, with identifiers and credentials redacted. Do not run the confirmed read-only mode until the static report has been reviewed.

To diagnose VPS network reachability to Alpaca API hosts without credentials or authenticated API calls, run:

```text
python bot.py --alpaca-connectivity-diagnostics
python bot.py --show-alpaca-connectivity-diagnostics
```

This writes `data/alpaca_connectivity_diagnostics.csv`, `data/alpaca_connectivity_diagnostics_summary.csv`, and `data/alpaca_connectivity_diagnostics_blockers.csv`. It performs DNS and raw TCP 443 checks only for `paper-api.alpaca.markets`, `api.alpaca.markets`, `alpaca.markets`, `github.com`, `google.com`, and `pypi.org`. It is intended for cases where the VPS cannot reach Alpaca API hosts while a laptop and normal HTTPS control sites work. It does not load config, use or print keys, call authenticated Alpaca endpoints, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve execution.

To review whether one tiny manually confirmed paper-order smoke test can even be discussed, run:

```text
python bot.py --paper-order-smoke-test-readiness-pack
```

This writes `data/paper_order_smoke_test_readiness_pack.csv`. It is saved-data/static/report-only: it summarises the saved Alpaca paper readiness report, stock/ETF execution-readiness context, project state, existing confirmation-gated smoke-test boundary, and saved kill-switch/protection reports where present. It may record a conservative future manual-review-only template such as AAPL buy 1, but it does not print a pasteable order command, call Alpaca, read positions, load config contents, create/submit/cancel/replace orders, write SQLite `trade_log`, send alerts, schedule anything, connect strategies to execution, or approve paper order execution.

To run a live read-only preflight shortly before discussing a future tiny manually confirmed paper-order smoke test, use default non-confirmed mode first:

```text
python bot.py --paper-order-smoke-test-live-preflight --ticker AAPL --side buy --quantity 1
```

This writes `data/paper_order_smoke_test_live_preflight.csv`. Default mode validates the proposed ticker, side, and quantity and reads saved readiness context only; it does not call Alpaca. A confirmed read-only mode exists behind `--confirm-readonly-alpaca-check` for account, clock, asset, and open-order status checks, but it still does not submit, create, cancel, replace, or preview executable orders. The terminal summary never prints a pasteable paper-order command and always keeps order execution, execution, scheduling, and run-now approval false.

After any future manually confirmed tiny paper-order smoke test, use the postcheck report:

```text
python bot.py --paper-order-smoke-test-postcheck --ticker AAPL --side buy --quantity 1
```

This writes `data/paper_order_smoke_test_postcheck.csv`. Default mode is saved-data/static only and does not call Alpaca. A confirmed read-only mode exists behind `--confirm-readonly-alpaca-check` to summarise recent orders, open orders, account block flags, and ticker position direction/quantity without printing account IDs, full order IDs, credentials, config contents, logs, databases, or full generated CSV contents. The postcheck never creates follow-up orders and always keeps follow-up order, order execution, execution, and scheduling approval false.

To prepare tomorrow's manual automation review without creating automation, run:

```text
python bot.py --future-refresh-cron-readiness-pack
```

This writes `data/future_refresh_cron_readiness_pack.csv`. It statically checks the current single Hermes status cron boundary, the design-only future refresh candidate sequence, lockfile/manual-review status, generated-output ignore policy, and false cron/execution approvals. It does not create, edit, trigger, delete, enable, or schedule any cron job.

The Monday manual smoke-test runbook is in `docs/PAPER_ORDER_SMOKE_TEST_RUNBOOK.md`. To verify the runbook text and false approval flags, run:

```text
python bot.py --paper-order-smoke-test-runbook-check
```

This writes `data/paper_order_smoke_test_runbook_check.csv`. The check is static/report-only and does not call Alpaca, create orders, read config contents, or schedule anything.

Diagnose why the manual paper smoke-test order was blocked by the kill-switch gate:

```text
python bot.py --paper-smoke-test-kill-switch-diagnosis
```

Saved display:

```text
python bot.py --show-paper-smoke-test-kill-switch-diagnosis
```

This writes `data/paper_smoke_test_kill_switch_diagnosis.csv`, `data/paper_smoke_test_kill_switch_diagnosis_summary.csv`, `data/paper_smoke_test_kill_switch_diagnosis_blockers.csv`, and `data/paper_smoke_test_kill_switch_diagnosis_recommendations.csv`. The report is saved-output-only: it classifies whether blockers belong to smoke-test connectivity safety or broader strategy-execution safety, preserves that the live preflight passed but the order gate blocked the attempt, confirms no matching order was found after the blocked attempt, and recommends manual gate review before any retry. It does not weaken the kill-switch, change `--paper-order-test`, call Alpaca, read paper positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord/Telegram alerts, change config defaults, schedule anything, or approve smoke-test execution.

Crypto strategy lab mode backtests a tiny fixed research-only strategy set for `BTC/USD`, `ETH/USD`, and `LTC/USD` using yfinance-compatible daily symbols (`BTC-USD`, `ETH-USD`, `LTC-USD`). The per-symbol strategies are `crypto_buy_and_hold_baseline`, `crypto_sma_50_200_trend`, `crypto_buy_above_200_exit_below_200`, and one controlled iteration: `crypto_buy_above_200_with_vol_gate`. The volatility-gate strategy uses fixed parameters only: 20-day realised volatility, trailing 252-day median volatility, and a 1.5x gate for new entries. The lab also writes a separate portfolio-style BTC/ETH/cash rotation test, `crypto_monthly_btc_eth_momentum_rotation`, using fixed monthly rebalance, 126-day momentum ranking, and a 200-day SMA absolute trend filter. It writes full-period, in-sample, and out-of-sample rows, plus an iteration log to discourage tuning after seeing results. Results include simple crypto research cost assumptions: `crypto_taker_fee_bps=10`, `crypto_spread_bps=5`, and `crypto_slippage_bps=10`. It does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Outputs:

```text
data/crypto_strategy_lab_results.csv
data/crypto_strategy_lab_trades.csv
data/crypto_strategy_iteration_log.csv
data/crypto_rotation_results.csv
data/crypto_rotation_trades.csv
```

The BTC/ETH/cash rotation is kept in separate CSVs because it is a portfolio-style strategy rather than a single-symbol strategy. The existing `--crypto-strategy-report` and `--crypto-strategy-decision-report` compare per-symbol strategies against matching per-symbol buy-and-hold benchmarks and do not directly rank the rotation yet.

Crypto strategy report mode reads `data/crypto_strategy_lab_results.csv` and writes a saved-data-only comparison report. It compares each strategy against `crypto_buy_and_hold_baseline` for the same symbol and period, including CAGR gap, drawdown reduction, and whether the strategy beats buy-and-hold on both CAGR and Calmar. It is research-only and does not approve execution.

Output:

```text
data/crypto_strategy_report.csv
```

Crypto strategy decision report mode reads `data/crypto_strategy_lab_results.csv` and `data/crypto_strategy_report.csv`, then writes a symbol-level decision report. It prefers out-of-sample Calmar and Sharpe over full-period CAGR, checks whether the best out-of-sample strategy beats buy-and-hold, and keeps every row research-only. It is not execution approval.

Output:

```text
data/crypto_strategy_decision_report.csv
```

Crypto cost stress report mode reruns the existing crypto strategy lab across four explicit one-way cost assumptions: `zero_cost` at 0 bps, `default_cost` at 25 bps, `high_cost` at 50 bps, and `extreme_cost` at 100 bps. It includes the existing crypto strategies only, compares each strategy against its own default-cost result, and marks every row research-only. It does not add strategies, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Output:

```text
data/crypto_cost_stress_report.csv
```

Crypto robustness report mode reruns the existing per-symbol crypto strategies across fixed chronological split points: 60/40, 70/30, and 80/20. It reports split date ranges, out-of-sample CAGR, Sharpe, max drawdown, Calmar, trade count, and the matching buy-and-hold out-of-sample benchmark metrics for the same symbol and split. A strategy can beat buy-and-hold for a split even when its own CAGR is negative if buy-and-hold was worse, so the benchmark fields and gap columns are included for interpretation. The BTC/ETH/cash rotation is not folded into this per-symbol robustness report because it needs a separate portfolio benchmark. This is research-only and does not add strategies, tune parameters, call Alpaca, create orders, enable shorting, enable margin, or approve execution.

Output:

```text
data/crypto_robustness_report.csv
```

Crypto period diagnostics mode reads saved crypto robustness, lab result, and lab trade CSVs to explain weak out-of-sample split periods for the current BTC and ETH focus candidates. It writes labels such as `benchmark_also_weak`, `cash_drag`, `whipsaw_sensitive`, and `profitable_but_weakening`. It is saved-data-only research reporting and does not refresh data, call Alpaca, create orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Output:

```text
data/crypto_period_diagnostics.csv
```

Crypto signal preview mode uses current yfinance-compatible daily data for the current best split-sensitive crypto research candidates: `BTC/USD` with `crypto_buy_above_200_with_vol_gate`, and `ETH/USD` with `crypto_buy_above_200_exit_below_200`. `LTC/USD` is included as research-only and remains flat when there is no selected candidate; if a saved decision report marks it `not_useful` or otherwise unsupported, the preview wording reflects that status instead of asking for research that already exists. It writes whether each candidate would prefer `long` or `flat` today, including SMA200 and volatility-gate diagnostics where applicable. It does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Output:

```text
data/crypto_signal_preview.csv
```

Crypto monitor display mode reads saved crypto CSVs only, starting with `data/crypto_signal_preview.csv`, and prints a terminal summary of current desired positions, signal reasons, saved decision status, saved robustness status, and saved period diagnostics. It does not refresh market data, call yfinance, call Alpaca, read positions, write files, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Command:

```text
python bot.py --show-crypto-monitor
```

Crypto research state report mode reads saved crypto CSVs only and writes one concise checkpoint across `BTC/USD`, `ETH/USD`, and `LTC/USD`. It combines universe status, saved decision status, saved signal preview, selected-candidate robustness and cost-stress status, separately labelled all-strategy robustness and cost-stress statuses, and period diagnostics. It is a checkpoint report only and does not refresh market data, call yfinance, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, add symbols, add strategies, or approve execution.

Command:

```text
python bot.py --crypto-research-state-report
```

Output:

```text
data/crypto_research_state_report.csv
```

Promoted strategy preview mode reads `data/strategy_promotion_report.csv`, previews current desired states for supported `preview_candidate` strategies, and writes `data/promoted_strategy_preview.csv`. It includes SPY regime, 50/200 SMA, 200-day threshold, 252-day high, and volume diagnostics where available. The `sma_50_200_trend` preview uses 50-day SMA versus 200-day SMA, while `buy_above_200_exit_below_200` uses close versus 200-day SMA. The clean QQQ lead `qqq_100_trend_gate` is also added as a promoted preview-review candidate from the saved `data/qqq100_preview_signal_pack.csv` output only; if that saved signal is missing, the QQQ100 row is blocked as missing input rather than refreshing data. `codex_broad_growth_balanced_breakout_control` remains high-growth research-only and is not promoted, and `qqq_150_trend_gate` remains rejected/not promoted. It does not call Alpaca, read paper positions, write to SQLite `trade_log`, send Discord alerts, or approve execution.

Output:

```text
data/promoted_strategy_preview.csv
```

Multi-strategy portfolio preview mode combines saved preview/research outputs into one non-executable portfolio-overlap review. It reads saved CSVs where present, including QQQ100 preview/action outputs, promoted preview rows, defensive context, high-growth branch checkpoints, crypto research/manual-review outputs, project research state, execution eligibility, and portfolio-risk policy outputs. It writes portfolio rows, summary, exposure grouping, conflict warnings, and blockers. QQQ100 is treated as the core growth trend candidate, defensive context is optional, high-growth and crypto remain research-only/blocked, and missing saved inputs are labelled as unavailable rather than refreshed. It does not call yfinance, call Alpaca, read paper positions, create order instructions, write SQLite `trade_log`, send Discord or Telegram alerts, approve scheduling, or approve execution.

```bash
python bot.py --multi-strategy-portfolio-preview
```

Saved display:

```bash
python bot.py --show-multi-strategy-portfolio-preview
```

Outputs:

```text
data/multi_strategy_portfolio_preview.csv
data/multi_strategy_portfolio_preview_summary.csv
data/multi_strategy_portfolio_preview_exposures.csv
data/multi_strategy_portfolio_preview_conflicts.csv
data/multi_strategy_portfolio_preview_blockers.csv
```

Promoted action preview mode reads `data/promoted_strategy_preview.csv` and compares desired positions with current Alpaca paper positions when read-only access is available. By default, dry-run mode does not read paper positions. To explicitly read paper positions for preview context without changing `dry_run`, use `python bot.py --preview-promoted-actions --use-paper-positions-readonly`. It never submits orders, cancels orders, writes `trade_log`, sends Discord alerts, or approves execution.

Output:

```text
data/promoted_strategy_action_preview.csv
```

Trend stress test mode focuses on slow SMA trend pairs and checks whether results survive higher trading costs:

- `40 / 160`
- `50 / 200`
- `60 / 200`
- `100 / 200`

It tests slippage at `0`, `5`, `10`, `25`, and `50` basis points using the shared research-only cost model. The optional ETF universe helps inspect broad index, sector, bond, and commodity ETFs separately from individual stocks.

Outputs:

```text
data/trend_stress_test_results.csv
data/trend_stress_test_portfolio.csv
```

Slow SMA preview mode shows the current long-only crossover signal for each ticker plus trend diagnostics. `HOLD` means there was no new crossover today; it can still be a bullish trend if the short SMA is already above the long SMA. `desired_position` is informational only and is not connected to order execution.

It does not submit Alpaca orders, does not send Discord alerts, and does not write to the live SQLite trade log.

Outputs:

```text
data/slow_sma_signal_preview.csv
```

Slow SMA action preview mode compares `desired_position` with current Alpaca paper positions, when paper credentials are available. This uses target-position alignment: the preview shows what would be needed to align the account with the strategy's current desired state, not just what a new crossover signal would do.

It is still preview-only. It does not submit orders, cancel orders, send Discord alerts, or write to the live SQLite trade log.

Outputs:

```text
data/slow_sma_action_preview.csv
```

Slow SMA paper execution is a separate explicit command. It requires `--confirm-slow-sma-paper`, requires Alpaca paper mode, refuses `allow_shorting: true`, and runs paper kill-switch preflight before any Alpaca, position, open-order, SQLite execution-write, Discord, or order-submission work. If future prerequisites pass, it checks assets and open orders before submitting and logs every submitted or skipped target-position action to SQLite.

It submits market DAY paper orders only. It is not connected to normal `python bot.py` behaviour.

Normal `python bot.py` still uses the original bot behaviour. Other research strategies should stay in backtest or preview mode until results are reviewed.

The initial V2 strategy lab skeleton exists in `trading_bot/strategies/base.py` and `trading_bot/strategies/registry.py`. The registry contains metadata for the existing research strategies. The research-only 52-week high breakout candidate is wired into `--compare-strategies` only. Monthly ETF rotation and adaptive risk-on/off momentum each have explicit research-only backtest commands. Crypto currently exists as research-only preview and strategy-lab scaffolding and is not connected to execution.

## How Trading Rules Work

The bot checks whether each ticker is currently flat, long, or short.

When `allow_shorting` is `false`:

- `BUY` opens a long position only if flat.
- `SELL` closes a long position only if already long.
- The bot never opens short positions.
- The bot never adds to an existing long position.

When `allow_shorting` is `true`:

- `BUY` opens a long position if flat.
- `BUY` closes an existing short position.
- `SELL` closes an existing long position.
- `SELL` opens a short position if flat.
- The bot never adds to an existing long or short position.

In dry-run mode, position state is simulated from the bot's own SQLite trade history. In Alpaca paper mode, position state comes from Alpaca.

Before submitting a paper order, the bot checks for existing open Alpaca orders for that ticker. Existing open orders block duplicate submissions.

## Check Logs and Trade History

Text logs:

```powershell
Get-Content logs\bot.log -Tail 50
```

SQLite trade history:

```powershell
python -c "import sqlite3; db=sqlite3.connect('data/trades.db'); [print(row) for row in db.execute(\"SELECT created_at,ticker,signal,action,order_status,error FROM trade_log ORDER BY id DESC LIMIT 20\")]"
```

You can also inspect `data/trades.db` with a SQLite browser tool.

Backtest CSVs:

```powershell
Get-Content data\backtest_results.csv
Get-Content data\strategy_comparison_results.csv
```

## Repeated Runs And Scheduling

The bot runs once and exits. Repeated runs are not approved by default.

For future monitoring-only, chat-delivered market monitor reports, prefer Hermes
cron once Hermes runs on the VPS. Windows Task Scheduler may be used only to
start or keep the Hermes gateway running on boot, not for execution-capable
trading commands.

Do not schedule:

```powershell
python bot.py
python bot.py --paper-order-test ...
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

Candidate future Hermes cron command for market monitor reports only:

```bat
cd /d C:\dev\paper-trading-bot
.venv\Scripts\python.exe bot.py --refresh-market-monitor
```

This candidate is not approved for scheduling yet and does not approve orders or
paper execution. Before any future scheduling review, run:

```powershell
python scripts\verify_repo_safety.py
python bot.py --market-monitor-scheduling-readiness-report
python bot.py --refresh-market-monitor
```

The manual VPS refresh must succeed, generated CSV/cache files must remain
ignored, and work must stop if any candidate tries to load `config.json`, call
Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, create
orders, or approve execution.

## Troubleshooting

Config file not found:

- Copy `config.example.json` to `config.json`.
- Run PowerShell from the project folder.

Alpaca key error:

- Keep `dry_run: true` until your paper API keys are ready.
- Use paper keys, not live keys.
- Keep `alpaca.paper: true`.

No market data:

- Check the ticker spelling.
- Use U.S. stock and ETF symbols only.
- Try a longer `history_period`, such as `1y`.

Not enough price history:

- Increase `history_period`.
- Use a smaller `long_window`.

Discord alert failed:

- Check that the webhook URL is correct.
- Make sure the Discord channel still exists.

Backtest output is empty:

- Confirm yfinance can download daily data locally.
- Try a longer `backtest.history_period`, such as `10y`.
- Remember that backtest mode needs enough rows for 200-day SMA and volatility windows.

## Useful References

- [yfinance download documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)
- [Alpaca Python SDK trading docs](https://alpaca.markets/sdks/python/trading.html)
- [Discord webhook docs](https://docs.discord.com/developers/resources/webhook)
