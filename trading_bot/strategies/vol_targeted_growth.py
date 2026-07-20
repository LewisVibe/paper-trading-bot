"""Live proxy calculation for the approved volatility-targeted paper sleeve."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN
from math import sqrt
from pathlib import Path
from statistics import stdev
from typing import Any
from zoneinfo import ZoneInfo


STRATEGY_NAME = "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x"
PAPER_CAPITAL_USD = Decimal("100000.00")
TARGET_VOLATILITY = Decimal("0.15")
VOLATILITY_WINDOW_DAYS = 20
EXPOSURE_CAP = Decimal("1")
QUANTITY_INCREMENT = Decimal("0.000001")
PRICE_FRESHNESS_MINUTES = Decimal("15")


@dataclass(frozen=True)
class SleeveSpec:
    name: str
    symbol: str
    base_weight: Decimal


SLEEVES = (
    SleeveSpec("qqq100_core_trend_sleeve", "QQQ", Decimal("0.70")),
    SleeveSpec("high_growth_stock_research_sleeve", "MGK", Decimal("0.20")),
    SleeveSpec("crypto_research_sleeve", "IBIT", Decimal("0.05")),
    SleeveSpec("defensive_cash_or_bond_sleeve", "SGOV", Decimal("0.05")),
)
MANAGED_SYMBOLS = tuple(sleeve.symbol for sleeve in SLEEVES)


@dataclass(frozen=True)
class VolatilitySnapshot:
    calculated_at: datetime
    market_data_as_of: str
    price_timestamp: datetime
    prices: dict[str, Decimal]
    realized_volatility: Decimal
    exposure_multiplier: Decimal
    effective_weights: dict[str, Decimal]
    cash_weight: Decimal
    return_observation_count: int
    price_age_minutes: Decimal
    prices_fresh: bool


def calculate_volatility_snapshot(
    close_rows: list[dict[str, Decimal]],
    *,
    market_data_as_of: str,
    price_timestamp: datetime,
    prices: dict[str, Decimal] | None = None,
    now: datetime | None = None,
) -> VolatilitySnapshot:
    """Calculate the 20-day realized-volatility exposure from mapped proxies."""
    if len(close_rows) < VOLATILITY_WINDOW_DAYS + 1:
        raise ValueError("At least 21 complete daily close rows are required.")

    for row in close_rows:
        missing = [symbol for symbol in MANAGED_SYMBOLS if row.get(symbol, Decimal("0")) <= 0]
        if missing:
            raise ValueError(f"Missing positive close prices for: {','.join(missing)}")

    portfolio_returns: list[float] = []
    for index in range(1, len(close_rows)):
        previous = close_rows[index - 1]
        current = close_rows[index]
        weighted_return = sum(
            sleeve.base_weight * ((current[sleeve.symbol] / previous[sleeve.symbol]) - Decimal("1"))
            for sleeve in SLEEVES
        )
        portfolio_returns.append(float(weighted_return))

    window = portfolio_returns[-VOLATILITY_WINDOW_DAYS:]
    realized = Decimal(str(stdev(window) * sqrt(252))) if len(window) > 1 else Decimal("0")
    exposure = EXPOSURE_CAP if realized <= 0 else min(EXPOSURE_CAP, TARGET_VOLATILITY / realized)
    exposure = exposure.quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
    effective_weights = {
        sleeve.symbol: (sleeve.base_weight * exposure).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        for sleeve in SLEEVES
    }
    cash_weight = max(Decimal("0"), Decimal("1") - sum(effective_weights.values()))

    calculated_at = _aware_utc(now or datetime.now(timezone.utc))
    normalized_price_timestamp = _aware_utc(price_timestamp)
    age_minutes = max(
        Decimal("0"),
        Decimal(str((calculated_at - normalized_price_timestamp).total_seconds())) / Decimal("60"),
    ).quantize(Decimal("0.01"))
    selected_prices = prices or close_rows[-1]
    clean_prices = {symbol: Decimal(str(selected_prices[symbol])) for symbol in MANAGED_SYMBOLS}

    return VolatilitySnapshot(
        calculated_at=calculated_at,
        market_data_as_of=market_data_as_of,
        price_timestamp=normalized_price_timestamp,
        prices=clean_prices,
        realized_volatility=realized.quantize(Decimal("0.000001")),
        exposure_multiplier=exposure,
        effective_weights=effective_weights,
        cash_weight=cash_weight.quantize(Decimal("0.000001")),
        return_observation_count=len(window),
        price_age_minutes=age_minutes,
        prices_fresh=age_minutes <= PRICE_FRESHNESS_MINUTES,
    )


def load_live_volatility_snapshot(
    root_dir: Path | str = ".",
    *,
    now: datetime | None = None,
) -> VolatilitySnapshot:
    """Fetch daily history and a current one-minute price row from yfinance."""
    root = Path(root_dir)
    try:
        from trading_bot.market_data import configure_yfinance_cache_location

        configure_yfinance_cache_location(root / "data" / "yfinance_cache")
    except Exception:
        pass

    import yfinance as yf

    symbols = list(MANAGED_SYMBOLS)
    daily = yf.download(
        symbols,
        period="3mo",
        interval="1d",
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    intraday = yf.download(
        symbols,
        period="1d",
        interval="1m",
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    calculation_time = _aware_utc(now or datetime.now(timezone.utc))
    current_market_date = calculation_time.astimezone(ZoneInfo("America/New_York")).date()
    daily_rows, daily_timestamp = _complete_close_rows(
        daily,
        symbols,
        before_date=current_market_date,
    )
    intraday_rows, intraday_timestamp = _complete_close_rows(intraday, symbols)
    if not intraday_rows:
        raise RuntimeError("No complete intraday price row was returned for all managed symbols.")

    return calculate_volatility_snapshot(
        daily_rows,
        market_data_as_of=str(daily_timestamp),
        price_timestamp=_timestamp_to_utc(intraday_timestamp),
        prices=intraday_rows[-1],
        now=now,
    )


def _complete_close_rows(
    data: Any,
    symbols: list[str],
    *,
    before_date: date | None = None,
) -> tuple[list[dict[str, Decimal]], Any]:
    if data is None or getattr(data, "empty", True):
        raise RuntimeError("Market-data response was empty.")
    closes = data["Close"]
    rows: list[dict[str, Decimal]] = []
    timestamps: list[Any] = []
    for timestamp, row in closes.iterrows():
        if before_date is not None and _timestamp_date(timestamp) >= before_date:
            continue
        values: dict[str, Decimal] = {}
        complete = True
        for symbol in symbols:
            try:
                value = Decimal(str(row[symbol]))
            except Exception:
                complete = False
                break
            if not value.is_finite() or value <= 0:
                complete = False
                break
            values[symbol] = value
        if complete:
            rows.append(values)
            timestamps.append(timestamp)
    if not rows:
        raise RuntimeError("No complete close-price rows were returned for all managed symbols.")
    return rows, timestamps[-1]


def _timestamp_to_utc(value: Any) -> datetime:
    candidate = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not isinstance(candidate, datetime):
        candidate = datetime.fromisoformat(str(candidate))
    return _aware_utc(candidate)


def _timestamp_date(value: Any) -> date:
    candidate = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if isinstance(candidate, datetime):
        return candidate.date()
    return datetime.fromisoformat(str(candidate)).date()


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
