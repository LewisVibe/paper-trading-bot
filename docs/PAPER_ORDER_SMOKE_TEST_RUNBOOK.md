# Manual Paper-Order Smoke-Test Runbook

This runbook prepares a future tiny Alpaca paper-order smoke test for manual
review. It does not approve the order, does not schedule anything, does not
connect strategy outputs to execution, and does not approve live trading.

## Scope

- Proposed manual template only: AAPL buy 1.
- Paper-only project boundary: live trading is out of scope.
- `dry_run` defaults true.
- `alpaca.paper` must remain true.
- `allow_shorting` defaults false.
- `execution_approved=false`
- `scheduling_approved=false`
- `followup_order_approved=false`
- No second order without manual review.

## Before Market Open

Run safe checks only:

```powershell
.venv\Scripts\python.exe scripts\verify_repo_safety.py
.venv\Scripts\python.exe scripts\verify_command_inventory.py
.venv\Scripts\python.exe bot.py --paper-order-smoke-test-readiness-pack
.venv\Scripts\python.exe bot.py --paper-order-smoke-test-live-preflight --ticker AAPL --side buy --quantity 1
```

Do not run an order outside market hours. Do not use normal `python bot.py`.
Do not run slow SMA paper execution. Do not schedule execution-capable commands.

## Near Or During US Regular Market Hours

Run the confirmed read-only live preflight only when manually reviewed:

```powershell
.venv\Scripts\python.exe bot.py --paper-order-smoke-test-live-preflight --ticker AAPL --side buy --quantity 1 --confirm-readonly-alpaca-check
```

Only if `market_status=open` and
`live_preflight_ready_for_manual_confirmation`, manually review the separate
paper-order smoke-test command. The order command remains high-risk/manual-only.
This is not strategy automation and not scheduling approval.

## After A Separately Approved Tiny Manual Paper Order

Run the confirmed read-only postcheck:

```powershell
.venv\Scripts\python.exe bot.py --paper-order-smoke-test-postcheck --ticker AAPL --side buy --quantity 1 --confirm-readonly-alpaca-check
```

Review the matching recent order status summary, open order summary, and position
summary. Do not submit any follow-up order without manual review.

## Interpretation

- Market closed: wait.
- Market open but preflight blocked: stop.
- Order queued or open after smoke test: do not submit another order; use
  postcheck/manual review.
- Order filled: record it as a connectivity/order-path smoke test only, not
  strategy success.
- Order rejected, cancelled, or expired: investigate; do not retry blindly.
- No matching order found in postcheck: investigate terminal output and saved
  postcheck.
- Any missing config, secret, credential, or safety issue: stop.

## Safety Reminders

- AAPL buy 1 is a proposed manual template only.
- This is not strategy execution.
- This is not automation.
- This is not cron.
- This is not live trading.
- No order execution is approved by this runbook.
- No scheduling is approved by this runbook.
- No follow-up order is approved by this runbook.
