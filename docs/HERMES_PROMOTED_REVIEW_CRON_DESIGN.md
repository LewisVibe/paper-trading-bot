# Future Hermes Promoted Review Refresh Cron Design

This document is a design/checkpoint only. No Hermes cron job is currently
created, scheduled, enabled, triggered, or approved. This does not approve
scheduling, execution, orders, paper execution, or live trading.

The possible future promoted-review refresh cron job would be separate from the
existing `paper-bot-vps-status-check` daily status job. It would be considered
only after a separate manual review confirms the exact cadence, exact command
list, enabled toolsets, output destination, and failure behaviour.

## Candidate Future Flow

The candidate job would run from `C:\dev\paper-trading-bot` and use
`.venv\Scripts\python.exe`.

Candidate future command sequence:

```powershell
.venv\Scripts\python.exe bot.py --refresh-promoted-review
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

`--refresh-promoted-review` is lock-wrapped today and must remain lock-wrapped
before any future cron review. The follow-up command may be
`--vps-daily-monitoring-summary` or `--vps-monitoring-status`; it should report
the resulting monitoring state without approving scheduling or execution.

## Required Boundaries

The candidate job must:

- stop on safety failures;
- treat stale lock detection as manual review;
- avoid committing, pushing, pulling, or updating code automatically;
- avoid creating, editing, deleting, triggering, or recursively creating other
  cron jobs;
- avoid Windows Task Scheduler tasks, services, startup scripts, loop mode,
  dashboard/web server mode, and background processes;
- avoid printing secrets, config contents, API keys, webhooks, account IDs,
  logs, database contents, or full generated CSV contents;
- avoid normal bot runs, paper-order smoke tests, slow-SMA paper execution, and
  any future order-capable workflow;
- avoid submitting, cancelling, or creating orders;
- avoid mutating positions;
- avoid writing SQLite `trade_log`;
- avoid sending trade alerts;
- avoid changing config defaults or strategy logic.

If promoted review reports strategy disagreement, that is a monitoring result,
not execution approval. Missing or stale saved outputs are prerequisites/status
issues, not trading approval.

## Approval Flags

Every future review must preserve:

- `scheduling_approved=False`
- `execution_approved=False`

Candidate cadence remains a future manual decision. Candidate output destination
remains a future manual decision. This design does not create or approve the job.
