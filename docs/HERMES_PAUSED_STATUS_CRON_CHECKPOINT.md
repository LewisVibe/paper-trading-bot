# Hermes Status Cron Checkpoint

This document records the enabled Hermes status cron job definition for
market-hours monitoring. It has not yet run by cron and does not approve refresh
automation, broker reads, strategy execution, paper execution, live trading,
repeat orders, or follow-up orders.

## Current Job State

- Job name: `paused-vps-safe-paper-bot-status-check`
- Job ID: `66c8a5bb438e`
- State: `scheduled`
- Enabled: `true`
- Schedule: `*/30 14-20 * * 1-5`
- Intended timezone: UK local / Europe-London
- Next run: `2026-06-29T14:00:00+01:00`
- Last run status: `null` / never run by cron
- Delivery: current/origin Telegram chat
- Toolsets restricted to: `terminal`
- Mode: script-only / no-agent
- Script: `vps_safe_paper_bot_status_check.py`
- Working directory: `C:\dev\paper-trading-bot`

## Command Sequence

The enabled job definition is status/report only. The command sequence is:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe scripts\verify_vps_daily_monitoring_summary.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

The sequence is designed to stop on verifier failure and return a concise
Telegram status summary only.

## Manual One-Off Test Result

On `2026-06-27`, the status command sequence was run once manually as a
status-only test. The job remained paused and disabled after that test, and the
schedule placeholder remained `2099-01-01 00:00` at that time. A later manual
metadata update changed the stored schedule to `*/30 14-20 * * 1-5` while
keeping the job paused, disabled, and never run by cron. On `2026-06-27`, the
existing job was then enabled without being manually triggered; Hermes reported
state `scheduled`, enabled `true`, next run `2026-06-29T14:00:00+01:00`, and
last run status `null` / never run by cron.

Observed manual-test result:

- repo safety: passed;
- Hermes cron readiness: `9` checks passed, `0` warnings, `0` errors;
- VPS daily monitoring summary verifier: passed;
- VPS daily monitoring final status: `monitoring_stale_or_missing_inputs`;
- VPS daily monitoring action required: `manual_review_required`;
- active volatility seed readiness status:
  `vol_targeted_growth_active_seed_monitoring_incomplete_manual_review_required`;
- active seed/ticker:
  `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE`;
- previous seed context: `qqq_100_trend_gate` / `QQQ`;
- approval flags remained false for execution, paper execution, scheduling,
  follow-up orders, and repeat execution;
- no order-capable commands were run.

After the missing saved active-seed readiness output was regenerated manually
with the existing report-only command, the VPS daily monitoring summary check
passed and the active-seed readiness section reported ready-for-monitoring
review. This is evidence that the status/report shell works; it is not
permission to add refresh, broker-read, or order-capable scheduling.

## Explicit Boundaries

This status cron job must not:

- run normal `python bot.py`;
- run paper-order tests;
- run QQQ100 paper execution;
- run slow-SMA paper execution;
- run broker-position comparison;
- run yfinance refresh commands;
- run refresh commands such as `--refresh-promoted-review` or
  `--refresh-defensive-research`;
- call Alpaca;
- read live or paper positions;
- create, prepare, submit, cancel, replace, or suggest orders;
- write SQLite `trade_log` rows;
- send trade alerts;
- read or print config contents, `.env`, API keys, webhooks, account IDs,
  logs, databases, auth files, tokens, or full generated CSV/chart contents;
- pull, commit, or push Git changes;
- create, edit, delete, trigger, enable, or schedule any other cron job.

## Approval State

This checkpoint preserves:

- `execution_approved=False`
- `paper_execution_approved=False`
- `scheduling_approved=False` for strategy execution, refresh jobs, and
  order-capable workflows
- `live_trading_approved=False`
- `followup_order_approved=False`
- `repeat_execution_approved=False`

This enabled status cron is approval for this status/report monitoring job only.
It is not approval for refresh automation, broker reads, order-capable commands,
strategy execution, paper execution, live trading, repeat orders, or follow-up
orders.

## Ongoing Monitoring Checklist

While the job is enabled, periodic manual review should confirm:

- repo safety passes on the VPS;
- Hermes cron readiness passes on the VPS;
- VPS daily monitoring summary verifier passes on the VPS;
- VPS daily monitoring summary includes the active volatility seed readiness section, or clearly reports the saved active-seed readiness output as missing/manual-review required;
- VPS daily monitoring summary remains status/report only;
- the job remains script-only / no-agent where possible;
- toolsets remain restricted to terminal;
- no refresh, broker-read, market-refresh, or order-capable command is added;
- all execution/order approval flags remain false.
