from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when config.json is missing required safe settings."""


@dataclass
class StrategyConfig:
    name: str = "regime_sma_vol_filter"
    regime_ticker: str = "SPY"
    short_window: int = 20
    long_window: int = 50
    trend_window: int = 200
    vol_window: int = 20
    vol_median_window: int = 252
    vol_gate_multiple: float = 1.5


@dataclass
class BacktestConfig:
    enabled: bool = False
    starting_cash: float = 100000.0
    position_size_dollars: float = 10000.0
    slippage_bps: float = 5.0
    history_period: str = "10y"
    output_csv: str = "data/backtest_results.csv"
    trades_csv: str = "data/backtest_trades.csv"
    split_date: str = "2021-01-01"


@dataclass
class ResearchUniverseConfig:
    enabled: bool = False
    tickers: list[str] | None = None


@dataclass
class SlowSmaStrategyConfig:
    enabled: bool = False
    short_window: int = 50
    long_window: int = 200
    etf_short_window: int = 100
    etf_long_window: int = 200


@dataclass
class AppConfig:
    tickers: list[str]
    short_window: int
    long_window: int
    history_period: str
    history_interval: str
    order_quantity: float
    dry_run: bool
    allow_shorting: bool
    database_path: Path
    log_file: Path
    discord_enabled: bool
    discord_webhook_url: str
    alpaca_paper: bool
    alpaca_api_key: str
    alpaca_secret_key: str
    strategy: StrategyConfig
    backtest: BacktestConfig
    research_universe: ResearchUniverseConfig
    etf_research_universe: ResearchUniverseConfig
    slow_sma_strategy: SlowSmaStrategyConfig
    paper_kill_switch_enabled: bool = False


def resolve_path(config_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config_path.parent / path


def parse_config_bool(raw: dict[str, Any], key: str, default: bool, parent: str = "") -> bool:
    field_name = f"{parent}.{key}" if parent else key
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ConfigError(
            f"{field_name} must be a JSON boolean true or false, not {value!r}."
        )
    return value


def parse_env_bool(env_key: str, default: bool) -> bool:
    value = os.getenv(env_key)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise ConfigError(f"{env_key} must be a boolean-like value, not {value!r}.")


def parse_config_bool_with_env(
    raw: dict[str, Any],
    key: str,
    default: bool,
    env_key: str,
) -> bool:
    if key in raw:
        return parse_config_bool(raw, key, default)
    return parse_env_bool(env_key, default)


def parse_config_int(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{key} must be a JSON integer, not {value!r}.")
    return value


def parse_config_quantity(raw: dict[str, Any], key: str) -> float:
    value = raw.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{key} must be a JSON number, not {value!r}.")
    if not math.isfinite(float(value)) or float(value) <= 0:
        raise ConfigError(f"{key} must be a finite positive number.")
    return float(value)


def parse_config_int_default(raw: dict[str, Any], key: str, default: int, parent: str) -> int:
    value = raw.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{parent}.{key} must be a JSON integer, not {value!r}.")
    return value


def parse_config_number_default(raw: dict[str, Any], key: str, default: float, parent: str) -> float:
    value = raw.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{parent}.{key} must be a JSON number, not {value!r}.")
    if not math.isfinite(float(value)):
        raise ConfigError(f"{parent}.{key} must be a finite number.")
    return float(value)


def parse_positive_number_default(
    raw: dict[str, Any], key: str, default: float, parent: str
) -> float:
    value = parse_config_number_default(raw, key, default, parent)
    if value <= 0:
        raise ConfigError(f"{parent}.{key} must be greater than zero.")
    return value


def parse_strategy_config(raw: dict[str, Any]) -> StrategyConfig:
    strategy = raw.get("strategy", {})
    if not isinstance(strategy, dict):
        raise ConfigError("strategy must be a JSON object.")

    return StrategyConfig(
        name=str(strategy.get("name", "regime_sma_vol_filter")),
        regime_ticker=str(strategy.get("regime_ticker", "SPY")).strip().upper(),
        short_window=parse_config_int_default(strategy, "short_window", 20, "strategy"),
        long_window=parse_config_int_default(strategy, "long_window", 50, "strategy"),
        trend_window=parse_config_int_default(strategy, "trend_window", 200, "strategy"),
        vol_window=parse_config_int_default(strategy, "vol_window", 20, "strategy"),
        vol_median_window=parse_config_int_default(
            strategy, "vol_median_window", 252, "strategy"
        ),
        vol_gate_multiple=parse_positive_number_default(
            strategy, "vol_gate_multiple", 1.5, "strategy"
        ),
    )


def parse_backtest_config(raw: dict[str, Any], config_path: Path) -> BacktestConfig:
    backtest = raw.get("backtest", {})
    if not isinstance(backtest, dict):
        raise ConfigError("backtest must be a JSON object.")

    return BacktestConfig(
        enabled=parse_config_bool(backtest, "enabled", False, parent="backtest"),
        starting_cash=parse_positive_number_default(
            backtest, "starting_cash", 100000, "backtest"
        ),
        position_size_dollars=parse_positive_number_default(
            backtest, "position_size_dollars", 10000, "backtest"
        ),
        slippage_bps=parse_config_number_default(backtest, "slippage_bps", 5, "backtest"),
        history_period=str(backtest.get("history_period", "10y")),
        output_csv=str(
            resolve_path(config_path, str(backtest.get("output_csv", "data/backtest_results.csv")))
        ),
        trades_csv=str(
            resolve_path(config_path, str(backtest.get("trades_csv", "data/backtest_trades.csv")))
        ),
        split_date=str(backtest.get("split_date", "2021-01-01")),
    )


def default_research_universe_tickers() -> list[str]:
    return [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V",
        "UNH", "XOM", "JNJ", "PG", "HD", "COST", "SPY", "QQQ", "DIA", "IWM",
        "XLK", "XLF", "XLE", "XLV", "XLY", "XLP",
    ]


def default_etf_research_universe_tickers() -> list[str]:
    return [
        "SPY", "QQQ", "DIA", "IWM", "XLK", "XLF", "XLE", "XLV", "XLY",
        "XLP", "XLI", "XLU", "XLB", "XLRE", "TLT", "IEF", "GLD", "SLV",
    ]


def parse_universe_config(
    raw: dict[str, Any],
    key: str,
    default_tickers: list[str],
) -> ResearchUniverseConfig:
    research_universe = raw.get(key, {})
    if not isinstance(research_universe, dict):
        raise ConfigError(f"{key} must be a JSON object.")

    tickers = research_universe.get("tickers", default_tickers)
    return ResearchUniverseConfig(
        enabled=parse_config_bool(
            research_universe,
            "enabled",
            False,
            parent=key,
        ),
        tickers=normalize_tickers(tickers),
    )


def parse_research_universe_config(raw: dict[str, Any]) -> ResearchUniverseConfig:
    return parse_universe_config(
        raw,
        "research_universe",
        default_research_universe_tickers(),
    )


def parse_etf_research_universe_config(raw: dict[str, Any]) -> ResearchUniverseConfig:
    return parse_universe_config(
        raw,
        "etf_research_universe",
        default_etf_research_universe_tickers(),
    )


def parse_slow_sma_strategy_config(raw: dict[str, Any]) -> SlowSmaStrategyConfig:
    slow_sma_strategy = raw.get("slow_sma_strategy", {})
    if not isinstance(slow_sma_strategy, dict):
        raise ConfigError("slow_sma_strategy must be a JSON object.")

    return SlowSmaStrategyConfig(
        enabled=parse_config_bool(
            slow_sma_strategy,
            "enabled",
            False,
            parent="slow_sma_strategy",
        ),
        short_window=parse_config_int_default(
            slow_sma_strategy,
            "short_window",
            50,
            "slow_sma_strategy",
        ),
        long_window=parse_config_int_default(
            slow_sma_strategy,
            "long_window",
            200,
            "slow_sma_strategy",
        ),
        etf_short_window=parse_config_int_default(
            slow_sma_strategy,
            "etf_short_window",
            100,
            "slow_sma_strategy",
        ),
        etf_long_window=parse_config_int_default(
            slow_sma_strategy,
            "etf_long_window",
            200,
            "slow_sma_strategy",
        ),
    )


def load_config(
    config_path: Path,
    force_dry_run: bool,
    allow_missing_alpaca_keys: bool = False,
) -> AppConfig:
    if not config_path.exists():
        raise ConfigError(
            f"Config file not found: {config_path}. Copy config.example.json to config.json first."
        )

    with config_path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    if not isinstance(raw, dict):
        raise ConfigError("config.json must contain a JSON object.")

    alpaca = raw.get("alpaca", {})
    discord = raw.get("discord", {})
    if not isinstance(alpaca, dict):
        raise ConfigError("alpaca must be a JSON object.")
    if not isinstance(discord, dict):
        raise ConfigError("discord must be a JSON object.")

    api_key = alpaca.get("api_key") or os.getenv("ALPACA_API_KEY", "")
    secret_key = alpaca.get("secret_key") or os.getenv("ALPACA_SECRET_KEY", "")
    webhook_url = discord.get("webhook_url") or os.getenv("DISCORD_WEBHOOK_URL", "")

    tickers = normalize_tickers(raw.get("tickers", []))
    strategy_config = parse_strategy_config(raw)
    backtest_config = parse_backtest_config(raw, config_path)
    research_universe_config = parse_research_universe_config(raw)
    etf_research_universe_config = parse_etf_research_universe_config(raw)
    slow_sma_strategy_config = parse_slow_sma_strategy_config(raw)
    short_window = parse_config_int(raw, "short_window")
    long_window = parse_config_int(raw, "long_window")
    order_quantity = parse_config_quantity(raw, "order_quantity")
    dry_run = parse_config_bool(raw, "dry_run", True)

    if force_dry_run:
        dry_run = True

    config = AppConfig(
        tickers=tickers,
        short_window=short_window,
        long_window=long_window,
        history_period=str(raw.get("history_period", "6mo")),
        history_interval=str(raw.get("history_interval", "1d")),
        order_quantity=order_quantity,
        dry_run=dry_run,
        allow_shorting=parse_config_bool(raw, "allow_shorting", False),
        paper_kill_switch_enabled=parse_config_bool_with_env(
            raw,
            "paper_kill_switch_enabled",
            False,
            "PAPER_KILL_SWITCH_ENABLED",
        ),
        database_path=resolve_path(config_path, str(raw.get("database_path", "data/trades.db"))),
        log_file=resolve_path(config_path, str(raw.get("log_file", "logs/bot.log"))),
        discord_enabled=parse_config_bool(discord, "enabled", False, parent="discord"),
        discord_webhook_url=webhook_url,
        alpaca_paper=parse_config_bool(alpaca, "paper", True, parent="alpaca"),
        alpaca_api_key=api_key,
        alpaca_secret_key=secret_key,
        strategy=strategy_config,
        backtest=backtest_config,
        research_universe=research_universe_config,
        etf_research_universe=etf_research_universe_config,
        slow_sma_strategy=slow_sma_strategy_config,
    )
    validate_config(config, allow_missing_alpaca_keys=allow_missing_alpaca_keys)
    return config


def normalize_tickers(raw_tickers: Any) -> list[str]:
    if not isinstance(raw_tickers, list):
        raise ConfigError("tickers must be a list, for example: [\"AAPL\", \"MSFT\", \"SPY\"]")

    tickers: list[str] = []
    seen: set[str] = set()
    for raw in raw_tickers:
        ticker = str(raw).strip().upper()
        if ticker and ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return tickers


def validate_config(config: AppConfig, allow_missing_alpaca_keys: bool = False) -> None:
    if not config.tickers:
        raise ConfigError("tickers must contain at least one U.S. stock or ETF symbol.")

    validate_ticker_symbols(config.tickers, "tickers")

    if config.short_window <= 0 or config.long_window <= 0:
        raise ConfigError("short_window and long_window must be positive integers.")

    if config.short_window >= config.long_window:
        raise ConfigError("short_window must be less than long_window.")

    if config.order_quantity <= 0:
        raise ConfigError("order_quantity must be greater than zero.")

    if not config.alpaca_paper:
        raise ConfigError("alpaca.paper must be true. This bot refuses to use live trading mode.")

    if (
        not allow_missing_alpaca_keys
        and not config.dry_run
        and (not config.alpaca_api_key or not config.alpaca_secret_key)
    ):
        raise ConfigError("Alpaca paper API key and secret key are required when dry_run is false.")

    if config.discord_enabled and not config.discord_webhook_url:
        raise ConfigError("Discord is enabled, but discord.webhook_url is empty.")

    if config.strategy.short_window <= 0 or config.strategy.long_window <= 0:
        raise ConfigError("strategy short_window and long_window must be positive.")

    if config.strategy.short_window >= config.strategy.long_window:
        raise ConfigError("strategy.short_window must be less than strategy.long_window.")

    if config.strategy.trend_window <= 0:
        raise ConfigError("strategy.trend_window must be positive.")

    if config.strategy.vol_window <= 0 or config.strategy.vol_median_window <= 0:
        raise ConfigError("strategy volatility windows must be positive.")

    if config.backtest.slippage_bps < 0:
        raise ConfigError("backtest.slippage_bps must be zero or greater.")

    try:
        datetime.fromisoformat(config.backtest.split_date)
    except ValueError as exc:
        raise ConfigError("backtest.split_date must use YYYY-MM-DD format.") from exc

    if not config.research_universe.tickers:
        raise ConfigError("research_universe.tickers must contain at least one symbol.")
    validate_ticker_symbols(config.research_universe.tickers, "research_universe.tickers")

    if not config.etf_research_universe.tickers:
        raise ConfigError("etf_research_universe.tickers must contain at least one symbol.")
    validate_ticker_symbols(
        config.etf_research_universe.tickers,
        "etf_research_universe.tickers",
    )

    if config.slow_sma_strategy.short_window <= 0 or config.slow_sma_strategy.long_window <= 0:
        raise ConfigError("slow_sma_strategy short_window and long_window must be positive.")

    if config.slow_sma_strategy.short_window >= config.slow_sma_strategy.long_window:
        raise ConfigError("slow_sma_strategy.short_window must be less than slow_sma_strategy.long_window.")

    if config.slow_sma_strategy.etf_short_window <= 0 or config.slow_sma_strategy.etf_long_window <= 0:
        raise ConfigError("slow_sma_strategy ETF windows must be positive.")

    if config.slow_sma_strategy.etf_short_window >= config.slow_sma_strategy.etf_long_window:
        raise ConfigError(
            "slow_sma_strategy.etf_short_window must be less than slow_sma_strategy.etf_long_window."
        )


def validate_ticker_symbols(tickers: list[str], field_name: str) -> None:
    for ticker in tickers:
        if not all(char.isalnum() or char in ".-" for char in ticker):
            raise ConfigError(
                f"{field_name} contains unsupported characters in '{ticker}'."
            )
