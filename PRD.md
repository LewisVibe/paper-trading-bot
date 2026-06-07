# Product Requirements Document: Python Market Monitoring and Paper Trading Bot

## 1. Overview

Build a beginner-friendly Python market monitoring and paper trading bot for Windows Server 2022. The bot will run once per execution, monitor a configured list of U.S. stock and ETF tickers, calculate simple moving-average crossover signals using `yfinance`, optionally submit paper trades through Alpaca paper trading, log decisions and trades to SQLite, and send Discord webhook alerts for important events.

Version 1 must be simple, readable, and safe by default. It should be suitable for a hobbyist learning how trading bots are structured.

## 2. MVP Decisions

- The bot runs once and exits.
- Repeated execution should be handled later with Windows Task Scheduler.
- Supported instruments are U.S. stocks and ETFs only.
- The default strategy is long-only trading.
- Short selling is controlled by `allow_shorting`.
- `allow_shorting` defaults to `false`.
- `dry_run` defaults to `true`.
- Alpaca live trading is not supported.
- The bot must refuse to run if Alpaca paper mode is set to `false`.
- Duplicate trade prevention only needs to work within a single run for version 1.
- Pyramiding is not allowed in version 1.
- Discord alerts are sent only for startup, submitted trades, errors, and completion summary.
- Discord alerts are not sent for every `HOLD` signal.
- The implementation should use one simple `bot.py` file unless splitting into modules makes the code clearer.

## 3. Goals

- Monitor a configurable ticker list using `yfinance`.
- Generate `BUY`, `SELL`, and `HOLD` signals using short and long simple moving averages.
- Check current paper/simulated position state before deciding whether a trade is allowed.
- Submit market orders to Alpaca paper trading when `dry_run` is `false`.
- Store all signal decisions, intended trades, submitted orders, and errors in SQLite.
- Send Discord webhook alerts for key events.
- Include:
  - `bot.py`
  - `requirements.txt`
  - `config.example.json`
  - `README.md`
  - `.gitignore`
  - `data/.gitkeep`
  - `logs/.gitkeep`

## 4. Non-Goals

- No live-money trading.
- No dashboard.
- No machine learning.
- No backtesting.
- No Docker setup.
- No complex indicators.
- No options, crypto, futures, or forex.
- No high-frequency trading.
- No continuous loop in version 1.
- No pyramiding into existing positions.

## 5. Target User

The target user is a beginner or intermediate Python hobbyist who wants to learn market monitoring and paper-trading automation without risking real money.

They should be able to:

- Install Python on Windows Server 2022.
- Create a virtual environment.
- Install dependencies.
- Copy `config.example.json` to `config.json`.
- Run `python bot.py`.
- Review `logs/bot.log`.
- Review `data/trades.db`.
- Later schedule repeated runs with Windows Task Scheduler.

## 6. Configuration Requirements

The bot reads from `config.json` by default.

`config.example.json` must include safe defaults:

```json
{
  "tickers": ["AAPL", "MSFT", "SPY"],
  "short_window": 20,
  "long_window": 50,
  "history_period": "6mo",
  "history_interval": "1d",
  "order_quantity": 1,
  "dry_run": true,
  "allow_shorting": false,
  "database_path": "data/trades.db",
  "log_file": "logs/bot.log",
  "discord": {
    "enabled": false,
    "webhook_url": ""
  },
  "alpaca": {
    "paper": true,
    "api_key": "",
    "secret_key": ""
  }
}
```

Environment variable fallback should be supported for secrets:

- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `DISCORD_WEBHOOK_URL`

Validation rules:

- `tickers` must be a non-empty list.
- Tickers should represent U.S. stocks or ETFs.
- `short_window` and `long_window` must be positive integers.
- `short_window` must be less than `long_window`.
- `order_quantity` must be positive.
- `dry_run` must default to `true`.
- `allow_shorting` must default to `false`.
- `alpaca.paper` must be `true`; otherwise, the bot refuses to run.
- If `dry_run` is `false`, Alpaca API key and secret key are required.
- If Discord is enabled, a webhook URL is required.

## 7. Command-Line Requirements

Required:

```powershell
python bot.py
```

Optional:

```powershell
python bot.py --config config.json
python bot.py --dry-run
```

`--dry-run` should force dry-run mode even if `config.json` has `dry_run` set to `false`.

## 8. Trading Strategy

For each ticker:

1. Download recent historical data with `yfinance`.
2. Use adjusted close data as returned by `yfinance` defaults.
3. Confirm there are enough closing-price rows for the long moving average plus crossover comparison.
4. Calculate:
   - Short simple moving average.
   - Long simple moving average.
5. Compare the previous row and the latest row:
   - `BUY` when the short average crosses above the long average.
   - `SELL` when the short average crosses below the long average.
   - `HOLD` otherwise.
6. Log the signal to SQLite.
7. Apply position rules before placing or simulating any trade.
8. Continue to the next ticker if one ticker fails.

## 9. Position and Shorting Rules

The bot must determine whether each ticker is currently:

- `flat`
- `long`
- `short`

When `dry_run` is `false`, position state should come from Alpaca paper positions.

When `dry_run` is `true`, position state may be simulated from the bot's own SQLite trade history.

### Long-Only Mode

When `allow_shorting` is `false`:

- `BUY` should only happen if the bot is currently flat for that ticker.
- `SELL` should only happen if the bot currently holds a long position.
- `SELL` should close the long position only.
- The bot must not open short positions.
- The bot must not add to an existing long position.
- The bot must not add to an existing short position.

### Shorting Enabled

When `allow_shorting` is `true`:

- `BUY` should open a long position if currently flat.
- `BUY` should close an existing short position if currently short.
- `SELL` should close an existing long position if currently long.
- `SELL` should open a short position if currently flat.
- The bot must not add to an existing long position.
- The bot must not add to an existing short position.

The README must clearly explain that short selling is riskier and is only simulated in paper trading.

## 10. Alpaca Paper Trading

When `dry_run` is `true`:

- The bot should not call Alpaca to submit orders.
- The bot should log intended trades as dry-run trades.
- The bot may use SQLite history to simulate position state.

When `dry_run` is `false`:

- The bot must use Alpaca paper trading.
- The bot must require `alpaca.paper` to be `true`.
- The bot must refuse to run if `alpaca.paper` is `false`.
- The bot must submit market orders only.
- The bot must log the Alpaca order ID and order status when available.

## 11. Duplicate Trade Prevention

Version 1 only needs duplicate trade prevention within the same run.

The bot should not submit or simulate the same trade action twice for the same ticker during one execution.

## 12. SQLite Logging

The bot creates the SQLite database automatically if it does not exist.

SQLite table: `trade_log`

Recommended fields:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | INTEGER PRIMARY KEY | Auto-increment |
| `created_at` | TEXT | ISO 8601 timestamp |
| `ticker` | TEXT | Stock or ETF symbol |
| `signal` | TEXT | `BUY`, `SELL`, or `HOLD` |
| `side` | TEXT | `buy`, `sell`, or empty |
| `action` | TEXT | `open_long`, `close_long`, `open_short`, `close_short`, or empty |
| `position_before` | TEXT | `flat`, `long`, or `short` |
| `position_after` | TEXT | `flat`, `long`, or `short` |
| `quantity` | REAL | Configured order quantity |
| `last_close` | REAL | Latest close used for signal |
| `short_ma` | REAL | Latest short SMA |
| `long_ma` | REAL | Latest long SMA |
| `dry_run` | INTEGER | `1` or `0` |
| `order_id` | TEXT | Alpaca order ID, if submitted |
| `order_status` | TEXT | Alpaca order status, if available |
| `error` | TEXT | Error message, if applicable |

The bot should record `HOLD` decisions, but Discord should not alert on every `HOLD`.

## 13. Discord Alerts

Discord webhook alerts should be optional.

Alerts should be sent for:

- Bot startup.
- Submitted paper trades or dry-run simulated trades.
- Errors.
- Completion summary.

Alerts should not be sent for:

- Every `HOLD` signal.
- Normal per-ticker progress.

Discord failures should be logged but must not crash the trading run.

## 14. Logging and Run Summary

The bot should log to console and `logs/bot.log`.

Log levels:

- `INFO` for normal progress.
- `WARNING` for skipped trades and recoverable issues.
- `ERROR` for failed downloads, failed order submissions, and unexpected exceptions.

At the end of each run, summarize:

- Tickers processed.
- `BUY` signals.
- `SELL` signals.
- `HOLD` signals.
- Skipped trades.
- Failed tickers.
- Submitted or simulated trades.

## 15. README Requirements

The README must include:

- Plain-language project description.
- Clear paper-trading safety warning.
- Short selling risk warning.
- Windows Server 2022 setup steps.
- Python virtual environment setup.
- Dependency installation.
- How to create `config.json`.
- How to configure Alpaca paper API keys.
- How to configure Discord webhook alerts.
- How to run manually.
- How to schedule repeated runs later with Windows Task Scheduler.
- How to inspect logs and SQLite data.
- Troubleshooting.

## 16. Version 1 Acceptance Criteria

Version 1 is complete when:

- `bot.py` exists.
- `requirements.txt` exists.
- `config.example.json` exists with `dry_run: true` and `allow_shorting: false`.
- `.gitignore` exists.
- `data/.gitkeep` exists.
- `logs/.gitkeep` exists.
- `README.md` has beginner-friendly Windows Server 2022 setup instructions.
- Running `python bot.py` with a valid `config.json`:
  - Loads config.
  - Refuses to run if `alpaca.paper` is `false`.
  - Downloads ticker data from `yfinance`.
  - Calculates moving-average crossover signals.
  - Applies long-only or shorting-enabled position rules.
  - Prevents duplicate trade actions within the same run.
  - Writes signal and trade rows to SQLite.
  - Sends Discord alerts only for startup, trades, errors, and completion summary.
  - Submits Alpaca paper orders only when `dry_run` is `false`.
  - Continues processing other tickers if one ticker fails.

## 17. Future Enhancements

Future work should only be added after version 1 is working and the user explicitly asks for it. Version 1 should not include a dashboard, machine learning, backtesting, Docker, live trading, complex indicators, or extra features outside this PRD.
