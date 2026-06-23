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
- Require saved research decision evidence.
- Require saved preview signal evidence.
- Require saved action preview evidence.
- Require portfolio/risk review evidence.
- Require execution-readiness evidence.
- Require no open blockers.
- Require explicit human approval before any paper execution command can be used.
- Promotion must not create orders.
- Promotion may output `paper_live_candidate=True`, but general `execution_approved` must remain false until the actual manual execution command.

## 6. Maintain QQQ100 Exact Alignment Before Further QQQ Paper Orders

- Desired long plus zero QQQ shares: buy one may be allowed after all gates pass.
- Desired long plus exactly one QQQ share: already aligned.
- Desired long plus more than one QQQ share: block/manual review. Do not reduce to one unless a separate explicit design is approved later.
- Desired flat plus zero QQQ shares: already flat.
- Desired flat plus exactly one QQQ share: sell one may be allowed after all gates pass.
- Desired flat plus more than one QQQ share: block/manual review. Do not sell all unless a separate explicit design is approved later.
- Verifier and pytest coverage must cover all six cases.

## 7. Build The Paper-Live Readiness Report

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

Add one saved-output command that answers:

- active paper-monitoring strategy,
- current desired state,
- current paper position,
- last paper order result,
- current alignment state,
- blockers,
- execution and scheduling flags.

This should be the daily check before touching any paper order command.

## 11. Schedule Monitoring Only

- Hermes cron may run status/report commands only.
- Hermes cron must not run QQQ100 execution.
- Hermes cron must not run normal `python bot.py`.
- Hermes cron must not run slow-SMA execution.
- Hermes cron must not run paper-order tests.
- Scheduled output should say monitoring only and no orders.

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
