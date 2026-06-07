from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.costs import (
    CostModel,
    adjusted_buy_fill_price,
    adjusted_sell_fill_price,
    calculate_bps_cost,
    calculate_fixed_commission_cost,
    calculate_notional_value,
    calculate_total_estimated_trade_cost,
)


def check(name: str, actual, expected) -> list[str]:
    if actual != expected:
        return [f"{name}: expected {expected!r}, got {actual!r}"]
    return []


def main() -> int:
    failures: list[str] = []

    zero_model = CostModel()
    failures.extend(check("zero notional cost", calculate_total_estimated_trade_cost(zero_model, 100, 2), Decimal("0")))
    failures.extend(check("zero buy price", adjusted_buy_fill_price(100, zero_model), Decimal("100")))
    failures.extend(check("zero sell price", adjusted_sell_fill_price(100, zero_model), Decimal("100")))

    fixed_model = CostModel(commission_per_trade=Decimal("1.25"))
    failures.extend(check("fixed commission", calculate_fixed_commission_cost(fixed_model), Decimal("1.25")))
    failures.extend(check("fixed total cost", calculate_total_estimated_trade_cost(fixed_model, 100, 2), Decimal("1.25")))

    bps_model = CostModel(commission_bps=Decimal("10"))
    failures.extend(check("notional", calculate_notional_value(100, 2), Decimal("200")))
    failures.extend(check("bps commission", calculate_bps_cost(Decimal("200"), Decimal("10")), Decimal("0.2")))
    failures.extend(check("bps total cost", calculate_total_estimated_trade_cost(bps_model, 100, 2), Decimal("0.2")))

    spread_slippage_model = CostModel(spread_bps=Decimal("5"), slippage_bps=Decimal("10"))
    failures.extend(
        check(
            "spread and slippage cost",
            calculate_total_estimated_trade_cost(spread_slippage_model, 100, 2),
            Decimal("0.3"),
        )
    )
    buy_price = adjusted_buy_fill_price(100, spread_slippage_model)
    sell_price = adjusted_sell_fill_price(100, spread_slippage_model)
    if buy_price <= Decimal("100"):
        failures.append(f"buy adjusted price should be above raw price, got {buy_price!r}")
    if sell_price >= Decimal("100"):
        failures.append(f"sell adjusted price should be below raw price, got {sell_price!r}")

    slippage_only_model = CostModel(slippage_bps=Decimal("25"))
    raw_price = Decimal("123.45")
    old_buy_fill = raw_price * (Decimal("1") + Decimal("25") / Decimal("10000"))
    old_sell_fill = raw_price * (Decimal("1") - Decimal("25") / Decimal("10000"))
    failures.extend(
        check(
            "slippage-only buy fill equivalence",
            adjusted_buy_fill_price(raw_price, slippage_only_model),
            old_buy_fill,
        )
    )
    failures.extend(
        check(
            "slippage-only sell fill equivalence",
            adjusted_sell_fill_price(raw_price, slippage_only_model),
            old_sell_fill,
        )
    )
    failures.extend(
        check(
            "sma sensitivity slippage-only buy fill path",
            adjusted_buy_fill_price(raw_price, slippage_only_model),
            old_buy_fill,
        )
    )
    failures.extend(
        check(
            "strategy comparison slippage-only sell fill path",
            adjusted_sell_fill_price(raw_price, slippage_only_model),
            old_sell_fill,
        )
    )
    failures.extend(
        check(
            "backtest slippage-only buy fill path",
            adjusted_buy_fill_price(raw_price, slippage_only_model),
            old_buy_fill,
        )
    )

    crypto_model = CostModel(
        crypto_maker_fee_bps=Decimal("99"),
        crypto_taker_fee_bps=Decimal("123"),
    )
    failures.extend(check("crypto maker field", crypto_model.crypto_maker_fee_bps, Decimal("99")))
    failures.extend(check("crypto taker field", crypto_model.crypto_taker_fee_bps, Decimal("123")))
    failures.extend(
        check(
            "crypto fields ignored by stock helper",
            calculate_total_estimated_trade_cost(crypto_model, 100, 2),
            Decimal("0"),
        )
    )

    if failures:
        print("Cost-model verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Cost-model verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
