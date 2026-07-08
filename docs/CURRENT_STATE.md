# Current State

This checkpoint is documentation only. It summarizes the project state for future Codex or ChatGPT sessions without changing code, configs, strategy logic, CSV outputs, or execution behavior.

For the ordered paper-live implementation path, see `docs/PAPER_LIVE_CHECKLIST.md`.

## Safety Boundary

- This project is paper-only. Live trading is out of scope.
- `dry_run` defaults to `true`.
- `alpaca.paper` must remain `true`; the bot refuses non-paper Alpaca mode.
- `config.json`, API keys, and Discord webhook URLs stay private.
- Normal `python bot.py` is monitoring-only. It may record intended actions with `order_status=monitor_only`, but it must not submit orders or mutate position state.
- Research, backtest, report, preview, and display commands do not approve execution.
- Execution-related commands are separate high-risk paths and must stay behind explicit confirmation and review.
- `paper_kill_switch_enabled` is a real config/env field with a safe default of `false`; it does not make the normal bot order-capable.
- Manual paper sells now have an oversell guard when shorting is disabled.
- `python scripts\verify_repo_safety.py` should be run before commits and pushes.
- Deployment readiness and VPS checklist docs are audits/planning aids only. They do not deploy, schedule, or approve execution.
- Portfolio risk policy reporting is not runtime enforcement and does not approve execution.

## Latest VPS Monitoring Checkpoint

- VPS pulled and verified commit `08ca16d Add high-growth sleeve concentration review`.
- VPS repo status was clean on `main...origin/main`.
- The VPS high-growth/component/concentration chain was rebuilt and working.
- VPS daily monitoring summary reported `final_status=healthy_monitoring_state`, `action_required=no_action_required`, all monitored saved outputs fresh, `execution_approved=False`, and `scheduling_approved=False`.
- This checkpoint confirms monitoring/report health only. It does not approve execution, crypto execution, scheduling, paper orders, live trading, or strategy-to-execution wiring.

## Volatility Execution-Design Checkpoint

- `python bot.py --vol-targeted-growth-execution-approval-request-readiness` can report that the closed checklist blockers are ready for a separate human approval question, but does not request or record execution approval.
- `python bot.py --vol-targeted-growth-execution-design-approval-wording` defines the narrow phrase for design-only approval.
- `python bot.py --vol-targeted-growth-execution-design-approval-record` records approval to continue designing the next non-submitting execution-ticket layer only.
- The design record does not populate order values, create an executable ticket, call Alpaca, submit orders, approve paper execution, approve live trading, or approve scheduling.
- `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-design` creates the first post-approval design artifact for a future executable-ticket review, but it keeps all order values blank and keeps `executable_ticket_created=False`.
- `python bot.py --vol-targeted-growth-ticket-values-approval-readiness`, `python bot.py --vol-targeted-growth-ticket-values-approval-wording`, and `python bot.py --vol-targeted-growth-ticket-values-approval-record` create a discussion-only checkpoint for future ticket-value placeholders.
- The ticket-values record can mark `ticket_value_discussion_approved=True`, but it keeps `ticket_values_approved=False`, `order_values_populated=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-ticket-value-placeholders` creates blank non-executable placeholders, and `python bot.py --vol-targeted-growth-ticket-value-quality-gate` verifies those placeholders still have `populated_order_value_count=0`.
- The placeholder quality gate can pass for structure only; it still keeps `ticket_values_approved=False`, `order_values_populated=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-ticket-value-proposal-approval-wording` and `python bot.py --vol-targeted-growth-ticket-value-proposal-approval-record` record permission to draft proposed ticket values in a future review-only report.
- The proposal record can mark `ticket_value_proposal_discussion_approved=True`, but it keeps `proposed_ticket_values_created=False`, `ticket_values_approved=False`, `order_values_populated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-proposed-ticket-values` drafts non-executable proposal labels, and `python bot.py --vol-targeted-growth-proposed-ticket-values-quality-gate` verifies they are not broker-ready order fields.
- The proposed-values quality gate can pass with `proposed_ticket_values_created=True`, but it keeps `ticket_values_approved=False`, `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-executable-ticket-draft-readiness` checks whether the review-only proposed values are clear enough for a later manual non-submitting draft discussion.
- Draft readiness can set `draft_discussion_ready=True`, but it still creates no ticket, no side, no quantity, no order instruction, no broker call, and no execution/scheduling approval.
- `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-draft` creates a saved review draft from proposed labels, and `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate` verifies it still has no executable order fields.
- The draft quality gate can pass with `draft_ticket_created=True`, but it keeps `ticket_values_approved=False`, `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-draft-ticket-value-approval-readiness` checks whether the non-submitting draft is complete enough to ask later for explicit ticket-value approval.
- Approval readiness can set `ticket_value_approval_request_ready=True`, but it keeps `ticket_value_approval_requested=False`, `ticket_value_approval_recorded=False`, `ticket_values_approved=False`, `order_values_populated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-draft-ticket-value-approval-wording` defines the narrow phrase for approving a later review-only draft-value population step.
- `python bot.py --vol-targeted-growth-draft-ticket-value-approval-record` records that narrow approval only. It can set `ticket_value_population_approved=True`, but it keeps `ticket_values_approved=False`, `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-review-only-draft-ticket-values` populates review-only labels for sleeve targets and blocked side/quantity/order fields.
- `python bot.py --vol-targeted-growth-review-only-draft-ticket-values-quality-gate` verifies those labels are still not executable. It can pass with `draft_ticket_values_created=True`, but it keeps `ticket_values_approved=False`, `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-draft-ticket-values-manual-review` reviews the saved draft labels as a report-only checkpoint.
- `python bot.py --vol-targeted-growth-executable-ticket-values-readiness` can set `executable_ticket_values_approval_request_ready=True` when the review-only values and quality gate are clear enough to ask later for explicit approval. It keeps `executable_ticket_values_approval_requested=False`, `executable_ticket_values_approved=False`, `order_values_populated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-executable-ticket-values-approval-wording` defines the narrow phrase for approving a later non-submitting executable ticket-values population step.
- `python bot.py --vol-targeted-growth-executable-ticket-values-approval-record` records that narrow approval only. It can set `executable_ticket_values_approved=True` and `ticket_values_approved=True`, but it keeps `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-values` populates reviewable seed/sleeve context after the approval record, and `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-values-quality-gate` verifies it remains non-submitting. When saved review quantity estimates exist, they are included as review-only estimate context, not broker-ready order quantities. This can set `non_submitting_ticket_values_populated=True`, but it keeps `broker_ready_order_values_populated=False`, `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-non-submitting-executable-ticket-values-manual-review` records saved-output manual review of those values, and `python bot.py --vol-targeted-growth-non-submitting-ticket-creation-readiness` can set `ticket_creation_discussion_ready=True` for a future non-submitting ticket-instance checkpoint. It keeps `ticket_creation_approved=False`, `ticket_instance_created=False`, `executable_ticket_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-checkpoint` records the next saved non-submitting checkpoint after readiness. It can set `ticket_instance_checkpoint_created=True`, but it keeps `ticket_instance_created=False`, `ticket_creation_approved=False`, `broker_ready_order_values_populated=False`, `order_values_populated=False`, `order_instructions_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-sleeve-symbol-mapping` and `python bot.py --vol-targeted-growth-broker-ready-action-proposal` move the active multi-sleeve seed from abstract sleeve labels to review symbols `QQQ`, `MGK`, `IBIT`, and `SGOV`. They keep side, quantity, order type, time-in-force, account, broker order id, order instructions, order submission, execution approval, and scheduling approval absent/false.
- `python bot.py --vol-targeted-growth-calculated-order-values` calculates target-dollar review values from a `$1000` notional across `QQQ`, `MGK`, `IBIT`, and `SGOV`. It keeps share quantities, side, order type, time-in-force, account, broker order id, order instructions, order submission, execution approval, and scheduling approval absent/false because saved prices and final approval are still missing.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-readiness` defines the saved price evidence needed before target-dollar rows could become quantities. It does not fetch prices, call Alpaca, refresh yfinance data, create order instructions, approve execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-approval-wording` and `python bot.py --vol-targeted-growth-saved-price-snapshot-approval-record` define and record approval to discuss the future saved-price snapshot method only. They still keep `saved_price_snapshot_approved=False`, `saved_prices_fetched=False`, `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-runner-design` defines the allowed future saved-price snapshot output fields and stop conditions. It still keeps `saved_price_snapshot_runner_approved=False`, `saved_price_snapshot_run_approved=False`, `saved_prices_fetched=False`, `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-runner-readiness` checks whether saved evidence is complete enough to discuss implementing the future runner. It can set `runner_implementation_discussion_ready=True`, but it keeps `runner_implementation_approved=False`, `saved_price_snapshot_run_approved=False`, `saved_prices_fetched=False`, `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-runner-approval-wording` and `python bot.py --vol-targeted-growth-saved-price-snapshot-runner-approval-record` define and record approval to implement the runner only. They can set `runner_implementation_approved=True` and `saved_price_snapshot_runner_approved=True`, but they keep `saved_price_snapshot_run_approved=False`, `saved_prices_fetched=False`, `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-saved-price-snapshot` is the guarded runner. Without `--confirm-saved-price-snapshot-run`, it writes a blocked report and fetches no prices. A future confirmed run remains price-only and still keeps `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-run-approval-wording` and `python bot.py --vol-targeted-growth-saved-price-snapshot-run-approval-record` define and record approval for one future price-only snapshot run. They can set `saved_price_snapshot_run_approved=True`, but they still keep `saved_prices_fetched=False`, `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-saved-price-snapshot-quality-gate` reads the saved price snapshot only and checks required symbols, missing/error rows, stale timestamps, and positive prices. A passing gate only means the saved prices are fit for manual review; it still keeps `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-quantity-calculation-readiness` reads saved target-dollar values and the saved price quality gate to decide whether a future quantity-calculation approval request is ready for manual review. It can set `quantity_calculation_discussion_ready=True`, but it keeps `quantity_calculation_approved=False`, `order_quantities_calculated=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- `python bot.py --vol-targeted-growth-quantity-calculation-approval-record`, `python bot.py --vol-targeted-growth-review-quantity-estimates`, and `python bot.py --vol-targeted-growth-review-quantity-quality-gate` create review-only share quantity estimates after explicit approval and quality-check them. They still keep `order_values_populated=False`, `order_instructions_created=False`, `orders_submitted=False`, and all execution/scheduling approvals false.
- The go/no-go dashboard and VPS daily monitoring summary surface the execution-design approval record, review quantity estimates, and quantity quality gate while keeping `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

## Paper-Live F7 Accounting Checkpoint

- `python bot.py --paper-live-f7-accounting-proof` is a report-only static checkpoint for the F7 accounting boundary.
- The checkpoint verifies weighted daily returns and no independent starting cash in the multi-sleeve portfolio backtest source.
- Expected status is `f7_accounting_static_proof_ready_for_manual_review` when those static checks pass.
- This F7 checkpoint has been accepted as the static accounting proof.
- Portfolio backtests remain not promotion evidence without a separate promotion review.
- Execution, paper execution, scheduling, live trading, repeat execution, and promotion approvals remain false.

## Paper-Live Next Ladder Candidate Scope

- `python bot.py --paper-live-next-ladder-candidate-scope` is a report-only checkpoint for the next manual ladder review scope.
- Current expected status is `next_ladder_candidate_scope_report_only`.
- Defensive sleeve is the next conservative report-only review scope.
- Multi-sleeve allocator is deferred until after defensive scope review.
- High-growth remains research-only and is not the next ladder scope.
- No promotion, execution, scheduling, order instructions, or portfolio backtest promotion evidence is approved.

## Paper-Live Defensive Sleeve Ladder-Scope Review

- `python bot.py --paper-live-defensive-sleeve-ladder-scope-review` is a saved-output/report-only defensive sleeve review.
- It checks saved defensive evidence file presence only.
- Expected status is `defensive_sleeve_ladder_scope_review_ready_for_manual_review` when the saved defensive evidence stack is present.
- If evidence files are missing, expected status is `defensive_sleeve_ladder_scope_missing_saved_evidence_manual_review_required`.
- `python bot.py --paper-live-defensive-sleeve-manual-review` now converts the complete saved defensive evidence stack into a manual-review checkpoint with `defensive_sleeve_manual_review_required`. QQQ100 remains the clean paper-live lead; the defensive sleeve is not promoted.
- `python bot.py --paper-live-defensive-sleeve-preview-readiness` records `defensive_sleeve_preview_candidate_not_approved_manual_review_required`, so defensive preview, promotion, execution, paper execution, repeat orders, live trading, and scheduling remain blocked until a separate manual decision.
- `python bot.py --paper-live-defensive-sleeve-evidence-quality` records `defensive_sleeve_evidence_quality_manual_review_required`, focusing the next review on split sensitivity, full-period drawdown, allocation decision blockers, and the QQQ100 role boundary. It is not a preview design and does not approve promotion or execution.
- `python bot.py --paper-live-checklist-status` now carries the defensive manual-review and preview-readiness statuses alongside the aligned QQQ100 no-action state.
- The defensive sleeve is not promoted, and no execution, scheduling, order instructions, or candidate label changes are approved.

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

The paper-live promotion gate comes from `python bot.py --paper-live-promotion-gate`, with saved display through `python bot.py --show-paper-live-promotion-gate`:

- It writes `data/paper_live_promotion_gate.csv`, `data/paper_live_promotion_gate_summary.csv`, `data/paper_live_promotion_gate_blockers.csv`, and `data/paper_live_promotion_gate_evidence.csv`.
- It is the Step 5 gate for manual paper-live candidate discussion only.
- It is limited to `qqq_100_trend_gate` / `QQQ`.
- `codex_qqq_adaptive_trend_exposure` remains an ambitious alternative only, `qqq_150_trend_gate` remains rejected, SMA/slow-SMA are excluded, and high-growth plus crypto remain research-only.
- `paper_live_candidate=True` can mean candidate-discussion status only. It does not approve execution, paper execution, order instructions, scheduling, or strategy-to-execution wiring.
- Missing required saved/static evidence is recorded as blocked/manual-review rather than silently promoting the candidate.
- Explicit human approval is still required before any future manually confirmed paper execution command.

The paper-live readiness report comes from `python bot.py --paper-live-readiness-report`, with saved display through `python bot.py --show-paper-live-readiness-report`:

- It writes `data/paper_live_readiness_report.csv`, `data/paper_live_readiness_summary.csv`, `data/paper_live_readiness_blockers.csv`, and `data/paper_live_readiness_evidence.csv`.
- It is the Step 7 readiness checkpoint for future manual QQQ100 paper-action discussion only.
- It checks repo-safety, baseline-freeze, paper-live promotion, QQQ100 exact alignment, and QQQ100 execution verifiers; monitoring-only normal bot policy; Alpaca paper-only/no-live boundaries; fixed `QQQ` and `qqq_100_trend_gate` scope; exact zero/one-share alignment; excluded SMA/slow-SMA/high-growth/crypto branches; separate confirmation-gated paper execution; open-order and duplicate-order requirements; postcheck/position-readability, portfolio/risk, and execution-readiness evidence; and no scheduling.
- Missing saved evidence is listed as a blocker or warning.
- It does not call Alpaca, read positions, refresh market data, create order instructions, approve execution, approve paper execution, approve scheduling, or approve live trading.
- Every summary row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, and `live_trading_approved=false`.

The paper-live state summary comes from `python bot.py --paper-live-state-summary`, with saved display through `python bot.py --show-paper-live-state-summary`:

- It writes `data/paper_live_state_summary.csv`, `data/paper_live_state_components.csv`, `data/paper_live_state_blockers.csv`, and `data/paper_live_state_evidence.csv`.
- It is the Step 10 daily checkpoint before any future manually confirmed QQQ100 paper command is considered.
- It reads saved QQQ100 preview/action/postcheck/order evidence, paper-live promotion gate output, paper-live readiness output, and saved paper-execution state files where available.
- It reports active strategy, active ticker, desired state, saved paper-position state, last saved QQQ100 order result, current saved alignment state, promotion gate status, readiness status, missing saved-evidence blockers, manual-discussion allowance, follow-up/repeat allowance, scheduling allowance, and live-trading allowance.
- Missing saved evidence is reported as blocked/manual-review or unavailable.
- It is not a readiness upgrade and does not call Alpaca, read live positions, refresh market data, create order instructions, approve execution, approve paper execution, approve follow-up orders, approve scheduling, or approve live trading.
- Every summary row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

The paper-live evidence audit comes from `python bot.py --paper-live-evidence-audit`, with saved display through `python bot.py --show-paper-live-evidence-audit`:

- It writes `data/paper_live_evidence_audit.csv`, `data/paper_live_evidence_audit_summary.csv`, `data/paper_live_evidence_audit_blockers.csv`, and `data/paper_live_evidence_audit_evidence.csv`.
- It is a saved-output-only reconciliation checkpoint for the QQQ100 paper-live chain.
- It reads saved QQQ100 preview/action/postcheck/order/state evidence and reports exact missing saved files or fields through `exact_missing_saved_evidence`.
- It can identify a reconciled saved state such as desired `long`, saved `paper_position_long`, saved quantity `1`, saved filled QQQ100 order result, and `aligned_long`.
- Reconciled saved evidence does not approve a follow-up or repeat paper order.
- Exact QQQ100 alignment requires saved quantity evidence. If the saved postcheck file or quantity field is missing, the state summary reports `qqq100_alignment_unverified_missing_saved_quantity` rather than treating a saved `paper_position_long` label as verified alignment.
- It does not call Alpaca, read live positions, refresh market data, create order instructions, approve execution, approve paper execution, approve follow-up orders, approve scheduling, or approve live trading.
- Every row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

The QQQ100 postcheck readiness report comes from `python bot.py --qqq100-postcheck-readiness-report`, with saved display through `python bot.py --show-qqq100-postcheck-readiness-report`:

- It writes `data/qqq100_postcheck_readiness_report.csv`, `data/qqq100_postcheck_readiness_summary.csv`, `data/qqq100_postcheck_readiness_blockers.csv`, and `data/qqq100_postcheck_readiness_runbook.csv`.
- It is a saved-output/runbook-only checkpoint for the VPS postcheck evidence state. It names exact missing evidence when `data\qqq100_paper_postcheck.csv` or `position_quantity_abs_or_current_position_quantity_abs` is missing, and reports saved postcheck status, recent-order match flag, saved QQQ position quantity, and alignment state when evidence is present.
- It documents that the only relevant future evidence command is `python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check`.
- It does not run that command. The read-only postcheck must not be run without explicit user approval.
- It does not call Alpaca, read live positions, run postcheck, run QQQ100 paper execution, create order instructions, approve execution, approve paper execution, approve follow-up orders, approve scheduling, or approve live trading.
- Every row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

The QQQ100 follow-up policy report comes from `python bot.py --qqq100-followup-policy-report`, with saved display through `python bot.py --show-qqq100-followup-policy-report`:

- It writes `data/qqq100_followup_policy_report.csv`, `data/qqq100_followup_policy_summary.csv`, `data/qqq100_followup_policy_blockers.csv`, and `data/qqq100_followup_policy_evidence.csv`.
- It is a saved-output/report-only no-action policy checkpoint for the current QQQ100 paper state.
- If desired state is `long` and saved QQQ position is long exactly one share, it reports `no_action_required_already_aligned` and explicitly does not allow another buy.
- If desired state is `flat` while saved QQQ is long exactly one share, it labels only `future_manual_flatten_discussion_possible`; if desired state is `long` while saved QQQ is flat, it labels only `future_manual_buy_discussion_possible`.
- Missing, fractional, excess, or contradictory saved quantity evidence blocks/manual-review.
- It does not call Alpaca, read live positions, run postcheck, run QQQ100 paper execution, create executable order instructions, approve execution, approve paper execution, approve repeat execution, approve follow-up orders, approve scheduling, or approve live trading.
- Every row preserves `repeat_execution_approved=false`, `followup_order_approved=false`, `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, and `live_trading_approved=false`.

The QQQ100 daily decision report comes from `python bot.py --qqq100-daily-decision-report`, with saved display through `python bot.py --show-qqq100-daily-decision-report`:

- It writes `data/qqq100_daily_decision_report.csv`, `data/qqq100_daily_decision_summary.csv`, `data/qqq100_daily_decision_blockers.csv`, and `data/qqq100_daily_decision_evidence.csv`.
- It reads saved QQQ100 paper-live evidence and saved follow-up/no-action policy only.
- It can report `qqq100_daily_decision_hold_no_action_aligned_long`, `qqq100_daily_decision_hold_no_action_aligned_flat`, `qqq100_daily_decision_manual_buy_discussion_possible_not_approved`, `qqq100_daily_decision_manual_flatten_discussion_possible_not_approved`, or `qqq100_daily_decision_blocked_manual_review_required`.
- It does not call Alpaca, read live positions, refresh market data, create executable order instructions, run QQQ100 paper execution, approve execution, approve repeat/follow-up orders, approve scheduling, or approve live trading.

The QQQ100 manual flatten readiness report comes from `python bot.py --qqq100-manual-flatten-readiness-report`, with saved display through `python bot.py --show-qqq100-manual-flatten-readiness-report`:

- It writes `data/qqq100_manual_flatten_readiness_report.csv`, `data/qqq100_manual_flatten_readiness_summary.csv`, `data/qqq100_manual_flatten_readiness_blockers.csv`, and `data/qqq100_manual_flatten_readiness_evidence.csv`.
- It reads saved QQQ100 paper-live evidence and saved follow-up/no-action policy only.
- Current aligned-long evidence should report `flatten_not_needed_currently` with `recommended_next_step=hold_no_action_and_monitor_only`.
- If a future saved signal says desired state is `flat` while saved QQQ position is long exactly one share, it can report `future_manual_flatten_discussion_possible_not_approved`, which is only a manual review checkpoint.
- It does not call Alpaca, read live positions, refresh market data, create executable order instructions, run QQQ100 paper execution, approve flatten execution, approve repeat/follow-up orders, approve scheduling, or approve live trading.

The QQQ100 manual flatten runbook/design report comes from `python bot.py --qqq100-manual-flatten-runbook-report`, with saved display through `python bot.py --show-qqq100-manual-flatten-runbook-report`:

- It writes `data/qqq100_manual_flatten_runbook_report.csv`, `data/qqq100_manual_flatten_runbook_summary.csv`, `data/qqq100_manual_flatten_runbook_blockers.csv`, and `data/qqq100_manual_flatten_runbook_evidence.csv`.
- It reads the saved QQQ100 manual flatten readiness checkpoint only.
- Current aligned-long evidence should report `manual_flatten_runbook_not_needed_currently`.
- If future saved evidence says desired state is `flat` while saved QQQ position is long exactly one share, it can report `manual_flatten_runbook_manual_review_required_not_approved`.
- It does not call Alpaca, read live positions, refresh market data, create executable order instructions, run QQQ100 paper execution, approve manual flatten, approve flatten execution, approve repeat/follow-up orders, approve scheduling, or approve live trading.

The paper-live monitoring status comes from `python bot.py --paper-live-monitoring-status`, with saved display through `python bot.py --show-paper-live-monitoring-status`:

- It writes `data/paper_live_monitoring_status.csv`, `data/paper_live_monitoring_components.csv`, and `data/paper_live_monitoring_blockers.csv`.
- It is a saved-output/report-only Step 11 checkpoint for VPS/Hermes-safe monitoring displays.
- It reports `active_strategy=qqq_100_trend_gate`, `active_ticker=QQQ`, saved QQQ position state/quantity, alignment state, follow-up policy status, no-action status, and `recommended_next_step=hold_no_action_and_monitor_only` when already aligned long one share.
- `python bot.py --vps-monitoring-status` and `python bot.py --vps-daily-monitoring-summary` include this saved paper-live status and the saved QQQ100 daily decision so VPS/Hermes output can show QQQ100 is aligned long one, the daily decision is hold/no-action, repeat/follow-up orders are unapproved, and `never_schedule_order_capable_commands=True`.
- The same VPS/Hermes-safe status output also includes the saved QQQ100 manual flatten readiness and runbook statuses when present. Current aligned-long evidence should show `flatten_not_needed_currently` and `manual_flatten_runbook_not_needed_currently`; neither status approves a flatten action.
- If saved evidence is missing, it reports `missing_saved_evidence` or manual review instead of approving execution.
- It does not create, edit, trigger, or schedule Hermes cron jobs; call Alpaca; read live positions; run postcheck; run QQQ100 paper execution; create executable order instructions; approve execution; approve paper execution; approve repeat execution; approve follow-up orders; approve scheduling; or approve live trading.
- Every row preserves `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, `followup_order_approved=false`, `repeat_execution_approved=false`, and `never_schedule_order_capable_commands=true`.

The paper-live checklist status closeout comes from `python bot.py --paper-live-checklist-status`, with saved display through `python bot.py --show-paper-live-checklist-status`:

- It writes `data/paper_live_checklist_status.csv`, `data/paper_live_checklist_status_summary.csv`, `data/paper_live_checklist_status_blockers.csv`, and `data/paper_live_checklist_status_evidence.csv`.
- It reads saved paper-live monitoring status only and records `paper_live_checklist_vol_targeted_seed_status_only_phase_ready_manual_review` when the volatility-targeted seed is the active status seed, QQQ100 remains aligned long one share as previous-seed context, no action is required, and `recommended_next_step=hold_no_action_and_monitor_only`.
- PAPER_LIVE_CHECKLIST Steps 1-11 are complete or complete-for-current-QQQ100-monitoring-phase; Step 12 remains future-only for a later generic promotion ladder, starting QQQ100 only.
- It does not approve execution, paper execution, repeat/follow-up orders, scheduling, live trading, or executable order instructions.

The paper-live F6/F7 audit comes from `python bot.py --paper-live-f6-f7-audit`, with saved display through `python bot.py --show-paper-live-f6-f7-audit`:

- It writes `data/paper_live_f6_f7_audit.csv`, `data/paper_live_f6_f7_audit_summary.csv`, `data/paper_live_f6_f7_audit_blockers.csv`, and `data/paper_live_f6_f7_audit_evidence.csv`.
- F6 audits preview/action/report paths so unknown positions stay loud (`position_unknown`, `position_unavailable`, `manual_review_required`) and are not assumed flat.
- F7 audits starting-cash/accounting consistency for portfolio backtests before any backtest output can become promotion evidence.
- Current expected status is `paper_live_f6_f7_audit_manual_review_required`: F6 boundaries are partially confirmed, and F7 needs targeted accounting tests or verifiers before any generic promotion ladder or multi-sleeve paper-live work.
- It does not run market-data backtests, call Alpaca/yfinance, read positions, approve execution, approve scheduling, or build the generic promotion ladder.
- F6/F7 targeted checks now use `python scripts\verify_paper_live_f6_f7_targeted_checks.py` to exercise pure preview helpers for unknown positions and to keep portfolio backtests not promotion evidence until accounting consistency is proven.

The paper-live promotion ladder design checkpoint comes from `python bot.py --paper-live-promotion-ladder-design`, with saved display through `python bot.py --show-paper-live-promotion-ladder-design`:

- It writes `data/paper_live_promotion_ladder_design.csv`, `data/paper_live_promotion_ladder_design_summary.csv`, `data/paper_live_promotion_ladder_design_blockers.csv`, and `data/paper_live_promotion_ladder_design_evidence.csv`.
- It documents future stage labels only: `research_candidate`, `preview_candidate`, `paper_live_candidate`, and `manually_executable_candidate`.
- The current report/status seed is `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE`; QQQ100 remains previous-seed context, monitor-only/aligned long one share, with no repeat, follow-up, or flatten QQQ order approved.
- It includes the saved QQQ100 manual flatten readiness/runbook checkpoints: current expected labels are `flatten_not_needed_currently` and `manual_flatten_runbook_not_needed_currently`.
- Multi-sleeve remains report/status only with no portfolio execution wiring; high-growth and crypto remain research-only, defensive sleeves remain future review only, and no SMA or slow-SMA paper-live promotion is allowed.
- Portfolio backtests are not promotion evidence until accounting consistency is proven; unknown positions block/manual-review rather than assume flat; no scheduled execution is allowed.
- This checkpoint is report-only and does not implement generic promotion logic, execution, order instructions, broker reads, scheduling, or strategy-to-execution wiring.

The paper-live promotion ladder status scaffold comes from `python bot.py --paper-live-promotion-ladder-status`, with saved display through `python bot.py --show-paper-live-promotion-ladder-status`:

- It writes `data/paper_live_promotion_ladder_status.csv`, `data/paper_live_promotion_ladder_status_summary.csv`, `data/paper_live_promotion_ladder_status_blockers.csv`, and `data/paper_live_promotion_ladder_status_evidence.csv`.
- It reads saved ladder design, paper-live monitoring, daily decision, and QQQ100 flatten readiness/runbook summaries only.
- The volatility-targeted growth candidate is the current report/status seed; QQQ100 remains previous-seed context. Current expected status is `paper_live_promotion_ladder_status_report_only` with QQQ100 `previous_seed_monitor_only_aligned_long_one`.
- High-growth and crypto remain research-only, defensive sleeves remain future-review-only, SMA and slow-SMA remain excluded, and portfolio backtests remain not promotion evidence. F7 accounting proof is accepted as a static accounting checkpoint, but it does not approve promotion.
- This scaffold does not promote strategies, create order instructions, call Alpaca, read positions, approve execution, approve scheduling, or implement generic promotion logic.

The paper-live QQQ-led multi-sleeve roadmap checkpoint comes from `python bot.py --paper-live-multi-sleeve-roadmap`, with saved display through `python bot.py --show-paper-live-multi-sleeve-roadmap`:

- It writes `data/paper_live_multi_sleeve_roadmap.csv`, `data/paper_live_multi_sleeve_roadmap_summary.csv`, `data/paper_live_multi_sleeve_roadmap_blockers.csv`, and `data/paper_live_multi_sleeve_roadmap_evidence.csv`.
- It documents the future QQQ-led multi-sleeve direction only and does not change the current QQQ100-only monitoring phase.
- QQQ100 core sleeve remains the current monitor-only base, aligned long one share, and the only current ladder seed.
- Defensive sleeve is future review only and must pass the promotion ladder separately.
- High-growth sleeve remains research-only until concentration, drawdown, and attribution review are complete.
- Crypto sleeve remains research-only/capped/future-only with no crypto execution approved.
- Multi-sleeve allocator is future-only with no portfolio execution wiring, no order instructions, and no scheduling.
- This checkpoint is report-only and does not implement portfolio execution, execution approval, order instructions, broker reads, scheduling, or strategy-to-execution wiring.

The paper-live next-phase backlog checkpoint comes from `python bot.py --paper-live-next-phase-backlog`, with saved display through `python bot.py --show-paper-live-next-phase-backlog`:

- It writes `data/paper_live_next_phase_backlog.csv`, `data/paper_live_next_phase_backlog_summary.csv`, `data/paper_live_next_phase_backlog_blockers.csv`, and `data/paper_live_next_phase_backlog_evidence.csv`.
- It lists the required future work for QQQ100 core, generic promotion ladder, F6/F7, defensive sleeve, high-growth sleeve, crypto sleeve, multi-sleeve allocator, and Monitoring/Hermes.
- Volatility-targeted growth is the current report/status seed. QQQ100 remains previous-seed context, aligned long one share, with no action required and no repeat/follow-up order approved.
- Generic promotion ladder implementation remains future-only with no execution wiring.
- F6/F7 targeted checks exist, unknown positions must stay loud, and portfolio backtest accounting must be proven before portfolio metrics become promotion evidence.
- Defensive, high-growth, crypto, and allocator work are blocked behind saved-output evidence reviews; no sleeve is promoted.
- Monitoring/Hermes remains monitoring-only and order-capable commands must never be scheduled.
- This checkpoint is report-only and does not implement portfolio execution, execution approval, order instructions, broker reads, scheduling, or strategy-to-execution wiring.

The paper-live multi-sleeve evidence-gap audit comes from `python bot.py --paper-live-multi-sleeve-evidence-gap`, with saved display through `python bot.py --show-paper-live-multi-sleeve-evidence-gap`:

- It writes `data/paper_live_multi_sleeve_evidence_gap.csv`, `data/paper_live_multi_sleeve_evidence_gap_summary.csv`, `data/paper_live_multi_sleeve_evidence_gap_blockers.csv`, and `data/paper_live_multi_sleeve_evidence_gap_evidence.csv`.
- It checks saved-output file presence only for QQQ100 core, defensive sleeve, high-growth sleeve, crypto sleeve, and multi-sleeve allocator evidence.
- Missing saved outputs are blockers/manual-review items, not execution approval.
- QQQ100 core remains the only current paper-live monitor base, aligned long one share with no action required.
- Defensive, high-growth, crypto, and allocator sleeves stay future-only/research-only until missing evidence blockers are closed.
- No sleeve is promoted, no action previews or order instructions are created, no research is rerun, no market data is refreshed, and no portfolio execution or scheduling is implemented.

The paper-live high-growth evidence-gap audit comes from `python bot.py --paper-live-high-growth-evidence-gap`, with saved display through `python bot.py --show-paper-live-high-growth-evidence-gap`:

- It writes `data/paper_live_high_growth_evidence_gap.csv`, `data/paper_live_high_growth_evidence_gap_summary.csv`, `data/paper_live_high_growth_evidence_gap_blockers.csv`, and `data/paper_live_high_growth_evidence_gap_evidence.csv`.
- It checks saved-output file presence only for high-growth saved lead evidence, concentration/top-contributor dependency evidence, drawdown-window evidence, component attribution evidence, survivorship/current-constituent/outlier warning evidence, and promotion-readiness blockers.
- Missing saved outputs are blockers/manual-review items, not execution approval.
- No high-growth sleeve is promoted, no action previews or order instructions are created, no research is rerun, no market data is refreshed, and no portfolio execution or scheduling is implemented.

The paper-live high-growth evidence quality review comes from `python bot.py --paper-live-high-growth-evidence-quality`, with saved display through `python bot.py --show-paper-live-high-growth-evidence-quality`:

- It writes `data/paper_live_high_growth_evidence_quality.csv`, `data/paper_live_high_growth_evidence_quality_summary.csv`, `data/paper_live_high_growth_evidence_quality_blockers.csv`, and `data/paper_live_high_growth_evidence_quality_evidence.csv`.
- It reads only canonical saved high-growth evidence CSVs and summarizes concentration/outlier quality, drawdown quality, component attribution quality, survivorship/current-constituent bias warnings, and promotion-readiness boundaries.
- It may surface TSLA/outlier dependency or severe drawdown context from saved evidence, but this remains manual-review context only.
- No high-growth sleeve is promoted, no preview candidate or paper-live candidate is approved, no action previews or order instructions are created, no market data is refreshed, and no execution or scheduling is approved.

The paper-live high-growth manual-review decision comes from `python bot.py --paper-live-high-growth-manual-review-decision`, with saved display through `python bot.py --show-paper-live-high-growth-manual-review-decision`:

- It writes `data/paper_live_high_growth_manual_review_decision.csv`, `data/paper_live_high_growth_manual_review_decision_summary.csv`, `data/paper_live_high_growth_manual_review_decision_blockers.csv`, and `data/paper_live_high_growth_manual_review_decision_evidence.csv`.
- It reads only the saved high-growth evidence-gap and evidence-quality outputs, summarizes the manual-review reason, and does not dump full generated CSV contents.
- Expected status is `high_growth_remains_research_only_manual_review_required` when saved evidence shows outlier dependence, one-name concentration, severe drawdown, survivorship/current-constituent warnings, or `high_growth_stock_outlier_dependent`.
- QQQ100 remains the cleaner current paper-live monitor base; high-growth is not a preview candidate or paper-live candidate, and high-growth promotion remains false.
- Future reconsideration requires concentration control evidence, component/drawdown attribution with acceptable dependency, split/cost review, portfolio accounting consistency, F6/F7 compatibility, risk policy review, and no order instructions or scheduling.

The QQQ100 manual paper execution command is `python bot.py --execute-qqq100-paper --confirm-qqq100-paper`:

- It is high-risk and manually confirmed.
- It reads only the saved `data/qqq100_preview_signal_pack.csv` signal for `qqq_100_trend_gate` / `QQQ`.
- It is fixed to exact zero/one QQQ paper-share alignment, requires Alpaca paper mode, refuses live mode, refuses shorting/leverage, and does not use the normal config ticker universe.
- It checks QQQ paper position, open QQQ orders, market-open status, and recent matching QQQ one-share broker orders before any submission.
- It may buy one QQQ share when the saved signal is `long` and QQQ is flat, hold when the saved signal is `long` and QQQ is exactly one share, sell one QQQ share when the saved signal is `flat` and QQQ is exactly one share, or hold flat when desired flat and QQQ is zero.
- If the QQQ paper position is more than one QQQ share, it must block/manual review rather than silently treating the position as aligned, reducing to one, or selling all.
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

The sleeve research scoreboard comes from `python bot.py --sleeve-research-scoreboard`, with saved display through `python bot.py --show-sleeve-research-scoreboard`:

- It reads saved CSV context only, including multi-sleeve monitor, QQQ100 repeat design, paper execution state, QQQ100 postcheck/action/signal, portfolio preview/risk, project research state, high-growth checkpoints, growth/defensive saved research, and crypto saved research where present.
- It writes `data/sleeve_research_scoreboard.csv`, `data/sleeve_research_candidates.csv`, `data/sleeve_research_rankings.csv`, `data/sleeve_research_blockers.csv`, `data/sleeve_research_next_steps.csv`, and `data/sleeve_research_codex_experimental_sleeve.csv`.
- It keeps `qqq100_core_trend_sleeve` as the only active paper sleeve and best active paper sleeve.
- It ranks defensive ETF, high-growth stock, crypto, and `codex_experimental_research_sleeve` as research-only candidates.
- The Codex experimental candidate is `codex_qqq_defensive_crash_gate_research_sleeve`, an adaptive QQQ plus defensive crash-gate research hypothesis; it is not preview/action/execution wiring.
- Missing metrics are labelled `missing_saved_metrics`; they are not invented.
- It preserves false execution, follow-up, repeat, scheduling, live, high-growth, crypto, and Codex-experimental execution approval flags.

The Codex QQQ defensive crash-gate research pack comes from `python bot.py --codex-qqq-defensive-crash-gate-research-pack`, with saved display through `python bot.py --show-codex-qqq-defensive-crash-gate-research-pack`:

- It reads saved CSV metrics/context only, including the sleeve scoreboard, QQQ100 signal/action/postcheck/state context, QQQ lead context, portfolio risk, growth/defensive research outputs, and project research state where present.
- It writes `data/codex_qqq_defensive_crash_gate_research_pack.csv`, `data/codex_qqq_defensive_crash_gate_candidates.csv`, `data/codex_qqq_defensive_crash_gate_rankings.csv`, `data/codex_qqq_defensive_crash_gate_splits.csv`, `data/codex_qqq_defensive_crash_gate_blockers.csv`, and `data/codex_qqq_defensive_crash_gate_next_steps.csv`.
- It compares `qqq100_trend_gate_reference`, `codex_qqq_cash_crash_gate_sleeve`, `codex_qqq_spy_defensive_gate_sleeve`, `codex_qqq_partial_defensive_sleeve`, `codex_qqq_fast_crash_exit_reentry_sleeve`, and `codex_qqq_calmar_optimised_defensive_gate_sleeve`.
- It labels missing candidate metrics, split metrics, and defensive ETF data as `missing_saved_metrics`, `missing_saved_split_metrics`, or `missing_saved_data` rather than inventing values.
- It keeps the Codex experimental sleeve research-only and preserves false execution, Codex-experimental execution, repeat, follow-up, live, and scheduling approval flags.

The sleeve return-stream generator comes from `python bot.py --sleeve-return-streams`, with saved display through `python bot.py --show-sleeve-return-streams`:

- It generates research-only daily stream rows for `qqq100_core_trend_sleeve` / `qqq_100_trend_gate`, defensive QQQ crash-gate candidates, cash/no-position, and the Codex experimental defensive QQQ sleeve where QQQ/SPY research price data exists.
- It writes `data/sleeve_return_streams.csv`, `data/sleeve_return_streams_summary.csv`, `data/sleeve_return_streams_sleeves.csv`, `data/sleeve_return_streams_quality.csv`, `data/sleeve_return_streams_blockers.csv`, and `data/sleeve_return_streams_next_steps.csv`.
- It labels QQQ100 metric alignment as `approximate_or_needs_reconciliation` unless exact saved-source parity is available.
- It labels high-growth and crypto as `missing_saved_return_stream` when no real daily stream exists and does not invent daily returns from summary metrics.
- The expected status is `sleeve_return_streams_partial_created` while high-growth and crypto are missing; all execution, follow-up, repeat, scheduling, live, high-growth, crypto, and Codex-experimental approval flags remain false.

The high-growth return-stream generator comes from `python bot.py --high-growth-return-streams`, with saved display through `python bot.py --show-high-growth-return-streams`:

- It reuses the fixed high-growth drawdown-control research logic to create saved daily stream rows for `codex_broad_growth_balanced_breakout_control` and the broad Top1 reference where research market data exists.
- It writes `data/high_growth_return_streams.csv`, `data/high_growth_return_stream_metrics.csv`, `data/high_growth_return_stream_summary.csv`, and `data/high_growth_return_stream_blockers.csv`.
- It keeps the high-growth branch research-only, preserves concentration/survivorship/outlier warnings, and does not approve preview promotion, execution, paper execution, repeat execution, scheduling, or Alpaca/order paths.
- The multi-sleeve backtest can consume `data/high_growth_return_streams.csv` as saved daily stream input; crypto remains missing unless a separate real daily stream exists.

The QQQ100 stream reconciliation checkpoint comes from `python bot.py --qqq100-stream-reconciliation`, with saved display through `python bot.py --show-qqq100-stream-reconciliation`:

- It compares saved `qqq_100_trend_gate` / `qqq100_core_trend_sleeve` benchmark metrics with the generated QQQ100 daily stream from `data/sleeve_return_streams.csv`.
- It writes `data/qqq100_stream_reconciliation.csv`, `data/qqq100_stream_reconciliation_candidates.csv`, `data/qqq100_stream_reconciliation_diagnostics.csv`, `data/qqq100_stream_reconciliation_blockers.csv`, `data/qqq100_stream_reconciliation_summary.csv`, `data/qqq100_recovered_reference_stream.csv`, and `data/qqq100_recovered_reference_metrics.csv`.
- It tests the current saved generated stream, close versus adjusted-close availability, signal shift, SMA100 warmup/date alignment, cash/flat handling, and cost/slippage assumption gaps where saved research price data exists.
- It includes one fixed recovered-inputs reconstruction candidate, `qqq100_recovered_inputs_sma200_close_to_close_10bps`, using QQQ daily yfinance-style assumptions, SMA200, prior-close signal timing, next-bar close-to-close returns, 1.00x exposure, zero cash return, and 10 bps exposure-change cost.
- It applies fixed gap thresholds for CAGR, Sharpe, MaxDD, and Calmar before any candidate can be called close enough for research review; current saved outputs remain `qqq100_reconciliation_still_blocked` while a material CAGR gap remains.
- The fixed reconstruction candidate uses `qqq100_reconstruction_close_enough_for_research_review` only if all thresholds pass; otherwise it is labelled `qqq100_reconstruction_attempt_still_blocked`.
- A threshold-passing recovered reference may be consumed by multi-sleeve reports as the preferred QQQ100 research reference, while the old generated `qqq_100_trend_gate` stream remains retained as diagnostic context.
- It labels missing original benchmark source stream/data, date range, price adjustment, cash, and cost assumptions rather than forcing generated-stream parity.
- It does not update `--sleeve-return-streams` automatically; QQQ100 remains the only active paper sleeve and all execution, follow-up, repeat, scheduling, and live-trading approval flags remain false.

The QQQ100 benchmark-input reconstruction checkpoint comes from `python bot.py --qqq100-benchmark-inputs-report`, with saved display through `python bot.py --show-qqq100-benchmark-inputs`:

- It writes `data/qqq100_benchmark_inputs_report.csv`, `data/qqq100_benchmark_inputs_summary.csv`, and `data/qqq100_benchmark_input_gaps.csv`.
- It documents the likely tracked source chain behind the saved `qqq_100_trend_gate` metrics: `fa1d63d` QQQ leverage validation, `ae0ab7f` QQQ lead decision, and `4aebc22` project research state refresh.
- It records the likely original assumptions as QQQ daily yfinance data, `period='10y'`, `interval='1d'`, `auto_adjust=True`, SMA200 trend gate, prior-close signal, next-bar close-to-close returns, zero-return cash days, and 10 bps exposure-change cost.
- It keeps the status at `source_partially_recovered` because the original daily equity/return stream and exact yfinance snapshot/date range are missing.
- It must not be used to force the generated QQQ100 stream to match the saved benchmark; all execution, paper execution, scheduling, and live-trading approvals remain false.

The multi-sleeve portfolio backtest checkpoint comes from `python bot.py --multi-sleeve-portfolio-backtest`, with saved display through `python bot.py --show-multi-sleeve-portfolio-backtest`:

- It reads saved CSV outputs only, keeps exact saved `qqq_100_trend_gate` / `qqq100_core_trend_sleeve` benchmark metrics separate from the old generated QQQ100 diagnostic stream, and consumes `data/qqq100_recovered_reference_stream.csv` as the preferred QQQ100 research reference only when its saved threshold-pass audit row is valid.
- It writes `data/multi_sleeve_portfolio_backtest.csv`, `data/multi_sleeve_portfolio_backtest_sleeves.csv`, `data/multi_sleeve_portfolio_backtest_allocations.csv`, `data/multi_sleeve_portfolio_backtest_rankings.csv`, `data/multi_sleeve_portfolio_backtest_splits.csv`, `data/multi_sleeve_portfolio_backtest_trades.csv`, `data/multi_sleeve_portfolio_backtest_blockers.csv`, and `data/multi_sleeve_portfolio_backtest_summary.csv`.
- It compares `qqq100_only_reference`, `qqq100_plus_cash_defensive_reference`, `qqq100_plus_spy_sma200_defensive_gate`, `qqq100_plus_rolling_drawdown_defensive_gate`, `qqq100_plus_combined_defensive_gate`, `codex_defensive_qqq_research_portfolio`, high-growth, crypto, balanced multi-sleeve, and Codex ambitious candidates.
- It consumes defensive and Codex generated streams when present, while high-growth and crypto remain labelled as missing unless real daily streams exist.
- The expected status is `multi_sleeve_candidate_needs_more_data`; `qqq100_core_trend_sleeve` remains the only active paper sleeve and all execution, follow-up, repeat, scheduling, live, high-growth, crypto, and Codex-experimental approval flags remain false.

The multi-sleeve robustness checkpoint comes from `python bot.py --multi-sleeve-robustness`, with saved display through `python bot.py --show-multi-sleeve-robustness`:

- It reads saved return streams and multi-sleeve backtest CSVs only, then tests `qqq100_plus_high_growth_research` against the preferred QQQ100 research reference across fixed `split_60_40`, `split_70_30`, and `split_80_20` out-of-sample windows.
- It writes `data/multi_sleeve_robustness_report.csv` and `data/multi_sleeve_robustness_summary.csv`.

The multi-sleeve crypto review checkpoint comes from `python bot.py --multi-sleeve-crypto-review`, with saved display through `python bot.py --show-multi-sleeve-crypto-review`:

- It reads saved QQQ100 recovered-reference, high-growth, BTC/ETH crypto, cash, and multi-sleeve backtest CSVs only.
- It writes `data/multi_sleeve_crypto_review.csv`, `data/multi_sleeve_crypto_review_summary.csv`, `data/multi_sleeve_crypto_review_cost_stress.csv`, `data/multi_sleeve_crypto_review_split_robustness.csv`, and `data/multi_sleeve_crypto_review_volatility.csv`.
- It reviews `qqq100_plus_high_growth_plus_crypto_research` across fixed 60/40, 70/30, and 80/20 split windows, fixed crypto turnover cost stresses, and crypto volatility/drawdown contribution.
- It remains research-only and does not approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.

The multi-sleeve crypto containment review comes from `python bot.py --multi-sleeve-crypto-containment-review`, with saved display through `python bot.py --show-multi-sleeve-crypto-containment-review`:

- It reads saved crypto return streams, crypto review rows, weight sensitivity, lead state, high-growth drawdown decomposition, and portfolio backtest context only.
- It writes `data/multi_sleeve_crypto_containment_review.csv`, `data/multi_sleeve_crypto_containment_summary.csv`, `data/multi_sleeve_crypto_containment_drawdowns.csv`, and `data/multi_sleeve_crypto_containment_blockers.csv`.
- It checks whether the 5% crypto sleeve inside `higher_growth_70_20_5_5` is contained enough, whether crypto materially contributed to the selected lead's worst drawdown, whether no-crypto or higher-crypto nearby weights are preferable, and whether standalone BTC/ETH/combined crypto drawdowns require a containment blocker.
- Expected current interpretation remains cautious: 5% crypto may be contained at portfolio level but is still high-volatility and drawdown-sensitive, and increasing crypto is not supported by saved weight sensitivity.
- It remains research-only and does not optimise weights, refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve crypto execution, or connect research to execution.

The multi-sleeve allocation policy review checkpoint comes from `python bot.py --multi-sleeve-allocation-policy-review`, with saved display through `python bot.py --show-multi-sleeve-allocation-policy-review`:

- It reads saved multi-sleeve backtest, crypto review, high-growth, crypto, and recovered QQQ100 metrics only.
- It writes `data/multi_sleeve_allocation_policy_review.csv`, `data/multi_sleeve_allocation_policy_summary.csv`, `data/multi_sleeve_allocation_policy_components.csv`, and `data/multi_sleeve_allocation_policy_blockers.csv`.
- It reviews the fixed 75% QQQ100, 15% high-growth, 5% crypto, 5% defensive cash/bond allocation, component roles, concentration, small-sleeve sensitivity, and blockers before any future candidate label change.
- It remains research-only and does not approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.

The multi-sleeve weight sensitivity checkpoint comes from `python bot.py --multi-sleeve-weight-sensitivity`, with saved display through `python bot.py --show-multi-sleeve-weight-sensitivity`:

- It reads saved QQQ100 recovered-reference, high-growth, and crypto daily streams only.
- It writes `data/multi_sleeve_weight_sensitivity.csv`, `data/multi_sleeve_weight_sensitivity_summary.csv`, and `data/multi_sleeve_weight_sensitivity_blockers.csv`.
- It tests the fixed nearby allocations `current_75_15_5_5`, `lower_crypto_77_15_3_5`, `no_crypto_80_15_0_5`, `lower_growth_80_10_5_5`, `balanced_lower_risk_85_10_0_5`, `higher_crypto_73_15_7_5`, and `higher_growth_70_20_5_5`.
- It remains research-only and does not optimise weights, approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.

The multi-sleeve higher-growth review checkpoint comes from `python bot.py --multi-sleeve-higher-growth-review`, with saved display through `python bot.py --show-multi-sleeve-higher-growth-review`:

- It reads saved QQQ100 recovered-reference, high-growth, and crypto daily streams only.
- It writes `data/multi_sleeve_higher_growth_review.csv`, `data/multi_sleeve_higher_growth_summary.csv`, `data/multi_sleeve_higher_growth_split_review.csv`, `data/multi_sleeve_higher_growth_cost_review.csv`, `data/multi_sleeve_higher_growth_drawdown_review.csv`, and `data/multi_sleeve_higher_growth_blockers.csv`.
- It compares `current_75_15_5_5` with `higher_growth_70_20_5_5` across headline metrics, fixed splits, fixed cost stress, drawdown windows, and approximate contribution deltas before any future candidate label change.
- It remains research-only and does not optimise weights, approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.
- It reports Calmar and Sharpe split wins, worst split by Calmar/MaxDD, key blockers, and the next review step.
- It remains blocked by QQQ100 generated-stream reconciliation until saved/generated benchmark parity is resolved, and it does not approve preview promotion, execution, scheduling, Alpaca/order paths, or any sleeve-to-execution wiring.

The multi-sleeve research lead decision checkpoint comes from `python bot.py --multi-sleeve-research-lead-decision`, with saved display through `python bot.py --show-multi-sleeve-research-lead-decision`:

- It reads saved higher-growth review, split, cost, drawdown, weight-sensitivity, allocation-policy, crypto-review, portfolio-backtest, and QQQ100 metrics context only.
- It writes `data/multi_sleeve_research_lead_decision.csv`, `data/multi_sleeve_research_lead_summary.csv`, and `data/multi_sleeve_research_lead_blockers.csv`.
- It asks whether `higher_growth_70_20_5_5` should become the current research lead candidate versus `current_75_15_5_5`, using fixed cautious checks for return, risk, splits, cost stress, drawdown sensitivity, and false execution/scheduling flags.
- It remains research-only and does not optimise weights, approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.

The multi-sleeve lead-state refresh comes from `python bot.py --multi-sleeve-lead-state-refresh`, with saved display through `python bot.py --show-multi-sleeve-lead-state`:

- It reads saved research-lead decision, research-lead blockers, higher-growth review, weight-sensitivity, allocation-policy, crypto-review, and portfolio-backtest outputs only.
- It writes `data/multi_sleeve_lead_state.csv`, `data/multi_sleeve_lead_state_summary.csv`, and `data/multi_sleeve_lead_state_blockers.csv`.
- It records `higher_growth_70_20_5_5` as the current research lead candidate when the saved decision supports it, keeps `current_75_15_5_5` as the previous baseline, and preserves copied metrics/deltas plus manual-review blockers.
- It remains research-only and does not rerun backtests, optimise weights, approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.

The multi-sleeve high-growth drawdown decomposition comes from `python bot.py --multi-sleeve-high-growth-drawdown-decomposition`, with saved display through `python bot.py --show-multi-sleeve-high-growth-drawdown-decomposition`:

- It reads saved lead-state, research-lead decision, higher-growth review, split review, weight-sensitivity, portfolio-backtest, and saved QQQ100/high-growth/crypto return-stream outputs only.
- It writes `data/multi_sleeve_high_growth_drawdown_decomposition.csv`, `data/multi_sleeve_high_growth_drawdown_summary.csv`, `data/multi_sleeve_high_growth_drawdown_periods.csv`, and `data/multi_sleeve_high_growth_drawdown_blockers.csv`.
- It reconstructs current versus higher-growth drawdown windows, decomposes same-window weighted sleeve contributions, records incremental high-growth risk, and reviews recovery/bounce-back context.
- It remains research-only and does not add strategies, rerun backtests, optimise weights, approve crypto execution, paper execution, scheduling, order instructions, Alpaca calls, position reads, alert sends, or strategy-to-execution wiring.

The high-growth sleeve quality review comes from `python bot.py --high-growth-sleeve-quality-review`, with saved display through `python bot.py --show-high-growth-sleeve-quality-review`:

- It reads saved high-growth return streams, lead-state context, high-growth drawdown decomposition, and adjacent multi-sleeve review outputs only.
- It writes `data/high_growth_sleeve_quality_review.csv`, `data/high_growth_sleeve_quality_summary.csv`, `data/high_growth_sleeve_quality_splits.csv`, `data/high_growth_sleeve_quality_drawdowns.csv`, and `data/high_growth_sleeve_quality_blockers.csv`.
- It reviews the standalone `codex_broad_growth_balanced_breakout_control` sleeve metrics, fixed split stability, worst drawdown/recovery, contribution to `higher_growth_70_20_5_5`, and whether saved ticker-level concentration data is available.
- Expected current interpretation remains conservative: the sleeve can be promising but drawdown-sensitive, and missing ticker concentration data is a blocker before any further label change.
- It remains research-only and does not refresh market data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve execution, or connect research to execution.

The high-growth component attribution review comes from `python bot.py --high-growth-component-attribution`, with saved display through `python bot.py --show-high-growth-component-attribution`:

- It inspects existing saved high-growth outputs for real component ticker identifiers, holding dates, weights, component returns, weighted contributions, and drawdown-window contribution data.
- It writes `data/high_growth_component_attribution.csv`, `data/high_growth_component_attribution_summary.csv`, and `data/high_growth_component_attribution_blockers.csv`.
- If real component data exists, it may also write `data/high_growth_component_contributions.csv` and `data/high_growth_component_drawdown_contributions.csv`.
- Expected current interpretation is likely blocked because the existing saved high-growth outputs contain sleeve-level return streams but not ticker-level component holdings/weights/contributions.
- It remains research-only and does not invent ticker attribution, refresh market data, call yfinance, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve execution, or connect research to execution.

The high-growth component streams builder comes from `python bot.py --high-growth-component-streams`, with saved display through `python bot.py --show-high-growth-component-streams`:

- It reuses the existing high-growth return-stream price loader and selected `codex_broad_growth_balanced_breakout_control` simulation to reconstruct daily component ticker rows where holdings are exposed by the research simulation.
- It writes `data/high_growth_component_streams.csv`, `data/high_growth_component_streams_summary.csv`, `data/high_growth_component_streams_blockers.csv`, and, when component rows exist, `data/high_growth_component_drawdown_contributions.csv`.
- Component rows are labelled `equal_weight_component_sleeve` and `approximate_from_reconstructed_research_stream` because they are reconstructed from the existing research simulation rather than a new strategy.
- It remains research-only and does not optimise the sleeve, add variants, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve execution, or connect research to execution.

The high-growth sleeve concentration review comes from `python bot.py --high-growth-sleeve-concentration-review`, with saved display through `python bot.py --show-high-growth-sleeve-concentration-review`:

- It reads saved component streams, component attribution, sleeve quality, drawdown, and lead-state outputs only.
- It writes `data/high_growth_sleeve_concentration_review.csv`, `data/high_growth_sleeve_concentration_summary.csv`, `data/high_growth_sleeve_concentration_top_contributors.csv`, `data/high_growth_sleeve_concentration_drawdown.csv`, and `data/high_growth_sleeve_concentration_blockers.csv`.
- It reviews active-component counts, max component weight, top/bottom ticker contribution shares, Herfindahl dependency, and worst-drawdown component concentration before any further high-growth label change.
- Expected current interpretation remains cautious: the sleeve may stay a 20% research component, but low average active component count and 1.0 max component weight require manual concentration review first.
- It remains research-only and does not refresh yfinance data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve execution, or connect research to execution.

The high-growth research checkpoint comes from `python bot.py --high-growth-research-checkpoint`, with saved display through `python bot.py --show-high-growth-research-checkpoint`:

- It reads saved multi-sleeve lead state, weight sensitivity, higher-growth review, research lead decision, high-growth drawdown decomposition, sleeve quality, component attribution, component streams, sleeve concentration, and optional crypto containment outputs only.
- It writes `data/high_growth_research_checkpoint.csv` and `data/high_growth_research_checkpoint_blockers.csv`.
- Current interpretation is `high_growth_research_checkpoint_manual_review_required`: `higher_growth_70_20_5_5` remains the selected research lead candidate versus `current_75_15_5_5`, but concentration, drawdown, and crypto context still require manual review before any further label change.
- It remains research-only and does not refresh yfinance data, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, approve execution, approve crypto execution, or connect research to execution.

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

The high-growth strategy discovery sprint comes from `python bot.py --high-growth-strategy-discovery-sprint`, with saved display through `python bot.py --show-high-growth-strategy-discovery-sprint`:

- It reads saved high-growth stock, crypto, QQQ100, multi-sleeve, higher-growth allocation, robustness, component, and paper-live high-growth decision outputs where present; it does not refresh yfinance data.
- It writes `data/high_growth_strategy_discovery_sprint.csv`, `data/high_growth_strategy_discovery_sprint_summary.csv`, `data/high_growth_strategy_discovery_sprint_evidence.csv`, and `data/high_growth_strategy_discovery_sprint_blockers.csv`.
- It records seven subagent-style workstreams: aggressive trend/breakout, relative strength/rotation, crypto/risk-on sleeves, unconstrained experimental allocation, backtest engineering, robustness/audit, and evidence/reporting.
- Current saved status is `high_growth_strategy_discovery_two_or_more_strong_candidates_found` with 16 strategies, 7 candidate families, and 4 distinct strong research candidates. The top two are `higher_growth_70_20_5_5` and `qqq100_plus_high_growth_plus_crypto_research`.
- Fragile standalone references such as broad Top1 and standalone crypto sleeves remain rejected or watchlist due drawdown/concentration risk. The sprint is research/report-only and does not approve preview promotion, paper execution, order instructions, scheduling, or high-growth promotion.

The higher-growth preview readiness pack comes from `python bot.py --higher-growth-preview-readiness-pack`, with saved display through `python bot.py --show-higher-growth-preview-readiness-pack`:

- It reads saved discovery-sprint, higher-growth review, multi-sleeve portfolio-backtest, and QQQ100 recovered-reference outputs only; it does not refresh yfinance data.
- It writes `data/higher_growth_preview_readiness_pack.csv`, `data/higher_growth_preview_readiness_summary.csv`, `data/higher_growth_preview_readiness_evidence.csv`, and `data/higher_growth_preview_readiness_blockers.csv`.
- Current saved status is `higher_growth_preview_discussion_ready_manual_review_required`.
- It compares `higher_growth_70_20_5_5` against `qqq100_only_reference` and `balanced_multi_sleeve_research_portfolio`: target metrics are CAGR `23.6634`, Sharpe `1.2232`, MaxDD `-22.5209`, Calmar `1.0507`; QQQ100 reference is CAGR `16.9832`, Sharpe `1.0073`, MaxDD `-23.4576`, Calmar `0.724`; balanced comparator is CAGR `20.9941`, Sharpe `1.1947`, MaxDD `-21.6286`, Calmar `0.9707`.
- The strongest evidence is the target's saved CAGR/Sharpe/Calmar improvement versus QQQ100; the largest blocker remains `preview_implementation_not_added_and_manual_review_required`.
- It supports manual preview discussion only. It does not implement preview mode, create action previews or order instructions, approve paper execution, approve scheduling, or promote high-growth.

The higher-growth candidate selection decision comes from `python bot.py --higher-growth-candidate-selection-decision`, with saved display through `python bot.py --show-higher-growth-candidate-selection-decision`:

- It reads saved higher-growth preview-readiness, discovery-sprint, higher-growth review, higher-growth summary, and multi-sleeve portfolio-backtest outputs only.
- It writes `data/higher_growth_candidate_selection_decision.csv`, `data/higher_growth_candidate_selection_summary.csv`, `data/higher_growth_candidate_selection_evidence.csv`, and `data/higher_growth_candidate_selection_blockers.csv`.
- Current saved status is `higher_growth_candidate_selected_for_preview_design_review`.
- It selects `higher_growth_70_20_5_5` for the next future preview-design review, keeps `balanced_multi_sleeve_research_portfolio` as the calmer runner-up, and keeps `qqq100_plus_high_growth_plus_crypto_research` behind separate crypto policy/volatility review.
- The recommended next step is `design_saved_output_preview_only_mode_for_higher_growth_70_20_5_5`.
- Preview candidate approval, preview implementation approval, paper execution approval, execution approval, scheduling approval, high-growth promotion, and crypto execution remain false.

The higher-growth preview design checkpoint comes from `python bot.py --higher-growth-preview-design`, with saved display through `python bot.py --show-higher-growth-preview-design`:

- It reads saved higher-growth candidate-selection, preview-readiness, higher-growth review, and multi-sleeve portfolio-backtest outputs only.
- It writes `data/higher_growth_preview_design.csv`, `data/higher_growth_preview_design_summary.csv`, `data/higher_growth_preview_design_evidence.csv`, and `data/higher_growth_preview_design_blockers.csv`.
- Current saved status is `higher_growth_preview_design_ready_for_future_preview_implementation`.
- The documented future target sleeve weights are 70% `qqq100_core_trend_sleeve`, 20% `high_growth_stock_research_sleeve`, 5% `crypto_research_sleeve`, and 5% `defensive_cash_or_bond_sleeve`.
- Future preview output scope is saved target weights, sleeve statuses, blockers, and safety flags only; no order side, quantity, type, account, or executable order fields are allowed.
- Largest blocker is `preview_signal_not_implemented_and_no_order_instructions_allowed`; recommended next step is `implement_saved_output_preview_signal_for_higher_growth_70_20_5_5_in_separate_prompt`.
- Preview signal creation, action preview creation, order instructions, paper execution approval, execution approval, scheduling approval, high-growth promotion, and crypto execution remain false.

The volatility-targeted growth research sprint comes from `python bot.py --vol-targeted-growth-research-sprint`, with saved display through `python bot.py --show-vol-targeted-growth-research-sprint`:

- It reads saved QQQ100 recovered reference, high-growth, crypto, sleeve, QQQ100 metric, high-growth metric, and higher-growth selection outputs only; it does not refresh yfinance data.
- It writes `data/vol_targeted_growth_research_sprint.csv`, `data/vol_targeted_growth_candidate_summary.csv`, `data/vol_targeted_growth_rejected_candidates.csv`, `data/vol_targeted_growth_robustness_audit.csv`, and `data/vol_targeted_growth_parameter_sensitivity.csv`.
- It tests volatility-targeting methods including fixed target vol levels of 10%, 15%, 20%, and 25%; 20/60/120-day rolling realized-vol windows; long/cash exposure scaling capped at 1x; drawdown-control partial de-risking; inverse-volatility sleeve allocation; and QQQ100/high-growth/crypto/multi-sleeve source streams.
- Current saved status is `vol_targeted_growth_research_two_or_more_strong_candidates_found`: 64 strategies, 7 candidate families, and 4 distinct strong research candidates.
- Top saved candidates are `high_growth_balanced_target_vol_25_win_20_cap_1x` with CAGR `33.5011`, Sharpe `1.2296`, MaxDD `-28.3531`, Calmar `1.1816`, realized vol `26.3073`; and `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` with CAGR `19.0011`, Sharpe `1.2861`, MaxDD `-18.1016`, Calmar `1.0497`, realized vol `14.331`.
- QQQ100-only volatility-targeted variants that became too low-return are rejected as smooth/low-return rather than rewarded just for safety, and concentrated Top1 variants remain fragile/outlier-dependent even when volatility targeting improves the drawdown.
- The sprint is research/report-only. It does not create preview signals, action previews, order instructions, execution approval, paper execution approval, scheduling approval, high-growth promotion, or crypto execution approval.

The volatility-targeted growth manual review pack comes from `python bot.py --vol-targeted-growth-manual-review-pack`, with saved display through `python bot.py --show-vol-targeted-growth-manual-review-pack`:

- It reads only the saved volatility-targeted sprint, summary, rejected-candidate, robustness-audit, and parameter-sensitivity CSVs.
- It writes `data/vol_targeted_growth_manual_review_pack.csv`, `data/vol_targeted_growth_manual_review_summary.csv`, `data/vol_targeted_growth_manual_review_evidence.csv`, and `data/vol_targeted_growth_manual_review_blockers.csv`.
- Current saved status is `vol_targeted_growth_manual_review_required`.
- Current interpretation favours `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` as the cleaner next research path because it gives up raw CAGR but has a stronger Sharpe/Calmar and drawdown profile.
- `high_growth_balanced_target_vol_25_win_20_cap_1x` remains exciting but higher-risk, with drawdown, concentration, and outlier-dependence review required before any label change.
- The required next step is `run_saved_output_vol_targeted_growth_robustness_checkpoint_before_preview_design`; preview implementation, paper execution, order instructions, high-growth/crypto promotion, and scheduling remain false.

The volatility-targeted growth robustness checkpoint comes from `python bot.py --vol-targeted-growth-robustness-checkpoint`, with saved display through `python bot.py --show-vol-targeted-growth-robustness-checkpoint`:

- It reads only saved volatility-targeted sprint, manual-review, rejected-candidate, robustness-audit, and parameter-sensitivity CSVs.
- It writes `data/vol_targeted_growth_robustness_checkpoint.csv`, `data/vol_targeted_growth_robustness_checkpoint_summary.csv`, `data/vol_targeted_growth_robustness_checkpoint_evidence.csv`, and `data/vol_targeted_growth_robustness_checkpoint_blockers.csv`.
- Current expected status is `vol_targeted_growth_robustness_manual_review_required`.
- It checks the preferred `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` candidate for nearby parameter sensitivity, saved split stability, drawdown tradeoff versus `high_growth_balanced_target_vol_25_win_20_cap_1x`, and QQQ100/balanced comparator context.
- Preview readiness remains `vol_targeted_growth_preview_design_not_ready_robustness_review_required`; preview implementation, paper execution, order instructions, high-growth/crypto promotion, and scheduling remain false.

The volatility-targeted growth nearby-variants review comes from `python bot.py --vol-targeted-growth-nearby-variants-review`, with saved display through `python bot.py --show-vol-targeted-growth-nearby-variants-review`:

- It reads only saved volatility-targeted sprint, robustness-checkpoint, and parameter-sensitivity CSVs.
- It writes `data/vol_targeted_growth_nearby_variants_review.csv`, `data/vol_targeted_growth_nearby_variants_summary.csv`, `data/vol_targeted_growth_nearby_variants_evidence.csv`, and `data/vol_targeted_growth_nearby_variants_blockers.csv`.
- Current expected status is `vol_targeted_growth_nearby_variants_manual_review_required`.
- Current interpretation keeps `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` as the best risk-adjusted variant because it leads the saved nearby grid on Sharpe and Calmar.
- `higher_growth_multi_sleeve_target_vol_20_win_20_cap_1x` is the nearest higher-volatility step, while `higher_growth_multi_sleeve_target_vol_25_win_20_cap_1x` is the highest-CAGR/higher-drawdown challenger; both should be reviewed manually before any preview-design decision.
- Preview status remains `preview_design_still_blocked_pending_variant_review`; preview implementation, paper execution, order instructions, high-growth/crypto promotion, and scheduling remain false.

The volatility-targeted growth preview-readiness decision comes from `python bot.py --vol-targeted-growth-preview-readiness-decision`, with saved display through `python bot.py --show-vol-targeted-growth-preview-readiness-decision`:

- It reads only saved nearby-variant, robustness, and manual-review summaries.
- It writes `data/vol_targeted_growth_preview_readiness_decision.csv`, `data/vol_targeted_growth_preview_readiness_summary.csv`, `data/vol_targeted_growth_preview_readiness_evidence.csv`, and `data/vol_targeted_growth_preview_readiness_blockers.csv`.
- Current expected status is `vol_targeted_growth_15_20_selected_for_preview_design_review`.
- It selects `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` as the disciplined volatility-targeted growth lead for a future preview-design review.
- It keeps `higher_growth_multi_sleeve_target_vol_20_win_20_cap_1x` as the nearest higher-volatility challenger and `higher_growth_multi_sleeve_target_vol_25_win_20_cap_1x` as the aggressive higher-CAGR/higher-drawdown challenger.
- Preview-design discussion status is `preview_design_discussion_ready_manual_review_required`, but preview implementation remains `preview_implementation_not_added`; paper execution, order instructions, high-growth/crypto promotion, and scheduling remain false.

The volatility-targeted growth preview design checkpoint comes from `python bot.py --vol-targeted-growth-preview-design`, with saved display through `python bot.py --show-vol-targeted-growth-preview-design`:

- It reads only saved volatility-targeted preview-readiness, nearby-variant, and robustness summaries.
- It writes `data/vol_targeted_growth_preview_design.csv`, `data/vol_targeted_growth_preview_design_summary.csv`, `data/vol_targeted_growth_preview_design_evidence.csv`, and `data/vol_targeted_growth_preview_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_preview_design_ready_for_future_preview_implementation`.
- The documented future target variant is `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`: higher-growth multi-sleeve base allocation, 15% volatility target, 20-day volatility window, 1x exposure cap, and no leverage.
- Future preview output scope is saved candidate identity, target weights, volatility target/window, sleeve statuses, blockers, and safety flags only; no order side, quantity, type, account, or executable order fields are allowed.
- Largest blocker is `preview_signal_not_implemented_and_no_order_instructions_allowed`; recommended next step is `implement_saved_output_preview_signal_for_vol_targeted_growth_15_20_in_separate_prompt`.
- Preview signal creation, action preview creation, order instructions, paper execution approval, execution approval, scheduling approval, high-growth promotion, and crypto execution remain false.

The volatility-targeted growth preview signal comes from `python bot.py --vol-targeted-growth-preview-signal`, with saved display through `python bot.py --show-vol-targeted-growth-preview-signal`:

- It reads only saved volatility-targeted preview-design, preview-readiness, and nearby-variant outputs.
- It writes `data/vol_targeted_growth_preview_signal.csv`, `data/vol_targeted_growth_preview_signal_summary.csv`, `data/vol_targeted_growth_preview_signal_evidence.csv`, and `data/vol_targeted_growth_preview_signal_blockers.csv`.
- Current expected status is `vol_targeted_growth_preview_signal_created_saved_output_only`.
- It records `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`, 15% volatility target, 20-day volatility window, 1x exposure cap, no leverage, and saved target sleeve weights only.
- It does not create an action preview, executable order instructions, order side/quantity/type/account fields, broker calls, paper execution approval, execution approval, or scheduling approval.

The volatility-targeted growth action-preview design checkpoint comes from `python bot.py --vol-targeted-growth-action-preview-design`, with saved display through `python bot.py --show-vol-targeted-growth-action-preview-design`:

- It reads only the saved volatility-targeted preview signal and design outputs.
- It writes `data/vol_targeted_growth_action_preview_design.csv`, `data/vol_targeted_growth_action_preview_design_summary.csv`, `data/vol_targeted_growth_action_preview_design_evidence.csv`, and `data/vol_targeted_growth_action_preview_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_action_preview_design_ready_manual_review_required`.
- It documents that any future action preview must use manual-review labels, treat unknown position state loudly, and avoid order side, order quantity, order type, account, order ID, API key, webhook, or secret fields.
- It does not create actual action-preview rows, read broker positions, create orders, approve paper execution, approve live execution, or approve scheduling.

The volatility-targeted growth action preview comes from `python bot.py --vol-targeted-growth-action-preview`, with saved display through `python bot.py --show-vol-targeted-growth-action-preview`:

- It reads only the saved volatility-targeted preview signal and action-preview design outputs.
- It writes `data/vol_targeted_growth_action_preview.csv`, `data/vol_targeted_growth_action_preview_summary.csv`, `data/vol_targeted_growth_action_preview_evidence.csv`, and `data/vol_targeted_growth_action_preview_blockers.csv`.
- Current expected status is `vol_targeted_growth_action_preview_created_saved_output_only`.
- It creates sleeve-level manual-review rows for the saved 15/20 target weights, while `current_exposure_status=current_exposure_not_read` and `broker_positions_compared=false`.
- It does not read broker positions, create executable order instructions, include order side/quantity/type/account fields, approve paper execution, approve live execution, or approve scheduling.

The volatility-targeted growth action-preview quality gate comes from `python bot.py --vol-targeted-growth-action-preview-quality-gate`, with saved display through `python bot.py --show-vol-targeted-growth-action-preview-quality-gate`:

- It reads only the saved volatility-targeted action-preview, action-preview summary/blocker, and active-seed readiness outputs.
- It writes `data/vol_targeted_growth_action_preview_quality_gate.csv`, `data/vol_targeted_growth_action_preview_quality_gate_summary.csv`, `data/vol_targeted_growth_action_preview_quality_gate_evidence.csv`, and `data/vol_targeted_growth_action_preview_quality_gate_blockers.csv`.
- Current expected status is `vol_targeted_growth_action_preview_quality_gate_usable_manual_review_required` when saved rows are present, forbidden order fields are absent, current exposure remains loudly not read, and all execution/scheduling flags remain false.
- It still treats broker-position comparison as incomplete and does not read positions, call Alpaca, create order instructions, approve paper execution, approve live execution, or approve scheduling.

The volatility-targeted growth broker-position comparison design comes from `python bot.py --vol-targeted-growth-broker-position-comparison-design`, with saved display through `python bot.py --show-vol-targeted-growth-broker-position-comparison-design`:

- It writes `data/vol_targeted_growth_broker_position_comparison_design.csv`, `data/vol_targeted_growth_broker_position_comparison_design_summary.csv`, `data/vol_targeted_growth_broker_position_comparison_design_evidence.csv`, and `data/vol_targeted_growth_broker_position_comparison_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_broker_position_comparison_design_ready_manual_review_required`.
- It is design-only and does not call Alpaca, read broker positions, create orders, or approve execution/scheduling.

The volatility-targeted growth portfolio-risk review comes from `python bot.py --vol-targeted-growth-portfolio-risk-review`, with saved display through `python bot.py --show-vol-targeted-growth-portfolio-risk-review`:

- It writes `data/vol_targeted_growth_portfolio_risk_review.csv`, `data/vol_targeted_growth_portfolio_risk_review_summary.csv`, `data/vol_targeted_growth_portfolio_risk_review_evidence.csv`, and `data/vol_targeted_growth_portfolio_risk_review_blockers.csv`.
- Current expected status is `vol_targeted_growth_portfolio_risk_manual_review_required`.
- It keeps the candidate research-only: broker-position comparison and portfolio risk policy remain unresolved, so paper-live discussion, paper execution, execution, and scheduling are not approved.

The volatility-targeted growth portfolio-risk policy design comes from `python bot.py --vol-targeted-growth-portfolio-risk-policy-design`, with saved display through `python bot.py --show-vol-targeted-growth-portfolio-risk-policy-design`:

- It writes `data/vol_targeted_growth_portfolio_risk_policy_design.csv`, `data/vol_targeted_growth_portfolio_risk_policy_design_summary.csv`, `data/vol_targeted_growth_portfolio_risk_policy_design_evidence.csv`, and `data/vol_targeted_growth_portfolio_risk_policy_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_portfolio_risk_policy_design_ready_manual_review_required`.
- It proposes manual-review guardrails: zero total allocation until approval, 70% QQQ100 sleeve context, 20% high-growth sleeve review, 5% crypto cap, 5% defensive buffer definition, drawdown guardrails, broker-position guardrails, and no execution boundary.
- It does not enforce policy, approve paper-live candidacy, read broker positions, create orders, approve execution, or approve scheduling.

The volatility-targeted growth paper-live decision checkpoint comes from `python bot.py --vol-targeted-growth-paper-live-decision`, with saved display through `python bot.py --show-vol-targeted-growth-paper-live-decision`:

- It writes `data/vol_targeted_growth_paper_live_decision.csv`, `data/vol_targeted_growth_paper_live_decision_summary.csv`, `data/vol_targeted_growth_paper_live_decision_evidence.csv`, and `data/vol_targeted_growth_paper_live_decision_blockers.csv`.
- Current expected status is `vol_targeted_growth_research_only_broker_comparison_discussion_ready_manual_review_required`.
- The 15/20 candidate remains research-only; the checkpoint only says a future read-only broker-position comparison may be discussed manually. It does not call Alpaca, read positions, create orders, approve paper-live candidacy, approve execution, or approve scheduling.

The volatility-targeted growth broker-comparison run-readiness checkpoint comes from `python bot.py --vol-targeted-growth-broker-comparison-run-readiness`, with saved display through `python bot.py --show-vol-targeted-growth-broker-comparison-run-readiness`:

- It writes `data/vol_targeted_growth_broker_comparison_run_readiness.csv`, `data/vol_targeted_growth_broker_comparison_run_readiness_summary.csv`, `data/vol_targeted_growth_broker_comparison_run_readiness_evidence.csv`, and `data/vol_targeted_growth_broker_comparison_run_readiness_blockers.csv`.
- Current expected status is `vol_targeted_growth_readonly_broker_comparison_ready_for_explicit_manual_approval_required`.
- This checkpoint now requires the saved action-preview quality gate to be usable for manual review before it says the project is ready to ask for explicit manual approval before a future read-only broker-position comparison. It does not grant approval, call Alpaca, read positions, approve paper-live candidacy, create orders, approve execution, or approve scheduling.

The volatility-targeted growth broker-position comparison comes from `python bot.py --vol-targeted-growth-broker-position-comparison`, with saved display through `python bot.py --show-vol-targeted-growth-broker-position-comparison`:

- It writes `data/vol_targeted_growth_broker_position_comparison.csv`, `data/vol_targeted_growth_broker_position_comparison_summary.csv`, `data/vol_targeted_growth_broker_position_comparison_evidence.csv`, and `data/vol_targeted_growth_broker_position_comparison_blockers.csv`.
- Default mode does not call Alpaca or read positions; it writes `vol_targeted_growth_broker_position_comparison_not_run_confirmation_required`.
- Confirmed read-only mode requires `--confirm-readonly-alpaca-check` in a separately approved run. Even then, it compares saved target sleeves with paper-position context only and does not create order instructions, approve paper-live candidacy, approve execution, or approve scheduling.
- Strategy explanation: the candidate is a research-only multi-sleeve growth portfolio with 70% QQQ100 core trend, 20% high-growth research, 5% crypto research, and 5% defensive buffer. It targets 15% volatility over a 20-day window with a 1x cap, so it tries to keep growth exposure while reducing exposure when recent volatility rises.

The volatility-targeted growth post-comparison decision comes from `python bot.py --vol-targeted-growth-post-comparison-decision`, with saved display through `python bot.py --show-vol-targeted-growth-post-comparison-decision`:

- It writes `data/vol_targeted_growth_post_comparison_decision.csv`, `data/vol_targeted_growth_post_comparison_decision_summary.csv`, `data/vol_targeted_growth_post_comparison_decision_evidence.csv`, and `data/vol_targeted_growth_post_comparison_decision_blockers.csv`.
- Current expected status after a confirmed saved comparison is `vol_targeted_growth_stricter_paper_live_discussion_gate_ready_manual_review_required`.
- This means the next safe step is designing a stricter manual paper-live discussion gate. It does not approve that gate, paper-live candidacy, order instructions, execution, scheduling, or another broker read.

The volatility-targeted growth stricter paper-live gate design comes from `python bot.py --vol-targeted-growth-stricter-paper-live-gate-design`, with saved display through `python bot.py --show-vol-targeted-growth-stricter-paper-live-gate-design`:

- It writes `data/vol_targeted_growth_stricter_paper_live_gate_design.csv`, `data/vol_targeted_growth_stricter_paper_live_gate_design_summary.csv`, `data/vol_targeted_growth_stricter_paper_live_gate_design_evidence.csv`, and `data/vol_targeted_growth_stricter_paper_live_gate_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_stricter_paper_live_gate_design_ready_manual_review_required`.
- The gate requires QQQ100 to remain the incumbent paper-live seed, a separate allocation cap, high-growth and crypto to remain research-only, unmapped sleeves to stay non-actionable, drawdown/stress review, current read-only broker-position context, no executable order fields, and all execution/scheduling approvals false. It defines requirements only; it does not enforce or approve the gate.

The volatility-targeted growth gate review comes from `python bot.py --vol-targeted-growth-gate-review`, with saved display through `python bot.py --show-vol-targeted-growth-gate-review`:

- It writes `data/vol_targeted_growth_gate_review.csv`, `data/vol_targeted_growth_gate_review_summary.csv`, `data/vol_targeted_growth_gate_review_evidence.csv`, and `data/vol_targeted_growth_gate_review_blockers.csv`.
- Current expected status is `vol_targeted_growth_limited_manual_candidate_discussion_ready_gate_review_required`.
- This means saved evidence can support a limited manual candidate discussion only. QQQ100 remains the incumbent paper-live seed, the stricter gate is not enforced, and paper-live candidacy, execution, order instructions, and scheduling remain unapproved.

The volatility-targeted growth candidate discussion blocker checklist comes from `python bot.py --vol-targeted-growth-candidate-discussion-blocker-checklist`, with saved display through `python bot.py --show-vol-targeted-growth-candidate-discussion-blocker-checklist`:

- It writes `data/vol_targeted_growth_candidate_discussion_blocker_checklist.csv`, `data/vol_targeted_growth_candidate_discussion_blocker_checklist_summary.csv`, `data/vol_targeted_growth_candidate_discussion_blocker_checklist_evidence.csv`, and `data/vol_targeted_growth_candidate_discussion_blocker_checklist_blockers.csv`.
- Current expected status is `vol_targeted_growth_candidate_discussion_blocker_checklist_manual_review_required`.
- This checklist lists open blockers before any volatility-targeted implementation work: the stricter gate is not enforced, component sleeves remain research-only, unmapped sleeves cannot become order instructions, and implementation, paper-live candidacy, execution, repeat orders, and scheduling remain unapproved.

The volatility-targeted growth candidate decision record comes from `python bot.py --vol-targeted-growth-candidate-decision-record`, with saved display through `python bot.py --show-vol-targeted-growth-candidate-decision-record`:

- It writes `data/vol_targeted_growth_candidate_decision_record.csv`, `data/vol_targeted_growth_candidate_decision_record_summary.csv`, `data/vol_targeted_growth_candidate_decision_record_evidence.csv`, and `data/vol_targeted_growth_candidate_decision_record_blockers.csv`.
- Current expected status is `vol_targeted_growth_candidate_decision_manual_discussion_only`.
- This record freezes the current decision: manual candidate discussion may continue, QQQ100 remains the incumbent paper-live seed, and implementation, seed change, order instructions, execution, repeat orders, and scheduling remain unapproved.

The volatility-targeted growth candidate discussion comes from `python bot.py --vol-targeted-growth-candidate-discussion`, with saved display through `python bot.py --show-vol-targeted-growth-candidate-discussion`:

- It writes `data/vol_targeted_growth_candidate_discussion.csv`, `data/vol_targeted_growth_candidate_discussion_summary.csv`, `data/vol_targeted_growth_candidate_discussion_evidence.csv`, and `data/vol_targeted_growth_candidate_discussion_blockers.csv`.
- Current expected status is `vol_targeted_growth_non_executable_candidate_proposal_ready_manual_review_required`.
- This means QQQ100 remains the incumbent paper-live seed, while the volatility-targeted strategy may be discussed only as a non-executable paper-live candidate proposal. No preview implementation, order instruction, Alpaca call, execution, repeat order, or scheduling is approved.

The volatility-targeted growth proposal implementation design comes from `python bot.py --vol-targeted-growth-proposal-implementation-design`, with saved display through `python bot.py --show-vol-targeted-growth-proposal-implementation-design`:

- It writes `data/vol_targeted_growth_proposal_implementation_design.csv`, `data/vol_targeted_growth_proposal_implementation_design_summary.csv`, `data/vol_targeted_growth_proposal_implementation_design_evidence.csv`, and `data/vol_targeted_growth_proposal_implementation_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_proposal_implementation_design_ready_manual_review_required`.
- This means the future proposal implementation requirements are documented only. No preview/action implementation, order instruction, Alpaca call, QQQ100 displacement, execution, repeat order, or scheduling is approved.

The volatility-targeted growth proposal preview schema comes from `python bot.py --vol-targeted-growth-proposal-preview-schema`, with saved display through `python bot.py --show-vol-targeted-growth-proposal-preview-schema`:

- It writes `data/vol_targeted_growth_proposal_preview_schema.csv`, `data/vol_targeted_growth_proposal_preview_schema_summary.csv`, `data/vol_targeted_growth_proposal_preview_schema_evidence.csv`, and `data/vol_targeted_growth_proposal_preview_schema_blockers.csv`.
- Current expected status is `vol_targeted_growth_proposal_preview_schema_ready_manual_review_required`.
- This means the allowed and forbidden fields for a future proposal preview are documented only. Order side, quantity, order type, account, API key, webhook, token, and order ID fields are forbidden; QQQ100 remains the incumbent seed and no implementation, execution, repeat order, or scheduling is approved.

The volatility-targeted growth proposal preview comes from `python bot.py --vol-targeted-growth-proposal-preview`, with saved display through `python bot.py --show-vol-targeted-growth-proposal-preview`:

- It writes `data/vol_targeted_growth_proposal_preview.csv`, `data/vol_targeted_growth_proposal_preview_summary.csv`, `data/vol_targeted_growth_proposal_preview_evidence.csv`, and `data/vol_targeted_growth_proposal_preview_blockers.csv`.
- Current expected status is `vol_targeted_growth_proposal_preview_created_saved_output_only`.
- This means sleeve-level proposal rows exist for manual review only. Current exposure is not read, QQQ100 remains the incumbent seed, and no action preview, order instruction, execution, repeat order, or scheduling is approved.
- `python scripts\verify_vol_targeted_growth_preview_action_chain_checkpoint.py` verifies the existing volatility proposal/action-preview chain remains complete enough for non-executable review while preserving false implementation, seed-change, order, execution, repeat-order, and scheduling approvals.

The volatility-targeted growth seed-change review comes from `python bot.py --vol-targeted-growth-seed-change-review`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-review`:

- It writes `data/vol_targeted_growth_seed_change_review.csv`, `data/vol_targeted_growth_seed_change_review_summary.csv`, `data/vol_targeted_growth_seed_change_review_evidence.csv`, and `data/vol_targeted_growth_seed_change_review_blockers.csv`.
- Current expected status is `vol_targeted_growth_seed_change_review_created_manual_review_required`.
- This means the volatility proposal can continue through manual seed-change review, but QQQ100 remains the seed. No QQQ100 displacement, seed change, action preview, order instruction, execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change evidence pack comes from `python bot.py --vol-targeted-growth-seed-change-evidence-pack`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-evidence-pack`:

- It writes `data/vol_targeted_growth_seed_change_evidence_pack.csv`, `data/vol_targeted_growth_seed_change_evidence_summary.csv`, `data/vol_targeted_growth_seed_change_evidence_sources.csv`, and `data/vol_targeted_growth_seed_change_evidence_blockers.csv`.
- Current expected status is `vol_targeted_growth_seed_change_evidence_pack_incomplete_manual_review_required`.
- This means required evidence is explicitly incomplete. Component-sleeve approval review, risk/reward comparison, drawdown/stress review, cost/turnover review, split stability review, operational exposure context, action-preview design, and a formal seed-change proposal remain missing or manual-review required. QQQ100 remains the seed and no displacement, order instruction, execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change risk/reward comparison comes from `python bot.py --vol-targeted-growth-seed-change-risk-reward-comparison`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-risk-reward-comparison`:

- It writes `data/vol_targeted_growth_seed_change_risk_reward_comparison.csv`, `data/vol_targeted_growth_seed_change_risk_reward_summary.csv`, `data/vol_targeted_growth_seed_change_risk_reward_evidence.csv`, and `data/vol_targeted_growth_seed_change_risk_reward_blockers.csv`.
- Current expected status is `vol_targeted_growth_risk_reward_evidence_created_manual_review_required`.
- Saved metrics show the volatility 15/20 candidate leading QQQ100 on CAGR, Sharpe, MaxDD, and Calmar, but the comparison is not a fresh apples-to-apples regeneration. Source mismatch, component, stress, cost, split, exposure, and formal proposal evidence remain blockers; QQQ100 remains the seed and no displacement, order instruction, execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change drawdown/stress review comes from `python bot.py --vol-targeted-growth-seed-change-drawdown-stress-review`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-drawdown-stress-review`:

- It writes `data/vol_targeted_growth_seed_change_drawdown_stress_review.csv`, `data/vol_targeted_growth_seed_change_drawdown_stress_summary.csv`, `data/vol_targeted_growth_seed_change_drawdown_stress_evidence.csv`, and `data/vol_targeted_growth_seed_change_drawdown_stress_blockers.csv`.
- Current expected status is `vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required`.
- Saved MaxDD favors the volatility 15/20 candidate over QQQ100, but the evidence is not a fresh apples-to-apples drawdown-window/stress regeneration. Stress-window evidence remains incomplete; QQQ100 remains the seed and no displacement, order instruction, execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change cost/turnover review comes from `python bot.py --vol-targeted-growth-seed-change-cost-turnover-review`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-cost-turnover-review`:

- It writes `data/vol_targeted_growth_seed_change_cost_turnover_review.csv`, `data/vol_targeted_growth_seed_change_cost_turnover_summary.csv`, `data/vol_targeted_growth_seed_change_cost_turnover_evidence.csv`, and `data/vol_targeted_growth_seed_change_cost_turnover_blockers.csv`.
- Current expected status is `vol_targeted_growth_cost_turnover_evidence_created_manual_review_required`.
- Exact saved turnover and cost-stress metrics are still missing for a seed-change proposal, so this evidence item is present but remains a manual-review blocker. QQQ100 remains the seed and no displacement, order instruction, execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change split-stability review comes from `python bot.py --vol-targeted-growth-seed-change-split-stability-review`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-split-stability-review`:

- It writes `data/vol_targeted_growth_seed_change_split_stability_review.csv`, `data/vol_targeted_growth_seed_change_split_stability_summary.csv`, `data/vol_targeted_growth_seed_change_split_stability_evidence.csv`, and `data/vol_targeted_growth_seed_change_split_stability_blockers.csv`.
- Current expected status is `vol_targeted_growth_split_stability_evidence_created_manual_review_required`.
- Saved split stability is supportive, but nearby-variant fragility and the remaining seed-change evidence items keep this manual-review only. QQQ100 remains the seed and no displacement, order instruction, execution, repeat order, or scheduling is approved.

The remaining volatility-targeted seed-change evidence reviews come from `python bot.py --vol-targeted-growth-seed-change-component-sleeve-review`, `python bot.py --vol-targeted-growth-seed-change-action-preview-design`, and `python bot.py --vol-targeted-growth-seed-change-proposal-document`, with matching saved display commands:

- They write saved component-sleeve, action-preview-design, and proposal-document checkpoint CSVs under `data/vol_targeted_growth_seed_change_*`.
- Current expected statuses are `vol_targeted_growth_component_sleeve_evidence_created_manual_review_required`, `vol_targeted_growth_action_preview_design_evidence_created_manual_review_required`, and `vol_targeted_growth_seed_change_proposal_document_draft_created_manual_review_required`.
- The proposal-document command is draft/checkpoint only. It does not create a formal seed-change proposal, does not displace QQQ100, and does not approve order instructions, execution, repeat orders, or scheduling. Broker exposure context remains a separate manual-review blocker.

The volatility-targeted growth seed-change broker-exposure review comes from `python bot.py --vol-targeted-growth-seed-change-broker-exposure-review`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-broker-exposure-review`:

- It writes `data/vol_targeted_growth_seed_change_broker_exposure_review.csv`, `data/vol_targeted_growth_seed_change_broker_exposure_summary.csv`, `data/vol_targeted_growth_seed_change_broker_exposure_evidence.csv`, and `data/vol_targeted_growth_seed_change_broker_exposure_blockers.csv`.
- Current expected status is `vol_targeted_growth_broker_exposure_evidence_created_manual_review_required`.
- It reviews saved broker-comparison output only. It does not call Alpaca or read positions now, and it does not approve a formal seed-change proposal, QQQ100 displacement, order instructions, execution, repeat orders, or scheduling.

The volatility-targeted growth seed-change manual-review checkpoint comes from `python bot.py --vol-targeted-growth-seed-change-manual-review-checkpoint`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-manual-review-checkpoint`:

- It writes `data/vol_targeted_growth_seed_change_manual_review_checkpoint.csv`, `data/vol_targeted_growth_seed_change_manual_review_summary.csv`, `data/vol_targeted_growth_seed_change_manual_review_evidence.csv`, and `data/vol_targeted_growth_seed_change_manual_review_blockers.csv`.
- Current expected status is `vol_targeted_growth_seed_change_ready_for_formal_proposal_manual_review`.
- This means the saved evidence pack can move to human formal-proposal review. It does not create a formal proposal, displace QQQ100, add action-preview implementation, create order instructions, approve execution, approve repeat orders, or approve scheduling.

The volatility-targeted growth formal seed-change proposal comes from `python bot.py --vol-targeted-growth-formal-seed-change-proposal`, with saved display through `python bot.py --show-vol-targeted-growth-formal-seed-change-proposal`:

- It writes `data/vol_targeted_growth_formal_seed_change_proposal.csv`, `data/vol_targeted_growth_formal_seed_change_proposal_summary.csv`, `data/vol_targeted_growth_formal_seed_change_proposal_evidence.csv`, `data/vol_targeted_growth_formal_seed_change_proposal_approvals.csv`, and `data/vol_targeted_growth_formal_seed_change_proposal_blockers.csv`.
- Current expected status is `vol_targeted_growth_formal_seed_change_proposal_created_manual_approval_required`.
- This creates the proposal document for human review only. Manual approval is not recorded, QQQ100 remains the seed, and no action-preview implementation, order instruction, paper execution, live execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change manual approval record comes from `python bot.py --vol-targeted-growth-seed-change-manual-approval-record`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-manual-approval-record`:

- It writes `data/vol_targeted_growth_seed_change_manual_approval_record.csv`, `data/vol_targeted_growth_seed_change_manual_approval_summary.csv`, `data/vol_targeted_growth_seed_change_manual_approval_evidence.csv`, and `data/vol_targeted_growth_seed_change_manual_approval_blockers.csv`.
- Current expected status is `vol_targeted_growth_seed_change_manual_approval_recorded_implementation_required`.
- This records manual approval for the next implementation-design checkpoint only. QQQ100 remains the active seed until a separate implementation change is reviewed, and no action-preview implementation, order instruction, paper execution, live execution, repeat order, or scheduling is approved.

The volatility-targeted growth seed-change implementation design comes from `python bot.py --vol-targeted-growth-seed-change-implementation-design`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-implementation-design`:

- It writes `data/vol_targeted_growth_seed_change_implementation_design.csv`, `data/vol_targeted_growth_seed_change_implementation_design_summary.csv`, `data/vol_targeted_growth_seed_change_implementation_design_evidence.csv`, and `data/vol_targeted_growth_seed_change_implementation_design_blockers.csv`.
- Current expected status is `vol_targeted_growth_seed_change_implementation_design_created_manual_review_required`.
- This describes the future code-change boundaries for a possible seed switch. It does not change the active seed, displace QQQ100, add action-preview implementation, create order instructions, approve paper execution, approve live execution, approve repeat orders, or approve scheduling.

The volatility-targeted growth seed-change dry-run diff comes from `python bot.py --vol-targeted-growth-seed-change-dry-run-diff`, with saved display through `python bot.py --show-vol-targeted-growth-seed-change-dry-run-diff`:

- It writes `data/vol_targeted_growth_seed_change_dry_run_diff.csv`, `data/vol_targeted_growth_seed_change_dry_run_diff_summary.csv`, `data/vol_targeted_growth_seed_change_dry_run_diff_evidence.csv`, and `data/vol_targeted_growth_seed_change_dry_run_diff_blockers.csv`.
- Current expected status is `vol_targeted_growth_seed_change_dry_run_diff_created_manual_review_required`.
- This lists the future files/areas that would need review for a seed switch. It does not modify those files, change the active seed, displace QQQ100, add action-preview implementation, create order instructions, approve paper execution, approve live execution, approve repeat orders, or approve scheduling.
- `python scripts\verify_vol_targeted_growth_seed_switch_status_only.py` verifies the implemented status-only report seed switch: volatility-targeted growth is the active report/status seed, QQQ100 remains previous-seed context, and order, execution, repeat-order, and scheduling approvals remain false.

Volatility-targeted growth is the current report/status seed after the status-only switch; QQQ100 remains previous-seed context and no execution or scheduling is approved.

The volatility-targeted growth active-seed readiness report comes from `python bot.py --vol-targeted-growth-active-seed-readiness`, with saved display through `python bot.py --show-vol-targeted-growth-active-seed-readiness`:

- It writes `data/vol_targeted_growth_active_seed_readiness.csv`, `data/vol_targeted_growth_active_seed_readiness_summary.csv`, `data/vol_targeted_growth_active_seed_readiness_evidence.csv`, and `data/vol_targeted_growth_active_seed_readiness_blockers.csv`.
- Expected ready status is `vol_targeted_growth_active_seed_monitoring_ready_manual_review_required` when saved monitoring/status reports and supporting evidence consistently point at `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE`.
- If saved evidence is missing or stale, expected status is `vol_targeted_growth_active_seed_monitoring_incomplete_manual_review_required`.
- This is monitoring/readiness only. It does not call Alpaca, refresh yfinance data, create action preview, create order instructions, approve execution, approve follow-up/repeat orders, or approve scheduling.
- `python bot.py --vps-daily-monitoring-summary` now includes a saved-output-only "Volatility active-seed readiness" section, so Telegram/status output can show the active seed readiness state without adding a separate runtime cron command.
- `python scripts\verify_vol_targeted_growth_seed_change_chain_checkpoint.py` verifies the saved seed-change review ladder, the implemented status-only seed switch, and active-seed readiness while preserving false order, execution, repeat-order, and scheduling approvals.

The volatility-targeted growth paper-live review bundle comes from three saved-output/manual-review checkpoints:

- `python bot.py --vol-targeted-growth-paper-live-manual-approval-gate`, with saved display through `python bot.py --show-vol-targeted-growth-paper-live-manual-approval-gate`.
- `python bot.py --vol-targeted-growth-paper-live-action-preview-pack`, with saved display through `python bot.py --show-vol-targeted-growth-paper-live-action-preview-pack`.
- `python bot.py --vol-targeted-growth-broker-comparison-reconciliation`, with saved display through `python bot.py --show-vol-targeted-growth-broker-comparison-reconciliation`.
- These checkpoints package the active seed gate, saved action-preview context, and saved broker-comparison evidence for review only. They do not call Alpaca, read positions, refresh market data, create order instructions, approve paper-live candidacy, approve execution, approve repeat/follow-up orders, or approve scheduling.

The volatility-targeted growth paper-live candidate approval record comes from `python bot.py --vol-targeted-growth-paper-live-candidate-approval-record`, with saved display through `python bot.py --show-vol-targeted-growth-paper-live-candidate-approval-record`:

- It records approval for paper-live candidate discussion only.
- `paper_live_candidate_discussion_approved=True`, but `paper_live_candidate_approved=False`, `execution_approved=False`, `paper_execution_approved=False`, `followup_order_approved=False`, `repeat_execution_approved=False`, and `scheduling_approved=False`.
- The required next step is allocation-cap and sleeve-mapping policy design before any order-design discussion.

The volatility-targeted growth allocation-cap and sleeve-mapping policy comes from `python bot.py --vol-targeted-growth-allocation-cap-sleeve-mapping-policy`, with saved display through `python bot.py --show-vol-targeted-growth-allocation-cap-sleeve-mapping-policy`:

- Current expected status is `vol_targeted_growth_allocation_cap_sleeve_mapping_policy_created_manual_review_required`.
- It documents a design boundary where executable allocation remains zero until a separate execution design exists.
- QQQ can be reviewed later as the only obvious single-symbol proxy; high-growth and crypto remain blocked/research-only, and defensive remains unmapped/manual-review.
- `allocation_cap_approved=False`, `sleeve_mapping_approved=False`, `target_position_design_approved=False`, `order_instructions_created=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

The volatility-targeted growth non-executable target-position plan comes from `python bot.py --vol-targeted-growth-non-executable-target-position-plan`, with saved display through `python bot.py --show-vol-targeted-growth-non-executable-target-position-plan`:

- Current expected status is `vol_targeted_growth_non_executable_target_position_plan_created_manual_review_required`.
- It documents target context for manual review only: QQQ is review-only with no order quantity, high-growth and crypto stay blocked/research-only, and defensive remains unmapped.
- `target_position_design_approved=False`, `executable_target_positions_created=False`, `order_instructions_created=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

The volatility-targeted growth order-ticket boundary design comes from `python bot.py --vol-targeted-growth-order-ticket-boundary-design`, with saved display through `python bot.py --show-vol-targeted-growth-order-ticket-boundary-design`:

- Current expected status is `vol_targeted_growth_order_ticket_boundary_design_created_manual_review_required`.
- It documents forbidden ticket fields and keeps QQQ as review-only with no side or quantity; high-growth and crypto stay blocked, and defensive remains unmapped.
- `order_ticket_design_approved=False`, `executable_order_ticket_created=False`, `order_instructions_created=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

The volatility-targeted growth executable ticket prerequisites review comes from `python bot.py --vol-targeted-growth-executable-ticket-prerequisites-review`, with saved display through `python bot.py --show-vol-targeted-growth-executable-ticket-prerequisites-review`:

- Current expected status is `vol_targeted_growth_executable_ticket_prerequisites_review_created_manual_review_required`.
- It lists the missing approvals and evidence before any future executable ticket design could be discussed: explicit execution-design approval, fresh read-only broker state, allocation/control approval, and component sleeve promotion remain missing.
- `executable_ticket_prerequisites_met=False`, `executable_ticket_design_allowed=False`, `executable_order_ticket_created=False`, `order_instructions_created=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

The volatility-targeted growth executable ticket gap list comes from `python bot.py --vol-targeted-growth-executable-ticket-gap-list`, with saved display through `python bot.py --show-vol-targeted-growth-executable-ticket-gap-list`:

- Current expected status is `vol_targeted_growth_executable_ticket_gap_list_execution_blocked_manual_review_required` with `final_ticket_design_decision=EXECUTABLE_TICKET_DESIGN_NOT_READY`.
- It turns the saved prerequisite review, execution blocker rollup, and go/no-go dashboard into a concise list of remaining gaps before any executable ticket design discussion.
- `python bot.py --vps-daily-monitoring-summary` now includes a saved-output-only "Volatility executable ticket gap list" section when the gap-list summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.
- It does not call Alpaca, read positions, create order fields, create executable tickets, approve execution, approve paper execution, approve live trading, or approve scheduling.

The volatility-targeted growth manual execution-design approval gate comes from `python bot.py --vol-targeted-growth-manual-execution-design-approval-gate`, with saved display through `python bot.py --show-vol-targeted-growth-manual-execution-design-approval-gate`:

- Current expected status is `vol_targeted_growth_manual_execution_design_approval_gate_not_approved` with `final_approval_gate_decision=MANUAL_EXECUTION_DESIGN_APPROVAL_NOT_RECORDED`.
- It defines the wording and scope a future explicit approval prompt would need before non-submitting executable ticket design could be discussed.
- `python bot.py --vps-daily-monitoring-summary` now includes a saved-output-only "Volatility manual execution-design approval gate" section when the approval-gate summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.
- It does not record approval, call Alpaca, read positions, create order fields, create executable tickets, approve execution, approve paper execution, approve live trading, or approve scheduling.

The volatility-targeted growth non-submitting ticket schema design comes from `python bot.py --vol-targeted-growth-non-submitting-ticket-schema-design`, with saved display through `python bot.py --show-vol-targeted-growth-non-submitting-ticket-schema-design`:

- Current expected status is `vol_targeted_growth_non_submitting_ticket_schema_design_created_manual_review_required` with `final_schema_design_decision=NON_SUBMITTING_TICKET_SCHEMA_DESIGNED_NO_TICKET_CREATED`.
- `python bot.py --vps-daily-monitoring-summary` now includes a saved-output-only "Volatility non-submitting ticket schema design" section when the schema-design summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.

The volatility-targeted growth non-submitting ticket-instance design comes from `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-design`, with saved display through `python bot.py --show-vol-targeted-growth-non-submitting-ticket-instance-design`:

- Current expected status is `vol_targeted_growth_non_submitting_ticket_instance_design_created_manual_review_required` with `final_ticket_instance_design_decision=NON_SUBMITTING_TICKET_INSTANCE_DESIGNED_NO_ORDER_VALUES`.
- The design creates a draft ticket shape only. It keeps side, quantity, order type, time-in-force, account reference, and broker order id blank, and keeps `ticket_instance_created=False`, `executable_ticket_created=False`, `order_values_populated=False`, `execution_approved=False`, and `scheduling_approved=False`.
- `python bot.py --vps-daily-monitoring-summary` includes a saved-output-only "Volatility non-submitting ticket-instance design" section when the summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.

The volatility-targeted growth fresh broker pre-ticket gate design comes from `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-design`, with saved display through `python bot.py --show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design`:

- Current expected status is `vol_targeted_growth_fresh_broker_pre_ticket_gate_design_created_manual_review_required` with `final_pre_ticket_gate_design_decision=FRESH_BROKER_PRE_TICKET_GATE_DESIGNED_NOT_RUN`.
- The design documents the future read-only broker gate, but it does not run the gate, call Alpaca, read positions, populate order values, create tickets, approve execution, or approve scheduling.
- `python bot.py --vps-daily-monitoring-summary` includes a saved-output-only "Volatility fresh broker pre-ticket gate design" section when the summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.

The volatility-targeted growth fresh broker pre-ticket gate run-readiness checkpoint comes from `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness`, with saved display through `python bot.py --show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness`:

- Current expected ready status is `vol_targeted_growth_fresh_broker_pre_ticket_gate_run_readiness_ready_to_request_manual_readonly_approval` with `final_pre_ticket_gate_run_readiness_decision=READY_TO_REQUEST_EXPLICIT_READONLY_ALPACA_APPROVAL` when the saved design chain is complete.
- Readiness to request approval is not approval to run. The checkpoint keeps `readonly_alpaca_run_approved=False`, `fresh_broker_pre_ticket_gate_run=False`, `broker_positions_read=False`, `order_values_populated=False`, `execution_approved=False`, and `scheduling_approved=False`.
- `python bot.py --vps-daily-monitoring-summary` includes a saved-output-only "Volatility fresh broker pre-ticket gate run-readiness" section when the summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.
- It defines future ticket schema fields for manual review after explicit user approval for design work, while keeping `ticket_instance_created=False` and `order_values_populated=False`.
- It does not call Alpaca, read positions, create a ticket instance, populate side/quantity/order-type/time-in-force values, submit orders, approve execution, approve paper execution, approve live trading, or approve scheduling.

The volatility-targeted growth fresh broker pre-ticket gate run comes from `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run --confirm-readonly-alpaca-check`, with saved display through `python bot.py --show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run`:

- It may run only with explicit read-only Alpaca confirmation. Without `--confirm-readonly-alpaca-check`, it records `readonly_confirmation_missing` and does not read broker positions.
- With confirmation, it reads paper positions through the existing read-only broker-position helper and saves counts/context only for manual review.
- The expected successful status is `vol_targeted_growth_fresh_broker_pre_ticket_gate_run_completed_readonly_manual_review_required`.
- The daily VPS monitoring summary now includes a saved-output-only "Volatility fresh broker pre-ticket gate run" section. Missing saved output is a monitoring issue only.
- It keeps `ticket_instance_created=False`, `executable_ticket_created=False`, `order_values_populated=False`, `order_instructions_created=False`, `orders_submitted=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

The volatility-targeted growth post-gate review comes from `python bot.py --vol-targeted-growth-post-gate-review`, with saved display through `python bot.py --show-vol-targeted-growth-post-gate-review`:

- It reads saved gate-run CSV output only. It does not call Alpaca again, read positions, refresh yfinance, create tickets, populate order values, submit orders, approve execution, or approve scheduling.
- When saved broker context exists, the expected status is `vol_targeted_growth_post_gate_review_manual_review_required` with `final_post_gate_review_decision=FRESH_BROKER_CONTEXT_SAVED_TICKET_VALUES_NOT_APPROVED`.
- The paper-live go/no-go dashboard now includes this post-gate status and still keeps `NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY`.

The volatility-targeted growth manual ticket-value design comes from `python bot.py --vol-targeted-growth-manual-ticket-value-design`, with saved display through `python bot.py --show-vol-targeted-growth-manual-ticket-value-design`:

- It is saved-output/design-only and does not call Alpaca, read positions, refresh market data, create executable tickets, submit orders, approve execution, or approve scheduling.
- It documents the fields that would need future manual values, but keeps order side, order quantity, order type, time-in-force, account reference, and broker order id blank/blocked.
- Expected status is `vol_targeted_growth_manual_ticket_value_design_manual_review_required` with `final_ticket_value_design_decision=TICKET_VALUE_DESIGN_REVIEW_ONLY_VALUES_NOT_APPROVED`.
- The paper-live go/no-go dashboard now includes this ticket-value design status and still keeps `NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY`.

The volatility-targeted growth executable-ticket closeout checkpoints come from `python bot.py --vol-targeted-growth-executable-ticket-prerequisites-closeout` and `python bot.py --vol-targeted-growth-executable-ticket-approval-readiness`, with saved display through the matching `--show-...` commands:

- The prerequisites closeout records `EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED`.
- The approval-readiness checkpoint records `NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL`.
- The approval-criteria checkpoint comes from `python bot.py --vol-targeted-growth-executable-ticket-approval-criteria` and records `APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED`.
- The criteria resolution plan comes from `python bot.py --vol-targeted-growth-executable-ticket-criteria-resolution-plan` and records `CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED`.
- The criteria source review comes from `python bot.py --vol-targeted-growth-executable-ticket-criteria-source-review` and records `CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED`.
- The criteria blocker closeout review comes from `python bot.py --vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review` and records `CRITERIA_BLOCKERS_REVIEWED_NONE_CLOSED`.
- The first blocker-specific reviews come from `python bot.py --vol-targeted-growth-criteria-source-blocker-review`, `python bot.py --vol-targeted-growth-criteria-resolution-plan-blocker-review`, `python bot.py --vol-targeted-growth-approval-criteria-not-approval-blocker-review`, and `python bot.py --vol-targeted-growth-criteria-blocker-specific-review-rollup`; the rollup records `CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED`.
- The closeout-candidate reviews come from `python bot.py --vol-targeted-growth-criteria-source-closeout-candidate-review`, `python bot.py --vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review`, `python bot.py --vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review`, and `python bot.py --vol-targeted-growth-criteria-closeout-candidate-review-rollup`; the rollup records `CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED`.
- The criteria-source closeout approval wording checkpoint comes from `python bot.py --vol-targeted-growth-criteria-source-closeout-approval-wording`, with saved display through `python bot.py --show-vol-targeted-growth-criteria-source-closeout-approval-wording`. It stores the simple future phrase `I approve closing the criteria_source_reviewed blocker only.` and records `CRITERIA_SOURCE_CLOSEOUT_APPROVAL_WORDING_DEFINED_NOT_APPROVED`; this does not close the blocker or record approval.
- The criteria-source closeout record comes from `python bot.py --vol-targeted-growth-criteria-source-closeout-record`, with saved display through `python bot.py --show-vol-targeted-growth-criteria-source-closeout-record`. It records `CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY` for `criteria_source_reviewed` and leaves `criteria_resolution_plan_open`, `approval_criteria_not_approval`, ticket values, executable-ticket approval, execution, and scheduling blocked.
- The criteria-resolution-plan closeout wording and record come from `python bot.py --vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording` and `python bot.py --vol-targeted-growth-criteria-resolution-plan-closeout-record`. They close only `criteria_resolution_plan_open`, leaving `approval_criteria_not_approval`, ticket values, executable-ticket prerequisites, execution, and scheduling blocked.
- The approval-criteria closeout wording and record come from `python bot.py --vol-targeted-growth-approval-criteria-closeout-approval-wording` and `python bot.py --vol-targeted-growth-approval-criteria-closeout-record`. They close only `approval_criteria_not_approval`, leaving ticket values, executable-ticket prerequisites, execution, and scheduling blocked.
- The final ticket blockers closeout wording and record come from `python bot.py --vol-targeted-growth-final-ticket-blockers-closeout-approval-wording` and `python bot.py --vol-targeted-growth-final-ticket-blockers-closeout-record`. They close `ticket_values_not_approved` and `executable_ticket_prerequisites_not_met` as checklist blockers only; order values remain blank, no executable ticket is created, and execution/scheduling stay blocked.
- The execution blocker rollup and executable ticket gap list consume those closeout records as saved evidence. They now show `closed_blocker_count=5`, all five checklist blocker booleans true, `remaining_known_blockers_after_closeout=none`, and `largest_blocker=execution_not_approved`.
- The execution approval request readiness checkpoint comes from `python bot.py --vol-targeted-growth-execution-approval-request-readiness`, with saved display through `python bot.py --show-vol-targeted-growth-execution-approval-request-readiness`. It records `READY_FOR_SEPARATE_EXECUTION_APPROVAL_REQUEST_NOT_APPROVED`, meaning the next step may be asking a separate explicit human approval question. It does not ask or record approval and keeps ticket values, executable tickets, orders, execution, and scheduling false.
- These checkpoints are saved-output/report-only and do not call Alpaca, read positions, refresh market data, populate order values, create executable tickets, submit orders, approve execution, or approve scheduling.
- The paper-live go/no-go dashboard and VPS daily monitoring summary now surface these decisions as monitoring context only.

The volatility-targeted growth paper-live execution blocker rollup comes from `python bot.py --vol-targeted-growth-paper-live-execution-blocker-rollup`, with saved display through `python bot.py --show-vol-targeted-growth-paper-live-execution-blocker-rollup`:

- Current expected status is `vol_targeted_growth_paper_live_execution_blocker_rollup_created_manual_review_required`.
- It summarizes the saved paper-live chain from manual gate through ticket prerequisites so monitoring can show the active blocker state in one place.
- `execution_blocker_rollup_cleared=False`, `executable_ticket_prerequisites_met=False`, `executable_ticket_design_allowed=False`, `order_instructions_created=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.
- `python bot.py --vps-daily-monitoring-summary` now includes a saved-output-only "Volatility paper-live execution blocker rollup" section; it does not add a separate cron command or approve execution.

The paper-live go/no-go dashboard comes from `python bot.py --paper-live-go-no-go-dashboard`, with saved display through `python bot.py --show-paper-live-go-no-go-dashboard`:

- It writes `data/paper_live_go_no_go_dashboard.csv`, `data/paper_live_go_no_go_dashboard_summary.csv`, `data/paper_live_go_no_go_dashboard_blockers.csv`, and `data/paper_live_go_no_go_dashboard_evidence.csv`.
- Current expected status is `paper_live_go_no_go_dashboard_execution_blocked_monitor_only` with `final_go_no_go_decision=NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY`.
- It summarizes QQQ100 no-action state, active volatility blocker state, executable-ticket closeout/readiness/criteria/resolution/source-review/blocker-review chain, paper-live checklist phase, and VPS monitoring assumptions in one saved-output view.
- It does not call Alpaca, read positions, create executable tickets, create order instructions, approve execution, approve paper execution, or approve scheduling.
- `python bot.py --vps-daily-monitoring-summary` now includes a saved-output-only "Paper-live go/no-go dashboard" section when the dashboard summary exists; if it is missing, the daily summary reports the missing saved output as a monitoring issue only.

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
- `python bot.py --show-current-research-state` is a compact saved-output-only terminal display helper for the multi-sleeve research state. It reads saved QQQ100 recovered-reference, high-growth stream, crypto stream, multi-sleeve portfolio, crypto-review, canonical lead-state, and high-growth drawdown decomposition CSVs where available, shows the current QQQ100 reference, high-growth sleeve, crypto sleeve, multi-sleeve candidate, canonical research lead candidate, drawdown watch context, and safety state, labels missing saved outputs as `missing_saved_output`, does not refresh market data, does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.
- `python bot.py --project-research-state-quality-report` writes `data/project_research_state_quality_report.csv`. It reads saved project research state only, checks freshness, required fields, and false approval flags, and reports warning/blocker rows for stale, missing, or non-false approval states. It does not approve scheduling or execution.
- `python bot.py --crypto-return-streams` writes `data/crypto_return_streams.csv`, `data/crypto_return_stream_metrics.csv`, `data/crypto_return_stream_summary.csv`, and `data/crypto_return_stream_blockers.csv`; `python bot.py --show-crypto-return-streams` reads the saved summary only. The generator reuses the existing BTC `crypto_buy_above_200_with_vol_gate` rule, ETH `crypto_buy_above_200_exit_below_200` rule, and fixed crypto research cost assumptions. LTC remains paused/not active. The streams are for multi-sleeve research only and do not approve crypto execution, preview promotion, paper execution, scheduling, shorting, margin, leverage, or Alpaca/order paths.
- `python bot.py --stock-etf-paper-execution-readiness-report` writes `data/stock_etf_paper_execution_readiness_report.csv`. It is a saved-data/static-source discussion checkpoint for whether the current stock/ETF research lead is ready even to discuss a future manually reviewed Alpaca paper-execution design. Current expected status is conservative: `qqq_100_trend_gate` is research-only, the adaptive QQQ candidate is an ambitious alternative rather than an execution route, the higher-drawdown QQQ leverage reference remains rejected, and preview, execution eligibility, kill-switch, portfolio-risk, crypto-out-of-scope, and scheduling boundaries still block or require manual review. It does not read credentials, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve paper execution.
- `python bot.py --alpaca-paper-readiness-report` writes `data/alpaca_paper_readiness_report.csv`. Default mode is static/no-network and checks safe paper prerequisites without reading config contents, calling Alpaca, reading positions, creating orders, writing SQLite `trade_log`, sending alerts, scheduling anything, or approving execution. `--confirm-readonly-alpaca-check` is implemented for a later explicit read-only Alpaca paper account/status check only; it must not be treated as a smoke test or execution approval.
- `python bot.py --alpaca-connectivity-diagnostics` writes `data/alpaca_connectivity_diagnostics.csv`, `data/alpaca_connectivity_diagnostics_summary.csv`, and `data/alpaca_connectivity_diagnostics_blockers.csv`; `python bot.py --show-alpaca-connectivity-diagnostics` displays the saved summary only. The diagnostics use DNS and raw TCP 443 socket checks for Alpaca API/public hosts and general HTTPS control hosts. They document the current VPS/laptop distinction where the VPS times out to `paper-api.alpaca.markets:443` and `api.alpaca.markets:443` while the laptop and normal HTTPS hosts work. They do not load config, use credentials, call authenticated Alpaca APIs, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve execution.
- `python bot.py --paper-order-smoke-test-readiness-pack` writes `data/paper_order_smoke_test_readiness_pack.csv`. It is a saved-data/static readiness pack for deciding whether one tiny manually confirmed Alpaca paper-order smoke test can even be discussed. It may record a future manual-review-only template such as AAPL buy 1, but it does not print a pasteable order command, call Alpaca, read positions, load config contents, create orders, write SQLite `trade_log`, send alerts, schedule anything, connect a strategy to execution, or approve order execution.
- `python bot.py --paper-order-smoke-test-live-preflight --ticker AAPL --side buy --quantity 1` writes `data/paper_order_smoke_test_live_preflight.csv`. Default mode is non-confirmed and does not call Alpaca; it validates the proposed manual-review-only ticker/side/quantity and summarises saved readiness context. Confirmed read-only mode is implemented behind `--confirm-readonly-alpaca-check` for account, market clock, asset, and open-order status checks only, and must still not create, submit, cancel, replace, or preview executable orders.
- `python bot.py --paper-order-smoke-test-postcheck --ticker AAPL --side buy --quantity 1` writes `data/paper_order_smoke_test_postcheck.csv`. Default mode is saved-data/static only and does not call Alpaca. Confirmed read-only mode is implemented behind `--confirm-readonly-alpaca-check` to summarise recent orders, open orders, account block flags, and ticker position direction/quantity without printing sensitive identifiers. It never creates follow-up orders or approves execution.
- `python bot.py --future-refresh-cron-readiness-pack` writes `data/future_refresh_cron_readiness_pack.csv`. It is a static/docs/report-only pack for tomorrow's separate manual review of a possible safe refresh/reporting Hermes cron. It does not create, edit, trigger, delete, enable, or schedule cron jobs, and it does not approve scheduling or execution.
- `docs/HERMES_PAUSED_STATUS_CRON_CHECKPOINT.md` now records the enabled Hermes status job definition `paused-vps-safe-paper-bot-status-check` with job ID `66c8a5bb438e`. It is `enabled=true`, `state=scheduled`, uses schedule `*/30 14-20 * * 1-5`, next run `2026-06-29T14:00:00+01:00`, and has not yet run by cron. Its sequence is repo safety, Hermes cron readiness, `verify_vps_daily_monitoring_summary.py`, and `--vps-daily-monitoring-summary`; standalone active-seed/paper-live report commands are intentionally omitted because the daily summary includes active-seed readiness. This is status/report monitoring only and does not approve refresh automation, broker reads, order-capable commands, paper execution, live trading, repeat orders, or follow-up orders. Verify with `python scripts\verify_hermes_paused_status_cron_checkpoint.py`.
- `docs/HERMES_STATUS_CRON_ENABLEMENT_CHECKLIST.md` records the market-hours status cron enablement checkpoint for that job. It documents the `*/30 14-20 * * 1-5` weekday UK-local status cadence, but it does not approve execution, paper execution, refresh jobs, broker reads, position reads, market-data refresh, or any order-capable command. Verify with `python scripts\verify_hermes_status_cron_enablement_checklist.py`.
- `docs/HERMES_FIRST_RUN_CHECKLIST.md` records what to check when the first scheduled Telegram/status result arrives on `2026-06-29T14:00:00+01:00`. It separates healthy, warning, and failure/stop-condition outputs, includes a first-run result log template, and preserves that warnings are monitoring/reporting issues only, not approval for broker reads, refresh jobs, paper execution, live trading, repeat orders, or follow-up orders. Verify with `python scripts\verify_hermes_first_run_checklist.py`.
- `docs/PAPER_ORDER_SMOKE_TEST_RUNBOOK.md` is the Monday manual paper-order smoke-test runbook. `python bot.py --paper-order-smoke-test-runbook-check` writes `data/paper_order_smoke_test_runbook_check.csv` and verifies the runbook remains static, manual-review-only, and false for smoke-test order, execution, scheduling, and follow-up order approval.
- `python bot.py --paper-smoke-test-kill-switch-diagnosis` writes `data/paper_smoke_test_kill_switch_diagnosis.csv`, `data/paper_smoke_test_kill_switch_diagnosis_summary.csv`, `data/paper_smoke_test_kill_switch_diagnosis_blockers.csv`, and `data/paper_smoke_test_kill_switch_diagnosis_recommendations.csv`; `python bot.py --show-paper-smoke-test-kill-switch-diagnosis` reads the saved summary only. It diagnoses why the manual AAPL paper smoke-test attempt was blocked by the kill-switch gate, separates connectivity-smoke-test blockers from broader strategy-execution blockers, preserves that no order was submitted, and does not weaken `--paper-order-test`, call Alpaca, read positions, write SQLite `trade_log`, send alerts, change config, schedule anything, or approve smoke-test execution.
- The manual `--paper-order-test` path now has a narrow connectivity-only smoke-test gate for the exact `AAPL buy 1 --confirm-paper-order` template. It can allow only that one manual paper smoke test through broader strategy-execution blockers after saved/read-only live preflight is ready, market status is open, Alpaca paper mode and credentials are present, no open AAPL order exists, and no recent matching AAPL buy 1 order exists. It writes `data/paper_order_smoke_test_gate_report.csv`, `data/paper_order_smoke_test_gate_summary.csv`, and `data/paper_order_smoke_test_gate_blockers.csv` when the manual path is run. Normal bot, slow-SMA paper execution, QQQ100 preview/action-preview, strategy execution, scheduling, live trading, config defaults, and follow-up orders remain unapproved and unchanged.
- `BTC/USD`: useful but split-sensitive; keep monitoring.
- `ETH/USD`: useful but research-only; keep monitoring.
- `LTC/USD`: researched but not useful; pause.
- Saved crypto return streams can now create `btc_trend_vol_gate_research_sleeve`, `eth_trend_research_sleeve`, and the combined `crypto_btc_eth_research_sleeve` for research-only multi-sleeve testing.
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
- `python bot.py --vps-daily-monitoring-summary` is a concise terminal-only daily report for Telegram/manual checks. It summarizes safety reminders, lock-wrapped safe commands, promoted decision-state counts, defensive refresh step counts, saved paper-live QQQ100 monitoring state, saved-output freshness labels, false approval flags, final status of `healthy_monitoring_state`, `monitoring_warning`, or `monitoring_stale_or_missing_inputs`, and action fields `action_required`, `action_reason`, and `suggested_manual_action`. It does not refresh data, call Alpaca/yfinance/Discord, write SQLite `trade_log`, read config contents, create generated files, schedule anything, or approve execution.
- The current daily Hermes status cron exists as `paper-bot-vps-status-check` with job ID `345188fbb60c`. It runs daily at 10:10am UK local time with cron expression `10 10 * * *`, delivers to Telegram, uses script-only / no-agent mode, runs from `C:\dev\paper-trading-bot`, and executes `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, `.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py`, and `.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary`. Verified output is repo_safety PASS, hermes_cron_readiness PASS, vps_daily_monitoring_summary PASS, QQQ100 paper-live status aligned long one with repeat/follow-up orders unapproved, final_monitoring_status `healthy_monitoring_state`, action_required `no_action_required`, execution_approved false, scheduling_approved false, and freshness_warnings: none. This status cron does not run refresh commands, trade, approve scheduling beyond this one status job, approve execution, pull/commit/push code, or inspect/print config contents, secrets, logs, databases, or full generated CSV contents.
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
python scripts\verify_paper_live_monitoring_in_vps_summary.py
python scripts\verify_paper_live_checklist_status.py
python scripts\verify_paper_live_f6_f7_audit.py
python scripts\verify_paper_live_f6_f7_targeted_checks.py
python scripts\verify_paper_live_promotion_ladder_design.py
python scripts\verify_paper_live_multi_sleeve_roadmap.py
python scripts\verify_paper_live_next_phase_backlog.py
python scripts\verify_paper_live_multi_sleeve_evidence_gap.py
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
