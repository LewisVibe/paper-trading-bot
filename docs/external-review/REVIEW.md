# Code Review — paper-trading-bot

**Reviewer:** Austin (external, on request)
**Date:** 2026-06-22
**Method:** Manual read of core paths + an independent automated review (OpenAI Codex gpt-5.5, read-only). Findings below were cross-checked against the source; every bug claim was verified at the cited `file:line`.
**Scope:** Read-only review. No code in the bot was changed.

---

## TL;DR

This is genuinely impressive **safety-first** engineering for a learning project — the paper-only lockdown, secrets hygiene, and trade-decision logic are better than most hobby bots. Two structural problems hold it back:

1. **`bot.py` is a 7,774-line god-file (216 CLI flags).** That sprawl is *directly* why the newer kill-switch safety layer misses the main order path — safety logic lives in 4 different places instead of one gateway.
2. **There is no real test suite** for the exact code that touches money (order accounting, oversell prevention, fills/rejects). The 169 `scripts/verify_*.py` files are useful workflow assertions but are **not** unit tests.

Verdict: solid foundation, real intent, but **don't treat it as reliable** until order handling is centralised, the verified bugs below are fixed, and broker-behaviour tests exist.

---

## What it does

A Python market-monitoring and paper-trading bot (runs once per command, not a daemon):

1. Pull price history via **yfinance**
2. Compute a signal — a **regime-filtered SMA + volatility** strategy (MA crossover, only trades above a long-term trend and below a volatility gate)
3. Translate signal → trade decision (open/close long; optional short, off by default)
4. Submit **market orders to Alpaca paper account only**, log to **SQLite**, alert via **Discord**

Plus a large research surface: backtesting, strategy comparison, parameter sweeps, stress tests, and preview modes. Non-core execution is gated behind explicit `--confirm-*` flags.

## How it's structured

| Area | Size | Notes |
|---|---|---|
| `bot.py` | **7,774 lines, 216 flags** | Entry point + order submission + backtests + previews + reporting |
| `trading_bot/` core | ~3,900 lines | Partial V2 refactor: `config.py`, `execution.py`, `positions.py`, `alpaca_client.py`, `strategies/`, `safety/` — clean and well-factored |
| `trading_bot/research/` | **~69,000 lines, 137 files** | Backtest/research scaffolding |
| `scripts/` | **~39,000 lines, 169 files** | Hand-rolled `verify_*` check scripts (not a test suite) |

The actual *bot* is a few thousand lines; there are **~108,000 lines of research + verification scaffolding** around it.

---

## What's good (keep doing this)

- ✅ **Paper-only enforced in depth.** All 6 `TradingClient(...)` calls are hardcoded `paper=True`, *and* `config.py:370` refuses to start if `alpaca.paper` isn't true. Belt and suspenders.
- ✅ **Secrets handled correctly.** `config.json`, `.env`, `*.db`, `*.log` gitignored; keys load from config-or-env; nothing sensitive committed (verified). Discord failures are redacted (`discord_alerts.py:20`).
- ✅ **Real order guards** in the normal path: asset validation (`alpaca_client.py:82`), within-run duplicate-action dedup, and an open-order check that blocks a duplicate order and reserves closeable quantity (`bot.py:1605–1653`).
- ✅ **Clean, pure decision logic.** `execution.py:decide_trade` handles long/short/flat transitions with `min(qty, position)` clamping so it can't oversell *in that path*.
- ✅ **No unsafe `eval` / `exec` / `pickle`** in the bot or package.
- ✅ **A dedicated, pure, side-effect-free kill-switch** module (`safety/paper_kill_switch.py`).

---

## Findings (severity-ranked, all verified)

### 🔴 Critical

**F1 — The normal `python bot.py` path bypasses the kill-switch.**
The newer `paper_kill_switch` gate is only wired into *special* commands (manual order test `bot.py:1842`, slow-SMA `bot.py:4548`, QQQ100). The everyday strategy path `process_ticker → submit_alpaca_order` (`bot.py:1666`) submits paper orders with only the older guards. The README itself notes normal-bot protection is "future work" (`README.md:705`). The safety story is therefore **partial, not platform-wide**. This is the headline issue and the clearest symptom of the god-file problem.

### 🟠 High

**F2 — QQQ100 "one-share alignment" does not enforce one share.** `trading_bot/safety/qqq100_paper_execution.py:291` (`qqq100_alignment_action`). Verified: if "long" is desired and *any* long exists, it returns `hold_already_long` (ignores size); if "flat" is desired it sells **exactly 1** even if more is held. Contradicts the documented "max one share, no scaling" boundary (`README.md:1716`).

**F3 — Manual `--paper-order-test sell` can oversell into a short.** `bot.py:1970`. Verified: validates the asset with `requires_shortable=False` and submits the sell **without checking the account holds enough long shares to close**. Directly violates the project's own rule "closing trades must not oversell or overbuy" (`PROJECT_CONTEXT.md:106`). Gated behind `--confirm-paper-order` and paper-only, so low blast radius — but a genuine logic gap, and exactly the kind of thing that bites later.

**F4 — Optimistic position accounting in the normal path.** `bot.py:1683`. The normal path records `position_after` from the order *status at submit time*, before confirming the fill — and unlike the manual/slow-SMA paths, it does **not** call `refresh_order_status`. Rejected / pending / partial / cancelled orders produce misleading state. Inconsistent with the safer paths that already do this right.

### 🟡 Medium

**F5 — `paper_kill_switch_enabled` is dead config.** Referenced via `getattr(config, "paper_kill_switch_enabled", None)` (`bot.py:4553`) but **never loaded into `AppConfig`** (`config.py:56`), and `load_config` drops unknown keys (`config.py:315`). The gate requires it `True` (`paper_kill_switch.py:54`), so those paths are effectively blocked forever until the code changes. Either load the key or remove the dead reference.

**F6 — Previews can silently assume a flat account.** Slow-SMA action preview returns `{}` / `simulated_flat` when Alpaca keys are missing/unreadable (`bot.py:4357`), then proposes opening longs from fake-flat state. Execution re-reads Alpaca, but the preview UX is easy to misread. Surface "positions unknown" loudly instead of defaulting to flat.

**F7 — Backtest portfolio accounting is internally inconsistent.** Per-ticker backtests use `position_size_dollars` as each ticker's starting cash (`research/backtesting.py:230`), so portfolio-level return/drawdown can be wrong unless that value happens to equal intended aggregate exposure.

### ⚪ Structural / quality

- **`bot.py` god-file** (7,774 lines / 216 flags) — root cause of F1. See `REFACTOR_PLAN.md`.
- **No real test suite** — `verify_*` scripts ≠ unit tests; the money-touching logic is untested. See `TESTING_PLAN.md`.
- **Scaffolding rot** — ~108k lines of research/verify artifacts vs a few-thousand-line bot; many are clearly one-off AI-session outputs (e.g. `verify_codex_ambitious_split_drawdown_validation.py`). Archive or delete dead ones.
- **Thin risk controls** — flat `order_quantity` only; no max exposure / drawdown / buying-power checks. See `RISK_CONTROLS_CHECKLIST.md`.
- **Dependencies** pinned only to broad ranges (`requirements.txt`); consider a lockfile for reproducibility.

---

## Recommended order of work

1. **F1 + the refactor's "order gateway"** — fixes the critical safety gap structurally (see `REFACTOR_PLAN.md`).
2. **F2, F3, F4** — concrete correctness bugs, each small and well-localised.
3. **`TESTING_PLAN.md`** — lock the above in with mocked-Alpaca tests so they can't regress.
4. **F5, F6, F7** — cleanups.
5. **`RISK_CONTROLS_CHECKLIST.md`** — mandatory *before* any real-money consideration.

See the companion docs in this folder.
