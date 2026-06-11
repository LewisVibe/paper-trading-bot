from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SAFE_MANUAL_COMMANDS = [
    r".venv\Scripts\python.exe bot.py --monitor-lockfile-readiness-report",
    r".venv\Scripts\python.exe bot.py --refresh-promoted-review",
    r".venv\Scripts\python.exe bot.py --refresh-defensive-research",
]

BLOCKED_COMMANDS = [
    "normal python bot.py",
    "--paper-order-test",
    "--confirm-paper-order",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
]

GENERATED_PATHS = [
    "data/monitor_lockfile_readiness_report.csv",
    "data/promoted_review_refresh_summary.csv",
    "data/defensive_research_refresh_summary.csv",
    "data/promoted_strategy_preview.csv",
    "data/promoted_strategy_action_preview.csv",
    "data/promoted_risk_preview.csv",
    "data/promoted_consensus_preview.csv",
    "data/promoted_decision_preview.csv",
    "data/defensive_candidate_comparison.csv",
    "data/etf_defensive_drawdown_comparison.csv",
    "data/charts/etf_defensive_drawdown_comparison.png",
]

SAVED_RESEARCH_PREREQUISITES = [
    "data/vol_managed_etf_robustness_report.csv",
    "data/etf_rotation_robustness_report.csv",
]


@dataclass(frozen=True)
class CheckRow:
    check_name: str
    status: str
    risk_level: str
    evidence: str
    required_next_step: str
    execution_approved: bool = False
    scheduling_approved: bool = False


def main() -> int:
    rows = build_rows()
    print_rows(rows)
    errors = [row for row in rows if row.status == "error"]
    warnings = [row for row in rows if row.status == "warning"]
    print(f"VPS monitoring prerequisite checks: {len(rows)}")
    print(f"Pass: {count_status(rows, 'pass')}, warning: {len(warnings)}, error: {len(errors)}")
    print(f"Execution approved false for all rows: {all(row.execution_approved is False for row in rows)}")
    print(f"Scheduling approved false for all rows: {all(row.scheduling_approved is False for row in rows)}")
    print("Warning: this checkpoint is report/verifier-only and does not approve scheduling or execution.")
    return 1 if errors else 0


def build_rows() -> list[CheckRow]:
    rows: list[CheckRow] = []
    rows.extend(environment_rows())
    rows.extend(config_rows())
    rows.extend(saved_research_rows())
    rows.extend(command_boundary_rows())
    rows.extend(generated_output_rows())
    return rows


def environment_rows() -> list[CheckRow]:
    checks = [
        (
            "venv_python_exists",
            ROOT / ".venv" / "Scripts" / "python.exe",
            "environment_not_ready",
            "Create or repair .venv before running VPS manual monitoring commands.",
        ),
        (
            "requirements_txt_exists",
            ROOT / "requirements.txt",
            "environment_not_ready",
            "Restore requirements.txt before installing dependencies.",
        ),
        (
            "bot_py_exists",
            ROOT / "bot.py",
            "environment_not_ready",
            "Restore bot.py before running command inventory or report commands.",
        ),
        (
            "repo_safety_verifier_exists",
            ROOT / "scripts" / "verify_repo_safety.py",
            "environment_not_ready",
            "Restore repo safety verifier before VPS handoff.",
        ),
        (
            "lockfile_final_state_verifier_exists",
            ROOT / "scripts" / "verify_monitor_lockfile_final_state.py",
            "environment_not_ready",
            "Restore final lockfile state verifier before VPS handoff.",
        ),
        (
            "config_example_exists",
            ROOT / "config.example.json",
            "environment_not_ready",
            "Restore config.example.json; do not create config.json from this verifier.",
        ),
    ]
    rows = []
    for check_name, path, missing_status, next_step in checks:
        exists = path.exists()
        rows.append(
            CheckRow(
                check_name=check_name,
                status="pass" if exists else "error",
                risk_level="low" if exists else "medium",
                evidence=f"{path.relative_to(ROOT)} exists: {exists}",
                required_next_step="None." if exists else next_step,
            )
        )
    return rows


def config_rows() -> list[CheckRow]:
    config_path = ROOT / "config.json"
    config_exists = config_path.exists()
    if config_exists:
        return [
            CheckRow(
                "local_config_presence",
                "pass",
                "medium",
                "config.json exists locally; contents were not read.",
                "Keep config.json private and untracked; do not paste secrets.",
            )
        ]
    return [
        CheckRow(
            "config_missing_for_readonly_promoted_review",
            "warning",
            "medium",
            "config.json is absent; contents were not read or created.",
            (
                "--refresh-promoted-review may refuse in its read-only paper-position preview context. "
                "Create local config only through the normal private VPS setup process; never print or paste secrets."
            ),
        )
    ]


def saved_research_rows() -> list[CheckRow]:
    missing = [path for path in SAVED_RESEARCH_PREREQUISITES if not (ROOT / path).exists()]
    if missing:
        return [
            CheckRow(
                "missing_saved_research_inputs",
                "warning",
                "low",
                "Missing saved defensive research prerequisites: " + ", ".join(missing),
                (
                    "--refresh-defensive-research may report missing saved CSV/chart prerequisites. "
                    "Do not run heavy market-data backtests automatically just to fill them."
                ),
            )
        ]
    return [
        CheckRow(
            "saved_research_inputs_present",
            "pass",
            "low",
            "Expected saved defensive research prerequisites are present.",
            "None.",
        )
    ]


def command_boundary_rows() -> list[CheckRow]:
    docs = docs_text().lower()
    rows: list[CheckRow] = []
    for command in SAFE_MANUAL_COMMANDS:
        present = command.lower() in docs
        rows.append(
            CheckRow(
                "safe_manual_command_documented",
                "pass" if present else "error",
                "low" if present else "medium",
                command,
                "Document this as a manual VPS monitoring command only." if not present else "None.",
            )
        )
    for command in BLOCKED_COMMANDS:
        present = command.lower() in docs
        rows.append(
            CheckRow(
                "blocked_execution_command_documented",
                "pass" if present else "error",
                "high" if not present else "low",
                command,
                "Document this command as blocked/manual-only and never schedule it." if not present else "None.",
            )
        )
    for phrase in [
        "does not approve scheduling or execution",
        "lockfile protection does not approve scheduling or execution",
        "no scheduling",
    ]:
        present = phrase in docs
        rows.append(
            CheckRow(
                "scheduling_execution_boundary_documented",
                "pass" if present else "error",
                "high" if not present else "low",
                phrase,
                "Document that lockfile protection and safe commands do not approve scheduling or execution."
                if not present
                else "None.",
            )
        )
    return rows


def generated_output_rows() -> list[CheckRow]:
    rows = []
    for path in GENERATED_PATHS:
        ignored = is_git_ignored(path)
        tracked = is_git_tracked(path)
        status = "pass" if ignored and not tracked else "error"
        rows.append(
            CheckRow(
                "generated_output_ignored_untracked",
                status,
                "medium" if status == "error" else "low",
                f"{path}: ignored={ignored}, tracked={tracked}",
                "Keep generated CSV/chart outputs ignored and untracked." if status == "error" else "None.",
            )
        )
    return rows


def print_rows(rows: list[CheckRow]) -> None:
    for row in rows:
        print(
            f"{row.status.upper()}: {row.check_name} | risk={row.risk_level} | "
            f"execution_approved={row.execution_approved} | scheduling_approved={row.scheduling_approved}"
        )
        print(f"  evidence: {row.evidence}")
        print(f"  next: {row.required_next_step}")


def count_status(rows: list[CheckRow], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def docs_text() -> str:
    paths = [
        ROOT / "README.md",
        ROOT / "docs" / "CURRENT_STATE.md",
        ROOT / "docs" / "VPS_SETUP_CHECKLIST.md",
        ROOT / "docs" / "HERMES_TASK_BOARD.md",
    ]
    return "\n".join(read_text(path) for path in paths)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def is_git_ignored(path: str) -> bool:
    completed = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def is_git_tracked(path: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


if __name__ == "__main__":
    sys.exit(main())
