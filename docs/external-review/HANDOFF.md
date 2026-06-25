# Handoff — where we left off (2026-06-23)

Quick summary of the review + changes, what's merged, what's still open, and the one finding that matters most for how you work on this going forward.

## What shipped (both merged)

- **PR #1** — external review + improvement plans (`docs/external-review/`: REVIEW, REFACTOR_PLAN, RISK_CONTROLS_CHECKLIST, TESTING_PLAN).
- **PR #2** — the critical safety fixes, in-place:
  - **F1** — normal `python bot.py` is now **monitoring-only**. It computes signals, logs intended actions as `monitor_only`, writes trade-log rows, alerts — but **never submits an order**. Only the dedicated, explicitly-confirmed commands (`--paper-order-test`, `--execute-slow-sma-paper`, QQQ100) place paper orders.
  - **F3** — manual `--paper-order-test sell` now refuses to oversell a long (when `allow_shorting` is false).
  - **F5** — `paper_kill_switch_enabled` is now a real config field (config or `PAPER_KILL_SWITCH_ENABLED`).
  - Plus a small `pytest` suite (32 tests) for the order-decision logic and the new config field.

## ⚠️ Please run the full verifier suite yourself

The fixes were validated with `pytest`, `py_compile`, and the static verifiers — **but the full `scripts/verify_*` suite needs `pandas`/`yfinance` and your `python`, which weren't available in the review environment.** Run `scripts/verify_*` and a real dry-run smoke test in your setup as the final gate. Nothing here was confirmed against the full suite.

## The finding that matters most: the codebase is welded shut

We tried to split `bot.py` (7,700 lines) and **couldn't** — not because of its size, but because **~140 of the 169 `verify_*` scripts read `bot.py`'s source text directly and assert specific functions/imports stay exactly where they are** (`run_paper_order_test`, `TradingClient(`, `submit_alpaca_order(`, the Alpaca imports, etc.).

That means **any structural change trips a tripwire.** The verify-scripts were meant to make changes *safer*; compounded over ~169 of them, they've made the code **un-refactorable**. We hit this twice — a clean "single order gateway" design broke 3+ verifiers, so we reverted it for the smaller in-place fixes that are now merged.

**The lesson:** verify **behaviour**, not **source text**. A test that says "a sell larger than the position is rejected" survives refactoring. A test that greps for `submit_alpaca_order(` inside a specific block freezes the file forever. If you want to be able to split `bot.py` later, the verify-scripts have to move from checking *structure* to checking *behaviour* first — otherwise the structure is the spec.

## Why splitting `bot.py` is still worth doing eventually

A 7,700-line file is one giant room with no internal walls — nothing's separated, you can't change one part without risking another, and anyone (or any AI agent) opening it gets the whole thing dumped on them at once instead of just the 200 lines that matter. Agents especially: the file floods their context and they edit half-blind. Splitting is just adding walls. But it can't happen until the verifiers stop pinning the source text.

## Still open (not started)

| Item | Notes |
|------|-------|
| **F2** — QQQ100 "one-share alignment" doesn't enforce one share | `qqq100_paper_execution.py` — `hold_already_long` ignores size; `sell_1` sells only one. Small fix. |
| **F6 / F7** — preview-assumes-flat; backtest portfolio accounting | From REVIEW.md; lower priority. |
| **`bot.py` split** | Blocked by the verifier coupling above — fix the verifiers first. |
| **Risk controls before real money** | See RISK_CONTROLS_CHECKLIST.md. None exist yet (no sizing, stops, drawdown limits). Mandatory before live. |

## Suggested next step

If you want one concrete improvement: **convert a handful of the structural `verify_*` scripts to behaviour tests** (using the `pytest` pattern already added in `tests/`). That's the unlock — once structure isn't frozen, the `bot.py` split becomes possible, and everything else gets easier to change.
