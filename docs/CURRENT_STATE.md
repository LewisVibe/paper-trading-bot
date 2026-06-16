# Current State

This checkpoint is documentation only. It summarizes the project state for future Codex or ChatGPT sessions without changing code, configs, strategy logic, CSV outputs, or execution behavior.

## Safety Boundary

- This project is paper-only. Live trading is out of scope.
- `dry_run` defaults to `true`.
- `alpaca.paper` must remain `true`; the bot refuses non-paper Alpaca mode.
- `config.json`, API keys, and Discord webhook URLs stay private.
- Research, backtest, report, preview, and display commands do not approve execution.
- Execution-related commands are separate high-risk paths and must stay behind explicit confirmation and review.
- `python scripts\verify_repo_safety.py` should be run before commits and pushes.
- Deployment readiness and VPS checklist docs are audits/planning aids only. They do not deploy, schedule, or approve execution.
- Portfolio risk policy reporting is not runtime enforcement and does not approve execution.

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

The short/leverage research lab comes from `python bot.py --short-leverage-research-lab`, with saved display through `python bot.py --show-short-leverage-research-lab`:

- It tests fixed synthetic hypotheses only: SPY/QQQ trend-gated leverage, saved stock/ETF lead leverage proxies when saved equity exists, weak-regime SPY short hedge, fixed sector relative long/short, and fixed defensive-versus-cyclical spread.
- It writes `data/short_leverage_research_lab.csv`, summary, cost, split, and drawdown CSVs.
- Cost, borrow-fee, and financing rows are placeholder sensitivities only, not broker-specific terms.
- Every row keeps `execution_approved=false`, `short_execution_approved=false`, `leverage_execution_approved=false`, `margin_approved=false`, `scheduling_approved=false`, `alpaca_called=false`, and `orders_created=false`.

The focused QQQ leverage validation report comes from `python bot.py --qqq-leverage-validation-report`, with saved display through `python bot.py --show-qqq-leverage-validation-report`:

- It tests fixed QQQ SMA200 trend-gated synthetic exposure levels: `1.0x`, `1.25x`, `1.5x`, `1.75x`, and `2.0x`.
- It writes `data/qqq_leverage_validation_report.csv`, summary, cost/financing, split, and drawdown CSVs.
- It compares against QQQ buy-and-hold, SPY buy-and-hold, and cash where market data is available.
- It is validation only. It does not approve leverage, margin, shorting, paper execution, live trading, scheduling, or strategy-to-execution wiring.

The QQQ adaptive leverage lab comes from `python bot.py --qqq-adaptive-leverage-lab`, with saved display through `python bot.py --show-qqq-adaptive-leverage-lab`:

- It compares QQQ buy-and-hold, SPY buy-and-hold, `qqq_100_trend_gate`, `qqq_125_trend_gate`, `qqq_150_trend_gate`, and two fixed Codex adaptive candidates.
- `codex_qqq_adaptive_trend_exposure` holds cash below QQQ SMA200, uses 1.0x in elevated volatility, 1.25x in normal positive trend, and 1.5x only when 20-day realised volatility is below 90% of its 252-day median.
- `codex_qqq_drawdown_brake_trend` holds cash below QQQ SMA200, uses 1.25x in positive trend, cuts to 0.75x after an 8% rolling 63-day drawdown, and requires 20-day recovery confirmation before re-leveraging.
- It writes `data/qqq_adaptive_leverage_lab.csv`, summary, cost/financing, split, and drawdown CSVs.
- It is research-only and does not approve leverage, margin, paper execution, live trading, scheduling, or strategy-to-execution wiring.

The QQQ lead decision report comes from `python bot.py --qqq-lead-decision-report`, with saved display through `python bot.py --show-qqq-lead-decision-report`:

- It reads saved QQQ leverage/adaptive outputs and saved Codex ambitious lead-decision context only.
- It compares `codex_ambitious_concentrated_growth_persistence`, `qqq_100_trend_gate`, `codex_qqq_adaptive_trend_exposure`, high-drawdown QQQ leverage references, and SPY/QQQ benchmarks where saved inputs exist.
- It writes `data/qqq_lead_decision_report.csv`, `data/qqq_lead_decision_summary.csv`, and `data/qqq_lead_decision_evidence.csv`.
- It does not refresh data, call yfinance or Alpaca, approve preview promotion, approve leverage or margin, schedule anything, or connect research to execution.

The QQQ trend-gate manual review pack comes from `python bot.py --qqq-trend-gate-manual-review-pack`, with saved display through `python bot.py --show-qqq-trend-gate-manual-review-pack`:

- It reads saved QQQ decision, validation, adaptive, project-state, and paper-readiness context only.
- It confirms `qqq_100_trend_gate` as the stock/ETF research lead, keeps `codex_qqq_adaptive_trend_exposure` as the ambitious alternative, and keeps `qqq_150_trend_gate` as the rejected high-drawdown reference.
- It writes `data/qqq_trend_gate_manual_review_pack.csv`, `data/qqq_trend_gate_manual_review_summary.csv`, `data/qqq_trend_gate_manual_review_evidence.csv`, and `data/qqq_trend_gate_manual_review_blockers.csv`.
- Expected status is `qqq_trend_gate_research_lead_confirmed_not_execution_ready`.
- It is research/report-only, does not approve preview promotion, does not approve execution, does not approve leverage or margin, does not schedule anything, and does not connect strategies to Alpaca or paper orders.

The QQQ preview-candidate readiness report comes from `python bot.py --qqq-preview-candidate-readiness-report`, with saved display through `python bot.py --show-qqq-preview-candidate-readiness-report`:

- It reads the saved QQQ manual review pack, lead decision, validation cost/split/drawdown rows, project research state, and paper-readiness context where available.
- It asks whether `qqq_100_trend_gate` is ready for manual preview-candidate discussion and records what still blocks paper execution.
- It writes `data/qqq_preview_candidate_readiness_report.csv`, `data/qqq_preview_candidate_readiness_summary.csv`, `data/qqq_preview_candidate_readiness_evidence.csv`, and `data/qqq_preview_candidate_readiness_blockers.csv`.
- Preview readiness is manual discussion only; it does not approve paper execution, does not approve execution, does not approve scheduling, and does not connect strategies to Alpaca or paper orders.

The QQQ100 preview-candidate readiness pack comes from `python bot.py --qqq100-preview-candidate-readiness-pack`, with saved display through `python bot.py --show-qqq100-preview-candidate-readiness-pack`:

- It reads saved QQQ lead/manual/readiness, adaptive/leverage validation, high-growth branch, project research-state, and paper-readiness outputs where present.
- It writes `data/qqq100_preview_candidate_readiness_pack.csv`, `data/qqq100_preview_candidate_readiness_summary.csv`, `data/qqq100_preview_candidate_readiness_evidence.csv`, and `data/qqq100_preview_candidate_readiness_blockers.csv`.
- It keeps `qqq_100_trend_gate` as the clean main lead, keeps `codex_qqq_adaptive_trend_exposure` as an ambitious alternative only, keeps `qqq_150_trend_gate` rejected, and keeps the high-growth stock branch out of preview discussion.
- It does not add preview implementation, does not approve paper execution, does not approve execution, does not approve scheduling, and does not connect strategies to Alpaca or paper orders.

The QQQ100 preview signal pack comes from `python bot.py --qqq100-preview-signal-pack`, with saved display through `python bot.py --show-qqq100-preview-signal-pack`:

- It may fetch QQQ daily data, calculate close versus the fixed 100-day SMA trend gate, and write `data/qqq100_preview_signal_pack.csv`, `data/qqq100_preview_signal_summary.csv`, `data/qqq100_preview_signal_design.csv`, and `data/qqq100_preview_signal_blockers.csv`.
- It records a non-execution preview signal only: `desired_position=long` above SMA100 or `desired_position=flat` at or below SMA100.
- It excludes the high-growth branch from preview, keeps `codex_qqq_adaptive_trend_exposure` alternative-only, keeps `qqq_150_trend_gate` rejected, and keeps action preview versus paper positions out of scope.
- It does not approve execution, does not create order instructions, does not read positions, does not approve scheduling, and does not connect strategies to Alpaca or paper orders.

The QQQ100 action preview shell comes from `python bot.py --qqq100-action-preview`, with saved display through `python bot.py --show-qqq100-action-preview`:

- Default mode reads only `data/qqq100_preview_signal_pack.csv` and writes `data/qqq100_action_preview.csv`, `data/qqq100_action_preview_summary.csv`, and `data/qqq100_action_preview_blockers.csv`.
- Default mode does not call Alpaca or read positions; it records `position_not_read` and `saved_signal_only`.
- Optional read-only paper-position context requires both `--use-paper-positions-readonly` and `--confirm-readonly-alpaca-check`; that mode is limited to QQQ paper-position comparison context and must not print secrets or account identifiers.
- The output uses alignment/manual-review wording only and does not create order instructions, approve paper execution, approve execution, approve scheduling, or connect the strategy to Alpaca or paper orders.

The QQQ100 paper-readiness blocker report comes from `python bot.py --qqq100-paper-readiness-blocker-report`, with saved display through `python bot.py --show-qqq100-paper-readiness-blocker-report`:

- It reads saved preview-signal, action-preview, QQQ readiness, portfolio risk, execution eligibility, paper kill-switch, paper-order smoke-test, project research-state, and high-growth contrast outputs where present.
- It writes `data/qqq100_paper_readiness_blocker_report.csv`, `data/qqq100_paper_readiness_blocker_summary.csv`, `data/qqq100_paper_readiness_blocker_evidence.csv`, and `data/qqq100_paper_readiness_blocker_blockers.csv`.
- It records blockers including the separate AAPL smoke test, QQQ100 execution design, sizing, portfolio risk enforcement, kill-switch enforcement, execution eligibility, open-order and duplicate-exposure handling, manual confirmation wording, postcheck design, scheduling, and strategy-to-execution integration.
- It is saved-output only and does not call Alpaca, read positions, refresh market data, create order instructions, approve paper execution, approve execution, approve scheduling, or connect strategies to paper orders.

The QQQ100 paper execution readiness report comes from `python bot.py --qqq100-paper-execution-readiness-report`, with saved display through `python bot.py --show-qqq100-paper-execution-readiness-report`:

- It reads saved readiness evidence only, including the AAPL smoke-test postcheck, QQQ100 preview signal/action preview, promoted preview row, multi-strategy portfolio overlap warnings, portfolio-risk, execution eligibility, kill-switch, protection, and project-state outputs where present.
- It writes `data/qqq100_paper_execution_readiness_report.csv`, `data/qqq100_paper_execution_readiness_summary.csv`, `data/qqq100_paper_execution_readiness_evidence.csv`, and `data/qqq100_paper_execution_readiness_blockers.csv`.
- It may say QQQ100 is ready for manual execution-design review, but it does not itself approve broad paper execution, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or connect strategies to paper orders.

The QQQ100 manual paper execution command is `python bot.py --execute-qqq100-paper --confirm-qqq100-paper`:

- It is high-risk and manually confirmed.
- It reads only the saved `data/qqq100_preview_signal_pack.csv` signal for `qqq_100_trend_gate` / `QQQ`.
- It is fixed to one QQQ share, requires Alpaca paper mode, refuses live mode, refuses shorting/leverage, and does not use the normal config ticker universe.
- It checks QQQ paper position, open QQQ orders, market-open status, and recent matching QQQ one-share broker orders before any submission.
- It may buy one QQQ share when the saved signal is `long` and QQQ is flat, may sell one QQQ share when the saved signal is `flat` and QQQ is long without overselling, and otherwise writes a no-order-needed or blocked result.
- It writes `data/qqq100_paper_execution_result.csv`, `data/qqq100_paper_execution_summary.csv`, and `data/qqq100_paper_execution_blockers.csv` when run.
- General `execution_approved`, `paper_execution_approved`, and `scheduling_approved` remain false. It must not be scheduled and must not be generalized to normal `python bot.py`, `--paper-order-test`, slow-SMA paper execution, high-growth, crypto, QQQ150, or adaptive QQQ paths.

The QQQ100 paper postcheck comes from `python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check`, with saved display through `python bot.py --show-qqq100-paper-postcheck`. It is read-only: it checks recent QQQ buy 1 paper order history and current QQQ paper position only after explicit read-only confirmation, writes `data/qqq100_paper_postcheck.csv`, `data/qqq100_paper_postcheck_summary.csv`, and `data/qqq100_paper_postcheck_blockers.csv`, and approves no follow-up, repeat, scheduling, or general execution.

The QQQ100 repeat/alignment workflow design comes from `python bot.py --qqq100-repeat-alignment-workflow-design`, with saved display through `python bot.py --show-qqq100-repeat-alignment-workflow-design`:

- It reads saved CSV context only, including QQQ100 signal/action preview, QQQ100 paper postcheck, paper execution state summary, readiness, portfolio preview/risk, and connectivity diagnostics where present.
- It writes `data/qqq100_repeat_alignment_workflow_design.csv`, `data/qqq100_repeat_alignment_workflow_states.csv`, `data/qqq100_repeat_alignment_workflow_blockers.csv`, and `data/qqq100_repeat_alignment_workflow_checklist.csv`.
- It is QQQ only and `qqq_100_trend_gate` only, with a planned maximum of one QQQ paper share for the current manual workflow.
- It records future design states such as `possible_manual_open_long_candidate`, `aligned_long_no_action`, `aligned_flat_no_action`, `possible_manual_flatten_review`, `block_due_to_open_order`, and `block_due_to_recent_order_cooldown`.
- It explicitly blocks duplicate buys when already long one share, scaling above one share, automatic flattening, high-growth/crypto linkage, scheduling, and repeat execution approval.
- It does not call Alpaca, read live positions, refresh market data, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve follow-up/repeat/general execution.

The multi-sleeve strategy monitor comes from `python bot.py --multi-sleeve-strategy-monitor`, with saved display through `python bot.py --show-multi-sleeve-strategy-monitor`:

- It reads saved CSV context only, including paper execution state, QQQ100 postcheck/action preview/repeat design, multi-strategy portfolio preview, portfolio risk, high-growth checkpoints, crypto research summaries, and project research state where present.
- It writes `data/multi_sleeve_strategy_monitor.csv`, `data/multi_sleeve_strategy_sleeves.csv`, `data/multi_sleeve_strategy_positions.csv`, `data/multi_sleeve_strategy_blockers.csv`, and `data/multi_sleeve_strategy_next_steps.csv`.
- It treats `qqq100_core_trend_sleeve` as the only active paper sleeve when saved evidence confirms QQQ long 1 and aligned.
- It keeps `defensive_etf_research_sleeve`, `high_growth_stock_research_sleeve`, and `crypto_research_sleeve` research-only, and keeps `cash_or_no_position_sleeve` design-only.
- It surfaces overlap and readiness warnings such as `high_growth_and_qqq_overlap_risk`, `crypto_volatility_sleeve_not_ready`, `defensive_sleeve_not_validated_for_execution`, `sleeve_allocation_policy_missing`, `repeat_execution_not_approved`, and `scheduling_not_approved`.
- It does not call Alpaca, read live positions, refresh market data, create orders, write SQLite `trade_log`, send alerts, add scheduling/Hermes/cron, expand QQQ100 execution, or approve any new execution path.

The paper execution state summary comes from `python bot.py --paper-execution-state-summary`, with saved display through `python bot.py --show-paper-execution-state-summary`:

- It reads saved CSV outputs only, including AAPL smoke-test postcheck, QQQ100 paper execution result/summary or QQQ100 paper postcheck, QQQ100 action preview, QQQ100 signal, readiness, connectivity, execution eligibility, portfolio preview, and portfolio-risk context where available.
- It writes `data/paper_execution_state_summary.csv`, `data/paper_execution_state_positions.csv`, `data/paper_execution_state_milestones.csv`, and `data/paper_execution_state_blockers.csv`.
- It can record historical milestone labels such as `aapl_smoke_test_filled_confirmed`, `qqq100_manual_paper_execution_filled_confirmed`, and `qqq100_aligned_long_confirmed` when saved evidence exists.
- It does not call Alpaca, read paper positions live, refresh market data, create/submit/cancel orders, write SQLite `trade_log`, send alerts, schedule anything, approve follow-up orders, approve repeat execution, or approve general execution.

The multi-strategy portfolio preview combiner comes from `python bot.py --multi-strategy-portfolio-preview`, with saved display through `python bot.py --show-multi-strategy-portfolio-preview`:

- It reads saved CSV outputs only, including QQQ100 preview/action outputs, promoted preview rows, defensive context, high-growth branch checkpoints, crypto research/manual-review outputs, project research state, execution eligibility, and portfolio-risk policy outputs where present.
- It writes `data/multi_strategy_portfolio_preview.csv`, `data/multi_strategy_portfolio_preview_summary.csv`, `data/multi_strategy_portfolio_preview_exposures.csv`, `data/multi_strategy_portfolio_preview_conflicts.csv`, and `data/multi_strategy_portfolio_preview_blockers.csv`.
- It treats QQQ100 as the core growth trend candidate, defensive context as optional, high-growth and crypto as research-only/blocked, and missing saved inputs as unavailable context rather than refreshing data.
- It is portfolio preview/report only and does not call yfinance, call Alpaca, read paper positions, create order instructions, write SQLite `trade_log`, send Discord or Telegram alerts, approve scheduling, approve execution, or connect strategies to paper orders.

The high-growth stock lab comes from `python bot.py --high-growth-stock-lab`, with saved display through `python bot.py --show-high-growth-stock-lab`:

- It trades only the fixed individual-stock universe `AAPL`, `MSFT`, `NVDA`, `AMZN`, `META`, `GOOGL`, `AVGO`, `AMD`, `TSLA`, and `NFLX`.
- SPY and QQQ are used only as benchmark/regime references.
- It tests fixed monthly top 1/top 2/top 3 composite momentum, `codex_high_conviction_growth_persistence`, `codex_growth_drawdown_reentry`, `codex_high_growth_breakout_acceleration`, and `codex_high_growth_crash_rebound_leader` without parameter search.
- The two newer Codex-designed variants are ambitious stock-only research candidates: breakout acceleration near 52-week highs, and crash-rebound leadership after QQQ/SPY recovery confirmation.
- It writes `data/high_growth_stock_lab.csv`, `data/high_growth_stock_lab_summary.csv`, `data/high_growth_stock_lab_trades.csv`, `data/high_growth_stock_lab_costs.csv`, `data/high_growth_stock_lab_splits.csv`, `data/high_growth_stock_lab_drawdowns.csv`, and `data/high_growth_stock_lab_concentration.csv`.
- It is research-only, flags survivorship bias and concentration risk, does not approve execution, and does not connect strategies to Alpaca or paper orders.

The high-growth stock universe expansion report comes from `python bot.py --high-growth-stock-universe-expansion-report`, with saved display through `python bot.py --show-high-growth-stock-universe-expansion-report`:

- It compares `mega_cap_growth_10`, `expanded_growth_30`, and `broad_liquid_growth_50` using fixed individual-stock universes only.
- SPY and QQQ remain benchmark/regime references only; ETFs are not traded holdings inside the stock strategies.
- It writes `data/high_growth_stock_universe_expansion_report.csv`, `data/high_growth_stock_universe_expansion_summary.csv`, `data/high_growth_stock_universe_expansion_trades.csv`, `data/high_growth_stock_universe_expansion_costs.csv`, `data/high_growth_stock_universe_expansion_splits.csv`, `data/high_growth_stock_universe_expansion_drawdowns.csv`, and `data/high_growth_stock_universe_expansion_concentration.csv`.
- It asks whether the top3 high-growth result improves, decays, or becomes more unstable as universe breadth expands. Current-constituent survivorship bias and concentration risk remain explicit; the report does not approve execution and does not connect strategies to Alpaca or paper orders.

The high-growth stock drawdown-control report comes from `python bot.py --high-growth-stock-drawdown-control-report`, with saved display through `python bot.py --show-high-growth-stock-drawdown-control-report`:

- It uses the fixed `broad_liquid_growth_50` individual-stock universe only; SPY and QQQ remain benchmark/regime references only.
- It tests fixed drawdown-control variants: top2/top3 concentration references, Top1 drawdown brake, Top1 volatility gate, Top1 cooldown after crash, and `codex_broad_growth_balanced_breakout_control`.
- It writes `data/high_growth_stock_drawdown_control_report.csv`, `data/high_growth_stock_drawdown_control_summary.csv`, `data/high_growth_stock_drawdown_control_trades.csv`, `data/high_growth_stock_drawdown_control_costs.csv`, `data/high_growth_stock_drawdown_control_splits.csv`, `data/high_growth_stock_drawdown_control_drawdowns.csv`, and `data/high_growth_stock_drawdown_control_concentration.csv`.
- It asks whether drawdown can be reduced enough to justify the high-growth branch. Survivorship bias, current-constituent bias, concentration risk, outlier dependence, cost/split sensitivity, and drawdown risk remain explicit; the report does not approve execution and does not connect strategies to Alpaca or paper orders.

The high-growth stock lead decision checkpoint comes from `python bot.py --high-growth-stock-lead-decision-report`, with saved display through `python bot.py --show-high-growth-stock-lead-decision-report`:

- It reads saved high-growth lab, universe expansion, drawdown-control, QQQ lead, QQQ review, preview-readiness, and project research-state CSVs where present; it does not refresh yfinance data.
- It writes `data/high_growth_stock_lead_decision_report.csv`, `data/high_growth_stock_lead_decision_summary.csv`, `data/high_growth_stock_lead_decision_evidence.csv`, and `data/high_growth_stock_lead_decision_blockers.csv`.
- It keeps `qqq_100_trend_gate` as the clean main stock/ETF lead, keeps `codex_qqq_adaptive_trend_exposure` as the ambitious QQQ alternative, rejects `broad_liquid_growth_50:concentrated_growth_momentum_top1` as the extreme drawdown reference, and labels `codex_broad_growth_balanced_breakout_control` as the high-risk stock research lead candidate.
- It is saved-output and research-only; it does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.

The high-growth stock manual review pack comes from `python bot.py --high-growth-stock-manual-review-pack`, with saved display through `python bot.py --show-high-growth-stock-manual-review-pack`:

- It reads saved high-growth lead-decision, lab, universe-expansion, drawdown-control, QQQ, and project research-state CSVs where present; it does not refresh yfinance data.
- It writes `data/high_growth_stock_manual_review_pack.csv`, `data/high_growth_stock_manual_review_summary.csv`, `data/high_growth_stock_manual_review_evidence.csv`, and `data/high_growth_stock_manual_review_blockers.csv`.
- It keeps `qqq_100_trend_gate` as the clean main stock/ETF lead, keeps `codex_broad_growth_balanced_breakout_control` as a high-risk stock research lead candidate only, keeps broad Top1 rejected, and blocks preview-candidate and paper-execution discussion.
- It is saved-output and research-only; it does not approve execution and does not connect strategies to Alpaca or paper orders.

The high-growth stock risk review pack comes from `python bot.py --high-growth-stock-risk-review-pack`, with saved display through `python bot.py --show-high-growth-stock-risk-review-pack`:

- It reads saved high-growth manual-review, lead-decision, lab, universe-expansion, drawdown-control, QQQ, and project research-state CSVs where present; it does not refresh yfinance data.
- It writes `data/high_growth_stock_risk_review_pack.csv`, `data/high_growth_stock_risk_review_summary.csv`, `data/high_growth_stock_risk_review_evidence.csv`, and `data/high_growth_stock_risk_review_blockers.csv`.
- It focuses on cost sensitivity, split sensitivity, concentration risk, outlier dependence, survivorship/current-constituent bias, drawdown severity, drawdown improvement versus broad Top1, and drawdown worsening versus `qqq_100_trend_gate`.
- It keeps `qqq_100_trend_gate` as the clean main lead, keeps `codex_broad_growth_balanced_breakout_control` high-risk research-only, keeps broad Top1 rejected, and keeps preview and execution blocked.

The high-growth stock risk evidence review comes from `python bot.py --high-growth-stock-risk-evidence-review`, with saved display through `python bot.py --show-high-growth-stock-risk-evidence-review`:

- It reads saved high-growth risk-review, manual-review, lead-decision, lab, universe-expansion, drawdown-control, QQQ, and project research-state CSVs where present; it does not refresh yfinance data.
- It writes `data/high_growth_stock_risk_evidence_review.csv`, `data/high_growth_stock_risk_evidence_summary.csv`, `data/high_growth_stock_risk_evidence_details.csv`, and `data/high_growth_stock_risk_evidence_blockers.csv`.
- It summarises return improvement versus `qqq_100_trend_gate`, drawdown worsening versus `qqq_100_trend_gate`, Calmar/Sharpe tradeoff, drawdown improvement versus broad Top1, fixed cost/split/concentration evidence, outlier dependence, and survivorship/current-constituent bias.
- It keeps `qqq_100_trend_gate` as the clean main lead, keeps `codex_broad_growth_balanced_breakout_control` high-risk research-only, keeps broad Top1 rejected, and does not approve execution, preview promotion, paper execution, or scheduling.

The high-growth stock branch decision checkpoint comes from `python bot.py --high-growth-stock-branch-decision-checkpoint`, with saved display through `python bot.py --show-high-growth-stock-branch-decision-checkpoint`:

- It reads saved high-growth risk-evidence, risk-review, manual-review, lead-decision, lab, universe-expansion, drawdown-control, QQQ, and project research-state CSVs where present; it does not refresh yfinance data.
- It writes `data/high_growth_stock_branch_decision_checkpoint.csv`, `data/high_growth_stock_branch_decision_summary.csv`, `data/high_growth_stock_branch_decision_evidence.csv`, and `data/high_growth_stock_branch_decision_blockers.csv`.
- It converts saved evidence into one conservative branch decision: continue research-only, pause due to drawdown, require a final validation pack before preview discussion, or mark saved evidence insufficient.
- It keeps `qqq_100_trend_gate` as the clean main lead, keeps broad Top1 rejected, keeps preview and execution blocked, and does not approve execution, preview promotion, paper execution, or scheduling.

The high-growth stock final validation pack comes from `python bot.py --high-growth-stock-final-validation-pack`, with saved display through `python bot.py --show-high-growth-stock-final-validation-pack`:

- It reads saved high-growth branch-decision, risk-evidence, risk-review, manual-review, lead-decision, lab, universe-expansion, drawdown-control, QQQ, and project research-state CSVs where present; it does not refresh yfinance data.
- It writes `data/high_growth_stock_final_validation_pack.csv`, `data/high_growth_stock_final_validation_summary.csv`, `data/high_growth_stock_final_validation_evidence.csv`, and `data/high_growth_stock_final_validation_blockers.csv`.
- It checks return improvement, drawdown tradeoff, broad Top1 improvement, Calmar/Sharpe tradeoff, cost, split, concentration, outlier, survivorship/current-constituent bias, and whether the high-risk branch has a clear role separate from `qqq_100_trend_gate`.
- It keeps `qqq_100_trend_gate` as the clean main lead, keeps broad Top1 rejected, keeps preview and execution blocked, and does not approve execution, preview promotion, paper execution, or scheduling.

Conclusion: short-selling and leverage remain research-only. Do not add short preview, short execution, margin, leverage execution, or crypto shorting. Only revisit these ideas through fixed research hypotheses with explicit borrow-fee, borrow-availability, recall, squeeze, financing, leverage-decay, and drawdown constraint modelling. `allow_shorting` must remain default false. No short execution, short preview, margin support, leverage support, or short crypto support is approved.

## Promoted Strategy Pipeline

These commands form a non-execution review chain:

- `python bot.py --refresh-promoted-review`
- `python bot.py --preview-promoted-strategies`
- `python bot.py --preview-promoted-actions`
- `python bot.py --preview-promoted-actions --use-paper-positions-readonly`
- `python bot.py --show-promoted-actions`
- `python bot.py --promoted-risk-preview`
- `python bot.py --show-promoted-risk`
- `python bot.py --promoted-consensus-preview`
- `python bot.py --promoted-decision-preview`
- `python bot.py --show-promoted-decision`

Current promoted interpretation:

- AAPL: `blocked_strategy_disagreement`.
- MSFT: `no_action_unanimous_flat`.
- SPY: `blocked_strategy_disagreement`.
- `execution_approved=False` for all rows.
- AAPL and SPY remain blocked by strategy disagreement.
- MSFT remains no-action/unanimous flat.
- `qqq_100_trend_gate` / QQQ is now included as a promoted preview-review candidate from the saved `qqq100_preview_signal_pack` output only; if the saved signal is missing, the promoted row is blocked as missing input.
- The high-growth branch `codex_broad_growth_balanced_breakout_control` remains research-only and is not promoted; `qqq_150_trend_gate` remains rejected/not promoted.
- All promoted strategy outputs remain preview-only or research-only.

`--refresh-promoted-review` writes `data/promoted_review_refresh_summary.csv` and runs the promoted review chain in order. It remains preview/report/display only and is protected by the monitor lockfile helper to prevent overlapping refresh runs. The lock does not connect promoted candidates to execution, approve scheduling, or approve execution.

`python scripts\verify_refresh_promoted_review_lock_readiness.py` statically checks that `--refresh-promoted-review` remains preview/report/display only, lock-wrapped only for no-overlap protection, unscheduled, and separate from execution approval.

`python scripts\verify_refresh_defensive_research_lock_readiness.py` statically checks that `--refresh-defensive-research` remains research/report/chart only, lock-wrapped only for no-overlap protection, unscheduled, and separate from execution approval.

## Workflow / Deployment / Risk Policy State

Today's workflow and risk-management additions are safety and reporting only. No deployment, scheduling, strategy change, risk enforcement, or execution approval was added.

Repository safety:

- `python scripts\verify_repo_safety.py` checks tracked and staged dangerous files, required `.gitignore` patterns, and repository hygiene before commits or pushes.
- It is included in the baseline verifier.
- Local repo safety passed.
- Codex may auto-commit and push only small low-risk changes after repo safety passes and after confirming no Python execution paths, generated artefacts, secrets, config defaults, scheduling, or execution behaviour changed.
- Codex must not auto-push medium/high-risk trading changes, order-path changes, normal bot runtime changes, execution command-routing changes, risk/kill-switch enforcement changes, generated outputs, or anything involving credentials/secrets.

Deployment readiness and VPS planning:

- `python bot.py --deployment-readiness-report` writes `data/deployment_readiness_report.csv`.
- It audits local/VPS readiness without deploying, scheduling, refreshing market data, calling Alpaca, reading positions, submitting orders, writing SQLite `trade_log`, or sending Discord alerts.
- `python bot.py --vps-operations-readiness-report` writes `data/vps_operations_readiness_report.csv`.
- It audits whether the repo is ready for VPS/Hermes monitoring/report/display operations only, including repo path, `.venv` expectation, command availability, ignored generated outputs, untracked private files, Hermes market-monitor candidate docs, and never-schedule command boundaries.
- It does not deploy, schedule, create services, load `config.json`, call Alpaca, read paper positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, approve scheduling, or approve execution.
- `docs/HERMES_WORKFLOW.md` documents MCP as a possible future safe operations adapter only for whitelisted report/display/monitor commands. MCP is not approved for implementation yet and must remain separate from trading execution.
- A future news workflow is only worth exploring as a risk veto. It may block or flag new long entries for major negative/event-risk news, but must never generate buy/sell signals, order instructions, position sizing, scheduling approval, or execution approval.
- `docs/VPS_SETUP_CHECKLIST.md` documents future Windows Server VPS setup, safe commands for future scheduling review, commands never to schedule, and secrets/config handling.
- The VPS checklist is future setup documentation only.

Portfolio risk policy:

- `python bot.py --portfolio-risk-policy-report` writes `data/portfolio_risk_policy_report.csv`.
- Current result: `blocked_for_review=1`, `not_implemented_future_work=2`, `pass=7`, `warning=2`.
- `execution_approved=False` for all rows.
- Main blocker: `strategy_disagreement_policy` for AAPL and SPY.
- Warnings: saved notional can be inspected, but no live account equity was read.
- Future-work rows: paper-only kill switch and Discord daily summary.
- `python bot.py --show-portfolio-risk-policy` reads `data/portfolio_risk_policy_report.csv` only and displays status counts, blockers, future-work rows, compact policy rows, and confirms no risk enforcement or execution approval.
- Portfolio risk policy reporting is policy/reporting only. It is not a runtime risk gate and does not enforce order sizing, exposure limits, kill switches, or execution approval.

Low-risk refactor:

- Additional saved display/report wrappers were extracted from `bot.py` into `trading_bot/runners/research_reports.py`.
- High-risk execution paths remained untouched.

Current verified workflow state:

- Full baseline passed locally.
- Repo safety passed locally.
- Git status was clean after commits and pushes.
- No runtime execution path changed.
- No Alpaca order submission path changed.
- No SQLite `trade_log` execution write path changed.
- No Discord alert path changed.
- No strategy logic changed.
- No deployment or scheduling was performed.

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
- `python bot.py --expanded-crypto-lead-decision`
- `python bot.py --show-expanded-crypto-lead-decision`
- `python bot.py --crypto-lead-split-sensitivity-diagnosis`
- `python bot.py --show-crypto-lead-split-sensitivity-diagnosis`
- `python bot.py --expanded-crypto-manual-review-pack`
- `python bot.py --show-expanded-crypto-manual-review-pack`
- `python bot.py --project-research-state-refresh`
- `python bot.py --show-project-research-state-refresh`
- `python bot.py --show-current-research-state`
- `python bot.py --project-research-state-quality-report`

Current crypto interpretation:

- `crypto_equal_weight_ex_highest_vol_2` is the current expanded crypto research lead as a research label only.
- `python bot.py --crypto-lead-split-sensitivity-diagnosis` reads saved crypto research CSVs and writes `data/crypto_lead_split_sensitivity_diagnosis.csv`, `data/crypto_lead_split_sensitivity_summary.csv`, `data/crypto_lead_split_sensitivity_periods.csv`, `data/crypto_lead_split_sensitivity_exclusions.csv`, and `data/crypto_lead_split_sensitivity_contributions.csv`.
- The split-sensitivity diagnosis for the current crypto research lead is research/report-only and does not approve crypto execution, paper execution, preview promotion, scheduling, order instructions, or strategy-to-execution wiring.
- `python bot.py --expanded-crypto-manual-review-pack` writes `data/expanded_crypto_manual_review_pack.csv`, `data/expanded_crypto_manual_review_summary.csv`, `data/expanded_crypto_manual_review_evidence.csv`, and `data/expanded_crypto_manual_review_blockers.csv`.
- This is the manual review pack for the current crypto research lead. It summarises universe readiness, benchmark reality, failed/deprioritised risk-control families, split sensitivity, exclusion instability, outlier dependence, cost review, high-drawdown context, and remaining blockers.
- The manual review pack is research/report-only; it does not approve crypto execution, does not approve preview promotion, and does not connect crypto to Alpaca or paper orders. The current crypto research lead remains manual-review-only unless future review changes that.
- `python bot.py --project-research-state-refresh` writes `data/project_research_state_refresh.csv`, `data/project_research_state_summary.csv`, and `data/project_research_state_next_steps.csv`.
- The project research state refresh consolidates current stock/ETF and crypto research state so the next research/reporting direction can be chosen cleanly. Current saved interpretation surfaces `qqq_100_trend_gate` as the stock/ETF research lead, keeps `codex_qqq_adaptive_trend_exposure` as an ambitious alternative, marks `qqq_150_trend_gate` as the rejected high-drawdown QQQ reference, and preserves `crypto_equal_weight_ex_highest_vol_2` as the manual-review-only crypto lead. It does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.
- `python bot.py --show-current-research-state` is a concise terminal display helper. It reads saved project research state, shows the QQQ stock/ETF lead context and crypto lead context, does not refresh market data, does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.
- `python bot.py --project-research-state-quality-report` writes `data/project_research_state_quality_report.csv`. It reads saved project research state only, checks freshness, required fields, and false approval flags, and reports warning/blocker rows for stale, missing, or non-false approval states. It does not approve scheduling or execution.
- `python bot.py --stock-etf-paper-execution-readiness-report` writes `data/stock_etf_paper_execution_readiness_report.csv`. It is a saved-data/static-source discussion checkpoint for whether the current stock/ETF research lead is ready even to discuss a future manually reviewed Alpaca paper-execution design. Current expected status is conservative: `qqq_100_trend_gate` is research-only, the adaptive QQQ candidate is an ambitious alternative rather than an execution route, the higher-drawdown QQQ leverage reference remains rejected, and preview, execution eligibility, kill-switch, portfolio-risk, crypto-out-of-scope, and scheduling boundaries still block or require manual review. It does not read credentials, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve paper execution.
- `python bot.py --alpaca-paper-readiness-report` writes `data/alpaca_paper_readiness_report.csv`. Default mode is static/no-network and checks safe paper prerequisites without reading config contents, calling Alpaca, reading positions, creating orders, writing SQLite `trade_log`, sending alerts, scheduling anything, or approving execution. `--confirm-readonly-alpaca-check` is implemented for a later explicit read-only Alpaca paper account/status check only; it must not be treated as a smoke test or execution approval.
- `python bot.py --alpaca-connectivity-diagnostics` writes `data/alpaca_connectivity_diagnostics.csv`, `data/alpaca_connectivity_diagnostics_summary.csv`, and `data/alpaca_connectivity_diagnostics_blockers.csv`; `python bot.py --show-alpaca-connectivity-diagnostics` displays the saved summary only. The diagnostics use DNS and raw TCP 443 socket checks for Alpaca API/public hosts and general HTTPS control hosts. They document the current VPS/laptop distinction where the VPS times out to `paper-api.alpaca.markets:443` and `api.alpaca.markets:443` while the laptop and normal HTTPS hosts work. They do not load config, use credentials, call authenticated Alpaca APIs, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve execution.
- `python bot.py --paper-order-smoke-test-readiness-pack` writes `data/paper_order_smoke_test_readiness_pack.csv`. It is a saved-data/static readiness pack for deciding whether one tiny manually confirmed Alpaca paper-order smoke test can even be discussed. It may record a future manual-review-only template such as AAPL buy 1, but it does not print a pasteable order command, call Alpaca, read positions, load config contents, create orders, write SQLite `trade_log`, send alerts, schedule anything, connect a strategy to execution, or approve order execution.
- `python bot.py --paper-order-smoke-test-live-preflight --ticker AAPL --side buy --quantity 1` writes `data/paper_order_smoke_test_live_preflight.csv`. Default mode is non-confirmed and does not call Alpaca; it validates the proposed manual-review-only ticker/side/quantity and summarises saved readiness context. Confirmed read-only mode is implemented behind `--confirm-readonly-alpaca-check` for account, market clock, asset, and open-order status checks only, and must still not create, submit, cancel, replace, or preview executable orders.
- `python bot.py --paper-order-smoke-test-postcheck --ticker AAPL --side buy --quantity 1` writes `data/paper_order_smoke_test_postcheck.csv`. Default mode is saved-data/static only and does not call Alpaca. Confirmed read-only mode is implemented behind `--confirm-readonly-alpaca-check` to summarise recent orders, open orders, account block flags, and ticker position direction/quantity without printing sensitive identifiers. It never creates follow-up orders or approves execution.
- `python bot.py --future-refresh-cron-readiness-pack` writes `data/future_refresh_cron_readiness_pack.csv`. It is a static/docs/report-only pack for tomorrow's separate manual review of a possible safe refresh/reporting Hermes cron. It does not create, edit, trigger, delete, enable, or schedule cron jobs, and it does not approve scheduling or execution.
- `docs/PAPER_ORDER_SMOKE_TEST_RUNBOOK.md` is the Monday manual paper-order smoke-test runbook. `python bot.py --paper-order-smoke-test-runbook-check` writes `data/paper_order_smoke_test_runbook_check.csv` and verifies the runbook remains static, manual-review-only, and false for smoke-test order, execution, scheduling, and follow-up order approval.
- `python bot.py --paper-smoke-test-kill-switch-diagnosis` writes `data/paper_smoke_test_kill_switch_diagnosis.csv`, `data/paper_smoke_test_kill_switch_diagnosis_summary.csv`, `data/paper_smoke_test_kill_switch_diagnosis_blockers.csv`, and `data/paper_smoke_test_kill_switch_diagnosis_recommendations.csv`; `python bot.py --show-paper-smoke-test-kill-switch-diagnosis` reads the saved summary only. It diagnoses why the manual AAPL paper smoke-test attempt was blocked by the kill-switch gate, separates connectivity-smoke-test blockers from broader strategy-execution blockers, preserves that no order was submitted, and does not weaken `--paper-order-test`, call Alpaca, read positions, write SQLite `trade_log`, send alerts, change config, schedule anything, or approve smoke-test execution.
- The manual `--paper-order-test` path now has a narrow connectivity-only smoke-test gate for the exact `AAPL buy 1 --confirm-paper-order` template. It can allow only that one manual paper smoke test through broader strategy-execution blockers after saved/read-only live preflight is ready, market status is open, Alpaca paper mode and credentials are present, no open AAPL order exists, and no recent matching AAPL buy 1 order exists. It writes `data/paper_order_smoke_test_gate_report.csv`, `data/paper_order_smoke_test_gate_summary.csv`, and `data/paper_order_smoke_test_gate_blockers.csv` when the manual path is run. Normal bot, slow-SMA paper execution, QQQ100 preview/action-preview, strategy execution, scheduling, live trading, config defaults, and follow-up orders remain unapproved and unchanged.
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

Current promoted review and portfolio risk policy both show no execution approval. AAPL and SPY remain blocked by strategy disagreement; MSFT remains no-action/unanimous flat.

## Staged Paper Monitoring Direction

The next operational direction is to improve paper monitoring without approving automated order execution.

A. Expand ticker universe in research/preview only.
B. Add or improve ticker-universe validation/reporting.
C. Add more frequent market monitoring as preview/display/report only.
D. Add loop/cron support only after single-run commands are stable.
E. Add lockfile/no-overlap protection before any repeated run.
F. Add portfolio risk controls before expanded paper execution.
G. Keep paper execution separate, explicit, confirmation-gated, and manually reviewed.
H. Do not treat monitoring signals as execution approval.

More frequent price checks do not mean more frequent trades. Daily strategies should not overtrade intraday noise unless a separate intraday strategy is researched and validated. For now, frequent monitoring should mean observe/report/preview, not submit orders. Any execution-capable loop or scheduled order workflow remains not approved.

More tickers should start with liquid U.S. stocks and ETFs only. Add universe expansion to research/preview first. Add liquidity, price, and duplicate validation before any execution review. More tickers require portfolio risk limits, max open positions, max notional exposure, and concentration checks before paper execution.

Ticker universe readiness reporting:

- `python bot.py --ticker-universe-readiness-report` writes `data/ticker_universe_readiness_report.csv`.
- `python bot.py --market-monitor-snapshot` writes `data/market_monitor_snapshot.csv`.
- `python bot.py --show-market-monitor` reads `data/market_monitor_snapshot.csv` only and displays a compact terminal summary without refreshing market data.
- `python bot.py --market-monitor-quality-report` reads `data/market_monitor_snapshot.csv` only and writes `data/market_monitor_quality_report.csv`.
- `python bot.py --refresh-market-monitor` runs the safe monitoring chain in order: ticker universe readiness, market monitor snapshot, saved display, and quality report.
- `python bot.py --market-monitor-scheduling-readiness-report` writes `data/market_monitor_scheduling_readiness_report.csv` for future manual scheduling review only.
- `python bot.py --monitor-lockfile-readiness-report` writes `data/monitor_lockfile_readiness_report.csv` for future no-overlap/lockfile design readiness only.
- It uses a fixed research/report-only candidate universe of broad ETFs, sector ETFs, and large liquid U.S. stocks; it does not read `config.json`.
- It labels obvious ETFs/stocks, validates duplicate tickers, includes conservative readiness gates, and marks `execution_approved=False` and `paper_execution_approved=False` for all rows.
- It may attempt recent daily yfinance data enrichment for latest close/volume, but market-data failures are captured in report rows instead of approving or blocking execution.
- The market monitor snapshot reuses the fixed candidate universe and fetches recent yfinance intraday bars for observation only. It records latest timestamp, close, previous close, intraday change, volume, data status, and any per-ticker errors.
- The saved display command does not call yfinance, Alpaca, paper positions, SQLite `trade_log`, or Discord alerts; it only reads the saved CSV and warns if execution approval flags are not false.
- The saved quality report checks required columns, row count, duplicates, missing prices/timestamps, stale timestamps, data errors, abnormal intraday moves, and monitoring/research/preview/execution approval flags. It does not refresh yfinance data.
- The refresh command is a convenience wrapper for the same report/display paths. It prints a step summary, stops conservatively on failure, and does not connect monitoring outputs to strategies or execution.
- The scheduling readiness report now audits the VPS-safe monitoring set: `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research`. It checks lockfile coverage, config presence without reading contents, saved promoted/defensive output presence, generated-output ignore policy, execution-capable command exclusion, and false scheduling/execution approval flags. It does not create Windows Task Scheduler tasks, add cron/loop execution, approve scheduling, or approve execution.
- Hermes cron preferred for future monitoring scheduling if configured. No refresh cron job or execution scheduling is currently approved or created beyond the existing status-only job. Use Hermes cron for safe monitoring/reporting only; not for execution. Windows Task Scheduler remains an alternative, not the default assumption, and should be limited to keeping the Hermes gateway running.
- Do not paste config/API keys/webhooks/account IDs into Hermes prompts. Initial cron candidate should probably be a status/checkpoint job before refresh jobs. The initial candidate command set is limited to `--vps-monitoring-status`, `--market-monitor-scheduling-readiness-report`, `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research`.
- Future Hermes cron jobs should run from `C:\dev\paper-trading-bot`, use `.venv\Scripts\python.exe`, include a repo-safety check, use concise output capture, avoid recursive cron creation, and use restricted `enabled_toolsets` where Hermes supports them.
- Refresh jobs should remain protected by lockfile/no-overlap. A stale lock requires manual review. Lockfile protection does not make execution-capable commands schedulable. Scheduling cadence is a separate future decision, and a future manual review must approve exact cadence, exact command list, enabled toolsets, output destination, and failure behaviour before any Hermes cron job is created.
- `docs/HERMES_CRON_JOB_DESIGN.md` records the current verified `paper-bot-vps-status-check` status cron, including job ID `345188fbb60c`, daily 10:10am UK local time cadence, cron expression `10 10 * * *`, Telegram delivery, script-only / no-agent mode, repo path, command sequence, and healthy output. It confirms the job does not run refresh commands and does not approve execution. Verify this checkpoint with `python scripts\verify_hermes_cron_job_design.py`.
- Before any future scheduling review, run `python scripts\verify_repo_safety.py`, run `python scripts\verify_hermes_cron_readiness.py`, run `python bot.py --market-monitor-scheduling-readiness-report`, and confirm generated CSV/cache files remain ignored.
- Stop if any scheduled candidate tries to load `config.json`, call Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, create orders, or approve execution.
- No repeated market-monitor refresh should be scheduled before no-overlap/lockfile protection exists. A future lockfile may prevent two safe refresh/report/display commands from running at once, but stale lock handling must be conservative and the lock must not contain secrets, account IDs, config contents, order IDs, webhook URLs, API keys, generated trading data, positions, or report contents.
- The monitor lockfile readiness report, promoted review refresh, and defensive research refresh are the only commands protected by the monitor lockfile helper. All three use transient no-overlap locks that do not approve scheduling or execution.
- `python scripts\verify_monitor_lockfile_contract.py` is a pure no-network contract verifier for future lock helper requirements. It does not implement locking, create lockfiles, schedule anything, or run bot commands.
- `python scripts\verify_monitor_lockfile_helper.py` verifies the helper in `trading_bot/safety/monitor_lockfile.py`, including temp-directory lock acquire/release cleanup, fresh-lock blocking, malformed-lock blocking, and stale-lock manual review.
- `python scripts\verify_monitor_lockfile_integration_readiness.py` is a static checkpoint for the next manual-review stage. It verifies exactly `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research` are lock-wrapped, `bot.py` is not using the helper directly, no other command is lock-wrapped, and future safe report/display/monitor refresh commands remain manual-review only.
- `python scripts\verify_monitor_lockfile_final_state.py` is the final static checkpoint for the current lockfile handoff. It verifies the exact three-command lock boundary, false execution/scheduling approval flags, stale-lock manual review, blocked execution commands, and VPS handoff documentation.
- VPS safe manual monitoring commands are report/refresh/display only. Use `git pull`, `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, and `.venv\Scripts\python.exe scripts\verify_monitor_lockfile_final_state.py` before manual review commands such as `.venv\Scripts\python.exe bot.py --monitor-lockfile-readiness-report`, `.venv\Scripts\python.exe bot.py --refresh-promoted-review`, and `.venv\Scripts\python.exe bot.py --refresh-defensive-research`.
- `python scripts\verify_vps_monitoring_prerequisites.py` is a static checkpoint for the first manual VPS monitoring test. It distinguishes environment/dependency readiness, `config_missing_for_readonly_promoted_review`, `missing_saved_research_inputs`, actual safety failures, and safe next manual VPS steps. It does not read or create `config.json`, install packages, run bot commands, or approve scheduling/execution.
- `python bot.py --vps-monitoring-status` is the VPS-safe terminal monitoring route. It is report/display-only and summarizes repo safety reminders, lockfile state, config presence without reading contents, saved research prerequisite presence, generated-output ignore expectations, latest saved promoted review step/decision counts when present, high-risk/manual-only boundaries in prose, and next safe manual report actions. It avoids printing pasteable high-risk command lines. It does not call Alpaca, yfinance, Discord, SQLite `trade_log`, read positions, create orders, schedule anything, or approve execution.
- `python bot.py --vps-monitoring-status` now labels key saved outputs by modification-time freshness only: `fresh`, `warning_stale`, `stale`, or `missing`. Freshness/staleness labels are monitoring diagnostics only, and missing/stale saved outputs are prerequisites/status issues, not trading approval.
- `python bot.py --vps-daily-monitoring-summary` is a concise terminal-only daily report for Telegram/manual checks. It summarizes safety reminders, lock-wrapped safe commands, promoted decision-state counts, defensive refresh step counts, saved-output freshness labels, false approval flags, final status of `healthy_monitoring_state`, `monitoring_warning`, or `monitoring_stale_or_missing_inputs`, and action fields `action_required`, `action_reason`, and `suggested_manual_action`. It does not refresh data, call Alpaca/yfinance/Discord, write SQLite `trade_log`, read config contents, create generated files, schedule anything, or approve execution.
- The current daily Hermes status cron exists as `paper-bot-vps-status-check` with job ID `345188fbb60c`. It runs daily at 10:10am UK local time with cron expression `10 10 * * *`, delivers to Telegram, uses script-only / no-agent mode, runs from `C:\dev\paper-trading-bot`, and executes `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, `.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py`, and `.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary`. Verified output is repo_safety PASS, hermes_cron_readiness PASS, vps_daily_monitoring_summary PASS, final_monitoring_status `healthy_monitoring_state`, action_required `no_action_required`, execution_approved false, scheduling_approved false, and freshness_warnings: none. This status cron does not run refresh commands, trade, approve scheduling beyond this one status job, approve execution, pull/commit/push code, or inspect/print config contents, secrets, logs, databases, or full generated CSV contents.
- No promoted-review refresh cron job is currently created. `docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` documents a possible future promoted-review refresh cron as a separate manual-review item, and `python scripts\verify_hermes_promoted_review_refresh_cron_design.py` verifies that it remains future-only and non-execution.
- `docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` is the canonical future-only promoted-review refresh cron design. `docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` is a legacy pointer only.
- `docs/HERMES_CRON_MONITORING_RUNBOOK.md` explains how to interpret Telegram/status output from `paper-bot-vps-status-check`, including `healthy_monitoring_state`, `monitoring_warning`, `monitoring_stale_or_missing_inputs`, and failed-step responses. Verify it with `python scripts\verify_hermes_cron_monitoring_runbook.py`.
- Terminal monitoring is the chosen VPS route for now. No dashboard, web server, public hosting, open ports, scheduling, or execution controls are added.
- `python bot.py --build-research-dashboard` remains a static saved-CSV dashboard builder only. When saved project research state files exist, it adds a minimal Project Research State panel that consolidates current stock/ETF and crypto research state. It does not approve preview promotion, does not approve execution, and does not create a dashboard server or background service.
- Generated CSVs/charts/logs/databases/secrets/config must not be committed or pasted. Generated outputs remain ignored and stale lockfiles require manual review, not automatic deletion.
- Lockfile planning applies only to report/preview/display/monitor refresh commands. Execution-capable commands must never be scheduled and must not be treated as safe merely because a lockfile exists. A lockfile does not approve scheduling, execution, or paper orders.
- It does not call Alpaca, read paper positions, create/cancel/submit orders, write SQLite `trade_log`, send Discord alerts, change strategy rules, or approve execution.
- More tickers and more frequent price checks do not mean more trades. Frequent monitoring should start as preview/display/report only, and daily strategies should not become intraday trading strategies without separate research.

Strategy improvement lab:

- `python bot.py --strategy-improvement-lab` runs a fixed research-only daily ETF lab for more growth-aware allocation variants. It writes `data/strategy_improvement_lab_results.csv`, `data/strategy_improvement_lab_trades.csv`, `data/strategy_improvement_lab_equity_curve.csv`, `data/strategy_improvement_lab_summary.csv`, and `data/strategy_improvement_lab_iteration_log.csv`.
- `python bot.py --show-strategy-improvement-lab` reads the saved summary CSV only. It does not refresh yfinance data.
- The lab intentionally explores whether the defensive ETF stack has too much cash drag, using fixed monthly rebalance variants only: monthly ETF rotation reference, balanced dual momentum with defensive sleeve, breadth-aware risk-on rotation, growth-biased rotation with crash gate, cost-aware growth-biased rebalance refinement, partial defensive-sleeve growth-biased refinement, factor/style absolute-gate rotation, sector 52-week-high continuation, and an ambitious fixed multi-sleeve growth allocator.
- `growth_biased_rotation_cost_aware_rebalance` preserves the original `growth_biased_rotation_crash_gate` and adds only a fixed 5 percentage-point rebalance threshold plus a near-top holding preference. It is a narrow research hypothesis for cost sensitivity, not a promotion or execution step.
- `growth_biased_rotation_partial_defensive_sleeve` also preserves the original growth-biased crash-gate strategy. It adds fixed defensive exposure only when breadth/regime weakens, targeting split stability and drawdown behaviour while trying to preserve most of the growth-biased return profile.
- The remaining fixed growth-biased batch tested re-entry confirmation, regime recovery, and fixed looser/stricter breadth gates. `growth_biased_rotation_breadth_stricter_gate` is now the active research lead because it improved CAGR, Sharpe, and Calmar versus the previous `growth_biased_rotation_crash_gate` baseline without worsening max drawdown, cash drag, cost sensitivity, or split sensitivity. Cost-aware rebalance, partial defensive sleeve, re-entry, recovery, and the looser breadth gate remain tested/rejected or secondary research history.
- `python bot.py --strategy-improvement-robustness` writes `data/strategy_improvement_robustness_report.csv`, `data/strategy_improvement_cost_stress_report.csv`, `data/strategy_improvement_drawdown_report.csv`, and `data/strategy_improvement_candidate_comparison.csv`. It compares all strategy-improvement candidates across fixed 60/40, 70/30, and 80/20 chronological splits, fixed low/default/high one-way cost assumptions, drawdown windows, cash drag, and benchmark deltas.
- `python bot.py --show-strategy-improvement-robustness` reads the saved candidate comparison CSV only. It does not refresh yfinance data.
- `python bot.py --strategy-improvement-diagnostics` reads saved strategy-improvement lab/robustness CSVs only and writes `data/strategy_improvement_diagnostics.csv` plus `data/growth_biased_rotation_diagnostics.csv`. It explains why `growth_biased_rotation_crash_gate` is split-sensitive by checking split decay, benchmark-relative gaps, cost stress, drawdown window/recovery context, cash drag, and active-leader status.
- `python bot.py --show-strategy-improvement-diagnostics` reads the saved growth-biased diagnostics CSV only. It does not refresh data.
- `python bot.py --growth-biased-stricter-validation` reads saved strategy-improvement outputs only and writes stricter-gate validation CSVs for deeper split validation, cost-stress review, drawdown-period review, benchmark comparison, and a promotion checkpoint. `python bot.py --show-growth-biased-stricter-validation` displays those saved validation CSVs only.
- `python bot.py --growth-biased-stricter-promotion-readiness` reads saved stricter-gate validation outputs only and writes `data/growth_biased_stricter_promotion_readiness.csv` plus `data/growth_biased_stricter_promotion_blockers.csv`. It explains benchmark, split, cost, drawdown, saved-output, and preview-readiness blockers for the active research lead. `python bot.py --show-growth-biased-stricter-promotion-readiness` displays the saved blocker report only.
- `python bot.py --growth-biased-stricter-manual-review-pack` reads saved stricter-gate validation and strategy-improvement outputs only and writes `data/growth_biased_stricter_manual_review_pack.csv` plus `data/growth_biased_stricter_regime_context.csv`. It assembles manual-review rows for active-lead status, SPY lag, improvement versus the previous crash-gate lead, drawdown, split validation, cost sensitivity, cash drag, turnover/trade count, and preview-discussion status. `python bot.py --show-growth-biased-stricter-manual-review-pack` displays the saved manual review pack only.
- `python bot.py --growth-biased-stricter-threshold-neighbourhood` runs a small fixed research-only threshold robustness check for the active stricter gate. It tests breadth gates at 40%, 45%, 50%, 55%, and 60%, writes `data/growth_biased_stricter_threshold_neighbourhood.csv` plus `data/growth_biased_stricter_threshold_neighbourhood_summary.csv`, and classifies whether the improvement is a credible nearby-threshold cluster or a threshold-sensitive result. `python bot.py --show-growth-biased-stricter-threshold-neighbourhood` displays the saved threshold report only.
- `python bot.py --growth-biased-stricter-cost-turnover-stress` reads the saved threshold-neighbourhood output only and writes `data/growth_biased_stricter_cost_turnover_stress.csv` plus `data/growth_biased_stricter_cost_turnover_stress_summary.csv`. It stress-tests the current 55% stricter-gate cluster under fixed 0, 5, 10, 25, 50, and 100 bps one-way cost assumptions and reports whether turnover/cost decay needs manual review. `python bot.py --show-growth-biased-stricter-cost-turnover-stress` displays the saved cost/turnover report only.
- `python bot.py --growth-biased-stricter-persistence-filter` runs fixed research-only persistence variants around the 55% stricter gate and writes `data/growth_biased_stricter_persistence_filter.csv` plus `data/growth_biased_stricter_persistence_filter_summary.csv`. It tests 2-month and 3-month minimum holds, a 5 percentage-point momentum-gap rule, near-top-2 holding, a combined persistence rule, and one Codex-designed candidate: `codex_ambitious_concentrated_growth_persistence`. `python bot.py --show-growth-biased-stricter-persistence-filter` displays the saved persistence report only.
- `python bot.py --codex-ambitious-validation` reads saved persistence-filter outputs only and writes `data/codex_ambitious_validation.csv`, `data/codex_ambitious_validation_summary.csv`, `data/codex_ambitious_validation_splits.csv`, `data/codex_ambitious_validation_costs.csv`, and `data/codex_ambitious_validation_drawdowns.csv`. It validates `codex_ambitious_concentrated_growth_persistence` for possible active research-lead discussion. `python bot.py --show-codex-ambitious-validation` displays the saved validation only.
- `python bot.py --codex-ambitious-split-drawdown-validation` runs the focused research-only split and drawdown-window checkpoint for `codex_ambitious_concentrated_growth_persistence` and writes `data/codex_ambitious_split_drawdown_validation.csv`, `data/codex_ambitious_split_validation.csv`, `data/codex_ambitious_drawdown_windows.csv`, and `data/codex_ambitious_lead_change_checkpoint.csv`. It checks fixed `split_60_40`, `split_70_30`, and `split_80_20` out-of-sample windows plus the worst drawdown window against SPY and the stricter-gate lead. `python bot.py --show-codex-ambitious-split-drawdown-validation` displays the saved checkpoint only.
- `python bot.py --codex-ambitious-lead-decision` reads saved Codex ambitious validation, split/drawdown, persistence, threshold, cost/turnover, and manual-review outputs where available and writes `data/codex_ambitious_lead_decision.csv`, `data/codex_ambitious_lead_decision_summary.csv`, and `data/codex_ambitious_lead_decision_evidence.csv`. It decides whether `codex_ambitious_concentrated_growth_persistence` should become the active research lead as a research label only, with cost review kept explicit when needed. `python bot.py --show-codex-ambitious-lead-decision` displays the saved decision only.
- The diagnostics layer does not add another strategy. It outputs suggestion-only next fixed hypotheses to guide a later task without random tuning.
- Diagnostics now compare the previous growth-biased baseline directly with `growth_biased_rotation_cost_aware_rebalance`, `growth_biased_rotation_partial_defensive_sleeve`, `growth_biased_rotation_reentry_filter`, `growth_biased_rotation_regime_recovery_filter`, and the fixed breadth-gate variants. The next work is validation/checkpointing for `growth_biased_rotation_breadth_stricter_gate`, not more random variants.
- The stricter-gate validation, promotion-readiness, manual-review-pack, threshold-neighbourhood, cost/turnover stress, persistence-filter, Codex ambitious validation, Codex ambitious split/drawdown, and Codex ambitious lead-decision checkpoints are research-only. They can support future preview-candidate discussion only after separate manual review, but they do not approve execution, paper execution, preview promotion, promoted execution, scheduling, or cron.
- Promising labels such as `promising_growth_candidate` are future research labels only. They do not approve orders, paper execution, scheduling, cron, shorting, leverage, margin, or strategy-to-execution wiring.
- `python scripts\verify_strategy_improvement_lab.py`, `python scripts\verify_strategy_improvement_robustness.py`, and `python scripts\verify_strategy_improvement_diagnostics.py` check command registration, generated-output ignore policy, fixed variants, fixed split/cost assumptions, saved diagnostics, false execution approval flags, saved display behavior, and absence of Alpaca/order/SQLite `trade_log`/Discord/config/scheduling paths.

## Recommended Next Steps

A. Keep the current research state stable and avoid adding more strategy complexity.

B. Expand liquid U.S. stock/ETF monitoring only through research/preview and ticker-universe validation first.

C. Improve reporting/charting around drawdown periods if useful.

D. Consider small refactors only after focused verifiers exist.

E. Only later consider paper execution for one conservative strategy after preview, risk checks, consensus/decision review, portfolio risk policy review, and explicit confirmation.

F. Crypto: keep monitoring BTC and ETH; do not add execution.

G. If adding new crypto symbols later, add one at a time and label each as research-only.

H. Run repo safety before commits/pushes and deployment readiness before any future VPS handoff.

I. Do not schedule execution-capable commands. Use `docs/VPS_SETUP_CHECKLIST.md` only as future setup guidance.

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
python bot.py --refresh-promoted-review
python bot.py --preview-promoted-strategies
python bot.py --preview-promoted-actions
python bot.py --show-promoted-actions
python bot.py --promoted-risk-preview
python bot.py --show-promoted-risk
python bot.py --promoted-consensus-preview
python bot.py --promoted-decision-preview
python bot.py --show-promoted-decision
```

Workflow, deployment, and risk policy checks:

```text
python scripts\verify_repo_safety.py
python scripts\verify_monitor_lockfile_contract.py
python scripts\verify_monitor_lockfile_helper.py
python scripts\verify_monitor_lockfile_integration_readiness.py
python scripts\verify_refresh_promoted_review_lock_readiness.py
python scripts\verify_refresh_defensive_research_lock_readiness.py
python scripts\verify_monitor_lockfile_final_state.py
python scripts\verify_vps_monitoring_prerequisites.py
python scripts\verify_vps_monitoring_status.py
python scripts\verify_vps_monitoring_freshness.py
python scripts\verify_vps_daily_monitoring_summary.py
python scripts\verify_hermes_promoted_review_refresh_cron_design.py
python scripts\verify_hermes_cron_monitoring_runbook.py
python scripts\verify_report_only_import_safety.py
python scripts\verify_market_monitor_scheduling_readiness.py
python bot.py --ticker-universe-readiness-report
python bot.py --market-monitor-snapshot
python bot.py --show-market-monitor
python bot.py --market-monitor-quality-report
python bot.py --refresh-market-monitor
python bot.py --market-monitor-scheduling-readiness-report
python bot.py --monitor-lockfile-readiness-report
python bot.py --deployment-readiness-report
python bot.py --vps-operations-readiness-report
python bot.py --vps-monitoring-status
python bot.py --vps-daily-monitoring-summary
python bot.py --portfolio-risk-policy-report
python bot.py --show-portfolio-risk-policy
```

Crypto research refresh:

```text
python bot.py --crypto-research-preview
python bot.py --crypto-universe-readiness-report
python bot.py --show-crypto-universe-readiness-report
python bot.py --expanded-crypto-strategy-lab
python bot.py --show-expanded-crypto-strategy-lab
python bot.py --expanded-crypto-robustness-report
python bot.py --show-expanded-crypto-robustness-report
python bot.py --crypto-equal-weight-crash-gate
python bot.py --show-crypto-equal-weight-crash-gate
python bot.py --crypto-equal-weight-volatility-scaling
python bot.py --show-crypto-equal-weight-volatility-scaling
python bot.py --crypto-equal-weight-capped-risk-report
python bot.py --show-crypto-equal-weight-capped-risk-report
python bot.py --expanded-crypto-lead-decision
python bot.py --show-expanded-crypto-lead-decision
python bot.py --crypto-strategy-lab
python bot.py --crypto-strategy-report
python bot.py --crypto-strategy-decision-report
python bot.py --crypto-cost-stress-report
python bot.py --crypto-robustness-report
python bot.py --crypto-period-diagnostics
python bot.py --crypto-research-state-report
```

Expanded crypto robustness report challenges whether static equal-weight eligible crypto is robust or hindsight-biased. `python bot.py --expanded-crypto-robustness-report` writes `data/expanded_crypto_robustness_report.csv`, `data/expanded_crypto_robustness_summary.csv`, `data/expanded_crypto_robustness_splits.csv`, `data/expanded_crypto_robustness_costs.csv`, `data/expanded_crypto_robustness_drawdowns.csv`, `data/expanded_crypto_asset_contribution.csv`, and `data/expanded_crypto_equal_weight_reality_check.csv`. It checks inception-aware equal weight, outlier exclusions, cost stress, splits, drawdown context, and asset contribution estimates while keeping `POL-USD` and `MATIC-USD` transition-blocked. `python bot.py --show-expanded-crypto-robustness-report` reads saved CSVs only. This is research/report-only, does not approve crypto execution, and does not connect crypto to Alpaca or paper orders.

Crypto equal-weight crash-gate report tests whether the robust equal-weight eligible-crypto benchmark can retain meaningful return while reducing catastrophic drawdown. `python bot.py --crypto-equal-weight-crash-gate` writes `data/crypto_equal_weight_crash_gate.csv`, `data/crypto_equal_weight_crash_gate_summary.csv`, `data/crypto_equal_weight_crash_gate_trades.csv`, `data/crypto_equal_weight_crash_gate_equity_curves.csv`, `data/crypto_equal_weight_crash_gate_costs.csv`, `data/crypto_equal_weight_crash_gate_splits.csv`, and `data/crypto_equal_weight_crash_gate_drawdowns.csv`. It compares fixed trend/crash-gate variants, inception-aware equal weight, static equal weight, the existing planned and Codex crypto candidates, BTC/ETH benchmarks, BTC/ETH 50/50, and cash while keeping `POL-USD` and `MATIC-USD` transition-blocked. `python bot.py --show-crypto-equal-weight-crash-gate` reads saved CSVs only. This is research/report-only, does not approve crypto execution, and does not connect crypto to Alpaca or paper orders.

Crypto equal-weight volatility-scaling report follows the hard crash-gate return-drag result by testing partial volatility/drawdown exposure scaling instead of binary cash exits. `python bot.py --crypto-equal-weight-volatility-scaling` writes `data/crypto_equal_weight_volatility_scaling.csv`, `data/crypto_equal_weight_volatility_scaling_summary.csv`, `data/crypto_equal_weight_volatility_scaling_trades.csv`, `data/crypto_equal_weight_volatility_scaling_equity_curves.csv`, `data/crypto_equal_weight_volatility_scaling_costs.csv`, `data/crypto_equal_weight_volatility_scaling_splits.csv`, and `data/crypto_equal_weight_volatility_scaling_drawdowns.csv`. It tests fixed volatility, drawdown, and combined scalers plus one Codex-designed fixed-rule risk-control idea, `codex_ambitious_crypto_core_alt_volatility_throttle`, while comparing static equal weight, inception-aware equal weight, existing crypto candidates, BTC/ETH benchmarks, BTC/ETH 50/50, and cash. `python bot.py --show-crypto-equal-weight-volatility-scaling` reads saved CSVs only. This is research/report-only, does not approve crypto execution, and does not connect crypto to Alpaca or paper orders.

Crypto equal-weight capped-risk report tests capped/equal-risk crypto allocation and outlier-dependence diagnostics while keeping broad crypto exposure. `python bot.py --crypto-equal-weight-capped-risk-report` writes `data/crypto_equal_weight_capped_risk_report.csv`, `data/crypto_equal_weight_capped_risk_summary.csv`, `data/crypto_equal_weight_capped_risk_trades.csv`, `data/crypto_equal_weight_capped_risk_equity_curves.csv`, `data/crypto_equal_weight_capped_risk_costs.csv`, `data/crypto_equal_weight_capped_risk_splits.csv`, `data/crypto_equal_weight_capped_risk_drawdowns.csv`, and `data/crypto_equal_weight_capped_risk_contributions.csv`. It tests fixed capped equal-weight, highest-volatility exclusion, top-contributor-pair exclusion, inverse-volatility, and equal-risk proxy variants while preserving false execution approval. `python bot.py --show-crypto-equal-weight-capped-risk-report` reads saved CSVs only. This is research/report-only, does not approve crypto execution, and does not connect crypto to Alpaca or paper orders.

Expanded crypto lead decision consolidates the crypto research branch into the current crypto research lead as a research label only. `python bot.py --expanded-crypto-lead-decision` reads saved crypto universe, expanded strategy lab, equal-weight robustness, crash-gate, volatility-scaling, capped-risk, split, cost, drawdown, and contribution outputs where available, then writes `data/expanded_crypto_lead_decision.csv`, `data/expanded_crypto_lead_decision_summary.csv`, and `data/expanded_crypto_lead_decision_evidence.csv`. `python bot.py --show-expanded-crypto-lead-decision` reads saved CSVs only. Any lead remains high-drawdown/manual-review-only; this does not approve crypto execution and does not connect crypto to Alpaca or paper orders.

Crypto signal and monitor refresh:

```text
python bot.py --preview-crypto-signals
python bot.py --show-crypto-monitor
```

Safe focused verification convention:

- Routine verifier blocks only need "passed" unless a failure, traceback, or new warning appears.
- For docs-only changes, runtime verification is not required.
- For Python changes, run the smallest focused verifier first, then broader baseline checks only if needed.
