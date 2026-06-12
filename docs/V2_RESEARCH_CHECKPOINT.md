# V2 Research Checkpoint

This checkpoint records the current research interpretation for the V2 paper trading bot. It is documentation only and does not change strategy logic, execution behavior, or saved research CSV outputs.

For the concise current-state handoff summary, see `docs/CURRENT_STATE.md`.

## Current Research Commands

- `python bot.py --backtest`
- `python bot.py --compare-strategies`
- `python bot.py --sma-sensitivity`
- `python bot.py --trend-stress-test`
- `python bot.py --etf-rotation-backtest`
- `python bot.py --adaptive-momentum-backtest`
- `python bot.py --research-report`
- `python bot.py --walk-forward-report`
- `python bot.py --strategy-promotion-report`
- `python bot.py --defensive-strategy-report`
- `python bot.py --crypto-research-preview`
- `python bot.py --crypto-strategy-lab`
- `python bot.py --crypto-strategy-report`
- `python bot.py --crypto-strategy-decision-report`
- `python bot.py --crypto-cost-stress-report`
- `python bot.py --crypto-robustness-report`
- `python bot.py --crypto-period-diagnostics`
- `python bot.py --preview-crypto-signals`
- `python bot.py --show-crypto-monitor`
- `python bot.py --crypto-research-state-report`
- `python bot.py --preview-promoted-strategies`
- `python bot.py --preview-promoted-actions`
- `python bot.py --preview-promoted-actions --use-paper-positions-readonly`
- `python bot.py --show-promoted-actions`
- `python bot.py --promoted-risk-preview`
- `python bot.py --show-promoted-risk`
- `python bot.py --promoted-consensus-preview`
- `python bot.py --promoted-decision-preview`

## Current Best Benchmark

- `buy_and_hold_baseline [portfolio, full_period]`

The current research report ranks buy-and-hold as the strongest decision-view benchmark.

## Current Best Active Strategy

- `sma_50_200_trend [portfolio, full_period]`

This is currently the best active strategy by active combined score, but it does not beat the benchmark on the main decision metrics.

## Best Defensive Active Strategy

- `monthly_etf_momentum_rotation`

ETF rotation is the best defensive active candidate so far. It reduces or reshapes risk, but the current report shows too much return drag versus the benchmark.

## Lowest Drawdown Active Strategy

- `fifty_two_week_high_breakout`

The breakout strategy currently has the lowest active drawdown, but its return gap versus the benchmark is still too large.

## Strategies To Pause

- `adaptive_risk_on_off_momentum`

Keep research-only. Adaptive now has explicit walk-forward split rows and can qualify as a defensive candidate, but it remains secondary to ETF rotation until turnover, cost burden, and defensive portfolio role are reviewed.

- Further random complex strategies

Pause broad experimentation with added complexity because the current report shows complexity has not beaten the benchmark.

## Main Lesson

Current active strategies reduce or reshape risk, but they do not beat benchmark buy-and-hold on the main decision metrics: CAGR, Sharpe, and Calmar.

## Recommended Next Development Options

A. Improve reporting/charting and analyse drawdown periods.

B. Use walk-forward validation reporting to inspect in-sample versus out-of-sample decay.

Current walk-forward interpretation should prioritize portfolio-level rows. Single-ticker out-of-sample winners are useful diagnostics, but they are not portfolio-level strategy approval. ETF rotation and adaptive momentum now write `full_period`, `in_sample`, and `out_of_sample` portfolio rows for walk-forward pairing.

Strategy promotion reporting is a conservative checklist only. A `preview_candidate` status means future preview-mode research, not paper execution approval.

Defensive strategy reporting reads saved `research_report.csv` and `walk_forward_report.csv` outputs and evaluates portfolio-level active strategies for defensive usefulness. It can rank ETF rotation fairly as a defensive candidate when it has lower drawdown and improved out-of-sample Sharpe/Calmar, but it remains research-only and does not approve execution.

Defensive candidate comparison reads saved walk-forward, defensive, and optional promotion reports and writes `data/defensive_candidate_comparison.csv`. It compares ETF rotation directly against adaptive momentum on out-of-sample metrics, drawdown, turnover, and complexity. It is research-only and does not approve execution.

Strategy improvement lab is the next ETF research-only checkpoint for reducing excessive cash drag without approving execution. `python bot.py --strategy-improvement-lab` tests a fixed small set of monthly ETF allocation variants: the monthly ETF rotation reference, balanced dual momentum with defensive sleeve, breadth-aware risk-on rotation, growth-biased rotation with crash gate, cost-aware growth-biased rebalance refinement, partial defensive-sleeve growth-biased refinement, re-entry confirmation, regime recovery, fixed looser/stricter breadth gates, factor/style absolute-gate rotation, sector 52-week-high continuation, and an ambitious fixed multi-sleeve growth allocator. It uses daily yfinance ETF history, fixed 126-day momentum, fixed 200-day trend checks, fixed 52-week-high closeness scoring where relevant, fixed 60/40/30 breadth thresholds, fixed 20/252-day volatility diagnostics, a fixed 5 percentage-point cost-aware rebalance threshold, fixed 75/25 mixed and 50/50 weak partial defensive-sleeve allocations, fixed 50% re-entry breadth confirmation, fixed 63/126-day recovery momentum, fixed 45%/55% breadth gates, SPY and equal-weight benchmarks, and chronological in/out-of-sample reporting. `growth_biased_rotation_breadth_stricter_gate` is now the active research lead after improving CAGR, Sharpe, and Calmar versus the previous `growth_biased_rotation_crash_gate` baseline without worsening max drawdown, cash drag, cost sensitivity, or split sensitivity. It remains research-only, still needs SPY/context review, and does not approve execution. `python bot.py --growth-biased-stricter-validation` is the dedicated saved-output checkpoint for stricter-gate split validation, cost-stress review, drawdown-period review, benchmark comparison, and future preview-candidate discussion readiness. `python bot.py --growth-biased-stricter-promotion-readiness` is the saved-output blocker report that explains what still prevents future preview-candidate discussion, including benchmark, split, cost, drawdown, and saved-output readiness blockers. `python bot.py --growth-biased-stricter-manual-review-pack` is the saved-output manual review pack for structural credibility, regime/context rows, and final preview-discussion status. `python bot.py --growth-biased-stricter-threshold-neighbourhood` is the small fixed 40%/45%/50%/55%/60% breadth-gate robustness check that helps decide whether the stricter-gate result is a credible nearby-threshold cluster or a one-threshold accident. `python bot.py --growth-biased-stricter-cost-turnover-stress` is the saved-output 55% cluster turnover/cost stress check across fixed 0/5/10/25/50/100 bps one-way cost assumptions. `python bot.py --growth-biased-stricter-persistence-filter` tests fixed persistence rules and one Codex-designed `codex_ambitious_concentrated_growth_persistence` candidate to see whether turnover can fall without losing net return/risk. Promising labels, blocker reports, manual review packs, threshold-neighbourhood labels, cost stress labels, and persistence labels are research prompts only; they do not approve buy/sell signals, order instructions, paper execution, preview promotion, scheduling, shorting, leverage, margin, or strategy-to-execution wiring.

Drawdown period reporting reads saved equity curves and writes `data/drawdown_period_report.csv`. It identifies major benchmark and active strategy drawdown periods, compares active drawdowns with overlapping benchmark windows where available, and remains research-only.

Crypto research preview is the first crypto scaffold only. It writes `data/crypto_research_preview.csv` for `BTC/USD`, `ETH/USD`, and `LTC/USD` with execution, shorting, margin, and execution approval disabled. It does not fetch data, call Alpaca, read positions, submit/cancel/create orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Crypto strategy lab is research-only. It uses yfinance-compatible daily data symbols (`BTC-USD`, `ETH-USD`, `LTC-USD`) for a tiny fixed per-symbol strategy set: `crypto_buy_and_hold_baseline`, `crypto_sma_50_200_trend`, `crypto_buy_above_200_exit_below_200`, and one controlled iteration, `crypto_buy_above_200_with_vol_gate`. The volatility gate uses fixed parameters only: 20-day realised volatility, trailing 252-day median volatility, and a 1.5x gate for new entries. The lab also writes a separate portfolio-style BTC/ETH/cash rotation test, `crypto_monthly_btc_eth_momentum_rotation`, using fixed monthly rebalance, 126-day momentum ranking, and a 200-day SMA absolute trend filter. It writes `full_period`, `in_sample`, and `out_of_sample` rows plus an iteration log so failed or weak strategies are recorded instead of silently discarded. Results include simple fixed research cost assumptions: `crypto_taker_fee_bps=10`, `crypto_spread_bps=5`, and `crypto_slippage_bps=10`. It does not connect to Alpaca, read positions, create orders, enable shorting, enable margin, or approve execution. The rotation output is kept separate from the per-symbol crypto report/decision flow until a clean portfolio benchmark comparison exists.

Crypto strategy report reads `data/crypto_strategy_lab_results.csv` and writes `data/crypto_strategy_report.csv`. It compares each strategy against `crypto_buy_and_hold_baseline` for the same symbol and period. It is saved-data-only research reporting and does not approve execution.

Crypto strategy decision report reads saved crypto lab/report CSVs and writes `data/crypto_strategy_decision_report.csv`. It creates symbol-level research statuses such as `strongest_research_candidate`, `research_watchlist`, `inconclusive`, `not_useful`, and `insufficient_data`. It does not refresh data, call Alpaca, create orders, enable shorting, enable margin, or approve execution.

Crypto cost stress report reruns the existing crypto strategy lab across fixed one-way cost assumptions: 0 bps, 25 bps, 50 bps, and 100 bps. It writes `data/crypto_cost_stress_report.csv`, includes buy-and-hold as the benchmark, and compares each strategy against its own default-cost result. It is research-only and does not add strategies, call Alpaca, create orders, enable shorting, enable margin, or approve execution.

Crypto robustness report reruns the existing per-symbol crypto strategies across fixed 60/40, 70/30, and 80/20 chronological split points. It writes `data/crypto_robustness_report.csv` and checks whether out-of-sample results persist across multiple splits rather than relying on one split. Rows include split date ranges and matching buy-and-hold out-of-sample benchmark metrics for the same symbol and split, so negative absolute returns that still beat a worse benchmark can be interpreted clearly. The BTC/ETH/cash rotation is kept out of this per-symbol report until a clean portfolio benchmark comparison exists. It is research-only and does not add strategies, tune parameters, call Alpaca, create orders, enable shorting, enable margin, or approve execution.

Crypto period diagnostics reads saved crypto robustness, lab result, and lab trade CSVs and writes `data/crypto_period_diagnostics.csv`. It focuses on the current BTC and ETH candidates and labels weak out-of-sample split periods as `benchmark_also_weak`, `cash_drag`, `whipsaw_sensitive`, `profitable_but_weakening`, or `insufficient_data`. It is saved-data-only research reporting and does not refresh data, call Alpaca, create orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Crypto signal preview uses current yfinance-compatible daily data to preview the current split-sensitive crypto research candidates: `BTC/USD` with `crypto_buy_above_200_with_vol_gate`, and `ETH/USD` with `crypto_buy_above_200_exit_below_200`. `LTC/USD` is included as research-only and remains flat when there is no selected candidate; if a saved decision report marks it `not_useful` or otherwise unsupported, the preview wording reflects that status. It writes `data/crypto_signal_preview.csv` with desired `long` or `flat` states and diagnostics. It does not call Alpaca, read positions, create orders, write SQLite `trade_log`, send Discord alerts, enable shorting, enable margin, or approve execution.

Crypto monitor display reads saved crypto CSVs only and prints a terminal summary of current desired positions, signal reasons, saved decision status, saved robustness status, and saved period diagnostics. It does not refresh market data, call yfinance, call Alpaca, read positions, write files, create orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Crypto research state report reads saved crypto CSVs only and writes `data/crypto_research_state_report.csv`. It combines universe status, saved decision status, saved signal preview, selected-candidate robustness and cost-stress status, separately labelled all-strategy robustness and cost-stress statuses, and period diagnostics across `BTC/USD`, `ETH/USD`, and `LTC/USD`. It is a checkpoint report only and does not refresh data, call Alpaca, add symbols, add strategies, or approve execution.

Promoted strategy preview mode may inspect current market data for preview candidates and add regime/trend/breakout diagnostics, but it remains research-only. The trend previews intentionally differ: `sma_50_200_trend` uses 50-day SMA versus 200-day SMA, while `buy_above_200_exit_below_200` uses close versus 200-day SMA. It does not place orders, read paper positions, write `trade_log`, or approve execution.

Promoted action preview mode may compare desired positions with read-only Alpaca paper positions, but it remains preview-only. By default, dry-run mode does not read paper positions. The explicit `--use-paper-positions-readonly` flag allows `python bot.py --preview-promoted-actions` to read Alpaca paper positions for preview context while leaving `dry_run` and `config.json` unchanged. This is different from setting `dry_run=false`. If paper positions cannot be read, rows remain `position_unavailable`. It does not create orders, cancel orders, write `trade_log`, send alerts, or approve execution.

Promoted action display mode reads only `data/promoted_strategy_action_preview.csv`, which is produced by `python bot.py --preview-promoted-actions`. It does not refresh market data, call Alpaca, read positions, submit or cancel orders, write SQLite rows, send Discord alerts, or approve execution.

Promoted risk preview mode reads saved promoted strategy CSVs only and writes `data/promoted_risk_preview.csv`. It is a conservative research-only inspection layer for desired long counts, duplicate ticker exposure, concentration risk, unavailable position context from the saved action preview, and rough desired notional estimates from saved `latest_close` values. It does not refresh market data, call yfinance, call Alpaca, read live/current positions directly, submit/cancel/create orders, write SQLite `trade_log` rows, send Discord alerts, or approve execution. Every output row is marked `research_only=True` and `preview_only=True`. The notional fields are `latest_close`, `assumed_quantity`, and `estimated_desired_notional`; they use saved `latest_close` values and `assumed_quantity=1`. They are saved-data-only estimates, not order instructions.

Current promoted risk checks:

- desired long count versus a conservative `max_open_positions`
- duplicate ticker exposure across promoted strategy rows
- concentration risk where multiple promoted strategies want the same ticker long
- unavailable current position data from the action preview
- notional data quality for saved `latest_close` values

Promoted risk display mode is intended to run after `python bot.py --promoted-risk-preview`. It reads only `data/promoted_risk_preview.csv`. It does not refresh market data, call yfinance, call Alpaca, read live/current positions, submit/cancel/create orders, write files, write SQLite `trade_log` rows, send Discord alerts, or approve execution. It displays count by `risk_status`, count by `risk_check`, count by `desired_position`, estimated desired notional by strategy, duplicated desired notional by ticker, unique desired notional by ticker, unique account-style desired notional total, blocked-for-review rows, warning rows, and a compact table of risk rows. Duplicated desired notional by ticker intentionally counts overlapping promoted strategy rows, while unique desired notional by ticker counts each desired-long ticker once for a more account-style exposure view.

Promoted consensus preview mode reads `data/promoted_strategy_preview.csv` and writes `data/promoted_consensus_preview.csv`. It groups promoted strategy rows by ticker, counts desired long/flat/other votes, and labels ticker-level agreement as `unanimous_long`, `unanimous_flat`, `mixed_long_flat`, `no_supported_votes`, or `unknown`. It is research-only and preview-only; every row has `execution_eligible=False`. It does not refresh market data, call yfinance, call Alpaca, read live/current positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

Promoted decision preview mode reads `data/promoted_consensus_preview.csv`, `data/promoted_strategy_action_preview.csv`, and `data/promoted_risk_preview.csv`. It writes `data/promoted_decision_preview.csv` and combines consensus, action, and risk context into a ticker-level policy judgement. Every row has `execution_approved=False`, `research_only=True`, and `preview_only=True`. It is a policy preview only; it does not refresh market data, call yfinance, call Alpaca, read live/current positions, create/submit/cancel orders, write SQLite `trade_log`, send Discord alerts, or approve execution.

C. Add risk-management research.

D. Only later consider paper execution for one conservative strategy after preview and risk checks.

E. Do not connect adaptive or rotation to paper execution yet.

## Safety Boundary

All research strategies remain research-only.

No new strategy should be connected to Alpaca execution without preview mode, risk checks, and explicit confirmation.

Live trading remains out of scope for this project.
