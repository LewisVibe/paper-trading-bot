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

Conclusion: pause short-selling research for now. Do not add short preview or short execution. Only revisit short research if a new fixed hypothesis is supported by external research and includes borrow-fee, borrow-availability, recall, squeeze, and short-sale constraint modelling. `allow_shorting` must remain default false. No short execution, short preview, or short crypto support is approved.

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
- The project research state refresh consolidates current stock/ETF and crypto research state so the next research/reporting direction can be chosen cleanly. It does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.
- `python bot.py --show-current-research-state` is a concise terminal display helper. It reads saved project research state, does not refresh market data, does not approve preview promotion, does not approve execution, and does not connect strategies to Alpaca or paper orders.
- `python bot.py --project-research-state-quality-report` writes `data/project_research_state_quality_report.csv`. It reads saved project research state only, checks freshness, required fields, and false approval flags, and reports warning/blocker rows for stale, missing, or non-false approval states. It does not approve scheduling or execution.
- `python bot.py --stock-etf-paper-execution-readiness-report` writes `data/stock_etf_paper_execution_readiness_report.csv`. It is a saved-data/static-source discussion checkpoint for whether the current stock/ETF research lead is ready even to discuss a future manually reviewed Alpaca paper-execution design. Current expected status is conservative: `codex_ambitious_concentrated_growth_persistence` remains research-only with 25 bps cost review, preview, execution eligibility, kill-switch, portfolio-risk, crypto-out-of-scope, and scheduling boundaries still blocking or requiring manual review. It does not read credentials, call Alpaca, read positions, create orders, write SQLite `trade_log`, send alerts, schedule anything, or approve paper execution.
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
