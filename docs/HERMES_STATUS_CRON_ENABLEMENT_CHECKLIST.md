# Hermes Status Cron Enablement Checklist

This checklist is a planning checkpoint for the paused Hermes status job. It
does not create, edit, trigger, enable, or schedule any Hermes cron job, and it
does not approve execution, paper execution, follow-up orders, repeat orders, or
live trading.

## Current Paused Job

- Job name: `paused-vps-safe-paper-bot-status-check`
- Job ID: `66c8a5bb438e`
- Current state: `paused`
- Enabled: `false`
- Stored future schedule: `*/30 14-20 * * 1-5`
- Intended timezone: UK local / Europe-London
- Last scheduled run: `never`
- Delivery: current/origin Telegram chat
- Toolsets restricted to: `terminal`
- Working directory: `C:\dev\paper-trading-bot`

## Status-Only Command Sequence

If this paused job is ever enabled after separate manual approval, the command
sequence should remain status/report only:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe scripts\verify_vps_daily_monitoring_summary.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

The job should stop on verifier failure and should not continue to the daily
summary when repo safety, Hermes readiness, or daily-summary verification fails.

## Market-Hours Cadence Options

The user preference is not a once-daily status cron. The paused job now stores a
future `*/30 14-20 * * 1-5` cadence for weekday UK-local market-hours status
checks, but cadence activation is not approved by this document.

Candidate cadence options for a later manual scheduling review:

- Conservative alternative: hourly during the US regular market session.
- Stored future candidate: every 30 minutes during the broad UK-local
  `14:00-20:59` weekday monitoring window.
- The stored future candidate is still every 30 minutes during the US regular
  market session in intent, with a broad UK-local window used for practical
  scheduling review.
- Avoid very frequent status checks until the Telegram output, saved-output
  freshness, and verifier stability have been observed over real market days.

US regular equity market hours are normally `09:30-16:00 America/New_York`.
During the normal UK/US summer overlap this is usually `14:30-21:00 UK local
time`. DST mismatch weeks must be reviewed manually before encoding a Hermes
schedule.

## Explicit Non-Approval State

This checkpoint preserves:

- `execution_approved=False`
- `paper_execution_approved=False`
- `scheduling_approved=False`
- `live_trading_approved=False`
- `followup_order_approved=False`
- `repeat_execution_approved=False`

Market-hours monitoring is observation only. It must not imply orders, action
previews, broker reads, strategy execution, seed changes, or scheduling approval.

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

Stop and keep the job paused if any of these occur:

- repo safety fails;
- Hermes cron readiness fails;
- VPS daily monitoring summary verification fails;
- the daily summary cannot show the active-seed readiness section and does not
  clearly label the missing saved-output state;
- any approval flag is not false;
- the command sequence drifts beyond status/report checks;
- a command tries to call Alpaca, read positions, refresh market data, send
  alerts, write SQLite `trade_log`, or create order fields;
- the proposed cadence is not reviewed against UK/US DST timing.

## Manual Approval Checklist Before Enabling

Before any human edits the paused Hermes job:

- confirm the VPS repo is clean enough for operations review;
- run repo safety on the VPS;
- run Hermes cron readiness on the VPS;
- run the VPS daily monitoring summary verifier on the VPS;
- run the current status-only sequence manually once;
- confirm the job is still paused and disabled before editing it;
- confirm the exact UK-local market-hours window and DST handling;
- choose one cadence explicitly, preferably hourly first;
- keep script-only / no-agent mode where supported;
- keep toolsets restricted to `terminal`;
- keep Telegram delivery;
- keep the working directory `C:\dev\paper-trading-bot`;
- keep the command sequence free of broker reads, refreshes, Git operations, and
  order-capable commands.

This checklist is not the approval itself. The next step is a separate manual
approval prompt that names the exact cadence, timezone handling, and job edit to
make.
