# V2 Refactor Inventory

This inventory captures the current V2 refactor state before moving any more production code.

## Safety Boundary

- This document does not change trading, strategy, execution, or command-routing behaviour.
- Live trading must never be added.
- `config.json` must remain private and must not be committed.
- `--paper-order-test` and `--execute-slow-sma-paper` must not be run during refactor verification unless explicitly requested.
- Alpaca order submission, manual paper-order smoke testing, and slow SMA paper execution are high-risk areas and should not move until additional verification exists.

## Modules Already Extracted

- `trading_bot/config.py` - config loading, config validation, defaults, environment variable fallback.
- `trading_bot/database.py` - SQLite database setup, migrations, and `trade_log` inserts.
- `trading_bot/discord_alerts.py` - Discord webhook alert helper and webhook redaction.
- `trading_bot/market_data.py` - yfinance cache setup and market-data download/column extraction helpers.
- `trading_bot/strategies/base.py` - initial strategy-lab base types for future research strategies; not wired into runtime commands.
- `trading_bot/strategies/registry.py` - initial strategy-lab registry; not wired into runtime commands.
- `trading_bot/strategies/breakout.py` - pure research-only 52-week high breakout helpers; wired into `--compare-strategies` only.
- `trading_bot/strategies/rotation.py` - pure research-only monthly ETF momentum rotation helpers; not wired into runtime commands.
- `trading_bot/strategies/adaptive.py` - pure research-only adaptive risk-on/off momentum helpers; wired into `--adaptive-momentum-backtest` only.
- `trading_bot/strategies/sma.py` - pure SMA constants, indicators, crossover signals, slow-SMA preview diagnostics, and strategy-comparison signal helpers.
- `trading_bot/research/backtesting.py` - research result rows, metrics, CSV writers, equity-curve writers, and ranked summaries.
- `trading_bot/research/costs.py` - research-only cost model helpers used by current research/backtest modes.
- `trading_bot/research/plotting.py` - saved strategy equity-curve CSV reading and matplotlib chart generation for `--plot-strategy-results`.
- `trading_bot/research/promoted_actions.py` - read-only promoted desired-position versus paper-position action preview for `--preview-promoted-actions`.
- `trading_bot/research/promoted_consensus.py` - research-only ticker-level consensus report for `--promoted-consensus-preview`.
- `trading_bot/research/promoted_decision.py` - research-only ticker-level decision policy report for `--promoted-decision-preview`.
- `trading_bot/research/promoted_preview.py` - preview-only promoted strategy signal rows for `--preview-promoted-strategies`.
- `trading_bot/research/promoted_risk.py` - research-only risk inspection for promoted desired positions in `--promoted-risk-preview`.
- `trading_bot/research/promotion.py` - conservative strategy promotion checklist for `--strategy-promotion-report`.
- `trading_bot/research/reporting.py` - research CSV aggregation and ranking for `--research-report`.
- `trading_bot/research/walk_forward.py` - research CSV period comparison for `--walk-forward-report`.
- `trading_bot/positions.py` - `Position`, signed quantity interpretation, dry-run position reconstruction, and read-only Alpaca position parsing.
- `trading_bot/alpaca_client.py` - read-only Alpaca helper functions for open orders, asset validation, order-status normalization, and status refresh.
- `trading_bot/execution.py` - trade-decision/action-translation helper `decide_trade` and `TradeDecision`.
- `trading_bot/logging_setup.py` - console and configured file logging setup.
- `trading_bot/output.py` - CLI table formatting helpers for slow SMA signal preview, action preview, and paper execution summaries.

## What Still Remains In `bot.py`

### Low Risk

- Small utility functions such as manual quantity parsing and decimal-to-float conversion.

### Medium Risk

- Command-line argument parsing and command routing.
- Normal one-shot bot orchestration.
- Backtest and research command orchestration.
- Slow SMA signal preview orchestration.
- Slow SMA action preview orchestration.
- Open-order blocking flow around trade processing, because it sits close to execution safety even though the lookup helper is already extracted.

### High Risk

- Alpaca order submission helper.
- Manual paper-order smoke test.
- Slow SMA paper execution.
- Normal paper-trading ticker processing around order submission and SQLite logging.
- Any logic that mutates positions, writes submitted/skipped order decisions, or sends trade alerts.

## Research Cost Model Status

- `trading_bot/research/costs.py` provides shared research-only cost helpers.
- `--trend-stress-test` uses `CostModel` for its existing slippage scenarios.
- `--sma-sensitivity` uses `CostModel` for its configured default slippage assumption.
- `--compare-strategies` uses `CostModel` for its configured default slippage assumption.
- `--backtest` uses `CostModel` for its configured default slippage assumption.
- `--etf-rotation-backtest` uses `CostModel` for its configured default slippage assumption.
- `--adaptive-momentum-backtest` uses `CostModel` for its configured default slippage assumption.
- All current research/backtest modes now use the shared research-only cost model.
- The cost model is not connected to Alpaca paper execution or order submission.

## Research Report Status

- `--research-report` reads existing research CSV outputs and writes `data/research_report.csv`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, or write to SQLite.
- Rankings are research-only and do not imply future profits.
- The report keeps all-row ranks for auditability, then adds a decision-view rank that prefers full-period portfolio-level rows and warns that in-sample single-ticker rows can be misleading.
- It also classifies benchmark rows separately from active strategy candidates and adds active-only rankings plus relative-to-benchmark fields.
- It includes report-only diagnostic columns for return gaps, drawdown reduction, turnover, and rule-based underperformance reasons.

## Walk-Forward Report Status

- `--walk-forward-report` reads existing research CSV outputs and writes `data/walk_forward_report.csv`.
- It pairs matching `in_sample` and `out_of_sample` rows by source file, strategy name, and ticker/portfolio.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, or modify existing research CSV outputs.
- Its headline summary focuses on portfolio-level benchmark and active rows; single-ticker winners are listed separately as diagnostics.
- ETF rotation results now include `full_period`, `in_sample`, and `out_of_sample` portfolio rows using a simple chronological 70% / 30% split.
- Adaptive momentum results now include `full_period`, `in_sample`, and `out_of_sample` portfolio rows using the same simple chronological 70% / 30% reporting split.
- Robustness labels are research-only and do not imply future profits.

## Strategy Promotion Report Status

- `--strategy-promotion-report` reads `data/research_report.csv` and `data/walk_forward_report.csv`.
- It writes `data/strategy_promotion_report.csv`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, or modify existing research CSV outputs.
- `preview_candidate` means future preview-mode research only. It is not approval for Alpaca paper execution.
- Any execution path still requires preview mode, risk checks, and explicit confirmation.

## Defensive Strategy Report Status

- `--defensive-strategy-report` reads `data/research_report.csv` and `data/walk_forward_report.csv`.
- It writes `data/defensive_strategy_report.csv`.
- It scores portfolio-level active strategies for defensive usefulness, not benchmark replacement.
- It rewards lower drawdown, strong out-of-sample Sharpe/Calmar, and robust or improved walk-forward labels.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, or approve execution.

## Defensive Candidate Comparison Status

- `--defensive-candidate-comparison` reads saved walk-forward, defensive, optional promotion, and vol-managed ETF reports.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic remains in `trading_bot/research/defensive_comparison.py`.
- It writes `data/defensive_candidate_comparison.csv`.
- It compares `monthly_etf_momentum_rotation`, `volatility_managed_dual_momentum_etf`, and `adaptive_risk_on_off_momentum` as defensive portfolio candidates using out-of-sample metrics, fixed-split consistency, drawdown, trade count, turnover burden, and complexity.
- It separates raw metric rank from policy rank so a split-sensitive strategy can lead raw metrics without becoming the preferred defensive candidate.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, tune strategies, or approve execution.

## ETF Defensive Drawdown Comparison Status

- `--etf-defensive-drawdown-comparison` reads saved ETF rotation and vol-managed ETF equity curves plus fixed-split robustness reports.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/etf_defensive_drawdowns.py`.
- It writes `data/etf_defensive_drawdown_comparison.csv`.
- It compares full-period and `split_80_20` out-of-sample drawdown periods for `monthly_etf_momentum_rotation` and `volatility_managed_dual_momentum_etf`.
- It includes fixed-split Calmar context so lower drawdown can be interpreted alongside CAGR, Sharpe, and Calmar tradeoffs.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, tune strategies, or approve execution.

## ETF Defensive Charting Status

- `--plot-etf-defensive-comparison` reads saved ETF rotation and vol-managed ETF equity curves only.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the charting logic lives in `trading_bot/research/etf_defensive_charts.py`.
- It writes `data/charts/etf_defensive_equity_comparison.png` and `data/charts/etf_defensive_drawdown_comparison.png`.
- It creates saved PNG diagnostics only and does not open a GUI.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, tune strategies, or approve execution.

## Defensive Research Refresh Status

- `--refresh-defensive-research` refreshes the current defensive saved-report/dashboard chain in a safe order.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the refresh logic lives in `trading_bot/research/defensive_refresh.py`.
- It writes `data/defensive_research_refresh_summary.csv`.
- It runs saved-data-safe steps for ETF rotation robustness, defensive candidate comparison, ETF defensive drawdown comparison, and ETF defensive charting.
- It treats `data/vol_managed_etf_robustness_report.csv` as a saved prerequisite instead of rerunning the market-data-backed vol-managed robustness command.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, tune strategies, or approve execution.

## Drawdown Period Report Status

- `--drawdown-period-report` reads saved equity-curve CSV files only.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic remains in `trading_bot/research/drawdown_periods.py`.
- It writes `data/drawdown_period_report.csv`.
- It identifies major drawdown periods for the main benchmark and active portfolio research candidates.
- It compares active drawdowns with benchmark drawdowns over overlapping dates where available.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not rerun backtests, download market data, call Alpaca, send Discord alerts, write to SQLite, tune strategies, or approve execution.

## Short-Selling Readiness Report Status

- `--short-selling-readiness-report` performs a static/local readiness audit only.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/short_selling_readiness.py`.
- It writes `data/short_selling_readiness_report.csv`.
- It checks shorting defaults, paper-only safety boundaries, slow SMA long-only refusal, promoted/crypto non-execution state, and absence of short execution commands.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not enable shorting, add short strategies, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Deployment Readiness Report Status

- `--deployment-readiness-report` performs a local readiness audit for possible future VPS/server use.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/deployment_readiness.py`.
- It writes `data/deployment_readiness_report.csv`.
- It checks local Python/package readiness, required files, Git ignore/safety status, paper-only/dry-run/shorting defaults, gated execution commands, safe scheduling candidates, must-not-schedule commands, and handoff docs.
- It reports whether `config.json` exists locally but does not read or print its contents.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not deploy, add loop mode, create Windows Task Scheduler tasks, call Alpaca, refresh market data, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Portfolio Risk Policy Report Status

- `--portfolio-risk-policy-report` performs a saved-data/static-context portfolio risk policy audit only.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/portfolio_risk_policy.py`.
- It writes `data/portfolio_risk_policy_report.csv`.
- It documents conservative report-only policies for paper-only mode, dry-run default, shorting disabled, proposed max open positions, desired notional review, duplicate ticker exposure, strategy disagreement, execution approval status, future kill switch work, and future daily summary work.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not enforce risk checks, change order sizing, call Alpaca, read positions/account equity, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Portfolio Risk Policy Display Status

- `--show-portfolio-risk-policy` reads `data/portfolio_risk_policy_report.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the display logic lives in `trading_bot/research/portfolio_risk_policy.py`.
- It displays counts by `risk_policy_status` and `risk_level`, blocked-for-review rows, future-work rows, compact policy rows, and execution-approved status.
- It does not rerun the policy report, refresh market data, call Alpaca, read positions, enforce risk checks, create/submit/cancel orders, write files, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Paper Kill-Switch Readiness Report Status

- `--paper-kill-switch-readiness-report` performs a reporting-only readiness audit for future paper kill-switch design.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/paper_kill_switch.py`.
- It writes `data/paper_kill_switch_readiness_report.csv`.
- It audits paper-only/dry-run/shorting boundaries, high-risk command gating, saved promoted decision state, saved portfolio risk policy state, scheduling boundaries, and future tests/design work needed before any kill-switch enforcement.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not add a config setting, enforce a kill switch, change order paths, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Execution Eligibility Report Status

- `--execution-eligibility-report` combines saved promoted decision, portfolio risk policy, paper kill-switch readiness, and deployment readiness reports into a final non-executable eligibility view.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/execution_eligibility.py`.
- It writes `data/execution_eligibility_report.csv`.
- It answers whether anything is execution-approved, what blocks execution discussion, which saved reports are missing, and what future work remains before any paper execution workflow can be considered.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not refresh previews, enforce risk policy, implement a kill switch, create order instructions, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Short Hedge Backtest Status

- `--short-hedge-backtest` runs a synthetic SPY-only short hedge backtest for research.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the backtest logic lives in `trading_bot/research/short_hedge.py`.
- It writes `data/short_hedge_backtest_results.csv`, `data/short_hedge_backtest_trades.csv`, and `data/short_hedge_equity_curve.csv`.
- It enters a research short when SPY closes below its 200-day SMA and returns flat when SPY closes at or above its 200-day SMA.
- It includes `full_period`, `in_sample`, and `out_of_sample` result rows.
- Result rows include `research_status`, `research_conclusion`, and `required_next_step`; weak negative CAGR/Sharpe/Calmar results are labelled `not_useful` rather than preview candidates.
- Borrow fees and real short constraints are explicitly marked `not_modelled_initial_research`.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not enable `allow_shorting`, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, touch crypto shorting, or approve execution.

## Short Strategy Lab Status

- `--short-strategy-lab` runs one controlled multi-ticker ETF short-selling research hypothesis.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the lab logic lives in `trading_bot/research/short_strategy_lab.py`.
- It writes `data/short_strategy_lab_results.csv`, `data/short_strategy_lab_trades.csv`, `data/short_strategy_lab_equity_curve.csv`, and `data/short_strategy_iteration_log.csv`.
- The fixed strategy is `research_weak_etf_short_momentum`.
- It uses the liquid ETF universe `SPY`, `QQQ`, `IWM`, `DIA`, `XLF`, `XLK`, `XLY`, `XLE`, `XLI`, and `XLU`.
- It only opens synthetic shorts when SPY is below its 200-day SMA, then shorts the weakest two eligible ETFs by 126-day return if they are below their own 200-day SMA.
- It rebalances monthly, remains short/cash only, avoids pyramiding, and caps synthetic gross short exposure at 1x.
- It uses fixed parameters only and does not run a parameter search.
- Borrow fees use the simplified placeholder `borrow_fee_bps_annual=300` with status `fixed_placeholder_300_bps_annual_initial_research`.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not enable `allow_shorting`, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, add crypto shorting, or approve execution.

## Crypto Research Preview Status

- `--crypto-research-preview` writes `data/crypto_research_preview.csv`.
- It starts the crypto phase as a static research scaffold for `BTC/USD`, `ETH/USD`, and `LTC/USD`.
- It marks execution, shorting, margin, and execution approval disabled.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It does not download market data, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Crypto Strategy Lab Status

- `--crypto-strategy-lab` writes `data/crypto_strategy_lab_results.csv`, `data/crypto_strategy_lab_trades.csv`, and `data/crypto_strategy_iteration_log.csv`.
- It uses yfinance-compatible daily symbols `BTC-USD`, `ETH-USD`, and `LTC-USD` for research data.
- It tests `crypto_buy_and_hold_baseline`, `crypto_sma_50_200_trend`, `crypto_buy_above_200_exit_below_200`, and one controlled iteration: `crypto_buy_above_200_with_vol_gate`.
- The volatility-gate iteration uses fixed parameters only: 20-day realised volatility, trailing 252-day median volatility, and a 1.5x gate for new entries.
- It also writes a separate portfolio-style BTC/ETH/cash rotation test, `crypto_monthly_btc_eth_momentum_rotation`, to `data/crypto_rotation_results.csv` and `data/crypto_rotation_trades.csv`.
- The rotation uses fixed monthly rebalance, 126-day momentum ranking, and a 200-day SMA absolute trend filter.
- The rotation is not folded into the per-symbol crypto report/decision flow until a clean portfolio benchmark comparison exists.
- It includes `full_period`, `in_sample`, and `out_of_sample` period rows.
- It applies fixed research-only cost assumptions: `crypto_taker_fee_bps=10`, `crypto_spread_bps=5`, and `crypto_slippage_bps=10`.
- It records the fixed parameter set and hypothesis in an iteration log to avoid tuning after seeing results.
- It does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Strategy Report Status

- `--crypto-strategy-report` reads `data/crypto_strategy_lab_results.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/crypto_report.py`.
- It writes `data/crypto_strategy_report.csv`.
- It ranks crypto strategies by symbol and period and compares each row with the matching `crypto_buy_and_hold_baseline`.
- It is saved-data-only research reporting and does not call yfinance, Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Strategy Decision Report Status

- `--crypto-strategy-decision-report` reads `data/crypto_strategy_lab_results.csv` and `data/crypto_strategy_report.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/crypto_decision.py`.
- It writes `data/crypto_strategy_decision_report.csv`.
- It creates symbol-level research statuses using out-of-sample Calmar, Sharpe, CAGR gap, drawdown reduction, and whether the strategy beats buy-and-hold.
- Every row is marked `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It is saved-data-only research reporting and does not call yfinance, Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Cost Stress Report Status

- `--crypto-cost-stress-report` reruns the existing crypto strategy lab across fixed one-way cost assumptions: `zero_cost` 0 bps, `default_cost` 25 bps, `high_cost` 50 bps, and `extreme_cost` 100 bps.
- It writes `data/crypto_cost_stress_report.csv`.
- It uses the existing crypto strategies only and does not add a new strategy or optimise parameters.
- It compares each strategy against its own default-cost result and marks every row `research_only=True`, `preview_only=True`, and `execution_approved=False`.
- It is research-only and does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Robustness Report Status

- `--crypto-robustness-report` reruns the existing per-symbol crypto strategies across fixed chronological splits: 60/40, 70/30, and 80/20.
- It writes `data/crypto_robustness_report.csv`.
- It reports split date ranges, out-of-sample CAGR, Sharpe, max drawdown, Calmar, trade count, matching buy-and-hold benchmark metrics, benchmark gaps, and drawdown reduction for each symbol, strategy, and split.
- The BTC/ETH/cash rotation is kept out of this per-symbol report until a clean portfolio benchmark comparison exists.
- It is research-only and does not add strategies, tune parameters, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Period Diagnostics Status

- `--crypto-period-diagnostics` reads saved `crypto_robustness_report.csv`, `crypto_strategy_lab_results.csv`, and `crypto_strategy_lab_trades.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/crypto_period_diagnostics.py`.
- It writes `data/crypto_period_diagnostics.csv`.
- It focuses on the current BTC and ETH crypto research candidates and labels weak out-of-sample split periods, including `benchmark_also_weak`, `cash_drag`, `whipsaw_sensitive`, and `profitable_but_weakening`.
- It is saved-data-only research reporting and does not refresh market data, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Signal Preview Status

- `--preview-crypto-signals` uses yfinance-compatible daily data to preview the current split-sensitive crypto research candidates.
- It writes `data/crypto_signal_preview.csv`.
- BTC uses `crypto_buy_above_200_with_vol_gate`; ETH uses `crypto_buy_above_200_exit_below_200`.
- LTC is included as research-only with `no_decision_candidate_yet` until lab/report/decision research identifies a candidate.
- It is preview-only research reporting and does not call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Monitor Display Status

- `--show-crypto-monitor` reads saved crypto CSVs only, starting with `data/crypto_signal_preview.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the display logic lives in `trading_bot/research/crypto_monitor.py`.
- It prints a terminal summary of current desired positions, signal reasons, saved decision status, saved robustness status, and saved period diagnostics.
- It does not refresh market data, call yfinance, call Alpaca, read positions, create/submit/cancel orders, write files, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, enable leverage, or approve execution.

## Crypto Research State Report Status

- `--crypto-research-state-report` reads saved crypto CSVs only and writes `data/crypto_research_state_report.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the report logic lives in `trading_bot/research/crypto_state.py`.
- It summarizes universe status, saved decision status, saved current signal, selected-candidate robustness and cost stress, separately labelled all-strategy robustness and cost stress, and period diagnostics across `BTC/USD`, `ETH/USD`, and `LTC/USD`.
- It is a checkpoint report only and does not refresh market data, call yfinance, call Alpaca, read positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, add symbols, add strategies, enable shorting, enable margin, enable leverage, or approve execution.

## Promoted Strategy Preview Status

- `--preview-promoted-strategies` reads `data/strategy_promotion_report.csv`.
- It previews only `preview_candidate` portfolio rows for supported strategies.
- It writes `data/promoted_strategy_preview.csv`.
- It includes regime, 50/200 SMA, 200-day threshold, 252-day high distance, and volume diagnostics where available.
- `sma_50_200_trend` preview uses 50-day SMA versus 200-day SMA; `buy_above_200_exit_below_200` preview uses close versus 200-day SMA.
- It does not call Alpaca, submit orders, read paper positions, write to SQLite `trade_log`, send Discord alerts, or approve execution.
- `buy_above_200_exit_below_200` is classified as a trend/absolute-momentum style strategy, not `unknown`.

## Promoted Action Preview Status

- `--preview-promoted-actions` reads `data/promoted_strategy_preview.csv`.
- It writes `data/promoted_strategy_action_preview.csv`.
- By default, dry-run mode does not read paper positions.
- `--preview-promoted-actions --use-paper-positions-readonly` explicitly reads Alpaca paper positions for preview context only while leaving `dry_run` and `config.json` unchanged.
- The read-only flag is different from setting `dry_run=false`.
- It may read current Alpaca paper positions through read-only helpers when explicitly requested and credentials are available, but it does not submit orders, cancel orders, mutate positions, write SQLite `trade_log`, send Discord alerts, or approve execution.
- If positions are unavailable, it marks rows as `position_unavailable` rather than assuming flat.

## Promoted Action Display Status

- `--show-promoted-actions` reads `data/promoted_strategy_action_preview.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the display logic lives in `trading_bot/research/promoted_actions.py`.
- It is only a terminal display helper for the CSV produced by `python bot.py --preview-promoted-actions`.
- It does not refresh market data, call Alpaca, read positions, submit or cancel orders, write SQLite rows, send Discord alerts, or approve execution.

## Promoted Risk Preview Status

- `--promoted-risk-preview` reads `data/promoted_strategy_preview.csv`.
- It optionally reads `data/promoted_strategy_action_preview.csv` for saved current-position context.
- It writes `data/promoted_risk_preview.csv`.
- It reads saved CSV files only and marks every output row `research_only=True` and `preview_only=True`.
- It includes saved-data-only notional estimate fields: `latest_close`, `assumed_quantity`, and `estimated_desired_notional`.
- It uses saved `latest_close` values from `data/promoted_strategy_preview.csv` and `assumed_quantity=1`; these estimates are not order instructions and do not refresh prices or positions.
- It flags simple deterministic risks:
    - desired long count versus a conservative `max_open_positions`
    - duplicate ticker exposure across promoted strategy rows
    - concentration risk where multiple promoted strategies want the same ticker long
    - unavailable current position data from the action preview
    - notional data quality for saved `latest_close` values
- It is research-only and preview-only. It does not refresh market data, call yfinance, call Alpaca, read live/current positions directly, submit/cancel/create orders, write SQLite `trade_log` rows, send Discord alerts, or approve execution.

## Promoted Risk Display Status

- `--show-promoted-risk` reads `data/promoted_risk_preview.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the display logic lives in `trading_bot/research/promoted_risk.py`.
- It is only a terminal display helper for the CSV produced by `python bot.py --promoted-risk-preview`.
- It does not refresh market data, call yfinance, call Alpaca, read live/current positions, submit/cancel/create orders, write files, write SQLite `trade_log` rows, send Discord alerts, or approve execution.
- It displays count by `risk_status`, count by `risk_check`, count by `desired_position`, estimated desired notional by strategy, duplicated desired notional by ticker, unique desired notional by ticker, unique account-style desired notional total, blocked-for-review rows, warning rows, and a compact table of risk rows.
- The duplicated ticker summary intentionally counts overlapping promoted strategy rows, while the unique summary counts each desired-long ticker once for a more account-style exposure view.

## Promoted Consensus Preview Status

- `--promoted-consensus-preview` reads `data/promoted_strategy_preview.csv`.
- It writes `data/promoted_consensus_preview.csv`.
- It groups promoted strategy rows by ticker and counts desired long, flat, and other votes.
- It labels ticker-level agreement as `unanimous_long`, `unanimous_flat`, `mixed_long_flat`, `no_supported_votes`, or `unknown`.
- It marks every row `execution_eligible=False`, `research_only=True`, and `preview_only=True`.
- It is research-only and preview-only. It does not refresh market data, call yfinance, call Alpaca, read live/current positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Promoted Decision Preview Status

- `--promoted-decision-preview` reads `data/promoted_consensus_preview.csv`, `data/promoted_strategy_action_preview.csv`, and `data/promoted_risk_preview.csv`.
- It writes `data/promoted_decision_preview.csv`.
- It combines consensus, action, and risk context into ticker-level policy judgement rows.
- It marks every row `execution_approved=False`, `research_only=True`, and `preview_only=True`.
- It is a policy preview only. It does not refresh market data, call yfinance, call Alpaca, read live/current positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

## Promoted Decision Display Status

- `--show-promoted-decision` reads `data/promoted_decision_preview.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the display logic lives in `trading_bot/research/promoted_decision.py`.
- It is only a terminal display helper for the CSV produced by `python bot.py --promoted-decision-preview`.
- It displays row count, counts by `decision_state`, counts by `execution_approved`, compact ticker-level decision rows, and a final execution-approved warning or all-false confirmation.
- It does not refresh market data, call yfinance, call Alpaca, read live/current positions, submit/cancel/create orders, write SQLite `trade_log` rows, send Discord alerts, or approve execution.

## Promoted Review Refresh Status

- `--refresh-promoted-review` runs the promoted review chain in order and writes `data/promoted_review_refresh_summary.csv`.
- Its command orchestration lives in `trading_bot/runners/research_reports.py`; the refresh logic lives in `trading_bot/research/promoted_review_refresh.py`.
- It runs `--preview-promoted-strategies`, `--preview-promoted-actions --use-paper-positions-readonly`, `--promoted-risk-preview`, `--promoted-consensus-preview`, `--promoted-decision-preview`, and `--show-promoted-decision`.
- It uses the existing read-only paper-position action preview path and does not change `dry_run`.
- It does not create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, connect promoted candidates to execution, or approve execution.

## Strategy Lab Status

- `trading_bot/strategies/base.py` and `trading_bot/strategies/registry.py` provide the initial strategy-lab skeleton.
- The skeleton supports future research strategy metadata and in-memory registration.
- The registry contains metadata-only entries for the existing research strategies.
- `trading_bot/strategies/breakout.py` contains pure helper functions for a research-only 52-week high breakout candidate.
- The breakout candidate is wired into `--compare-strategies` only.
- `trading_bot/strategies/rotation.py` contains pure helper functions for a research-only monthly ETF momentum rotation candidate.
- The rotation candidate is wired into `--etf-rotation-backtest` only.
- ETF rotation results include SPY, QQQ, and equal-weight buy-and-hold benchmark comparisons.
- ETF rotation result summaries include `full_period`, `in_sample`, and `out_of_sample` period labels for walk-forward reporting.
- `--vol-managed-etf-backtest` is the first advanced long-only ETF research lab from the deep research shortlist.
- It writes `data/vol_managed_etf_results.csv`, `data/vol_managed_etf_trades.csv`, `data/vol_managed_etf_equity_curve.csv`, and `data/vol_managed_etf_iteration_log.csv`.
- It uses fixed monthly rebalance, top 3 dual-momentum selection, 200-day SMA filters, 63-day realised volatility, inverse-volatility sizing, and a 10% annual volatility target with gross exposure capped at 100%.
- It remains research-only and does not use leverage, margin, shorting, Alpaca, SQLite `trade_log`, Discord alerts, or execution approval.
- `--etf-rotation-robustness` writes `data/etf_rotation_robustness_report.csv`.
- It reads saved ETF rotation equity/trade CSVs and creates matching `split_60_40`, `split_70_30`, and `split_80_20` rows for comparison.
- It does not rerun or change ETF rotation strategy rules.
- `--vol-managed-etf-robustness` writes `data/vol_managed_etf_robustness_report.csv`.
- It checks the same fixed strategy across `split_60_40`, `split_70_30`, and `split_80_20` without tuning parameters.
- It compares against matching monthly ETF rotation robustness rows when available, falling back to the original 70/30 ETF rotation result only when the fixed-split report is missing.
- It is research/reporting only and does not change strategy rules or execution behavior.
- Adaptive momentum result summaries include `full_period`, `in_sample`, and `out_of_sample` period labels for walk-forward reporting.
- ETF rotation skips partial rebalance trades below `100.0`.
- `trading_bot/strategies/adaptive.py` contains pure helper functions for a research-only adaptive risk-on/off momentum candidate.
- The adaptive candidate is wired into `--adaptive-momentum-backtest` only.
- `trading_bot/research/crypto.py` contains the first crypto research-preview scaffold only.
- `trading_bot/research/crypto_lab.py` contains the first crypto research-only strategy lab.
- `trading_bot/research/crypto_report.py` contains the saved-data-only crypto strategy report.
- `trading_bot/research/crypto_decision.py` contains the saved-data-only crypto strategy decision report.
- `trading_bot/research/crypto_cost_stress.py` contains the research-only crypto cost stress report.
- `trading_bot/research/crypto_robustness.py` contains the research-only crypto fixed-split robustness report.
- `trading_bot/research/crypto_period_diagnostics.py` contains the saved-data-only crypto period diagnostics report.
- `trading_bot/research/crypto_rotation.py` contains the research-only BTC/ETH/cash monthly momentum rotation helper.
- `trading_bot/research/crypto_signal_preview.py` contains the preview-only current crypto signal report.
- `trading_bot/research/crypto_monitor.py` contains the saved-CSV-only crypto monitor terminal display.
- `trading_bot/research/crypto_state.py` contains the saved-CSV-only crypto research state checkpoint report.
- These research candidates are not wired into normal bot runs, previews, Alpaca paper execution, or order tests.

## Recommended Next Extraction Order

### Medium Risk

1. Move research command orchestration after baseline and CSV output checks are strong enough.
2. Move slow SMA signal preview orchestration after preview CSV column checks exist.
3. Move slow SMA action preview orchestration after no-order/no-alert preview tests exist.
4. Move command routing only after each command has a focused smoke test.

### High Risk

1. Move normal paper-trading processing only after trade-log and order-blocking tests exist.
2. Move open-order blocking only after tests verify duplicate-order blocking and close-quantity reservation behaviour.
3. Move shared Alpaca execution helpers only after paper-only safety tests exist.

### Should Not Move Yet

- Alpaca order submission.
- Manual paper-order smoke test.
- Slow SMA paper execution.

These areas should stay in `bot.py` until there is additional no-network test coverage plus a clear paper-only integration checklist. They are the most likely places for accidental order behaviour changes.

## Verification Before Future Refactors

Run the baseline checks before and after each extraction:

```powershell
python -m py_compile bot.py
python scripts\verify_position_rules.py
python scripts\verify_v2_baseline.py --timeout-seconds 180
```

Do not run:

```powershell
python bot.py --paper-order-test ...
python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper
```
