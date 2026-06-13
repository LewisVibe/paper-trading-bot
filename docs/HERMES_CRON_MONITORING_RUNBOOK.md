# Hermes Cron Monitoring Runbook

This runbook explains how to interpret Telegram output from the status-only
Hermes cron job and choose safe manual follow-up checks. It does not approve
execution, create a second cron job, approve refresh automation, or approve live
trading.

## Current Status Cron

- Job name: `paper-bot-vps-status-check`
- Job ID: `345188fbb60c`
- Cadence: daily at 10:10am UK local time
- Cron expression: `10 10 * * *`
- Delivery: Telegram
- Mode: script-only / no-agent
- Working directory: `C:\dev\paper-trading-bot`

Command sequence:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

Expected healthy output includes repo_safety PASS, hermes_cron_readiness PASS,
vps_daily_monitoring_summary PASS, final_monitoring_status
`healthy_monitoring_state`, action_required
`no_action_required`, `execution_approved=false`, `scheduling_approved=false`,
and freshness_warnings: none.

## Final States

### healthy_monitoring_state

Meaning:

- status cron worked;
- repo safety passed;
- Hermes cron readiness passed;
- daily monitoring summary passed;
- `action_required=no_action_required`;
- no immediate action is needed.

Suggested response:

- record or check output if useful;
- do not create execution or scheduling changes;
- do not create a refresh job purely because the status is healthy.

### monitoring_warning

Meaning:

- monitoring ran, but a non-critical warning appeared;
- likely a freshness warning, missing optional report, or stale saved output;
- `action_required` should normally explain the safe manual follow-up category;
- this is not execution approval.

Suggested response:

- inspect the warning text;
- run safe status/report commands manually if needed;
- if it relates to promoted review freshness, consider a manual promoted-review
  refresh chain only after repo safety passes;
- do not schedule refresh automatically based only on one warning.

### monitoring_stale_or_missing_inputs

Meaning:

- key saved monitoring inputs are stale or missing;
- monitoring state is not healthy enough for scheduling changes;
- `action_required=manual_review_required` should point to saved monitoring input
  review rather than any high-risk command;
- this is not execution approval.

Suggested response:

- run repo safety first;
- run the relevant design/status verifier;
- manually refresh the specific missing or stale report chain if appropriate;
- rerun `--vps-daily-monitoring-summary`;
- keep cron scheduling unchanged until healthy again.

### Failed Step

Examples:

- repo_safety: FAIL
- hermes_cron_readiness: FAIL
- vps_daily_monitoring_summary: FAIL

Suggested response:

- stop;
- do not run refresh jobs;
- do not create or edit cron jobs;
- inspect the failing verifier/report only;
- fix docs/code only after scoped review.

## Safe Manual Checks

Use the VPS virtual environment:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe scripts\verify_hermes_promoted_review_refresh_cron_design.py
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
.venv\Scripts\python.exe bot.py --vps-monitoring-status
```

## Manual Promoted-Review Diagnostic

This chain is a future/manual diagnostic only, not automatic scheduling
approval:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe bot.py --refresh-promoted-review
.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary
```

Manual refresh is not cron creation. Manual refresh is not execution approval.
Manual refresh writes or refreshes generated monitoring outputs only. The
promoted-review refresh command is lock-wrapped; a lock issue means stop and
manual review.

## Boundaries

This runbook preserves `execution_approved=false` and
`scheduling_approved=false`. It does not approve execution. It does not approve
creating the second cron. It does not approve live trading.

Do not print or inspect secrets, config contents, logs, databases, auth files,
tokens, account IDs, webhooks, or full generated CSV contents. Do not schedule
execution-capable commands. Normal bot runs, paper-order smoke tests, slow-SMA
paper execution, and any future order-capable command remain manual-only and
outside Hermes cron automation.
