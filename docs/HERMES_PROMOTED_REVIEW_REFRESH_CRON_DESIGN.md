# Future Hermes Promoted Review Refresh Cron Design

This is a future-only design/checklist. No promoted-review refresh Hermes cron
job is currently created, scheduled, enabled, triggered, or approved. This
design does not approve scheduling, execution, orders, paper execution, or live
trading.

The candidate job would be separate from the existing `paper-bot-vps-status-check`
daily status cron. It should only be considered after the daily status cron runs
reliably and a later manual review approves the exact cadence, exact command
list, enabled toolsets, output destination, and failure behaviour.

## Candidate Purpose

Refresh promoted review outputs and then report a compact daily monitoring
summary. Strategy disagreement, no-action states, blocked review states, missing
outputs, or stale outputs are monitoring results only. They are not execution
approval.

## Candidate Command Sequence

If later approved, the candidate job would run from `C:\dev\paper-trading-bot`
and use `.venv\Scripts\python.exe`.

Candidate future sequence:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe bot.py --refresh-promoted-review
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

`--refresh-promoted-review` is already lock-wrapped. If the lock is fresh,
malformed, stale, or otherwise blocks the command, the job should stop and
require manual review. Lockfile protection is overlap control only, not
scheduling approval, execution approval, order approval, or paper-execution
approval.

Read-only paper-position context is allowed only through the existing preview
path. Do not expand it.

## Required Boundaries

The candidate job must remain preview/report-only and must not:

- submit, cancel, or create orders;
- mutate positions;
- write SQLite `trade_log`;
- send trade alerts;
- change config defaults;
- change strategy logic;
- run the normal bot workflow;
- run paper-order smoke tests;
- run slow-SMA paper execution;
- inspect or print secrets, config contents, account IDs, logs, databases, or
  full generated CSV contents;
- commit, push, pull, or update code automatically;
- create, edit, delete, trigger, or recursively create other cron jobs;
- create Windows Task Scheduler tasks, services, startup scripts, loop mode,
  dashboard/web server mode, or background processes.

Failure behaviour should stop on the first safety/check failure and report
concise output.

## Approval Flags

This design requires:

- `scheduling_approved=False`
- `execution_approved=False`

Cadence is not approved yet and remains a later manual decision. Output
destination is not approved yet and remains a later manual decision. A separate
manual review is required before this job can be created.
