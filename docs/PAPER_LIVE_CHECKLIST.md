# Paper-Live Checklist

This checklist is the planned path for operating the bot with Alpaca paper trading only. It does not approve live trading, automated order scheduling, or broad strategy-to-execution wiring. Work through it in separate prompts and keep each step narrow.

## Current Position And Remaining Path To Paper-Live

Current status:

- The active report/status seed is `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` / `MULTI_SLEEVE`.
- The previous QQQ100 seed context remains `qqq_100_trend_gate` / `QQQ`, with saved evidence showing long exactly one share and no follow-up/repeat order needed.
- The VPS/Hermes status job is monitoring-only and must remain status/report-only.
- The volatility seed has a non-submitting ticket schema design, a non-submitting ticket-instance design, a fresh broker pre-ticket gate design, a run-readiness checkpoint, a manual ticket-value design, and executable-ticket closeout/readiness/criteria/resolution-plan/source-review/blocker-review checkpoints, but no executable ticket instance, no populated order values, no broker refresh tied to a ticket, and no execution approval.
- High-growth, crypto, defensive, SMA, and slow-SMA remain excluded from paper-live execution.

Remaining steps, in order:

1. **Refresh local/VPS safety baseline.**
   - Run repo safety, command inventory, pytest, daily monitoring summary verifier, and the latest volatility ticket-schema verifier.
   - Do not run normal `python bot.py`.
   - Do not run any order-capable command.

2. **Confirm the market-hours read-only broker state.**
   - This requires a separate explicit approval prompt before running any Alpaca read-only command.
   - Candidate command, only after explicit approval:
     `.venv\Scripts\python.exe bot.py --vol-targeted-growth-broker-position-comparison --confirm-readonly-alpaca-check`
   - Purpose: confirm current Alpaca paper positions against saved target-sleeve context.
   - This must not create, submit, cancel, replace, or prepare orders.

3. **Reconcile broker comparison into saved paper-live evidence.**
   - Run saved-output reconciliation after the read-only broker comparison exists.
   - No new Alpaca call should happen in this step.
   - Confirm unknown/missing broker state remains loud and blocks.

4. **Review the non-submitting ticket schema.**
   - Confirm schema fields are acceptable for a future ticket instance.
   - Confirm `ticket_instance_created=False`, `order_values_populated=False`, `order_instructions_created=False`, and all execution/scheduling flags remain false.
   - Decide whether the schema needs changes before any ticket-instance design.

5. **Create a ticket-instance design checkpoint, still non-submitting.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-design`.
   - Saved display: `python bot.py --show-vol-targeted-growth-non-submitting-ticket-instance-design`.
   - It defines what a future ticket instance would look like, but keeps side, quantity, order type, time-in-force, account, and broker order ID unpopulated.
   - It does not call Alpaca, read positions, create orders, schedule anything, or approve execution.

6. **Create a fresh-read broker pre-ticket gate.**
   - Implemented design checkpoint: `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-design`.
   - Saved display: `python bot.py --show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design`.
   - The design is report-only and does not run Alpaca.
   - The future run is market-hours useful and requires explicit read-only Alpaca approval.
   - A future run should compare fresh broker state, saved target context, existing QQQ position, and multi-sleeve constraints immediately before any future ticket-instance discussion.
   - If broker state is unavailable, stale, mismatched, or ambiguous, it must block/manual-review.

6a. **Create a fresh-read broker pre-ticket gate run-readiness checkpoint.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness`.
   - Saved display: `python bot.py --show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness`.
   - The checkpoint may say the saved design chain is ready to request explicit read-only Alpaca approval.
   - It does not approve the read-only run, does not call Alpaca, does not read positions, does not create tickets, and does not approve execution.

6b. **Run the fresh-read broker pre-ticket gate only after explicit read-only approval.**
   - Implemented command: `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run --confirm-readonly-alpaca-check`.
   - Saved display: `python bot.py --show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run`.
   - The command may read Alpaca paper positions only with the confirmation flag.
   - It does not create tickets, populate side/quantity/order-type/time-in-force values, submit orders, or approve paper execution.
   - The next step after a successful read remains manual review before any ticket values or order design.

6c. **Review the saved fresh-broker context before ticket values.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-post-gate-review`.
   - Saved display: `python bot.py --show-vol-targeted-growth-post-gate-review`.
   - It reads saved gate-run outputs only and does not call Alpaca again.
   - It can confirm saved broker context exists, but it keeps ticket values, order instructions, paper execution, and scheduling blocked.

6d. **Create a manual ticket-value design checkpoint without values.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-manual-ticket-value-design`.
   - Saved display: `python bot.py --show-vol-targeted-growth-manual-ticket-value-design`.
   - It lists the fields that would need future manual values, but keeps side, quantity, order type, time-in-force, account reference, and broker order id blank/blocked.
   - It keeps `populated_ticket_value_count=0`, `order_values_populated=False`, `order_instructions_created=False`, `executable_ticket_created=False`, and all execution/scheduling flags false.

6e. **Close out executable-ticket prerequisites as still open.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-executable-ticket-prerequisites-closeout`.
   - Saved display: `python bot.py --show-vol-targeted-growth-executable-ticket-prerequisites-closeout`.
   - Current decision is `EXECUTABLE_TICKET_PREREQUISITES_NOT_CLOSED`.
   - This records that the prerequisite chain is not complete; it does not populate order values, create an executable ticket, or approve execution.

6f. **Check approval readiness without requesting approval.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-executable-ticket-approval-readiness`.
   - Saved display: `python bot.py --show-vol-targeted-growth-executable-ticket-approval-readiness`.
   - Current decision is `NOT_READY_TO_REQUEST_EXECUTABLE_TICKET_APPROVAL`.
   - This does not request or record approval and keeps execution, paper execution, live trading, and scheduling approvals false.

6g. **Define manual approval criteria without asking for approval.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-executable-ticket-approval-criteria`.
   - Saved display: `python bot.py --show-vol-targeted-growth-executable-ticket-approval-criteria`.
   - Current decision is `APPROVAL_CRITERIA_DEFINED_APPROVAL_NOT_REQUESTED`.
   - This defines the future manual questions around prerequisites, fresh broker context, ticket values, sleeve boundaries, and scheduling, but it does not request approval, record approval, create ticket values, create an executable ticket, or approve execution.

6h. **Order the criteria blocker resolution plan without resolving blockers.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-executable-ticket-criteria-resolution-plan`.
   - Saved display: `python bot.py --show-vol-targeted-growth-executable-ticket-criteria-resolution-plan`.
   - Current decision is `CRITERIA_BLOCKER_RESOLUTION_PLAN_CREATED_APPROVAL_STILL_BLOCKED`.
   - This orders the manual review work, but it does not resolve blockers, request approval, record approval, create ticket values, create an executable ticket, or approve execution.

6i. **Review criteria source wording without closing blockers.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-executable-ticket-criteria-source-review`.
   - Saved display: `python bot.py --show-vol-targeted-growth-executable-ticket-criteria-source-review`.
   - Current decision is `CRITERIA_SOURCE_REVIEWED_NO_BLOCKERS_CLOSED`.
   - This checks whether the saved criteria and resolution-plan wording are coherent for manual review, but it does not change criteria, resolve blockers, request approval, record approval, create ticket values, create an executable ticket, or approve execution.

6j. **Review criteria blocker closeout status without closing blockers.**
   - Implemented checkpoint: `python bot.py --vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review`.
   - Saved display: `python bot.py --show-vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review`.
   - Current decision is `CRITERIA_BLOCKERS_REVIEWED_NONE_CLOSED`.
   - This classifies blockers for manual review, but it does not close blockers, change approval readiness, request approval, record approval, create ticket values, create an executable ticket, or approve execution.

6k. **Review the first blocker-specific checkpoints without closing blockers.**
   - Implemented checkpoints:
     `python bot.py --vol-targeted-growth-criteria-source-blocker-review`,
     `python bot.py --vol-targeted-growth-criteria-resolution-plan-blocker-review`,
     `python bot.py --vol-targeted-growth-approval-criteria-not-approval-blocker-review`,
     and `python bot.py --vol-targeted-growth-criteria-blocker-specific-review-rollup`.
   - Current rollup decision is `CRITERIA_BLOCKER_SPECIFIC_REVIEWS_CREATED_NONE_CLOSED`.
   - These reports confirm source evidence, resolution-plan ordering, and approval-criteria boundaries for manual review only; they do not close blockers, request approval, record approval, populate ticket values, create an executable ticket, or approve execution.

6l. **Prepare closeout-candidate reviews without closing blockers.**
   - Implemented checkpoints:
     `python bot.py --vol-targeted-growth-criteria-source-closeout-candidate-review`,
     `python bot.py --vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review`,
     `python bot.py --vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review`,
     and `python bot.py --vol-targeted-growth-criteria-closeout-candidate-review-rollup`.
   - Current rollup decision is `CRITERIA_CLOSEOUT_CANDIDATES_REVIEWED_NONE_CLOSED`.
   - These reports can mark `criteria_source_reviewed` as ready for human closeout consideration and keep the other two blockers not ready, but they do not close blockers, change approval readiness, request approval, record approval, populate ticket values, create an executable ticket, or approve execution.

6m. **Define simple wording for the one candidate-ready blocker, without recording approval.**
   - Run `python bot.py --vol-targeted-growth-criteria-source-closeout-approval-wording`.
   - Optional display: `python bot.py --show-vol-targeted-growth-criteria-source-closeout-approval-wording`.
   - Future approval phrase, if Lewis chooses to use it later: `I approve closing the criteria_source_reviewed blocker only.`
   - This defines wording only. It does not close the blocker, record approval, close any other blocker, populate ticket values, create an executable ticket, or approve execution/scheduling.

6n. **Close only the criteria source blocker after explicit approval.**
   - Run `python bot.py --vol-targeted-growth-criteria-source-closeout-record`.
   - Optional display: `python bot.py --show-vol-targeted-growth-criteria-source-closeout-record`.
   - Current closeout decision is `CRITERIA_SOURCE_REVIEWED_BLOCKER_CLOSED_ONLY`.
   - This closes only `criteria_source_reviewed`. It does not close `criteria_resolution_plan_open` or `approval_criteria_not_approval`, does not populate ticket values, does not create an executable ticket, and does not approve execution/scheduling.
   - The execution blocker rollup and executable ticket gap list must show `criteria_source_reviewed_closed=True` and the exact remaining blockers before any further ticket-design work.

6o. **Close only the criteria resolution-plan blocker after explicit approval.**
   - Run `python bot.py --vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording`.
   - Optional display: `python bot.py --show-vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording`.
   - Run `python bot.py --vol-targeted-growth-criteria-resolution-plan-closeout-record`.
   - Optional display: `python bot.py --show-vol-targeted-growth-criteria-resolution-plan-closeout-record`.
   - Current closeout decision is `CRITERIA_RESOLUTION_PLAN_OPEN_BLOCKER_CLOSED_ONLY`.
   - This closes only `criteria_resolution_plan_open`. It does not close `approval_criteria_not_approval`, does not populate ticket values, does not create an executable ticket, and does not approve execution/scheduling.
   - The execution blocker rollup and executable ticket gap list must show `criteria_resolution_plan_open_closed=True` and the exact remaining blockers before any further ticket-design work.

6p. **Close only the approval-criteria-not-approval blocker after explicit approval.**
   - Run `python bot.py --vol-targeted-growth-approval-criteria-closeout-approval-wording`.
   - Optional display: `python bot.py --show-vol-targeted-growth-approval-criteria-closeout-approval-wording`.
   - Run `python bot.py --vol-targeted-growth-approval-criteria-closeout-record`.
   - Optional display: `python bot.py --show-vol-targeted-growth-approval-criteria-closeout-record`.
   - Current closeout decision is `APPROVAL_CRITERIA_NOT_APPROVAL_BLOCKER_CLOSED_ONLY`.
   - This closes only `approval_criteria_not_approval`. It does not populate ticket values, does not create an executable ticket, and does not approve execution/scheduling.
   - The execution blocker rollup and executable ticket gap list must now show `closed_blocker_count=3`, `criteria_source_reviewed_closed=True`, `criteria_resolution_plan_open_closed=True`, `approval_criteria_not_approval_closed=True`, and the exact remaining blockers before any ticket-value discussion.

6q. **Close the final two checklist blockers as non-executable checklist evidence only.**
   - Run `python bot.py --vol-targeted-growth-final-ticket-blockers-closeout-approval-wording`.
   - Optional display: `python bot.py --show-vol-targeted-growth-final-ticket-blockers-closeout-approval-wording`.
   - Run `python bot.py --vol-targeted-growth-final-ticket-blockers-closeout-record`.
   - Optional display: `python bot.py --show-vol-targeted-growth-final-ticket-blockers-closeout-record`.
   - Current closeout decision is `FINAL_TICKET_BLOCKERS_CLOSED_NO_EXECUTION_APPROVAL`.
   - This closes `ticket_values_not_approved` and `executable_ticket_prerequisites_not_met` only as checklist blockers. It does not populate side, quantity, order type, time-in-force, account, or broker-order fields. It does not create an executable ticket and does not approve execution/scheduling.
   - The execution blocker rollup and executable ticket gap list must now show `closed_blocker_count=5`, `ticket_values_not_approved_closed=True`, `executable_ticket_prerequisites_not_met_closed=True`, `remaining_known_blockers_after_closeout=none`, and `largest_blocker=execution_not_approved`.

6r. **Create execution approval request readiness, without requesting approval.**
   - Run `python bot.py --vol-targeted-growth-execution-approval-request-readiness`.
   - Optional display: `python bot.py --show-vol-targeted-growth-execution-approval-request-readiness`.
   - Expected decision is `READY_FOR_SEPARATE_EXECUTION_APPROVAL_REQUEST_NOT_APPROVED`.
   - This means the checklist is ready for a separate explicit human approval question only. It must keep `approval_requested=False`, `approval_recorded=False`, `order_values_populated=False`, `executable_ticket_created=False`, `execution_approved=False`, `paper_execution_approved=False`, and `scheduling_approved=False`.

7. **Create a non-submitting draft ticket instance only if explicitly approved later.**
   - This is not approved yet.
   - It must still be non-submitting and must not connect to the order gateway.
   - It must preserve `orders_created=False`, `orders_submitted=False`, `paper_execution_approved=False`, and `execution_approved=False`.

8. **Add ticket-instance quality gates and tests.**
   - Verify no secrets, account IDs, webhook URLs, broker order IDs, or generated trading data appear in ticket outputs.
   - Verify no order can be submitted from a report-only ticket.
   - Verify stale broker data, unknown positions, missing target weights, or component-sleeve blockers all block.

9. **Manual review of whether paper execution should ever be allowed for this seed.**
   - This is a human decision point, not an automatic result of previous reports.
   - Required blockers to review: component sleeves, allocation cap, fresh broker state, QQQ existing exposure, high-growth research-only boundary, crypto research-only boundary, defensive sleeve mapping, drawdown risk, and scheduling prohibition.

10. **If approved later, design a separate paper-order execution gate.**
    - This is not approved yet.
    - It must remain Alpaca paper-only.
    - It must be a separate explicit command with confirmation.
    - It must not alter normal `python bot.py`.
    - It must not be scheduled by Hermes, cron, Task Scheduler, or any loop.

11. **Only after all above, consider one manually confirmed paper order.**
    - This is not approved by this checklist.
    - It would require a fresh live preflight, fresh broker state, exact ticket review, duplicate-order protection, open-order checks, kill-switch checks, and explicit confirmation.
    - Postcheck must be read-only and must reconcile broker order/position evidence after the manual order.

12. **Keep monitoring-only automation after any manual paper action.**
    - Hermes may continue to run status/report summaries only.
    - No order-capable command may be scheduled.
    - Daily summary must continue to show execution/paper execution/scheduling approvals as false unless a later, explicit, narrow paper execution design changes only the appropriate manual command path.

Current next safe implementation step:

- If the run-readiness checkpoint passes, the next operational step is a separate prompt explicitly approving the read-only fresh broker pre-ticket gate run. That future run must still not create a ticket, populate order values, submit orders, or approve execution.

Current next market-hours operational step, only after explicit approval:

- Run the read-only volatility broker-position comparison during market hours:
  `.venv\Scripts\python.exe bot.py --vol-targeted-growth-broker-position-comparison --confirm-readonly-alpaca-check`

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
- `python bot.py --high-growth-strategy-discovery-sprint` may identify strong high-growth research candidates such as `higher_growth_70_20_5_5` and `qqq100_plus_high_growth_plus_crypto_research`, but that sprint is not preview promotion, paper-live approval, or execution approval.
- `python bot.py --higher-growth-preview-readiness-pack` may mark `higher_growth_70_20_5_5` ready for manual preview discussion, but it still does not implement preview mode, promote high-growth, approve paper execution, or approve scheduling.
- `python bot.py --higher-growth-candidate-selection-decision` may select `higher_growth_70_20_5_5` for a future preview-only design prompt, but preview implementation and all execution approvals remain blocked.
- `python bot.py --higher-growth-preview-design` documents the future preview-only target weights and output shape for `higher_growth_70_20_5_5`, but it still does not create a preview signal, action preview, order instructions, or execution approval.
- `python bot.py --vol-targeted-growth-research-sprint` may identify volatility-targeted growth research candidates, but it still does not create preview signals, action previews, order instructions, paper-live approval, execution approval, or scheduling approval.
- `python bot.py --vol-targeted-growth-manual-review-pack` may favour `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` as a cleaner next research path, but it still does not implement preview mode, promote high-growth/crypto, approve paper execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-robustness-checkpoint` may support continued manual review of that candidate, but preview design, action previews, order instructions, paper execution, and scheduling remain blocked.
- `python bot.py --vol-targeted-growth-nearby-variants-review` may compare 15%/20-day against nearby multi-sleeve vol-targeted settings, but it still does not choose a paper-live strategy, create preview signals, approve execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-preview-readiness-decision` may select 15%/20-day for a future preview-design review, but it still does not implement preview mode, create action previews, create order instructions, approve execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-preview-design` may document the future preview-only output shape for 15%/20-day, but it still does not create a preview signal, action preview, order instructions, paper execution, or scheduling approval.
- `python bot.py --vol-targeted-growth-preview-signal` may write saved candidate identity, target sleeve weights, volatility settings, blockers, and safety flags for 15%/20-day, but it still does not create an action preview, order instructions, paper execution, or scheduling approval.
- `python bot.py --vol-targeted-growth-action-preview-design` may document how a future action-preview checkpoint should behave, but it still does not create action rows, read broker positions, create order instructions, approve paper execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-action-preview` may create saved sleeve-level manual-review rows from the 15%/20-day preview signal, but current exposure remains not read and it still does not create order instructions, approve paper execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-action-preview-quality-gate` may check whether those saved action-preview rows are usable for manual review only, but broker-position comparison remains incomplete and it still does not create order instructions, approve paper execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-broker-position-comparison-design` may document a future read-only broker comparison gate, but it still does not call Alpaca, read positions, approve execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-portfolio-risk-review` keeps the 15%/20-day candidate research-only until broker comparison and portfolio risk policy are reviewed; it does not approve paper-live candidacy.
- `python bot.py --vol-targeted-growth-portfolio-risk-policy-design` may propose guardrails for allocation, crypto cap, high-growth review, drawdown review, and broker-position review, but it does not enforce policy or approve paper-live candidacy.
- `python bot.py --vol-targeted-growth-paper-live-decision` may mark the 15%/20-day candidate ready for manual discussion of a future read-only broker-position comparison, but it keeps the candidate research-only and does not approve paper-live candidacy, execution, or scheduling.
- `python bot.py --vol-targeted-growth-broker-comparison-run-readiness` may mark the saved chain ready to request explicit manual approval for a future read-only broker-position comparison only after the action-preview quality gate is usable for manual review, but it still does not grant approval, call Alpaca, read positions, approve paper-live candidacy, execution, or scheduling.
- `python bot.py --vol-targeted-growth-broker-position-comparison` may compare saved target sleeves with paper-position context only after a separately approved `--confirm-readonly-alpaca-check` run; default mode must not call Alpaca, and neither mode may create order instructions or approve paper-live candidacy.
- `python bot.py --vol-targeted-growth-post-comparison-decision` may mark the chain ready to design a stricter manual paper-live discussion gate after saved confirmed comparison evidence, but it still does not approve the gate, paper-live candidacy, execution, or scheduling.
- `python bot.py --vol-targeted-growth-stricter-paper-live-gate-design` defines hard blockers for any future discussion: QQQ100 remains the incumbent seed, allocation cap is separate, high-growth/crypto stay research-only, unmapped sleeves cannot become order instructions, and the gate is not enforced or approved.
- `python bot.py --vol-targeted-growth-gate-review` may mark the candidate ready for limited manual discussion only; it still does not approve paper-live candidacy, enforce the gate, create order instructions, execute, or schedule.
- `python bot.py --vol-targeted-growth-candidate-discussion-blocker-checklist` lists the final open blockers before any volatility-targeted implementation work; it does not approve implementation, paper-live candidacy, order fields, execution, repeat orders, or scheduling.
- `python bot.py --vol-targeted-growth-candidate-decision-record` may record that manual candidate discussion can continue, but QQQ100 remains the incumbent seed and no implementation, seed change, order field, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-candidate-discussion` may mark the volatility-targeted strategy as a non-executable paper-live candidate proposal for manual review only; QQQ100 remains the incumbent seed and no preview/action implementation, order instruction, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-proposal-implementation-design` may document a future non-executable preview/action proposal design only; it does not add implementation, create order fields, displace QQQ100, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-proposal-preview-schema` may document allowed/forbidden fields for a future proposal preview only; order side, quantity, order type, account, API key, webhook, token, and order ID fields are forbidden, and QQQ100 remains the incumbent seed.
- `python bot.py --vol-targeted-growth-proposal-preview` may create saved sleeve-level proposal rows for manual review only; it does not read positions, create order fields, displace QQQ100, approve action, execute, repeat orders, or schedule.
- `python scripts\verify_vol_targeted_growth_preview_action_chain_checkpoint.py` checks the existing volatility proposal/action-preview chain as a non-executable review chain only; it does not add implementation, run broker checks, approve QQQ100 displacement, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-seed-change-review` may allow manual consideration of the volatility proposal to continue, but QQQ100 remains the seed and no displacement, seed change, action, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-seed-change-evidence-pack` may list missing evidence required before QQQ100 displacement could even be proposed; it does not create a seed-change proposal, change the seed, read positions, create order fields, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-seed-change-risk-reward-comparison` may fill the risk/reward evidence item from saved metrics only; source mismatch/manual review remains a blocker and no QQQ100 displacement, seed change, action, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-seed-change-drawdown-stress-review` may fill the drawdown/stress evidence item from saved MaxDD metrics only; stress-window evidence remains incomplete and no QQQ100 displacement, seed change, action, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-seed-change-cost-turnover-review` may fill the cost/turnover evidence item from saved outputs only; exact cost stress remains missing and no QQQ100 displacement, seed change, action, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-seed-change-split-stability-review` may fill the split-stability evidence item from saved split outputs only; supportive split evidence remains manual-review-only and no QQQ100 displacement, seed change, action, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-seed-change-component-sleeve-review`, `python bot.py --vol-targeted-growth-seed-change-action-preview-design`, and `python bot.py --vol-targeted-growth-seed-change-proposal-document` may fill non-broker evidence checkpoints only; the proposal document is draft-only, broker exposure remains separate, and no QQQ100 displacement, seed change, action implementation, execution, repeat order, or scheduling is approved.
- `python bot.py --vol-targeted-growth-seed-change-broker-exposure-review` may review saved read-only broker-comparison output only; it must not call Alpaca or read positions again, and it does not approve QQQ100 displacement, seed change, action implementation, execution, repeat order, or scheduling.
- `python bot.py --vol-targeted-growth-seed-change-manual-review-checkpoint` may mark completed saved evidence ready for human formal-proposal review only; it does not create the formal proposal, displace QQQ100, change the seed, implement action preview, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-formal-seed-change-proposal` may create the saved proposal document for human review only; it does not record approval, displace QQQ100, change the seed, implement action preview, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-seed-change-manual-approval-record` may record approval for the implementation-design checkpoint only; it does not displace QQQ100, change the seed, implement action preview, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-seed-change-implementation-design` may describe future seed-change code boundaries only; it does not displace QQQ100, change the seed, implement action preview, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-seed-change-dry-run-diff` may list future seed-switch target files/areas only; it does not modify those files, displace QQQ100, change the seed, implement action preview, execute, repeat orders, or schedule.
- `python scripts\verify_vol_targeted_growth_seed_switch_status_only.py` verifies the implemented status-only report seed switch: volatility-targeted growth is the active report/status seed, QQQ100 remains previous-seed context, and all order/execution/scheduling approvals remain false.
- `python bot.py --vol-targeted-growth-active-seed-readiness` may check saved monitoring/status consistency for the current volatility-targeted report/status seed only; it does not implement action preview, execute, repeat orders, schedule, call Alpaca, or refresh market data.
- `python bot.py --vol-targeted-growth-paper-live-manual-approval-gate` may package the active volatility seed paper-live manual gate for review only; it does not record approval, create order instructions, execute, repeat orders, schedule, call Alpaca, or read positions.
- `python bot.py --vol-targeted-growth-paper-live-action-preview-pack` may package saved action-preview rows and quality-gate context for manual review only; it does not read current broker exposure, create executable order fields, execute, repeat orders, or schedule.
- `python bot.py --vol-targeted-growth-broker-comparison-reconciliation` may reconcile saved broker-comparison output only; it must not call Alpaca or read positions again, and it does not approve paper-live candidacy, execution, repeat orders, or scheduling.
- `python bot.py --vol-targeted-growth-paper-live-candidate-approval-record` may record approval for paper-live candidate discussion only; it does not approve paper-live candidacy, allocation caps, sleeve mapping, order design, execution, repeat orders, or scheduling.
- `python bot.py --vol-targeted-growth-allocation-cap-sleeve-mapping-policy` may document allocation-cap and sleeve-mapping boundaries only; executable allocation remains zero until a separate execution design exists, QQQ is review-only, high-growth/crypto stay research-only, defensive remains unmapped, and target-position design/execution/scheduling remain unapproved.
- `python bot.py --vol-targeted-growth-non-executable-target-position-plan` may document target-position review context only; it keeps QQQ review-only with no order quantity, keeps high-growth/crypto blocked, keeps defensive unmapped, and creates no executable target positions, order instructions, execution approval, or scheduling approval.
- `python bot.py --vol-targeted-growth-order-ticket-boundary-design` may document order-ticket boundaries only; it keeps QQQ review-only with no side or quantity, keeps research sleeves blocked/unmapped, and creates no executable order ticket, order instructions, execution approval, or scheduling approval.
- `python bot.py --vol-targeted-growth-executable-ticket-prerequisites-review` may list missing prerequisites for any future executable ticket design only; it does not satisfy those prerequisites, call Alpaca, read positions, create tickets, approve execution, or approve scheduling.
- `python bot.py --vol-targeted-growth-executable-ticket-gap-list` may summarize remaining gaps before executable ticket design discussion only; it does not clear gaps, create order fields, call Alpaca, read positions, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved gap-list status as monitoring context only.
- `python bot.py --vol-targeted-growth-manual-execution-design-approval-gate` may define the wording/scope required for a future explicit approval prompt only; it does not record approval, create order fields, create executable tickets, call Alpaca, read positions, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved approval-gate status as monitoring context only.
- `python bot.py --vol-targeted-growth-non-submitting-ticket-schema-design` may define future ticket schema fields for manual review only; it does not create a ticket instance, populate order values, call Alpaca, read positions, submit orders, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved schema-design status as monitoring context only.
- `python bot.py --vol-targeted-growth-non-submitting-ticket-instance-design` may define a draft future ticket-instance shape for manual review only; it does not create an executable ticket, populate side, quantity, order type, time-in-force, account, or broker order id, call Alpaca, read positions, submit orders, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved ticket-instance design status as monitoring context only.
- `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-design` may define the future read-only broker gate for manual review only; it does not run the gate, call Alpaca, read positions, create tickets, populate order values, submit orders, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved gate-design status as monitoring context only.
- `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness` may check whether the saved design chain is ready to request explicit read-only Alpaca approval; it does not approve or run Alpaca, read positions, create tickets, populate order values, submit orders, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved run-readiness status as monitoring context only.
- `python bot.py --vol-targeted-growth-fresh-broker-pre-ticket-gate-run --confirm-readonly-alpaca-check` may perform the explicitly approved read-only Alpaca paper-position gate and save broker context for manual review only. It still does not create tickets, populate order values, submit orders, approve follow-up execution, or approve scheduling. Without the confirmation flag, it records missing confirmation and does not read the broker.
- `python bot.py --vol-targeted-growth-post-gate-review` may interpret saved fresh broker context only; it does not call Alpaca, read positions, create tickets, populate order values, submit orders, approve execution, or approve scheduling. The go/no-go dashboard may display this saved post-gate status as context only.
- `python bot.py --vol-targeted-growth-manual-ticket-value-design` may document future ticket-value fields only; it does not populate side, quantity, order type, time-in-force, account reference, broker order id, submit-ready state, create executable tickets, submit orders, approve execution, or approve scheduling. The go/no-go dashboard may display this saved ticket-value design status as context only.
- `python bot.py --vol-targeted-growth-paper-live-execution-blocker-rollup` may summarize the volatility paper-live blocker chain only; it does not clear blockers, create executable tickets, approve execution, or approve scheduling. The VPS daily monitoring summary may display this saved rollup status as monitoring context only.
- `python bot.py --paper-live-go-no-go-dashboard` may summarize QQQ100 no-action state, volatility blocker state, checklist phase, and VPS monitoring assumptions in one saved-output view only; current expected decision is `NO_GO_EXECUTION_BLOCKED_MONITOR_ONLY`, and it does not approve execution or scheduling.
- `python bot.py --vps-daily-monitoring-summary` may display the saved paper-live go/no-go dashboard status when present; missing dashboard output is reported as monitoring-only missing saved evidence and does not create orders, broker reads, cron changes, execution approval, or scheduling approval.
- `python scripts\verify_vol_targeted_growth_seed_change_chain_checkpoint.py` verifies the saved seed-change review ladder through active-seed readiness remains complete and review-only; it does not implement a seed switch, create order fields, execute, repeat orders, or schedule.
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

Implemented daily decision checkpoint: `python bot.py --qqq100-daily-decision-report`.

Saved display: `python bot.py --show-qqq100-daily-decision-report`.

Outputs: `data/qqq100_daily_decision_report.csv`, `data/qqq100_daily_decision_summary.csv`, `data/qqq100_daily_decision_blockers.csv`, and `data/qqq100_daily_decision_evidence.csv`.

The daily decision reads saved QQQ100 paper-live evidence and the saved follow-up/no-action policy only. It can report `qqq100_daily_decision_hold_no_action_aligned_long`, `qqq100_daily_decision_hold_no_action_aligned_flat`, `qqq100_daily_decision_manual_buy_discussion_possible_not_approved`, `qqq100_daily_decision_manual_flatten_discussion_possible_not_approved`, or `qqq100_daily_decision_blocked_manual_review_required`. It does not approve execution, paper execution, repeat/follow-up orders, scheduling, or executable order instructions.

Implemented manual flatten readiness checkpoint: `python bot.py --qqq100-manual-flatten-readiness-report`.

Saved display: `python bot.py --show-qqq100-manual-flatten-readiness-report`.

Outputs: `data/qqq100_manual_flatten_readiness_report.csv`, `data/qqq100_manual_flatten_readiness_summary.csv`, `data/qqq100_manual_flatten_readiness_blockers.csv`, and `data/qqq100_manual_flatten_readiness_evidence.csv`.

The manual flatten readiness report reads saved QQQ100 evidence and the saved follow-up/no-action policy only. Current aligned-long evidence should report `flatten_not_needed_currently`. If a future saved signal says desired state is `flat` while saved QQQ position is long exactly one share, it may report `future_manual_flatten_discussion_possible_not_approved`; that remains only a separate manual discussion checkpoint and does not approve a sell, repeat execution, follow-up order, scheduling, or executable order instruction.

Implemented manual flatten runbook/design checkpoint: `python bot.py --qqq100-manual-flatten-runbook-report`.

Saved display: `python bot.py --show-qqq100-manual-flatten-runbook-report`.

Outputs: `data/qqq100_manual_flatten_runbook_report.csv`, `data/qqq100_manual_flatten_runbook_summary.csv`, `data/qqq100_manual_flatten_runbook_blockers.csv`, and `data/qqq100_manual_flatten_runbook_evidence.csv`.

The manual flatten runbook reads the saved flatten readiness checkpoint only. Current aligned-long evidence should report `manual_flatten_runbook_not_needed_currently`. If a future saved signal says desired state is `flat` while saved QQQ position is long exactly one share, it may report `manual_flatten_runbook_manual_review_required_not_approved`; this remains a design/runbook checkpoint and still does not approve a sell, repeat execution, follow-up order, scheduling, or executable order instruction.

## 11. Schedule Monitoring Only

- Implemented report-only monitoring checkpoint: `python bot.py --paper-live-monitoring-status`.
- Saved display: `python bot.py --show-paper-live-monitoring-status`.
- Outputs: `data/paper_live_monitoring_status.csv`, `data/paper_live_monitoring_components.csv`, and `data/paper_live_monitoring_blockers.csv`.
- This checkpoint may show `qqq_100_trend_gate` / `QQQ` aligned long one share with `no_action_required=True` and `recommended_next_step=hold_no_action_and_monitor_only`.
- `python bot.py --vps-monitoring-status` and `python bot.py --vps-daily-monitoring-summary` include the saved paper-live monitoring status and saved QQQ100 daily decision when available, so the current status-only Hermes output can show aligned long one share and hold/no-action without adding a new cron command.
- `python bot.py --vps-daily-monitoring-summary` also includes the saved volatility-targeted candidate decision record when available, so Hermes/manual status can show manual discussion only, QQQ100 still incumbent, and implementation/execution/scheduling still unapproved.
- The same status-only outputs include saved QQQ100 manual flatten readiness/runbook statuses when available, so the current Hermes output can show flatten is not needed and not approved.
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

Current expected closeout status is `paper_live_checklist_vol_targeted_seed_status_only_phase_ready_manual_review`: Steps 1-11 are complete or complete-for-current-status-only-seed-phase, the volatility-targeted candidate is the active report/status seed, QQQ100 remains aligned long one share as previous-seed context, no further QQQ order is needed now, repeat/follow-up orders remain blocked, and scheduling remains monitoring-only.

Implemented F6/F7 audit checkpoint: `python bot.py --paper-live-f6-f7-audit`.

Saved display: `python bot.py --show-paper-live-f6-f7-audit`.

Outputs: `data/paper_live_f6_f7_audit.csv`, `data/paper_live_f6_f7_audit_summary.csv`, `data/paper_live_f6_f7_audit_blockers.csv`, and `data/paper_live_f6_f7_audit_evidence.csv`.

Current expected audit status is `paper_live_f6_f7_audit_manual_review_required`: F6 confirms some loud position unknown / position unavailable boundaries but still needs future promotion-ladder review, and F7 requires starting-cash/accounting tests or verifiers before portfolio backtests are used as promotion evidence.

Implemented F6/F7 targeted checks verifier: `python scripts\verify_paper_live_f6_f7_targeted_checks.py`.

This no-network verifier exercises pure preview/action helpers so unknown positions stay loud and never silently become flat, aligned, or eligible. It also keeps portfolio backtests not promotion evidence until starting-cash/accounting consistency is proven. It does not approve execution, scheduling, multi-sleeve promotion, or generic promotion-ladder work.

Implemented generic promotion ladder design checkpoint: `python bot.py --paper-live-promotion-ladder-design`.

Saved display: `python bot.py --show-paper-live-promotion-ladder-design`.

Outputs: `data/paper_live_promotion_ladder_design.csv`, `data/paper_live_promotion_ladder_design_summary.csv`, `data/paper_live_promotion_ladder_design_blockers.csv`, and `data/paper_live_promotion_ladder_design_evidence.csv`.

Current expected design status is `paper_live_promotion_ladder_design_report_only`: the volatility-targeted multi-sleeve candidate is the current report/status seed, QQQ100 remains previous-seed context and aligned long one share, no repeat/follow-up/flatten QQQ order is approved, saved flatten readiness/runbook statuses are `flatten_not_needed_currently` and `manual_flatten_runbook_not_needed_currently`, high-growth and crypto remain research-only, defensive sleeves remain future review only, no SMA or slow-SMA paper-live promotion is allowed, portfolio backtests are not promotion evidence until accounting consistency is proven, unknown positions block/manual-review, and no scheduled execution is allowed.

Implemented first report-only promotion ladder status scaffold: `python bot.py --paper-live-promotion-ladder-status`.

Saved display: `python bot.py --show-paper-live-promotion-ladder-status`.

Outputs: `data/paper_live_promotion_ladder_status.csv`, `data/paper_live_promotion_ladder_status_summary.csv`, `data/paper_live_promotion_ladder_status_blockers.csv`, and `data/paper_live_promotion_ladder_status_evidence.csv`.

Current expected status is `paper_live_promotion_ladder_status_report_only`: the volatility-targeted growth candidate is the current report/status seed, QQQ100 remains previous-seed context with `previous_seed_monitor_only_aligned_long_one`, high-growth and crypto remain research-only, defensive sleeves remain future-review-only, SMA and slow-SMA remain excluded, and portfolio backtests are not promotion evidence. F7 accounting proof is accepted for the accounting checkpoint, but it does not approve promotion, execution, or scheduling.

Implemented F7 accounting proof checkpoint: `python bot.py --paper-live-f7-accounting-proof`.

Saved display: `python bot.py --show-paper-live-f7-accounting-proof`.

Outputs: `data/paper_live_f7_accounting_proof.csv`, `data/paper_live_f7_accounting_proof_summary.csv`, `data/paper_live_f7_accounting_proof_blockers.csv`, and `data/paper_live_f7_accounting_proof_evidence.csv`.

Current expected F7 status is `f7_accounting_static_proof_ready_for_manual_review`: the saved-output multi-sleeve portfolio backtest uses weighted daily returns and no independent starting cash is detected in the source. This checkpoint has been accepted as the F7 accounting proof, but portfolio backtests are still not promotion evidence without separate promotion review; execution, paper execution, scheduling, live trading, repeat execution, and promotion approval remain false.

Implemented next ladder candidate scope checkpoint: `python bot.py --paper-live-next-ladder-candidate-scope`.

Saved display: `python bot.py --show-paper-live-next-ladder-candidate-scope`.

Outputs: `data/paper_live_next_ladder_candidate_scope.csv`, `data/paper_live_next_ladder_candidate_scope_summary.csv`, `data/paper_live_next_ladder_candidate_scope_blockers.csv`, and `data/paper_live_next_ladder_candidate_scope_evidence.csv`.

Current expected scope status is `next_ladder_candidate_scope_report_only`: defensive sleeve is the next conservative report-only review scope, multi-sleeve allocator is deferred until after defensive review, and high-growth remains research-only. This does not approve promotion, execution, scheduling, order instructions, or portfolio backtest promotion evidence.

Implemented defensive sleeve ladder-scope review: `python bot.py --paper-live-defensive-sleeve-ladder-scope-review`.

Saved display: `python bot.py --show-paper-live-defensive-sleeve-ladder-scope-review`.

Outputs: `data/paper_live_defensive_sleeve_ladder_scope_review.csv`, `data/paper_live_defensive_sleeve_ladder_scope_review_summary.csv`, `data/paper_live_defensive_sleeve_ladder_scope_review_blockers.csv`, and `data/paper_live_defensive_sleeve_ladder_scope_review_evidence.csv`.

Current expected defensive scope status is either `defensive_sleeve_ladder_scope_review_ready_for_manual_review` when the saved defensive evidence stack is present, or `defensive_sleeve_ladder_scope_missing_saved_evidence_manual_review_required` when files are missing. In both cases, the defensive sleeve is not promoted, no candidate label changes are approved, and no orders or scheduling are approved.

Implemented defensive sleeve manual review checkpoint: `python bot.py --paper-live-defensive-sleeve-manual-review`.

Saved display: `python bot.py --show-paper-live-defensive-sleeve-manual-review`.

Outputs: `data/paper_live_defensive_sleeve_manual_review.csv`, `data/paper_live_defensive_sleeve_manual_review_summary.csv`, `data/paper_live_defensive_sleeve_manual_review_blockers.csv`, and `data/paper_live_defensive_sleeve_manual_review_evidence.csv`.

Current expected manual review status is `defensive_sleeve_manual_review_required` when saved defensive evidence is complete. This confirms the branch can be discussed manually while `qqq_100_trend_gate` remains the clean paper-live lead. Preview, promotion, execution, paper execution, repeat orders, live trading, and scheduling remain unapproved.

Implemented defensive sleeve preview-readiness checkpoint: `python bot.py --paper-live-defensive-sleeve-preview-readiness`.

Saved display: `python bot.py --show-paper-live-defensive-sleeve-preview-readiness`.

Outputs: `data/paper_live_defensive_sleeve_preview_readiness.csv`, `data/paper_live_defensive_sleeve_preview_readiness_summary.csv`, `data/paper_live_defensive_sleeve_preview_readiness_blockers.csv`, and `data/paper_live_defensive_sleeve_preview_readiness_evidence.csv`.

Current expected preview-readiness status is `defensive_sleeve_preview_candidate_not_approved_manual_review_required`: the defensive sleeve remains research-only and not a preview candidate until a separate manual decision approves a label change. The paper-live checklist status now carries this blocked defensive state alongside the QQQ100 aligned/no-action state.

Implemented defensive sleeve evidence-quality review checkpoint: `python bot.py --paper-live-defensive-sleeve-evidence-quality`.

Saved display: `python bot.py --show-paper-live-defensive-sleeve-evidence-quality`.

Outputs: `data/paper_live_defensive_sleeve_evidence_quality.csv`, `data/paper_live_defensive_sleeve_evidence_quality_summary.csv`, `data/paper_live_defensive_sleeve_evidence_quality_blockers.csv`, and `data/paper_live_defensive_sleeve_evidence_quality_evidence.csv`.

Current expected evidence-quality status is `defensive_sleeve_evidence_quality_manual_review_required`: the saved evidence can support continued defensive research, but split sensitivity, full-period drawdown, allocation decision blockers, and the QQQ100 role boundary must be manually reviewed before any defensive preview design. It does not approve preview candidacy, promotion, execution, paper execution, repeat orders, live trading, or scheduling.

Implemented QQQ-led multi-sleeve roadmap checkpoint: `python bot.py --paper-live-multi-sleeve-roadmap`.

Saved display: `python bot.py --show-paper-live-multi-sleeve-roadmap`.

Outputs: `data/paper_live_multi_sleeve_roadmap.csv`, `data/paper_live_multi_sleeve_roadmap_summary.csv`, `data/paper_live_multi_sleeve_roadmap_blockers.csv`, and `data/paper_live_multi_sleeve_roadmap_evidence.csv`.

Current expected roadmap status is `paper_live_multi_sleeve_roadmap_report_only`: the volatility-targeted growth candidate is now the current report/status seed, QQQ100 core remains previous-seed context, defensive sleeve is future review only, high-growth remains research-only until concentration/drawdown/attribution review is complete, crypto remains research-only/capped/future-only with no crypto execution approved, and the allocator has no portfolio execution wiring, no order instructions, and no scheduled execution.

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

> Add the saved non-submitting ticket schema design status to `python bot.py --vps-daily-monitoring-summary`, preserving monitoring-only behaviour and all false approval flags.

After that, the next market-hours step is a separate explicit-approval prompt for a read-only fresh broker pre-ticket gate run for `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`. Do not run any Alpaca check, broker read, paper order, ticket population, or execution command without explicit approval in that prompt.
