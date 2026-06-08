# Python Market Monitoring and Paper Trading Bot

This is a beginner-friendly Python bot for monitoring U.S. stocks and ETFs, researching daily strategies, recording activity in SQLite, sending Discord alerts, and optionally placing Alpaca paper trading orders.

It runs once and exits. To run it repeatedly, use Windows Task Scheduler.

For the current V2 project checkpoint, see [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md).

## Safety First

This project is for learning and paper trading only. It is not financial advice and it does not guarantee profits.

The default config uses:

- `dry_run: true`
- `allow_shorting: false`
- Alpaca paper mode only

The bot refuses to run if `alpaca.paper` is set to `false`. Research and backtest modes do not submit Alpaca orders and do not send Discord alerts.

Short selling is riskier than normal long-only trading because losses can grow quickly if price rises. In this project, short selling is only simulated or sent to an Alpaca paper account, never live trading.

## What The Bot Does

- Tracks a list of U.S. stock and ETF tickers.
- Downloads price history with `yfinance`.
- Calculates moving-average signals.
- Creates `BUY`, `SELL`, or `HOLD` signals.
- Supports long-only trading by default.
- Supports optional paper shorting with `allow_shorting: true`.
- Prevents pyramiding.
- Tracks positions using signed quantity.
- Checks for open Alpaca orders before submitting new paper orders.
- Logs every signal and trade decision to SQLite.
- Sends Discord alerts for startup, trades, errors, and completion summary.
- Does not alert every `HOLD`.
- Includes a manual paper-order smoke test.
- Includes a research backtest for `regime_sma_vol_filter`.
- Includes strategy comparison backtesting.
- Exports strategy equity curves for visual inspection.
- Creates simple matplotlib charts from saved strategy comparison results.
- Includes SMA trend parameter sensitivity testing.
- Includes slow SMA trend stress testing across slippage assumptions.
- Includes slow SMA signal preview mode with no order execution.

## Files

- `bot.py` - the bot.
- `config.example.json` - safe example settings.
- `requirements.txt` - Python packages.
- `data/trades.db` - created automatically when the bot runs.
- `logs/bot.log` - created automatically when the bot runs.
- `data/backtest_results.csv` - created by `--backtest`.
- `data/backtest_trades.csv` - created by `--backtest`.
- `data/strategy_comparison_results.csv` - created by `--compare-strategies`.
- `data/strategy_comparison_trades.csv` - created by `--compare-strategies`.
- `data/strategy_portfolio_comparison.csv` - created by `--compare-strategies`.
- `data/strategy_robustness_summary.csv` - created by `--compare-strategies`.
- `data/strategy_portfolio_equity_curves.csv` - created by `--compare-strategies`.
- `data/strategy_ticker_equity_curves.csv` - created by `--compare-strategies`.
- `data/charts/` - created by `--plot-strategy-results`.
- `data/sma_sensitivity_results.csv` - created by `--sma-sensitivity`.
- `data/sma_sensitivity_portfolio.csv` - created by `--sma-sensitivity`.
- `data/trend_stress_test_results.csv` - created by `--trend-stress-test`.
- `data/trend_stress_test_portfolio.csv` - created by `--trend-stress-test`.
- `data/slow_sma_signal_preview.csv` - created by `--preview-slow-sma-signals`.
- `data/slow_sma_action_preview.csv` - created by `--preview-slow-sma-actions`.

## Windows Server 2022 Setup

Install Python 3.11 or newer from the official Python website:

[Python downloads](https://www.python.org/downloads/windows/)

During installation, select **Add python.exe to PATH**.

Open PowerShell in this project folder:

```powershell
cd "C:\Users\lewis\OneDrive\Documents\Paper Trading Bot"
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Create Your Config

Copy the example config:

```powershell
Copy-Item config.example.json config.json
```

Open `config.json` and edit the ticker list:

```json
"tickers": ["AAPL", "MSFT", "SPY"]
```

Use only U.S. stocks and ETFs for version 1.

## Config Options

Important settings:

- `short_window` - shorter moving average window.
- `long_window` - longer moving average window.
- `order_quantity` - number of shares to paper trade.
- `dry_run` - when `true`, the bot does not submit Alpaca orders.
- `allow_shorting` - when `false`, the bot only opens and closes long positions.
- `database_path` - where SQLite trade history is stored.
- `log_file` - where the text log is stored.
- `strategy` - research strategy settings for `regime_sma_vol_filter`.
- `backtest` - backtest cash, sizing, slippage, history, and output settings.

Keep this unless you know what you are changing:

```json
"alpaca": {
  "paper": true
}
```

If `alpaca.paper` is `false`, the bot refuses to run.

## Alpaca Paper Trading

You only need Alpaca keys when `dry_run` is `false`.

Create or log into an Alpaca account and use paper trading API keys, not live keys:

[Alpaca paper trading](https://alpaca.markets/)

Add the keys to `config.json`:

```json
"alpaca": {
  "paper": true,
  "api_key": "YOUR_PAPER_API_KEY",
  "secret_key": "YOUR_PAPER_SECRET_KEY"
}
```

Or set them as Windows environment variables:

```powershell
setx ALPACA_API_KEY "YOUR_PAPER_API_KEY"
setx ALPACA_SECRET_KEY "YOUR_PAPER_SECRET_KEY"
```

Open a new PowerShell window after using `setx`.

## Discord Alerts

Discord alerts are optional. The bot sends alerts only for:

- Startup.
- Simulated or submitted trades.
- Errors.
- Completion summary.

It does not send an alert for every `HOLD`.

To enable alerts, create a Discord webhook URL for a channel, then set:

```json
"discord": {
  "enabled": true,
  "webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
}
```

You can also use an environment variable:

```powershell
setx DISCORD_WEBHOOK_URL "YOUR_DISCORD_WEBHOOK_URL"
```

## Run the Bot

With the virtual environment activated:

```powershell
python bot.py
```

Use a different config file:

```powershell
python bot.py --config config.json
```

Force safe dry-run mode:

```powershell
python bot.py --dry-run
```

Run the manual paper-order smoke test:

```powershell
python bot.py --paper-order-test MSFT buy 1 --confirm-paper-order
```

Run the regime-filtered SMA volatility backtest:

```powershell
python bot.py --backtest
```

Compare research strategies:

```powershell
python bot.py --compare-strategies
```

Run SMA parameter sensitivity testing:

```powershell
python bot.py --sma-sensitivity
```

Run slow SMA trend stress testing:

```powershell
python bot.py --trend-stress-test
python bot.py --trend-stress-test --research-universe
python bot.py --trend-stress-test --etf-universe
```

Run the research-only monthly ETF momentum rotation backtest:

```powershell
python bot.py --etf-rotation-backtest
```

Run the research-only adaptive risk-on/off momentum backtest:

```powershell
python bot.py --adaptive-momentum-backtest
```

Create a consolidated research ranking report from saved CSV outputs:

```powershell
python bot.py --research-report
```

Create a walk-forward validation report from saved in/out-of-sample CSV outputs:

```powershell
python bot.py --walk-forward-report
```

Create a conservative strategy promotion checklist from saved research reports:

```powershell
python bot.py --strategy-promotion-report
```

Preview current signals for promoted research candidates without trading:

```powershell
python bot.py --preview-promoted-strategies
```

Compare promoted desired positions with current paper positions without trading:

```powershell
python bot.py --preview-promoted-actions
```

To explicitly read Alpaca paper positions for preview context while leaving `dry_run`
unchanged:

```powershell
python bot.py --preview-promoted-actions --use-paper-positions-readonly
```

This flag is read-only and only works with `--preview-promoted-actions`. It requires
Alpaca paper mode and paper API credentials, does not change `config.json`, and is
different from setting `dry_run=false`. If paper positions cannot be read, the preview
keeps using conservative `position_unavailable` rows.

Show the saved promoted action preview as a read-only terminal summary:

```powershell
python bot.py --show-promoted-actions
```

This display helper only reads `data/promoted_strategy_action_preview.csv`, which is created by
`python bot.py --preview-promoted-actions`. It does not refresh market data, call Alpaca, read
positions, submit or cancel orders, write SQLite rows, or send Discord alerts.

Create a research-only risk preview from saved promoted strategy CSVs:

```powershell
python bot.py --promoted-risk-preview
```

This report reads `data/promoted_strategy_preview.csv` and, when available,
`data/promoted_strategy_action_preview.csv`. It writes `data/promoted_risk_preview.csv`.
It reads saved CSV files only. It does not refresh market data, call yfinance, call Alpaca,
read live/current positions directly, submit/cancel/create orders, write SQLite `trade_log`
rows, send Discord alerts, or approve execution. Every output row is marked
`research_only=True` and `preview_only=True`.

When `latest_close` is available in `data/promoted_strategy_preview.csv`, the risk preview
also writes `latest_close`, `assumed_quantity`, and `estimated_desired_notional`.
`estimated_desired_notional` is calculated from the saved close price and
`assumed_quantity=1`. These are saved-data-only estimates, not order instructions, and
they do not refresh prices or positions.

Current risk checks include:

- desired long count versus a conservative `max_open_positions`
- duplicate ticker exposure across promoted strategy rows
- concentration risk where multiple promoted strategies want the same ticker long
- unavailable current position data from the action preview
- notional data quality for saved `latest_close` values

Show the saved promoted risk preview as a read-only terminal summary:

```powershell
python bot.py --show-promoted-risk
```

Run this after `python bot.py --promoted-risk-preview`. This display helper only reads
`data/promoted_risk_preview.csv`. It does not refresh market data, call yfinance, call
Alpaca, read live/current positions, submit/cancel/create orders, write files, write
SQLite `trade_log` rows, send Discord alerts, or approve execution.

It displays count by `risk_status`, count by `risk_check`, count by `desired_position`,
estimated desired notional by strategy, duplicated desired notional by ticker, unique
desired notional by ticker, unique account-style desired notional total,
blocked-for-review rows, warning rows, and a compact table of risk rows. Duplicated
desired notional by ticker intentionally counts overlapping promoted strategy rows, so
two promoted strategies wanting AAPL long can count AAPL twice. Unique desired notional
by ticker counts each desired-long ticker once, which is closer to an account-style
exposure view.

Create a research-only ticker-level consensus report from saved promoted strategy rows:

```powershell
python bot.py --promoted-consensus-preview
```

This report reads `data/promoted_strategy_preview.csv` and writes
`data/promoted_consensus_preview.csv`. It groups promoted strategy rows by ticker,
counts desired long/flat/other votes, and labels each ticker as `unanimous_long`,
`unanimous_flat`, `mixed_long_flat`, `no_supported_votes`, or `unknown`. It is
research-only and preview-only: every row has `execution_eligible=False`, and the
report does not refresh market data, call yfinance, call Alpaca, read live/current
positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts,
or approve execution.

Create a research-only decision policy preview from saved promoted reports:

```powershell
python bot.py --promoted-decision-preview
```

This report reads `data/promoted_consensus_preview.csv`,
`data/promoted_strategy_action_preview.csv`, and `data/promoted_risk_preview.csv`.
It writes `data/promoted_decision_preview.csv` and labels each ticker with a
non-executable `decision_state`, such as `blocked_strategy_disagreement`,
`blocked_risk_review`, `no_action_unanimous_flat`, `review_warning`, or
`research_only_unanimous_long`. Every row has `execution_approved=False`,
`research_only=True`, and `preview_only=True`. It is a policy preview only and does
not refresh market data, call yfinance, call Alpaca, read live/current positions,
create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve
execution.

Display the saved promoted decision preview without trading:

```powershell
python bot.py --show-promoted-decision
```

Run this after `python bot.py --promoted-decision-preview`. This display helper only
reads `data/promoted_decision_preview.csv`; it does not refresh market data, call
yfinance, call Alpaca, read positions, create/submit/cancel orders, write SQLite
`trade_log`, send Discord alerts, or approve execution.

Refresh the promoted review chain without approving execution:

```powershell
python bot.py --refresh-promoted-review
```

This convenience command runs the promoted review chain in order, including the
read-only paper-position action preview path, then prints a compact decision summary.
It writes `data/promoted_review_refresh_summary.csv`. It does not change `dry_run`,
create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve
execution.

Preview slow SMA signals without trading:

```powershell
python bot.py --preview-slow-sma-signals
python bot.py --preview-slow-sma-signals --research-universe
python bot.py --preview-slow-sma-signals --etf-universe
```

Preview slow SMA target-position actions without trading:

```powershell
python bot.py --preview-slow-sma-actions
python bot.py --preview-slow-sma-actions --research-universe
python bot.py --preview-slow-sma-actions --etf-universe
```

Execute slow SMA target-position alignment in Alpaca paper trading:

```powershell
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper --research-universe
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper --etf-universe
```

Create simple PNG charts from saved strategy comparison CSV files:

```powershell
python bot.py --plot-strategy-results
```

## V2 Baseline Verification

Before V2 refactors, run the baseline verifier:

```powershell
python scripts\verify_v2_baseline.py
```

The script runs safe command checks only. It does not run `--paper-order-test` or `--execute-slow-sma-paper`, so it does not submit Alpaca orders.

Before GitHub commits or pushes, run the repository safety verifier:

```powershell
python scripts\verify_repo_safety.py
```

It checks that private files, generated CSVs, database files, logs, charts, virtual environments, and obvious secret-like filenames are not tracked or staged.

Create a local deployment readiness audit before any future VPS/server handoff:

```powershell
python bot.py --deployment-readiness-report
```

This is a reporting-only check for future Windows Server VPS use. It may inspect local files and Git metadata, but it does not deploy, create Windows Task Scheduler tasks, refresh market data, call Alpaca, submit orders, send Discord alerts, or approve execution. Any future Windows Task Scheduler setup must start with report/display commands only and is not execution approval.

Create a research-only portfolio risk policy audit before any future execution discussion:

```powershell
python bot.py --portfolio-risk-policy-report
```

This reads saved CSVs and `config.example.json` only, writes `data/portfolio_risk_policy_report.csv`, and documents conservative report-only policies such as paper-only mode, dry-run default, shorting disabled, proposed max open positions, desired notional review, duplicate ticker exposure, strategy disagreement, execution approval status, future kill switch work, and future daily summary work. It does not enforce risk checks, change order sizing, read live positions/account equity, call Alpaca, submit orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Display the saved portfolio risk policy report without rerunning it:

```powershell
python bot.py --show-portfolio-risk-policy
```

This is a read-only terminal display helper for `data/portfolio_risk_policy_report.csv`. It does not refresh data, read positions, enforce risk policy, submit orders, write files, or approve execution.

Create a reporting-only readiness audit for future paper kill-switch design:

```powershell
python bot.py --paper-kill-switch-readiness-report
```

This writes `data/paper_kill_switch_readiness_report.csv` and audits what would be required for a future paper-only kill switch. It does not add a config setting, enforce a kill switch, change order paths, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Create a design/report-only paper kill-switch gate scaffold:

```powershell
python bot.py --paper-kill-switch-gate-report
```

This writes `data/paper_kill_switch_gate_report.csv` and checks static/saved prerequisites for a future paper kill-switch gate, including safe config example defaults, confirmation-gated high-risk commands, isolated helper availability, existing readiness/eligibility reports, and whether defensive allocation remains blocked. It explicitly reports that the helper is not wired into order paths and does not add enforcement, create order instructions, call Alpaca, write SQLite `trade_log`, send Discord alerts, promote strategies, or approve execution.

Verify the future paper kill-switch enforcement contract without wiring enforcement into order paths:

```powershell
python scripts\verify_paper_kill_switch_enforcement_contract.py
```

This no-network verifier defines the contract that any future defensive paper-execution command would have to satisfy before execution design can continue. It checks paper-only/default boundaries, confirmation gates, report/preview non-approval, and that the current gate remains blocked/future-work-required. It does not add a bot command, enforce a kill switch, touch order paths, or approve execution.

An isolated pure helper also exists at `trading_bot/safety/paper_kill_switch.py`. It can evaluate plain Python safety context values for future paper kill-switch design tests, and the saved readiness reports recognize it as partial progress, but it is not wired into `--paper-order-test`, `--execute-slow-sma-paper`, normal `python bot.py` behavior, or any order path.

Create a saved-data-only defensive execution readiness report:

```powershell
python bot.py --defensive-execution-readiness-report
```

This writes `data/defensive_execution_readiness_report.csv` and summarizes what still blocks future paper execution design for the defensive allocation path. It combines saved defensive allocation, kill-switch gate, contract-verifier presence, execution eligibility, and portfolio risk policy state. It does not start execution design, add enforcement to order paths, create order instructions, call Alpaca, write SQLite `trade_log`, send Discord alerts, promote strategies, or approve execution.

Create a saved-data-only execution eligibility view:

```powershell
python bot.py --execution-eligibility-report
```

This writes `data/execution_eligibility_report.csv` and combines saved promoted decision, portfolio risk policy, paper kill-switch readiness, and deployment readiness reports into a final non-executable eligibility view. It does not refresh previews, enforce risk policy, implement a kill switch, create order instructions, call Alpaca, read positions, submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Build a static saved-CSV research dashboard:

```powershell
python bot.py --build-research-dashboard
```

This writes `data/dashboard/research_dashboard.html` from existing saved CSV reports and optional existing chart PNGs. When available, it also displays `data/defensive_research_state_report.csv` as an optional defensive state section. It is a static HTML file only: no Flask, Streamlit, Dash, FastAPI, localhost server, network port, market-data refresh, Alpaca call, order action, SQLite `trade_log` write, Discord alert, risk enforcement, or execution approval is added.

The initial `trading_bot/` package skeleton now exists for V2 refactoring, but `bot.py` still owns the current behaviour for now.

See `docs/V2_REFACTOR_INVENTORY.md` for the current extraction inventory and recommended next refactor order.

See `docs/V2_RESEARCH_CHECKPOINT.md` for the current research conclusions and safety boundary before adding more strategy work.

See `docs/CODEX_WORKFLOW.md` for the recommended prompt and verification workflow for future Codex tasks.

## Research Backtesting

Backtest mode is research-only. It does not call Alpaca, does not submit orders, and does not send Discord alerts.

The current research strategy is `regime_sma_vol_filter`:

- Uses SPY as the market regime ticker.
- Enters long only when SPY is above its 200-day SMA.
- Requires the ticker to be above its 200-day SMA.
- Uses a 20-day SMA crossing above a 50-day SMA as the entry trigger.
- Skips new entries when recent realised volatility is unusually high.
- Exits on a bearish 20/50 crossover or when the ticker falls below its 200-day SMA.
- Uses next-day open execution with slippage to avoid look-ahead bias.

Outputs:

```text
data/backtest_results.csv
data/backtest_trades.csv
```

The normal research backtest uses the shared research-only cost model for the configured default slippage assumption. It does not connect to Alpaca execution.

Strategy comparison mode compares:

- `buy_and_hold_baseline`
- `sma_20_50_basic`
- `sma_20_50_regime`
- `sma_50_200_trend`
- `buy_above_200_exit_below_200`
- `fifty_two_week_high_breakout`

Buy-and-hold is included as a benchmark so active strategies can be compared against simply owning the ticker.

Outputs:

```text
data/strategy_comparison_results.csv
data/strategy_comparison_trades.csv
data/strategy_portfolio_comparison.csv
data/strategy_robustness_summary.csv
data/strategy_portfolio_equity_curves.csv
data/strategy_ticker_equity_curves.csv
data/charts/
```

Strategy comparison uses the shared research-only cost model for the configured default slippage assumption. The 52-week high breakout candidate is included here as research-only and is not connected to Alpaca execution.

SMA sensitivity mode tests whether the 50/200 trend strategy is robust across nearby parameter choices:

- `20 / 100`
- `30 / 150`
- `40 / 160`
- `50 / 200`
- `60 / 200`
- `100 / 200`

Outputs:

```text
data/sma_sensitivity_results.csv
data/sma_sensitivity_portfolio.csv
```

SMA sensitivity uses the shared research-only cost model for the configured default slippage assumption. It does not connect to Alpaca execution.

ETF rotation backtest mode tests a long-only monthly momentum rotation across a default liquid ETF universe. It uses SPY as the regime filter, holds the top 3 eligible ETFs by default, skips partial rebalance trades below `100.0`, reports SPY/QQQ/equal-weight buy-and-hold benchmarks, saves only research CSV files, and is not connected to Alpaca execution. `data/etf_rotation_results.csv` includes `full_period`, `in_sample`, and `out_of_sample` portfolio rows using a simple chronological 70% / 30% split so the walk-forward report can pair the strategy.

Outputs:

```text
data/etf_rotation_results.csv
data/etf_rotation_trades.csv
data/etf_rotation_equity_curve.csv
```

ETF rotation robustness mode reads saved ETF rotation equity/trade CSVs only and writes fixed chronological out-of-sample rows for `split_60_40`, `split_70_30`, and `split_80_20`. It does not rerun the strategy, change ETF rotation rules, download market data, call Alpaca, write SQLite `trade_log`, send Discord alerts, or approve execution. These rows let volatility-managed ETF robustness compare against matching monthly ETF rotation split metrics.

Command:

```text
python bot.py --etf-rotation-robustness
```

Output:

```text
data/etf_rotation_robustness_report.csv
```

ETF breadth regime backtest mode reads a saved ETF close-history CSV only and tests a fixed research-only breadth regime allocation. The expected saved input is `data/etf_breadth_price_history.csv` with `date,ticker,close` columns. It classifies regimes from ETF breadth versus 200-day SMA and SPY trend, then writes research CSVs without downloading market data, calling Alpaca, creating orders, writing SQLite `trade_log`, sending Discord alerts, changing existing strategy logic, or approving execution.

Build the saved ETF close-history input first when it is missing:

```text
python bot.py --build-etf-breadth-price-history
```

The builder uses the existing research market-data/yfinance pattern to write `data/etf_breadth_price_history.csv`. It is research data-prep only; it does not call Alpaca, read positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, change strategy logic, or approve execution.

Command:

```text
python bot.py --etf-breadth-regime-backtest
```

Outputs:

```text
data/etf_breadth_regime_backtest.csv
data/etf_breadth_regime_summary.csv
```

ETF breadth regime decision mode reads saved breadth backtest/summary rows and saved defensive comparison/robustness rows when available. It compares breadth regime metrics against `monthly_etf_momentum_rotation` and `volatility_managed_dual_momentum_etf`, then labels the idea conservatively as underperforming, diagnostic-only, promising-needs-robustness, or insufficient-data. It does not download market data, call Alpaca, create orders, change promotion logic, or approve execution.

Command:

```text
python bot.py --etf-breadth-regime-decision-report
```

Output:

```text
data/etf_breadth_regime_decision_report.csv
```

ETF breadth regime robustness mode reads the saved ETF breadth price history and evaluates the fixed breadth allocation across `split_60_40`, `split_70_30`, and `split_80_20` out-of-sample periods. It labels the idea conservatively as `robust_diagnostic_candidate`, `split_sensitive_diagnostic`, `not_robust`, or `insufficient_data`. It remains research/reporting only and does not download market data, call Alpaca, create orders, promote the strategy, or approve execution.

Command:

```text
python bot.py --etf-breadth-regime-robustness
```

Output:

```text
data/etf_breadth_regime_robustness_report.csv
```

Vol-managed ETF backtest mode tests the first advanced long-only ETF research idea from the deep research shortlist. The fixed strategy, `volatility_managed_dual_momentum_etf`, uses the ETF rotation universe, monthly rebalance, top 3 momentum selection, 200-day SMA asset and SPY regime filters, 63-day realised volatility, inverse-volatility sizing, and a 10% annual target-volatility cap with gross exposure capped at 100%. It does not use leverage, margin, shorting, Alpaca, SQLite `trade_log`, Discord alerts, or execution approval.

Command:

```text
python bot.py --vol-managed-etf-backtest
```

Outputs:

```text
data/vol_managed_etf_results.csv
data/vol_managed_etf_trades.csv
data/vol_managed_etf_equity_curve.csv
data/vol_managed_etf_iteration_log.csv
```

Vol-managed ETF robustness mode checks the same fixed strategy across fixed chronological splits: `split_60_40`, `split_70_30`, and `split_80_20`. It compares against matching monthly ETF rotation robustness rows from `data/etf_rotation_robustness_report.csv` when available, falling back to the existing 70/30 ETF rotation result if the fixed-split report has not been generated yet. It does not tune parameters, change strategy rules, call Alpaca, write SQLite `trade_log`, send Discord alerts, or approve execution.

Command:

```text
python bot.py --vol-managed-etf-robustness
```

Output:

```text
data/vol_managed_etf_robustness_report.csv
```

Adaptive momentum backtest mode is research-only. It ranks risk ETFs by fixed multi-horizon momentum with a volatility penalty, uses SPY as the risk regime filter, and rotates to defensive ETFs when the regime is weak. It saves only research CSV files and is not connected to Alpaca execution. `data/adaptive_momentum_results.csv` includes `full_period`, `in_sample`, and `out_of_sample` portfolio rows using the same simple chronological 70% / 30% reporting split as ETF rotation so the walk-forward report can pair the strategy.

Outputs:

```text
data/adaptive_momentum_results.csv
data/adaptive_momentum_trades.csv
data/adaptive_momentum_equity_curve.csv
```

Research report mode reads existing research CSV files and creates a side-by-side ranked report. It does not rerun backtests, download data, submit orders, or send alerts. The report keeps all-row rankings for transparency, adds a decision-view ranking that prefers full-period portfolio-level rows, separates buy-and-hold benchmarks from active strategy candidates, and includes simple diagnostic columns explaining return gaps, drawdown tradeoffs, turnover, and likely underperformance reasons.

Output:

```text
data/research_report.csv
```

Walk-forward report mode reads existing research CSV files and compares matching `in_sample` and `out_of_sample` rows. It labels robustness conservatively, adds portfolio/single-ticker and benchmark/active classifications, keeps portfolio-level rows as the headline decision view, includes ETF rotation and adaptive momentum when their period rows have been generated, and does not rerun backtests, download data, submit orders, or send alerts.

Output:

```text
data/walk_forward_report.csv
```

Strategy promotion report mode combines `data/research_report.csv` and `data/walk_forward_report.csv` into a conservative checklist. A `preview_candidate` status means future preview-mode research only; it does not approve paper execution.

Output:

```text
data/strategy_promotion_report.csv
```

Defensive strategy report mode reads saved research and walk-forward reports and scores portfolio-level active strategies for defensive usefulness. It does not require beating buy-and-hold CAGR, and instead rewards lower drawdown, strong out-of-sample Sharpe/Calmar, and robust or improved walk-forward labels. It is research-only and does not approve execution.

Output:

```text
data/defensive_strategy_report.csv
```

Defensive candidate comparison mode reads saved walk-forward, defensive, promotion, and vol-managed ETF reports to compare `monthly_etf_momentum_rotation`, `volatility_managed_dual_momentum_etf`, and `adaptive_risk_on_off_momentum`. It separates raw metric rank from policy rank, focuses on out-of-sample Sharpe/Calmar, drawdown, fixed-split consistency, trade count, turnover burden, and strategy complexity. It is research-only and does not approve execution.

Command:

```text
python bot.py --defensive-candidate-comparison
```

Output:

```text
data/defensive_candidate_comparison.csv
```

Defensive research state report mode reads saved defensive comparison, ETF breadth, short research, promoted decision, portfolio risk, and execution eligibility CSVs where available. It consolidates the current stock/ETF defensive checkpoint into one saved report without rerunning backtests, refreshing market data, calling Alpaca, creating orders, writing SQLite `trade_log`, sending Discord alerts, promoting strategies, or approving execution.

Command:

```text
python bot.py --defensive-research-state-report
```

Output:

```text
data/defensive_research_state_report.csv
```

Defensive allocation preview mode reads the saved defensive research state report and writes a compact posture preview for the lead defensive reference, secondary/split-sensitive checks, breadth diagnostic context, adaptive monitoring, paused short research, and the execution gate. It is preview/reporting only: it creates no order instructions, promotes no strategy, and grants no execution approval.

Command:

```text
python bot.py --defensive-allocation-preview
```

Output:

```text
data/defensive_allocation_preview.csv
```

Defensive allocation risk preview mode reads `data/defensive_allocation_preview.csv` and checks whether the saved posture preview is complete and safely non-executable before any future defensive allocation decision report is considered. It checks expected components, execution approval flags, order-instruction style columns, split sensitivity, diagnostic-only breadth status, adaptive complexity, paused short research, and the blocked execution gate. It is saved-data-only and does not approve execution.

Command:

```text
python bot.py --defensive-allocation-risk-preview
```

Output:

```text
data/defensive_allocation_risk_preview.csv
```

Defensive allocation decision report mode combines the saved defensive allocation preview and risk preview into a final non-executable decision checkpoint. It answers whether the current defensive allocation posture can move toward paper-execution design; the current expected answer is no/not yet while execution remains blocked and future kill-switch, risk, and confirmation gates are not cleared. It does not create order instructions, promote strategies, or approve execution.

Command:

```text
python bot.py --defensive-allocation-decision-report
```

Output:

```text
data/defensive_allocation_decision_report.csv
```

ETF defensive drawdown comparison mode reads saved monthly ETF rotation and vol-managed ETF equity curves plus fixed-split robustness reports. It compares worst drawdown periods and the `split_80_20` out-of-sample drawdown tradeoff, including whether lower drawdown came with weaker CAGR/Sharpe/Calmar context. It is research-only and does not rerun backtests, refresh market data, call Alpaca, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.

Command:

```text
python bot.py --etf-defensive-drawdown-comparison
```

Output:

```text
data/etf_defensive_drawdown_comparison.csv
```

ETF defensive comparison charting reads saved ETF rotation and vol-managed ETF equity curves only and writes PNG diagnostics under `data/charts/`. It creates one equity comparison chart and one drawdown comparison chart. It does not rerun backtests, refresh market data, call Alpaca, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.

Command:

```text
python bot.py --plot-etf-defensive-comparison
```

Outputs:

```text
data/charts/etf_defensive_equity_comparison.png
data/charts/etf_defensive_drawdown_comparison.png
```

Defensive research refresh mode runs the current defensive saved-report/dashboard chain in order and writes a small step summary. It refreshes saved-data reports/charts where safe, checks the saved vol-managed robustness report as a prerequisite, and does not rerun market-data-backed backtests. It does not call Alpaca, read positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.

Command:

```text
python bot.py --refresh-defensive-research
```

Output:

```text
data/defensive_research_refresh_summary.csv
```

Drawdown period report mode reads saved equity-curve CSV files and identifies major portfolio drawdown periods for the main benchmark and active research candidates. It compares active drawdowns with matching benchmark windows where dates overlap, marks missing curves as `insufficient_data`, and remains research-only.

Command:

```text
python bot.py --drawdown-period-report
```

Output:

```text
data/drawdown_period_report.csv
```

Short-selling readiness report mode performs a static/local readiness audit for possible future short-selling research and preview work. It does not enable shorting, add short strategies, create orders, call Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, or approve execution.

Command:

```text
python bot.py --short-selling-readiness-report
```

Output:

```text
data/short_selling_readiness_report.csv
```

Short hedge backtest mode tests a synthetic SPY-only short hedge concept for research. It enters a research short when SPY closes below its 200-day SMA and returns flat when SPY closes at or above the 200-day SMA. It writes full-period, in-sample, and out-of-sample result rows, plus trades and an equity curve. Result rows include `research_status`, `research_conclusion`, and `required_next_step`; the initial simple rule is labelled not useful when CAGR, Sharpe, and Calmar are negative. It does not enable `allow_shorting`, create or submit orders, call Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, model borrow availability, or approve execution. Borrow fees are explicitly marked `not_modelled_initial_research`.

Command:

```text
python bot.py --short-hedge-backtest
```

Outputs:

```text
data/short_hedge_backtest_results.csv
data/short_hedge_backtest_trades.csv
data/short_hedge_equity_curve.csv
```

Short strategy lab mode tests one controlled multi-ticker ETF short-selling research hypothesis after the simple SPY short hedge failed. The fixed strategy, `research_weak_etf_short_momentum`, shorts the weakest two liquid ETFs by 126-day return only when SPY is below its 200-day SMA and each selected ETF is below its own 200-day SMA. It rebalances monthly, stays short/cash only, caps synthetic gross short exposure at 1x, and records a fixed placeholder borrow-fee assumption of `borrow_fee_bps_annual=300`. It does not run a parameter search, enable `allow_shorting`, add short preview or execution, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, add crypto shorting, or approve execution.

Command:

```text
python bot.py --short-strategy-lab
```

Outputs:

```text
data/short_strategy_lab_results.csv
data/short_strategy_lab_trades.csv
data/short_strategy_lab_equity_curve.csv
data/short_strategy_iteration_log.csv
```

Crypto research preview mode starts the crypto phase as a scaffold only. It writes the current research universe (`BTC/USD`, `ETH/USD`, `LTC/USD`) with execution, shorting, margin, and execution approval all disabled. It does not refresh data, call Alpaca, read positions, submit or cancel orders, write SQLite `trade_log`, or send Discord alerts.

Output:

```text
data/crypto_research_preview.csv
```

Crypto strategy lab mode backtests a tiny fixed research-only strategy set for `BTC/USD`, `ETH/USD`, and `LTC/USD` using yfinance-compatible daily symbols (`BTC-USD`, `ETH-USD`, `LTC-USD`). The per-symbol strategies are `crypto_buy_and_hold_baseline`, `crypto_sma_50_200_trend`, `crypto_buy_above_200_exit_below_200`, and one controlled iteration: `crypto_buy_above_200_with_vol_gate`. The volatility-gate strategy uses fixed parameters only: 20-day realised volatility, trailing 252-day median volatility, and a 1.5x gate for new entries. The lab also writes a separate portfolio-style BTC/ETH/cash rotation test, `crypto_monthly_btc_eth_momentum_rotation`, using fixed monthly rebalance, 126-day momentum ranking, and a 200-day SMA absolute trend filter. It writes full-period, in-sample, and out-of-sample rows, plus an iteration log to discourage tuning after seeing results. Results include simple crypto research cost assumptions: `crypto_taker_fee_bps=10`, `crypto_spread_bps=5`, and `crypto_slippage_bps=10`. It does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Outputs:

```text
data/crypto_strategy_lab_results.csv
data/crypto_strategy_lab_trades.csv
data/crypto_strategy_iteration_log.csv
data/crypto_rotation_results.csv
data/crypto_rotation_trades.csv
```

The BTC/ETH/cash rotation is kept in separate CSVs because it is a portfolio-style strategy rather than a single-symbol strategy. The existing `--crypto-strategy-report` and `--crypto-strategy-decision-report` compare per-symbol strategies against matching per-symbol buy-and-hold benchmarks and do not directly rank the rotation yet.

Crypto strategy report mode reads `data/crypto_strategy_lab_results.csv` and writes a saved-data-only comparison report. It compares each strategy against `crypto_buy_and_hold_baseline` for the same symbol and period, including CAGR gap, drawdown reduction, and whether the strategy beats buy-and-hold on both CAGR and Calmar. It is research-only and does not approve execution.

Output:

```text
data/crypto_strategy_report.csv
```

Crypto strategy decision report mode reads `data/crypto_strategy_lab_results.csv` and `data/crypto_strategy_report.csv`, then writes a symbol-level decision report. It prefers out-of-sample Calmar and Sharpe over full-period CAGR, checks whether the best out-of-sample strategy beats buy-and-hold, and keeps every row research-only. It is not execution approval.

Output:

```text
data/crypto_strategy_decision_report.csv
```

Crypto cost stress report mode reruns the existing crypto strategy lab across four explicit one-way cost assumptions: `zero_cost` at 0 bps, `default_cost` at 25 bps, `high_cost` at 50 bps, and `extreme_cost` at 100 bps. It includes the existing crypto strategies only, compares each strategy against its own default-cost result, and marks every row research-only. It does not add strategies, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Output:

```text
data/crypto_cost_stress_report.csv
```

Crypto robustness report mode reruns the existing per-symbol crypto strategies across fixed chronological split points: 60/40, 70/30, and 80/20. It reports split date ranges, out-of-sample CAGR, Sharpe, max drawdown, Calmar, trade count, and the matching buy-and-hold out-of-sample benchmark metrics for the same symbol and split. A strategy can beat buy-and-hold for a split even when its own CAGR is negative if buy-and-hold was worse, so the benchmark fields and gap columns are included for interpretation. The BTC/ETH/cash rotation is not folded into this per-symbol robustness report because it needs a separate portfolio benchmark. This is research-only and does not add strategies, tune parameters, call Alpaca, create orders, enable shorting, enable margin, or approve execution.

Output:

```text
data/crypto_robustness_report.csv
```

Crypto period diagnostics mode reads saved crypto robustness, lab result, and lab trade CSVs to explain weak out-of-sample split periods for the current BTC and ETH focus candidates. It writes labels such as `benchmark_also_weak`, `cash_drag`, `whipsaw_sensitive`, and `profitable_but_weakening`. It is saved-data-only research reporting and does not refresh data, call Alpaca, create orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Output:

```text
data/crypto_period_diagnostics.csv
```

Crypto signal preview mode uses current yfinance-compatible daily data for the current best split-sensitive crypto research candidates: `BTC/USD` with `crypto_buy_above_200_with_vol_gate`, and `ETH/USD` with `crypto_buy_above_200_exit_below_200`. `LTC/USD` is included as research-only and remains flat when there is no selected candidate; if a saved decision report marks it `not_useful` or otherwise unsupported, the preview wording reflects that status instead of asking for research that already exists. It writes whether each candidate would prefer `long` or `flat` today, including SMA200 and volatility-gate diagnostics where applicable. It does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Output:

```text
data/crypto_signal_preview.csv
```

Crypto monitor display mode reads saved crypto CSVs only, starting with `data/crypto_signal_preview.csv`, and prints a terminal summary of current desired positions, signal reasons, saved decision status, saved robustness status, and saved period diagnostics. It does not refresh market data, call yfinance, call Alpaca, read positions, write files, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Command:

```text
python bot.py --show-crypto-monitor
```

Crypto research state report mode reads saved crypto CSVs only and writes one concise checkpoint across `BTC/USD`, `ETH/USD`, and `LTC/USD`. It combines universe status, saved decision status, saved signal preview, selected-candidate robustness and cost-stress status, separately labelled all-strategy robustness and cost-stress statuses, and period diagnostics. It is a checkpoint report only and does not refresh market data, call yfinance, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, add symbols, add strategies, or approve execution.

Command:

```text
python bot.py --crypto-research-state-report
```

Output:

```text
data/crypto_research_state_report.csv
```

Promoted strategy preview mode reads `data/strategy_promotion_report.csv`, previews current desired states for supported `preview_candidate` strategies, and writes `data/promoted_strategy_preview.csv`. It includes SPY regime, 50/200 SMA, 200-day threshold, 252-day high, and volume diagnostics where available. The `sma_50_200_trend` preview uses 50-day SMA versus 200-day SMA, while `buy_above_200_exit_below_200` uses close versus 200-day SMA. It does not call Alpaca, read paper positions, write to SQLite `trade_log`, send Discord alerts, or approve execution.

Output:

```text
data/promoted_strategy_preview.csv
```

Promoted action preview mode reads `data/promoted_strategy_preview.csv` and compares desired positions with current Alpaca paper positions when read-only access is available. By default, dry-run mode does not read paper positions. To explicitly read paper positions for preview context without changing `dry_run`, use `python bot.py --preview-promoted-actions --use-paper-positions-readonly`. It never submits orders, cancels orders, writes `trade_log`, sends Discord alerts, or approves execution.

Output:

```text
data/promoted_strategy_action_preview.csv
```

Trend stress test mode focuses on slow SMA trend pairs and checks whether results survive higher trading costs:

- `40 / 160`
- `50 / 200`
- `60 / 200`
- `100 / 200`

It tests slippage at `0`, `5`, `10`, `25`, and `50` basis points using the shared research-only cost model. The optional ETF universe helps inspect broad index, sector, bond, and commodity ETFs separately from individual stocks.

Outputs:

```text
data/trend_stress_test_results.csv
data/trend_stress_test_portfolio.csv
```

Slow SMA preview mode shows the current long-only crossover signal for each ticker plus trend diagnostics. `HOLD` means there was no new crossover today; it can still be a bullish trend if the short SMA is already above the long SMA. `desired_position` is informational only and is not connected to order execution.

It does not submit Alpaca orders, does not send Discord alerts, and does not write to the live SQLite trade log.

Outputs:

```text
data/slow_sma_signal_preview.csv
```

Slow SMA action preview mode compares `desired_position` with current Alpaca paper positions, when paper credentials are available. This uses target-position alignment: the preview shows what would be needed to align the account with the strategy's current desired state, not just what a new crossover signal would do.

It is still preview-only. It does not submit orders, cancel orders, send Discord alerts, or write to the live SQLite trade log.

Outputs:

```text
data/slow_sma_action_preview.csv
```

Slow SMA paper execution is a separate explicit command. It requires `--confirm-slow-sma-paper`, requires Alpaca paper mode, refuses `allow_shorting: true`, checks assets and open orders before submitting, and logs every submitted or skipped target-position action to SQLite.

It submits market DAY paper orders only. It is not connected to normal `python bot.py` behaviour.

Normal `python bot.py` still uses the original bot behaviour. Other research strategies should stay in backtest or preview mode until results are reviewed.

The initial V2 strategy lab skeleton exists in `trading_bot/strategies/base.py` and `trading_bot/strategies/registry.py`. The registry contains metadata for the existing research strategies. The research-only 52-week high breakout candidate is wired into `--compare-strategies` only. Monthly ETF rotation and adaptive risk-on/off momentum each have explicit research-only backtest commands. Crypto currently exists as research-only preview and strategy-lab scaffolding and is not connected to execution.

## How Trading Rules Work

The bot checks whether each ticker is currently flat, long, or short.

When `allow_shorting` is `false`:

- `BUY` opens a long position only if flat.
- `SELL` closes a long position only if already long.
- The bot never opens short positions.
- The bot never adds to an existing long position.

When `allow_shorting` is `true`:

- `BUY` opens a long position if flat.
- `BUY` closes an existing short position.
- `SELL` closes an existing long position.
- `SELL` opens a short position if flat.
- The bot never adds to an existing long or short position.

In dry-run mode, position state is simulated from the bot's own SQLite trade history. In Alpaca paper mode, position state comes from Alpaca.

Before submitting a paper order, the bot checks for existing open Alpaca orders for that ticker. Existing open orders block duplicate submissions.

## Check Logs and Trade History

Text logs:

```powershell
Get-Content logs\bot.log -Tail 50
```

SQLite trade history:

```powershell
python -c "import sqlite3; db=sqlite3.connect('data/trades.db'); [print(row) for row in db.execute(\"SELECT created_at,ticker,signal,action,order_status,error FROM trade_log ORDER BY id DESC LIMIT 20\")]"
```

You can also inspect `data/trades.db` with a SQLite browser tool.

Backtest CSVs:

```powershell
Get-Content data\backtest_results.csv
Get-Content data\strategy_comparison_results.csv
```

## Run Repeatedly With Windows Task Scheduler

Version 1 runs once and exits. To run it repeatedly:

1. Open **Task Scheduler**.
2. Choose **Create Basic Task**.
3. Pick a schedule, for example once per weekday after market close.
4. Choose **Start a program**.
5. Program/script:

```text
C:\Users\lewis\OneDrive\Documents\Paper Trading Bot\.venv\Scripts\python.exe
```

6. Add arguments:

```text
bot.py
```

7. Start in:

```text
C:\Users\lewis\OneDrive\Documents\Paper Trading Bot
```

Run the task manually once to confirm logs appear in `logs/bot.log`.

## Troubleshooting

Config file not found:

- Copy `config.example.json` to `config.json`.
- Run PowerShell from the project folder.

Alpaca key error:

- Keep `dry_run: true` until your paper API keys are ready.
- Use paper keys, not live keys.
- Keep `alpaca.paper: true`.

No market data:

- Check the ticker spelling.
- Use U.S. stock and ETF symbols only.
- Try a longer `history_period`, such as `1y`.

Not enough price history:

- Increase `history_period`.
- Use a smaller `long_window`.

Discord alert failed:

- Check that the webhook URL is correct.
- Make sure the Discord channel still exists.

Backtest output is empty:

- Confirm yfinance can download daily data locally.
- Try a longer `backtest.history_period`, such as `10y`.
- Remember that backtest mode needs enough rows for 200-day SMA and volatility windows.

## Useful References

- [yfinance download documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)
- [Alpaca Python SDK trading docs](https://alpaca.markets/sdks/python/trading.html)
- [Discord webhook docs](https://docs.discord.com/developers/resources/webhook)
