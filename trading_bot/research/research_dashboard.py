"""Static saved-CSV research dashboard builder."""

from __future__ import annotations

import csv
import html
import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DASHBOARD_INPUTS = {
    "research_report": ("data/research_report.csv", "python bot.py --research-report"),
    "walk_forward_report": ("data/walk_forward_report.csv", "python bot.py --walk-forward-report"),
    "defensive_candidate_comparison": (
        "data/defensive_candidate_comparison.csv",
        "python bot.py --defensive-candidate-comparison",
    ),
    "etf_defensive_drawdown_comparison": (
        "data/etf_defensive_drawdown_comparison.csv",
        "python bot.py --etf-defensive-drawdown-comparison",
    ),
    "portfolio_risk_policy_report": (
        "data/portfolio_risk_policy_report.csv",
        "python bot.py --portfolio-risk-policy-report",
    ),
    "execution_eligibility_report": (
        "data/execution_eligibility_report.csv",
        "python bot.py --execution-eligibility-report",
    ),
    "promoted_decision_preview": (
        "data/promoted_decision_preview.csv",
        "python bot.py --refresh-promoted-review",
    ),
    "crypto_research_state_report": (
        "data/crypto_research_state_report.csv",
        "python bot.py --crypto-research-state-report",
    ),
    "deployment_readiness_report": (
        "data/deployment_readiness_report.csv",
        "python bot.py --deployment-readiness-report",
    ),
    "paper_kill_switch_readiness_report": (
        "data/paper_kill_switch_readiness_report.csv",
        "python bot.py --paper-kill-switch-readiness-report",
    ),
}

OPTIONAL_DASHBOARD_INPUTS = {
    "defensive_research_state_report": (
        "data/defensive_research_state_report.csv",
        "python bot.py --defensive-research-state-report",
    ),
    "etf_breadth_regime_backtest": (
        "data/etf_breadth_regime_backtest.csv",
        "python bot.py --etf-breadth-regime-backtest",
    ),
    "etf_breadth_regime_summary": (
        "data/etf_breadth_regime_summary.csv",
        "python bot.py --etf-breadth-regime-backtest",
    ),
    "etf_breadth_regime_decision_report": (
        "data/etf_breadth_regime_decision_report.csv",
        "python bot.py --etf-breadth-regime-decision-report",
    ),
    "paper_execution_protection_report": (
        "data/paper_execution_protection_report.csv",
        "python bot.py --paper-execution-protection-report",
    ),
    "normal_bot_execution_policy_report": (
        "data/normal_bot_execution_policy_report.csv",
        "python bot.py --normal-bot-execution-policy-report",
    ),
}

CHART_INPUTS = [
    "data/charts/etf_defensive_equity_comparison.png",
    "data/charts/etf_defensive_drawdown_comparison.png",
]


@dataclass
class ResearchDashboardResult:
    output_path: Path
    missing_inputs: list[tuple[str, str]]
    summary_lines: list[str]


def build_research_dashboard(
    root_dir: Path | str = ".",
    output_filename: str = "data/dashboard/research_dashboard.html",
) -> ResearchDashboardResult:
    root = Path(root_dir)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = read_dashboard_inputs(root)
    missing_inputs = missing_dashboard_inputs(data)
    output_path = root / output_filename
    html_text = build_dashboard_html(root, output_path, data, missing_inputs, created_at)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    return ResearchDashboardResult(
        output_path=output_path,
        missing_inputs=missing_inputs,
        summary_lines=[
            "RESEARCH DASHBOARD. STATIC SAVED-CSV DISPLAY ONLY. NOT EXECUTION.",
            f"Saved research dashboard to {output_path}",
            f"Missing saved CSV inputs: {len(missing_inputs)}",
            "No localhost server was started. No execution approval was granted.",
        ],
    )


def read_dashboard_inputs(root: Path) -> dict[str, dict[str, Any]]:
    data: dict[str, dict[str, Any]] = {}
    for name, (relative_path, command) in DASHBOARD_INPUTS.items():
        path = root / relative_path
        data[name] = {
            "path": path,
            "relative_path": relative_path,
            "command": command,
            "rows": read_csv_rows(path),
            "exists": path.exists(),
        }
    for name, (relative_path, command) in OPTIONAL_DASHBOARD_INPUTS.items():
        path = root / relative_path
        data[name] = {
            "path": path,
            "relative_path": relative_path,
            "command": command,
            "rows": read_csv_rows(path),
            "exists": path.exists(),
        }
    return data


def build_dashboard_html(
    root: Path,
    output_path: Path,
    data: dict[str, dict[str, Any]],
    missing_inputs: list[tuple[str, str]],
    created_at: str,
) -> str:
    cards = dashboard_cards(data)
    sections = [
        render_header(created_at),
        render_cards(cards),
        render_meaning(data),
        render_next_commands(),
        render_execution_safety_state(data),
        render_defensive_research_state(data),
        render_defensive_comparison(data),
        render_etf_breadth_regime(data),
        render_promoted_decisions(data),
        render_portfolio_risk_and_eligibility(data),
        render_drawdown_comparison(root, output_path, data),
        render_crypto_state(data),
        render_missing_inputs(missing_inputs),
    ]
    return "<!doctype html>\n" + tag(
        "html",
        tag("head", tag("meta", "", charset="utf-8") + tag("title", "Research Dashboard") + tag("style", CSS))
        + tag("body", "\n".join(sections)),
        lang="en",
    )


def dashboard_cards(data: dict[str, dict[str, Any]]) -> list[tuple[str, str, str, str]]:
    eligibility_rows = data["execution_eligibility_report"]["rows"]
    defensive_rows = data["defensive_candidate_comparison"]["rows"]
    promoted_rows = data["promoted_decision_preview"]["rows"]
    kill_switch_rows = data["paper_kill_switch_readiness_report"]["rows"]

    preferred = first_value(defensive_rows, "comparison_status", "preferred_defensive_candidate", "strategy_name")
    blockers = sorted(
        {
            row.get("ticker", "")
            for row in promoted_rows
            if row.get("decision_state") == "blocked_strategy_disagreement" and row.get("ticker")
        }
    )
    eligible = "False"
    final = first_row(eligibility_rows, "eligibility_check_name", "final_execution_eligibility")
    if final and final.get("eligibility_status") == "eligible_for_discussion":
        eligible = "False; discussion only"
    kill_switch_status = first_matching_status(
        kill_switch_rows,
        "check_status",
        {"not_implemented_future_work", "not_ready", "warning", "blocked_for_review"},
    ) or status_summary(kill_switch_rows, "check_status") or "not available"
    missing_count = str(len(missing_dashboard_inputs(data)))
    return [
        ("Execution eligible", eligible, "BLOCKED", "danger"),
        ("Main blocker", blocker_text(blockers), "BLOCKED" if blockers else "PASS", "danger" if blockers else "ok"),
        ("Preferred defensive candidate", preferred or "not available", "RESEARCH", "neutral"),
        ("Kill-switch status", kill_switch_status, "FUTURE WORK", "warn"),
        ("Missing inputs", missing_count, "PASS" if missing_count == "0" else "WARNING", "ok" if missing_count == "0" else "warn"),
    ]


def render_header(created_at: str) -> str:
    return tag(
        "header",
        tag("div", tag("span", "STATIC SAVED-CSV DISPLAY ONLY", class_="eyebrow") + tag("h1", "RESEARCH DASHBOARD"), class_="title-block")
        + tag("div", "No execution approval. No orders. No Alpaca calls. No market-data refresh.", class_="safety-strip danger")
        + tag("p", f"Generated at {escape(created_at)}.", class_="meta")
        + tag("p", "No localhost server was started. No execution approval was granted.", class_="meta")
        + tag("p", "This static file reads saved CSVs only. It does not start a server, refresh market data, call Alpaca, submit orders, write trade_log rows, send Discord alerts, enforce risk, or approve execution.", class_="meta"),
        class_="hero",
    )


def render_cards(cards: list[tuple[str, str, str, str]]) -> str:
    body = "".join(
        tag(
            "div",
            tag("div", escape(status), class_=f"badge {css_class}")
            + tag("h3", escape(title))
            + tag("p", escape(value)),
            class_=f"card {css_class}",
        )
        for title, value, status, css_class in cards
    )
    return section("Executive Status", tag("div", body, class_="cards"))


def render_meaning(data: dict[str, dict[str, Any]]) -> str:
    promoted_rows = data["promoted_decision_preview"]["rows"]
    blockers = sorted(
        {
            row.get("ticker", "")
            for row in promoted_rows
            if row.get("decision_state") == "blocked_strategy_disagreement" and row.get("ticker")
        }
    )
    flat = sorted(
        {
            row.get("ticker", "")
            for row in promoted_rows
            if row.get("decision_state") == "no_action_unanimous_flat" and row.get("ticker")
        }
    )
    items = [
        "No execution is approved.",
        f"{', '.join(blockers) if blockers else 'No promoted tickers'} are blocked by strategy disagreement.",
        f"{', '.join(flat) if flat else 'No promoted tickers'} are no-action/flat.",
        "Kill switch checks are readiness-only; no runtime kill switch enforcement is enabled by this dashboard.",
        "The dashboard reads saved CSVs only and does not refresh market data or read positions.",
    ]
    return section("What This Means", tag("ul", "".join(tag("li", escape(item)) for item in items), class_="meaning-list"))


def render_next_commands() -> str:
    commands = [
        "python bot.py --refresh-promoted-review",
        "python bot.py --portfolio-risk-policy-report",
        "python bot.py --paper-kill-switch-readiness-report",
        "python bot.py --deployment-readiness-report",
        "python bot.py --execution-eligibility-report",
        "python bot.py --build-research-dashboard",
    ]
    return section(
        "Next Useful Commands",
        tag("div", "".join(tag("code", escape(command)) for command in commands), class_="command-grid"),
    )


def render_execution_safety_state(data: dict[str, dict[str, Any]]) -> str:
    protection_rows = data["paper_execution_protection_report"]["rows"]
    policy_rows = data["normal_bot_execution_policy_report"]["rows"]
    body = tag(
        "p",
        "Static saved-CSV display only. No execution approval, no order actions, and normal bot remains separate from defensive paper execution.",
        class_="safety-strip danger",
    )
    body += tag("p", "Optional section: missing safety CSVs do not block dashboard generation.", class_="meta")
    body += tag("h3", "Paper Execution Protection")
    body += render_table(
        protection_rows,
        [
            "execution_path",
            "protection_status",
            "finding",
            "currently_blocks_execution",
            "required_next_step",
            "execution_approved",
        ],
    )
    body += tag("h3", "Normal Bot Execution Policy")
    body += render_table(
        policy_rows,
        [
            "policy_area",
            "policy_status",
            "finding",
            "required_next_step",
            "execution_approved",
        ],
    )
    return section("Execution Safety State", body)


def render_defensive_comparison(data: dict[str, dict[str, Any]]) -> str:
    rows = [
        row for row in data["defensive_candidate_comparison"]["rows"]
        if row.get("strategy_name") in {
            "monthly_etf_momentum_rotation",
            "volatility_managed_dual_momentum_etf",
            "adaptive_risk_on_off_momentum",
        }
    ]
    columns = [
        "strategy_name",
        "policy_rank",
        "metric_rank",
        "comparison_status",
        "out_of_sample_sharpe",
        "out_of_sample_calmar",
        "out_of_sample_max_drawdown_pct",
        "comparison_reason",
    ]
    return section("Defensive Strategy Comparison", render_table(rows, columns))


def render_defensive_research_state(data: dict[str, dict[str, Any]]) -> str:
    rows = data["defensive_research_state_report"]["rows"]
    columns = [
        "component",
        "category",
        "state_label",
        "headline_metric",
        "headline_value",
        "interpretation",
        "required_next_step",
        "execution_approved",
    ]
    body = tag("p", "Saved-data only. Research/display only. No execution approval.")
    if rows and any(column not in rows[0] for column in columns):
        body += tag(
            "p",
            "Optional defensive research state CSV is present but does not include all expected display columns.",
            class_="muted",
        )
    body += render_table(rows, columns)
    return section("Defensive Research State", body)


def render_etf_breadth_regime(data: dict[str, dict[str, Any]]) -> str:
    result_rows = data["etf_breadth_regime_backtest"]["rows"]
    summary_rows = data["etf_breadth_regime_summary"]["rows"]
    decision_rows = data["etf_breadth_regime_decision_report"]["rows"]
    headline_columns = [
        "period",
        "cagr_pct",
        "sharpe_ratio",
        "max_drawdown_pct",
        "calmar_ratio",
        "exposure_pct",
        "robustness_status",
    ]
    regime_columns = ["regime", "pct_of_days", "average_breadth_pct"]
    decision_columns = ["decision_label", "comparison_status", "finding", "required_next_step"]
    body = tag("p", "ETF breadth regime is research-only. It is not promoted and does not approve execution.")
    body += tag("h3", "Headline metrics")
    body += render_table(result_rows, headline_columns)
    body += tag("h3", "Time in regimes")
    body += render_table(summary_rows, regime_columns)
    body += tag("h3", "Decision")
    body += render_table(decision_rows[:3], decision_columns)
    return section("ETF Breadth Regime", body)


def render_drawdown_comparison(root: Path, output_path: Path, data: dict[str, dict[str, Any]]) -> str:
    rows = data["etf_defensive_drawdown_comparison"]["rows"]
    columns = [
        "comparison_period",
        "strategy_name",
        "drawdown_depth_pct",
        "matching_other_strategy_drawdown_pct",
        "drawdown_advantage_pct",
        "split_80_20_oos_calmar",
        "interpretation_label",
        "interpretation_reason",
    ]
    charts = []
    for relative_path in CHART_INPUTS:
        path = root / relative_path
        if path.exists():
            src = Path(os.path.relpath(path, output_path.parent)).as_posix()
            charts.append(tag("figure", tag("img", "", src=src, alt=Path(relative_path).name) + tag("figcaption", escape(relative_path))))
    return section("Drawdown Comparison", render_table(rows, columns) + "".join(charts))


def render_promoted_decisions(data: dict[str, dict[str, Any]]) -> str:
    rows = data["promoted_decision_preview"]["rows"]
    columns = [
        "ticker",
        "decision_state",
        "reason",
        "execution_approved",
        "consensus_state",
        "long_votes",
        "flat_votes",
    ]
    return section("Promoted Strategy Decision", render_table(rows, columns))


def render_portfolio_risk_and_eligibility(data: dict[str, dict[str, Any]]) -> str:
    risk_rows = data["portfolio_risk_policy_report"]["rows"]
    eligibility_rows = data["execution_eligibility_report"]["rows"]
    risk_counts = status_summary(risk_rows, "risk_policy_status")
    eligibility_counts = status_summary(eligibility_rows, "eligibility_status")
    blockers = [
        row for row in eligibility_rows
        if row.get("eligibility_status") in {"blocked_for_review", "not_ready", "missing_input"}
    ]
    future = [
        row for row in risk_rows
        if row.get("risk_policy_status") == "not_implemented_future_work"
    ]
    body = tag("p", "Risk policy status counts: " + escape(risk_counts or "not available"))
    body += tag("p", "Eligibility status counts: " + escape(eligibility_counts or "not available"))
    body += tag("h3", "Eligibility blockers")
    body += render_table(blockers, ["eligibility_check_name", "eligibility_status", "blocking_reason", "finding", "required_next_step"])
    body += tag("h3", "Risk policy rows")
    body += render_table(risk_rows, ["risk_policy_name", "risk_policy_status", "risk_level", "finding", "required_next_step", "execution_approved"])
    body += tag("h3", "Future-work items")
    body += render_table(future, ["risk_policy_name", "risk_policy_status", "finding", "required_next_step"])
    return section("Portfolio Risk / Execution Eligibility", body)


def render_crypto_state(data: dict[str, dict[str, Any]]) -> str:
    rows = data["crypto_research_state_report"]["rows"]
    columns = [
        "symbol",
        "best_research_candidate",
        "decision_status",
        "current_desired_position",
        "current_signal_reason",
        "research_conclusion",
        "next_research_step",
        "execution_approved",
    ]
    body = tag("p", "Crypto remains research/monitoring only. Crypto execution is disabled.")
    return section("Crypto Monitor / Research State", body + render_table(rows, columns))


def render_missing_inputs(missing_inputs: list[tuple[str, str]]) -> str:
    if not missing_inputs:
        return section("Missing Inputs", tag("p", "No required saved CSV inputs are missing."))
    rows = [{"missing_csv": path, "command": command} for path, command in missing_inputs]
    return section("Missing Inputs", render_table(rows, ["missing_csv", "command"]))


def render_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return tag("p", "No saved rows available.", class_="muted")
    header = tag("tr", "".join(tag("th", escape(column)) for column in columns))
    body = "".join(
        tag(
            "tr",
            "".join(tag("td", escape(str(row.get(column, ""))), class_=cell_class(str(row.get(column, "")))) for column in columns),
        )
        for row in rows
    )
    return tag("div", tag("table", tag("thead", header) + tag("tbody", body)), class_="table-wrap")


def missing_dashboard_inputs(data: dict[str, dict[str, Any]]) -> list[tuple[str, str]]:
    required_paths = {relative_path for relative_path, _ in DASHBOARD_INPUTS.values()}
    return [
        (entry["relative_path"], entry["command"])
        for entry in data.values()
        if not entry["exists"] and entry["relative_path"] in required_paths
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def first_value(rows: list[dict[str, str]], key: str, expected: str, value_key: str) -> str:
    row = first_row(rows, key, expected)
    return row.get(value_key, "") if row else ""


def first_row(rows: list[dict[str, str]], key: str, expected: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == expected:
            return row
    return None


def status_summary(rows: list[dict[str, str]], status_column: str) -> str:
    counts = Counter(row.get(status_column, "") or "blank" for row in rows)
    if not counts:
        return ""
    return ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))


def first_matching_status(rows: list[dict[str, str]], status_column: str, statuses: set[str]) -> str:
    for row in rows:
        status = row.get(status_column, "")
        if status in statuses:
            return status
    return ""


def blocker_text(blockers: list[str]) -> str:
    if not blockers:
        return "none or not available"
    if blockers == ["AAPL", "SPY"]:
        return "AAPL/SPY strategy disagreement"
    return f"{', '.join(blockers)} strategy disagreement"


def crypto_summary(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "not available"
    parts = []
    for row in rows:
        symbol = row.get("symbol", "")
        conclusion = row.get("research_conclusion") or row.get("decision_status") or "unknown"
        desired = row.get("current_desired_position") or "unknown"
        if symbol:
            parts.append(f"{symbol}: {conclusion}; {desired}")
    return " | ".join(parts) if parts else "not available"


def section(title: str, body: str) -> str:
    return tag("section", tag("h2", escape(title)) + body)


def tag(name: str, content: str, **attrs: str) -> str:
    attr_text = "".join(
        f' {html.escape(key.rstrip("_").replace("_", "-"))}="{html.escape(value, quote=True)}"'
        for key, value in attrs.items()
        if value is not None
    )
    return f"<{name}{attr_text}>{content}</{name}>"


def escape(value: str) -> str:
    return html.escape(value, quote=True)


def cell_class(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in ["blocked", "false", "not_ready", "not useful"]):
        return "cell danger"
    if any(token in lowered for token in ["warning", "future", "split-sensitive", "promising"]):
        return "cell warn"
    if any(token in lowered for token in ["pass", "preferred", "false for all rows"]):
        return "cell ok"
    return "cell"


CSS = """
:root {
  --bg: #f4f7fb;
  --panel: #ffffff;
  --ink: #172033;
  --muted: #667085;
  --line: #d8dee8;
  --red: #b42318;
  --red-bg: #fff1f0;
  --amber: #b54708;
  --amber-bg: #fffaeb;
  --green: #087443;
  --green-bg: #ecfdf3;
  --blue: #175cd3;
  --blue-bg: #eff6ff;
  --head: #26364d;
}
* { box-sizing: border-box; }
body { font-family: Arial, sans-serif; margin: 0; color: var(--ink); background: var(--bg); line-height: 1.45; }
.hero {
  position: sticky;
  top: 0;
  z-index: 10;
  max-width: 1320px;
  margin: 0 auto 18px;
  padding: 20px 24px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
  box-shadow: 0 8px 24px rgba(16, 24, 40, 0.08);
}
.title-block { display: flex; align-items: baseline; justify-content: space-between; gap: 18px; flex-wrap: wrap; }
.eyebrow { color: var(--blue); font-size: 0.78rem; font-weight: 800; letter-spacing: 0; }
h1 { margin: 0; font-size: 2.05rem; letter-spacing: 0; }
h2 { margin: 0 0 12px; font-size: 1.25rem; }
h3 { margin: 16px 0 8px; font-size: 1rem; }
section { margin: 18px auto; max-width: 1320px; background: var(--panel); padding: 20px; border: 1px solid var(--line); border-radius: 8px; }
.safety-strip { margin: 14px 0 10px; padding: 12px 14px; border-radius: 6px; font-weight: 800; }
.meta { margin: 4px 0; color: var(--muted); }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }
.card { min-height: 128px; border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #f9fbfd; }
.card h3 { margin: 10px 0 6px; color: #344054; }
.card p { margin: 0; font-size: 1.05rem; font-weight: 800; overflow-wrap: anywhere; }
.badge { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 0.72rem; font-weight: 800; border: 1px solid currentColor; }
.ok { border-left: 5px solid var(--green); }
.warn { border-left: 5px solid var(--amber); }
.danger { border-left: 5px solid var(--red); }
.neutral { border-left: 5px solid var(--blue); }
.badge.ok, .cell.ok { color: var(--green); background: var(--green-bg); }
.badge.warn, .cell.warn { color: var(--amber); background: var(--amber-bg); }
.badge.danger, .cell.danger { color: var(--red); background: var(--red-bg); }
.badge.neutral { color: var(--blue); background: var(--blue-bg); }
.meaning-list { display: grid; gap: 8px; margin: 0; padding-left: 22px; }
.command-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 8px; }
code { display: block; padding: 8px 10px; border: 1px solid var(--line); border-radius: 6px; background: #f8fafc; color: #253858; overflow-wrap: anywhere; }
.table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; margin: 12px 0; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; min-width: 980px; }
th, td { border-bottom: 1px solid var(--line); padding: 8px 9px; vertical-align: top; overflow-wrap: anywhere; font-size: 0.88rem; }
th { position: sticky; top: 0; background: var(--head); color: #fff; text-align: left; font-weight: 800; }
tbody tr:nth-child(even) { background: #f8fafc; }
tbody tr:hover { background: #eef4ff; }
td { max-height: 6.5rem; }
.muted { color: var(--muted); }
figure { margin: 16px 0; }
img { max-width: 100%; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
figcaption { color: var(--muted); font-size: 0.9rem; }
"""
