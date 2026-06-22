# Risk Controls Checklist — "before real money"

**Read this first:** The bot is currently **paper-only and should stay that way** until *every* box below is checked, reviewed, and tested. Paper-only is not the same as safe — it just means a bug costs nothing today. The moment real capital is involved, the missing controls below are how an account blows up.

This is the gap between "a paper bot that works" and "a system you'd trust with money." Nothing here exists yet.

---

## Tier 1 — Non-negotiable (must exist before live is even discussed)

- [ ] **Position sizing that isn't a flat 1 share.** Today `order_quantity` is a fixed integer (1 in the example config). Real sizing should be a function of account equity and per-trade risk (e.g. risk a fixed % of equity per position, sized off the stop distance).
- [ ] **Per-symbol notional cap.** No single position may exceed X% of equity (e.g. 5–10%).
- [ ] **Max concurrent positions / total exposure cap.** Bound how much of the account can be deployed at once.
- [ ] **Buying-power check before every order.** Query account buying power and reject orders that would exceed it. (Alpaca exposes this on the account object.)
- [ ] **Oversell/overbuy guard on *every* path.** Currently only the normal strategy path clamps; the manual path does not (finding **F3**). The order gateway in `REFACTOR_PLAN.md` centralises this.
- [ ] **Account-level kill switch.** A single check that halts all order submission when tripped — wired into the order gateway so no path can bypass it (finding **F1**).
- [ ] **Daily loss limit.** If realised+unrealised P&L for the day breaches `-X%`, stop trading for the day.
- [ ] **Max drawdown stop.** If equity falls `X%` from peak, halt and require manual re-enable.

## Tier 2 — Strongly recommended

- [ ] **Stop-loss on every position.** The strategy has no exit on adverse moves beyond the MA crossover. Add a hard stop (bracket order or monitored stop).
- [ ] **Fill confirmation before recording state.** Don't mark a position open until the fill is confirmed (finding **F4**). The gateway does this once for all paths.
- [ ] **Max orders per run / per day.** Rate-limit to contain runaway loops or bad signals.
- [ ] **Slippage & cost modelling in live sizing**, not just backtests — so live decisions account for real costs.
- [ ] **Reconciliation step.** At the start of each run, compare local SQLite state against Alpaca's actual positions and alert on any mismatch.

## Tier 3 — Operational safety

- [ ] **Structured alerting on every order, rejection, and guard trip** (Discord already exists — extend it).
- [ ] **A documented manual "panic" procedure** — how to flatten everything and disable the bot fast.
- [ ] **Audit log** of every decision + order with the inputs that produced it (partly covered by the SQLite `trade_log`).
- [ ] **Dry-run parity test** — prove dry-run and live take identical decisions on the same inputs, so dry-run is a faithful rehearsal.

---

## How to think about "going live"

Suggested staged path, each stage gated on the previous behaving for a sustained period:

1. **Paper, fixed 1 share** (today) → prove plumbing and signals.
2. **Paper, real sizing + all Tier-1 controls** → prove the risk layer behaves.
3. **Live, tiny fixed size** (money you'd shrug off losing) → prove paper↔live parity.
4. **Live, real sizing** → only after weeks of stage 3 with no surprises.

Do **not** skip stage 3. Paper fills are optimistic; the first thing real money teaches you is that fills, partial fills, and rejections behave differently.

> Honest framing for the conversation: the *strategy* (SMA crossover with a regime + vol filter) is a reasonable, well-understood starting point — but it is not an edge by itself. The risk controls above matter far more to the outcome than the entry signal does.
