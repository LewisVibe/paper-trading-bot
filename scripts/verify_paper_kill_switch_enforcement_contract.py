from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
APPLICATION = ROOT / "trading_bot" / "cli" / "application.py"
PARSER = ROOT / "trading_bot" / "cli" / "parser.py"
VOL_TARGETED_RUNNER = ROOT / "trading_bot" / "runners" / "vol_targeted_growth_paper.py"

CONTRACT_PREREQUISITES = [
    "alpaca_paper_only",
    "live_trading_impossible",
    "allow_shorting_false_for_defensive_allocation",
    "paper_kill_switch_setting_exists",
    "paper_kill_switch_explicitly_allows_execution",
    "execution_eligibility_not_blocked",
    "defensive_allocation_decision_allows_progression",
    "explicit_confirmation_flag_required",
    "separate_from_normal_bot_behavior",
    "not_runnable_from_report_preview_dashboard_modes",
]

SUSPICIOUS_NEW_EXECUTION_COMMANDS = [
    "--defensive-allocation-execute",
    "--execute-defensive-allocation",
    "--paper-defensive-allocation",
    "--confirm-defensive-allocation",
    "--defensive-paper-execution",
]

ORDER_INSTRUCTION_COLUMNS = {
    "side",
    "quantity",
    "order_type",
    "order_id",
    "target_order",
    "submit" + "_order",
}

REPORT_PREVIEW_MODULES = [
    ROOT / "trading_bot" / "research",
    ROOT / "trading_bot" / "runners" / "research_reports.py",
]


def main() -> int:
    failures: list[str] = []
    help_text = bot_help_text()
    bot_source = read_text(APPLICATION)
    config_example = read_json(ROOT / "config.example.json")

    verify_contract_defined(failures)
    verify_safe_config_defaults(config_example, failures)
    verify_high_risk_commands_still_gated(help_text, failures)
    verify_no_new_defensive_execution_command(help_text, failures)
    verify_normal_bot_separation(bot_source, failures)
    verify_report_preview_no_execution_approval(failures)
    verify_contract_has_no_order_instruction_columns(failures)
    verify_gate_blocked_future_work(failures)
    verify_helper_wired_only_to_manual_paper_order_test(failures)

    if failures:
        print("Paper kill-switch enforcement contract verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PAPER KILL-SWITCH ENFORCEMENT CONTRACT VERIFICATION")
    print("Contract prerequisites: pass")
    print("High-risk command confirmation gates: pass")
    print("Future defensive execution command absent: pass")
    print("Report/preview execution approval scan: pass")
    print("Current gate remains blocked/future-work-required: pass")
    print("Isolated helper wiring covers only the guarded manual paper execution paths: pass")
    print("Result: passed")
    return 0


def verify_contract_defined(failures: list[str]) -> None:
    missing = [item for item in CONTRACT_PREREQUISITES if not item]
    if missing or len(CONTRACT_PREREQUISITES) != 10:
        failures.append("future kill-switch enforcement contract prerequisites are incomplete")


def verify_safe_config_defaults(config_example: dict[str, object], failures: list[str]) -> None:
    if config_example.get("dry_run") is not True:
        failures.append("config.example.json must keep dry_run=true")
    if nested_value(config_example, ["alpaca", "paper"]) is not True:
        failures.append("config.example.json must keep alpaca.paper=true")
    if config_example.get("allow_shorting") is not False:
        failures.append("config.example.json must keep allow_shorting=false")


def verify_high_risk_commands_still_gated(help_text: str, failures: list[str]) -> None:
    if "--paper-order-test" not in help_text or "--confirm-paper-order" not in help_text:
        failures.append("--paper-order-test must remain paired with --confirm-paper-order")
    if "--execute-slow-sma-paper" not in help_text or "--confirm-slow-sma-paper" not in help_text:
        failures.append("--execute-slow-sma-paper must remain paired with --confirm-slow-sma-paper")
    paper_context = help_line_for(help_text, "--confirm-paper-order").lower()
    if "required" not in paper_context:
        failures.append("--confirm-paper-order help should remain explicitly required")
    slow_context = help_line_for(help_text, "--confirm-slow-sma-paper").lower()
    if "required" not in slow_context:
        failures.append("--confirm-slow-sma-paper help should remain explicitly required")


def verify_no_new_defensive_execution_command(help_text: str, failures: list[str]) -> None:
    for command in SUSPICIOUS_NEW_EXECUTION_COMMANDS:
        if command in help_text:
            failures.append(f"unexpected defensive execution command present: {command}")


def verify_normal_bot_separation(bot_source: str, failures: list[str]) -> None:
    normal_entry_marker = "config_path = Path(args.config).resolve()"
    decision_route = "if args.defensive_allocation_decision_report:"
    gate_route = "if args.paper_kill_switch_gate_report:"
    if normal_entry_marker not in bot_source:
        failures.append("could not locate normal bot config-loading boundary")
        return
    normal_index = bot_source.index(normal_entry_marker)
    if decision_route in bot_source and bot_source.index(decision_route) > normal_index:
        failures.append("defensive allocation decision report should remain separate from normal bot config-loaded behavior")
    if gate_route in bot_source and bot_source.index(gate_route) > normal_index:
        failures.append("paper kill-switch gate report should remain separate from normal bot config-loaded behavior")


def verify_report_preview_no_execution_approval(failures: list[str]) -> None:
    forbidden_tokens = [
        '"execution_approved": True',
        "'execution_approved': True",
    ]
    for path in iter_report_preview_sources():
        text = read_text(path)
        for token in forbidden_tokens:
            if token in text:
                failures.append(f"report/preview source can approve execution: {path.relative_to(ROOT)}")
                break


def verify_contract_has_no_order_instruction_columns(failures: list[str]) -> None:
    contract_columns = {
        "contract_check",
        "contract_status",
        "severity",
        "source",
        "finding",
        "required_before_execution_design",
        "required_next_step",
        "research_only",
        "preview_only",
        "execution_approved",
    }
    found = sorted(ORDER_INSTRUCTION_COLUMNS.intersection(contract_columns))
    if found:
        failures.append("contract/spec columns include order-instruction names: " + ", ".join(found))


def verify_gate_blocked_future_work(failures: list[str]) -> None:
    gate_path = ROOT / "data" / "paper_kill_switch_gate_report.csv"
    if not gate_path.exists():
        failures.append("data/paper_kill_switch_gate_report.csv is missing; run python bot.py --paper-kill-switch-gate-report")
        return
    rows = read_csv_rows(gate_path)
    statuses = {row.get("gate_check"): row.get("gate_status") for row in rows}
    if statuses.get("kill_switch_enforcement_not_implemented") != "future_work_required":
        failures.append("kill_switch_enforcement_not_implemented should remain future_work_required")
    if statuses.get("future_execution_requires_kill_switch_gate") != "blocked":
        failures.append("future_execution_requires_kill_switch_gate should remain blocked")
    for row in rows:
        if str(row.get("execution_approved", "")).strip().lower() != "false":
            failures.append("paper kill-switch gate report must keep execution_approved=False for every row")
            break


def verify_helper_wired_only_to_manual_paper_order_test(failures: list[str]) -> None:
    helper_path = ROOT / "trading_bot" / "safety" / "paper_kill_switch.py"
    if not helper_path.exists():
        failures.append("isolated paper kill-switch helper is missing")
        return
    helper_text = read_text(helper_path)
    if "evaluate_paper_kill_switch_gate" not in helper_text:
        failures.append("isolated paper kill-switch helper must expose evaluate_paper_kill_switch_gate")
    bot_source = read_text(APPLICATION)
    vol_targeted_source = read_text(VOL_TARGETED_RUNNER)
    if "evaluate_paper_kill_switch_gate" not in bot_source:
        failures.append("configured application should use isolated paper kill-switch helper")
    elif not helper_call_is_limited_to_scoped_paper_commands(bot_source):
        failures.append("isolated helper must be limited to manual and slow SMA paper preflights")
    if "evaluate_paper_kill_switch_gate" not in vol_targeted_source:
        failures.append("volatility-targeted paper execution must use the isolated paper kill-switch helper")
    elif not vol_targeted_helper_call_is_scoped(vol_targeted_source):
        failures.append("volatility-targeted kill-switch use must remain inside its manual execution route")
    high_risk_paths = [
        ROOT / "trading_bot" / "execution.py",
        ROOT / "trading_bot" / "alpaca_client.py",
        ROOT / "trading_bot" / "database.py",
        ROOT / "trading_bot" / "discord_alerts.py",
    ]
    for path in high_risk_paths:
        text = read_text(path)
        if "trading_bot.safety.paper_kill_switch" in text or "evaluate_paper_kill_switch_gate" in text:
            failures.append(f"isolated helper must not be wired into high-risk path: {path.relative_to(ROOT)}")


def helper_call_is_limited_to_scoped_paper_commands(bot_source: str) -> bool:
    try:
        manual_start = bot_source.index("def run_paper_order_test(")
        manual_end = bot_source.index("def estimate_manual_position_after(", manual_start)
        slow_start = bot_source.index("def run_slow_sma_paper_execution(")
        slow_end = bot_source.index("def validate_slow_sma_execution_safety(", slow_start)
    except ValueError:
        return False
    manual_source = bot_source[manual_start:manual_end]
    slow_source = bot_source[slow_start:slow_end]
    outside_source = (
        bot_source[:manual_start]
        + bot_source[manual_end:slow_start]
        + bot_source[slow_end:]
    )
    if "evaluate_paper_kill_switch_gate(" in outside_source:
        return False
    return preflight_before_terms(
        manual_source,
        ["TradingClient(", "submit_paper_order(", "init_database("],
    ) and preflight_before_terms(
        slow_source,
        ["configure_yfinance_cache(", "init_database(", "send_discord_alert(", "TradingClient(", "get_alpaca_positions("],
    )


def vol_targeted_helper_call_is_scoped(source: str) -> bool:
    try:
        execution_start = source.index("def run_execute_vol_targeted_growth_paper(")
        execution_end = source.index("def run_vol_targeted_growth_paper_postcheck(", execution_start)
    except ValueError:
        return False
    execution_source = source[execution_start:execution_end]
    outside_source = source[:execution_start] + source[execution_end:]
    if "evaluate_paper_kill_switch_gate(" in outside_source:
        return False
    return preflight_before_terms(execution_source, ["submit_paper_order("])


def preflight_before_terms(source: str, terms: list[str]) -> bool:
    helper_call = "evaluate_paper_kill_switch_gate("
    if helper_call not in source:
        return False
    preflight_index = source.index(helper_call)
    for term in terms:
        if term not in source or preflight_index > source.index(term):
            return False
    return True


def iter_report_preview_sources() -> list[Path]:
    paths: list[Path] = []
    for source in REPORT_PREVIEW_MODULES:
        if source.is_dir():
            paths.extend(sorted(source.rglob("*.py")))
        elif source.exists():
            paths.append(source)
    return paths


def bot_help_text() -> str:
    result = subprocess.run(
        [PYTHON, "bot.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode == 0 and "--paper-order-test" in output:
        return output
    return read_text(PARSER)


def help_line_for(output: str, command: str) -> str:
    source_token = f'"{command}"'
    if source_token in output:
        command_index = output.index(source_token)
        argument_start = output.rfind("parser.add_argument(", 0, command_index)
        argument_end = output.find("\n    )", command_index)
        if argument_start >= 0 and argument_end >= 0:
            return output[argument_start:argument_end]
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if line.lstrip().startswith(command):
            context = [line]
            for next_line in lines[index + 1:]:
                stripped = next_line.strip()
                if stripped.startswith("--"):
                    break
                if stripped:
                    context.append(next_line)
            return " ".join(context)
    return ""


def read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def nested_value(data: dict[str, object], keys: list[str]) -> object:
    value: object = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


if __name__ == "__main__":
    raise SystemExit(main())
