# First Hermes Cron Job Design

This is a design/checklist for the first future VPS-safe Hermes cron job. It is
planning only. No Hermes cron job, Windows Task Scheduler task, service, startup
script, cron file, loop mode, background process, scheduling approval, or
execution approval is currently created.

## Scope

The first Hermes cron job should be status-only. It should prove that a scheduled
Hermes status/checkpoint report can run cleanly before any refresh cron job is
considered.

The first job should run from `C:\dev\paper-trading-bot` and use the VPS Python:

```powershell
.venv\Scripts\python.exe
```

The first status-only job may run:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py
.venv\Scripts\python.exe bot.py --vps-monitoring-status
.venv\Scripts\python.exe bot.py --market-monitor-scheduling-readiness-report
```

The final scheduling decision, exact cadence, exact command list, enabled
toolsets, output destination, and failure behaviour remain future manual
decisions. A conservative cadence such as hourly or a few times per day may be
considered later, but no cadence is approved by this design.

## First Job Exclusions

The first status-only cron job must not run refresh commands yet:

- `--refresh-promoted-review`
- `--refresh-defensive-research`

Refresh cron jobs require a later separate review after the status-only job
proves stable. Refresh jobs should remain protected by lockfile/no-overlap. A
stale lock requires manual review. Lockfile protection is for overlap control
only; it is not scheduling approval, execution approval, order approval, or
paper-execution approval.

Execution-capable commands remain high-risk/manual-only and must not be
scheduled or automated:

- normal bot run
- paper-order smoke test
- slow-SMA paper execution
- any future order-capable command

The job must not run any command that submits, cancels, or creates orders,
mutates positions, writes SQLite `trade_log`, sends trade alerts, changes config
defaults, or changes strategy logic.

## Data And Secret Boundaries

The job must not inspect, print, paste, or expose config contents, API keys,
webhooks, account IDs, `.env` files, auth files, tokens, logs, SQLite databases,
or generated CSV/chart contents. It may rely on the status command's existing
compact summaries, but it must not independently read generated output contents.

If generated outputs are missing, report that as a prerequisite/status issue,
not execution approval and not a reason to bypass safety checks.

## Hermes Runtime Checklist

Before any future creation of the cron job, review this checklist:

- Use Hermes cron for safe monitoring/reporting only; not for execution.
- Use restricted Hermes toolsets if supported, such as `enabled_toolsets` scoped
  to the minimum needed for command execution and concise reporting.
- Run from `C:\dev\paper-trading-bot`.
- Use `.venv\Scripts\python.exe`.
- Run repo safety before status.
- Treat any safety verifier failure as a stop condition.
- Capture output concisely.
- Report failures clearly.
- Do not create, edit, delete, or recursively create other cron jobs.
- Do not create Windows Task Scheduler tasks, services, startup scripts, loop
  modes, or background processes.
- Do not perform Git commits or pushes.
- Do not run automatic `git pull` unless a later separate review approves update
  behaviour.
- Preserve `scheduling_approved=False`.
- Preserve `execution_approved=False`.

No scheduling is currently approved or created. This design is only a checkpoint
for a future manual scheduling review.
