from __future__ import annotations

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.safety.vol_targeted_growth_paper_execution import (  # noqa: E402
    AssetState,
    BrokerState,
    build_ticket_document,
    execution_preflight_reasons,
)
from trading_bot.strategies.vol_targeted_growth import (  # noqa: E402
    MANAGED_SYMBOLS,
    SLEEVES,
    VolatilitySnapshot,
)


NOW = datetime(2026, 7, 10, 15, 0, tzinfo=timezone.utc)


def main() -> int:
    failures: list[str] = []
    snapshot = VolatilitySnapshot(
        calculated_at=NOW,
        market_data_as_of="2026-07-10",
        price_timestamp=NOW,
        prices={"QQQ": Decimal("700"), "MGK": Decimal("90"), "IBIT": Decimal("35"), "SGOV": Decimal("100")},
        realized_volatility=Decimal("0.20"),
        exposure_multiplier=Decimal("0.75"),
        effective_weights={s.symbol: s.base_weight * Decimal("0.75") for s in SLEEVES},
        cash_weight=Decimal("0.25"),
        return_observation_count=20,
        price_age_minutes=Decimal("0"),
        prices_fresh=True,
    )
    assets = {symbol: AssetState(symbol, "us_equity", True, True) for symbol in MANAGED_SYMBOLS}
    broker = BrokerState(
        captured_at=NOW,
        market_open=True,
        account_status="active",
        account_blocked=False,
        trading_blocked=False,
        trade_suspended_by_user=False,
        cash=Decimal("100000"),
        equity=Decimal("100000"),
        buying_power=Decimal("100000"),
        positions={},
        position_market_values={},
        open_order_symbols=(),
        recent_client_order_ids=(),
        assets=assets,
    )
    document = build_ticket_document(snapshot, broker, now=NOW)
    payload = document["payload"]

    if payload["paper_capital_usd"] != "100000":
        failures.append("paper ticket must use the approved $100,000 cap")
    if set(row["symbol"] for row in payload["targets"]) != set(MANAGED_SYMBOLS):
        failures.append("paper ticket must be limited to QQQ, MGK, IBIT, and SGOV")
    if not payload["execution_ready"]:
        failures.append("safe fresh mock state should create an execution-ready ticket")
    if payload["live_trading_approved"] or payload["scheduling_approved"]:
        failures.append("live trading and scheduling must remain false")
    missing_confirmation = execution_preflight_reasons(
        document,
        broker,
        supplied_ticket_id=document["ticket_id"],
        confirmed=False,
        now=NOW,
    )
    if "--confirm-vol-targeted-growth-paper is required" not in missing_confirmation:
        failures.append("execution must refuse a missing explicit confirmation")

    gateway_source = (ROOT / "trading_bot" / "paper_orders.py").read_text(encoding="utf-8")
    runner_source = (ROOT / "trading_bot" / "runners" / "vol_targeted_growth_paper.py").read_text(encoding="utf-8")
    parser_source = (ROOT / "trading_bot" / "cli" / "parser.py").read_text(encoding="utf-8")
    normal_source = (ROOT / "trading_bot" / "runners" / "paper_execution.py").read_text(encoding="utf-8")
    for token in [
        "--prepare-vol-targeted-growth-paper-ticket",
        "--execute-vol-targeted-growth-paper",
        "--confirm-vol-targeted-growth-paper",
        "--vol-targeted-growth-paper-postcheck",
        "--run-vol-targeted-growth-auto-paper",
    ]:
        if token not in parser_source:
            failures.append(f"parser is missing {token}")
    if "PaperOrderRoute.VOL_TARGETED_GROWTH" not in runner_source:
        failures.append("volatility execution must use its audited gateway route")
    if ".submit_order(" in runner_source:
        failures.append("volatility runner must not submit directly to Alpaca")
    if "client_order_id=request.client_order_id" not in gateway_source:
        failures.append("paper gateway must carry deterministic client order IDs")
    if "run_execute_vol_targeted_growth_paper" in normal_source:
        failures.append("normal bot path must remain disconnected from volatility paper execution")
    for token in [
        "auto_paper_trading_enabled",
        "AUTO_WINDOW_START_MINUTE",
        "America/New_York",
        "acquire_auto_lease",
        "vtga-",
        "send_discord_alert",
        "run_vol_targeted_growth_auto_paper",
        "partial_or_failed_manual_review_required",
    ]:
        if token not in runner_source:
            failures.append(f"automatic paper runner is missing safety token: {token}")
    config_example = (ROOT / "config.example.json").read_text(encoding="utf-8")
    if '"auto_paper_trading_enabled": false' not in config_example:
        failures.append("automatic paper trading must default false in config.example.json")

    if failures:
        print("Volatility-targeted paper execution verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted paper execution verification passed.")
    print("Verified $100,000 cap, four-symbol scope, manual confirmation, explicit auto opt-in, lease/idempotency, gateway routing, and no live path.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
