# VPS Setup Checklist

This checklist is for a possible future Windows Server VPS setup. It is not a
deployment plan, and it does not approve scheduling, paper execution, live
trading, or any order-submission workflow.

The first VPS phase should run safe report, display, and preview commands only.

## Purpose

- Prepare a Windows Server VPS environment for future manual testing.
- Keep the project paper-only and dry-run-first.
- Verify local repository, Python, package, and safety readiness before running
  any report or preview commands.
- Keep execution-capable commands manually gated and out of automation.

## Safety Boundary

- Never live trade.
- Keep `alpaca.paper=true`.
- Keep `dry_run=true` unless a separately reviewed paper-execution workflow is
  explicitly being tested.
- Keep `allow_shorting=false`.
- Do not schedule execution-capable commands.
- Do not commit `config.json`, `.env` files, logs, databases, CSV outputs, or
  chart files.
- Keep API keys, Discord webhooks, account IDs, and all secrets private.
- Do not paste secrets into ChatGPT, Codex, GitHub issues, commits, logs, or
  screenshots.
- Research, report, preview, and display commands do not approve execution.

## Initial VPS Prerequisites

- Windows Server VPS.
- Git installed and available from PowerShell or CMD.
- Python 3.11 or newer installed.
- Project cloned from GitHub:
  `https://github.com/LewisVibe/paper-trading-bot.git`
- Python virtual environment created.
- `requirements.txt` installed.

## Safe Clone And Setup Steps

Future setup example:

```powershell
git clone https://github.com/LewisVibe/paper-trading-bot.git
cd "paper-trading-bot"
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

These commands prepare the project only. They do not schedule anything and do
not approve execution.

## Local Config Setup

- Copy `config.example.json` to `config.json`.
- Add Alpaca paper credentials locally only.
- Add a Discord webhook locally only if needed.
- Keep `alpaca.paper=true`.
- Keep `dry_run=true`.
- Keep `allow_shorting=false`.
- Never commit `config.json`.
- Never paste secrets into ChatGPT, Codex, GitHub, terminal transcripts, or docs.

## First Safety Checks On VPS

Run these manually after setup:

```powershell
python scripts\verify_repo_safety.py
python bot.py --deployment-readiness-report
python bot.py --vps-operations-readiness-report
python scripts\verify_v2_baseline.py --timeout-seconds 180
```

Expected caveat:

- Network-backed yfinance or Discord checks may fail if the VPS firewall,
  network, DNS, or webhook configuration blocks them.
- No-network verifiers are still useful for code safety and repository hygiene.
- Treat any new failure, traceback, or warning as something to investigate
  before scheduling or relying on the VPS.

## Safe Commands For Future Scheduling Review

These are candidates for later scheduling review only after each has been run
manually and verified on the VPS:

```powershell
python bot.py --refresh-defensive-research
python bot.py --refresh-promoted-review
python bot.py --show-promoted-decision
python bot.py --show-crypto-monitor
python bot.py --deployment-readiness-report
python bot.py --vps-operations-readiness-report
python scripts\verify_repo_safety.py
```

Scheduling any command should be treated as a separate reviewed task. A command
being listed here does not mean it is approved for automatic scheduling today.

## Hermes Cron Plan For Market Monitor Only

Once Hermes is running on the VPS, Hermes cron is preferred for
monitoring-only, chat-delivered market monitor reports. Windows Task Scheduler
may still be used only to start or keep the Hermes gateway running on boot, not
for execution-capable trading commands.

Use no-agent mode for deterministic commands where possible. The candidate
future scheduled command is:

```bat
cd /d C:\dev\paper-trading-bot
.venv\Scripts\python.exe bot.py --refresh-market-monitor
```

This command is a future scheduling candidate only. It is not approved for
scheduling yet, and it does not approve orders or paper execution.

Prerequisites before any scheduling review:

```powershell
python scripts\verify_repo_safety.py
python bot.py --market-monitor-scheduling-readiness-report
python bot.py --vps-operations-readiness-report
python bot.py --refresh-market-monitor
```

Only continue to a separate scheduling review after the manual VPS refresh run
succeeds and generated CSV/cache files remain ignored by git.

Stop if any candidate schedule tries to load `config.json`, call Alpaca, read
positions, write SQLite `trade_log`, send Discord alerts, create orders, or
approve execution.

## Commands Never To Schedule Automatically

Do not schedule:

```powershell
python bot.py
python bot.py --paper-order-test ... --confirm-paper-order
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

Also do not schedule:

- Any future execution command.
- Any command that submits, cancels, or creates orders.
- Any command that writes SQLite `trade_log` rows as part of an execution path.
- Any command that mutates positions.
- Any command that bypasses preview, risk checks, or explicit manual review.

## Update Workflow

When updating the VPS copy later:

```powershell
git pull
python scripts\verify_repo_safety.py
python bot.py --deployment-readiness-report
```

Then run the relevant verifier for the area being changed. Only after those
checks pass should safe report, preview, or display commands be run manually.

## Troubleshooting

- Git not recognised: install Git for Windows, restart the terminal, and confirm
  `git --version` works.
- Python not recognised: install Python 3.11+, enable PATH during install, or
  use the full Python path.
- Virtual environment activation issue: run PowerShell as a normal user and, if
  needed, review the local execution policy for script activation.
- Missing package: activate `.venv`, then rerun
  `python -m pip install -r requirements.txt`.
- Alpaca credential issue: confirm `config.json` exists locally and contains
  paper credentials only. Do not print or paste the values.
- yfinance or network issue: check VPS firewall, DNS, outbound HTTPS access, and
  whether the data provider is temporarily unavailable.
- Discord webhook issue: confirm webhook presence locally if alerts are needed,
  but do not paste the webhook into logs or chat.
- OneDrive or Git object lock issue: keep the VPS repo outside OneDrive or other
  synced folders.

## Current Non-Goals

- No loop mode.
- No automatic execution.
- No crypto execution.
- No short execution.
- No live trading.
- No automatic scheduling of execution-capable commands.

## References

- `docs/CURRENT_STATE.md` is the current project handoff and research state.
- `docs/CODEX_WORKFLOW.md` describes Codex task safety and prompt structure.
- `docs/V2_REFACTOR_INVENTORY.md` lists extracted modules and high-risk areas.
- `python bot.py --deployment-readiness-report` checks local deployment
  readiness without deploying.
- `python scripts\verify_repo_safety.py` checks for dangerous tracked or staged
  files before commits.
