from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_PATH = ROOT / "bot.py"

COMMANDS = [
    "--vol-targeted-growth-candidate-decision-record",
    "--show-vol-targeted-growth-candidate-decision-record",
    "--vol-targeted-growth-proposal-implementation-design",
    "--show-vol-targeted-growth-proposal-implementation-design",
    "--vol-targeted-growth-proposal-preview-schema",
    "--show-vol-targeted-growth-proposal-preview-schema",
    "--vol-targeted-growth-proposal-preview",
    "--show-vol-targeted-growth-proposal-preview",
    "--vol-targeted-growth-action-preview-design",
    "--show-vol-targeted-growth-action-preview-design",
    "--vol-targeted-growth-action-preview",
    "--show-vol-targeted-growth-action-preview",
    "--vol-targeted-growth-action-preview-quality-gate",
    "--show-vol-targeted-growth-action-preview-quality-gate",
]

MODULES = [
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_candidate_decision_record.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_proposal_implementation_design.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_proposal_preview_schema.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_proposal_preview.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_action_preview_design.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_action_preview.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_action_preview_quality_gate.py",
]

FOCUSED_VERIFIERS = [
    "scripts/verify_vol_targeted_growth_candidate_decision_record.py",
    "scripts/verify_vol_targeted_growth_proposal_implementation_design.py",
    "scripts/verify_vol_targeted_growth_proposal_preview_schema.py",
    "scripts/verify_vol_targeted_growth_proposal_preview.py",
    "scripts/verify_vol_targeted_growth_action_preview_design.py",
    "scripts/verify_vol_targeted_growth_action_preview.py",
    "scripts/verify_vol_targeted_growth_action_preview_quality_gate.py",
]

EXPECTED_OUTPUTS = [
    "data/vol_targeted_growth_candidate_decision_record.csv",
    "data/vol_targeted_growth_candidate_decision_record_summary.csv",
    "data/vol_targeted_growth_candidate_decision_record_evidence.csv",
    "data/vol_targeted_growth_candidate_decision_record_blockers.csv",
    "data/vol_targeted_growth_proposal_implementation_design.csv",
    "data/vol_targeted_growth_proposal_implementation_design_summary.csv",
    "data/vol_targeted_growth_proposal_implementation_design_evidence.csv",
    "data/vol_targeted_growth_proposal_implementation_design_blockers.csv",
    "data/vol_targeted_growth_proposal_preview_schema.csv",
    "data/vol_targeted_growth_proposal_preview_schema_summary.csv",
    "data/vol_targeted_growth_proposal_preview_schema_evidence.csv",
    "data/vol_targeted_growth_proposal_preview_schema_blockers.csv",
    "data/vol_targeted_growth_proposal_preview.csv",
    "data/vol_targeted_growth_proposal_preview_summary.csv",
    "data/vol_targeted_growth_proposal_preview_evidence.csv",
    "data/vol_targeted_growth_proposal_preview_blockers.csv",
    "data/vol_targeted_growth_action_preview_design.csv",
    "data/vol_targeted_growth_action_preview_design_summary.csv",
    "data/vol_targeted_growth_action_preview_design_evidence.csv",
    "data/vol_targeted_growth_action_preview_design_blockers.csv",
    "data/vol_targeted_growth_action_preview.csv",
    "data/vol_targeted_growth_action_preview_summary.csv",
    "data/vol_targeted_growth_action_preview_evidence.csv",
    "data/vol_targeted_growth_action_preview_blockers.csv",
    "data/vol_targeted_growth_action_preview_quality_gate.csv",
    "data/vol_targeted_growth_action_preview_quality_gate_summary.csv",
    "data/vol_targeted_growth_action_preview_quality_gate_evidence.csv",
    "data/vol_targeted_growth_action_preview_quality_gate_blockers.csv",
]

REQUIRED_TOKENS = [
    "vol_targeted_growth_candidate_decision_manual_discussion_only",
    "vol_targeted_growth_proposal_implementation_design_ready_manual_review_required",
    "vol_targeted_growth_proposal_preview_schema_ready_manual_review_required",
    "vol_targeted_growth_proposal_preview_created_saved_output_only",
    "vol_targeted_growth_action_preview_design_ready_manual_review_required",
    "vol_targeted_growth_action_preview_created_saved_output_only",
    "vol_targeted_growth_action_preview_quality_gate_usable_manual_review_required",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "qqq_100_trend_gate",
    "order_instructions_created",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "never_schedule_order_capable_commands",
]

FORBIDDEN_TOKENS = [
    "TradingClient(",
    "get_all_positions(",
    "submit_order(",
    "MarketOrderRequest(",
    "cancel_order(",
    "replace_order(",
    "load_config(",
    "config.json",
    "insert_trade_log(",
    "send_discord",
    "send_telegram",
    "yf.download(",
    "import yfinance",
    "Register-ScheduledTask",
    "schtasks /create",
    "crontab",
    "systemctl",
]


def main() -> int:
    failures: list[str] = []
    bot_source = read_text(BOT_PATH)
    verify_commands(bot_source, failures)
    verify_modules(failures)
    verify_outputs_ignored(failures)
    run_focused_verifiers(failures)
    if failures:
        print("Volatility-targeted preview/action chain checkpoint failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted preview/action chain checkpoint passed.")
    print("Verified existing non-executable design/preview/action-preview chain, false approval boundaries, ignored outputs, and focused verifier coverage.")
    return 0


def verify_commands(source: str, failures: list[str]) -> None:
    load_config = source.find("config = load_config(")
    if load_config < 0:
        load_config = len(source)
    for command in COMMANDS:
        if command not in source:
            failures.append(f"missing command: {command}")
        early = source.find(f'sys.argv[1:] == ["{command}"]')
        if early < 0:
            failures.append(f"missing early report-only route: {command}")
        elif early > load_config:
            failures.append(f"route appears after config loading: {command}")


def verify_modules(failures: list[str]) -> None:
    combined = ""
    for path in MODULES:
        source = read_text(path)
        if not source:
            failures.append(f"missing module: {path.relative_to(ROOT)}")
            continue
        combined += "\n" + source
        if "SAFETY_FLAGS" not in source:
            failures.append(f"missing SAFETY_FLAGS: {path.relative_to(ROOT)}")
        if "write_rows" not in source:
            failures.append(f"missing saved-output writer: {path.relative_to(ROOT)}")
        for token in FORBIDDEN_TOKENS:
            if token in source:
                failures.append(f"forbidden token in {path.relative_to(ROOT)}: {token}")
        show_start = source.find("def show_")
        if show_start >= 0:
            show_body = source[show_start : source.find("\ndef ", show_start + 1) if source.find("\ndef ", show_start + 1) >= 0 else len(source)]
            if "write_rows" in show_body or "generate_" in show_body:
                failures.append(f"show command may regenerate output: {path.relative_to(ROOT)}")
    for token in REQUIRED_TOKENS:
        if token not in combined:
            failures.append(f"missing required chain token: {token}")


def verify_outputs_ignored(failures: list[str]) -> None:
    for output in EXPECTED_OUTPUTS:
        result = subprocess.run(
            ["git", "check-ignore", output],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"generated output is not ignored: {output}")


def run_focused_verifiers(failures: list[str]) -> None:
    for verifier in FOCUSED_VERIFIERS:
        result = subprocess.run(
            [sys.executable, verifier],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if result.returncode != 0:
            failures.append(f"{verifier} failed: {(result.stdout + result.stderr).strip()}")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
