"""Research-only short-selling readiness audit.

This module performs static/local checks only. It does not enable shorting,
call broker APIs, read positions, create orders, write SQLite, send alerts, or
refresh market data.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SHORT_SELLING_READINESS_COLUMNS = [
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

DANGEROUS_SHORT_COMMAND_PATTERNS = [
    "--execute-short",
    "--short-execution",
    "--short-paper",
    "--short-selling-execute",
    "--crypto-short",
]


@dataclass
class ShortSellingReadinessReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_short_selling_readiness_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/short_selling_readiness_report.csv",
) -> ShortSellingReadinessReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = build_short_selling_readiness_rows(root, created_at)
    output_path = root / output_filename
    write_short_selling_readiness_report(output_path, rows)
    return ShortSellingReadinessReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_short_selling_readiness_summary(rows, output_path),
    )


def build_short_selling_readiness_rows(root: Path, created_at: str) -> list[dict[str, Any]]:
    config_source = read_text(root / "trading_bot" / "config.py")
    execution_source = read_text(root / "trading_bot" / "execution.py")
    bot_source = read_text(root / "bot.py")
    crypto_source = read_text(root / "trading_bot" / "research" / "crypto.py")
    promoted_risk_source = read_text(root / "trading_bot" / "research" / "promoted_risk.py")
    promoted_decision_source = read_text(root / "trading_bot" / "research" / "promoted_decision.py")
    readme_source = read_text(root / "README.md")
    help_text = bot_help_text(root)
    example_config = read_json(root / "config.example.json")

    rows = [
        readiness_row(
            created_at,
            "allow_shorting_default_false",
            "pass" if 'parse_config_bool(raw, "allow_shorting", False)' in config_source else "blocked_for_review",
            "high",
            "Config loading defaults allow_shorting to false." if 'parse_config_bool(raw, "allow_shorting", False)' in config_source else "Could not confirm allow_shorting defaults to false.",
            "Keep allow_shorting default false before any short-selling research.",
        ),
        readiness_row(
            created_at,
            "config_example_allow_shorting_false",
            "pass" if example_config.get("allow_shorting") is False else "blocked_for_review",
            "high",
            "config.example.json keeps allow_shorting=false." if example_config.get("allow_shorting") is False else "config.example.json does not clearly keep allow_shorting=false.",
            "Keep example config long-only by default.",
        ),
        readiness_row(
            created_at,
            "alpaca_paper_required",
            "pass" if 'parse_config_bool(alpaca, "paper", True' in config_source and "alpaca.paper must be true" in config_source else "blocked_for_review",
            "high",
            "Config validation requires Alpaca paper mode." if 'parse_config_bool(alpaca, "paper", True' in config_source and "alpaca.paper must be true" in config_source else "Could not confirm Alpaca paper-only validation.",
            "Keep alpaca.paper required true.",
        ),
        readiness_row(
            created_at,
            "normal_shorting_rules_gated",
            "warning" if "if not allow_shorting" in execution_source and "open_short" in execution_source else "blocked_for_review",
            "high",
            "Normal trade-decision helpers contain shorting logic, but it is gated by allow_shorting." if "if not allow_shorting" in execution_source and "open_short" in execution_source else "Could not confirm normal shorting rules are gated.",
            "Before any future short research, add targeted no-network tests for every long/short transition.",
        ),
        readiness_row(
            created_at,
            "slow_sma_long_only",
            "pass" if "allow_shorting must be false because the slow SMA strategy is long-only" in bot_source else "blocked_for_review",
            "high",
            "Slow SMA paper execution refuses allow_shorting=true." if "allow_shorting must be false because the slow SMA strategy is long-only" in bot_source else "Could not confirm slow SMA paper execution refuses shorting.",
            "Keep slow SMA paper execution long-only.",
        ),
        readiness_row(
            created_at,
            "promoted_pipeline_long_flat_only",
            "pass" if "desired_position" in promoted_risk_source and "unanimous_long" in promoted_decision_source and "execution_approved" in promoted_decision_source else "blocked_for_review",
            "medium",
            "Promoted review pipeline is framed around long/flat desired-position review and does not approve execution." if "desired_position" in promoted_risk_source and "unanimous_long" in promoted_decision_source and "execution_approved" in promoted_decision_source else "Could not confirm promoted review pipeline stays long/flat and non-execution.",
            "Keep promoted strategy reviews long/flat unless a separate short preview design is explicitly reviewed.",
        ),
        readiness_row(
            created_at,
            "crypto_shorting_disabled",
            "pass" if '"shorting_enabled": False' in crypto_source else "blocked_for_review",
            "high",
            "Crypto research preview marks shorting_enabled=False." if '"shorting_enabled": False' in crypto_source else "Could not confirm crypto shorting remains disabled.",
            "Keep crypto shorting disabled.",
        ),
        readiness_row(
            created_at,
            "no_short_execution_command",
            "pass" if not any(pattern in help_text for pattern in DANGEROUS_SHORT_COMMAND_PATTERNS) else "blocked_for_review",
            "high",
            "No short-selling execution command appears in help output." if not any(pattern in help_text for pattern in DANGEROUS_SHORT_COMMAND_PATTERNS) else "A short-selling execution-like command appears in help output.",
            "Do not add short execution commands without a separate safety design.",
        ),
        readiness_row(
            created_at,
            "no_research_preview_short_approval",
            "pass" if "execution_approved=False" in readme_source or "execution_approved=False" in promoted_decision_source else "warning",
            "high",
            "Research and preview documentation/code keep execution_approved false for preview/report outputs." if "execution_approved=False" in readme_source or "execution_approved=False" in promoted_decision_source else "Could not broadly confirm execution_approved remains false in preview/report outputs.",
            "Keep research and preview reports from approving shorting or any execution.",
        ),
        readiness_row(
            created_at,
            "docs_warn_short_risk",
            "pass" if "Short selling is riskier" in readme_source and "paper" in readme_source else "warning",
            "medium",
            "README warns that short selling is riskier and paper-only in this project." if "Short selling is riskier" in readme_source and "paper" in readme_source else "README short-selling warning was not found.",
            "Keep short-selling risk warnings prominent.",
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


def write_short_selling_readiness_report(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=SHORT_SELLING_READINESS_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in SHORT_SELLING_READINESS_COLUMNS})


def build_short_selling_readiness_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    counts = {
        status: sum(1 for row in rows if row.get("check_status") == status)
        for status in ["pass", "warning", "blocked_for_review", "not_applicable"]
    }
    blocked = [str(row["check_name"]) for row in rows if row.get("check_status") == "blocked_for_review"]
    return [
        "SHORT SELLING READINESS REPORT. RESEARCH ONLY. NOT EXECUTION.",
        f"Pass: {counts['pass']}, warning: {counts['warning']}, blocked: {counts['blocked_for_review']}, not_applicable: {counts['not_applicable']}",
        "Blocked items: " + (", ".join(blocked) if blocked else "none"),
        "Short selling is not enabled and is not execution-approved.",
        f"Saved short-selling readiness report to {output_path}",
    ]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    return data if isinstance(data, dict) else {}


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
