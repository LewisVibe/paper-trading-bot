# Hermes Autonomous Paper Rebalance Cron

This is the only approved scheduled broker-write workflow. Lewis explicitly approved it on
2026-07-20 for autonomous Alpaca paper rebalancing of `QQQ`, `MGK`, `IBIT`, and `SGOV`, once
per U.S. trading day, with the existing `$100,000` cap and safety gates. Live trading remains
unsupported.

## Required Config

The private VPS `config.json` must keep:

```json
{
  "dry_run": true,
  "allow_shorting": false,
  "paper_kill_switch_enabled": true,
  "auto_paper_trading_enabled": true,
  "alpaca": {
    "paper": true
  }
}
```

Credentials and webhook values remain private and must never be printed or committed. The
checked-in example keeps `auto_paper_trading_enabled=false`, so a clone cannot trade
automatically without a separate local opt-in.

## Job Definition

- Job name: `paper-bot-auto-paper-rebalance`
- Cron expression: `5 14,15 * * 1-5`
- Scheduler timezone: keep the existing global Hermes timezone `Europe/London`; do not change it
- Working directory: `C:\dev\paper-trading-bot`
- Mode: script-only / no-agent
- Enabled toolsets: `terminal`
- Delivery: concise status to the current Telegram chat; execution outcome also goes to the
  configured Discord webhook
- Command:

```powershell
.venv\Scripts\python.exe bot.py --run-vol-targeted-growth-auto-paper
```

The existing `paper-bot-vps-status-check` monitoring job remains separate and unchanged.
The autonomous job must not run Git commands, package installation, tests, report refreshes,
or any second command.

Hermes does not expose per-job timezone, retry, or missed-run catch-up fields. The two London
hours cover both possible `10:05 America/New_York` mappings across the U.S./U.K. daylight-saving
transition gaps. The runner silently exits before broker access when a probe is outside its
10:00-10:20 New York window, so only the matching probe can reach execution safeguards. This is
one cron job, not retry behavior; the durable session lease still permits at most one rebalance.

## Runtime Gates

The command fails closed unless all of these hold:

- `auto_paper_trading_enabled=true`;
- `paper_kill_switch_enabled=true`;
- `alpaca.paper=true`;
- `allow_shorting=false`;
- local time is between 10:00 and 10:20 `America/New_York`;
- Alpaca reports the paper market open and the account active/unblocked;
- all four assets are U.S. equities, tradable, and fractionable;
- current prices are at most 15 minutes old;
- there are no open paper orders or short positions;
- unrelated holdings remain unchanged and the combined target stays unleveraged;
- cash plus conservative sell proceeds can fund buys;
- no local session state, session lease, or matching Alpaca client order ID already exists.

The command writes an exclusive date-scoped lease before broker submission. Any existing or
ambiguous lease blocks automatic retry for that session. Do not delete a lease automatically.
A partial fill, failed order, postcheck mismatch, or Discord `REVIEW REQUIRED` result requires
manual broker review and disabling this job until reconciled.

On a weekday market holiday, the command records `skipped_market_closed`, submits no orders,
and exits successfully. When all managed positions are already within the sub-dollar residual
tolerance, it records `no_action_aligned`, submits no orders, and exits successfully.

## Never Schedule

The scoped approval applies only to `--run-vol-targeted-growth-auto-paper`. Do not schedule:

- normal `python bot.py`;
- manual ticket preparation, manual ticket execution, or manual postcheck;
- paper-order smoke tests;
- QQQ100 or slow-SMA execution;
- refresh commands;
- cancellation, replacement, retry, flatten, or live-trading commands.

Do not configure automatic retries. A future change to symbols, weights, capital cap, schedule,
strategy logic, order behavior, or live/paper boundary requires a new explicit approval.
