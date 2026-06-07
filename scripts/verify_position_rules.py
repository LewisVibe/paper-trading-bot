from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.execution import decide_trade
from trading_bot.positions import Position
from trading_bot.strategies.sma import SIGNAL_BUY, SIGNAL_HOLD, SIGNAL_SELL


@dataclass
class ExpectedDecision:
    name: str
    signal: str
    start_qty: Decimal
    allow_shorting: bool
    order_qty: Decimal
    should_trade: bool
    side: str
    action: str
    trade_qty: Decimal
    after_qty: Decimal


def assert_decision(case: ExpectedDecision) -> list[str]:
    decision = decide_trade(
        signal=case.signal,
        position_before=Position(case.start_qty),
        allow_shorting=case.allow_shorting,
        configured_quantity=float(case.order_qty),
    )

    failures: list[str] = []
    checks = [
        ("should_trade", decision.should_trade, case.should_trade),
        ("side", decision.side, case.side),
        ("action", decision.action, case.action),
        ("trade_quantity", decision.trade_quantity, case.trade_qty),
        ("position_after.quantity", decision.position_after.quantity, case.after_qty),
    ]
    for field_name, actual, expected in checks:
        if actual != expected:
            failures.append(
                f"{case.name}: expected {field_name}={expected!r}, got {actual!r}"
            )
    return failures


def main() -> int:
    cases = [
        ExpectedDecision(
            "long_only flat BUY opens long",
            SIGNAL_BUY,
            Decimal("0"),
            False,
            Decimal("5"),
            True,
            "buy",
            "open_long",
            Decimal("5.0"),
            Decimal("5.0"),
        ),
        ExpectedDecision(
            "long_only flat SELL skips",
            SIGNAL_SELL,
            Decimal("0"),
            False,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("0"),
        ),
        ExpectedDecision(
            "long_only long SELL closes long",
            SIGNAL_SELL,
            Decimal("5"),
            False,
            Decimal("5"),
            True,
            "sell",
            "close_long",
            Decimal("5.0"),
            Decimal("0.0"),
        ),
        ExpectedDecision(
            "long_only long BUY skips pyramiding",
            SIGNAL_BUY,
            Decimal("5"),
            False,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("5"),
        ),
        ExpectedDecision(
            "long_only short BUY skips",
            SIGNAL_BUY,
            Decimal("-5"),
            False,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("-5"),
        ),
        ExpectedDecision(
            "long_only short SELL skips",
            SIGNAL_SELL,
            Decimal("-5"),
            False,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("-5"),
        ),
        ExpectedDecision(
            "shorting flat BUY opens long",
            SIGNAL_BUY,
            Decimal("0"),
            True,
            Decimal("5"),
            True,
            "buy",
            "open_long",
            Decimal("5.0"),
            Decimal("5.0"),
        ),
        ExpectedDecision(
            "shorting flat SELL opens short",
            SIGNAL_SELL,
            Decimal("0"),
            True,
            Decimal("5"),
            True,
            "sell",
            "open_short",
            Decimal("5.0"),
            Decimal("-5.0"),
        ),
        ExpectedDecision(
            "shorting long SELL closes long",
            SIGNAL_SELL,
            Decimal("5"),
            True,
            Decimal("5"),
            True,
            "sell",
            "close_long",
            Decimal("5.0"),
            Decimal("0.0"),
        ),
        ExpectedDecision(
            "shorting long BUY skips pyramiding",
            SIGNAL_BUY,
            Decimal("5"),
            True,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("5"),
        ),
        ExpectedDecision(
            "shorting short BUY closes short",
            SIGNAL_BUY,
            Decimal("-5"),
            True,
            Decimal("5"),
            True,
            "buy",
            "close_short",
            Decimal("5.0"),
            Decimal("0.0"),
        ),
        ExpectedDecision(
            "shorting short SELL skips pyramiding",
            SIGNAL_SELL,
            Decimal("-5"),
            True,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("-5"),
        ),
        ExpectedDecision(
            "HOLD never creates order action",
            SIGNAL_HOLD,
            Decimal("0"),
            True,
            Decimal("5"),
            False,
            "",
            "",
            Decimal("0"),
            Decimal("0"),
        ),
        ExpectedDecision(
            "close long caps quantity to current long",
            SIGNAL_SELL,
            Decimal("2"),
            True,
            Decimal("5"),
            True,
            "sell",
            "close_long",
            Decimal("2"),
            Decimal("0"),
        ),
        ExpectedDecision(
            "close short caps quantity to current short",
            SIGNAL_BUY,
            Decimal("-2"),
            True,
            Decimal("5"),
            True,
            "buy",
            "close_short",
            Decimal("2"),
            Decimal("0"),
        ),
    ]

    failures: list[str] = []
    for case in cases:
        failures.extend(assert_decision(case))

    if failures:
        print("Position-rule verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Position-rule verification passed ({len(cases)} cases).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
