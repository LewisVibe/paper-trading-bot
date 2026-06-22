# Refactor Plan — taming `bot.py`

**Goal:** Finish the V2 migration so `bot.py` becomes a thin CLI, and route **every** order through one gateway. This is the structural fix for finding **F1** (normal path bypasses the kill-switch).

**Hard constraint (from `PROJECT_CONTEXT.md`):** preserve all existing commands and behaviour. Refactor moves code; it must not change what the commands do. Paper-only and once-per-command behaviour stay.

**Approach:** small, reviewable steps, each independently runnable. Don't try to do it in one big rewrite — that's how working behaviour gets lost.

---

## Target structure

```
bot.py                      # thin: parse args -> dispatch to a runner. Aim < 300 lines.
trading_bot/
  cli/
    __init__.py
    dispatch.py             # maps flags -> runner functions (the 216-flag table)
  broker/
    gateway.py              # THE single order gateway (see below)
    alpaca_client.py        # (already exists) raw Alpaca calls, paper=True
  execution/
    normal_run.py           # process_ticker / run_bot live here
    manual_order.py         # --paper-order-test
    slow_sma.py             # --execute-slow-sma-paper
    qqq100.py               # QQQ100 path
  research/                 # (already exists) backtests, previews, reports
  reporting/                # CSV writers, summaries, Discord formatting
  config.py positions.py strategies/ safety/   # (already exist, keep)
```

`bot.py` ends up: read argv → `cli.dispatch.run(argv)` → done.

---

## The order gateway (do this first — it fixes F1)

Today, 4 paths submit orders independently and only some pass the kill-switch. Replace all direct `submit_alpaca_order(...)` calls with one chokepoint:

```python
# trading_bot/broker/gateway.py
@dataclass(frozen=True)
class OrderRequest:
    ticker: str
    side: str            # "buy" | "sell"
    quantity: Decimal
    action: str          # open_long | close_long | open_short | close_short
    source: str          # "normal" | "manual" | "slow_sma" | "qqq100"
    confirmed: bool      # explicit --confirm-* flag for this path

def submit_order(client, config, req: OrderRequest, *, current_position: Position) -> OrderResult:
    # 1. paper-only assertion (defence in depth; config already enforces it)
    # 2. kill-switch gate  -> evaluate_paper_kill_switch_gate(...)   <-- now ALL paths
    # 3. oversell/overbuy guard: closes cannot exceed current_position.abs_quantity   (fixes F3)
    # 4. open-order / duplicate-action check
    # 5. asset validation (tradable, shortable-if-needed)
    # 6. submit via alpaca_client, then refresh_order_status BEFORE returning  (fixes F4)
    # 7. return OrderResult(order_id, confirmed_status, filled_qty, position_after)
```

Every execution path constructs an `OrderRequest` and calls `submit_order`. The kill-switch, oversell guard, and fill-confirmation now apply **uniformly** — F1, F3, and F4 are fixed by construction, not by remembering to add a check in each path.

---

## Phases

### Phase 0 — Safety net (before moving any code)
- [ ] Add the test scaffolding from `TESTING_PLAN.md` and write **characterization tests** for current behaviour of the 4 order paths (mocked Alpaca). These tests are the contract: refactor must keep them green.
- [ ] `pip freeze > requirements.lock.txt` so the environment is reproducible during the refactor.

### Phase 1 — Order gateway (fixes F1, F3, F4)
- [ ] Create `trading_bot/broker/gateway.py` with `submit_order` as above.
- [ ] Route the **normal** path through it first; confirm characterization tests still pass.
- [ ] Route manual, slow-SMA, and QQQ100 through it. Delete the now-duplicated guard code in each.
- [ ] Confirm the kill-switch now gates the normal run (F1 closed).

### Phase 2 — Extract execution runners
- [ ] Move `run_bot` / `process_ticker` → `trading_bot/execution/normal_run.py`.
- [ ] Move manual / slow-SMA / QQQ100 paths into their own modules under `execution/`.
- [ ] `bot.py` imports and calls them; behaviour unchanged.

### Phase 3 — Extract CLI dispatch
- [ ] Move the flag→function routing into `trading_bot/cli/dispatch.py`.
- [ ] Reduce `bot.py` to argv → dispatch. Target < 300 lines.

### Phase 4 — Extract reporting
- [ ] Move CSV writers, summary builders, Discord formatting → `trading_bot/reporting/`.

### Phase 5 — Fix the medium bugs + clean up
- [ ] **F2:** make `qqq100_alignment_action` enforce exactly 0 or 1 share (sell *all* excess to reach target, or block if >1 and that's disallowed).
- [ ] **F5:** load `paper_kill_switch_enabled` into `AppConfig`, or remove the dead reference.
- [ ] **F6:** previews must surface "positions unknown" loudly, never silently assume flat.
- [ ] **F7:** fix backtest portfolio starting-cash aggregation.
- [ ] Archive dead `scripts/verify_*` and `research/` one-offs into `archive/` (don't delete history; just get them out of the active tree).

---

## Definition of done

- `bot.py` < 300 lines; no `submit_order` call anywhere except inside `gateway.py`.
- All four order paths pass through the kill-switch + oversell guard + fill-confirmation.
- Every existing CLI command behaves identically (characterization tests prove it).
- `grep -rn "submit_alpaca_order(" bot.py trading_bot/execution` returns nothing.

> Tip for the implementer: do Phase 0 and Phase 1 and **stop**. That alone closes the critical finding and the two high-severity order bugs. Phases 2–4 are quality-of-life and can follow at any pace.
