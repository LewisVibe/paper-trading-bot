# Paper-Live Checklist

This checklist is the planned path for operating the bot with Alpaca paper trading only. It does not approve live trading, automated order scheduling, or broad strategy-to-execution wiring. Work through it in separate prompts and keep each step narrow.

## 1. Freeze The Current Baseline

- Pull latest `main`.
- Confirm repo safety passes.
- Confirm pytest passes.
- Confirm command inventory passes.
- Confirm normal `python bot.py` remains monitoring-only.
- Confirm paper execution remains separate and explicitly confirmed.
- Confirm Alpaca remains paper-only.
- Confirm no generated CSVs, logs, databases, charts, or secrets are staged.

## 2. Write The Paper-Live Policy

- Paper-live means Alpaca paper only, not live money.
- Normal `python bot.py` must remain monitoring-only.
- Paper execution must happen only through separate explicit commands.
- Do not schedule order-capable commands.
- Do not add live trading.
- Do not add shorting unless a separate design explicitly approves it later.
- Do not use the SMA or slow-SMA strategy as the paper-live strategy.
- Slow-SMA can remain preview, research, or manual testing only.

## 3. Close Remaining External Review Feedback

- F1: normal bot bypassing kill-switch is handled by making normal bot monitoring-only. Keep this locked.
- F3: manual sell oversell guard is implemented. Keep tests around it.
- F5: `paper_kill_switch_enabled` is implemented as real config/env state.
- F2: QQQ100 one-share alignment now enforces exactly zero or one QQQ share. More than one QQQ share blocks/manual review rather than silently counting as aligned or selling only one share.
- F6 still needs audit: previews must never silently assume flat when positions are unknown.
- F7 still needs audit: portfolio backtest starting-cash/accounting consistency needs a verifier before backtest results are used as promotion evidence.
- `bot.py` remains large. That is not a paper-live blocker if narrow execution stays safe, but it remains refactor debt.

## 4. Choose The First Paper-Live Candidate

- Use `qqq_100_trend_gate` as the clean main stock/ETF paper candidate.
- Keep `codex_qqq_adaptive_trend_exposure` as an ambitious alternative only.
- Keep `qqq_150_trend_gate` rejected.
- Keep the high-growth stock branch research-only.
- Keep crypto research-only.
- Keep SMA/slow-SMA out of paper-live promotion.

## 5. Create A Strategy Promotion Gate

- Define what promoted to paper-live candidate means.
- Implemented checkpoint: `python bot.py --paper-live-promotion-gate`.
- Saved display: `python bot.py --show-paper-live-promotion-gate`.
- Outputs: `data/paper_live_promotion_gate.csv`, `data/paper_live_promotion_gate_summary.csv`, `data/paper_live_promotion_gate_blockers.csv`, and `data/paper_live_promotion_gate_evidence.csv`.
- `paper_live_candidate=True` means manual candidate-discussion status only.
- Require saved research decision evidence.
- Require saved preview signal evidence.
- Require saved action preview evidence.
- Require portfolio/risk review evidence.
- Require execution-readiness evidence.
- Require no open blockers.
- Require explicit human approval before any paper execution command can be used.
- Promotion must not create orders.
- Promotion may output `paper_live_candidate=True`, but general `execution_approved` must remain false until the actual manual execution command.
- `paper_execution_approved` and `scheduling_approved` must also remain false.

## 6. Maintain QQQ100 Exact Alignment Before Further QQQ Paper Orders

- Desired long plus zero QQQ shares: buy one may be allowed after all gates pass.
- Desired long plus exactly one QQQ share: already aligned.
- Desired long plus more than one QQQ share: block/manual review. Do not reduce to one unless a separate explicit design is approved later.
- Desired flat plus zero QQQ shares: already flat.
- Desired flat plus exactly one QQQ share: sell one may be allowed after all gates pass.
- Desired flat plus more than one QQQ share: block/manual review. Do not sell all unless a separate explicit design is approved later.
- Verifier and pytest coverage must cover all six cases.

## 7. Build The Paper-Live Readiness Report

Implemented checkpoint: `python bot.py --paper-live-readiness-report`.

Saved display: `python bot.py --show-paper-live-readiness-report`.

Outputs: `data/paper_live_readiness_report.csv`, `data/paper_live_readiness_summary.csv`, `data/paper_live_readiness_blockers.csv`, and `data/paper_live_readiness_evidence.csv`.

The readiness report should check:

- repo safety,
- Alpaca paper mode,
- normal bot monitoring-only boundary,
- QQQ100 exact alignment,
- recent duplicate-order checks,
- open-order checks,
- position readability,
- max one-share policy,
- no scheduling,
- no SMA promotion,
- no high-growth promotion,
- no crypto promotion.

The readiness report is manual-review status only. It must preserve `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, and `live_trading_approved=false`.

## 8. Keep Manual Paper Execution Narrow

The QQQ100 paper command should stay limited to:

- fixed ticker: `QQQ`,
- fixed strategy: `qqq_100_trend_gate`,
- fixed quantity policy: maximum one share,
- explicit confirmation required,
- Alpaca paper only,
- no live mode,
- no shorting,
- no strategy basket execution.

It must write result, summary, blockers, and postcheck files on every path.

## 9. Add Post-Execution Verification

After any manual QQQ100 paper order:

- read broker order history,
- read QQQ paper position,
- confirm order status,
- confirm alignment,
- write postcheck files,
- never create, cancel, replace, or submit follow-up orders.

If postcheck cannot verify the result, mark manual review required.

## 10. Create The Paper-Live State Summary

Implemented checkpoint: `python bot.py --paper-live-state-summary`.

Saved display: `python bot.py --show-paper-live-state-summary`.

Outputs: `data/paper_live_state_summary.csv`, `data/paper_live_state_components.csv`, `data/paper_live_state_blockers.csv`, and `data/paper_live_state_evidence.csv`.

Add one saved-output command that answers:

- active paper-monitoring strategy,
- current desired state,
- current paper position,
- last paper order result,
- current alignment state,
- blockers,
- execution and scheduling flags.

This should be the daily check before touching any paper order command.

The state summary is not a readiness upgrade and must preserve `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

Implemented reconciliation checkpoint: `python bot.py --paper-live-evidence-audit`.

Saved display: `python bot.py --show-paper-live-evidence-audit`.

Outputs: `data/paper_live_evidence_audit.csv`, `data/paper_live_evidence_audit_summary.csv`, `data/paper_live_evidence_audit_blockers.csv`, and `data/paper_live_evidence_audit_evidence.csv`.

The audit reads saved QQQ100 preview/action/postcheck/order/state evidence, lists exact missing saved files or fields through `exact_missing_saved_evidence`, and can confirm that saved evidence is reconciled while still keeping follow-up/repeat order approval false.

The evidence audit does not call Alpaca, read live positions, refresh market data, create order instructions, or approve execution, paper execution, scheduling, live trading, or follow-up orders.

Implemented postcheck runbook checkpoint: `python bot.py --qqq100-postcheck-readiness-report`.

Saved display: `python bot.py --show-qqq100-postcheck-readiness-report`.

Outputs: `data/qqq100_postcheck_readiness_report.csv`, `data/qqq100_postcheck_readiness_summary.csv`, `data/qqq100_postcheck_readiness_blockers.csv`, and `data/qqq100_postcheck_readiness_runbook.csv`.

This checkpoint documents that missing VPS quantity evidence must be generated later, if explicitly approved, only by `python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check`. It must not run postcheck itself, and it must keep all execution, paper execution, scheduling, live trading, and follow-up order approvals false.

Implemented follow-up/no-action policy checkpoint: `python bot.py --qqq100-followup-policy-report`.

Saved display: `python bot.py --show-qqq100-followup-policy-report`.

Outputs: `data/qqq100_followup_policy_report.csv`, `data/qqq100_followup_policy_summary.csv`, `data/qqq100_followup_policy_blockers.csv`, and `data/qqq100_followup_policy_evidence.csv`.

If desired state is `long` and saved QQQ position is long exactly one share, the policy status is `no_action_required_already_aligned`. This must not approve another buy, repeat execution, follow-up orders, scheduling, live trading, or executable order instructions.

## 11. Schedule Monitoring Only

- Implemented report-only monitoring checkpoint: `python bot.py --paper-live-monitoring-status`.
- Saved display: `python bot.py --show-paper-live-monitoring-status`.
- Outputs: `data/paper_live_monitoring_status.csv`, `data/paper_live_monitoring_components.csv`, and `data/paper_live_monitoring_blockers.csv`.
- This checkpoint may show `qqq_100_trend_gate` / `QQQ` aligned long one share with `no_action_required=True` and `recommended_next_step=hold_no_action_and_monitor_only`.
- `python bot.py --vps-monitoring-status` and `python bot.py --vps-daily-monitoring-summary` include the saved paper-live monitoring status when available, so the current status-only Hermes output can show aligned long one share without adding a new cron command.
- It does not create, edit, trigger, or schedule Hermes cron jobs and must preserve `never_schedule_order_capable_commands=True`.
- Hermes cron may run status/report commands only.
- Hermes cron must not run QQQ100 execution.
- Hermes cron must not run normal `python bot.py`.
- Hermes cron must not run slow-SMA execution.
- Hermes cron must not run paper-order tests.
- Scheduled output should say monitoring only and no orders.

Implemented checklist closeout checkpoint: `python bot.py --paper-live-checklist-status`.

Saved display: `python bot.py --show-paper-live-checklist-status`.

Outputs: `data/paper_live_checklist_status.csv`, `data/paper_live_checklist_status_summary.csv`, `data/paper_live_checklist_status_blockers.csv`, and `data/paper_live_checklist_status_evidence.csv`.

Current expected closeout status is `paper_live_checklist_current_qqq100_monitoring_phase_closed_out`: Steps 1-11 are complete or complete-for-current-QQQ100-monitoring-phase, QQQ100 is aligned long one share, no further QQQ order is needed now, repeat/follow-up orders remain blocked, and scheduling remains monitoring-only.

Implemented F6/F7 audit checkpoint: `python bot.py --paper-live-f6-f7-audit`.

Saved display: `python bot.py --show-paper-live-f6-f7-audit`.

Outputs: `data/paper_live_f6_f7_audit.csv`, `data/paper_live_f6_f7_audit_summary.csv`, `data/paper_live_f6_f7_audit_blockers.csv`, and `data/paper_live_f6_f7_audit_evidence.csv`.

Current expected audit status is `paper_live_f6_f7_audit_manual_review_required`: F6 confirms some loud position unknown / position unavailable boundaries but still needs future promotion-ladder review, and F7 requires starting-cash/accounting tests or verifiers before portfolio backtests are used as promotion evidence.

Implemented F6/F7 targeted checks verifier: `python scripts\verify_paper_live_f6_f7_targeted_checks.py`.

This no-network verifier exercises pure preview/action helpers so unknown positions stay loud and never silently become flat, aligned, or eligible. It also keeps portfolio backtests not promotion evidence until starting-cash/accounting consistency is proven. It does not approve execution, scheduling, multi-sleeve promotion, or generic promotion-ladder work.

Implemented generic promotion ladder design checkpoint: `python bot.py --paper-live-promotion-ladder-design`.

Saved display: `python bot.py --show-paper-live-promotion-ladder-design`.

Outputs: `data/paper_live_promotion_ladder_design.csv`, `data/paper_live_promotion_ladder_design_summary.csv`, `data/paper_live_promotion_ladder_design_blockers.csv`, and `data/paper_live_promotion_ladder_design_evidence.csv`.

Current expected design status is `paper_live_promotion_ladder_design_report_only`: QQQ100 is the only current ladder seed, QQQ100 remains monitor-only and aligned long one share, no repeat/follow-up QQQ order is approved, multi-sleeve is future-only, high-growth and crypto remain research-only, defensive sleeves remain future review only, no SMA or slow-SMA paper-live promotion is allowed, portfolio backtests are not promotion evidence until accounting consistency is proven, unknown positions block/manual-review, and no scheduled execution is allowed.

Implemented QQQ-led multi-sleeve roadmap checkpoint: `python bot.py --paper-live-multi-sleeve-roadmap`.

Saved display: `python bot.py --show-paper-live-multi-sleeve-roadmap`.

Outputs: `data/paper_live_multi_sleeve_roadmap.csv`, `data/paper_live_multi_sleeve_roadmap_summary.csv`, `data/paper_live_multi_sleeve_roadmap_blockers.csv`, and `data/paper_live_multi_sleeve_roadmap_evidence.csv`.

Current expected roadmap status is `paper_live_multi_sleeve_roadmap_report_only`: QQQ100 core remains the current monitor-only base and only current seed, defensive sleeve is future review only, high-growth remains research-only until concentration/drawdown/attribution review is complete, crypto remains research-only/capped/future-only with no crypto execution approved, and the allocator has no portfolio execution wiring, no order instructions, and no scheduled execution.

Implemented next-phase backlog checkpoint: `python bot.py --paper-live-next-phase-backlog`.

Saved display: `python bot.py --show-paper-live-next-phase-backlog`.

Outputs: `data/paper_live_next_phase_backlog.csv`, `data/paper_live_next_phase_backlog_summary.csv`, `data/paper_live_next_phase_backlog_blockers.csv`, and `data/paper_live_next_phase_backlog_evidence.csv`.

Current expected backlog status is `paper_live_next_phase_backlog_report_only`: QQQ100 core remains monitor-only/no-action, generic ladder implementation is future-only, F6/F7 requires loud unknown-position handling and portfolio accounting proof, defensive/high-growth/crypto/allocator work needs saved-output evidence review, and Monitoring/Hermes remains monitoring-only with order-capable commands never scheduled.

Implemented multi-sleeve evidence-gap audit checkpoint: `python bot.py --paper-live-multi-sleeve-evidence-gap`.

Saved display: `python bot.py --show-paper-live-multi-sleeve-evidence-gap`.

Outputs: `data/paper_live_multi_sleeve_evidence_gap.csv`, `data/paper_live_multi_sleeve_evidence_gap_summary.csv`, `data/paper_live_multi_sleeve_evidence_gap_blockers.csv`, and `data/paper_live_multi_sleeve_evidence_gap_evidence.csv`.

Current expected evidence-gap status is `paper_live_multi_sleeve_evidence_gap_manual_review_required`: the audit checks saved-output file presence only, treats missing saved outputs as blockers/manual-review items, and does not rerun research, refresh market data, promote sleeves, create action previews, create order instructions, wire portfolio execution, or schedule anything.

Implemented high-growth evidence-gap audit checkpoint: `python bot.py --paper-live-high-growth-evidence-gap`.

Saved display: `python bot.py --show-paper-live-high-growth-evidence-gap`.

Outputs: `data/paper_live_high_growth_evidence_gap.csv`, `data/paper_live_high_growth_evidence_gap_summary.csv`, `data/paper_live_high_growth_evidence_gap_blockers.csv`, and `data/paper_live_high_growth_evidence_gap_evidence.csv`.

Current expected high-growth evidence-gap status is `paper_live_high_growth_evidence_gap_manual_review_required`: the audit checks saved-output file presence only for saved high-growth lead evidence, concentration/top-contributor dependency evidence, drawdown evidence, attribution evidence, bias-risk warnings, and promotion readiness. No high-growth sleeve is promoted, no action previews or order instructions are created, no research is rerun, no market data is refreshed, and no portfolio execution or scheduling is implemented.

Implemented high-growth evidence quality review checkpoint: `python bot.py --paper-live-high-growth-evidence-quality`.

Saved display: `python bot.py --show-paper-live-high-growth-evidence-quality`.

Outputs: `data/paper_live_high_growth_evidence_quality.csv`, `data/paper_live_high_growth_evidence_quality_summary.csv`, `data/paper_live_high_growth_evidence_quality_blockers.csv`, and `data/paper_live_high_growth_evidence_quality_evidence.csv`.

Current expected high-growth quality status is `high_growth_evidence_quality_manual_review_required`: saved evidence may be present, but concentration/outlier, drawdown, attribution, survivorship/current-constituent, and promotion-readiness quality remain manual-review items. No high-growth preview candidate, paper-live candidate, action preview, order instruction, execution wiring, market refresh, broker call, or scheduling is approved.

Implemented high-growth manual-review decision checkpoint: `python bot.py --paper-live-high-growth-manual-review-decision`.

Saved display: `python bot.py --show-paper-live-high-growth-manual-review-decision`.

Outputs: `data/paper_live_high_growth_manual_review_decision.csv`, `data/paper_live_high_growth_manual_review_decision_summary.csv`, `data/paper_live_high_growth_manual_review_decision_blockers.csv`, and `data/paper_live_high_growth_manual_review_decision_evidence.csv`.

Current expected decision is `high_growth_remains_research_only_manual_review_required`: high-growth is not a preview candidate, not a paper-live candidate, and not promoted. QQQ100 remains the cleaner current paper-live monitor base. High-growth can be reconsidered later only with stronger concentration-control, component/drawdown attribution, split/cost, portfolio-accounting, F6/F7, and risk-policy evidence, with no order instructions or scheduling.

## 12. Build A Future Promotion System Later

Later, after QQQ100 is stable, build a generic promotion ladder:

- research candidate,
- preview candidate,
- paper-live candidate,
- manually executable candidate.

Start with QQQ100 only. Do not generalize too early.

## First Implementation Prompt

Use this as the next implementation prompt:

> Continue with F6/F7 audits after the exact QQQ100 one-share alignment verifier and tests pass. No order runs.

That is the highest-priority gap before treating the QQQ100 paper-live path as credible.
