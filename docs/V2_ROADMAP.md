# V2 Roadmap

This roadmap is documentation and workflow planning only. It does not change code, config defaults, strategy logic, generated outputs, scheduling, or execution behaviour.

## Safety Boundaries

- Live trading remains out of scope.
- `dry_run` defaults to `true`.
- `alpaca.paper` must remain `true`.
- `allow_shorting` defaults to `false`.
- Config files, credentials, account IDs, auth files, tokens, logs, databases, generated CSVs, and chart outputs stay private unless a future task explicitly scopes a safe read of a specific non-secret generated artefact.
- Research, preview, report, and display outputs do not approve execution.
- Paper execution remains separate, explicit, confirmation-gated, and manually reviewed.
- Execution-capable loops or scheduled order workflows are not approved.

## Codex Commit/Push Policy

Codex may commit and push by itself only for small low-risk changes, such as docs-only updates, typo or formatting fixes, workflow notes, README or documentation clarifications, non-execution report text changes, and small verifier-script or documentation changes that do not touch trading logic.

Before Codex auto-commits or pushes, it must run `python scripts\verify_repo_safety.py`, run any focused verifier relevant to the task if code changed, confirm no Python execution paths changed unless explicitly scoped, confirm no secrets or generated artefacts were touched, show a `git status` summary in its report, and use a clear commit message.

Codex must not auto-push Alpaca/order submission changes, normal `python bot.py` runtime behaviour changes, slow SMA paper execution changes, paper-order smoke test changes, command-routing changes touching execution paths, config default changes, scheduling/cron/loop changes, risk or kill-switch enforcement changes, generated CSV/log/database/chart changes, or anything involving credentials/secrets.

For medium/high-risk changes, Codex may make a local branch or local commit only if explicitly asked, but must not push until the user reviews the diff and approves.

## Towards Live Paper Monitoring

The staged direction is:

A. Expand ticker universe in research/preview only.
B. Add or improve ticker-universe validation/reporting.
C. Add more frequent market monitoring as preview/display/report only.
D. Add loop/cron support only after single-run commands are stable.
E. Add lockfile/no-overlap protection before any repeated run.
F. Add portfolio risk controls before expanded paper execution.
G. Keep paper execution separate, explicit, confirmation-gated, and manually reviewed.
H. Do not treat monitoring signals as execution approval.

More frequent price checks do not mean more frequent trades. Daily strategies should not overtrade intraday noise unless a separate intraday strategy is researched and validated. For now, frequent monitoring should mean observe/report/preview, not submit orders.

## More Tickers Rule

More tickers should start with liquid U.S. stocks and ETFs only. Add universe expansion to research/preview first, then add liquidity, price, and duplicate validation before execution.

More tickers require portfolio risk limits, max open positions, max notional exposure, and concentration checks before expanded paper execution.
