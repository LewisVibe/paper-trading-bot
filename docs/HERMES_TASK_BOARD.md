# Hermes Task Board

This task board is guidance only. It does not approve execution, scheduling, or strategy-to-paper integration. Any execution-capable, order-capable, scheduling, or strategy-integration work still requires a separate explicit review and manual confirmation.

Cross-references:
- `docs/HERMES_WORKFLOW.md`
- `docs/CURRENT_STATE.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/V2_REFACTOR_INVENTORY.md`
- `docs/VPS_SETUP_CHECKLIST.md`

Latest execution-safety checkpoint: normal `python bot.py` is now monitoring-only and must not submit Alpaca orders or mutate position state. Order-capable paper paths remain separate and explicitly confirmed; manual paper sells have an oversell guard when shorting is disabled; QQQ100 paper alignment is exact zero/one-share only and blocks/manual review for more than one QQQ share; `paper_kill_switch_enabled` is real config/env state with safe default `false`.

Paper-live promotion checkpoint: `python bot.py --paper-live-promotion-gate` is saved-output/report-only and limited to `qqq_100_trend_gate` / `QQQ` as the first paper-live candidate discussion gate. `paper_live_candidate=True` is a manual-discussion label only; execution, paper execution, scheduling, and order instructions remain false. Do not use this gate to promote SMA, slow-SMA, high-growth, crypto, QQQ150, or adaptive QQQ.

Paper-live readiness checkpoint: `python bot.py --paper-live-readiness-report` is saved-output/report-only and summarizes whether the project is ready for any future manually confirmed QQQ100 paper-action discussion. It must keep `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, and `live_trading_approved=false`; it must not be used to create schedules or run order-capable commands.

Paper-live state checkpoint: `python bot.py --paper-live-state-summary` is saved-output/report-only and summarizes the current saved QQQ100 paper-live state before any future manual command discussion. It must keep `execution_approved=false`, `paper_execution_approved=false`, `scheduling_approved=false`, `live_trading_approved=false`, and `followup_order_approved=false`; it must not read live positions or trigger order-capable commands.

## 1. Safe now

### Task: QQQ100 repeat/alignment workflow design review
- **Purpose:** Review the saved-output-only QQQ100 repeat/alignment design before any future repeat execution command change.
- **Risk level:** Medium / report-only design, because it is adjacent to a manual paper execution path.
- **Allowed files:**
  - `trading_bot/research/qqq100_repeat_alignment_workflow_design.py`
  - `scripts/verify_qqq100_repeat_alignment_workflow_design.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_qqq100_repeat_alignment_workflow_design.py` and repo safety/inventory verifiers only.
- **Stop condition:** Stop if the task starts adding a repeat execution command, expanding `--execute-qqq100-paper`, reading broker state, calling Alpaca, changing config defaults, approving scheduling, or approving follow-up/repeat orders.

### Task: Multi-sleeve strategy monitor review
- **Purpose:** Review the saved-output-only monitor that places QQQ100 beside defensive, high-growth, crypto, and cash/no-position sleeves without connecting those sleeves to execution.
- **Risk level:** Medium / report-only design, because it describes future portfolio-style sleeves near an existing manual paper milestone.
- **Allowed files:**
  - `trading_bot/research/multi_sleeve_strategy_monitor.py`
  - `scripts/verify_multi_sleeve_strategy_monitor.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_multi_sleeve_strategy_monitor.py` and repo safety/inventory verifiers only.
- **Stop condition:** Stop if the task starts adding new execution commands, expanding `--execute-qqq100-paper`, reading broker state, calling Alpaca, refreshing market data, changing config defaults, approving scheduling, or wiring defensive/high-growth/crypto sleeves to execution.

### Task: QQQ100 stream reconciliation review
- **Purpose:** Review why the generated `qqq_100_trend_gate` daily return stream differs from saved QQQ100 benchmark metrics before changing any stream configuration or portfolio labels.
- **Risk level:** Medium / research-only reconciliation, because it sits near the active QQQ100 paper sleeve and generated multi-sleeve research metrics.
- **Allowed files:**
  - `trading_bot/research/qqq100_stream_reconciliation.py`
  - `scripts/verify_qqq100_stream_reconciliation.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules
  - QQQ100 paper execution code unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_qqq100_stream_reconciliation.py` and repo safety/inventory verifiers only.
- **Stop condition:** Stop if the task starts expanding `--execute-qqq100-paper`, adding repeat execution, calling Alpaca, reading broker state, changing config defaults, approving scheduling, treating a material metric-gap candidate or fixed recovered-inputs reconstruction candidate as fully reconciled, silently replacing the old generated QQQ100 diagnostic stream without an audit row, or treating a reconciliation candidate as execution approval.

### Task: QQQ100 benchmark-input reconstruction review
- **Purpose:** Document the recovered source chain and unresolved gaps behind the saved `qqq_100_trend_gate` benchmark metrics before changing any generated QQQ100 stream.
- **Risk level:** Medium / report-only reconstruction, because it sits near active QQQ100 paper-sleeve research and should not become execution evidence.
- **Allowed files:**
  - `trading_bot/research/qqq100_benchmark_inputs.py`
  - `scripts/verify_qqq100_benchmark_inputs_report.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules
  - QQQ100 paper execution code
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_qqq100_benchmark_inputs_report.py` and repo safety/inventory/verifier-only checks.
- **Stop condition:** Stop if the task starts refreshing market data, calling Alpaca, reading broker state, updating sleeve return streams, changing QQQ100 paper execution, approving scheduling, or treating partial source recovery as execution approval.

### Task: High-growth return-stream review
- **Purpose:** Review saved daily high-growth stock return streams before they are used in any multi-sleeve research conclusion.
- **Risk level:** Medium / research-only stream generation, because it introduces high-risk stock branch returns near portfolio research.
- **Allowed files:**
  - `trading_bot/research/high_growth_return_streams.py`
  - `scripts/verify_high_growth_return_streams.py`
  - `trading_bot/research/multi_sleeve_portfolio_backtest.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules
  - QQQ100 paper execution code
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_high_growth_return_streams.py` and repo safety/inventory verifiers only.
- **Stop condition:** Stop if the task starts approving preview, execution, paper execution, repeat execution, scheduling, or connecting high-growth streams to Alpaca/order paths.

### Task: Sleeve research scoreboard review
- **Purpose:** Review the saved-output-only scoreboard that ranks QQQ100, defensive ETF, high-growth, crypto, and Codex experimental candidate sleeves before choosing the next research pack.
- **Risk level:** Medium / report-only research ranking, because it compares future candidate sleeves near an active manual paper milestone.
- **Allowed files:**
  - `trading_bot/research/sleeve_research_scoreboard.py`
  - `scripts/verify_sleeve_research_scoreboard.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_sleeve_research_scoreboard.py` and repo safety/inventory verifiers only.
- **Stop condition:** Stop if the task starts adding preview/action/execution wiring, expanding `--execute-qqq100-paper`, reading broker state, calling Alpaca, refreshing market data, changing config defaults, approving scheduling, or wiring high-growth/defensive/crypto/Codex experimental sleeves to execution.

### Task: Codex QQQ defensive crash-gate research pack
- **Purpose:** Review the saved-output-only targeted research pack for `codex_qqq_defensive_crash_gate_research_sleeve` before any deeper validation work.
- **Risk level:** Medium / research-only, because it explores a Codex experimental sleeve near an active manual QQQ100 paper milestone.
- **Allowed files:**
  - `trading_bot/research/codex_qqq_defensive_crash_gate_research_pack.py`
  - `scripts/verify_codex_qqq_defensive_crash_gate_research_pack.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_codex_qqq_defensive_crash_gate_research_pack.py` and repo safety/inventory verifiers only.
- **Stop condition:** Stop if the task starts adding preview/action/execution wiring, expanding `--execute-qqq100-paper`, reading broker state, calling Alpaca, changing config defaults, approving scheduling, or turning the Codex experimental sleeve into an order path.

### Task: Sleeve return-stream generation checkpoint
- **Purpose:** Review the research-only daily return-stream layer that feeds reduced multi-sleeve portfolio metrics before any candidate label change.
- **Risk level:** Medium / research-only, because it may fetch QQQ/SPY research price data while staying separate from broker, position, order, and execution paths.
- **Allowed files:**
  - `trading_bot/research/sleeve_return_streams.py`
  - `trading_bot/research/multi_sleeve_portfolio_backtest.py`
  - `scripts/verify_sleeve_return_streams.py`
  - `scripts/verify_multi_sleeve_portfolio_backtest.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `scripts/verify_command_inventory.py`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_sleeve_return_streams.py`, `python scripts\verify_multi_sleeve_portfolio_backtest.py`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task starts calling Alpaca, reading live positions, creating order instructions, adding repeat execution, expanding `--execute-qqq100-paper`, promoting high-growth/crypto/Codex experimental sleeves, changing config defaults, approving scheduling, or inventing daily returns from summary metrics.

### Task: Multi-sleeve portfolio backtest checkpoint
- **Purpose:** Review the saved-output-only multi-sleeve portfolio research checkpoint before any candidate label change, preview discussion, or execution wiring.
- **Risk level:** Medium / research-only, because it compares QQQ100, defensive, high-growth, crypto, cash, and Codex experimental sleeve concepts near an active manual QQQ100 paper milestone.
- **Allowed files:**
  - `trading_bot/research/multi_sleeve_portfolio_backtest.py`
  - `scripts/verify_multi_sleeve_portfolio_backtest.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `scripts/verify_command_inventory.py`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_multi_sleeve_portfolio_backtest.py` and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task starts fetching broker data, calling Alpaca, reading live positions, creating order instructions, adding repeat execution, expanding `--execute-qqq100-paper`, promoting high-growth/crypto/Codex experimental sleeves, changing config defaults, approving scheduling, or inventing portfolio metrics when return streams are missing.

### Task: Crypto return-stream checkpoint
- **Purpose:** Review the research-only BTC/ETH daily return-stream layer that can feed crypto and QQQ100-plus-high-growth-plus-crypto multi-sleeve research candidates.
- **Risk level:** Medium / research-only, because the generator may fetch yfinance crypto data while staying separate from broker, position, order, execution, and scheduling paths.
- **Allowed files:**
  - `trading_bot/research/crypto_return_streams.py`
  - `trading_bot/research/multi_sleeve_portfolio_backtest.py`
  - `scripts/verify_crypto_return_streams.py`
  - `scripts/verify_multi_sleeve_portfolio_backtest.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `scripts/verify_command_inventory.py`
- **Forbidden files:**
  - `config.json`
  - `.env`
  - generated `data/` outputs
  - logs/databases/charts
  - Alpaca/order submission modules unless a separate explicit execution review allows it
  - scheduling, Hermes cron, Task Scheduler, service, or loop files
- **Allowed commands:** `python scripts\verify_crypto_return_streams.py`, `python bot.py --crypto-return-streams`, `python bot.py --show-crypto-return-streams`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task starts calling Alpaca, reading live positions, creating order instructions, adding crypto execution, enabling shorting/margin/leverage, changing config defaults, approving scheduling, treating LTC as active after the saved pause decision, or promoting crypto from research-only.

### Task: Multi-sleeve robustness checkpoint
- **Purpose:** Review saved split robustness for `qqq100_plus_high_growth_research` before any candidate label change, preview discussion, or execution wiring.
- **Risk level:** Medium / research-only validation near the active QQQ100 paper sleeve.
- **Allowed files:**
  - `trading_bot/research/multi_sleeve_robustness.py`
  - `scripts/verify_multi_sleeve_robustness.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `scripts/verify_command_inventory.py`
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_robustness.py` and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, promotes the candidate, changes config defaults, approves scheduling, or treats saved benchmark metrics as daily return streams.

### Task: Multi-sleeve crypto review checkpoint
- **Purpose:** Review saved split robustness, crypto turnover cost stress, and crypto volatility/drawdown contribution for `qqq100_plus_high_growth_plus_crypto_research` before any candidate label change, preview discussion, or execution wiring.
- **Risk level:** Medium / research-only validation near the active QQQ100 paper sleeve and a crypto research sleeve.
- **Allowed files:**
  - `trading_bot/research/multi_sleeve_crypto_review.py`
  - `scripts/verify_multi_sleeve_crypto_review.py`
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_RESEARCH_CHECKPOINT.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `scripts/verify_command_inventory.py`
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_crypto_review.py`, `python bot.py --multi-sleeve-crypto-review`, `python bot.py --show-multi-sleeve-crypto-review`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, promotes the candidate, changes config defaults, approves scheduling, or treats crypto as anything other than a research sleeve.

### Task: Multi-sleeve crypto containment review checkpoint
- **Purpose:** Review whether the fixed 5% crypto sleeve is contained enough inside `higher_growth_70_20_5_5` before any further candidate label change.
- **Risk level:** Medium / research-only containment review near the active QQQ100 paper sleeve and a crypto research sleeve.
- **Allowed files:** `trading_bot/research/multi_sleeve_crypto_containment.py`, `scripts/verify_multi_sleeve_crypto_containment.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_crypto_containment.py`, `python bot.py --multi-sleeve-crypto-containment-review`, `python bot.py --show-multi-sleeve-crypto-containment-review`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, reruns backtests from market data, optimises weights, or treats crypto containment as execution approval.

### Task: Multi-sleeve allocation policy review checkpoint
- **Purpose:** Review the fixed 75% QQQ100, 15% high-growth, 5% crypto, 5% defensive cash/bond allocation policy before any candidate label change, preview discussion, or execution wiring.
- **Risk level:** Medium / research-only validation near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/multi_sleeve_allocation_policy.py`, `scripts/verify_multi_sleeve_allocation_policy_review.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_allocation_policy_review.py`, `python bot.py --multi-sleeve-allocation-policy-review`, `python bot.py --show-multi-sleeve-allocation-policy-review`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, promotes the candidate, changes config defaults, approves scheduling, or treats allocation review as execution approval.

### Task: Multi-sleeve weight sensitivity checkpoint
- **Purpose:** Test a fixed nearby-weight set around the 75/15/5/5 crypto-inclusive candidate before any candidate label change, preview discussion, or execution wiring.
- **Risk level:** Medium / research-only validation near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/multi_sleeve_weight_sensitivity.py`, `scripts/verify_multi_sleeve_weight_sensitivity.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_weight_sensitivity.py`, `python bot.py --multi-sleeve-weight-sensitivity`, `python bot.py --show-multi-sleeve-weight-sensitivity`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, promotes the candidate, changes config defaults, approves scheduling, runs a broad optimiser/grid, or treats the weight review as execution approval.

### Task: Multi-sleeve higher-growth review checkpoint
- **Purpose:** Compare `higher_growth_70_20_5_5` with `current_75_15_5_5` across headline metrics, fixed splits, cost stress, drawdown windows, and contribution diagnostics before any candidate label change.
- **Risk level:** Medium / research-only validation near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/multi_sleeve_higher_growth_review.py`, `scripts/verify_multi_sleeve_higher_growth_review.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_higher_growth_review.py`, `python bot.py --multi-sleeve-higher-growth-review`, `python bot.py --show-multi-sleeve-higher-growth-review`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, promotes the candidate, changes config defaults, approves scheduling, runs a broad optimiser/grid, or treats the challenger review as execution approval.

### Task: Multi-sleeve research lead decision checkpoint
- **Purpose:** Decide whether `higher_growth_70_20_5_5` should become the current multi-sleeve research lead candidate versus `current_75_15_5_5` using saved higher-growth review evidence only.
- **Risk level:** Medium / research-only label decision near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/multi_sleeve_research_lead_decision.py`, `scripts/verify_multi_sleeve_research_lead_decision.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_research_lead_decision.py`, `python bot.py --multi-sleeve-research-lead-decision`, `python bot.py --show-multi-sleeve-research-lead-decision`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, runs a broad optimiser/grid, or treats the decision checkpoint as execution approval.

### Task: Multi-sleeve lead-state refresh checkpoint
- **Purpose:** Write one canonical saved-output state for the selected multi-sleeve research lead candidate after the research-lead decision checkpoint.
- **Risk level:** Medium / research-only state consolidation near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/multi_sleeve_lead_state.py`, `scripts/verify_multi_sleeve_lead_state.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_lead_state.py`, `python bot.py --multi-sleeve-lead-state-refresh`, `python bot.py --show-multi-sleeve-lead-state`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, reruns backtests, optimises weights, or treats the lead-state checkpoint as execution approval.

### Task: Multi-sleeve high-growth drawdown decomposition checkpoint
- **Purpose:** Decompose the drawdown effect of moving from `current_75_15_5_5` to `higher_growth_70_20_5_5` using saved return streams only.
- **Risk level:** Medium / research-only blocker review near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/multi_sleeve_high_growth_drawdown.py`, `scripts/verify_multi_sleeve_high_growth_drawdown.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_multi_sleeve_high_growth_drawdown.py`, `python bot.py --multi-sleeve-high-growth-drawdown-decomposition`, `python bot.py --show-multi-sleeve-high-growth-drawdown-decomposition`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, reruns backtests from market data, optimises weights, or treats the drawdown checkpoint as execution approval.

### Task: High-growth sleeve quality review checkpoint
- **Purpose:** Review the saved high-growth sleeve itself before any further label change for `higher_growth_70_20_5_5`.
- **Risk level:** Medium / research-only quality review near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/high_growth_sleeve_quality.py`, `scripts/verify_high_growth_sleeve_quality.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_high_growth_sleeve_quality.py`, `python bot.py --high-growth-sleeve-quality-review`, `python bot.py --show-high-growth-sleeve-quality-review`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, reruns backtests from market data, optimises weights, or treats sleeve quality as execution approval.

### Task: High-growth component attribution readiness checkpoint
- **Purpose:** Audit whether saved outputs contain real ticker/component attribution for the high-growth sleeve concentration blocker.
- **Risk level:** Medium / research-only attribution readiness review near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/high_growth_component_attribution.py`, `scripts/verify_high_growth_component_attribution.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases/generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_high_growth_component_attribution.py`, `python bot.py --high-growth-component-attribution`, `python bot.py --show-high-growth-component-attribution`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls yfinance, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, invents ticker attribution, or treats component attribution as execution approval.

### Task: High-growth component streams builder checkpoint
- **Purpose:** Reconstruct saved component ticker streams for `codex_broad_growth_balanced_breakout_control` using the existing high-growth research simulation.
- **Risk level:** Medium / research-only market-data-backed builder near the active QQQ100 paper sleeve and high-risk research sleeves.
- **Allowed files:** `trading_bot/research/high_growth_component_streams.py`, `scripts/verify_high_growth_component_streams.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases unrelated to generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_high_growth_component_streams.py`, `python bot.py --high-growth-component-streams`, `python bot.py --show-high-growth-component-streams`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, invents ticker attribution, changes the selected sleeve rule, optimises weights, or treats component streams as execution approval.

### Task: High-growth sleeve concentration review checkpoint
- **Purpose:** Use saved high-growth component streams to review ticker concentration, contribution dependency, and drawdown concentration for `codex_broad_growth_balanced_breakout_control`.
- **Risk level:** Low / saved-output-only research review.
- **Allowed files:** `trading_bot/research/high_growth_sleeve_concentration.py`, `scripts/verify_high_growth_sleeve_concentration.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases unrelated to generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_high_growth_sleeve_concentration.py`, `python bot.py --high-growth-sleeve-concentration-review`, `python bot.py --show-high-growth-sleeve-concentration-review`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls yfinance, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, optimises weights, changes the selected sleeve rule, or treats concentration review as execution approval.

### Task: High-growth research checkpoint consolidation
- **Purpose:** Consolidate the completed high-growth/multi-sleeve manual-review chain into one saved-output-only checkpoint.
- **Risk level:** Low / saved-output-only research checkpoint.
- **Allowed files:** `trading_bot/research/high_growth_research_checkpoint.py`, `scripts/verify_high_growth_research_checkpoint.py`, docs, README, and command inventory only.
- **Forbidden files:** config/secrets/logs/databases unrelated to generated outputs, Alpaca/order/position modules, scheduling, Hermes cron, Task Scheduler, service, or loop files.
- **Allowed commands:** `python scripts\verify_high_growth_research_checkpoint.py`, `python bot.py --high-growth-research-checkpoint`, `python bot.py --show-high-growth-research-checkpoint`, and repo safety/inventory/related research verifiers only.
- **Stop condition:** Stop if the task refreshes market data, calls yfinance, calls Alpaca, reads live positions, creates order instructions, adds crypto execution, enables shorting/margin/leverage, labels anything execution-ready, changes config defaults, approves scheduling, optimises weights, changes strategy logic, or treats the checkpoint as execution approval.

### Task: Documentation safety alignment review
- **Purpose:** Compare the workflow and safety docs explicitly named by the user for inconsistent safety wording. Common candidates are `HERMES_WORKFLOW.md`, `HERMES_TASK_BOARD.md`, `CODEX_WORKFLOW.md`, `CURRENT_STATE.md`, VPS checklist docs, and refactor inventory docs.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - The docs explicitly named by the user.
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `docs/CODEX_WORKFLOW.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_REFACTOR_INVENTORY.md` only if explicitly scoped.
  - `docs/VPS_SETUP_CHECKLIST.md` only if explicitly scoped.
- **Forbidden files:**
  - `config.json`
  - `.env`
  - `data/`
  - `logs/`
  - SQLite databases
  - generated CSVs/charts
  - auth/token/key files
  - Python code unless explicitly requested later
- **Allowed commands:** None by default. If user later permits verification: `python scripts\verify_repo_safety.py`.
- **Stop condition:** Stop if review requires reading config, generated artefacts, logs, databases, or source code.

### Task: Add/refresh safe handoff summary
- **Purpose:** Keep a concise docs-only handoff for Hermes/Codex/ChatGPT safety boundaries and next safe tasks.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - `docs/HERMES_WORKFLOW.md`
  - `docs/CURRENT_STATE.md`
  - possibly a new docs-only handoff file if explicitly requested
- **Forbidden files:**
  - Python code
  - config/secrets/logs/databases/generated outputs
- **Allowed commands:** None unless user explicitly asks; then `python scripts\verify_repo_safety.py`.
- **Stop condition:** Stop if the task starts changing strategy conclusions, command behavior, config defaults, or execution policy.

### Task: VPS safety checklist wording cleanup
- **Purpose:** Clarify that VPS work is planning/audit only; no scheduling or execution approval.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - `docs/VPS_SETUP_CHECKLIST.md`
  - `docs/HERMES_WORKFLOW.md`
- **Forbidden files:**
  - Task Scheduler config
  - scripts that schedule jobs
  - config/secrets/generated artefacts
- **Allowed commands:** None by default.
- **Stop condition:** Stop if asked to create schedules, cron jobs, Task Scheduler entries, or automation.

### Task: Report-back template standardization
- **Purpose:** Make Hermes/Codex report-back formats consistent: files changed, verification, commands or execution paths changed, Python changed, and secrets/generated artefacts touched.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `docs/CODEX_WORKFLOW.md`
- **Forbidden files:**
  - Source code
  - generated outputs
  - secrets/config/logs/databases
- **Allowed commands:** None by default.
- **Stop condition:** Stop if implementation changes are requested as part of wording cleanup.

### Task: Codex auto-commit policy update
- **Purpose:** Document when Codex may commit and push small low-risk changes by itself, and when it must stop for review.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - `docs/CODEX_WORKFLOW.md`
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_ROADMAP.md`
- **Forbidden files:**
  - Python code
  - `config.json`
  - `.env`
  - generated CSV/log/database/chart outputs
  - auth/token/key files
- **Allowed commands:** `python scripts\verify_repo_safety.py` before any commit or push.
- **Stop condition:** Stop instead of committing or pushing if Python code changes, generated files appear, repo safety fails, execution/scheduling/config defaults are touched, or secrets/config are encountered.

### Task: Staged paper-monitoring roadmap
- **Purpose:** Plan movement toward more operational paper monitoring with more liquid U.S. stocks/ETFs and more frequent checks, while keeping execution separate and manually reviewed.
- **Risk level:** Low / docs-only planning.
- **Allowed files:**
  - `docs/CODEX_WORKFLOW.md`
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_ROADMAP.md`
- **Forbidden files:**
  - Python code
  - `config.json`
  - scheduling files
  - generated outputs
  - logs/databases/secrets
- **Allowed commands:** None by default. If committing or handing off, run `python scripts\verify_repo_safety.py`.
- **Stop condition:** Stop if the plan starts adding loops, cron jobs, order workflows, config default changes, or execution-capable automation.

## 2. Needs ChatGPT review

### Task: Higher-risk task prompt template
- **Purpose:** Draft a reusable prompt template for asking ChatGPT/Codex to review high-risk changes without exposing secrets or approving execution.
- **Risk level:** Medium / docs-only, but safety-sensitive.
- **Allowed files:**
  - `docs/HERMES_WORKFLOW.md`
  - `docs/CODEX_WORKFLOW.md`
  - `docs/CURRENT_STATE.md`
- **Forbidden files:**
  - `config.json`
  - account IDs
  - auth/token files
  - generated outputs
  - logs/databases
- **Allowed commands:** None.
- **Stop condition:** Stop if prompt would include secrets, actual account details, order IDs, webhook URLs, or generated trading history.

### Task: Paper execution readiness review plan
- **Purpose:** Create a non-executable review checklist for any future paper-execution work.
- **Risk level:** Medium-high planning / no code.
- **Allowed files:**
  - `docs/HERMES_WORKFLOW.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_REFACTOR_INVENTORY.md`
  - `docs/CODEX_WORKFLOW.md`
- **Forbidden files:**
  - `bot.py` unless user explicitly permits source inspection later
  - `config.json`
  - logs/databases/generated CSVs
- **Allowed commands:** None.
- **Stop condition:** Stop if the plan starts defining live order instructions, paper order quantities, execution scheduling, or implementation steps that bypass confirmation.

### Task: Strategy research governance review
- **Purpose:** Review whether current docs sufficiently prevent overfitting, random strategy additions, crypto expansion, short execution, and research-to-execution leakage.
- **Risk level:** Medium / research governance.
- **Allowed files:**
  - `docs/CURRENT_STATE.md`
  - `docs/V2_REFACTOR_INVENTORY.md`
  - `docs/HERMES_WORKFLOW.md`
- **Forbidden files:**
  - generated CSVs
  - research output files
  - config/secrets
  - Python strategy code unless explicitly requested later
- **Allowed commands:** None.
- **Stop condition:** Stop if asked to rank strategies from generated outputs or inspect saved research CSVs without explicit permission.

## 3. Needs Codex

### Task: Low-risk utility extraction proposal
- **Purpose:** Ask Codex to propose, not implement, a tiny refactor of low-risk `bot.py` utilities such as manual quantity parsing or decimal-to-float conversion.
- **Risk level:** Medium / source-planning only.
- **Allowed files:**
  - `docs/V2_REFACTOR_INVENTORY.md`
  - `docs/CODEX_WORKFLOW.md`
  - `docs/HERMES_WORKFLOW.md`
  - If later approved: specific low-risk source files only
- **Forbidden files:**
  - `config.json`
  - high-risk execution sections
  - logs/databases/generated CSVs
  - auth/secrets
- **Allowed commands:** None at proposal stage. Later, if implementation is approved:
  - `python -m py_compile bot.py`
  - `python scripts\verify_position_rules.py`
  - `python scripts\verify_v2_baseline.py --timeout-seconds 180`
- **Stop condition:** Stop if Codex needs to modify Alpaca order submission, normal bot execution, paper-order smoke tests, slow SMA paper execution, or SQLite execution logging.

### Task: Focused verifier design for preview refactor
- **Purpose:** Have Codex propose tests/verifiers needed before moving slow SMA signal/action preview orchestration.
- **Risk level:** Medium.
- **Allowed files:**
  - `docs/V2_REFACTOR_INVENTORY.md`
  - `docs/CODEX_WORKFLOW.md`
  - `docs/HERMES_WORKFLOW.md`
  - Later, explicitly scoped preview source files
- **Forbidden files:**
  - execution code paths
  - config/secrets
  - generated CSV outputs unless the user explicitly permits fixture inspection
- **Allowed commands:** None for proposal. Later verifier commands only after user approval.
- **Stop condition:** Stop if proposal would call Alpaca, submit/cancel orders, write `trade_log`, send Discord alerts, or require real credentials.

### Task: Research command orchestration refactor plan
- **Purpose:** Ask Codex to plan moving research command orchestration only after baseline and CSV output checks are strong enough.
- **Risk level:** Medium / command routing adjacent.
- **Allowed files:**
  - `docs/V2_REFACTOR_INVENTORY.md`
  - `docs/CODEX_WORKFLOW.md`
  - `docs/CURRENT_STATE.md`
  - Later, explicitly scoped research runner/source files
- **Forbidden files:**
  - Alpaca execution helper
  - manual paper-order smoke test
  - slow SMA paper execution
  - normal paper-trading ticker processing
  - config/secrets/generated outputs
- **Allowed commands:** Proposal stage: none. Implementation stage only after review:
  - `python -m py_compile bot.py`
  - `python scripts\verify_v2_baseline.py --timeout-seconds 180`
  - `python scripts\verify_repo_safety.py`
- **Stop condition:** Stop if command routing changes could route research/preview/display commands into execution behavior.

## 4. Needs verifier first

### Task: Any Python source change
- **Purpose:** Ensure source changes do not break safety, routing, or behavior.
- **Risk level:** Medium to high depending on file.
- **Allowed files:**
  - Only explicitly scoped Python files.
  - Prefer low-risk files first.
- **Forbidden files:**
  - `config.json`
  - `.env`
  - logs/databases/generated outputs
  - auth/token files
  - high-risk execution paths unless explicitly approved
- **Allowed commands:**
  - `python -m py_compile bot.py`
  - `python scripts\verify_position_rules.py`
  - `python scripts\verify_v2_baseline.py --timeout-seconds 180`
  - `python scripts\verify_repo_safety.py`
- **Stop condition:** Stop if verifiers fail, new warnings appear, or the change touches Alpaca/order/SQLite trade-log/Discord alert paths unexpectedly.

### Task: Command-routing refactor
- **Purpose:** Move or simplify CLI command routing without behavior changes.
- **Risk level:** Medium-high.
- **Allowed files:**
  - Explicitly scoped routing files only, after review.
  - Relevant docs.
- **Forbidden files:**
  - execution helpers
  - order submission
  - paper-order smoke test
  - slow SMA paper execution
  - config/secrets/generated outputs
- **Allowed commands:**
  - `python -m py_compile bot.py`
  - focused command-routing smoke tests if created and reviewed
  - `python scripts\verify_v2_baseline.py --timeout-seconds 180`
  - `python scripts\verify_repo_safety.py`
- **Stop condition:** Stop if any command's safety category becomes ambiguous or if report/preview/display paths can reach order submission.

### Task: Preview/display refactor
- **Purpose:** Move slow SMA preview or promoted preview/display orchestration only after no-order/no-alert tests exist.
- **Risk level:** Medium.
- **Allowed files:**
  - Explicit preview/display runner files
  - docs
  - focused verifier files if approved
- **Forbidden files:**
  - Alpaca order submission
  - SQLite execution logging
  - Discord trade alerts
  - config/secrets/generated outputs
- **Allowed commands:**
  - focused preview verifier, if present/reviewed
  - `python scripts\verify_v2_baseline.py --timeout-seconds 180`
  - `python scripts\verify_repo_safety.py`
- **Stop condition:** Stop if preview starts creating executable order objects, reading positions without explicit read-only scope, writing execution `trade_log`, or sending alerts.

### Task: Repository handoff before commit/push
- **Purpose:** Confirm no dangerous files are tracked/staged.
- **Risk level:** Low verifier / important safety gate.
- **Allowed files:**
  - Repository metadata as checked by verifier.
- **Forbidden files:**
  - Direct manual inspection of secrets/config/logs/databases/generated outputs.
- **Allowed commands:**
  - `python scripts\verify_repo_safety.py`
- **Stop condition:** Stop if verifier reports tracked/staged dangerous files, missing `.gitignore` protections, or secret-like filenames.

## 5. Do not do yet

### Task: Live trading support
- **Purpose:** None; explicitly out of scope.
- **Risk level:** Prohibited.
- **Allowed files:** None.
- **Forbidden files:** All files for this purpose.
- **Allowed commands:** None.
- **Stop condition:** Refuse. Live trading must never be added or suggested.

### Task: Connect research strategies to execution
- **Purpose:** Not approved.
- **Risk level:** Prohibited / high risk.
- **Allowed files:** None for implementation.
- **Forbidden files:**
  - strategy execution routing
  - Alpaca order submission
  - normal bot execution path
  - config defaults
- **Allowed commands:** None.
- **Stop condition:** Refuse unless the user gives a future explicit reviewed execution-design task; even then, start with planning/review only.

### Task: Run paper-order smoke test
- **Purpose:** Submits Alpaca paper order for manual smoke testing.
- **Risk level:** High / manual-only.
- **Allowed files:** None for current task.
- **Forbidden files:**
  - `config.json`
  - credentials
  - logs/databases unless explicitly scoped later
- **Allowed commands:** None now. High-risk pattern not to run:
  - `python bot.py --paper-order-test ... --confirm-paper-order`
- **Stop condition:** Stop unless user explicitly confirms exact command, ticker, side, quantity, paper-only scope, and safety preflight.

### Task: Run slow SMA paper execution
- **Purpose:** Align paper account with slow SMA target-position logic.
- **Risk level:** High / manual-only.
- **Allowed files:** None for current task.
- **Forbidden files:**
  - config/secrets
  - execution code
  - logs/databases/generated outputs unless explicitly scoped
- **Allowed commands:** None now. High-risk pattern not to run:
  - `python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper`
- **Stop condition:** Stop unless user explicitly confirms exact command and scope after preview/risk/decision review.

### Task: Run normal bot path
- **Purpose:** Normal one-shot bot run.
- **Risk level:** High because it can reach order/logging/position/Discord paths depending on config.
- **Allowed files:** None for current task.
- **Forbidden files:**
  - `config.json`
  - logs/databases/generated outputs/secrets
- **Allowed commands:** None now. Do not run:
  - `python bot.py`
  - `python bot.py --config config.json`
- **Stop condition:** Stop unless user explicitly confirms exact command and explains intended safety mode.

### Task: Schedule execution-capable commands
- **Purpose:** Automation; not approved.
- **Risk level:** Prohibited until separate scheduling review, and execution-capable commands remain never-schedule.
- **Allowed files:** None for execution scheduling.
- **Forbidden files:**
  - Task Scheduler changes
  - cron/Hermes scheduled jobs
  - scripts that automate execution paths
  - config/secrets
- **Allowed commands:** None.
- **Stop condition:** Refuse to schedule paper-order tests, slow SMA paper execution, normal bot execution, or any future order-capable command.

### Task: Plan Hermes cron for market monitor reports
- **Purpose:** Document a future Hermes cron path for monitoring-only, chat-delivered market monitor refresh reports on the VPS.
- **Risk level:** Medium docs/report planning only; scheduling is not approved.
- **Allowed files:**
  - `README.md`
  - `docs/CURRENT_STATE.md`
  - `docs/VPS_SETUP_CHECKLIST.md`
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
- **Forbidden files/areas:**
  - Python code
  - Task Scheduler changes
  - Hermes cron job creation
  - config/secrets/logs/databases/generated outputs
  - Alpaca/order/position/SQLite `trade_log`/Discord alert logic
- **Preferred scheduler:** Hermes cron preferred for future monitoring scheduling if configured. Windows Task Scheduler remains an alternative, not the default assumption, and may be used only to start or keep the Hermes gateway running on boot, not for execution-capable trading commands.
- **Scheduling state:** No refresh cron job or execution scheduling is currently approved or created beyond the existing status-only job. Use Hermes cron for safe monitoring/reporting only; not for execution.
- **Initial candidate set:** Initial cron candidate should probably be a status/checkpoint job before refresh jobs. Candidate commands are `--vps-monitoring-status`, `--market-monitor-scheduling-readiness-report`, `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research`.
- **Prompt/tooling boundary:** Do not paste config/API keys/webhooks/account IDs into Hermes prompts. Future jobs should run from `C:\dev\paper-trading-bot`, use `.venv\Scripts\python.exe`, include a repo-safety check, use concise output capture, avoid recursive cron creation, and use restricted `enabled_toolsets` where Hermes supports them.
- **Manual review required:** Scheduling cadence is a separate future decision. A future review must approve exact cadence, exact command list, enabled toolsets, output destination, and failure behaviour before any Hermes cron job is created.
- **Lock boundary:** Refresh jobs should remain protected by lockfile/no-overlap. A stale lock requires manual review. Lockfile protection does not make execution-capable commands schedulable.
- **Current status-job checkpoint:** `docs/HERMES_CRON_JOB_DESIGN.md` records the verified `paper-bot-vps-status-check` job, including job ID, daily 10:10am UK local time cadence, cron expression `10 10 * * *`, Telegram delivery, script-only / no-agent mode, repo path, command sequence, and healthy output. It excludes refresh commands until a later review. Verify it with `python scripts\verify_hermes_cron_job_design.py`.
- **Prerequisites before scheduling review:**
  - `python scripts\verify_repo_safety.py`
  - `python scripts\verify_hermes_cron_job_design.py`
  - `python scripts\verify_hermes_cron_readiness.py`
  - `python bot.py --market-monitor-scheduling-readiness-report`
  - Confirmation generated CSV/cache files remain ignored
- **Never schedule:**
  - `python bot.py`
  - `python bot.py --paper-order-test ...`
  - `python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper`
- **Stop condition:** Stop if the plan creates schedules, approves scheduling, approves execution, or any candidate command tries to load `config.json`, call Alpaca, read positions, write SQLite `trade_log`, send Discord alerts, or create orders.

### Task: Plan MCP safe operations adapter
- **Purpose:** Document whether MCP could later wrap safe VPS/Hermes operations for whitelisted report/display/monitor commands only.
- **Risk level:** Medium docs-only planning. MCP implementation is not approved.
- **Allowed files:**
  - `docs/CURRENT_STATE.md`
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `docs/VPS_SETUP_CHECKLIST.md`
  - `docs/CODEX_WORKFLOW.md`
  - `README.md`
- **Forbidden files/areas:**
  - Python code
  - MCP server implementation
  - MCP package installation
  - services
  - schedules or Hermes cron jobs
  - config/secrets/logs/databases/generated outputs
  - Alpaca/order/position/SQLite `trade_log`/Discord alert logic
- **Candidate future MCP tools:**
  - `repo_safety_check`
  - `refresh_market_monitor`
  - `market_monitor_scheduling_readiness`
  - `vps_operations_readiness`
  - `deployment_readiness_report`
  - `fetch_news_risk_report`
  - `write_news_risk_veto_report`
  - `show_news_risk_veto`
  - `show_safe_command_list`
- **Forbidden MCP tools:**
  - `submit_order`
  - `cancel_order`
  - `run_normal_bot`
  - `run_paper_order_test`
  - `run_slow_sma_paper_execution`
  - `generate_buy_signal_from_news`
  - `generate_sell_signal_from_news`
  - `approve_trade_from_news`
  - `read_config`
  - `read_env`
  - `read_logs`
  - `read_database`
  - `expose_tokens`
  - `schedule_execution`
  - `approve_execution`
- **News risk-veto concept:** Future news support may fetch market and financial news only to write ticker-level risk-veto labels such as `block_new_entries_today`, `manual_review_required`, or `no_news_block`. It may block or flag new long entries for major negative or event-risk news, but must never generate buy/sell signals, order instructions, position sizing, or execution approval.
- **Security rules:** Use a tiny local/custom MCP server only if implemented later, no third-party MCP servers by default, hardcoded allowlist, deny by default, fixed working directory `C:\dev\paper-trading-bot`, no arbitrary shell tool, no secrets/generated data access, news output includes source/time/confidence/reason, stale news expires automatically, and return `execution_approved=False` and `scheduling_approved=False` where applicable.
- **Recommended order:** Stabilize VPS readiness/report chain, add no-overlap or lockfile protection for monitor refresh, add docs/report-only news-veto design, add saved-data-only news-veto report command, then consider a minimal proof of concept exposing only `repo_safety_check` and `refresh_market_monitor`.
- **Stop condition:** Stop if the plan starts implementing MCP, adding news API calls, installing packages, creating services, creating schedules, approving execution, generating buy/sell signals from news, or exposing any order, config, secret, log, database, token, or arbitrary shell access.

### Task: Plan no-overlap protection for market monitor refresh
- **Purpose:** Document a future no-overlap/lockfile plan before any repeated VPS/Hermes market-monitor refresh.
- **Risk level:** Medium docs-only planning. Lockfile implementation and scheduling are not approved.
- **Allowed files:**
  - `docs/CURRENT_STATE.md`
  - `docs/VPS_SETUP_CHECKLIST.md`
  - `docs/HERMES_WORKFLOW.md`
  - `docs/HERMES_TASK_BOARD.md`
  - `docs/CODEX_WORKFLOW.md`
- **Forbidden files/areas:**
  - Python code
  - Task Scheduler changes
  - cron/Hermes scheduled jobs
  - loop mode
  - config default changes
  - config/secrets/logs/databases/generated outputs
  - Alpaca/order/position/SQLite `trade_log`/Discord alert logic
- **Lockfile contract:** A future lock helper must be pure and no-network. A future lock file may prevent two safe refresh/report/display commands from running at once. Stale lock handling must be conservative, and uncertain stale locks should stop for manual review.
- **Allowed lock metadata:** command name, `started_at`, host, pid, `lock_version`, and optional `stale_after_seconds` if safe.
- **Forbidden lock metadata:** secrets, account IDs, config contents, order IDs, webhook URLs, API keys, logs, database contents, generated CSV contents, generated trading data, trading history, positions, and report contents.
- **Scope:** Applies only to future report, preview, display, and monitor refresh commands.
- **Never schedule:** Normal `python bot.py`, paper-order tests, slow-SMA paper execution, or any future execution-capable command. Execution-capable commands must not be treated as safe merely because a lockfile exists.
- **Recommended order:** Add report-only no-overlap/lockfile design or verifier, add isolated lock helper tests, apply only to safe refresh/report/display commands, then only after manual review consider scheduling safe monitor/report refresh commands.
- **Current scaffold commands:** `python bot.py --monitor-lockfile-readiness-report`, `python bot.py --refresh-promoted-review`, and `python bot.py --refresh-defensive-research` are the only commands protected by the monitor lockfile helper. The locks are transient report-only no-overlap guards and do not approve scheduling or execution.
- **Scheduling-readiness checkpoint:** `python bot.py --market-monitor-scheduling-readiness-report` assesses only the three VPS-safe lock-wrapped monitoring commands, config presence without reading contents, saved promoted/defensive output presence, generated-output ignore policy, and false scheduling/execution approval flags. It may report readiness for a future manual scheduling review, but it does not create or approve scheduling.
- **Hermes cron readiness checkpoint:** `python scripts\verify_hermes_cron_readiness.py` verifies Hermes cron is the preferred future monitoring scheduler if configured, Windows Task Scheduler is only an alternative, no scheduler is created or approved, initial candidates are limited to safe status/report/refresh commands, refresh jobs remain lock-wrapped, `enabled_toolsets` restrictions are documented, and execution-capable commands remain high-risk/manual-only.
- **Hermes cron job design checkpoint:** `python scripts\verify_hermes_cron_job_design.py` verifies the current status cron remains status-only, uses the VPS repo path and `.venv\Scripts\python.exe`, runs repo safety and Hermes cron readiness before the daily summary, avoids config/secrets/generated-content exposure, avoids recursive cron creation and Git writes, preserves false approval flags, and leaves the lock-wrapped set unchanged.
- **Current daily status cron:** `paper-bot-vps-status-check` is running as a status-only Hermes cron job. Job ID is `345188fbb60c`; cadence is daily at 10:10am UK local time; cron expression is `10 10 * * *`; timezone is `Europe/London`; delivery is Telegram; mode is script-only / no-agent; working directory is `C:\dev\paper-trading-bot`; command sequence is `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, `.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py`, and `.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary`. Verified output is repo_safety PASS, hermes_cron_readiness PASS, vps_daily_monitoring_summary PASS, final_monitoring_status `healthy_monitoring_state`, action_required `no_action_required`, execution_approved false, scheduling_approved false, and freshness_warnings: none. It does not run refresh commands, trade, approve scheduling beyond this one status job, approve execution, pull/commit/push code, or inspect/print config contents, secrets, logs, databases, or full generated CSV contents.
- **Daily summary command:** `python bot.py --vps-daily-monitoring-summary` is report/display-only for concise Telegram/manual checks. It summarizes promoted/defensive/freshness state plus saved QQQ100 paper-live monitoring status, adds `action_required`, `action_reason`, and `suggested_manual_action`, and keeps `execution_approved=False` and `scheduling_approved=False`.
- **Freshness checkpoint:** `python scripts\verify_vps_monitoring_freshness.py` verifies `--vps-monitoring-status` labels saved-output freshness from file modification times only and does not read full CSV contents for freshness.
- **Promoted refresh cron design:** `docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` and `python scripts\verify_hermes_promoted_review_refresh_cron_design.py` document a possible future second Hermes cron job for lock-wrapped `--refresh-promoted-review` followed by daily summary output. No refresh cron job is currently created or approved.
- **Canonical promoted refresh design:** `docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` is canonical. `docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` is a legacy pointer only.
- **Monitoring runbook:** `docs/HERMES_CRON_MONITORING_RUNBOOK.md` and `python scripts\verify_hermes_cron_monitoring_runbook.py` explain how to interpret Telegram/status output from `paper-bot-vps-status-check`, including healthy, warning, stale/missing, and failed-step responses without approving execution or creating a second cron.
- **Contract verifier:** `python scripts\verify_monitor_lockfile_contract.py` is pure/no-network and defines future helper requirements only.
- **Helper verifier:** `python scripts\verify_monitor_lockfile_helper.py` checks temp-directory acquire/release cleanup, fresh-lock blocking, malformed-lock blocking, and stale-lock manual review in `trading_bot/safety/monitor_lockfile.py`.
- **Integration checkpoint:** `python scripts\verify_monitor_lockfile_integration_readiness.py` verifies exactly `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research` are lock-wrapped, `bot.py` is not using the helper directly, no other command is lock-wrapped, and future safe report/display/monitor refresh commands remain manual-review only.
- **Promoted refresh checkpoint:** `python scripts\verify_refresh_promoted_review_lock_readiness.py` verifies `--refresh-promoted-review` is lock-wrapped only for no-overlap protection, remains preview/report/display only, unscheduled, and separate from execution approval.
- **QQQ100 promoted preview integration checkpoint:** `python scripts\verify_qqq100_promoted_preview_integration.py` verifies `qqq_100_trend_gate` / QQQ is added to the promoted preview-review path from saved `qqq100_preview_signal_pack` output only, keeps high-growth and QQQ150 excluded, avoids order-instruction columns, and preserves false execution, paper execution, scheduling, and order-created/submitted/cancelled flags.
- **Defensive refresh checkpoint:** `python scripts\verify_refresh_defensive_research_lock_readiness.py` verifies `--refresh-defensive-research` is lock-wrapped only for no-overlap protection, remains research/report/chart only, unscheduled, and separate from execution approval.
- **Final state checkpoint:** `python scripts\verify_monitor_lockfile_final_state.py` verifies the exact three-command lock boundary, blocked execution commands, false execution/scheduling approval flags, stale-lock manual review, and VPS handoff documentation.
- **VPS prerequisite checkpoint:** `python scripts\verify_vps_monitoring_prerequisites.py` distinguishes environment/dependency readiness, missing local config for read-only promoted preview, missing saved defensive research inputs, actual safety failures, and safe next manual VPS steps.
- **VPS terminal status:** `python bot.py --vps-monitoring-status` is report/display-only terminal monitoring. It summarizes lockfile state, config presence without reading contents, saved defensive input presence, generated-output ignore expectations, latest saved promoted review counts when present, high-risk/manual-only boundaries in prose, and next safe manual report actions without Alpaca, yfinance, Discord, SQLite `trade_log`, scheduling, or execution approval.
- **Import safety checkpoint:** `python scripts\verify_report_only_import_safety.py` verifies `--vps-monitoring-status` can route before top-level Alpaca imports while normal execution imports remain present.
- **Strategy improvement lab checkpoint:** `python scripts\verify_strategy_improvement_lab.py` verifies `--strategy-improvement-lab` and `--show-strategy-improvement-lab` remain research/display only, use fixed ETF variants, keep generated CSV outputs ignored, and preserve false execution approval flags. The lab may explore cash-drag reduction, but promising labels do not approve execution or scheduling.
- **Short/leverage research lab checkpoint:** `python scripts\verify_short_leverage_research_lab.py` verifies `--short-leverage-research-lab` and `--show-short-leverage-research-lab` remain synthetic research/display only, use fixed short/leverage hypotheses, keep generated CSV outputs ignored, preserve false execution, short execution, leverage execution, margin, scheduling, Alpaca, and order flags, and do not add short/leverage execution commands.
- **QQQ leverage validation checkpoint:** `python scripts\verify_qqq_leverage_validation_report.py` verifies `--qqq-leverage-validation-report` and `--show-qqq-leverage-validation-report` remain synthetic QQQ leverage research/display only, test fixed 1.0x/1.25x/1.5x/1.75x/2.0x SMA200 trend-gated exposure variants, keep generated CSV outputs ignored, preserve false execution, leverage, margin, short, scheduling, Alpaca, and order flags, and do not add leverage or margin execution commands.
- **QQQ adaptive leverage checkpoint:** `python scripts\verify_qqq_adaptive_leverage_lab.py` verifies `--qqq-adaptive-leverage-lab` and `--show-qqq-adaptive-leverage-lab` remain fixed synthetic QQQ adaptive research/display only, test the two fixed Codex adaptive candidates without parameter search, keep generated CSV outputs ignored, preserve false execution, leverage, margin, short, scheduling, Alpaca, and order flags, and do not add leverage or margin execution commands.
- **QQQ lead decision checkpoint:** `python scripts\verify_qqq_lead_decision_report.py` verifies `--qqq-lead-decision-report` and `--show-qqq-lead-decision-report` remain saved-output report/display only, compare QQQ conservative/adaptive candidates against the current stock/ETF active research lead, keep generated CSV outputs ignored, preserve false execution, leverage, margin, short, scheduling, Alpaca, and order flags, and do not refresh market data.
- **QQQ trend-gate manual review checkpoint:** `python scripts\verify_qqq_trend_gate_manual_review_pack.py` verifies `--qqq-trend-gate-manual-review-pack` and `--show-qqq-trend-gate-manual-review-pack` remain saved-output research/report-only, confirm `qqq_100_trend_gate` as the stock/ETF research lead, keep `codex_qqq_adaptive_trend_exposure` as an ambitious alternative, keep `qqq_150_trend_gate` rejected as a high-drawdown reference, write ignored manual-review CSVs, and preserve false preview, execution, leverage, margin, short, scheduling, Alpaca, and order flags.
- **QQQ preview-candidate readiness checkpoint:** `python scripts\verify_qqq_preview_candidate_readiness_report.py` verifies `--qqq-preview-candidate-readiness-report` and `--show-qqq-preview-candidate-readiness-report` remain saved-output research/report-only, ask whether `qqq_100_trend_gate` is ready for manual preview-candidate discussion, keep paper execution blocked, write ignored readiness CSVs, and preserve false paper execution, execution, leverage, margin, scheduling, Alpaca, and order flags.
- **QQQ100 preview-candidate readiness pack checkpoint:** `python scripts\verify_qqq100_preview_candidate_readiness_pack.py` verifies `--qqq100-preview-candidate-readiness-pack` and `--show-qqq100-preview-candidate-readiness-pack` remain saved-output report/display only, keep `qqq_100_trend_gate` as the clean main lead, keep `codex_qqq_adaptive_trend_exposure` as an ambitious alternative only, keep `qqq_150_trend_gate` rejected, keep the high-growth branch out of preview discussion, write ignored QQQ100 readiness CSVs, and preserve false preview implementation, paper execution, execution, scheduling, Alpaca, and order flags.
- **QQQ100 preview signal pack checkpoint:** `python scripts\verify_qqq100_preview_signal_pack.py` verifies `--qqq100-preview-signal-pack` and `--show-qqq100-preview-signal-pack` remain non-execution preview-signal/report-display only, preview only `qqq_100_trend_gate`, keep high-growth excluded, keep adaptive QQQ alternative-only, keep QQQ150 rejected, write ignored preview-signal CSVs, omit order-instruction columns, and preserve false action preview, paper execution, execution, scheduling, Alpaca, and order flags.
- **QQQ100 action preview checkpoint:** `python scripts\verify_qqq100_action_preview.py` verifies `--qqq100-action-preview` and `--show-qqq100-action-preview` remain saved-signal action-preview/display only, default to no Alpaca and no position read, require both explicit flags for read-only paper-position context, write ignored action-preview CSVs, omit order-instruction and sensitive columns, and preserve false order, SQLite `trade_log`, Discord, paper execution, execution, and scheduling flags.
- **QQQ100 paper-readiness blocker report checkpoint:** `python scripts\verify_qqq100_paper_readiness_blocker_report.py` verifies `--qqq100-paper-readiness-blocker-report` and `--show-qqq100-paper-readiness-blocker-report` remain saved-output blocker report/display only, read QQQ100 preview/action-preview and readiness evidence where present, write ignored blocker CSVs, omit order-instruction and sensitive columns, keep high-growth excluded, and preserve false order, SQLite `trade_log`, Discord/Telegram, paper execution, execution, and scheduling flags.
- **QQQ100 paper execution readiness checkpoint:** `python scripts\verify_qqq100_paper_execution_readiness_report.py` verifies `--qqq100-paper-execution-readiness-report` and `--show-qqq100-paper-execution-readiness-report` remain saved-output-only readiness/report-display commands, recognise saved AAPL smoke-test postcheck plus QQQ100 preview/action/promoted evidence, surface portfolio overlap warnings, keep high-growth and crypto excluded, and preserve false Alpaca, order, SQLite `trade_log`, Discord/Telegram, paper execution, execution, QQQ100 execution, and scheduling flags.
- **QQQ100 manual paper execution checkpoint:** `python scripts\verify_execute_qqq100_paper.py` verifies `--execute-qqq100-paper --confirm-qqq100-paper` stays limited to the saved `qqq_100_trend_gate` / QQQ signal, one paper share, manual confirmation, paper mode, no shorting/leverage, QQQ open-order and recent-order blocking, ignored generated execution CSVs, no high-growth/crypto/QQQ150/adaptive wiring, and no scheduling or general execution approval.
- **QQQ100 paper postcheck checkpoint:** `python scripts\verify_qqq100_paper_postcheck.py` verifies `--qqq100-paper-postcheck --confirm-readonly-alpaca-check` and `--show-qqq100-paper-postcheck` remain read-only verification/report-display commands, detect saved/broker recent QQQ buy 1 status and QQQ alignment only after read-only confirmation, write ignored postcheck CSVs, and preserve false follow-up, repeat, order, SQLite `trade_log`, Discord/Telegram, execution, QQQ100 execution, and scheduling flags.
- **Paper execution state summary checkpoint:** `python scripts\verify_paper_execution_state_summary.py` verifies `--paper-execution-state-summary` and `--show-paper-execution-state-summary` remain saved-output-only milestone/report-display commands, recognise saved AAPL smoke-test fill, saved QQQ100 manual paper execution fill, and saved QQQ100 aligned-long action-preview evidence, write ignored state summary/positions/milestones/blockers CSVs, keep high-growth and crypto excluded from execution, and preserve false follow-up, repeat, general execution, QQQ100 execution, order, SQLite `trade_log`, Discord/Telegram, Alpaca, and scheduling flags.
- **Multi-strategy portfolio preview checkpoint:** `python scripts\verify_multi_strategy_portfolio_preview.py` verifies `--multi-strategy-portfolio-preview` and `--show-multi-strategy-portfolio-preview` remain saved-output-only portfolio preview/display commands, tolerate missing optional saved inputs, keep QQQ100 as the core growth trend candidate when saved input exists, keep high-growth and crypto research-only/blocked, write ignored portfolio preview/exposure/conflict/blocker CSVs, omit order-instruction and sensitive columns, and preserve false order, SQLite `trade_log`, Discord/Telegram, paper execution, execution, and scheduling flags.
- **High-growth stock lab checkpoint:** `python scripts\verify_high_growth_stock_lab.py` verifies `--high-growth-stock-lab` and `--show-high-growth-stock-lab` remain research-only, use a fixed individual-stock universe rather than ETFs, keep SPY/QQQ as benchmark/regime references only, write ignored report/trade/cost/split/drawdown/concentration CSVs, preserve survivorship-bias and concentration warnings, and preserve false paper execution, execution, leverage, margin, short, scheduling, Alpaca, and order flags.
- **High-growth stock universe expansion checkpoint:** `python scripts\verify_high_growth_stock_universe_expansion_report.py` verifies `--high-growth-stock-universe-expansion-report` and `--show-high-growth-stock-universe-expansion-report` remain research-only, compare the fixed `mega_cap_growth_10`, `expanded_growth_30`, and `broad_liquid_growth_50` individual-stock universes, keep SPY/QQQ as benchmark/regime references only, write ignored universe-expansion CSVs, preserve survivorship-bias and concentration warnings, and preserve false paper execution, execution, leverage, margin, short, scheduling, Alpaca, and order flags.
- **High-growth stock drawdown-control checkpoint:** `python scripts\verify_high_growth_stock_drawdown_control_report.py` verifies `--high-growth-stock-drawdown-control-report` and `--show-high-growth-stock-drawdown-control-report` remain research-only, use the fixed `broad_liquid_growth_50` individual-stock universe, test only fixed drawdown-control variants, keep SPY/QQQ as benchmark/regime references only, write ignored drawdown-control CSVs, preserve survivorship-bias, concentration, outlier, drawdown, and false execution/scheduling flags, and do not add execution commands.
- **High-growth stock lead decision checkpoint:** `python scripts\verify_high_growth_stock_lead_decision_report.py` verifies `--high-growth-stock-lead-decision-report` and `--show-high-growth-stock-lead-decision-report` remain saved-output report/display only, read saved high-growth and QQQ decision CSVs where present, keep `qqq_100_trend_gate` as clean main stock/ETF lead, label `codex_broad_growth_balanced_breakout_control` as high-risk stock research lead candidate only, write ignored decision/evidence/blocker CSVs, and preserve false preview, paper execution, execution, leverage, margin, short, scheduling, Alpaca, and order flags.
- **High-growth stock manual review pack checkpoint:** `python scripts\verify_high_growth_stock_manual_review_pack.py` verifies `--high-growth-stock-manual-review-pack` and `--show-high-growth-stock-manual-review-pack` remain saved-output report/display only, keep `qqq_100_trend_gate` as clean main lead, keep `codex_broad_growth_balanced_breakout_control` as high-risk research-only candidate, keep broad Top1 rejected, write ignored manual-review CSVs, and preserve blocked preview, false paper execution, false execution, and false scheduling flags.
- **High-growth stock risk review pack checkpoint:** `python scripts\verify_high_growth_stock_risk_review_pack.py` verifies `--high-growth-stock-risk-review-pack` and `--show-high-growth-stock-risk-review-pack` remain saved-output report/display only, focus on cost, split, concentration, outlier, survivorship, and drawdown blockers, keep `qqq_100_trend_gate` as clean main lead, keep `codex_broad_growth_balanced_breakout_control` high-risk research-only, keep broad Top1 rejected, write ignored risk-review CSVs, and preserve blocked preview, false paper execution, false execution, and false scheduling flags.
- **High-growth stock risk evidence review checkpoint:** `python scripts\verify_high_growth_stock_risk_evidence_review.py` verifies `--high-growth-stock-risk-evidence-review` and `--show-high-growth-stock-risk-evidence-review` remain saved-output report/display only, compare saved evidence for return, drawdown, cost, split, concentration, outlier, and survivorship blockers, keep `qqq_100_trend_gate` as clean main lead, keep `codex_broad_growth_balanced_breakout_control` high-risk research-only, keep broad Top1 rejected, write ignored risk-evidence CSVs, and preserve blocked preview, false paper execution, false execution, and false scheduling flags.
- **High-growth stock branch decision checkpoint:** `python scripts\verify_high_growth_stock_branch_decision_checkpoint.py` verifies `--high-growth-stock-branch-decision-checkpoint` and `--show-high-growth-stock-branch-decision-checkpoint` remain saved-output report/display only, convert saved evidence into a conservative branch decision, keep `qqq_100_trend_gate` as clean main lead, keep broad Top1 rejected, keep the high-growth branch research-only unless paused, write ignored branch-decision CSVs, and preserve blocked preview, false paper execution, false execution, and false scheduling flags.
- **High-growth stock final validation pack checkpoint:** `python scripts\verify_high_growth_stock_final_validation_pack.py` verifies `--high-growth-stock-final-validation-pack` and `--show-high-growth-stock-final-validation-pack` remain saved-output report/display only, check final return/drawdown/cost/split/concentration/outlier/survivorship evidence before manual preview-candidate discussion, keep `qqq_100_trend_gate` as clean main lead, keep broad Top1 rejected, write ignored final-validation CSVs, and preserve blocked preview, false paper execution, false execution, and false scheduling flags.
- **Strategy improvement robustness checkpoint:** `python scripts\verify_strategy_improvement_robustness.py` verifies `--strategy-improvement-robustness` and `--show-strategy-improvement-robustness` remain research/display only, use fixed split and cost assumptions, keep generated CSV outputs ignored, and preserve false execution approval flags.
- **Strategy improvement diagnostics checkpoint:** `python scripts\verify_strategy_improvement_diagnostics.py` verifies `--strategy-improvement-diagnostics` and `--show-strategy-improvement-diagnostics` remain saved-CSV diagnostics only, keep `growth_biased_rotation_breadth_stricter_gate` as the active research lead, compare tested refinements against the previous growth-biased baseline, recommend stricter-gate validation/checkpointing rather than more random variants, and preserve false execution approval flags.
- **Growth-biased stricter validation checkpoint:** `python scripts\verify_growth_biased_stricter_validation.py` verifies `--growth-biased-stricter-validation` and `--show-growth-biased-stricter-validation` remain saved-output validation/display only, write ignored split/cost/drawdown/benchmark/promotion validation CSVs, keep `growth_biased_rotation_breadth_stricter_gate` as research lead, and preserve false execution approval flags.
- **Growth-biased stricter promotion-readiness checkpoint:** `python scripts\verify_growth_biased_stricter_promotion_readiness.py` verifies `--growth-biased-stricter-promotion-readiness` and `--show-growth-biased-stricter-promotion-readiness` remain saved-output blocker/display only, write ignored promotion-readiness CSVs, keep `growth_biased_rotation_breadth_stricter_gate` as research lead, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter manual-review-pack checkpoint:** `python scripts\verify_growth_biased_stricter_manual_review_pack.py` verifies `--growth-biased-stricter-manual-review-pack` and `--show-growth-biased-stricter-manual-review-pack` remain saved-output report/display only, write ignored manual-review and regime-context CSVs, keep `growth_biased_rotation_breadth_stricter_gate` as research lead, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter threshold-neighbourhood checkpoint:** `python scripts\verify_growth_biased_stricter_threshold_neighbourhood.py` verifies `--growth-biased-stricter-threshold-neighbourhood` and `--show-growth-biased-stricter-threshold-neighbourhood` remain fixed research/report-display only, write ignored threshold-neighbourhood CSVs, test only the fixed 40/45/50/55/60 breadth-gate neighbourhood, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter cost/turnover stress checkpoint:** `python scripts\verify_growth_biased_stricter_cost_turnover_stress.py` verifies `--growth-biased-stricter-cost-turnover-stress` and `--show-growth-biased-stricter-cost-turnover-stress` remain saved-output report/display only, write ignored cost/turnover stress CSVs, test only fixed 0/5/10/25/50/100 bps one-way costs for the 55% cluster, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter persistence-filter checkpoint:** `python scripts\verify_growth_biased_stricter_persistence_filter.py` verifies `--growth-biased-stricter-persistence-filter` and `--show-growth-biased-stricter-persistence-filter` remain fixed research/report-display only, test the fixed persistence variants plus one Codex-designed `codex_ambitious_concentrated_growth_persistence` candidate, write ignored persistence CSVs, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Codex ambitious validation checkpoint:** `python scripts\verify_codex_ambitious_validation.py` verifies `--codex-ambitious-validation` and `--show-codex-ambitious-validation` remain saved-output report/display only, validate `codex_ambitious_concentrated_growth_persistence` for possible active research-lead discussion, write ignored validation/split/cost/drawdown CSVs, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Codex ambitious split/drawdown checkpoint:** `python scripts\verify_codex_ambitious_split_drawdown_validation.py` verifies `--codex-ambitious-split-drawdown-validation` and `--show-codex-ambitious-split-drawdown-validation` remain research/report-display only, validate fixed `split_60_40`, `split_70_30`, `split_80_20`, drawdown windows, and a lead-change checkpoint for `codex_ambitious_concentrated_growth_persistence`, write ignored CSVs, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Codex ambitious lead-decision checkpoint:** `python scripts\verify_codex_ambitious_lead_decision.py` verifies `--codex-ambitious-lead-decision` and `--show-codex-ambitious-lead-decision` remain saved-output report/display only, decide whether `codex_ambitious_concentrated_growth_persistence` becomes the active research lead as a research label only, write ignored decision CSVs, keep cost review explicit when needed, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Crypto universe readiness checkpoint:** `python scripts\verify_crypto_universe_readiness.py` verifies `--crypto-universe-readiness-report` and `--show-crypto-universe-readiness-report` remain research/report-display only, classify the expanded yfinance-compatible crypto universe before new strategy design, write ignored readiness CSVs, flag POL/MATIC transition risk, and preserve false execution approval flags.
- **Expanded crypto strategy lab checkpoint:** `python scripts\verify_expanded_crypto_strategy_lab.py` verifies `--expanded-crypto-strategy-lab` and `--show-expanded-crypto-strategy-lab` remain research/report-display only, test `crypto_risk_on_momentum_persistence` plus `codex_ambitious_crypto_btc_eth_core_alt_accelerator`, exclude POL/MATIC until transition review, write ignored result/cost/split/trade/equity CSVs, and preserve false execution approval flags.
- **Expanded crypto robustness checkpoint:** `python scripts\verify_expanded_crypto_robustness_report.py` verifies `--expanded-crypto-robustness-report` and `--show-expanded-crypto-robustness-report` remain research/report-display only, challenge static equal-weight crypto for hindsight bias, inception-aware construction, outlier dependence, cost/split/drawdown robustness, keep POL/MATIC transition-blocked, write ignored robustness CSVs, and preserve false execution approval flags.
- **Crypto equal-weight crash-gate checkpoint:** `python scripts\verify_crypto_equal_weight_crash_gate.py` verifies `--crypto-equal-weight-crash-gate` and `--show-crypto-equal-weight-crash-gate` remain research/report-display only, test fixed trend/crash-gate variants around equal-weight eligible crypto, keep POL/MATIC transition-blocked, write ignored result/summary/trade/equity/cost/split/drawdown CSVs, and preserve false execution approval flags.
- **Crypto equal-weight volatility-scaling checkpoint:** `python scripts\verify_crypto_equal_weight_volatility_scaling.py` verifies `--crypto-equal-weight-volatility-scaling` and `--show-crypto-equal-weight-volatility-scaling` remain research/report-display only, test partial volatility/drawdown exposure scaling plus one Codex-designed fixed-rule crypto risk-control idea, keep POL/MATIC transition-blocked, write ignored result/summary/trade/equity/cost/split/drawdown CSVs, and preserve false execution approval flags.
- **Crypto equal-weight capped-risk checkpoint:** `python scripts\verify_crypto_equal_weight_capped_risk_report.py` verifies `--crypto-equal-weight-capped-risk-report` and `--show-crypto-equal-weight-capped-risk-report` remain research/report-display only, test capped/equal-risk crypto allocation plus outlier-dependence diagnostics, keep POL/MATIC transition-blocked, write ignored result/summary/trade/equity/cost/split/drawdown/contribution CSVs, and preserve false execution approval flags.
- **Expanded crypto lead-decision checkpoint:** `python scripts\verify_expanded_crypto_lead_decision.py` verifies `--expanded-crypto-lead-decision` and `--show-expanded-crypto-lead-decision` remain saved-output report/display only, consolidate the current crypto research lead as a research label only, keep high-drawdown/manual-review-only wording, write ignored decision/summary/evidence CSVs, and preserve false execution approval flags.
- **Crypto lead split-sensitivity diagnosis checkpoint:** `python scripts\verify_crypto_lead_split_sensitivity_diagnosis.py` verifies `--crypto-lead-split-sensitivity-diagnosis` and `--show-crypto-lead-split-sensitivity-diagnosis` remain saved-output research/report-only, diagnose the current crypto research lead across fixed splits, broad-market versus lead-specific weakness, exclusion stability, and BNB-USD/TRX-USD/top-contributor dependence, write ignored diagnosis CSVs, and preserve false execution approval flags.
- **Expanded crypto manual review pack checkpoint:** `python scripts\verify_expanded_crypto_manual_review_pack.py` verifies `--expanded-crypto-manual-review-pack` and `--show-expanded-crypto-manual-review-pack` remain saved-output research/report-only, consolidate the manual review pack for the current crypto research lead, preserve benchmark/risk-control/split/outlier/blocker wording, write ignored manual-review CSVs, and preserve false execution, paper execution, promotion, and scheduling approval flags.
- **Project research state refresh checkpoint:** `python scripts\verify_project_research_state_refresh.py` verifies `--project-research-state-refresh` and `--show-project-research-state-refresh` remain saved-output research/report-only, consolidate `qqq_100_trend_gate` as the stock/ETF research lead, preserve `codex_qqq_adaptive_trend_exposure` as an ambitious alternative, keep `qqq_150_trend_gate` rejected as a high-drawdown reference, preserve the manual-review-only crypto lead, write ignored project-state CSVs, and preserve false preview-promotion, execution, paper execution, crypto execution, and scheduling approval flags.
- **Current research state display checkpoint:** `python scripts\verify_show_current_research_state.py` verifies `--show-current-research-state` remains a compact saved-output-only terminal display helper for the multi-sleeve research state, reads saved QQQ100 recovered-reference, high-growth stream, crypto stream, multi-sleeve portfolio, crypto-review, canonical lead-state, and high-growth drawdown CSVs where available, labels missing saved outputs as `missing_saved_output`, avoids market-data refresh, avoids preview promotion/execution approval, and does not connect strategies to Alpaca or paper orders.
- **Project research state quality checkpoint:** `python scripts\verify_project_research_state_quality_report.py` verifies `--project-research-state-quality-report` reads saved project-state files only, writes ignored quality CSV output, checks freshness/required fields/false approval flags conservatively, and remains report-only with no execution or scheduling approval.
- **Stock/ETF paper execution discussion checkpoint:** `python scripts\verify_stock_etf_paper_execution_readiness_report.py` verifies `--stock-etf-paper-execution-readiness-report` remains saved-data/static-source only, writes ignored readiness CSV output, keeps `codex_ambitious_concentrated_growth_persistence` as research-only with cost review and execution-gate blockers explicit, excludes crypto execution, and preserves false execution/scheduling approval flags.
- **Alpaca paper readiness checkpoint:** `python scripts\verify_alpaca_paper_readiness_report.py` verifies `--alpaca-paper-readiness-report` writes ignored readiness CSV output, default mode does not call Alpaca, the optional read-only account/status check requires `--confirm-readonly-alpaca-check`, no order/alert/scheduler call patterns are added, and false execution/scheduling approval flags are preserved.
- **Alpaca connectivity diagnostics checkpoint:** `python scripts\verify_alpaca_connectivity_diagnostics.py` verifies `--alpaca-connectivity-diagnostics` and `--show-alpaca-connectivity-diagnostics` remain unauthenticated DNS/TCP 443 diagnostics only, write ignored diagnostics CSVs, avoid config/credentials/authenticated Alpaca APIs/order/position/SQLite/alert/scheduler paths, and preserve false execution/scheduling approval flags. This is for VPS network triage only, including the case where Alpaca API hosts time out while general HTTPS control sites work.
- **Paper-order smoke-test readiness checkpoint:** `python scripts\verify_paper_order_smoke_test_readiness_pack.py` verifies `--paper-order-smoke-test-readiness-pack` writes ignored readiness-pack CSV output, remains saved-data/static/report-only, does not call Alpaca or order paths, does not print a pasteable paper-order command, and preserves false order execution, execution, scheduling, run-now, and Alpaca-called flags.
- **Paper-order smoke-test live preflight checkpoint:** `python scripts\verify_paper_order_smoke_test_live_preflight.py` verifies `--paper-order-smoke-test-live-preflight` writes ignored live-preflight CSV output, default mode does not call Alpaca, confirmed read-only mode requires `--confirm-readonly-alpaca-check`, no order/alert/scheduler call patterns are added, no pasteable paper-order command is printed, and false order execution, execution, scheduling, and run-now flags are preserved.
- **Paper-order smoke-test postcheck checkpoint:** `python scripts\verify_paper_order_smoke_test_postcheck.py` verifies `--paper-order-smoke-test-postcheck` writes ignored postcheck CSV output, default mode does not call Alpaca, confirmed read-only mode requires `--confirm-readonly-alpaca-check`, no order/alert/scheduler call patterns are added, no pasteable paper-order command or sensitive identifiers are printed, and false follow-up order, order execution, execution, and scheduling approval flags are preserved.
- **Future refresh cron readiness checkpoint:** `python scripts\verify_future_refresh_cron_readiness_pack.py` verifies `--future-refresh-cron-readiness-pack` remains static/docs/report-only, writes ignored readiness output, checks the current single status cron and design-only future refresh candidate sequence, excludes confirmed read-only Alpaca and execution-capable commands, and preserves false cron, scheduling, execution, and order-execution approvals.
- **Manual smoke-test runbook checkpoint:** `python scripts\verify_paper_order_smoke_test_runbook_check.py` verifies `docs/PAPER_ORDER_SMOKE_TEST_RUNBOOK.md` and `--paper-order-smoke-test-runbook-check` remain static/report-only, preserve Monday manual-review wording, avoid broker/order/scheduler paths, and keep smoke-test order, execution, scheduling, and follow-up order approval false.
- **Paper smoke-test kill-switch diagnosis checkpoint:** `python scripts\verify_paper_smoke_test_kill_switch_diagnosis.py` verifies `--paper-smoke-test-kill-switch-diagnosis` and `--show-paper-smoke-test-kill-switch-diagnosis` remain saved-output diagnosis/display only, classify kill-switch blockers without changing the paper-order gate, write ignored diagnosis CSVs, avoid Alpaca/order/position/SQLite/alert/scheduler paths, and preserve false smoke-test order, paper execution, execution, and scheduling approvals.
- **Manual paper smoke-test gate checkpoint:** `python scripts\verify_manual_paper_smoke_test_gate.py` verifies the existing `--paper-order-test` path has a narrow `AAPL buy 1 --confirm-paper-order` connectivity-only gate, keeps wrong ticker/side/quantity/confirmation/paper-mode/open-order/duplicate cases blocked, keeps normal bot and slow-SMA paths unchanged, writes ignored gate CSVs only when the manual path runs, and preserves false strategy execution, scheduling, follow-up order, and live-trading approvals.
- **Research dashboard project-state panel:** `python scripts\verify_research_dashboard.py` verifies `--build-research-dashboard` remains static saved-CSV display only, includes the minimal Project Research State panel when saved inputs exist, does not create a server or background service, and preserves false execution/scheduling wording.
- **VPS handoff:** Manual update flow is `git pull`, `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, then `.venv\Scripts\python.exe scripts\verify_monitor_lockfile_final_state.py`. Safe manual monitoring commands are `.venv\Scripts\python.exe bot.py --vps-monitoring-status`, `.venv\Scripts\python.exe bot.py --monitor-lockfile-readiness-report`, `.venv\Scripts\python.exe bot.py --refresh-promoted-review`, and `.venv\Scripts\python.exe bot.py --refresh-defensive-research`; these are not scheduling approval or execution approval.
- **Stop condition:** Stop if the plan creates a lockfile implementation, creates schedules, adds loop mode, changes Python source, changes config defaults, approves scheduling, approves execution, or touches private/generated files.

### Task: Move high-risk execution code out of `bot.py`
- **Purpose:** Refactor high-risk execution internals.
- **Risk level:** High; explicitly "should not move yet" in refactor inventory.
- **Allowed files:** None for implementation now.
- **Forbidden files/areas:**
  - Alpaca order submission
  - manual paper-order smoke test
  - slow SMA paper execution
  - normal paper-trading ticker processing
  - open-order blocking
  - SQLite execution logging
  - Discord trade alerts
- **Allowed commands:** None now.
- **Stop condition:** Stop until additional no-network test coverage and a clear paper-only integration checklist exist.

### Task: Expand crypto/short execution
- **Purpose:** Not approved.
- **Risk level:** Prohibited/high.
- **Allowed files:** Docs-only discussion if explicitly requested.
- **Forbidden files:**
  - execution code
  - config defaults
  - Alpaca order paths
- **Allowed commands:** None.
- **Stop condition:** Refuse any short execution, crypto execution, margin, leverage, or crypto shorting work. Current crypto remains research-only; short-selling research is paused.

### Task: Paper-live evidence reconciliation checkpoint
- **Purpose:** Use `python bot.py --paper-live-evidence-audit` to review saved QQQ100 evidence consistency before any separate manual follow-up design.
- **Risk level:** Low/report-only when limited to saved CSV evidence.
- **Allowed commands:** `python bot.py --paper-live-evidence-audit`, `python bot.py --show-paper-live-evidence-audit`.
- **Forbidden commands:** QQQ100 paper execution, paper-order tests, slow-SMA execution, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, create order instructions, approve follow-up orders, or change scheduling.

### Task: QQQ100 postcheck readiness runbook
- **Purpose:** Use `python bot.py --qqq100-postcheck-readiness-report` to document the missing VPS saved postcheck quantity evidence and the future manual read-only postcheck step.
- **Risk level:** Low/report-only when it only writes the runbook report.
- **Allowed commands:** `python bot.py --qqq100-postcheck-readiness-report`, `python bot.py --show-qqq100-postcheck-readiness-report`.
- **Forbidden commands:** `python bot.py --qqq100-paper-postcheck --confirm-readonly-alpaca-check` unless the user explicitly approves it in a later prompt; QQQ100 paper execution; paper-order tests; normal bot execution; scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, run postcheck, create order instructions, approve follow-up orders, or change scheduling.

### Task: QQQ100 follow-up/no-action policy
- **Purpose:** Use `python bot.py --qqq100-followup-policy-report` to document whether saved QQQ100 state requires no action or only a future manual discussion.
- **Risk level:** Low/report-only when it reads saved evidence only.
- **Allowed commands:** `python bot.py --qqq100-followup-policy-report`, `python bot.py --show-qqq100-followup-policy-report`.
- **Forbidden commands:** QQQ100 paper execution, QQQ100 postcheck unless separately approved, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, create executable order instructions, approve repeat/follow-up orders, or change scheduling.

### Task: QQQ100 daily decision report
- **Purpose:** Use `python bot.py --qqq100-daily-decision-report` to turn saved QQQ100 paper-live evidence into a daily hold/manual-discussion/blocked status.
- **Risk level:** Low/report-only when it reads saved evidence and saved follow-up policy only.
- **Allowed commands:** `python bot.py --qqq100-daily-decision-report`, `python bot.py --show-qqq100-daily-decision-report`.
- **Expected status:** `qqq100_daily_decision_hold_no_action_aligned_long` when QQQ100 is already aligned long one share.
- **Forbidden commands:** QQQ100 paper execution, QQQ100 postcheck unless separately approved, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, refresh market data, create executable order instructions, approve repeat/follow-up orders, or change scheduling.

### Task: QQQ100 manual flatten readiness report
- **Purpose:** Use `python bot.py --qqq100-manual-flatten-readiness-report` to document whether a future saved flat signal would need a separate manual flatten discussion.
- **Risk level:** Low/report-only when it reads saved evidence and saved follow-up policy only.
- **Allowed commands:** `python bot.py --qqq100-manual-flatten-readiness-report`, `python bot.py --show-qqq100-manual-flatten-readiness-report`.
- **Expected current status:** `flatten_not_needed_currently` when QQQ100 is already aligned long one share and desired state remains long.
- **Future-only status:** `future_manual_flatten_discussion_possible_not_approved` if saved desired state is flat while saved QQQ position is long exactly one share.
- **Forbidden commands:** QQQ100 paper execution, QQQ100 postcheck unless separately approved, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, refresh market data, create executable order instructions, approve a flatten action, approve repeat/follow-up orders, or change scheduling.

### Task: QQQ100 manual flatten runbook/design report
- **Purpose:** Use `python bot.py --qqq100-manual-flatten-runbook-report` to document future manual-review boundaries for a flat-signal plus long-one-share QQQ100 state.
- **Risk level:** Low/report-only when it reads the saved flatten readiness checkpoint only.
- **Allowed commands:** `python bot.py --qqq100-manual-flatten-runbook-report`, `python bot.py --show-qqq100-manual-flatten-runbook-report`.
- **Expected current status:** `manual_flatten_runbook_not_needed_currently` when QQQ100 is already aligned long one share and desired state remains long.
- **Future-only status:** `manual_flatten_runbook_manual_review_required_not_approved` if saved desired state is flat while saved QQQ position is long exactly one share.
- **Forbidden commands:** QQQ100 paper execution, QQQ100 postcheck unless separately approved, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, refresh market data, create executable order instructions, approve manual flatten, approve flatten execution, approve repeat/follow-up orders, or change scheduling.

### Task: Paper-live monitoring status
- **Purpose:** Use `python bot.py --paper-live-monitoring-status` to include QQQ100 no-action/aligned state in safe VPS/Hermes monitoring output.
- **Risk level:** Low/report-only when it reads saved evidence only.
- **Allowed commands:** `python bot.py --paper-live-monitoring-status`, `python bot.py --show-paper-live-monitoring-status`.
- **VPS integration:** `python bot.py --vps-monitoring-status` and `python bot.py --vps-daily-monitoring-summary` now include the saved paper-live monitoring status and saved QQQ100 daily decision when available. The existing `paper-bot-vps-status-check` cron command sequence is unchanged; do not add paper-live commands to cron.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, QQQ100 paper execution, QQQ100 postcheck unless separately approved, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would call Alpaca, read live positions, create executable order instructions, approve repeat/follow-up orders, or change scheduling.

### Task: Paper-live checklist status closeout
- **Purpose:** Use `python bot.py --paper-live-checklist-status` to close out the current QQQ100 paper-live monitoring phase with saved evidence only.
- **Risk level:** Low/report-only when it reads `data/paper_live_monitoring_status.csv` only.
- **Allowed commands:** `python bot.py --paper-live-checklist-status`, `python bot.py --show-paper-live-checklist-status`.
- **Expected status:** `paper_live_checklist_current_qqq100_monitoring_phase_closed_out` when QQQ100 is aligned long one share, no action is required, and Step 12 remains future-only.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, QQQ100 paper execution, QQQ100 postcheck unless separately approved, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would build the generic promotion ladder, approve another QQQ order, change the Hermes cron sequence, or touch execution/config/secrets.

### Task: Paper-live promotion ladder status
- **Purpose:** Use `python bot.py --paper-live-promotion-ladder-status` to summarize the current report-only promotion ladder state from saved outputs.
- **Risk level:** Low/report-only when it reads saved ladder design and QQQ100 monitoring outputs only.
- **Allowed commands:** `python bot.py --paper-live-promotion-ladder-status`, `python bot.py --show-paper-live-promotion-ladder-status`.
- **Expected status:** `paper_live_promotion_ladder_status_report_only` with QQQ100 as the only current seed, `monitor_only_aligned_long_one`, and F7 accounting proof accepted while portfolio backtests remain not promotion evidence.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, generic promotion implementation, QQQ100 paper execution, paper-order tests, normal bot execution, scheduler changes.
- **Stop condition:** Stop if the task would promote high-growth/crypto/defensive/SMA/slow-SMA, treat portfolio backtests as promotion evidence before accounting proof, create order instructions, or touch execution/config/secrets.

### Task: Paper-live F7 accounting proof
- **Purpose:** Use `python bot.py --paper-live-f7-accounting-proof` to statically check the F7 portfolio accounting boundary.
- **Risk level:** Low/report-only when limited to source inspection and saved CSV outputs.
- **Allowed commands:** `python bot.py --paper-live-f7-accounting-proof`, `python bot.py --show-paper-live-f7-accounting-proof`, and `python scripts\verify_paper_live_f7_accounting_proof.py`.
- **Expected status:** `f7_accounting_static_proof_ready_for_manual_review`; weighted daily returns are confirmed and no independent starting cash is detected. This F7 accounting checkpoint is accepted, but portfolio backtests remain not promotion evidence without separate promotion review.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, scheduler changes, generic ladder implementation.
- **Stop condition:** Stop if the task would use portfolio backtests as promotion evidence without manual review, create order instructions, or approve execution/scheduling.

### Task: Paper-live next ladder candidate scope
- **Purpose:** Use `python bot.py --paper-live-next-ladder-candidate-scope` to choose the next manual ladder review scope without promoting anything.
- **Risk level:** Low/report-only when limited to saved CSV outputs and static scope labels.
- **Allowed commands:** `python bot.py --paper-live-next-ladder-candidate-scope`, `python bot.py --show-paper-live-next-ladder-candidate-scope`, and `python scripts\verify_paper_live_next_ladder_candidate_scope.py`.
- **Expected status:** `next_ladder_candidate_scope_report_only`; defensive sleeve is the next conservative review scope, allocator is deferred, and high-growth remains research-only.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, scheduler changes, promotion implementation.
- **Stop condition:** Stop if the task would promote defensive/high-growth/crypto/allocator, create order instructions, or approve execution/scheduling.

### Task: Paper-live defensive sleeve ladder-scope review
- **Purpose:** Use `python bot.py --paper-live-defensive-sleeve-ladder-scope-review` to check saved defensive evidence before any candidate discussion.
- **Risk level:** Low/report-only when limited to saved-output file presence.
- **Allowed commands:** `python bot.py --paper-live-defensive-sleeve-ladder-scope-review`, `python bot.py --show-paper-live-defensive-sleeve-ladder-scope-review`, and `python scripts\verify_paper_live_defensive_sleeve_ladder_scope_review.py`.
- **Expected status:** `defensive_sleeve_ladder_scope_review_ready_for_manual_review` if saved evidence is present, or `defensive_sleeve_ladder_scope_missing_saved_evidence_manual_review_required` if evidence is missing.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, scheduler changes, defensive promotion implementation.
- **Stop condition:** Stop if the task would promote the defensive sleeve, create order instructions, rerun research, or approve execution/scheduling.

### Task: Paper-live F6/F7 audit
- **Purpose:** Use `python bot.py --paper-live-f6-f7-audit` to audit remaining external-review items before any generic promotion ladder or multi-sleeve paper-live work.
- **Risk level:** Low/report-only when limited to static/source review and saved output files.
- **Allowed commands:** `python bot.py --paper-live-f6-f7-audit`, `python bot.py --show-paper-live-f6-f7-audit`.
- **Expected status:** `paper_live_f6_f7_audit_manual_review_required`; F6 unknown-position handling is partially confirmed and F7 accounting consistency still needs targeted tests/verifiers.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, QQQ100 paper execution, paper-order tests, normal bot execution, market-data backtests, yfinance refresh, Alpaca reads, scheduler changes.
- **Stop condition:** Stop if the task would treat unknown positions as flat, use portfolio backtests as promotion evidence, approve execution, or build the generic promotion ladder.

### Task: Paper-live F6/F7 targeted checks
- **Purpose:** Use `python scripts\verify_paper_live_f6_f7_targeted_checks.py` to verify pure helper boundaries before generic promotion-ladder work.
- **Risk level:** Low/test-only when limited to no-network helper checks.
- **Allowed commands:** `python scripts\verify_paper_live_f6_f7_targeted_checks.py`.
- **Expected status:** F6 unknown positions stay loud and manual-review only; F7 portfolio backtests remain not promotion evidence until accounting consistency is proven.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, scheduler changes.
- **Stop condition:** Stop if the task would wrap commands, approve execution/scheduling, or promote multi-sleeve, high-growth, defensive, crypto, SMA, or slow-SMA paths.

### Task: Paper-live promotion ladder design
- **Purpose:** Use `python bot.py --paper-live-promotion-ladder-design` to create report-only design scaffolding for a future generic ladder.
- **Risk level:** Low/report-only when limited to saved output files and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-promotion-ladder-design`, `python bot.py --show-paper-live-promotion-ladder-design`.
- **Expected status:** `paper_live_promotion_ladder_design_report_only`; QQQ100 is the only current seed and remains monitor-only/aligned long one share with no repeat/follow-up order approved.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, scheduler changes, real promotion implementation.
- **Stop condition:** Stop if the task would implement generic promotion logic, treat portfolio backtests as promotion evidence, assume unknown positions are flat, approve execution/scheduling, or promote multi-sleeve, high-growth, defensive, crypto, SMA, or slow-SMA paths.

### Task: Paper-live multi-sleeve roadmap
- **Purpose:** Use `python bot.py --paper-live-multi-sleeve-roadmap` to document the future QQQ-led multi-sleeve direction without changing current QQQ100-only monitoring.
- **Risk level:** Low/report-only when limited to saved output files and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-multi-sleeve-roadmap`, `python bot.py --show-paper-live-multi-sleeve-roadmap`.
- **Expected status:** `paper_live_multi_sleeve_roadmap_report_only`; QQQ100 core remains monitor-only, defensive is future review only, high-growth and crypto remain research-only, and allocator execution wiring is absent.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, scheduler changes, portfolio execution implementation.
- **Stop condition:** Stop if the task would create portfolio execution wiring, order instructions, scheduling, crypto execution, or promote high-growth/defensive/crypto/SMA/slow-SMA paths.

### Task: Paper-live next-phase backlog
- **Purpose:** Use `python bot.py --paper-live-next-phase-backlog` to list exactly what must happen before any future sleeve can move through the promotion ladder.
- **Risk level:** Low/report-only when limited to saved output files and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-next-phase-backlog`, `python bot.py --show-paper-live-next-phase-backlog`.
- **Expected status:** `paper_live_next_phase_backlog_report_only`; only saved-output reviews and verifiers are allowed next.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, scheduler changes, portfolio execution implementation.
- **Stop condition:** Stop if the task would create execution wiring, order instructions, scheduling, promote a sleeve, or treat portfolio metrics as promotion evidence before accounting is proven.

### Task: Paper-live multi-sleeve evidence-gap audit
- **Purpose:** Use `python bot.py --paper-live-multi-sleeve-evidence-gap` to map present/missing saved evidence before any future sleeve can move through the promotion ladder.
- **Risk level:** Low/report-only when limited to saved-output file presence checks and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-multi-sleeve-evidence-gap`, `python bot.py --show-paper-live-multi-sleeve-evidence-gap`.
- **Expected status:** `paper_live_multi_sleeve_evidence_gap_manual_review_required`; missing saved outputs are blockers/manual-review items.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, research reruns, market-data refresh, Alpaca reads, action previews, order instructions, portfolio execution implementation.
- **Stop condition:** Stop if the task would read broker state, refresh data, promote a sleeve, create action previews/order instructions, or treat missing evidence as approval.

### Task: Paper-live high-growth evidence-gap audit
- **Purpose:** Use `python bot.py --paper-live-high-growth-evidence-gap` to map present/missing saved high-growth evidence before any future high-growth sleeve promotion-ladder discussion.
- **Risk level:** Low/report-only when limited to saved-output file presence checks and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-high-growth-evidence-gap`, `python bot.py --show-paper-live-high-growth-evidence-gap`.
- **Expected status:** `paper_live_high_growth_evidence_gap_manual_review_required`; missing lead, concentration/top-contributor, drawdown, attribution, survivorship/outlier, F6/F7, or portfolio-risk evidence remains a blocker.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, research reruns, market-data refresh, Alpaca reads, action previews, order instructions, portfolio execution implementation, or high-growth promotion.
- **Stop condition:** Stop if the task would read broker state, refresh data, promote high-growth, create action previews/order instructions, or treat saved metrics as execution evidence.

### Task: Paper-live high-growth evidence quality review
- **Purpose:** Use `python bot.py --paper-live-high-growth-evidence-quality` to review present high-growth evidence quality before any future high-growth promotion-ladder discussion.
- **Risk level:** Low/report-only when limited to saved-output CSV summaries and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-high-growth-evidence-quality`, `python bot.py --show-paper-live-high-growth-evidence-quality`.
- **Expected status:** `high_growth_evidence_quality_manual_review_required`; saved evidence can be present while concentration/outlier, drawdown, attribution, survivorship/current-constituent, and promotion-readiness blockers remain manual-review items.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, research reruns, market-data refresh, Alpaca reads, action previews, order instructions, portfolio execution implementation, or high-growth promotion.
- **Stop condition:** Stop if the task would approve preview/paper-live/execution/scheduling, hide TSLA/outlier/concentration/bias warnings, or treat saved metrics as order instructions.

### Task: Paper-live high-growth manual-review decision
- **Purpose:** Use `python bot.py --paper-live-high-growth-manual-review-decision` to record the current high-growth manual-review decision from saved gap/quality outputs only.
- **Risk level:** Low/report-only when limited to saved evidence-gap and evidence-quality outputs and no broker reads.
- **Allowed commands:** `python bot.py --paper-live-high-growth-manual-review-decision`, `python bot.py --show-paper-live-high-growth-manual-review-decision`.
- **Expected status:** `high_growth_remains_research_only_manual_review_required`; QQQ100 remains the cleaner current paper-live monitor base, and high-growth preview/paper-live/promotion flags remain false.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, research reruns, market-data refresh, Alpaca reads, action previews, order instructions, portfolio execution implementation, or high-growth promotion.
- **Stop condition:** Stop if the task would promote high-growth, approve preview/paper-live/execution/scheduling, create order instructions, or treat the decision checkpoint as permanent rejection rather than future manual-review context.

### Task: High-growth strategy discovery sprint
- **Purpose:** Use `python bot.py --high-growth-strategy-discovery-sprint` to consolidate saved high-growth, crypto, QQQ100, and multi-sleeve research into a subagent-style candidate sprint.
- **Risk level:** Low/report-only when limited to saved CSV outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --high-growth-strategy-discovery-sprint`, `python bot.py --show-high-growth-strategy-discovery-sprint`, and `python scripts\verify_high_growth_strategy_discovery_sprint.py`.
- **Expected status:** `high_growth_strategy_discovery_two_or_more_strong_candidates_found` when at least two distinct saved-evidence candidate families pass the research screen; current top candidates are `higher_growth_70_20_5_5` and `qqq100_plus_high_growth_plus_crypto_research`.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, action previews, order instructions, portfolio execution implementation, high-growth promotion, or scheduling.
- **Stop condition:** Stop if the task would refresh yfinance data, promote high-growth, approve preview/paper-live/execution/scheduling, create order instructions, or treat the sprint as paper-live approval.

### Task: Higher-growth preview readiness pack
- **Purpose:** Use `python bot.py --higher-growth-preview-readiness-pack` to compare `higher_growth_70_20_5_5` against QQQ100 and `balanced_multi_sleeve_research_portfolio` before any preview-design discussion.
- **Risk level:** Low/report-only when limited to saved CSV outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --higher-growth-preview-readiness-pack`, `python bot.py --show-higher-growth-preview-readiness-pack`, and `python scripts\verify_higher_growth_preview_readiness_pack.py`.
- **Expected status:** `higher_growth_preview_discussion_ready_manual_review_required`; this means manual discussion is reasonable, not that preview mode or execution is approved.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, action previews, order instructions, portfolio execution implementation, high-growth promotion, or scheduling.
- **Stop condition:** Stop if the task would implement preview mode, create action previews/order instructions, approve execution/scheduling, or treat the pack as paper-live approval.

### Task: Higher-growth candidate selection decision
- **Purpose:** Use `python bot.py --higher-growth-candidate-selection-decision` to choose the next saved-output preview-design review candidate from the higher-growth shortlist.
- **Risk level:** Low/report-only when limited to saved CSV outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --higher-growth-candidate-selection-decision`, `python bot.py --show-higher-growth-candidate-selection-decision`, and `python scripts\verify_higher_growth_candidate_selection_decision.py`.
- **Expected status:** `higher_growth_candidate_selected_for_preview_design_review`; selected candidate is `higher_growth_70_20_5_5`, runner-up is `balanced_multi_sleeve_research_portfolio`, and crypto blend remains deferred.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would implement preview mode, create action previews/order instructions, approve execution/scheduling, promote high-growth/crypto, or treat the decision as paper-live approval.

### Task: Higher-growth preview design
- **Purpose:** Use `python bot.py --higher-growth-preview-design` to document the future preview-only shape for `higher_growth_70_20_5_5`.
- **Risk level:** Low/report-only when limited to saved CSV outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --higher-growth-preview-design`, `python bot.py --show-higher-growth-preview-design`, and `python scripts\verify_higher_growth_preview_design.py`.
- **Expected status:** `higher_growth_preview_design_ready_for_future_preview_implementation`; target weights are 70% QQQ100 core, 20% high-growth stock research sleeve, 5% crypto research sleeve, and 5% defensive cash/bond sleeve.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would create an actual preview signal, include order side/quantity/type/account fields, approve execution/scheduling, or treat the design as paper-live approval.

### Task: Volatility-targeted growth research sprint
- **Purpose:** Use `python bot.py --vol-targeted-growth-research-sprint` to test saved-stream volatility-targeted growth candidates as an alternative to simply adding more growth exposure.
- **Risk level:** Low/report-only when limited to saved return streams and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-research-sprint`, `python bot.py --show-vol-targeted-growth-research-sprint`, and `python scripts\verify_vol_targeted_growth_research_sprint.py`.
- **Expected status:** `vol_targeted_growth_research_two_or_more_strong_candidates_found`; current top research candidates are `high_growth_balanced_target_vol_25_win_20_cap_1x` and `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, preview signals, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would call yfinance, create preview signals, include order side/quantity/type/account fields, approve execution/scheduling, or treat research candidates as paper-live approval.

### Task: Volatility-targeted growth manual review pack
- **Purpose:** Use `python bot.py --vol-targeted-growth-manual-review-pack` to compare the two leading volatility-targeted growth candidates side by side before any preview-design discussion.
- **Risk level:** Low/report-only when limited to saved volatility-targeted sprint outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-manual-review-pack`, `python bot.py --show-vol-targeted-growth-manual-review-pack`, and `python scripts\verify_vol_targeted_growth_manual_review_pack.py`.
- **Expected status:** `vol_targeted_growth_manual_review_required`; current interpretation favours `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x` as the cleaner next research path, while `high_growth_balanced_target_vol_25_win_20_cap_1x` remains higher-return/higher-risk.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, preview signals, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would implement preview mode, create action previews/order instructions, approve execution/scheduling, or treat the manual-review result as paper-live approval.

### Task: Volatility-targeted growth robustness checkpoint
- **Purpose:** Use `python bot.py --vol-targeted-growth-robustness-checkpoint` to review the preferred multi-sleeve volatility-targeted candidate before any preview-design discussion.
- **Risk level:** Low/report-only when limited to saved volatility-targeted sprint/manual-review outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-robustness-checkpoint`, `python bot.py --show-vol-targeted-growth-robustness-checkpoint`, and `python scripts\verify_vol_targeted_growth_robustness_checkpoint.py`.
- **Expected status:** `vol_targeted_growth_robustness_manual_review_required`; preview readiness remains `vol_targeted_growth_preview_design_not_ready_robustness_review_required`.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, preview signals, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would implement preview mode, create action previews/order instructions, approve execution/scheduling, or treat robustness review as paper-live approval.

### Task: Volatility-targeted growth nearby-variants review
- **Purpose:** Use `python bot.py --vol-targeted-growth-nearby-variants-review` to compare the preferred 15% target / 20-day variant against adjacent multi-sleeve volatility-targeted variants.
- **Risk level:** Low/report-only when limited to saved volatility-targeted sprint/robustness outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-nearby-variants-review`, `python bot.py --show-vol-targeted-growth-nearby-variants-review`, and `python scripts\verify_vol_targeted_growth_nearby_variants_review.py`.
- **Expected status:** `vol_targeted_growth_nearby_variants_manual_review_required`; preview status remains `preview_design_still_blocked_pending_variant_review`.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, preview signals, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would implement preview mode, create action previews/order instructions, approve execution/scheduling, or treat a nearby variant as paper-live approval.

### Task: Volatility-targeted growth preview-readiness decision
- **Purpose:** Use `python bot.py --vol-targeted-growth-preview-readiness-decision` to select the disciplined volatility-targeted growth variant for a future preview-design review.
- **Risk level:** Low/report-only when limited to saved nearby-variant/robustness outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-preview-readiness-decision`, `python bot.py --show-vol-targeted-growth-preview-readiness-decision`, and `python scripts\verify_vol_targeted_growth_preview_readiness_decision.py`.
- **Expected status:** `vol_targeted_growth_15_20_selected_for_preview_design_review`; preview-design discussion may be ready for manual review, but preview implementation remains `preview_implementation_not_added`.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, preview signals, action previews, order instructions, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would implement preview mode, create action previews/order instructions, approve execution/scheduling, or treat preview-readiness as paper-live approval.

### Task: Volatility-targeted growth preview design
- **Purpose:** Use `python bot.py --vol-targeted-growth-preview-design` to document the future preview-only shape for `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`.
- **Risk level:** Low/report-only when limited to saved preview-readiness outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-preview-design`, `python bot.py --show-vol-targeted-growth-preview-design`, and `python scripts\verify_vol_targeted_growth_preview_design.py`.
- **Expected status:** `vol_targeted_growth_preview_design_ready_for_future_preview_implementation`; target variant is higher-growth multi-sleeve, 15% vol target, 20-day vol window, 1x cap, and no leverage.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, preview signals, action previews, order side/quantity/type/account fields, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would create an actual preview signal, include executable order fields, approve execution/scheduling, or treat the design as paper-live approval.

### Task: Volatility-targeted growth preview signal
- **Purpose:** Use `python bot.py --vol-targeted-growth-preview-signal` to create a saved-output preview signal for `higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x`.
- **Risk level:** Low/report-only when limited to saved preview-design/readiness outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-preview-signal`, `python bot.py --show-vol-targeted-growth-preview-signal`, and `python scripts\verify_vol_targeted_growth_preview_signal.py`.
- **Expected status:** `vol_targeted_growth_preview_signal_created_saved_output_only`; target variant is 15% vol target, 20-day vol window, 1x cap, no leverage, and saved target sleeve weights only.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, action previews, order side/quantity/type/account fields, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would create an action preview, include executable order fields, approve execution/scheduling, or treat the preview signal as paper-live approval.

### Task: Volatility-targeted growth action-preview design
- **Purpose:** Use `python bot.py --vol-targeted-growth-action-preview-design` to document the shape of a possible future action-preview checkpoint after the saved 15/20 preview signal.
- **Risk level:** Low/report-only when limited to saved preview-signal outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-action-preview-design`, `python bot.py --show-vol-targeted-growth-action-preview-design`, and `python scripts\verify_vol_targeted_growth_action_preview_design.py`.
- **Expected status:** `vol_targeted_growth_action_preview_design_ready_manual_review_required`; it should remain design-only and require manual review before any saved action-preview implementation.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, actual action previews, order side/quantity/type/account fields, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would create action rows, read broker positions, include executable order fields, approve execution/scheduling, or treat the design as paper-live approval.

### Task: Volatility-targeted growth action preview
- **Purpose:** Use `python bot.py --vol-targeted-growth-action-preview` to create saved sleeve-level manual-review rows from the 15/20 preview signal.
- **Risk level:** Low/report-only when limited to saved preview-signal/design outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-action-preview`, `python bot.py --show-vol-targeted-growth-action-preview`, and `python scripts\verify_vol_targeted_growth_action_preview.py`.
- **Expected status:** `vol_targeted_growth_action_preview_created_saved_output_only`; current exposure should remain `current_exposure_not_read` and broker comparison should remain false.
- **Forbidden commands:** Creating/editing/triggering Hermes cron jobs, order-capable commands, normal bot execution, market-data refresh, Alpaca reads, live position reads, broker-position comparison, order side/quantity/type/account fields, portfolio execution implementation, high-growth/crypto promotion, or scheduling.
- **Stop condition:** Stop if the task would read broker positions, include executable order fields, approve execution/scheduling, or treat the saved action preview as paper-live approval.

### Task: Volatility-targeted growth broker-position comparison design
- **Purpose:** Use `python bot.py --vol-targeted-growth-broker-position-comparison-design` to document gates for a possible future explicit read-only broker-position comparison.
- **Risk level:** Low/report-only when no broker read is performed.
- **Allowed commands:** `python bot.py --vol-targeted-growth-broker-position-comparison-design`, `python bot.py --show-vol-targeted-growth-broker-position-comparison-design`, and `python scripts\verify_vol_targeted_growth_broker_position_comparison_design.py`.
- **Expected status:** `vol_targeted_growth_broker_position_comparison_design_ready_manual_review_required`; broker positions remain unread.
- **Forbidden commands:** Alpaca calls, position reads, order-capable commands, executable order fields, scheduling, or paper-live approval.
- **Stop condition:** Stop if the task would perform the broker read instead of only designing it.

### Task: Volatility-targeted growth portfolio-risk review
- **Purpose:** Use `python bot.py --vol-targeted-growth-portfolio-risk-review` to decide whether the 15/20 candidate stays research-only or can enter paper-live discussion.
- **Risk level:** Low/report-only when limited to saved outputs and no broker or market-data reads.
- **Allowed commands:** `python bot.py --vol-targeted-growth-portfolio-risk-review`, `python bot.py --show-vol-targeted-growth-portfolio-risk-review`, and `python scripts\verify_vol_targeted_growth_portfolio_risk_review.py`.
- **Expected status:** `vol_targeted_growth_portfolio_risk_manual_review_required`; paper-live discussion remains not approved until broker comparison and portfolio risk policy are reviewed.
- **Forbidden commands:** Broker reads, market refresh, order instructions, portfolio execution wiring, high-growth/crypto promotion, scheduling, or paper-live approval.
- **Stop condition:** Stop if the task would approve paper-live candidacy or execution.
