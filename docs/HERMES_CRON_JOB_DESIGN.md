# Hermes Daily Status Cron Checkpoint

This document records the current verified first Hermes cron job. It is
status-only. It does not approve any refresh cron job, execution workflow,
orders, paper execution, live trading, or broader scheduling.

## Current Verified Job

- Job name: `paper-bot-vps-status-check`
- Job ID: `345188fbb60c`
- Cadence: once daily / every 1440m
- Delivery: Telegram
- Mode: script-only / no-agent
- Working directory: `C:\dev\paper-trading-bot`

Current command sequence:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

Verified output:

- repo_safety: PASS
- hermes_cron_readiness: PASS
- vps_daily_monitoring_summary: PASS
- final_monitoring_status: healthy_monitoring_state
- execution_approved: false
- scheduling_approved: false
- freshness_warnings: none

## Boundaries

The current job:

- runs only status/checkpoint reporting;
- uses `.venv\Scripts\python.exe`, not bare `python`;
- sends concise output to Telegram;
- does not run `--refresh-promoted-review`;
- does not run `--refresh-defensive-research`;
- does not trade;
- does not approve scheduling beyond this one status job;
- does not approve execution;
- does not pull, commit, or push code;
- does not inspect or print config contents, secrets, API keys, webhooks,
  account IDs, logs, SQLite databases, or full generated CSV/chart contents;
- does not create, edit, delete, trigger, or recursively create other cron jobs.

Refresh cron jobs require a later separate review. Refresh jobs should remain
protected by lockfile/no-overlap. A stale lock requires manual review. Lockfile
protection is for overlap control only; it is not scheduling approval, execution
approval, order approval, or paper-execution approval.

Execution-capable commands remain high-risk/manual-only and must not be
scheduled or automated:

- normal bot run;
- paper-order smoke test;
- slow-SMA paper execution;
- any future order-capable command.

This checkpoint preserves:

- `scheduling_approved=False`
- `execution_approved=False`
