# External Review — 2026-06-22

Outside review of the paper-trading-bot, requested as feedback. **Read-only — no bot code was changed.**

Combines a manual read of the core paths with an independent automated review (OpenAI Codex gpt-5.5). Every bug claim was verified at the cited `file:line`.

## Read in this order

1. **[REVIEW.md](REVIEW.md)** — what it does, what's good, and all findings (severity-ranked). Start here.
2. **[REFACTOR_PLAN.md](REFACTOR_PLAN.md)** — how to tame the 7,774-line `bot.py` and build one order gateway. Fixes the critical finding structurally.
3. **[RISK_CONTROLS_CHECKLIST.md](RISK_CONTROLS_CHECKLIST.md)** — what must exist before real money is ever considered.
4. **[TESTING_PLAN.md](TESTING_PLAN.md)** — a real `pytest` suite for the money-touching code, with starter code.

## One-line verdict

Impressive safety-first foundation for a learning project; held back by a god-file that let the kill-switch miss the main order path, plus the absence of real tests. Fix the order gateway (Refactor Phases 0–1) and the three verified order bugs, then add the tests — that's the high-leverage 20%.
