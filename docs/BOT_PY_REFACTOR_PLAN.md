# `bot.py` Refactor Plan

## Purpose

`bot.py` is currently the compatibility entry point for the project, but at
roughly 12,800 lines it also contains CLI parsing, command dispatch,
research/backtest orchestration, paper-trading orchestration, and order
submission helpers. That makes ordinary changes harder to review and makes
high-risk paths sit too close to report-only work.

This plan reduces `bot.py` to a small compatibility entry point without
changing command behaviour, research results, order rules, or paper-only
safety controls.

This is a refactor plan, not approval to change trading logic or submit a
paper order.

## Non-negotiable safety boundary

- Keep the existing paper-only configuration and all explicit confirmation
  gates.
- Do not add live trading, scheduling, or background execution.
- Do not run `--paper-order-test`, `--execute-slow-sma-paper`, or
  `--execute-qqq100-paper` while validating refactor work.
- Do not weaken the paper kill switch, duplicate-order checks, position
  checks, SQLite audit trail, or alert behaviour.
- Treat any code that can submit an Alpaca order, mutate execution state, or
  write a trade log as a separate high-risk change with focused mocked tests.
- Keep `config.json`, broker credentials, and any other secrets private.

## What the repository already has

The project is not starting from a blank slate. Useful pieces already live in
separate modules:

- `trading_bot/config.py`, `database.py`, `market_data.py`, `positions.py`,
  `alpaca_client.py`, `execution.py`, and `safety/` own core concerns.
- `trading_bot/research/` contains most saved-data reports, research helpers,
  and strategy logic.
- `trading_bot/runners/research_reports.py` already proves the intended
  pattern: a thin command wrapper delegates to a focused research module.
- The existing tests cover config, execution decisions, paper-live evidence,
  and QQQ100 alignment.

The remaining concentration is mainly in `bot.py`:

| Area | Approximate shape today | Risk |
| --- | --- | --- |
| Early report-only routing | Import-time fast paths | Low, but awkward to test |
| CLI parser | 550+ option registrations | Medium |
| Main dispatch | Long ordered chain of flag checks | Medium |
| Research and backtests | Large orchestration helpers | Medium |
| Normal paper path and order helpers | Alpaca, logging, and order decisions close together | High |
| Manual, slow-SMA, and QQQ100 paper paths | Explicitly gated but order-capable | High |

## Target architecture

The end state keeps `python bot.py ...` working, but makes the entry point a
thin compatibility facade.

```text
bot.py
  -> trading_bot.cli.entrypoint.run(argv)
       -> trading_bot.cli.parser.parse_args(argv)
       -> trading_bot.cli.dispatch.dispatch(args)
            -> trading_bot.runners.report_only
            -> trading_bot.runners.research
            -> trading_bot.runners.backtests
            -> trading_bot.runners.previews
            -> trading_bot.runners.paper_execution  (separate high-risk phase)

trading_bot.execution.py
  -> pure decision helpers only

trading_bot.alpaca_client.py
  -> raw broker read helpers and one deliberately reviewed submission adapter

trading_bot.safety/
  -> gates that are pure, isolated, and directly unit-tested
```

`trading_bot/runners/` is deliberately reused instead of proposing an
`execution/` directory: `trading_bot/execution.py` already exists, so a folder
with that name would conflict with Python imports.

## Delivery rules for every phase

Each implementation PR should:

1. Move one coherent responsibility only.
2. Preserve command names, help text, defaults, exit codes, output files, and
   side-effect boundaries unless a separately approved behaviour change says
   otherwise.
3. Add or retain characterization tests before deleting the old code.
4. Run `pytest -q` plus the focused tests for the moved area.
5. Avoid broker calls, market-data downloads, Discord alerts, SQLite writes,
   and all order-capable commands during routine refactor verification.
6. Be small enough that a reviewer can compare the old function with the new
   module without detective work.

## Phase 0: Lock down behaviour before moving it

**Goal:** create a reliable safety net; do not materially reduce `bot.py` yet.

- Add a command inventory generated from the parser and compare it to a saved
  expected list. This protects against silently dropping one of the many CLI
  flags during extraction.
- Add parser characterization tests for representative command families:
  normal run, report-only, research/backtest, preview, and explicitly
  confirmed paper commands.
- Add dispatch tests with mocked runner functions. They should prove the right
  flag reaches the right runner without invoking an external dependency.
- Expand mocked tests around every direct order-submission call site before
  moving those paths later.
- Record the baseline test command and current test count in the PR that
  starts the implementation work.

**Exit criteria:** the safety net can detect a missing flag, changed default,
or altered dispatch destination without touching Alpaca.

## Phase 1: Extract the parser unchanged

**Goal:** move the long `argparse` registration block into
`trading_bot/cli/parser.py` as a mechanical extraction.

- Keep flag spelling, help text, choices, defaults, and mutually exclusive
  relationships byte-for-byte where practical.
- Make `bot.py` import and call `parse_args`; do not redesign the flags.
- Keep early reporting behaviour intact for this phase. The point is a narrow,
  reviewable move.

**Exit criteria:** `python bot.py --help` exposes the same command inventory,
and parser characterization tests pass.

## Phase 2: Extract report-only and saved-output dispatch

**Goal:** remove the lowest-risk routing first.

- Move early report-only routes into `trading_bot/cli/report_only.py`.
- Move saved-output/report commands to runner functions under the existing
  `trading_bot/runners/` package.
- Preserve the current rule that a report-only command must not turn into a
  market-data refresh, broker read, order submission, alert, or SQLite write.
- Replace import-time routing with an explicit `entrypoint.run(argv)` call
  where tests prove the observable command behaviour remains the same.

**Exit criteria:** report-only routing has focused tests and no longer needs
thousands of unrelated imports in `bot.py`.

## Phase 3: Extract research and backtest orchestration

**Goal:** move research-mode orchestration into clearly named runners without
changing any strategy calculation.

- Create focused runner modules such as `research.py`, `backtests.py`, and
  `previews.py` only where the ownership boundary is genuinely clear.
- Keep calculations in their existing strategy and research modules.
- Preserve output file names, CSV columns, cost-model settings, and failure
  messages.
- Separate saved-data-only commands from commands that may download market
  data. Their names and tests should make that distinction obvious.

**Exit criteria:** research/backtest dispatch is outside `bot.py`; no strategy
math is rewritten as part of this phase.

## Phase 4: Make command dispatch declarative and testable

**Goal:** replace the giant ordered `if args...` chain with a small, explicit
dispatch layer.

- Use a command registry or ordered command descriptors only after the
  existing ordering is captured in tests.
- Keep multi-argument commands and confirmation flags explicit; do not hide
  them behind magic reflection.
- Make each command descriptor state its side-effect class:
  `report_only`, `research`, `market_data`, `broker_read`, or
  `paper_execution`.
- Use the side-effect class for audit tests and human-readable command
  documentation, not to silently change permission at runtime.

**Exit criteria:** adding a new report command does not require editing a
thousands-of-lines conditional chain, and no command is routed twice.

## Phase 5: Isolate normal paper execution, without changing it

**Goal:** move the normal path only after its behaviour is characterised.

- Extract `run_bot`, ticker processing, summary building, and execution
  context into a dedicated runner module.
- Keep the current paper configuration checks, dry-run path, order decision
  logic, database write logic, and alert calls intact.
- Use dependency injection for the Alpaca client, clock, database writer, and
  alert sender so tests can prove behaviour without a network connection.
- Do not consolidate order submission in this phase unless all existing order
  paths are already protected by tests.

**Exit criteria:** mocked tests prove normal-run decisions, skipped-order
reasons, database records, and alert boundaries are unchanged.

## Phase 6: Audit and isolate each order-capable path

**Goal:** give every paper-order route one clearly reviewed gateway.

This is the highest-risk phase and should happen only in a separate explicitly
approved PR series.

- First inventory direct submission calls and identify which safety gate,
  confirmation flag, duplicate-order check, and post-submit status check each
  one currently uses.
- Create a narrow `OrderRequest` / `OrderResult` adapter around the existing
  broker client. It must be paper-only and take its confirmation state
  explicitly.
- Route one path at a time: normal, manual paper-order test, slow-SMA paper
  path, then QQQ100 if still order-capable.
- Add a regression test before and after each move for paper-only enforcement,
  kill-switch behaviour, confirmation requirements, duplicate/open-order
  refusal, position limits, and post-submit state handling.
- Leave read-only Alpaca reports separate from the submission adapter.

**Exit criteria:** all actual order submissions pass through one audited
adapter, while no report-only path imports or reaches it.

## Phase 7: Finish the compatibility facade and remove dead code carefully

**Goal:** make `bot.py` genuinely small and make ownership obvious.

- Reduce `bot.py` to imports plus `SystemExit(run(sys.argv[1:]))`.
- Keep it as the supported compatibility command until a later deliberate
  packaging/console-script change.
- Remove only code proven unreachable by the command inventory and tests.
- Archive historical verifier scripts only after checking documentation and
  scheduled/manual runbooks no longer reference them.
- Update the command reference and architecture section of the README.

**Exit criteria:** `bot.py` is a thin facade, the public CLI remains stable,
and a new contributor can identify the owner of a command without searching a
12,000-line file.

## Suggested PR sequence

1. `Add bot refactor characterization tests`
2. `Extract bot CLI parser`
3. `Extract report-only command routing`
4. `Extract research and backtest runners`
5. `Introduce audited command dispatch`
6. `Extract normal paper execution runner`
7. `Route paper submissions through audited gateway`
8. `Finish bot entrypoint refactor`

The first five are structural. The last three touch execution-adjacent code
and deserve slower review, mocked broker tests, and explicit user approval.

## Definition of done

- `bot.py` is a small compatibility facade rather than the project runtime.
- Existing CLI commands retain their behaviour and side-effect boundaries.
- The command inventory is test-covered.
- Report-only commands cannot accidentally enter market-data, broker, order,
  alert, or database-write paths.
- Every actual paper-order submission uses one audited adapter and preserves
  paper-only, confirmation, gate, duplicate-order, and position protections.
- The full test suite passes without broker credentials or network access.
- No refactor PR has introduced live trading or changed a strategy's economic
  rules by accident.

## First implementation recommendation

Start with Phase 0, then Phase 1. It produces a clean, useful reduction in
future risk without touching research logic or anything that could submit an
order. The order-gateway work should wait until its current behaviour is fully
characterised, because safety is more valuable here than fast file splitting.
