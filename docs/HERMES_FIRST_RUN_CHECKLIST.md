# Hermes First Scheduled Run Checklist

This checklist is for the first scheduled Telegram/status result from the
enabled Hermes market-hours status job. It is a review aid only. It does not
create, edit, trigger, disable, or schedule any Hermes job, and it does not
approve trading, paper execution, refresh automation, broker reads, repeat
orders, or follow-up orders.

## Job To Observe

- Job name: `paused-vps-safe-paper-bot-status-check`
- Job ID: `66c8a5bb438e`
- State expected before first run: `scheduled`
- Enabled expected before first run: `true`
- Schedule: `*/30 14-20 * * 1-5`
- Intended timezone: UK local / Europe-London
- First expected scheduled run: `2026-06-29T14:00:00+01:00`
- Delivery: current/origin Telegram chat
- Toolsets restricted to: `terminal`
- Mode: script-only / no-agent
- Working directory: `C:\dev\paper-trading-bot`

## Expected Command Sequence

The scheduled job must run only this status/report sequence:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe scripts\verify_vps_daily_monitoring_summary.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

The job should stop on verifier failure. It should not attempt any auto-fix,
Git operation, broker read, market-data refresh, or order-capable command.

## Healthy First-Run Result

Treat the first scheduled run as healthy if the Telegram output shows:

- repo safety passed;
- Hermes cron readiness passed;
- VPS daily monitoring summary verifier passed;
- `python bot.py --vps-daily-monitoring-summary` completed;
- final status is `healthy_monitoring_state`, or a clearly explained
  manual-review status caused only by stale/missing saved report inputs;
- active seed context is visible, currently
  `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE`;
- previous seed context is visible, currently `qqq_100_trend_gate` / `QQQ`;
- approval flags remain false for execution, paper execution, follow-up orders,
  repeat execution, and strategy/order scheduling.

## Warning Result

Treat the first scheduled run as warning/manual-review if:

- one of the saved-output sections is stale or missing, but the output labels it
  clearly as stale/missing/manual-review;
- the active-seed readiness section is incomplete but does not approve action;
- the final status is `monitoring_stale_or_missing_inputs`;
- Telegram delivery works but formatting is hard to scan.

Warnings should be handled by report/verifier or saved-output maintenance only.
They must not trigger broker reads, refresh jobs, paper orders, or cron command
expansion.

## Failure / Stop Conditions

Stop and disable the job for manual review if any first-run output shows:

- repo safety failed;
- Hermes cron readiness failed;
- VPS daily monitoring summary verifier failed;
- the job ran a command outside the four-command status sequence;
- any approval flag is true;
- output suggests order creation, order submission, order cancellation, order
  replacement, broker-position reads, Alpaca calls, yfinance refreshes, SQLite
  `trade_log` writes, Discord/Telegram trade alerts, Git pulls, Git commits, or
  Git pushes;
- config contents, `.env`, API keys, webhook URLs, account IDs, order IDs,
  logs, databases, or full generated CSV/chart contents are printed.

## Explicit Non-Approval State

This first-run checklist preserves:

- `execution_approved=False`
- `paper_execution_approved=False`
- `scheduling_approved=False` for strategy execution, refresh jobs, and
  order-capable workflows
- `live_trading_approved=False`
- `followup_order_approved=False`
- `repeat_execution_approved=False`

The enabled cron is only for the existing status/report monitoring sequence.
It is not approval for refresh automation, broker reads, trading, strategy
execution, paper execution, live trading, repeat orders, or follow-up orders.

## First-Run Result Log Template

After the first scheduled Telegram message arrives, record:

- observed run time:
- job state after run:
- last run status:
- repo safety result:
- Hermes cron readiness result:
- VPS daily monitoring summary verifier result:
- VPS daily monitoring final status:
- active seed/ticker:
- previous seed/ticker:
- approval flags false:
- warnings or blockers:
- action taken:

If the result is healthy, continue observing the next few scheduled messages
without changing the job. If the result is warning or failure, handle it as a
monitoring/reporting issue only.
