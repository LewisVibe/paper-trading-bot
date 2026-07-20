"""Local deployment readiness audit for future server/VPS use."""

from __future__ import annotations

import csv
import importlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEPLOYMENT_READINESS_COLUMNS = [
    "created_at",
    "check_name",
    "check_status",
    "risk_level",
    "finding",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

SAFE_SCHEDULE_CANDIDATES = [
    "--refresh-defensive-research",
    "--refresh-promoted-review",
    "--show-promoted-decision",
    "--show-crypto-monitor",
    "--research-report",
    "--walk-forward-report",
    "--strategy-promotion-report",
    "--defensive-candidate-comparison",
    "--drawdown-period-report",
]

MUST_NOT_SCHEDULE_COMMANDS = [
    "--paper-order-test",
    "--execute-slow-sma-paper",
    "every execution command except --run-vol-targeted-growth-auto-paper",
]

REQUIRED_GITIGNORE_PATTERNS = [
    "config.json",
    ".env",
    ".env.*",
    ".venv/",
    "logs/*",
    "!logs/.gitkeep",
    "*.log",
    "data/*",
    "!data/.gitkeep",
    "*.db",
]

PACKAGE_IMPORTS = {
    "yfinance": "yfinance",
    "alpaca-py": "alpaca",
    "requests": "requests",
    "matplotlib": "matplotlib",
}


@dataclass
class DeploymentReadinessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_deployment_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/deployment_readiness_report.csv",
) -> DeploymentReadinessReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = build_deployment_readiness_rows(root, created_at)
    output_path = root / output_filename
    write_deployment_readiness_report(output_path, rows)
    return DeploymentReadinessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_deployment_readiness_summary(rows, output_path),
    )


def build_deployment_readiness_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    cli_source = "\n".join(
        [
            read_text(root / "trading_bot" / "cli" / "parser.py"),
            read_text(root / "trading_bot" / "cli" / "application.py"),
            read_text(root / "trading_bot" / "cli" / "dispatch.py"),
        ]
    )
    config_source = read_text(root / "trading_bot" / "config.py")
    readme_source = read_text(root / "README.md")
    current_state_exists = (root / "docs" / "CURRENT_STATE.md").exists()
    help_text = bot_help_text(root)
    gitignore_lines = gitignore_patterns(root / ".gitignore")
    missing_gitignore_patterns = [pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in gitignore_lines]
    git_available = git_executable() is not None
    git_status = git_status_summary(root)
    repo_safety = repo_safety_summary(root)
    packages_ok, package_finding = required_packages_importable()

    rows = [
        readiness_row(
            created_at,
            "python_version_compatible",
            "pass" if sys.version_info >= (3, 11) else "blocked_for_review",
            "medium",
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} is available.",
            "Use Python 3.11 or newer on the VPS.",
        ),
        readiness_row(
            created_at,
            "required_packages_importable",
            "pass" if packages_ok else "blocked_for_review",
            "medium",
            package_finding,
            "Install requirements.txt in the VPS environment before running the bot.",
        ),
        readiness_row(
            created_at,
            "requirements_txt_exists",
            "pass" if (root / "requirements.txt").exists() else "blocked_for_review",
            "medium",
            "requirements.txt exists." if (root / "requirements.txt").exists() else "requirements.txt is missing.",
            "Keep requirements.txt committed for VPS setup.",
        ),
        readiness_row(
            created_at,
            "config_example_exists",
            "pass" if (root / "config.example.json").exists() else "blocked_for_review",
            "high",
            "config.example.json exists." if (root / "config.example.json").exists() else "config.example.json is missing.",
            "Keep a safe example config committed.",
        ),
        readiness_row(
            created_at,
            "config_json_local_presence",
            "warning" if (root / "config.json").exists() else "not_applicable",
            "high",
            "config.json exists locally; contents were not read or printed." if (root / "config.json").exists() else "config.json is not present locally.",
            "Never commit config.json or print its contents.",
        ),
        readiness_row(
            created_at,
            "config_json_ignored_by_git",
            "pass" if "config.json" in gitignore_lines else "blocked_for_review",
            "high",
            "config.json is listed in .gitignore." if "config.json" in gitignore_lines else "config.json is not listed in .gitignore.",
            "Add config.json to .gitignore before using private config locally.",
        ),
        readiness_row(
            created_at,
            "env_files_ignored_by_git",
            "pass" if ".env" in gitignore_lines and ".env.*" in gitignore_lines else "blocked_for_review",
            "high",
            ".env and .env.* are listed in .gitignore." if ".env" in gitignore_lines and ".env.*" in gitignore_lines else ".env ignore patterns are incomplete.",
            "Keep .env and .env.* ignored.",
        ),
        readiness_row(
            created_at,
            "core_gitignore_patterns_present",
            "pass" if not missing_gitignore_patterns else "blocked_for_review",
            "high",
            "Core private/generated-file .gitignore patterns are present." if not missing_gitignore_patterns else "Missing .gitignore patterns: " + ", ".join(missing_gitignore_patterns),
            "Keep private config, environment files, generated data, logs, and databases ignored.",
        ),
        readiness_row(
            created_at,
            "data_and_logs_directories_exist",
            "pass" if (root / "data").is_dir() and (root / "logs").is_dir() else "warning",
            "medium",
            "data/ and logs/ directories exist." if (root / "data").is_dir() and (root / "logs").is_dir() else "data/ or logs/ directory is missing.",
            "Create data/ and logs/ on the VPS before scheduled/report runs.",
        ),
        readiness_row(
            created_at,
            "gitkeep_placeholders_exist",
            "pass" if (root / "data" / ".gitkeep").exists() and (root / "logs" / ".gitkeep").exists() else "warning",
            "low",
            "data/.gitkeep and logs/.gitkeep exist." if (root / "data" / ".gitkeep").exists() and (root / "logs" / ".gitkeep").exists() else "One or both .gitkeep placeholders are missing.",
            "Keep placeholders so empty generated-output directories are represented.",
        ),
        readiness_row(
            created_at,
            "repo_safety_verifier",
            repo_safety[0],
            "high",
            repo_safety[1],
            "Run python scripts\\verify_repo_safety.py before commits and VPS handoff.",
        ),
        readiness_row(
            created_at,
            "git_working_tree_status",
            git_status[0],
            "medium",
            git_status[1],
            "Review uncommitted changes before deployment handoff.",
        ),
        readiness_row(
            created_at,
            "git_remote_configured",
            "pass" if git_available and git_remote_configured(root) else ("not_applicable" if not git_available else "warning"),
            "low",
            git_remote_finding(root, git_available),
            "Configure a Git remote before VPS clone/pull workflows.",
        ),
        readiness_row(
            created_at,
            "alpaca_paper_safety_rule",
            "pass" if "alpaca.paper must be true" in config_source else "blocked_for_review",
            "high",
            "Config validation refuses non-paper Alpaca mode." if "alpaca.paper must be true" in config_source else "Could not confirm alpaca.paper safety validation.",
            "Keep Alpaca paper-only validation before server use.",
        ),
        readiness_row(
            created_at,
            "dry_run_default_true",
            "pass" if 'parse_config_bool(raw, "dry_run", True)' in config_source else "blocked_for_review",
            "high",
            "dry_run defaults to true in config loading." if 'parse_config_bool(raw, "dry_run", True)' in config_source else "Could not confirm dry_run default true.",
            "Keep dry_run default true.",
        ),
        readiness_row(
            created_at,
            "allow_shorting_default_false",
            "pass" if 'parse_config_bool(raw, "allow_shorting", False)' in config_source else "blocked_for_review",
            "high",
            "allow_shorting defaults to false in config loading." if 'parse_config_bool(raw, "allow_shorting", False)' in config_source else "Could not confirm allow_shorting default false.",
            "Keep allow_shorting default false.",
        ),
        readiness_row(
            created_at,
            "high_risk_commands_gated",
            "pass" if high_risk_commands_gated(help_text, cli_source) else "blocked_for_review",
            "high",
            "Manual paper order and slow SMA paper execution commands remain explicitly gated." if high_risk_commands_gated(help_text, cli_source) else "Could not confirm high-risk commands remain gated.",
            "Keep confirmation flags required for execution-capable commands.",
        ),
        readiness_row(
            created_at,
            "safe_scheduled_command_candidates_documented",
            "pass" if all(command in help_text or command in readme_source for command in SAFE_SCHEDULE_CANDIDATES[:4]) else "warning",
            "medium",
            "Safe report/display refresh candidates are available for future scheduling review.",
            "Only schedule report/display commands after single-run checks remain stable.",
        ),
        readiness_row(
            created_at,
            "must_not_schedule_commands_documented",
            "pass" if all(command in help_text for command in ["--paper-order-test", "--execute-slow-sma-paper"]) else "blocked_for_review",
            "high",
            "Execution-capable commands are identifiable and must not be scheduled automatically.",
            "Do not schedule execution-capable commands without a separate safety design.",
        ),
        readiness_row(
            created_at,
            "readme_windows_task_scheduler_note",
            "pass" if task_scheduler_boundary_documented(readme_source) else "warning",
            "medium",
            "README mentions Task Scheduler readiness boundaries." if task_scheduler_boundary_documented(readme_source) else "README does not yet mention Task Scheduler readiness boundaries.",
            "Document any future scheduler setup as report/display only until execution is separately approved.",
        ),
        readiness_row(
            created_at,
            "current_state_handoff_exists",
            "pass" if current_state_exists else "warning",
            "low",
            "docs/CURRENT_STATE.md exists for handoff context." if current_state_exists else "docs/CURRENT_STATE.md is missing.",
            "Keep CURRENT_STATE.md updated before VPS handoff.",
        ),
    ]
    return rows


def readiness_row(
    created_at: str,
    check_name: str,
    check_status: str,
    risk_level: str,
    finding: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "check_name": check_name,
        "check_status": check_status,
        "risk_level": risk_level,
        "finding": finding,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def required_packages_importable() -> tuple[bool, str]:
    failures = []
    for requirement_name, module_name in PACKAGE_IMPORTS.items():
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{requirement_name}: {type(exc).__name__}")
    if failures:
        return False, "Required package import failures: " + ", ".join(failures)
    return True, "Required packages import without network calls."


def repo_safety_summary(root: Path) -> tuple[str, str]:
    script = root / "scripts" / "verify_repo_safety.py"
    if not script.exists():
        return "warning", "Repo safety verifier is missing."
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return "warning", "Repo safety verifier timed out."
    if result.returncode == 0:
        return "pass", "Repo safety verifier passed."
    return "warning", "Repo safety verifier did not pass in this environment."


def git_status_summary(root: Path) -> tuple[str, str]:
    git = git_executable()
    if git is None:
        return "not_applicable", "Git is unavailable; working tree status is unknown."
    result = run_git(root, ["status", "--porcelain"])
    if result is None:
        return "warning", "Git status could not be inspected."
    if not result:
        return "pass", "Git working tree is clean."
    return "warning", "Git working tree has local changes; review before VPS handoff."


def git_remote_configured(root: Path) -> bool:
    result = run_git(root, ["remote", "-v"])
    return bool(result)


def git_remote_finding(root: Path, git_available: bool) -> str:
    if not git_available:
        return "Git is unavailable; remote configuration is unknown."
    return "Git remote is configured." if git_remote_configured(root) else "No Git remote detected."


def run_git(root: Path, args: list[str]) -> str | None:
    git = git_executable()
    if git is None:
        return None
    try:
        result = subprocess.run(
            [git, *args],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_executable() -> str | None:
    found = shutil.which("git")
    if found:
        return found
    for path in [
        Path("C:/Program Files/Git/bin/git.exe"),
        Path("C:/Program Files/Git/cmd/git.exe"),
        Path("C:/Program Files (x86)/Git/bin/git.exe"),
        Path("C:/Program Files (x86)/Git/cmd/git.exe"),
    ]:
        if path.exists():
            return str(path)
    return None


def high_risk_commands_gated(help_text: str, cli_source: str) -> bool:
    return (
        "--paper-order-test" in help_text
        and "--confirm-paper-order" in help_text
        and "--execute-slow-sma-paper" in help_text
        and "--confirm-slow-sma-paper" in help_text
        and "--confirm-paper-order" in cli_source
        and "--confirm-slow-sma-paper" in cli_source
    )


def task_scheduler_boundary_documented(readme_source: str) -> bool:
    lower_source = readme_source.lower()
    scheduler_named = "windows task scheduler" in lower_source or "task scheduler" in lower_source
    execution_refused = "do not schedule execution-capable commands" in lower_source or "must never be placed" in lower_source
    return scheduler_named and execution_refused


def gitignore_patterns(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def write_deployment_readiness_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=DEPLOYMENT_READINESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in DEPLOYMENT_READINESS_COLUMNS})


def build_deployment_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = {
        status: sum(1 for row in rows if row.get("check_status") == status)
        for status in ["pass", "warning", "blocked_for_review", "not_applicable"]
    }
    blocked = [str(row["check_name"]) for row in rows if row.get("check_status") == "blocked_for_review"]
    return [
        "DEPLOYMENT READINESS REPORT. REPORTING ONLY. NOT EXECUTION.",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, blocked: {counts['blocked_for_review']}, not_applicable: {counts['not_applicable']}",
        "Blocked items: " + (", ".join(blocked) if blocked else "none"),
        "Safe-to-schedule candidates: " + ", ".join(SAFE_SCHEDULE_CANDIDATES),
        "Must-not-schedule commands: " + ", ".join(MUST_NOT_SCHEDULE_COMMANDS),
        "No deployment, scheduling, or execution approval was performed.",
        f"Saved deployment readiness report to {output_path}",
    ]


def bot_help_text(root: Path) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "bot.py", "--help"],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return ""
    return (result.stdout or "") + "\n" + (result.stderr or "")


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
