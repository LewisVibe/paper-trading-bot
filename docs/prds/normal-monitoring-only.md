# PRD — Normal run is monitoring-only + manual oversell guard (in-place)

**Status:** Ready for implementation
**Branch:** `refactor/order-gateway` (will be reset to `main` and rebuilt with this approach)
**Supersedes:** the earlier `order-gateway.md` PRD. **Do NOT build a gateway.** The single-gateway approach broke the repo's codified safety verifiers (which pin exact execution-code structure). This PRD takes the in-place approach the repo owner asked for.

---

## Background / decision

PR review by the repo owner established the policy: **the normal `python bot.py` run must never submit orders** — only the dedicated, explicitly-confirmed execution commands (`--paper-order-test`, `--execute-slow-sma-paper`, QQQ100) may place paper orders. The repo encodes its safety contract through ~half a dozen `scripts/verify_*.py` checks that assert specific imports, per-command code structure, and "kill-switch helper limited to manual + slow-SMA". Any refactor must keep those green and must not weaken them.

## Problem (from the external review)

- **F1 (Critical):** the normal path submits paper orders when `dry_run=False`, with no kill-switch and outside the dedicated-command policy.
- **F3 (High):** the manual `--paper-order-test sell` path submits a sell without checking the account holds enough long shares, so it can open a short — violating "closing trades must not oversell or overbuy" (`PROJECT_CONTEXT.md`).
- **F5 (Medium):** `paper_kill_switch_enabled` is read via `getattr` but never loaded into `AppConfig`.

(F4 — optimistic position accounting — is resolved for the normal path by making it non-executing; the manual and slow-SMA paths already call `refresh_order_status` and already clamp closes, so they need no change.)

## Goal

Minimal, structure-preserving in-place changes that fix F1, F3, F5 while keeping every currently-green verifier green.

## Non-goals

- No order gateway. No moving imports out of `bot.py`. No changes to the QQQ100, slow-SMA, or manual command *structure* beyond the specific F3 guard below.
- No `bot.py` package split, no risk-sizing, no crypto/loop/live.
- F2/F6/F7 not in scope.
- Do not modify `scripts/verify_*` or `trading_bot/research/*`.

---

## Required changes

### 1. Normal run → monitoring-only (F1)

In `process_ticker` (`bot.py`), the normal run must **never** call `submit_alpaca_order` / submit any order, regardless of `dry_run`.

- Keep: downloading prices, computing the signal, computing the `decide_trade` decision, reading current positions (read-only monitoring), logging, Discord alerts, and writing to the SQLite `trade_log`.
- Remove: the live-order submission branch for the normal path.
- When a non-HOLD signal would have traded, record it as a non-executing observation — e.g. `order_status="monitor_only"` (pick a clear, consistent label) with the intended side/action in the log and an info-level log line like "Monitoring only: would <action> <qty> <ticker> (normal run does not place orders)". Do not mutate persisted position state from a non-existent fill.
- The startup/summary Discord behaviour must be unchanged from `main` (do not suppress dry-run alerts).
- `submit_alpaca_order`, `TradingClient`, `MarketOrderRequest`, and `validate_alpaca_asset_for_order` imports MUST remain in `bot.py` (they are still used by the dedicated execution commands and are required by `verify_report_only_import_safety.py`).

### 2. Manual `--paper-order-test` oversell guard (F3)

In `run_paper_order_test` (`bot.py`), before submitting a **sell**, block the order if it would oversell:

- If `config.allow_shorting` is `False` and the sell `quantity` exceeds the current long position for the ticker, **do not submit**. Log the reason, write a `skipped` trade-log row, send a warning Discord alert, and return a non-zero exit code consistent with the other manual skip paths.
- Use the position the manual path already reads (`position_before`). Do not change the surrounding command structure: the block must still contain `validate_alpaca_asset_for_order(`, `submit_alpaca_order(`, and `refresh_order_status(` for the paths that do submit (required by the verifiers).

### 3. Keep `paper_kill_switch_enabled` in config (F5)

- Add `paper_kill_switch_enabled: bool = False` to `AppConfig` and load it in `load_config` from the top-level `paper_kill_switch_enabled` key, with `PAPER_KILL_SWITCH_ENABLED` env fallback (matching the existing key/env pattern).
- Add `"paper_kill_switch_enabled": false` to `config.example.json`.
- This makes the existing kill-switch gate (used by the dedicated execution preflights) able to actually read the flag. Do **not** wire the kill-switch into the normal path (that would violate the verifier contract).

---

## Tests (pytest, no network/yfinance dependency)

Add `tests/`, `pytest.ini`, `requirements-dev.txt` (`pytest>=8.0`). Tests must import only pure modules (`trading_bot.execution`, `trading_bot.positions`, `trading_bot.config`) — not anything requiring `yfinance`.

- `decide_trade`: exhaustive long-only + shorting cases incl. oversell clamping.
- `config`: `paper_kill_switch_enabled` defaults False, loads from config and from `PAPER_KILL_SWITCH_ENABLED`; `validate_config` rejects `alpaca_paper=False`.
- Manual oversell guard: a unit-testable helper for "is this sell an oversell given position + allow_shorting" returns block/allow correctly. (Factor the guard into a small pure function so it can be tested without Alpaca.)

`pytest -q` must pass.

---

## Acceptance criteria

- [ ] Normal `python bot.py` never submits an order (no `submit_alpaca_order` reachable from `process_ticker`); it still monitors, logs, alerts, and writes trade_log rows.
- [ ] Manual sell that would oversell a long (with `allow_shorting=False`) is blocked, not submitted.
- [ ] `paper_kill_switch_enabled` is a real `AppConfig` field loaded from config/env; `config.example.json` updated.
- [ ] `submit_alpaca_order` / `TradingClient` / `MarketOrderRequest` / `validate_alpaca_asset_for_order` imports remain in `bot.py`.
- [ ] QQQ100, slow-SMA, and manual command code structure is otherwise unchanged (their `submit_alpaca_order(` / `validate_alpaca_asset_for_order(` calls remain in their blocks).
- [ ] These previously-green static verifiers pass again: `verify_report_only_import_safety.py`, `verify_execute_qqq100_paper.py`, `verify_market_monitor_scheduling_readiness.py`.
- [ ] `pytest -q` green. `python3 -m py_compile bot.py` clean.
- [ ] Paper-only invariant intact (every `TradingClient` remains `paper=True`).

## Constraints

- Paper-only software. No live trading, ever.
- Keep the diff small and structure-preserving. The whole point of this approach is to respect the repo's codified safety contract.
