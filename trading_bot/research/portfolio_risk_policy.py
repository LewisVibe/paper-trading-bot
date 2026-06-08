"""Research-only portfolio risk policy audit."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PORTFOLIO_RISK_POLICY_COLUMNS = [
    "created_at",
    "risk_policy_name",
    "risk_policy_status",
    "risk_level",
    "current_value_or_limit",
    "finding",
    "required_next_step",
    "research_only",
    "preview_only",
    "execution_approved",
]

PORTFOLIO_RISK_POLICY_DISPLAY_COLUMNS = [
    "risk_policy_name",
    "risk_policy_status",
    "risk_level",
    "current_value_or_limit",
    "finding",
    "required_next_step",
    "execution_approved",
]

DEFAULT_MAX_OPEN_POSITIONS = 2


@dataclass
class PortfolioRiskPolicyReportResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def generate_portfolio_risk_policy_report(
    root_dir: Path | str = ".",
    output_filename: str = "data/portfolio_risk_policy_report.csv",
) -> PortfolioRiskPolicyReportResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    inputs = read_policy_inputs(root)
    rows = build_portfolio_risk_policy_rows(inputs, created_at)
    output_path = root / output_filename
    write_portfolio_risk_policy_report(output_path, rows)
    return PortfolioRiskPolicyReportResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_portfolio_risk_policy_summary(rows, output_path),
    )


def read_policy_inputs(root: Path) -> dict[str, Any]:
    return {
        "config_example": read_json(root / "config.example.json"),
        "promoted_decision": read_csv_rows(root / "data" / "promoted_decision_preview.csv"),
        "promoted_risk": read_csv_rows(root / "data" / "promoted_risk_preview.csv"),
        "promoted_actions": read_csv_rows(root / "data" / "promoted_strategy_action_preview.csv"),
        "defensive_comparison": read_csv_rows(root / "data" / "defensive_candidate_comparison.csv"),
        "deployment_readiness": read_csv_rows(root / "data" / "deployment_readiness_report.csv"),
        "current_state_exists": (root / "docs" / "CURRENT_STATE.md").exists(),
    }


def build_portfolio_risk_policy_rows(inputs: dict[str, Any], created_at: str) -> list[dict[str, Any]]:
    config_example = inputs["config_example"]
    promoted_decision = inputs["promoted_decision"]
    promoted_risk = inputs["promoted_risk"]
    defensive_comparison = inputs["defensive_comparison"]
    deployment_readiness = inputs["deployment_readiness"]

    paper_value = nested_value(config_example, ["alpaca", "paper"])
    dry_run_value = config_example.get("dry_run") if isinstance(config_example, dict) else None
    allow_shorting_value = config_example.get("allow_shorting") if isinstance(config_example, dict) else None

    unique_long_notional = unique_desired_long_notional_by_ticker(promoted_risk)
    duplicate_tickers = duplicate_desired_long_tickers(promoted_risk)
    strategy_disagreements = [
        row.get("ticker", "")
        for row in promoted_decision
        if row.get("decision_state") == "blocked_strategy_disagreement"
    ]
    approved_sources = execution_approved_sources(
        [
            ("promoted_decision_preview", promoted_decision),
            ("defensive_candidate_comparison", defensive_comparison),
            ("deployment_readiness_report", deployment_readiness),
        ]
    )

    rows = [
        policy_row(
            created_at,
            "paper_only_policy",
            "pass" if paper_value is True else "blocked_for_review",
            "high",
            f"alpaca.paper={format_value(paper_value)}",
            "config.example.json keeps Alpaca paper mode true." if paper_value is True else "Could not confirm alpaca.paper=true in config.example.json.",
            "Keep Alpaca paper mode true; live trading remains out of scope.",
        ),
        policy_row(
            created_at,
            "dry_run_default_policy",
            "pass" if dry_run_value is True else "blocked_for_review",
            "high",
            f"dry_run={format_value(dry_run_value)}",
            "config.example.json keeps dry_run true." if dry_run_value is True else "Could not confirm dry_run=true in config.example.json.",
            "Keep dry_run true unless a separately reviewed paper-execution workflow is explicitly tested.",
        ),
        policy_row(
            created_at,
            "shorting_policy",
            "pass" if allow_shorting_value is False else "blocked_for_review",
            "high",
            f"allow_shorting={format_value(allow_shorting_value)}",
            "config.example.json keeps allow_shorting false." if allow_shorting_value is False else "Could not confirm allow_shorting=false in config.example.json.",
            "Keep shorting disabled unless a separate research-only review supports further work.",
        ),
        max_open_positions_row(created_at, promoted_risk, unique_long_notional),
        max_single_position_notional_row(created_at, promoted_risk, unique_long_notional),
        max_total_desired_notional_row(created_at, promoted_risk, unique_long_notional),
        duplicate_ticker_exposure_row(created_at, promoted_risk, duplicate_tickers),
        strategy_disagreement_row(created_at, promoted_decision, strategy_disagreements),
        execution_approval_row(created_at, promoted_decision, defensive_comparison, deployment_readiness, approved_sources),
        safe_scheduling_row(created_at, deployment_readiness),
        policy_row(
            created_at,
            "kill_switch_policy",
            "not_implemented_future_work",
            "high",
            "future requirement",
            "Paper-only kill switch policy is documented as future risk-management work and is not enforced by this report.",
            "Design and verify a paper-only kill switch separately before any execution discussion.",
        ),
        policy_row(
            created_at,
            "discord_daily_summary_policy",
            "not_implemented_future_work",
            "low",
            "future non-execution summary",
            "Daily summary messaging is a future non-execution reporting idea and is not implemented here.",
            "Design summary-only messaging separately; do not connect it to order approval.",
        ),
    ]
    return rows


def max_open_positions_row(
    created_at: str,
    promoted_risk: list[dict[str, str]],
    unique_long_notional: dict[str, float],
) -> dict[str, Any]:
    if not promoted_risk:
        return policy_row(
            created_at,
            "max_open_positions_policy",
            "insufficient_data",
            "medium",
            f"proposed_limit={DEFAULT_MAX_OPEN_POSITIONS}",
            "Promoted risk preview is missing, so desired long count could not be audited.",
            "Run python bot.py --promoted-risk-preview before revisiting execution discussion.",
        )
    desired_longs = len(unique_long_notional)
    status = "warning" if desired_longs > DEFAULT_MAX_OPEN_POSITIONS else "pass"
    finding = (
        f"Saved promoted risk preview has {desired_longs} unique desired-long ticker(s); "
        f"report-only proposed max_open_positions is {DEFAULT_MAX_OPEN_POSITIONS}."
    )
    return policy_row(
        created_at,
        "max_open_positions_policy",
        status,
        "medium",
        f"desired_longs={desired_longs}; proposed_limit={DEFAULT_MAX_OPEN_POSITIONS}",
        finding,
        "Keep this as report-only until a separately reviewed risk gate is designed and tested.",
    )


def max_single_position_notional_row(
    created_at: str,
    promoted_risk: list[dict[str, str]],
    unique_long_notional: dict[str, float],
) -> dict[str, Any]:
    if not promoted_risk:
        return policy_row(
            created_at,
            "max_single_position_notional_policy",
            "insufficient_data",
            "medium",
            "paper_account_equity=not_read",
            "Promoted risk preview is missing, and this report does not read live account equity.",
            "Run promoted risk preview and define a paper account equity policy before enforcement.",
        )
    if not unique_long_notional:
        return policy_row(
            created_at,
            "max_single_position_notional_policy",
            "insufficient_data",
            "medium",
            "paper_account_equity=not_read",
            "No saved desired-long notional estimates were available; this report does not read live account equity.",
            "Add account-size context in a future reviewed policy before enforcing notional limits.",
        )
    ticker, value = max(unique_long_notional.items(), key=lambda item: item[1])
    return policy_row(
        created_at,
        "max_single_position_notional_policy",
        "warning",
        "medium",
        f"largest_saved_desired_notional={ticker}:{value:.4f}; paper_account_equity=not_read",
        "Largest saved desired notional can be inspected, but no live account equity was read and no limit is enforced.",
        "Define max single-position notional as a reviewed paper-only policy before any execution discussion.",
    )


def max_total_desired_notional_row(
    created_at: str,
    promoted_risk: list[dict[str, str]],
    unique_long_notional: dict[str, float],
) -> dict[str, Any]:
    if not promoted_risk:
        return policy_row(
            created_at,
            "max_total_desired_notional_policy",
            "insufficient_data",
            "medium",
            "estimated_unique_desired_notional=not_available",
            "Promoted risk preview is missing, so total desired notional could not be audited.",
            "Run promoted risk preview before using this policy report.",
        )
    total = sum(unique_long_notional.values())
    return policy_row(
        created_at,
        "max_total_desired_notional_policy",
        "pass" if total == 0 else "warning",
        "medium",
        f"estimated_unique_desired_notional={total:.4f}; paper_account_equity=not_read",
        "Saved unique desired notional was calculated from saved preview CSVs only; no live equity was read and no limit is enforced.",
        "Define max portfolio exposure with paper account equity context before any enforcement work.",
    )


def duplicate_ticker_exposure_row(
    created_at: str,
    promoted_risk: list[dict[str, str]],
    duplicate_tickers: dict[str, int],
) -> dict[str, Any]:
    if not promoted_risk:
        return policy_row(
            created_at,
            "duplicate_ticker_exposure_policy",
            "insufficient_data",
            "medium",
            "duplicate_desired_long_tickers=not_available",
            "Promoted risk preview is missing, so duplicate ticker exposure could not be audited.",
            "Run promoted risk preview and review duplicates before execution discussion.",
        )
    if duplicate_tickers:
        details = ", ".join(f"{ticker}:{count}" for ticker, count in sorted(duplicate_tickers.items()))
        return policy_row(
            created_at,
            "duplicate_ticker_exposure_policy",
            "warning",
            "medium",
            f"duplicate_desired_long_tickers={details}",
            "Multiple promoted strategy rows want the same ticker long in saved previews.",
            "Resolve duplicated exposure policy before any execution discussion.",
        )
    return policy_row(
        created_at,
        "duplicate_ticker_exposure_policy",
        "pass",
        "medium",
        "duplicate_desired_long_tickers=none",
        "No duplicate desired-long ticker exposure was found in saved promoted risk rows.",
        "Keep duplicate exposure review as report-only until a runtime risk gate is designed.",
    )


def strategy_disagreement_row(
    created_at: str,
    promoted_decision: list[dict[str, str]],
    strategy_disagreements: list[str],
) -> dict[str, Any]:
    if not promoted_decision:
        return policy_row(
            created_at,
            "strategy_disagreement_policy",
            "insufficient_data",
            "high",
            "promoted_decision_preview=missing",
            "Promoted decision preview is missing, so strategy disagreement could not be audited.",
            "Run promoted consensus, risk, and decision previews before execution discussion.",
        )
    if strategy_disagreements:
        tickers = ", ".join(sorted(set(strategy_disagreements)))
        return policy_row(
            created_at,
            "strategy_disagreement_policy",
            "blocked_for_review",
            "high",
            f"blocked_strategy_disagreement={tickers}",
            "Saved promoted decision preview has strategy disagreement rows; this blocks execution discussion.",
            "Keep promoted candidates research-only until disagreements are resolved and reviewed.",
        )
    return policy_row(
        created_at,
        "strategy_disagreement_policy",
        "pass",
        "high",
        "blocked_strategy_disagreement=none",
        "No strategy disagreement rows were found in saved promoted decision preview.",
        "Continue requiring decision preview review before execution discussion.",
    )


def execution_approval_row(
    created_at: str,
    promoted_decision: list[dict[str, str]],
    defensive_comparison: list[dict[str, str]],
    deployment_readiness: list[dict[str, str]],
    approved_sources: list[str],
) -> dict[str, Any]:
    inspected_count = sum(bool(rows) for rows in [promoted_decision, defensive_comparison, deployment_readiness])
    if approved_sources:
        return policy_row(
            created_at,
            "execution_approval_policy",
            "blocked_for_review",
            "high",
            "execution_approved_true_sources=" + ", ".join(approved_sources),
            "At least one saved report row has execution_approved=True; manual review is required.",
            "Do not discuss execution until all saved research/report rows are non-approving.",
        )
    if inspected_count == 0:
        return policy_row(
            created_at,
            "execution_approval_policy",
            "insufficient_data",
            "high",
            "execution_approved=not_available",
            "No saved reports with execution_approved fields were available for audit.",
            "Run relevant saved reports before execution discussion.",
        )
    return policy_row(
        created_at,
        "execution_approval_policy",
        "pass",
        "high",
        "execution_approved=False for inspected saved rows",
        "Relevant saved preview/report rows do not approve execution.",
        "Keep execution approval false unless a future explicitly reviewed workflow changes policy.",
    )


def safe_scheduling_row(created_at: str, deployment_readiness: list[dict[str, str]]) -> dict[str, Any]:
    if not deployment_readiness:
        return policy_row(
            created_at,
            "safe_scheduling_policy",
            "insufficient_data",
            "high",
            "deployment_readiness_report=missing",
            "Deployment readiness report is missing, so scheduling policy could not be audited.",
            "Run python bot.py --deployment-readiness-report before scheduling review.",
        )
    checks = {row.get("check_name", ""): row for row in deployment_readiness}
    must_not = checks.get("must_not_schedule_commands_documented")
    if must_not and must_not.get("check_status") == "pass":
        return policy_row(
            created_at,
            "safe_scheduling_policy",
            "pass",
            "high",
            "must_not_schedule_commands_documented=pass",
            "Deployment readiness report documents that execution-capable commands must not be scheduled.",
            "Schedule only manually verified report/display commands, never execution-capable commands.",
        )
    return policy_row(
        created_at,
        "safe_scheduling_policy",
        "warning",
        "high",
        "must_not_schedule_commands_documented=not_confirmed",
        "Could not confirm deployment readiness scheduling safety row is passing.",
        "Review deployment readiness before any scheduler setup.",
    )


def unique_desired_long_notional_by_ticker(rows: list[dict[str, str]]) -> dict[str, float]:
    values: dict[str, float] = {}
    for row in rows:
        if (row.get("desired_position") or "").lower() != "long":
            continue
        ticker = row.get("ticker", "").strip()
        if not ticker:
            continue
        notional = parse_float(row.get("estimated_desired_notional"))
        if notional is None:
            continue
        values[ticker] = max(values.get(ticker, 0.0), notional)
    return values


def duplicate_desired_long_tickers(rows: list[dict[str, str]]) -> dict[str, int]:
    strategies_by_ticker: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if (row.get("desired_position") or "").lower() != "long":
            continue
        ticker = row.get("ticker", "").strip()
        strategy = row.get("strategy_name", "").strip()
        if ticker and strategy:
            strategies_by_ticker[ticker].add(strategy)
    return {
        ticker: len(strategies)
        for ticker, strategies in strategies_by_ticker.items()
        if len(strategies) > 1
    }


def execution_approved_sources(sources: list[tuple[str, list[dict[str, str]]]]) -> list[str]:
    approved: list[str] = []
    for source_name, rows in sources:
        for index, row in enumerate(rows, start=1):
            if is_truthy(row.get("execution_approved")):
                label = row.get("ticker") or row.get("strategy_name") or row.get("check_name") or f"row_{index}"
                approved.append(f"{source_name}:{label}")
    return approved


def policy_row(
    created_at: str,
    risk_policy_name: str,
    risk_policy_status: str,
    risk_level: str,
    current_value_or_limit: str,
    finding: str,
    required_next_step: str,
) -> dict[str, Any]:
    return {
        "created_at": created_at,
        "risk_policy_name": risk_policy_name,
        "risk_policy_status": risk_policy_status,
        "risk_level": risk_level,
        "current_value_or_limit": current_value_or_limit,
        "finding": finding,
        "required_next_step": required_next_step,
        "research_only": True,
        "preview_only": True,
        "execution_approved": False,
    }


def build_portfolio_risk_policy_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    status_counts = Counter(str(row.get("risk_policy_status", "unknown")) for row in rows)
    approved = any(is_truthy(row.get("execution_approved")) for row in rows)
    blocked = [row for row in rows if row.get("risk_policy_status") == "blocked_for_review"]
    lines = [
        "PORTFOLIO RISK POLICY REPORT. RESEARCH ONLY. NOT EXECUTION.",
        "This report documents and inspects policy only. No risk policy was enforced.",
        f"Rows: {len(rows)}",
        "Count by risk_policy_status:",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"  {status}: {count}")
    lines.extend(
        [
            "Current execution approval status: "
            + ("WARNING: at least one output row approved execution." if approved else "False for all rows."),
            "Blocked-for-review reasons:",
        ]
    )
    if blocked:
        for row in blocked:
            lines.append(f"  {row['risk_policy_name']}: {row['finding']}")
    else:
        lines.append("  none")
    lines.extend(
        [
            "No risk policy was enforced and no execution approval was granted.",
            "A blocked result means do not discuss execution yet; it is not a runtime order block.",
            f"Saved portfolio risk policy report to {output_path}",
        ]
    )
    return lines


def write_portfolio_risk_policy_report(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=PORTFOLIO_RISK_POLICY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def show_portfolio_risk_policy_file(input_path: Path) -> tuple[int, list[str]]:
    if not input_path.exists():
        return 1, build_missing_portfolio_risk_policy_lines(input_path)
    return 0, build_show_portfolio_risk_policy_lines(input_path, read_csv_rows(input_path))


def build_missing_portfolio_risk_policy_lines(input_path: Path) -> list[str]:
    return [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/portfolio_risk_policy_report.csv and does not refresh data, read positions, enforce risk, or submit orders.",
        f"Missing portfolio risk policy report file: {input_path}",
        "Run this first:",
        "python bot.py --portfolio-risk-policy-report",
        "Then rerun: python bot.py --show-portfolio-risk-policy",
        "No risk policy was enforced by this display command.",
    ]


def build_show_portfolio_risk_policy_lines(input_path: Path, rows: list[dict[str, str]]) -> list[str]:
    status_counts = Counter(row.get("risk_policy_status", "") or "blank" for row in rows)
    level_counts = Counter(row.get("risk_level", "") or "blank" for row in rows)
    blocked = [row for row in rows if row.get("risk_policy_status") == "blocked_for_review"]
    future_work = [row for row in rows if row.get("risk_policy_status") == "not_implemented_future_work"]
    has_execution_approved = any(is_truthy(row.get("execution_approved", "")) for row in rows)
    final_line = (
        "WARNING: at least one row has execution_approved=True; manual review required."
        if has_execution_approved
        else "Execution approved: False for all rows."
    )
    return [
        "READ-ONLY DISPLAY. NOT EXECUTION.",
        "This command only reads data/portfolio_risk_policy_report.csv and does not refresh data, read positions, enforce risk, or submit orders.",
        f"Input file: {input_path}",
        f"Rows: {len(rows)}",
        "",
        "Count by risk_policy_status:",
        *_format_display_counts(status_counts),
        "",
        "Count by risk_level:",
        *_format_display_counts(level_counts),
        "",
        "Blocked-for-review rows:",
        *_format_policy_list(blocked),
        "",
        "Future-work rows:",
        *_format_policy_list(future_work),
        "",
        *_format_portfolio_risk_policy_table(rows),
        "",
        final_line,
        "No risk policy was enforced by this display command.",
    ]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def nested_value(data: dict[str, Any], keys: list[str]) -> Any:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def parse_float(value: object) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(str(value))
    except ValueError:
        return None


def is_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def format_value(value: object) -> str:
    if value is None:
        return "not_available"
    return str(value)


def _format_display_counts(counts: Counter[str]) -> list[str]:
    if not counts:
        return ["- none"]
    return [f"- {name}: {count}" for name, count in sorted(counts.items())]


def _format_policy_list(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["- none"]
    return [
        f"- {row.get('risk_policy_name', '')}: {row.get('finding', '')}"
        for row in rows
    ]


def _format_portfolio_risk_policy_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["No portfolio risk policy rows found."]
    display_rows = [
        {
            column: _truncate(str(row.get(column, "")), _column_width(column))
            for column in PORTFOLIO_RISK_POLICY_DISPLAY_COLUMNS
        }
        for row in rows
    ]
    widths = {
        column: min(
            _column_width(column),
            max(len(column), *(len(row[column]) for row in display_rows)),
        )
        for column in PORTFOLIO_RISK_POLICY_DISPLAY_COLUMNS
    }
    header = " | ".join(column.ljust(widths[column]) for column in PORTFOLIO_RISK_POLICY_DISPLAY_COLUMNS)
    separator = "-+-".join("-" * widths[column] for column in PORTFOLIO_RISK_POLICY_DISPLAY_COLUMNS)
    lines = [header, separator]
    for row in display_rows:
        lines.append(" | ".join(row[column].ljust(widths[column]) for column in PORTFOLIO_RISK_POLICY_DISPLAY_COLUMNS))
    return lines


def _column_width(column: str) -> int:
    widths = {
        "risk_policy_name": 36,
        "risk_policy_status": 28,
        "risk_level": 12,
        "current_value_or_limit": 42,
        "finding": 68,
        "required_next_step": 68,
        "execution_approved": 18,
    }
    return widths.get(column, 20)


def _truncate(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return f"{value[: width - 3]}..."
