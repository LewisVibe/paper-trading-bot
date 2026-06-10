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
- **Candidate future command only:**
  ```bat
  cd /d C:\dev\paper-trading-bot
  .venv\Scripts\python.exe bot.py --refresh-market-monitor
  ```
- **Preferred scheduler:** Hermes cron once Hermes runs on the VPS. Windows Task Scheduler may be used only to start or keep the Hermes gateway running on boot, not for execution-capable trading commands.
- **Mode:** Prefer no-agent mode for deterministic commands where possible.
- **Prerequisites before scheduling review:**
  - `python scripts\verify_repo_safety.py`
  - `python bot.py --market-monitor-scheduling-readiness-report`
  - Manual successful VPS run of `python bot.py --refresh-market-monitor`
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
- **Current scaffold command:** `python bot.py --monitor-lockfile-readiness-report` writes `data/monitor_lockfile_readiness_report.csv` when run, but does not create a lockfile, wrap any command, approve scheduling, or approve execution.
- **Contract verifier:** `python scripts\verify_monitor_lockfile_contract.py` is pure/no-network and defines future helper requirements only.
- **Helper verifier:** `python scripts\verify_monitor_lockfile_helper.py` checks the isolated helper in `trading_bot/safety/monitor_lockfile.py`; the helper is not wired into runtime commands and does not create real lockfiles.
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
