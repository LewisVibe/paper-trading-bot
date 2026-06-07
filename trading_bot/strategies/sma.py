"""Pure SMA, trend, volatility, and signal helpers."""

from __future__ import annotations

import math
from dataclasses import dataclass

from trading_bot.config import AppConfig


SIGNAL_BUY = "BUY"
SIGNAL_SELL = "SELL"
SIGNAL_HOLD = "HOLD"
SMA_SENSITIVITY_PAIRS = [
    (20, 100),
    (30, 150),
    (40, 160),
    (50, 200),
    (60, 200),
    (100, 200),
]
TREND_STRESS_TEST_PAIRS = [
    (40, 160),
    (50, 200),
    (60, 200),
    (100, 200),
]


@dataclass
class SignalResult:
    signal: str
    last_close: float
    short_ma: float
    long_ma: float


@dataclass
class SlowSmaPreviewRow:
    ticker: str
    date: str
    close: float
    short_sma: float
    long_sma: float
    previous_short_sma: float
    previous_long_sma: float
    signal: str
    reason: str
    trend_state: str
    desired_position: str
    distance_from_short_sma_pct: float
    distance_from_long_sma_pct: float
    days_since_last_crossover: int | None
    last_crossover_type: str
    last_crossover_date: str
    close_above_short_sma: bool
    close_above_long_sma: bool
    used_short_window: int
    used_long_window: int


def detect_sma_signal(
    previous_short: float,
    previous_long: float,
    latest_short: float,
    latest_long: float,
) -> str:
    if previous_short <= previous_long and latest_short > latest_long:
        return SIGNAL_BUY
    if previous_short >= previous_long and latest_short < latest_long:
        return SIGNAL_SELL
    return SIGNAL_HOLD


def calculate_signal(config: AppConfig, close_prices) -> SignalResult:
    short_ma_series = close_prices.rolling(window=config.short_window).mean()
    long_ma_series = close_prices.rolling(window=config.long_window).mean()

    previous_short = float(short_ma_series.iloc[-2])
    previous_long = float(long_ma_series.iloc[-2])
    latest_short = float(short_ma_series.iloc[-1])
    latest_long = float(long_ma_series.iloc[-1])
    latest_close = float(close_prices.iloc[-1])

    values = [previous_short, previous_long, latest_short, latest_long, latest_close]
    if any(math.isnan(value) for value in values):
        raise RuntimeError("Moving averages contain empty values. Try a longer history_period.")

    signal = detect_sma_signal(previous_short, previous_long, latest_short, latest_long)

    return SignalResult(
        signal=signal,
        last_close=latest_close,
        short_ma=latest_short,
        long_ma=latest_long,
    )


def calculate_slow_sma_preview_row(
    ticker: str,
    close_prices,
    short_window: int,
    long_window: int,
) -> SlowSmaPreviewRow:
    short_sma_series = close_prices.rolling(short_window).mean()
    long_sma_series = close_prices.rolling(long_window).mean()

    previous_short_sma = float(short_sma_series.iloc[-2])
    previous_long_sma = float(long_sma_series.iloc[-2])
    short_sma = float(short_sma_series.iloc[-1])
    long_sma = float(long_sma_series.iloc[-1])
    close = float(close_prices.iloc[-1])

    values = [previous_short_sma, previous_long_sma, short_sma, long_sma, close]
    if any(math.isnan(value) for value in values):
        raise RuntimeError("Moving averages contain empty values. Try a longer backtest.history_period.")

    signal = detect_sma_signal(
        previous_short_sma,
        previous_long_sma,
        short_sma,
        long_sma,
    )
    trend_state = calculate_slow_sma_trend_state(short_sma, long_sma)
    desired_position = "long" if trend_state == "bullish" else "flat"
    last_crossover_type, last_crossover_date, days_since_last_crossover = (
        find_last_slow_sma_crossover(short_sma_series, long_sma_series)
    )
    if signal == SIGNAL_BUY:
        reason = f"sma{short_window}_crossed_above_sma{long_window}"
    elif signal == SIGNAL_SELL:
        reason = f"sma{short_window}_crossed_below_sma{long_window}"
    else:
        # HOLD only means there is no new crossover today. It can still be a
        # bullish active trend if the short SMA is already above the long SMA.
        reason = "no_crossover"

    return SlowSmaPreviewRow(
        ticker=ticker,
        date=close_prices.index[-1].date().isoformat(),
        close=close,
        short_sma=short_sma,
        long_sma=long_sma,
        previous_short_sma=previous_short_sma,
        previous_long_sma=previous_long_sma,
        signal=signal,
        reason=reason,
        trend_state=trend_state,
        desired_position=desired_position,
        distance_from_short_sma_pct=calculate_distance_pct(close, short_sma),
        distance_from_long_sma_pct=calculate_distance_pct(close, long_sma),
        days_since_last_crossover=days_since_last_crossover,
        last_crossover_type=last_crossover_type,
        last_crossover_date=last_crossover_date,
        close_above_short_sma=close > short_sma,
        close_above_long_sma=close > long_sma,
        used_short_window=short_window,
        used_long_window=long_window,
    )


def calculate_slow_sma_trend_state(short_sma: float, long_sma: float) -> str:
    if short_sma > long_sma:
        return "bullish"
    if short_sma < long_sma:
        return "bearish"
    return "neutral"


def calculate_distance_pct(close: float, moving_average: float) -> float:
    if moving_average == 0:
        return 0.0
    return ((close - moving_average) / moving_average) * 100


def find_last_slow_sma_crossover(short_sma_series, long_sma_series) -> tuple[str, str, int | None]:
    last_type = "none"
    last_date = ""
    last_index: int | None = None

    for index in range(1, len(short_sma_series)):
        values = [
            float(short_sma_series.iloc[index - 1]),
            float(long_sma_series.iloc[index - 1]),
            float(short_sma_series.iloc[index]),
            float(long_sma_series.iloc[index]),
        ]
        if any(math.isnan(value) for value in values):
            continue

        if crossed_above(values[0], values[1], values[2], values[3]):
            last_type = "bullish"
            last_date = short_sma_series.index[index].date().isoformat()
            last_index = index
        elif crossed_below(values[0], values[1], values[2], values[3]):
            last_type = "bearish"
            last_date = short_sma_series.index[index].date().isoformat()
            last_index = index

    if last_index is None:
        return last_type, last_date, None
    return last_type, last_date, len(short_sma_series) - 1 - last_index


def prepare_trend_stress_test_data(ticker_data):
    data = ticker_data.copy()
    windows = sorted({window for pair in TREND_STRESS_TEST_PAIRS for window in pair})
    for window in windows:
        data[f"sma{window}"] = data["close"].rolling(window).mean()

    data = data.dropna()
    if len(data) < 3:
        raise RuntimeError("Not enough data after trend stress warm-up.")
    return data


def prepare_sma_sensitivity_data(ticker_data):
    data = ticker_data.copy()
    windows = sorted({window for pair in SMA_SENSITIVITY_PAIRS for window in pair})
    for window in windows:
        data[f"sma{window}"] = data["close"].rolling(window).mean()

    # Every SMA pair starts from the same warmed-up window, using the slowest
    # long average. That keeps the comparison from favoring faster pairs simply
    # because they had more history to trade.
    data = data.dropna()
    if len(data) < 3:
        raise RuntimeError("Not enough data after SMA warm-up.")
    return data


def prepare_strategy_comparison_data(ticker_data, regime_data):
    data = ticker_data.join(
        regime_data[["close"]].rename(columns={"close": "regime_close"}),
        how="inner",
    )
    data["sma20"] = data["close"].rolling(20).mean()
    data["sma50"] = data["close"].rolling(50).mean()
    data["sma200"] = data["close"].rolling(200).mean()
    data["regime_sma200"] = data["regime_close"].rolling(200).mean()

    # All strategies for a ticker must use the same comparison window. Otherwise
    # a fast strategy could start earlier than a slow strategy, and the returns
    # would mix strategy quality with different market periods.
    data = data.dropna()
    if len(data) < 3:
        raise RuntimeError("Not enough shared comparison data after warm-up.")
    return data


def comparison_entry_signal(strategy_name: str, yesterday, today) -> tuple[bool, str]:
    if strategy_name == "sma_20_50_basic":
        return (
            crossed_above(float(yesterday["sma20"]), float(yesterday["sma50"]), float(today["sma20"]), float(today["sma50"])),
            "sma20_cross_above_sma50",
        )

    if strategy_name == "sma_20_50_regime":
        # Regime filter: require the broad market proxy, SPY, to be above its 200-day SMA.
        regime_ok = float(today["regime_close"]) > float(today["regime_sma200"])
        crossover = crossed_above(float(yesterday["sma20"]), float(yesterday["sma50"]), float(today["sma20"]), float(today["sma50"]))
        return regime_ok and crossover, "sma20_cross_above_sma50,spy_above_200"

    if strategy_name == "sma_50_200_trend":
        return (
            crossed_above(float(yesterday["sma50"]), float(yesterday["sma200"]), float(today["sma50"]), float(today["sma200"])),
            "sma50_cross_above_sma200",
        )

    if strategy_name == "buy_above_200_exit_below_200":
        # This strategy uses the ticker's own 200-day trend plus the SPY regime filter.
        regime_ok = float(today["regime_close"]) > float(today["regime_sma200"])
        ticker_cross = crossed_above(float(yesterday["close"]), float(yesterday["sma200"]), float(today["close"]), float(today["sma200"]))
        return regime_ok and ticker_cross, "close_cross_above_200,spy_above_200"

    raise RuntimeError(f"Unknown strategy: {strategy_name}")


def comparison_exit_signal(strategy_name: str, yesterday, today) -> tuple[bool, str]:
    if strategy_name == "sma_20_50_basic":
        return (
            crossed_below(float(yesterday["sma20"]), float(yesterday["sma50"]), float(today["sma20"]), float(today["sma50"])),
            "sma20_cross_below_sma50",
        )

    if strategy_name == "sma_20_50_regime":
        crossover_down = crossed_below(float(yesterday["sma20"]), float(yesterday["sma50"]), float(today["sma20"]), float(today["sma50"]))
        regime_break = float(today["regime_close"]) < float(today["regime_sma200"])
        return crossover_down or regime_break, "sma20_cross_below_sma50" if crossover_down else "spy_below_200"

    if strategy_name == "sma_50_200_trend":
        return (
            crossed_below(float(yesterday["sma50"]), float(yesterday["sma200"]), float(today["sma50"]), float(today["sma200"])),
            "sma50_cross_below_sma200",
        )

    if strategy_name == "buy_above_200_exit_below_200":
        ticker_cross = crossed_below(float(yesterday["close"]), float(yesterday["sma200"]), float(today["close"]), float(today["sma200"]))
        regime_break = float(today["regime_close"]) < float(today["regime_sma200"])
        return ticker_cross or regime_break, "close_cross_below_200" if ticker_cross else "spy_below_200"

    raise RuntimeError(f"Unknown strategy: {strategy_name}")


def crossed_above(previous_fast: float, previous_slow: float, current_fast: float, current_slow: float) -> bool:
    return previous_fast <= previous_slow and current_fast > current_slow


def crossed_below(previous_fast: float, previous_slow: float, current_fast: float, current_slow: float) -> bool:
    return previous_fast >= previous_slow and current_fast < current_slow
