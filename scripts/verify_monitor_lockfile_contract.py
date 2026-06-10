from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SAFE_DOC_PATHS = [
    ROOT / "README.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
    ROOT / "docs" / "HERMES_WORKFLOW.md",
    ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ROOT / "docs" / "CODEX_WORKFLOW.md",
]

ALLOWED_METADATA_FIELDS = [
    "command name",
    "started_at",
    "host",
    "pid",
    "lock_version",
    "stale_after_seconds",
]

FORBIDDEN_LOCK_CONTENTS = [
    "secrets",
    "account IDs",
    "API keys",
    "webhook URLs",
    "order IDs",
    "config contents",
    "logs",
    "database contents",
    "generated CSV contents",
    "trading history",
]

BLOCKED_COMMANDS = [
    "normal `python bot.py`",
    "python bot.py --paper-order-test ... --confirm-paper-order",
    "python bot.py --execute-slow-sma-paper --confirm-slow-sma-paper",
    "any future execution-capable command",
]

PAPER_ONLY_BOUNDARIES = [
    "paper-only",
    "dry_run",
    "alpaca.paper",
    "allow_shorting",
    "scheduling approval",
    "execution approval",
]

REQUIRED_CONTRACT_PHRASES = [
    "pure",
    "no-network",
    "stale lock",
    "conservative",
    "manual review",
    "report, preview, display, and monitor refresh commands",
    "does not approve scheduling",
    "does not approve execution",
    "lock helper tests",
    "transient no-overlap lock",
]


def main() -> int:
    failures: list[str] = []
    docs_text = "\n".join(read_text(path) for path in SAFE_DOC_PATHS)
    docs_lower = docs_text.lower()

    require_present(docs_lower, REQUIRED_CONTRACT_PHRASES, "contract phrase", failures)
    require_present(docs_text, ALLOWED_METADATA_FIELDS, "allowed metadata field", failures)
    require_present(docs_text, FORBIDDEN_LOCK_CONTENTS, "forbidden lock content", failures)
    require_present(docs_lower, [command.lower() for command in BLOCKED_COMMANDS], "blocked command", failures)
    require_present(docs_lower, PAPER_ONLY_BOUNDARIES, "paper-only boundary", failures)
    verify_no_network_imports(failures)
    verify_no_runtime_locking_claims(docs_lower, failures)

    if failures:
        print("Monitor lockfile contract verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Monitor lockfile contract verification passed.")
    print("Verified pure/no-network contract wording, metadata limits, blocked commands, paper-only boundaries, and test requirement.")
    return 0


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def require_present(source: str, required: list[str], label: str, failures: list[str]) -> None:
    for item in required:
        if item not in source:
            failures.append(f"Missing {label}: {item}")


def verify_no_network_imports(failures: list[str]) -> None:
    source = Path(__file__).read_text(encoding="utf-8")
    forbidden_imports = ["requests", "urllib", "http.client", "socket", "yfinance", "alpaca"]
    for name in forbidden_imports:
        if f"import {name}" in source or f"from {name}" in source:
            failures.append(f"Verifier must remain no-network and must not import {name}")


def verify_no_runtime_locking_claims(docs_lower: str, failures: list[str]) -> None:
    required_refusals = [
        "only command protected by the monitor lockfile helper",
        "future safe report/display/monitor refresh commands remain manual-review only",
        "does not create schedules",
        "execution-capable commands must never be scheduled",
    ]
    for phrase in required_refusals:
        if phrase not in docs_lower:
            failures.append(f"Missing runtime-locking refusal: {phrase}")


if __name__ == "__main__":
    sys.exit(main())
