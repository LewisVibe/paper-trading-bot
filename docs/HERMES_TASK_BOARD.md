# Hermes Task Board

This task board is guidance only. It does not approve execution, scheduling, or strategy-to-paper integration. Any execution-capable, order-capable, scheduling, or strategy-integration work still requires a separate explicit review and manual confirmation.

Cross-references:
- `docs/HERMES_WORKFLOW.md`
- `docs/CURRENT_STATE.md`
- `docs/CODEX_WORKFLOW.md`
- `docs/V2_REFACTOR_INVENTORY.md`
- `docs/VPS_SETUP_CHECKLIST.md`

## 1. Safe now

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
- **Current status-job checkpoint:** `docs/HERMES_CRON_JOB_DESIGN.md` records the verified `paper-bot-vps-status-check` job, including job ID, once-daily cadence, Telegram delivery, script-only / no-agent mode, repo path, command sequence, and healthy output. It excludes refresh commands until a later review. Verify it with `python scripts\verify_hermes_cron_job_design.py`.
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
- **Current daily status cron:** `paper-bot-vps-status-check` is running as a status-only Hermes cron job. Job ID is `345188fbb60c`; cadence is once daily / every 1440m; delivery is Telegram; mode is script-only / no-agent; working directory is `C:\dev\paper-trading-bot`; command sequence is `.venv\Scripts\python.exe scripts\verify_repo_safety.py`, `.venv\Scripts\python.exe scripts\verify_hermes_cron_readiness.py`, and `.venv\Scripts\python.exe bot.py --vps-daily-monitoring-summary`. Verified output is repo_safety PASS, hermes_cron_readiness PASS, vps_daily_monitoring_summary PASS, final_monitoring_status `healthy_monitoring_state`, execution_approved false, scheduling_approved false, and freshness_warnings: none. It does not run refresh commands, trade, approve scheduling beyond this one status job, approve execution, pull/commit/push code, or inspect/print config contents, secrets, logs, databases, or full generated CSV contents.
- **Daily summary command:** `python bot.py --vps-daily-monitoring-summary` is report/display-only for concise Telegram/manual checks. It summarizes promoted/defensive/freshness state and keeps `execution_approved=False` and `scheduling_approved=False`.
- **Freshness checkpoint:** `python scripts\verify_vps_monitoring_freshness.py` verifies `--vps-monitoring-status` labels saved-output freshness from file modification times only and does not read full CSV contents for freshness.
- **Promoted refresh cron design:** `docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` and `python scripts\verify_hermes_promoted_review_refresh_cron_design.py` document a possible future second Hermes cron job for lock-wrapped `--refresh-promoted-review` followed by daily summary output. No refresh cron job is currently created or approved.
- **Canonical promoted refresh design:** `docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md` is canonical. `docs/HERMES_PROMOTED_REVIEW_CRON_DESIGN.md` is a legacy pointer only.
- **Monitoring runbook:** `docs/HERMES_CRON_MONITORING_RUNBOOK.md` and `python scripts\verify_hermes_cron_monitoring_runbook.py` explain how to interpret Telegram/status output from `paper-bot-vps-status-check`, including healthy, warning, stale/missing, and failed-step responses without approving execution or creating a second cron.
- **Contract verifier:** `python scripts\verify_monitor_lockfile_contract.py` is pure/no-network and defines future helper requirements only.
- **Helper verifier:** `python scripts\verify_monitor_lockfile_helper.py` checks temp-directory acquire/release cleanup, fresh-lock blocking, malformed-lock blocking, and stale-lock manual review in `trading_bot/safety/monitor_lockfile.py`.
- **Integration checkpoint:** `python scripts\verify_monitor_lockfile_integration_readiness.py` verifies exactly `--monitor-lockfile-readiness-report`, `--refresh-promoted-review`, and `--refresh-defensive-research` are lock-wrapped, `bot.py` is not using the helper directly, no other command is lock-wrapped, and future safe report/display/monitor refresh commands remain manual-review only.
- **Promoted refresh checkpoint:** `python scripts\verify_refresh_promoted_review_lock_readiness.py` verifies `--refresh-promoted-review` is lock-wrapped only for no-overlap protection, remains preview/report/display only, unscheduled, and separate from execution approval.
- **Defensive refresh checkpoint:** `python scripts\verify_refresh_defensive_research_lock_readiness.py` verifies `--refresh-defensive-research` is lock-wrapped only for no-overlap protection, remains research/report/chart only, unscheduled, and separate from execution approval.
- **Final state checkpoint:** `python scripts\verify_monitor_lockfile_final_state.py` verifies the exact three-command lock boundary, blocked execution commands, false execution/scheduling approval flags, stale-lock manual review, and VPS handoff documentation.
- **VPS prerequisite checkpoint:** `python scripts\verify_vps_monitoring_prerequisites.py` distinguishes environment/dependency readiness, missing local config for read-only promoted preview, missing saved defensive research inputs, actual safety failures, and safe next manual VPS steps.
- **VPS terminal status:** `python bot.py --vps-monitoring-status` is report/display-only terminal monitoring. It summarizes lockfile state, config presence without reading contents, saved defensive input presence, generated-output ignore expectations, latest saved promoted review counts when present, high-risk/manual-only boundaries in prose, and next safe manual report actions without Alpaca, yfinance, Discord, SQLite `trade_log`, scheduling, or execution approval.
- **Import safety checkpoint:** `python scripts\verify_report_only_import_safety.py` verifies `--vps-monitoring-status` can route before top-level Alpaca imports while normal execution imports remain present.
- **Strategy improvement lab checkpoint:** `python scripts\verify_strategy_improvement_lab.py` verifies `--strategy-improvement-lab` and `--show-strategy-improvement-lab` remain research/display only, use fixed ETF variants, keep generated CSV outputs ignored, and preserve false execution approval flags. The lab may explore cash-drag reduction, but promising labels do not approve execution or scheduling.
- **Strategy improvement robustness checkpoint:** `python scripts\verify_strategy_improvement_robustness.py` verifies `--strategy-improvement-robustness` and `--show-strategy-improvement-robustness` remain research/display only, use fixed split and cost assumptions, keep generated CSV outputs ignored, and preserve false execution approval flags.
- **Strategy improvement diagnostics checkpoint:** `python scripts\verify_strategy_improvement_diagnostics.py` verifies `--strategy-improvement-diagnostics` and `--show-strategy-improvement-diagnostics` remain saved-CSV diagnostics only, keep `growth_biased_rotation_breadth_stricter_gate` as the active research lead, compare tested refinements against the previous growth-biased baseline, recommend stricter-gate validation/checkpointing rather than more random variants, and preserve false execution approval flags.
- **Growth-biased stricter validation checkpoint:** `python scripts\verify_growth_biased_stricter_validation.py` verifies `--growth-biased-stricter-validation` and `--show-growth-biased-stricter-validation` remain saved-output validation/display only, write ignored split/cost/drawdown/benchmark/promotion validation CSVs, keep `growth_biased_rotation_breadth_stricter_gate` as research lead, and preserve false execution approval flags.
- **Growth-biased stricter promotion-readiness checkpoint:** `python scripts\verify_growth_biased_stricter_promotion_readiness.py` verifies `--growth-biased-stricter-promotion-readiness` and `--show-growth-biased-stricter-promotion-readiness` remain saved-output blocker/display only, write ignored promotion-readiness CSVs, keep `growth_biased_rotation_breadth_stricter_gate` as research lead, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter manual-review-pack checkpoint:** `python scripts\verify_growth_biased_stricter_manual_review_pack.py` verifies `--growth-biased-stricter-manual-review-pack` and `--show-growth-biased-stricter-manual-review-pack` remain saved-output report/display only, write ignored manual-review and regime-context CSVs, keep `growth_biased_rotation_breadth_stricter_gate` as research lead, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter threshold-neighbourhood checkpoint:** `python scripts\verify_growth_biased_stricter_threshold_neighbourhood.py` verifies `--growth-biased-stricter-threshold-neighbourhood` and `--show-growth-biased-stricter-threshold-neighbourhood` remain fixed research/report-display only, write ignored threshold-neighbourhood CSVs, test only the fixed 40/45/50/55/60 breadth-gate neighbourhood, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter cost/turnover stress checkpoint:** `python scripts\verify_growth_biased_stricter_cost_turnover_stress.py` verifies `--growth-biased-stricter-cost-turnover-stress` and `--show-growth-biased-stricter-cost-turnover-stress` remain saved-output report/display only, write ignored cost/turnover stress CSVs, test only fixed 0/5/10/25/50/100 bps one-way costs for the 55% cluster, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Growth-biased stricter persistence-filter checkpoint:** `python scripts\verify_growth_biased_stricter_persistence_filter.py` verifies `--growth-biased-stricter-persistence-filter` and `--show-growth-biased-stricter-persistence-filter` remain fixed research/report-display only, test the fixed persistence variants plus one Codex-designed `codex_ambitious_concentrated_growth_persistence` candidate, write ignored persistence CSVs, and preserve false execution, promotion, paper execution, and scheduling approval flags.
- **Codex ambitious validation checkpoint:** `python scripts\verify_codex_ambitious_validation.py` verifies `--codex-ambitious-validation` and `--show-codex-ambitious-validation` remain saved-output report/display only, validate `codex_ambitious_concentrated_growth_persistence` for possible active research-lead discussion, write ignored validation/split/cost/drawdown CSVs, and preserve false execution, promotion, paper execution, and scheduling approval flags.
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
