# Codex Workflow Guide

This project is a Python paper trading bot. Future Codex prompts should keep safety boundaries explicit, especially when a task touches trading, Alpaca, positions, or command routing.

## Default Project Safety Assumptions

- The project is paper-only.
- Live trading must never be added.
- `dry_run` defaults to `true`.
- `alpaca.paper` must remain `true`.
- `config.json`, API keys, Discord webhook URLs, account IDs, and other secrets stay private.
- Normal `python bot.py` is monitoring-only. It may log intended actions, but must not submit Alpaca orders or mutate position state.
- Research, preview, display, and report commands must not execute trades.
- Paper execution commands must remain separate, explicit, and protected by confirmation flags.
- Manual paper sell paths must not oversell a long position while `allow_shorting` is false.
- The QQQ100 paper path must enforce exact zero/one-share QQQ alignment: more than one QQQ share must block/manual review, not count as aligned and not trigger an automatic reduce-to-one or sell-all flow.
- The paper-live promotion gate may label `qqq_100_trend_gate` as `paper_live_candidate=True` for manual discussion only. That label must not create order instructions, approve execution, approve paper execution, approve scheduling, or include SMA, slow-SMA, high-growth, crypto, QQQ150, or adaptive QQQ as paper-live candidates.
- The paper-live readiness report is a saved-output checklist only. It may summarize readiness blockers for future manual QQQ100 paper-action discussion, but `execution_approved`, `paper_execution_approved`, `scheduling_approved`, and `live_trading_approved` must remain false.
- The paper-live state summary is a saved-output daily checkpoint only. It may summarize saved QQQ100 desired state, saved position/alignment context, saved order result, promotion/readiness status, and blockers, but it must keep `execution_approved`, `paper_execution_approved`, `scheduling_approved`, `live_trading_approved`, and `followup_order_approved` false.
- The F7 accounting proof is report-only. It may statically confirm weighted daily returns and no independent starting cash in multi-sleeve portfolio backtests. The current proof is accepted as an accounting checkpoint, but portfolio backtests remain not promotion evidence without a separate promotion review.
- The next ladder candidate scope checkpoint is report-only. Defensive sleeve may be selected as the next manual review scope, while allocator/high-growth/crypto remain blocked from promotion unless separate saved-output reviews are completed.
- The defensive sleeve ladder-scope review is report-only. It may check saved defensive evidence presence and list blockers, but it must not promote the defensive sleeve, create order instructions, rerun research, or approve execution/scheduling.

## Task Risk Levels

- Docs-only: documentation updates, roadmap notes, workflow notes. No runtime verification needed unless code changes unexpectedly.
- Research-only: backtests, reports, CSV analysis, deterministic research helpers. No Alpaca orders, Discord alerts, or SQLite `trade_log` writes.
- Preview/display-only: reads saved CSVs or current market/position context for inspection. Must not approve execution or create executable order objects.
- Command-routing/refactor: moves or routes code without behavior changes. Needs focused verifiers and baseline checks.
- Execution-related/high risk: any paper-order submission, Alpaca order checks, position mutation, order sizing, close/open logic, or SQLite `trade_log` write path. Requires explicit scope, safety preflight, focused tests, and user confirmation before any order-capable run.

## Codex Commit/Push Policy

Codex may commit and push by itself only for small low-risk changes, such as docs-only updates, typo or formatting fixes, workflow notes, README or documentation clarifications, non-execution report text changes, and small verifier-script or documentation changes that do not touch trading logic.

Before Codex auto-commits or pushes, it must:

- Run `python scripts\verify_repo_safety.py`.
- Run any focused verifier relevant to the task if code changed.
- Confirm no Python execution paths changed unless explicitly scoped.
- Confirm no secrets or generated artefacts were touched.
- Show a `git status` summary in its report.
- Use a clear commit message.

Codex must not auto-push:

- Alpaca or order submission changes.
- Normal `python bot.py` runtime behaviour changes.
- Reintroducing order submission to the normal `python bot.py` path.
- Slow SMA paper execution changes.
- Paper-order smoke test changes.
- Command-routing changes touching execution paths.
- Config default changes.
- Scheduling, cron, or loop changes.
- Risk or kill-switch enforcement changes.
- Generated CSV, log, database, or chart changes.
- Anything involving credentials or secrets.

For medium/high-risk changes, Codex may make a local branch or local commit only if explicitly asked, but must not push until the user reviews the diff and approves.

## Towards Live Paper Monitoring

The staged direction is operational paper monitoring without jumping straight to automated order execution:

A. Expand ticker universe in research/preview only.
B. Add or improve ticker-universe validation and reporting.
C. Add more frequent market monitoring as preview, display, or report only.
D. Add loop or cron support only after single-run commands are stable.
E. Add lockfile/no-overlap protection before any repeated run.
F. Add portfolio risk controls before expanded paper execution.
G. Keep paper execution separate, explicit, confirmation-gated, and manually reviewed.
H. Do not treat monitoring signals as execution approval.

More frequent price checks do not mean more frequent trades. Daily strategies should not overtrade intraday noise unless a separate intraday strategy is researched and validated. For now, frequent monitoring means observe, report, and preview; it does not mean submit orders. Any execution-capable loop or scheduled order workflow remains not approved.

## No-Overlap / Lockfile Readiness Boundary

Before any repeated market-monitor refresh is considered, add no-overlap
protection as a separate reviewed effort. Overlapping report runs could collide
while fetching data, writing CSVs, updating caches, or producing quality reports,
so the future lockfile is for report integrity only.

The monitor lockfile helper is pure/no-network and now prevents overlapping safe
refresh/report commands only. It is applied exactly to
`python bot.py --monitor-lockfile-readiness-report`,
`python bot.py --refresh-promoted-review`, and
`python bot.py --refresh-defensive-research`.

Stale lock handling is conservative: stale lockfiles require manual review, not
automatic deletion. Lock metadata may include command name, `started_at`, host,
pid, `lock_version`, and optional `stale_after_seconds` if safe, but must not
include secrets, account IDs, config contents, order IDs, webhook URLs, API
keys, logs, database contents, generated CSV contents, generated trading data,
trading history, positions, or report contents.

This applies only to report, preview, display, and monitor refresh commands.
Execution-capable commands must never be scheduled and must not be protected
merely by a lockfile. A lockfile does not approve scheduling, execution, or paper
orders.

Use `python scripts\verify_monitor_lockfile_final_state.py` to verify the final
three-command lock boundary, stale-lock manual-review policy, false
execution/scheduling approval flags, and VPS handoff documentation.

For VPS monitoring, prefer terminal-only report/display commands. The
`python bot.py --vps-monitoring-status` command is safe to route before top-level
Alpaca imports so it can report environment status without requiring trading
dependencies at startup. The `python bot.py --market-monitor-scheduling-readiness-report`
checkpoint uses the same narrow report-only route and assesses only the three
VPS-safe lock-wrapped monitoring commands for future manual scheduling review.
Keep these exceptions narrow: do not weaken normal bot, paper-order-test,
slow-SMA paper execution, or any execution-capable dependency checks.

Hermes cron preferred for future monitoring scheduling if configured, but no
refresh cron job or execution scheduling is currently approved or created beyond
the existing status-only job. Use Hermes cron for safe
monitoring/reporting only; not for execution. Do not paste config/API
keys/webhooks/account IDs into Hermes prompts. Initial cron candidate should
probably be a status/checkpoint job before refresh jobs. Refresh jobs should
remain protected by lockfile/no-overlap, and a stale lock requires manual
review. Scheduling cadence is a separate future decision; a future review must
approve exact cadence, exact command list, enabled toolsets, output destination,
and failure behaviour before any Hermes cron job is created.

Use `docs/HERMES_CRON_JOB_DESIGN.md` and
`python scripts\verify_hermes_cron_job_design.py` for the current status-job
checkpoint. That checkpoint records the verified status-only Hermes cron and
confirms refresh commands still require a later separate review.

The current `paper-bot-vps-status-check` Hermes cron is status-only. Job ID is
`345188fbb60c`; cadence is daily at 10:10am UK local time with cron expression
`10 10 * * *`; delivery is Telegram; mode is script-only / no-agent; working
directory is `C:\dev\paper-trading-bot`; the command sequence is repo safety,
Hermes cron readiness, and `--vps-daily-monitoring-summary`. Verified output is `healthy_monitoring_state`,
action_required `no_action_required`, execution_approved false,
scheduling_approved false, and freshness_warnings: none. It does not run refresh
commands, trade, approve
execution, approve scheduling beyond this one status job, pull/commit/push code,
or inspect/print config contents, secrets, logs, databases, or full generated
CSV contents. A possible promoted-review refresh cron remains a future
manual-review item documented in
`docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md`; do not create or trigger it
during routine documentation or verifier work.
The older `docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` file is a legacy pointer
only. Use `docs/HERMES_CRON_MONITORING_RUNBOOK.md` and
`python scripts\verify_hermes_cron_monitoring_runbook.py` when interpreting
Telegram/status output from the existing status cron.

## Strategy Improvement Lab Boundary

`python bot.py --strategy-improvement-lab` is a research-only ETF allocation
lab for testing a fixed small set of more growth-aware variants. It may refresh
daily yfinance ETF history and write generated CSVs under `data/`, but it must
not load config, call Alpaca, read positions, submit/cancel/create orders, write
SQLite `trade_log`, send Discord alerts, schedule jobs, add shorting/leverage,
or approve execution.

`python bot.py --show-strategy-improvement-lab` is saved-CSV display only. Use
`python scripts\verify_strategy_improvement_lab.py` when changing the lab or
its command routing. Promising labels from the lab mean "research this further";
they are not buy/sell signals, order instructions, paper execution approval, or
scheduling approval.

`python bot.py --strategy-improvement-robustness` is the matching fixed
robustness layer for the same candidate set. It may refresh daily yfinance ETF
history and write generated robustness/cost/drawdown/comparison CSVs under
`data/`, but it must remain research-only and use fixed chronological splits and
fixed cost assumptions. Use
`python scripts\verify_strategy_improvement_robustness.py` when changing that
report. No cron, scheduling, or execution change is part of strategy
improvement research.

`python bot.py --strategy-improvement-diagnostics` is saved-CSV diagnostics for
the current best active strategy-improvement lead. It explains split
sensitivity, benchmark lag, cost stress, drawdown behaviour, cash drag, and
next fixed-hypothesis ideas without adding another strategy. Use
`python scripts\verify_strategy_improvement_diagnostics.py` when changing this
layer. Diagnostics are guidance for a later fixed research task, not tuning,
promotion, scheduling, or execution approval.

The first tested narrow refinement is `growth_biased_rotation_cost_aware_rebalance`.
It must preserve `growth_biased_rotation_crash_gate` unchanged and use the fixed
rebalance threshold documented in code. Judge it directly against the original
growth-biased strategy for turnover, cost sensitivity, split sensitivity, and
return drag. When diagnostics label it `cost_refinement_return_drag`, keep it
as tested/rejected research history rather than a next recommendation.

The second tested narrow refinement is `growth_biased_rotation_partial_defensive_sleeve`.
It must preserve `growth_biased_rotation_crash_gate` unchanged, use fixed
defensive-sleeve allocations only when breadth/regime weakens, and be judged
against the original growth-biased strategy, the cost-aware refinement, monthly
ETF rotation, and SPY. It is research-only and must not change scheduling,
execution, or strategy-to-order wiring. When diagnostics label it
`defensive_sleeve_return_drag`, keep it as tested/rejected research history.

The remaining fixed batch tested `growth_biased_rotation_reentry_filter`,
`growth_biased_rotation_regime_recovery_filter`, and fixed 45%/55% breadth-gate
reviews. `growth_biased_rotation_breadth_stricter_gate` is now the active
research lead, with `growth_biased_rotation_crash_gate` retained as the previous
baseline. Next work should validate the stricter gate with split, cost-stress,
drawdown-period, and promotion-checkpoint reports. Do not add random variants,
ML, intraday logic, scheduling, execution, or strategy-to-order wiring.

Use `python bot.py --growth-biased-stricter-validation` for the dedicated
stricter-gate validation checkpoint covering deeper split validation,
drawdown-period review, cost stress, benchmark comparison, and
`python bot.py --show-growth-biased-stricter-validation` for the saved display.
The checkpoint can support future preview-candidate discussion only; it must
not approve execution, paper execution, promoted execution, scheduling, or cron.

Use `python bot.py --growth-biased-stricter-promotion-readiness` after the
saved stricter-gate validation exists when the question is what still blocks
future preview-candidate discussion. It reads saved outputs only and writes
benchmark, split, cost, drawdown, saved-output, and final preview-readiness
blocker rows. `python bot.py --show-growth-biased-stricter-promotion-readiness`
is saved-display only. The report does not approve preview promotion,
execution, paper execution, scheduling, or strategy-to-order wiring.

## MCP Feasibility Boundary

MCP may be considered later as a tiny local/custom safe operations adapter for
VPS/Hermes report, display, and monitor commands only. It is not approved for
implementation yet, and it must not become a trading execution interface.

Any future MCP proof of concept must use a hardcoded allowlist, deny by default,
use fixed working directory `C:\dev\paper-trading-bot`, avoid arbitrary shell
access, avoid secrets and generated data by default, and return
`execution_approved=False` and `scheduling_approved=False` where applicable.
The first possible tools should be limited to `repo_safety_check` and
`refresh_market_monitor` only after VPS readiness reports are stable and
no-overlap or lockfile protection exists.

A future market/financial news layer may be researched only as a risk veto. It
may label tickers with `block_new_entries_today`, `manual_review_required`, or
`no_news_block`, and may block or flag new long entries for major negative or
event-risk news. It must not generate buy signals, sell signals, order
instructions, position sizing, or execution approval. News output must include
source, observed time, confidence, and reason, and stale vetoes must expire
automatically.

## More Tickers Rule

More tickers should start with liquid U.S. stocks and ETFs only. Universe expansion must land in research/preview first, with liquidity, price, and duplicate validation before any execution review.

Before expanded paper execution is considered, more tickers require portfolio risk limits, max open positions, max notional exposure, and concentration checks.

## Socratic Preflight Questions

For non-trivial tasks, start by answering:

- What is the smallest safe change?
- Which files are expected to change?
- Which files must not change?
- Is this docs, research, preview/display, refactor, or execution-related?
- What accidental side effects could happen?
- What verifier or no-network check is needed?
- When should Codex stop instead of continuing?

Stop and ask before proceeding if a task might submit/cancel orders, alter live/paper positions, expose secrets, change normal `python bot.py` behavior, or weaken paper-only safety.

## Standard Report-Back Format

Report back with:

- Files changed
- Command added or changed, if any
- Verification run and result
- Git status summary, if committing or pushing
- Whether Python code changed
- Whether any execution paths changed
- Whether secrets or generated artefacts were touched
- Whether Codex committed/pushed or only edited locally
- Whether the known sandbox yfinance/Discord network limitation appeared

Keep successful routine verifier blocks concise. "Passed" is enough unless there is a failure, traceback, new warning, or unexpected output.

Before commits or pushes, run `python scripts\verify_repo_safety.py` to check that private config, environment files, generated data, logs, charts, databases, and secret-like filenames are not tracked or staged.

## CMD Verification Convention

When the user asks for Windows/CMD-style verification, keep command blocks easy to paste and avoid noisy output in the final report. For routine verifier blocks, summarize only the pass/fail status unless something unusual appears.

Known sandbox limitation: local Codex runs may fail network-backed checks that need yfinance or Discord. Treat that as an environment limitation when the no-network verifiers pass and the failure is clearly a blocked network call.

Paper-live evidence reconciliation uses `python bot.py --paper-live-evidence-audit` and `python bot.py --show-paper-live-evidence-audit`. These commands are saved-output-only QQQ100 reports: they may identify exact missing saved files or fields and reconcile saved desired/position/order/alignment state, but they must keep `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`.

QQQ100 postcheck readiness uses `python bot.py --qqq100-postcheck-readiness-report` and `python bot.py --show-qqq100-postcheck-readiness-report`. These commands are runbook-only and must not run `python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check`; that read-only broker check requires a separate explicit user approval.

QQQ100 follow-up policy uses `python bot.py --qqq100-followup-policy-report` and `python bot.py --show-qqq100-followup-policy-report`. These commands are saved-output-only and may report `no_action_required_already_aligned`, but they must not create executable order instructions or approve repeat/follow-up orders.

QQQ100 daily decision uses `python bot.py --qqq100-daily-decision-report` and `python bot.py --show-qqq100-daily-decision-report`. These commands read saved QQQ100 evidence and follow-up policy only, can report `qqq100_daily_decision_hold_no_action_aligned_long`, and must not approve execution, paper execution, repeat/follow-up orders, live trading, scheduling, or executable order instructions.

QQQ100 manual flatten readiness uses `python bot.py --qqq100-manual-flatten-readiness-report` and `python bot.py --show-qqq100-manual-flatten-readiness-report`. These commands read saved QQQ100 evidence and follow-up policy only, should report `flatten_not_needed_currently` while the saved desired state remains long/aligned, and may only label `future_manual_flatten_discussion_possible_not_approved` if future saved evidence says desired flat while holding exactly one QQQ share. They must not create order instructions or approve a flatten action.

QQQ100 manual flatten runbook uses `python bot.py --qqq100-manual-flatten-runbook-report` and `python bot.py --show-qqq100-manual-flatten-runbook-report`. These commands read the saved flatten readiness checkpoint only, should report `manual_flatten_runbook_not_needed_currently` while QQQ100 remains aligned long one share, and may only label `manual_flatten_runbook_manual_review_required_not_approved` for a future saved flat-plus-one case. They must not create order instructions, approve manual flatten, or approve flatten execution.

Paper-live promotion ladder status uses `python bot.py --paper-live-promotion-ladder-status` and `python bot.py --show-paper-live-promotion-ladder-status`. These commands read saved ladder design and QQQ100 monitoring outputs only, keep QQQ100 as the only current seed, keep high-growth and crypto research-only, keep defensive sleeves future-review-only, and keep portfolio backtests not promotion evidence until accounting consistency is proven.

Paper-live monitoring status uses `python bot.py --paper-live-monitoring-status` and `python bot.py --show-paper-live-monitoring-status`. These commands are saved-output-only monitoring/report commands; they must not create, edit, trigger, or schedule Hermes cron jobs and must preserve `never_schedule_order_capable_commands=true`.
The safe VPS monitoring status and daily monitoring summary include that saved paper-live status and the saved QQQ100 daily decision when available, so the existing Telegram status job can show `qqq_100_trend_gate` / `QQQ` aligned long one share, `qqq100_daily_decision_hold_no_action_aligned_long`, `no_action_required=True`, `hold_no_action_and_monitor_only`, and repeat/follow-up order approvals still false. This is report integration only; do not add paper-live commands to the Hermes cron sequence.

Paper-live checklist status uses `python bot.py --paper-live-checklist-status` and `python bot.py --show-paper-live-checklist-status`. It is the saved-output closeout for the current QQQ100 monitoring phase: Steps 1-11 may be complete or complete-for-current-QQQ100-monitoring-phase, while Step 12 remains future-only for a later generic promotion ladder. It must not approve execution, repeat/follow-up orders, live trading, or scheduling.

Paper-live F6/F7 audit uses `python bot.py --paper-live-f6-f7-audit` and `python bot.py --show-paper-live-f6-f7-audit`. It is static/report-only: F6 checks that unknown positions remain loud and are not assumed flat; F7 keeps starting-cash/accounting consistency as manual-review work before portfolio backtests can become promotion evidence. It must not run market-data backtests, call Alpaca/yfinance, read positions, build the generic promotion ladder, or approve execution/scheduling.

Paper-live F6/F7 targeted checks use `python scripts\verify_paper_live_f6_f7_targeted_checks.py`. This is no-network verifier coverage only: unknown positions must remain `position_unknown` / `position_unavailable` / manual-review states, and portfolio backtests remain not promotion evidence until accounting consistency is proven. Do not use this checkpoint to promote multi-sleeve, high-growth, defensive, crypto, SMA, or slow-SMA paths.

Paper-live promotion ladder design uses `python bot.py --paper-live-promotion-ladder-design` and `python bot.py --show-paper-live-promotion-ladder-design`. It is report-only design scaffolding for future stage labels: `research_candidate`, `preview_candidate`, `paper_live_candidate`, and `manually_executable_candidate`. QQQ100 is the only current seed, current QQQ100 stays monitor-only/aligned long one share, no repeat/follow-up order is approved, multi-sleeve is future-only, high-growth and crypto stay research-only, defensive sleeves stay future-review only, no SMA/slow-SMA paper-live promotion is allowed, portfolio backtests are not promotion evidence until accounting consistency is proven, unknown positions block/manual-review, and no scheduled execution is allowed.

Paper-live multi-sleeve roadmap uses `python bot.py --paper-live-multi-sleeve-roadmap` and `python bot.py --show-paper-live-multi-sleeve-roadmap`. It is a saved-output QQQ-led multi-sleeve roadmap only: QQQ100 core sleeve remains the current monitor-only base and only current seed, defensive sleeve is future review only, high-growth sleeve remains research-only until concentration/drawdown/attribution review is complete, crypto sleeve remains research-only/capped/future-only with no crypto execution approved, and the allocator has no portfolio execution wiring, no order instructions, and no scheduled execution.

Paper-live next-phase backlog uses `python bot.py --paper-live-next-phase-backlog` and `python bot.py --show-paper-live-next-phase-backlog`. It is a report-only checklist of prerequisites before any sleeve moves through the ladder: QQQ100 core remains monitor-only/no-action, generic ladder implementation is future-only, F6/F7 keeps unknown positions loud and portfolio accounting unproven, defensive/high-growth/crypto/allocator work needs saved-output evidence review, and Monitoring/Hermes remains monitoring-only with order-capable commands never scheduled.

Paper-live multi-sleeve evidence-gap audit uses `python bot.py --paper-live-multi-sleeve-evidence-gap` and `python bot.py --show-paper-live-multi-sleeve-evidence-gap`. It checks saved-output file presence only, treats missing saved outputs as blockers/manual-review items, and must not rerun research, refresh market data, promote sleeves, create action previews, create order instructions, wire portfolio execution, or schedule anything.

Paper-live high-growth evidence-gap audit uses `python bot.py --paper-live-high-growth-evidence-gap` and `python bot.py --show-paper-live-high-growth-evidence-gap`. It checks saved-output file presence only for high-growth lead evidence, concentration/top-contributor dependency, drawdown, attribution, survivorship/current-constituent/outlier warnings, and promotion readiness. It must not rerun research, refresh market data, promote high-growth, create action previews, create order instructions, wire portfolio execution, or schedule anything.

Paper-live high-growth evidence quality review uses `python bot.py --paper-live-high-growth-evidence-quality` and `python bot.py --show-paper-live-high-growth-evidence-quality`. It reads only canonical saved high-growth evidence CSVs and summarizes concentration/outlier, drawdown, attribution, bias-risk, and promotion-readiness quality as manual-review context. It must not approve high-growth promotion, preview, paper-live, action previews, order instructions, execution wiring, market refresh, broker calls, or scheduling.

Paper-live high-growth manual-review decision uses `python bot.py --paper-live-high-growth-manual-review-decision` and `python bot.py --show-paper-live-high-growth-manual-review-decision`. It reads only saved high-growth evidence-gap and evidence-quality outputs, should report `high_growth_remains_research_only_manual_review_required` when outlier/concentration/drawdown/bias warnings remain, and must keep QQQ100 as the cleaner current paper-live monitor base. It must not permanently reject high-growth, but future reconsideration requires stronger concentration, attribution, split/cost, portfolio-accounting, F6/F7, and risk-policy evidence with no order instructions or scheduling.

High-growth strategy discovery sprint uses `python bot.py --high-growth-strategy-discovery-sprint` and `python bot.py --show-high-growth-strategy-discovery-sprint`. It is saved-output-only research across aggressive trend/breakout, relative strength/rotation, crypto/risk-on, experimental allocation, backtest engineering, robustness/audit, and evidence/reporting workstreams. It may identify multiple strong research candidates, but it must not promote high-growth, create preview implementation, create order instructions, refresh market data, call Alpaca, or approve execution/scheduling.

Higher-growth preview readiness uses `python bot.py --higher-growth-preview-readiness-pack` and `python bot.py --show-higher-growth-preview-readiness-pack`. It is saved-output-only manual-review evidence for `higher_growth_70_20_5_5` versus QQQ100 and the balanced multi-sleeve comparator. It may report `higher_growth_preview_discussion_ready_manual_review_required`, but it must not implement preview mode, create action previews, create order instructions, promote high-growth, refresh market data, call Alpaca, or approve execution/scheduling.

Higher-growth candidate selection uses `python bot.py --higher-growth-candidate-selection-decision` and `python bot.py --show-higher-growth-candidate-selection-decision`. It may select `higher_growth_70_20_5_5` for future saved-output preview-design review, keep `balanced_multi_sleeve_research_portfolio` as the runner-up, and defer crypto blend candidates behind crypto policy review. It must not implement preview mode, create action previews, create order instructions, promote high-growth/crypto, call Alpaca, or approve execution/scheduling.

Higher-growth preview design uses `python bot.py --higher-growth-preview-design` and `python bot.py --show-higher-growth-preview-design`. It documents the future preview-only shape for `higher_growth_70_20_5_5`, including target sleeve weights and allowed saved-output fields. It must not create the actual preview signal, create action previews, include order side/quantity/type/account fields, call Alpaca, or approve execution/scheduling.

Volatility-targeted growth research sprint uses `python bot.py --vol-targeted-growth-research-sprint` and `python bot.py --show-vol-targeted-growth-research-sprint`. It is saved-output-only research using existing return streams to test volatility targeting, drawdown control, growth momentum risk overlays, and multi-sleeve risk allocation. It may identify strong research candidates, but it must not create preview signals, action previews, order instructions, market-data refreshes, Alpaca calls, high-growth/crypto promotion, or execution/scheduling approval.

Volatility-targeted growth manual review uses `python bot.py --vol-targeted-growth-manual-review-pack` and `python bot.py --show-vol-targeted-growth-manual-review-pack`. It reads only the saved volatility-targeted sprint outputs and compares `high_growth_balanced_target_vol_25_win_20_cap_1x` with `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`. It may identify the multi-sleeve candidate as the cleaner next research path, but it must not implement preview mode, create action previews, create order instructions, call Alpaca, or approve execution/scheduling.

Volatility-targeted growth robustness checkpoint uses `python bot.py --vol-targeted-growth-robustness-checkpoint` and `python bot.py --show-vol-targeted-growth-robustness-checkpoint`. It reads saved volatility-targeted outputs only and checks the preferred multi-sleeve candidate for parameter-neighbourhood support, split stability, drawdown tradeoff, and baseline context. It must keep preview design, action previews, order instructions, broker calls, and execution/scheduling approval blocked.

Volatility-targeted growth nearby-variants review uses `python bot.py --vol-targeted-growth-nearby-variants-review` and `python bot.py --show-vol-targeted-growth-nearby-variants-review`. It reads saved volatility-targeted outputs only and compares the preferred 15% target / 20-day setting against adjacent target-vol/window variants. It may identify a higher-return neighboring challenger, but it must keep preview design, action previews, order instructions, broker calls, and execution/scheduling approval blocked.

Volatility-targeted growth preview-readiness decision uses `python bot.py --vol-targeted-growth-preview-readiness-decision` and `python bot.py --show-vol-targeted-growth-preview-readiness-decision`. It reads saved nearby-variant and robustness outputs only, selects `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` for future preview-design review, and keeps the 20/20 and 25/20 variants as challengers. It may mark preview-design discussion ready for manual review, but it must not implement preview mode, create action previews, create order instructions, call Alpaca, or approve execution/scheduling.

Volatility-targeted growth preview design uses `python bot.py --vol-targeted-growth-preview-design` and `python bot.py --show-vol-targeted-growth-preview-design`. It reads saved preview-readiness outputs only and documents a future preview-only shape for `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`: 15% volatility target, 20-day volatility window, 1x exposure cap, no leverage, and saved candidate/weight/status/blocker outputs only. It must not create the actual preview signal, create action previews, include order side/quantity/type/account fields, call Alpaca, or approve execution/scheduling.

Volatility-targeted growth preview signal uses `python bot.py --vol-targeted-growth-preview-signal` and `python bot.py --show-vol-targeted-growth-preview-signal`. It reads saved preview-design/readiness evidence only and writes candidate identity, volatility settings, target sleeve weights, blockers, and safety flags for `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`. It must not create action previews, include order side/quantity/type/account fields, call Alpaca, refresh market data, or approve execution/scheduling.

Volatility-targeted growth action-preview design uses `python bot.py --vol-targeted-growth-action-preview-design` and `python bot.py --show-vol-targeted-growth-action-preview-design`. It reads the saved preview signal only and documents how a future action-preview checkpoint should stay manual-review-only, loud on unknown position state, and free of order side/quantity/type/account fields. It must not create actual action-preview rows, read broker positions, call Alpaca, refresh market data, or approve execution/scheduling.

Volatility-targeted growth action preview uses `python bot.py --vol-targeted-growth-action-preview` and `python bot.py --show-vol-targeted-growth-action-preview`. It reads saved preview-signal/design outputs only and creates sleeve-level manual-review rows with `current_exposure_not_read` by default. It must not read broker positions, call Alpaca, refresh market data, include order side/quantity/type/account fields, or approve execution/scheduling.

Volatility-targeted growth broker-position comparison design uses `python bot.py --vol-targeted-growth-broker-position-comparison-design` and `python bot.py --show-vol-targeted-growth-broker-position-comparison-design`. It documents the future gates for an explicit read-only broker comparison, but must not call Alpaca, read positions, create order instructions, or approve execution/scheduling.

Volatility-targeted growth portfolio-risk review uses `python bot.py --vol-targeted-growth-portfolio-risk-review` and `python bot.py --show-vol-targeted-growth-portfolio-risk-review`. It reads saved action-preview and review outputs only, keeps the candidate research-only, and must not approve paper-live candidacy, execution, broker reads, or scheduling.

Volatility-targeted growth portfolio-risk policy design uses `python bot.py --vol-targeted-growth-portfolio-risk-policy-design` and `python bot.py --show-vol-targeted-growth-portfolio-risk-policy-design`. It proposes guardrails for allocation caps, high-growth/crypto sleeves, drawdown review, broker-position review, and execution boundaries. It must not enforce policy, approve paper-live candidacy, read broker positions, create order instructions, or approve execution/scheduling.

Volatility-targeted growth paper-live decision uses `python bot.py --vol-targeted-growth-paper-live-decision` and `python bot.py --show-vol-targeted-growth-paper-live-decision`. It keeps the 15/20 candidate research-only while marking a future read-only broker-position comparison as manual-review discussion-ready only. It must not call Alpaca, read positions, create order instructions, approve paper-live candidacy, or approve execution/scheduling.

Volatility-targeted growth broker-comparison run-readiness uses `python bot.py --vol-targeted-growth-broker-comparison-run-readiness` and `python bot.py --show-vol-targeted-growth-broker-comparison-run-readiness`. It checks whether the saved chain is ready to request explicit manual approval for a future read-only broker-position comparison, but it must not grant approval, call Alpaca, read positions, create order instructions, approve paper-live candidacy, or approve execution/scheduling.

Volatility-targeted growth broker-position comparison uses `python bot.py --vol-targeted-growth-broker-position-comparison` and `python bot.py --show-vol-targeted-growth-broker-position-comparison`. Default mode must not call Alpaca and should write a confirmation-required report; confirmed read-only mode requires `--confirm-readonly-alpaca-check` in a separately approved run and still must not create order instructions, approve paper-live candidacy, or approve execution/scheduling. The strategy is a research-only 70% QQQ100, 20% high-growth, 5% crypto, 5% defensive sleeve mix with a 15% volatility target, 20-day volatility window, and 1x cap.

Volatility-targeted growth post-comparison decision uses `python bot.py --vol-targeted-growth-post-comparison-decision` and `python bot.py --show-vol-targeted-growth-post-comparison-decision`. It reads saved comparison outputs only and may mark the chain ready to design a stricter manual paper-live discussion gate. It must not call Alpaca, read positions, create order instructions, approve the gate, approve paper-live candidacy, or approve execution/scheduling.

Volatility-targeted growth stricter paper-live gate design uses `python bot.py --vol-targeted-growth-stricter-paper-live-gate-design` and `python bot.py --show-vol-targeted-growth-stricter-paper-live-gate-design`. It defines hard blockers before any paper-live discussion: QQQ100 stays the incumbent seed, allocation cap is separate, high-growth/crypto stay research-only, drawdown/stress and broker-position context require review, and no executable order fields are allowed. It must not enforce or approve the gate, call Alpaca, read positions, create order instructions, or approve execution/scheduling.

Volatility-targeted growth gate review uses `python bot.py --vol-targeted-growth-gate-review` and `python bot.py --show-vol-targeted-growth-gate-review`. It applies the stricter gate to saved evidence and may mark the candidate ready for limited manual discussion only. It must not enforce the gate, approve paper-live candidacy, call Alpaca, read positions, create order instructions, or approve execution/scheduling.

Volatility-targeted growth candidate discussion uses `python bot.py --vol-targeted-growth-candidate-discussion` and `python bot.py --show-vol-targeted-growth-candidate-discussion`. It compares QQQ100 and the volatility-targeted candidate in plain English and may mark the latter as a non-executable proposal for manual review only. It must not displace QQQ100, add preview/action implementation, call Alpaca, read positions, create order instructions, or approve execution/scheduling.

Volatility-targeted growth proposal implementation design uses `python bot.py --vol-targeted-growth-proposal-implementation-design` and `python bot.py --show-vol-targeted-growth-proposal-implementation-design`. It documents what a later non-executable preview/action proposal would require, while leaving implementation unadded. It must not create order fields, call Alpaca, read positions, displace QQQ100, wire execution, or approve execution/scheduling.

Volatility-targeted growth proposal preview schema uses `python bot.py --vol-targeted-growth-proposal-preview-schema` and `python bot.py --show-vol-targeted-growth-proposal-preview-schema`. It defines allowed review fields and forbidden executable/account/secret fields for a future proposal preview. It must not add preview implementation, create order fields, call Alpaca, read positions, displace QQQ100, wire execution, or approve execution/scheduling.

Volatility-targeted growth proposal preview uses `python bot.py --vol-targeted-growth-proposal-preview` and `python bot.py --show-vol-targeted-growth-proposal-preview`. It creates saved sleeve-level review rows from allowed schema fields only. It must not call Alpaca, read positions, create order fields, displace QQQ100, add action preview behavior, wire execution, or approve execution/scheduling.

Volatility-targeted growth seed-change review uses `python bot.py --vol-targeted-growth-seed-change-review` and `python bot.py --show-vol-targeted-growth-seed-change-review`. It compares the saved proposal preview against QQQ100 as the incumbent seed and may allow manual consideration to continue only. It must not change the seed, approve QQQ100 displacement, call Alpaca, read positions, create order fields, wire execution, or approve execution/scheduling.
