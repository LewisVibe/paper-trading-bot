# Current State

This checkpoint is documentation only. It summarizes the project state for future Codex or ChatGPT sessions without changing code, configs, strategy logic, CSV outputs, or execution behavior.

## Safety Boundary

- This project is paper-only. Live trading is out of scope.
- `dry_run` defaults to `true`.
- `alpaca.paper` must remain `true`; the bot refuses non-paper Alpaca mode.
- `config.json`, API keys, and Discord webhook URLs stay private.
- Research, backtest, report, preview, and display commands do not approve execution.
- Execution-related commands are separate high-risk paths and must stay behind explicit confirmation and review.

## Stock/ETF Research State

- Best benchmark: `buy_and_hold_baseline`.
- No active strategy currently replaces buy-and-hold as the benchmark replacement.
- Best active trend candidate: `sma_50_200_trend`.
- Best defensive candidate: `monthly_etf_momentum_rotation`.
- Promising but split-sensitive defensive research candidate: `volatility_managed_dual_momentum_etf`.
- Secondary defensive candidate: `adaptive_risk_on_off_momentum`.
- Lowest drawdown active strategy: `fifty_two_week_high_breakout`.
- Adaptive now has explicit `full_period`, `in_sample`, and `out_of_sample` rows and is no longer missing walk-forward data.
- Volatility-managed ETF momentum beats monthly ETF rotation on 2 of 3 fixed splits, but loses the `split_80_20` comparison on CAGR, Sharpe, and Calmar.
- Adaptive remains research-only because ETF rotation and volatility-managed ETF momentum lead on defensive metrics, while adaptive has higher complexity and turnover.

## Defensive Candidate Comparison

- `monthly_etf_momentum_rotation`: `preferred_defensive_candidate`.
- `volatility_managed_dual_momentum_etf`: `promising_but_split_sensitive`.
- `adaptive_risk_on_off_momentum`: secondary or lower because of higher turnover and complexity burden.
- The comparison report separates raw OOS metric rank from policy rank: vol-managed can lead on raw metrics while ETF rotation remains policy rank 1 because vol-managed is still split-sensitive.
- No defensive candidate is execution-approved.
- Future defensive work should compare fixed-split consistency, turnover, cost burden, drawdown periods, out-of-sample Sharpe/Calmar, and portfolio role.

The ETF defensive drawdown comparison comes from `python bot.py --etf-defensive-drawdown-comparison`:

- ETF rotation worst drawdown: `2018-10-01` -> `2019-08-05`, `20.1858%`.
- Vol-managed ETF worst drawdown: `2018-10-01` -> `2020-03-18`, `25.7488%`.
- `split_80_20` drawdown comparison: ETF rotation `11.2666%`, vol-managed ETF `10.1051%`.
- Interpretation: vol-managed ETF has lower `split_80_20` drawdown, but ETF rotation leads `split_80_20` CAGR, Sharpe, and Calmar. Lower drawdown alone is not enough to displace ETF rotation while vol-managed remains split-sensitive.

ETF defensive comparison charting comes from `python bot.py --plot-etf-defensive-comparison`:

- It reads saved CSV files only and is research/display only.
- It creates `data/charts/etf_defensive_equity_comparison.png`.
- It creates `data/charts/etf_defensive_drawdown_comparison.png`.
- Purpose: visually compare `monthly_etf_momentum_rotation` and `volatility_managed_dual_momentum_etf` equity curves and drawdowns rather than relying only on CSV metrics.
- Interpretation: the charts are diagnostic only. They do not change the current conclusion that ETF rotation remains the preferred defensive candidate while vol-managed ETF remains promising but split-sensitive.
- The chart command does not approve execution.

## Drawdown-Period Findings

These findings come from `python bot.py --drawdown-period-report`. They are research-only and do not approve execution.

- Worst benchmark drawdown: `buy_and_hold_baseline`, `2021-12-27` -> `2023-01-05`, `30.2278%`.
- Worst active drawdown: `sma_50_200_trend`, `2020-02-19` -> `2020-03-23`, `30.2351%`.
- Best drawdown reduction versus benchmark: `monthly_etf_momentum_rotation`, `2022-04-08` -> `2023-03-15`, reduction `14.2869` percentage points, with strategy drawdown `15.9409%` versus benchmark drawdown `30.2278%`.
- ETF rotation worst drawdown: `20.1858%`.
- Adaptive worst drawdown: `28.4416%`.
- Adaptive had a slow 2022-style drawdown recovery, with `recovery_duration_days=861`.
- Interpretation: ETF rotation remains the preferred defensive candidate. Adaptive remains secondary because its drawdown/recovery profile and turnover are worse than ETF rotation.

## Short-Selling Research State

These findings are research-only. They do not enable shorting, approve short previews, approve short execution, or add crypto shorting.

Short-selling readiness comes from `python bot.py --short-selling-readiness-report`:

- Readiness result: pass `9`, warning `1`, blocked `0`.
- Short selling remains disabled by default.
- The one warning is that normal trade-decision helpers contain shorting logic, but it is gated by `allow_shorting`.
- No short execution command exists.
- Slow SMA paper execution remains long-only.
- Crypto shorting remains disabled.
- The promoted strategy pipeline remains long/flat.

The first SPY short hedge research test comes from `python bot.py --short-hedge-backtest`:

- Strategy: `research_spy_short_hedge`.
- Rule: synthetic SPY short when SPY close is below SMA200; cover when close is at or above SMA200.
- Full-period result: CAGR `-3.2760%`, Sharpe `-0.2404`, max drawdown `33.9800%`, Calmar `-0.0964`.
- Out-of-sample result: CAGR `-3.7001%`, Sharpe `-0.3975`, max drawdown `17.3072%`, Calmar `-0.2138`.
- Research status: `not_useful`.
- Borrow fees and real short constraints are not modelled.
- Conclusion: pause short hedge research; do not continue this simple rule to preview or execution.

The controlled multi-ticker ETF short research test comes from `python bot.py --short-strategy-lab`:

- Strategy: `research_weak_etf_short_momentum`.
- Rule: monthly short weakest `N=2` liquid ETFs by 126-day momentum, only when SPY is below SMA200 and the ETF is below its own SMA200.
- Borrow fee placeholder: `300` bps annual.
- Full-period result: CAGR `-7.6551%`, Sharpe `-0.5735`, max drawdown `54.8795%`, Calmar `-0.1395`.
- Out-of-sample result: CAGR `-2.8997%`, Sharpe `-0.3000`, max drawdown `18.8880%`, Calmar `-0.1535`.
- Research status: `not_useful`.

Conclusion: pause short-selling research for now. Do not add short preview or short execution. Only revisit short research if a new fixed hypothesis is supported by external research and includes borrow-fee, borrow-availability, recall, squeeze, and short-sale constraint modelling. `allow_shorting` must remain default false. No short execution, short preview, or short crypto support is approved.

## Promoted Strategy Pipeline

These commands form a non-execution review chain:

- `python bot.py --preview-promoted-strategies`
- `python bot.py --preview-promoted-actions`
- `python bot.py --preview-promoted-actions --use-paper-positions-readonly`
- `python bot.py --show-promoted-actions`
- `python bot.py --promoted-risk-preview`
- `python bot.py --show-promoted-risk`
- `python bot.py --promoted-consensus-preview`
- `python bot.py --promoted-decision-preview`

Current promoted interpretation:

- AAPL and SPY had mixed long/flat strategy disagreement.
- MSFT was unanimous flat.
- Decision preview blocked execution because of strategy disagreement or no action.
- All promoted strategy outputs remain preview-only or research-only.

## Crypto Research State

Crypto remains research-only. No crypto execution has been added.

Research chain:

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

Current crypto interpretation:

- `BTC/USD`: useful but split-sensitive; keep monitoring.
- `ETH/USD`: useful but research-only; keep monitoring.
- `LTC/USD`: researched but not useful; pause.
- Current crypto signal state: BTC flat, ETH flat, LTC flat.
- BTC best research candidate: `crypto_buy_above_200_with_vol_gate`.
- ETH best research candidate: `crypto_buy_above_200_exit_below_200`.
- LTC should not be iterated unless new evidence appears.
- No shorting, margin, leverage, or Alpaca crypto orders have been added.

## Paused Or Deprioritised

- No SOL expansion yet; avoid adding more tickers until the current crypto universe is understood.
- Do not iterate LTC for now.
- Do not tune adaptive randomly.
- Do not add more crypto strategies just because one split looks good.
- Avoid broad parameter searches and curve-fitting.

## Execution Boundary

Research, backtest, report, display, and preview commands are non-execution paths.

Explicit paper execution areas are high risk:

- Alpaca order submission.
- Manual paper-order smoke test.
- Slow SMA paper execution.
- Normal bot order/logging path.

Any future execution work must require preview, risk checks, consensus/decision review where relevant, and explicit confirmation. Research-only or preview-only rows must never be treated as execution approval.

## Recommended Next Steps

A. Keep the current research state stable and avoid adding more strategy complexity.

B. Improve reporting/charting around drawdown periods if useful.

C. Consider small refactors only after focused verifiers exist.

D. Only later consider paper execution for one conservative strategy after preview, risk, consensus, and decision checks.

E. Crypto: keep monitoring BTC and ETH; do not add execution.

F. If adding new crypto symbols later, add one at a time and label each as research-only.

## Useful Command Groups

Stock/ETF research refresh:

```text
python bot.py --backtest
python bot.py --compare-strategies
python bot.py --sma-sensitivity
python bot.py --trend-stress-test
python bot.py --etf-rotation-backtest
python bot.py --adaptive-momentum-backtest
python bot.py --research-report
python bot.py --walk-forward-report
python bot.py --strategy-promotion-report
python bot.py --defensive-strategy-report
```

Defensive comparison refresh:

```text
python bot.py --defensive-candidate-comparison
```

Promoted preview chain:

```text
python bot.py --preview-promoted-strategies
python bot.py --preview-promoted-actions
python bot.py --show-promoted-actions
python bot.py --promoted-risk-preview
python bot.py --show-promoted-risk
python bot.py --promoted-consensus-preview
python bot.py --promoted-decision-preview
```

Crypto research refresh:

```text
python bot.py --crypto-research-preview
python bot.py --crypto-strategy-lab
python bot.py --crypto-strategy-report
python bot.py --crypto-strategy-decision-report
python bot.py --crypto-cost-stress-report
python bot.py --crypto-robustness-report
python bot.py --crypto-period-diagnostics
python bot.py --crypto-research-state-report
```

Crypto signal and monitor refresh:

```text
python bot.py --preview-crypto-signals
python bot.py --show-crypto-monitor
```

Safe focused verification convention:

- Routine verifier blocks only need "passed" unless a failure, traceback, or new warning appears.
- For docs-only changes, runtime verification is not required.
- For Python changes, run the smallest focused verifier first, then broader baseline checks only if needed.
