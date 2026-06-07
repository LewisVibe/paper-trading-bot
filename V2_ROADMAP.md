# V2 Roadmap

This roadmap describes the next phase after the current working paper-trading version is frozen. V2 should preserve all existing commands and behaviour while making the project easier to extend, test, and operate.

## Guiding Rules

- Keep live trading disabled.
- Keep Alpaca execution paper-only unless a future phase explicitly changes that after review.
- Do not add crypto execution before crypto monitoring, preview, and backtesting are validated.
- Do not add loop mode until single-run commands remain stable.
- Avoid overfitting. Prefer robust strategy families and parameter clusters over one winning parameter set.

## 1. Strategy Lab Framework

Create a strategy lab that makes new ideas easy to compare without wiring them directly to execution.

- Create a clean strategy interface.
- Add a strategy registry.
- Allow new strategies to be benchmarked against existing strategies.
- Keep all strategy tests reproducible and config-driven.
- Support shared metrics, shared cost assumptions, shared universes, and shared output formats.

Existing benchmarks should include:

- `buy_and_hold_baseline`
- `sma_50_200_trend`
- `sma_60_200_trend`
- ETF `100/200` trend

New candidate strategies should include:

- 52-week high breakout
- Monthly ETF momentum rotation
- Volatility-scaled trend following
- Later crypto trend strategies

Research warning:

- Do not run large parameter searches just to find the best historical result.
- Treat any single winning parameter pair with suspicion.
- Prefer strategies that perform reasonably across assets, periods, costs, and nearby parameter choices.

## 2. More Realistic Backtest Costs

Add a shared cost model that every research mode uses.

Cost fields:

- `commission_per_trade`
- `commission_bps`
- `spread_bps`
- `slippage_bps`
- Crypto maker fee assumptions
- Crypto taker fee assumptions

Requirements:

- Include costs in every strategy comparison.
- Include costs in every stress test.
- Show gross and net results if that stays simple.
- Make cost assumptions visible in CSV outputs.
- Keep stock/ETF and crypto cost assumptions separate.

## 3. Refactor Plan

Split the current single-file implementation into a package structure:

```text
trading_bot/config.py
trading_bot/database.py
trading_bot/market_data.py
trading_bot/alpaca_client.py
trading_bot/execution.py
trading_bot/positions.py
trading_bot/discord_alerts.py
trading_bot/strategies/
trading_bot/research/
trading_bot/runners/
```

Refactor requirements:

- Preserve every existing command.
- Preserve current command output where practical.
- Preserve SQLite schema compatibility.
- Preserve paper-only safety checks.
- Preserve dry-run behaviour.
- Preserve slow SMA explicit execution gating.
- Add tests or small verification scripts around command routing before moving code.
- Move code in small slices, not one giant rewrite.

## 4. Crypto Phase

Crypto should start as research only.

Initial scope:

- Monitoring only.
- Backtesting only.
- Use Alpaca symbols like `BTC/USD` and `ETH/USD`.
- No shorting.
- No margin.
- Crypto-specific fees.
- Crypto-specific time-in-force values.
- Do not use stock `DAY` order assumptions for crypto.

Execution rule:

- Add crypto execution only after crypto preview and crypto backtests are validated.
- Keep crypto separate from stock/ETF execution paths until the differences are well understood.

## 5. Loop And Cron Support

Add repeated-running support after the single-run commands stay stable.

Future command:

```powershell
python bot.py --run-loop --interval-minutes 15
```

Requirements:

- Add a lockfile to prevent overlapping runs.
- Add maximum error handling before the loop exits or pauses.
- Keep the current once-per-command style for cron and scheduled jobs.
- Do not rely only on Windows Task Scheduler long term.
- Make loop logs readable and rotation-friendly.

## 6. Risk Management

Add portfolio-level controls before expanding execution.

Risk controls:

- `max_open_positions`
- `max_position_value`
- `max_portfolio_exposure`
- Per-asset notional sizing
- Paper-only kill switch
- Discord daily summary

Risk behaviour:

- Risk checks should run before order submission.
- Skipped actions should be logged clearly.
- Discord alerts should explain risk-based skips when alerts are enabled.
- Risk settings should be conservative by default.

## Recommended Implementation Order

A. Freeze current working version.

B. Refactor safely.

C. Add cost model.

D. Build strategy lab.

E. Add new stock/ETF strategy candidates.

F. Add crypto research only.

G. Add loop/cron runner.

H. Consider crypto paper execution.
