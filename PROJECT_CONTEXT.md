# Project Context

## 1. Project Purpose

Python market monitoring and paper trading bot for Windows. It uses `yfinance`, Alpaca paper trading, SQLite, Discord webhooks, and config-driven tickers.

The project direction is paper-trading safety first, then research and backtesting, then carefully reviewed strategy-to-paper integration later.

## 2. Current Working Features

- Normal run: `python bot.py`
- Dry-run mode
- Alpaca paper mode only
- SQLite `trade_log`
- Discord startup, summary, trade, and error alerts
- Manual paper-order smoke test:

```powershell
python bot.py --paper-order-test MSFT buy 1 --confirm-paper-order
```

- Position tracking with signed quantity
- Open Alpaca order checks before submitting new orders
- Safe config validation
- Regime-filtered SMA volatility backtest:

```powershell
python bot.py --backtest
```

- Strategy comparison backtest:

```powershell
python bot.py --compare-strategies
```

- Strategy result charting from saved CSV files:

```powershell
python bot.py --plot-strategy-results
```

- SMA trend parameter sensitivity testing:

```powershell
python bot.py --sma-sensitivity
```

- Slow SMA trend stress testing:

```powershell
python bot.py --trend-stress-test
python bot.py --trend-stress-test --research-universe
python bot.py --trend-stress-test --etf-universe
```

- Slow SMA signal preview mode:

```powershell
python bot.py --preview-slow-sma-signals
python bot.py --preview-slow-sma-signals --research-universe
python bot.py --preview-slow-sma-signals --etf-universe
```

- Slow SMA target-position action preview mode:

```powershell
python bot.py --preview-slow-sma-actions
python bot.py --preview-slow-sma-actions --research-universe
python bot.py --preview-slow-sma-actions --etf-universe
```

- Slow SMA target-position paper execution:

```powershell
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper --research-universe
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper --etf-universe
```

- Backtest CSV outputs:
  - `data/backtest_results.csv`
  - `data/backtest_trades.csv`
  - `data/strategy_comparison_results.csv`
  - `data/strategy_comparison_trades.csv`
  - `data/strategy_portfolio_comparison.csv`
  - `data/strategy_robustness_summary.csv`
  - `data/strategy_portfolio_equity_curves.csv`
  - `data/strategy_ticker_equity_curves.csv`
  - `data/charts/`
  - `data/sma_sensitivity_results.csv`
  - `data/sma_sensitivity_portfolio.csv`
  - `data/trend_stress_test_results.csv`
  - `data/trend_stress_test_portfolio.csv`
  - `data/slow_sma_signal_preview.csv`
  - `data/slow_sma_action_preview.csv`

## 3. Important Safety Rules

- Never live trade.
- `alpaca.paper` must be `true`.
- `dry_run` defaults to `true`.
- `allow_shorting` defaults to `false`.
- `config.json` must remain private.
- No API keys or Discord webhook URLs in Git.
- Closing trades must not oversell or overbuy.
- Existing open orders must block duplicate order submission.
- Backtest mode must not call Alpaca.
- Backtest mode must not send Discord alerts.
- Research strategies must not be connected to live or paper execution until reviewed.
- Do not add crypto yet.

## 4. Current Local Setup Commands

Project path:

```text
C:\Users\lewis\OneDrive\Documents\Paper Trading Bot
```

Python version:

```text
3.12
```

Virtual environment:

```text
.venv
```

Activate:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run bot:

```powershell
python bot.py
```

## 5. Current Tested Status

- `yfinance` data works locally.
- SQLite database created at `data/trades.db`.
- Logs created at `logs/bot.log`.
- Discord webhook works.
- Alpaca paper account connection works.
- Alpaca paper account returned active status and buying power during testing.
- Manual AAPL paper buy was detected by the bot as long 1.
- Manual MSFT paper-order smoke test submitted successfully.
- `--backtest` command exists and creates CSV output files.
- `--compare-strategies` command exists and creates CSV output files.
- `--plot-strategy-results` command exists and creates PNG charts from saved CSV output when `matplotlib` is installed.
- `--sma-sensitivity` command exists and compares SMA trend parameter pairs.
- `--trend-stress-test` command exists and tests slow SMA pairs across slippage assumptions.
- `--preview-slow-sma-signals` command exists and previews slow SMA signals without trading.
- `--preview-slow-sma-actions` command exists and previews target-position alignment actions without trading.
- `--execute-slow-sma-paper` command exists and requires `--confirm-slow-sma-paper` before paper orders can be submitted.
- Slow SMA paper execution was tested locally and successfully submitted paper orders to close MSFT and open SPY, while AAPL was held.
- Strategy comparison simulator passed a local synthetic-data check.

## 6. Alpaca Paper Test Status

- Alpaca paper account connection is confirmed working.
- Manual AAPL paper buy was detected by the bot as long 1.
- Manual MSFT paper-order smoke test submitted successfully.
- Slow SMA target-position paper execution was tested locally with confirmed paper execution.
- The slow SMA paper execution held AAPL, submitted a paper order to close MSFT, and submitted a paper order to open SPY.
- The project must remain paper-only.

## 7. Known Current Paper Positions

- AAPL long 1
- SPY long 1

## 8. Current Next Development Phase

- Freeze the current working version before starting V2 work.
- Use `V2_ROADMAP.md` as the high-level plan for the next phase.
- V2 direction: safe refactor, shared cost model, strategy lab, new stock/ETF strategy candidates, crypto research later, loop/cron support later, and stronger risk management.
- The refactor must preserve all existing commands and behaviour.
- Do not add crypto yet; crypto starts later as monitoring and backtesting only.
- Do not add loop mode yet; keep once-per-command behaviour stable first.
- Do not connect additional strategies to execution until backtests, previews, and safety checks are reviewed.
- Slow SMA paper execution remains a separate explicit command, not normal `python bot.py` behaviour.

## 9. Files That Must Never Be Committed

- `config.json`
- `.venv/`
- `data/*.db`
- `logs/*.log`
- `data/backtest_results.csv`
- `data/backtest_trades.csv`
- `data/strategy_comparison_results.csv`
- `data/strategy_comparison_trades.csv`
- `data/strategy_portfolio_comparison.csv`
- `data/strategy_robustness_summary.csv`
- `data/strategy_portfolio_equity_curves.csv`
- `data/strategy_ticker_equity_curves.csv`
- `data/charts/`
- `data/sma_sensitivity_results.csv`
- `data/sma_sensitivity_portfolio.csv`
- `data/trend_stress_test_results.csv`
- `data/trend_stress_test_portfolio.csv`
- `data/slow_sma_signal_preview.csv`
- `data/slow_sma_action_preview.csv`
- Any file containing API keys or Discord webhook URLs

## 10. Useful Commands For Testing

Run the normal bot:

```powershell
python bot.py
```

Force dry-run mode:

```powershell
python bot.py --dry-run
```

Run the manual paper-order smoke test:

```powershell
python bot.py --paper-order-test MSFT buy 1 --confirm-paper-order
```

Run backtest mode:

```powershell
python bot.py --backtest
```

Run strategy comparison:

```powershell
python bot.py --compare-strategies
```

Run SMA sensitivity testing:

```powershell
python bot.py --sma-sensitivity
```

Run trend stress testing:

```powershell
python bot.py --trend-stress-test
python bot.py --trend-stress-test --etf-universe
```

Preview slow SMA signals:

```powershell
python bot.py --preview-slow-sma-signals
python bot.py --preview-slow-sma-signals --etf-universe
```

Preview slow SMA target-position actions:

```powershell
python bot.py --preview-slow-sma-actions
python bot.py --preview-slow-sma-actions --etf-universe
```

Execute slow SMA target-position paper alignment:

```powershell
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```

Create strategy result charts:

```powershell
python bot.py --plot-strategy-results
```

Check backtest outputs:

```powershell
Get-Content data\backtest_results.csv
Get-Content data\strategy_comparison_results.csv
Get-Content data\sma_sensitivity_portfolio.csv
Get-Content data\trend_stress_test_portfolio.csv
Get-Content data\slow_sma_signal_preview.csv
Get-Content data\slow_sma_action_preview.csv
Get-ChildItem data\charts
```

Check recent logs:

```powershell
Get-Content logs\bot.log -Tail 50
```
