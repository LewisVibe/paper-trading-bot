"""yfinance market data download and price-column normalization helpers."""

from __future__ import annotations

import logging

import yfinance as yf

from trading_bot.config import AppConfig


def configure_yfinance_cache(config: AppConfig, logger: logging.Logger) -> None:
    cache_dir = config.database_path.parent / "yfinance_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        yf.set_tz_cache_location(str(cache_dir))
    except AttributeError:
        logger.warning("Installed yfinance version does not support custom cache location.")


def download_close_prices(config: AppConfig, ticker: str):
    data = yf.download(
        ticker,
        period=config.history_period,
        interval=config.history_interval,
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        raise RuntimeError("No market data returned by yfinance.")

    close = extract_close_column(data, ticker)
    close = close.dropna()

    required_rows = config.long_window + 1
    if len(close) < required_rows:
        raise RuntimeError(
            f"Not enough price history. Need at least {required_rows} rows, got {len(close)}."
        )

    return close


def extract_close_column(data, ticker: str):
    columns = data.columns
    has_multi_index = getattr(columns, "nlevels", 1) > 1

    if has_multi_index:
        for key in (("Close", ticker), (ticker, "Close")):
            if key in columns:
                close = data[key]
                return first_series(close)

        if "Close" in columns.get_level_values(0):
            close = data.xs("Close", axis=1, level=0)
            return first_series(close)

        if "Close" in columns.get_level_values(1):
            close = data.xs("Close", axis=1, level=1)
            return first_series(close)

    if "Close" not in data:
        raise RuntimeError("Downloaded data does not contain a Close price column.")

    return first_series(data["Close"])


def first_series(value):
    if getattr(value, "ndim", 1) == 2:
        return value.iloc[:, 0]
    return value


def download_backtest_prices(config: AppConfig, ticker: str):
    data = yf.download(
        ticker,
        period=config.backtest.history_period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        raise RuntimeError("No daily market data returned by yfinance.")

    open_prices = extract_price_column(data, ticker, "Open")
    high_prices = extract_price_column(data, ticker, "High")
    low_prices = extract_price_column(data, ticker, "Low")
    close_prices = extract_price_column(data, ticker, "Close")
    volume = extract_price_column(data, ticker, "Volume")
    prices = open_prices.to_frame(name="open")
    prices["high"] = high_prices
    prices["low"] = low_prices
    prices["close"] = close_prices
    prices["volume"] = volume
    prices = prices.dropna()

    required_rows = max(
        config.strategy.trend_window,
        config.strategy.vol_median_window + config.strategy.vol_window,
        config.strategy.long_window,
    ) + 2
    if len(prices) < required_rows:
        raise RuntimeError(f"Not enough history. Need at least {required_rows} rows, got {len(prices)}.")

    return prices


def extract_price_column(data, ticker: str, field: str):
    columns = data.columns
    has_multi_index = getattr(columns, "nlevels", 1) > 1

    if has_multi_index:
        for key in ((field, ticker), (ticker, field)):
            if key in columns:
                return first_series(data[key])
        if field in columns.get_level_values(0):
            return first_series(data.xs(field, axis=1, level=0))
        if field in columns.get_level_values(1):
            return first_series(data.xs(field, axis=1, level=1))

    if field not in data:
        raise RuntimeError(f"Downloaded data does not contain a {field} price column.")
    return first_series(data[field])


def download_slow_sma_preview_prices(
    ticker: str,
    history_period: str,
    short_window: int,
    long_window: int,
):
    data = yf.download(
        ticker,
        period=history_period,
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if data is None or data.empty:
        raise RuntimeError("No daily market data returned by yfinance.")

    close_prices = extract_close_column(data, ticker).dropna()
    required_rows = max(short_window, long_window) + 2
    if len(close_prices) < required_rows:
        raise RuntimeError(
            f"Not enough daily history. Need at least {required_rows} rows, got {len(close_prices)}."
        )
    return close_prices
