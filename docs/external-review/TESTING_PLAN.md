# Testing Plan — real tests for the money-touching code

**Problem:** There is no `tests/`, no `pytest`, no CI. The 169 `scripts/verify_*.py` files are standalone assertion scripts run by hand — useful for workflow checks, but they do **not** test broker/order behaviour with mocked responses, and they don't run automatically.

**Goal:** A small `pytest` suite that pins the exact logic that can move money, so the bugs in `REVIEW.md` can't regress and the refactor can proceed safely.

This doc is a plan + ready-to-drop-in starter code. It does not modify the bot.

---

## Setup

```bash
pip install pytest
mkdir tests
```

Add to `requirements.txt` (dev) or a new `requirements-dev.txt`:

```
pytest>=8.0
```

Optional `pytest.ini` in the repo root:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

Run with: `pytest -q`

---

## Priority 1 — Pure logic (no mocks needed, highest value/effort ratio)

`trading_bot/execution.py:decide_trade` and `trading_bot/positions.py` are pure functions. Test them exhaustively first.

```python
# tests/test_decide_trade.py
from decimal import Decimal
from trading_bot.execution import decide_trade
from trading_bot.positions import Position
from trading_bot.strategies.sma import SIGNAL_BUY, SIGNAL_SELL, SIGNAL_HOLD

def test_buy_from_flat_opens_long():
    d = decide_trade(SIGNAL_BUY, Position(Decimal("0")), allow_shorting=False, configured_quantity=1)
    assert d.should_trade and d.action == "open_long" and d.trade_quantity == Decimal("1")

def test_long_only_will_not_short_on_sell_when_flat():
    d = decide_trade(SIGNAL_SELL, Position(Decimal("0")), allow_shorting=False, configured_quantity=1)
    assert not d.should_trade

def test_sell_cannot_oversell_a_long():
    # holding 1, configured to sell 5 -> close at most 1, never go negative
    d = decide_trade(SIGNAL_SELL, Position(Decimal("1")), allow_shorting=False, configured_quantity=5)
    assert d.trade_quantity == Decimal("1")
    assert d.position_after.quantity == Decimal("0")

def test_hold_never_trades():
    assert not decide_trade(SIGNAL_HOLD, Position(Decimal("0")), False, 1).should_trade
```

Also test `qqq100_alignment_action` (finding **F2**) — write the test for the *intended* behaviour (exactly 0 or 1 share) so it fails today and passes after the fix:

```python
# tests/test_qqq100_alignment.py
from decimal import Decimal
from trading_bot.positions import Position
from trading_bot.safety.qqq100_paper_execution import qqq100_alignment_action
from trading_bot.positions import POSITION_LONG, POSITION_FLAT

def test_flat_target_with_excess_long_should_not_leave_a_residual():
    # holding 3, target flat -> must end at 0, not 2 (documents F2; expected to fail until fixed)
    action, side = qqq100_alignment_action(POSITION_FLAT, Position(Decimal("3")))
    assert side == "sell"
    # after the fix this should close the whole position, not just 1 share
```

## Priority 2 — Order paths with a mocked Alpaca client

Use a fake `TradingClient` so no network/account is touched. This is where findings **F1, F3, F4** get locked down (best done *after* the order gateway from `REFACTOR_PLAN.md` exists, since then there's a single function to test).

```python
# tests/conftest.py
import pytest
from decimal import Decimal

class FakeOrder:
    def __init__(self, id="ord_1", status="filled", qty="1", filled_qty="1", side="buy"):
        self.id, self.status, self.qty, self.filled_qty, self.side = id, status, qty, filled_qty, side

class FakeTradingClient:
    """Records calls; returns scripted responses. Never hits the network."""
    def __init__(self, open_orders=None, asset=None, order_result=None):
        self._open_orders = open_orders or []
        self._asset = asset
        self._order_result = order_result or FakeOrder()
        self.submitted = []
    def get_orders(self, filter=None): return list(self._open_orders)
    def get_asset(self, ticker): return self._asset
    def get_order_by_id(self, oid): return self._order_result
    def submit_order(self, order_data=None):
        self.submitted.append(order_data)
        return self._order_result

@pytest.fixture
def fake_client():
    class Asset:  # tradable US equity by default
        asset_class = "us_equity"; tradable = True; shortable = True
    return FakeTradingClient(asset=Asset())
```

Cases the mocked suite must cover:

| Test | Guards finding |
|---|---|
| Submitting an order when an open order already exists is **skipped** | existing guard |
| Closing more than the held quantity is **rejected** (oversell) on *every* path incl. manual | **F3** |
| A `rejected`/`canceled` order does **not** update recorded position state | **F4** |
| A `partially_filled` order records only the filled qty | **F4** |
| Kill-switch disabled ⇒ normal run submits **no** orders once gateway lands | **F1** |
| Duplicate action within one run is skipped | existing guard |
| Non-tradable / non-equity asset is rejected | existing guard |

## Priority 3 — Config & safety validation

```python
# tests/test_config_safety.py
import pytest
from trading_bot.config import validate_config, ConfigError
# build an AppConfig with alpaca_paper=False -> must raise
def test_live_mode_is_rejected(make_config):
    with pytest.raises(ConfigError):
        validate_config(make_config(alpaca_paper=False))
```

(Use a small `make_config` factory fixture so tests don't depend on a real `config.json`.)

---

## Stretch — CI

A minimal GitHub Actions workflow so tests run on every push:

```yaml
# .github/workflows/tests.yml
name: tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt pytest
      - run: pytest -q
```

---

## Suggested first session for your brother

1. `pip install pytest`, create `tests/`, drop in `test_decide_trade.py` above. Get green.
2. Add the `qqq100` test — watch it fail, then fix F2, watch it pass. (This is the satisfying loop that teaches why tests matter.)
3. Add `conftest.py` + one mocked-order test once the gateway exists.

That's enough to make the codebase safe to change — which is the whole point.
