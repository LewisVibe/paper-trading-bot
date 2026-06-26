# Hermes Paused Status Cron Checkpoint

This document records a paused Hermes cron job definition for future manual
activation review. It is not enabled, has never run, and does not approve
scheduling, refresh automation, execution, paper execution, live trading, repeat
orders, or follow-up orders.

## Paused Job State

- Job name: `paused-vps-safe-paper-bot-status-check`
- Job ID: `66c8a5bb438e`
- State: `paused`
- Enabled: `false`
- Schedule placeholder: once at `2099-01-01 00:00`
- Last run: `never`
- Delivery: current/origin Telegram chat
- Toolsets restricted to: `terminal`
- Working directory: `C:\dev\paper-trading-bot`

## Intended Command Sequence

The paused job definition is status/report only. If it is ever reviewed for
activation, the intended sequence is:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe scripts\verify_vps_daily_monitoring_summary.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

The sequence is designed to stop on verifier failure and return a concise
Telegram status summary only.

## Explicit Boundaries

This paused job must not:

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
- `scheduling_approved=False`
- `live_trading_approved=False`
- `followup_order_approved=False`
- `repeat_execution_approved=False`

The paused job definition is not scheduling approval. Activation requires a
separate manual approval step after the saved report chain remains healthy on
the VPS.

## Manual Activation Checklist

Before the paused job may be enabled or rescheduled, a separate manual review
must confirm:

- repo safety passes on the VPS;
- Hermes cron readiness passes on the VPS;
- VPS daily monitoring summary verifier passes on the VPS;
- VPS daily monitoring summary includes the active volatility seed readiness section;
- VPS daily monitoring summary remains status/report only;
- the job remains script-only / no-agent where possible;
- toolsets remain restricted to terminal;
- no refresh, broker-read, market-refresh, or order-capable command is added;
- all approval flags remain false.
