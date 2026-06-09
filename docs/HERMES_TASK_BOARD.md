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
- **Purpose:** Compare `HERMES_WORKFLOW.md`, `CODEX_WORKFLOW.md`, `CURRENT_STATE.md`, and VPS/refactor docs for inconsistent safety wording.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - `docs/HERMES_WORKFLOW.md`
  - `docs/CODEX_WORKFLOW.md`
  - `docs/CURRENT_STATE.md`
  - `docs/V2_REFACTOR_INVENTORY.md`
  - `docs/VPS_SETUP_CHECKLIST.md`
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
- **Purpose:** Make Hermes/Codex report-back formats consistent: files changed, verification, Python changed, execution paths changed, secrets touched.
- **Risk level:** Low / docs-only.
- **Allowed files:**
  - `docs/HERMES_WORKFLOW.md`
  - `docs/CODEX_WORKFLOW.md`
- **Forbidden files:**
  - Source code
  - generated outputs
  - secrets/config/logs/databases
- **Allowed commands:** None by default.
- **Stop condition:** Stop if implementation changes are requested as part of wording cleanup.

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
