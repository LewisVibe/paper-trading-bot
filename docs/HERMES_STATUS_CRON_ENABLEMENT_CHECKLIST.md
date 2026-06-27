# Hermes Status Cron Enablement Checklist

This checklist records the manual enablement checkpoint for the Hermes status
job. The job is now enabled for status/report monitoring only. This does not
approve execution, paper execution, refresh jobs, broker reads, follow-up orders,
repeat orders, or live trading.

## Current Enabled Job

- Job name: `paused-vps-safe-paper-bot-status-check`
- Job ID: `66c8a5bb438e`
- Current state: `scheduled`
- Enabled: `true`
- Schedule: `*/30 14-20 * * 1-5`
- Intended timezone: UK local / Europe-London
- Next run: `2026-06-29T14:00:00+01:00`
- Last scheduled run: `null` / never run by cron
- Delivery: current/origin Telegram chat
- Toolsets restricted to: `terminal`
- Mode: script-only / no-agent
- Working directory: `C:\dev\paper-trading-bot`

## Status-Only Command Sequence

The enabled job command sequence must remain status/report only:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe scripts\verify_vps_daily_monitoring_summary.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

The job should stop on verifier failure and should not continue to the daily
summary when repo safety, Hermes readiness, or daily-summary verification fails.

## Market-Hours Cadence

The user preference is not a once-daily status cron. The job now uses
`*/30 14-20 * * 1-5` for weekday UK-local market-hours status checks.

Cadence notes:

- Conservative alternative: hourly during the US regular market session.
- Current enabled cadence: every 30 minutes during the broad UK-local
  `14:00-20:59` weekday monitoring window.
- The current enabled cadence is still every 30 minutes during the US regular
  market session in intent, with a broad UK-local window used for practical
  scheduling review.
- Avoid adding more frequent checks until the Telegram output, saved-output
  freshness, and verifier stability have been observed over real market days.

US regular equity market hours are normally `09:30-16:00 America/New_York`.
During the normal UK/US summer overlap this is usually `14:30-21:00 UK local
time`. DST mismatch weeks must be reviewed manually before changing the Hermes
schedule.

## Explicit Non-Approval State

This checkpoint preserves:

- `execution_approved=False`
- `paper_execution_approved=False`
- `scheduling_approved=False` for strategy execution, refresh jobs, and
  order-capable workflows
- `live_trading_approved=False`
- `followup_order_approved=False`
- `repeat_execution_approved=False`

Market-hours monitoring is observation only. It must not imply orders, action
previews, broker reads, strategy execution, seed changes, refresh jobs, or
order-capable scheduling.

## Things This Job Must Not Do

The status cron must not run normal `python bot.py`, paper-order tests, QQQ100
paper execution, slow-SMA paper execution, broker-position comparison, yfinance
refresh commands, promoted-review refresh, defensive-research refresh, market
monitor refresh, action-preview commands, or any order-capable command.

It must not call Alpaca, read live or paper positions, create order fields,
prepare orders, submit orders, cancel orders, replace orders, write SQLite
`trade_log` rows, send trade alerts, read or print config contents, read or
print `.env` contents, read logs/databases/generated CSV contents in full, pull
code, commit code, or push code.

## Stop Conditions

Stop and disable the job for manual review if any of these occur:

- repo safety fails;
- Hermes cron readiness fails;
- VPS daily monitoring summary verification fails;
- the daily summary cannot show the active-seed readiness section and does not
  clearly label the missing saved-output state;
- any execution/order approval flag is not false;
- the command sequence drifts beyond status/report checks;
- a command tries to call Alpaca, read positions, refresh market data, send
  alerts, write SQLite `trade_log`, or create order fields;
- the cadence needs UK/US DST adjustment and has not been manually reviewed.

## Manual Checklist Before Future Changes

Before any human edits this Hermes job again:

- confirm the VPS repo is clean enough for operations review;
- run repo safety on the VPS;
- run Hermes cron readiness on the VPS;
- run the VPS daily monitoring summary verifier on the VPS;
- run the current status-only sequence manually once if the change affects commands or cadence;
- confirm the job state before editing it;
- confirm the exact UK-local market-hours window and DST handling;
- keep script-only / no-agent mode where supported;
- keep toolsets restricted to `terminal`;
- keep Telegram delivery;
- keep the working directory `C:\dev\paper-trading-bot`;
- keep the command sequence free of broker reads, refreshes, Git operations, and
  order-capable commands.

This checklist documents the current status-only enablement. Any future change
to cadence, commands, toolsets, delivery, or execution boundaries requires a
separate manual approval prompt that names the exact job edit to make.
