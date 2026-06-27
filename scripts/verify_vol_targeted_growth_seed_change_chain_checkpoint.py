from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOT_PATH = ROOT / "bot.py"

COMMANDS = [
    "--vol-targeted-growth-seed-change-review",
    "--show-vol-targeted-growth-seed-change-review",
    "--vol-targeted-growth-seed-change-evidence-pack",
    "--show-vol-targeted-growth-seed-change-evidence-pack",
    "--vol-targeted-growth-seed-change-risk-reward-comparison",
    "--show-vol-targeted-growth-seed-change-risk-reward-comparison",
    "--vol-targeted-growth-seed-change-drawdown-stress-review",
    "--show-vol-targeted-growth-seed-change-drawdown-stress-review",
    "--vol-targeted-growth-seed-change-cost-turnover-review",
    "--show-vol-targeted-growth-seed-change-cost-turnover-review",
    "--vol-targeted-growth-seed-change-split-stability-review",
    "--show-vol-targeted-growth-seed-change-split-stability-review",
    "--vol-targeted-growth-seed-change-component-sleeve-review",
    "--show-vol-targeted-growth-seed-change-component-sleeve-review",
    "--vol-targeted-growth-seed-change-action-preview-design",
    "--show-vol-targeted-growth-seed-change-action-preview-design",
    "--vol-targeted-growth-seed-change-proposal-document",
    "--show-vol-targeted-growth-seed-change-proposal-document",
    "--vol-targeted-growth-seed-change-broker-exposure-review",
    "--show-vol-targeted-growth-seed-change-broker-exposure-review",
    "--vol-targeted-growth-seed-change-manual-review-checkpoint",
    "--show-vol-targeted-growth-seed-change-manual-review-checkpoint",
    "--vol-targeted-growth-formal-seed-change-proposal",
    "--show-vol-targeted-growth-formal-seed-change-proposal",
    "--vol-targeted-growth-seed-change-manual-approval-record",
    "--show-vol-targeted-growth-seed-change-manual-approval-record",
    "--vol-targeted-growth-seed-change-implementation-design",
    "--show-vol-targeted-growth-seed-change-implementation-design",
    "--vol-targeted-growth-seed-change-dry-run-diff",
    "--show-vol-targeted-growth-seed-change-dry-run-diff",
    "--vol-targeted-growth-active-seed-readiness",
    "--show-vol-targeted-growth-active-seed-readiness",
]

MODULES = [
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_review.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_evidence_pack.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_risk_reward_comparison.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_drawdown_stress_review.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_cost_turnover_review.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_split_stability_review.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_remaining_evidence_reviews.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_manual_review_checkpoint.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_formal_seed_change_proposal.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_manual_approval_record.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_implementation_design.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_seed_change_dry_run_diff.py",
    ROOT / "trading_bot" / "research" / "vol_targeted_growth_active_seed_readiness.py",
]

FOCUSED_VERIFIERS = [
    "scripts/verify_vol_targeted_growth_seed_change_review.py",
    "scripts/verify_vol_targeted_growth_seed_change_evidence_pack.py",
    "scripts/verify_vol_targeted_growth_seed_change_risk_reward_comparison.py",
    "scripts/verify_vol_targeted_growth_seed_change_drawdown_stress_review.py",
    "scripts/verify_vol_targeted_growth_seed_change_cost_split_reviews.py",
    "scripts/verify_vol_targeted_growth_seed_change_remaining_evidence_reviews.py",
    "scripts/verify_vol_targeted_growth_seed_change_manual_review_checkpoint.py",
    "scripts/verify_vol_targeted_growth_formal_seed_change_proposal.py",
    "scripts/verify_vol_targeted_growth_seed_change_manual_approval_record.py",
    "scripts/verify_vol_targeted_growth_seed_change_implementation_design.py",
    "scripts/verify_vol_targeted_growth_seed_change_dry_run_diff.py",
    "scripts/verify_vol_targeted_growth_seed_switch_status_only.py",
    "scripts/verify_vol_targeted_growth_active_seed_readiness.py",
]

EXPECTED_STATUS_TOKENS = [
    "vol_targeted_growth_seed_change_review_created_manual_review_required",
    "vol_targeted_growth_seed_change_evidence_pack_incomplete_manual_review_required",
    "vol_targeted_growth_risk_reward_evidence_created_manual_review_required",
    "vol_targeted_growth_drawdown_stress_evidence_created_manual_review_required",
    "vol_targeted_growth_cost_turnover_evidence_created_manual_review_required",
    "vol_targeted_growth_split_stability_evidence_created_manual_review_required",
    "vol_targeted_growth_component_sleeve_evidence_created_manual_review_required",
    "vol_targeted_growth_action_preview_design_evidence_created_manual_review_required",
    "vol_targeted_growth_seed_change_proposal_document_draft_created_manual_review_required",
    "vol_targeted_growth_broker_exposure_evidence_created_manual_review_required",
    "vol_targeted_growth_seed_change_ready_for_formal_proposal_manual_review",
    "vol_targeted_growth_formal_seed_change_proposal_created_manual_approval_required",
    "vol_targeted_growth_seed_change_manual_approval_recorded_implementation_required",
    "vol_targeted_growth_seed_change_implementation_design_created_manual_review_required",
    "vol_targeted_growth_seed_change_dry_run_diff_created_manual_review_required",
    "vol_targeted_growth_active_seed_monitoring_ready_manual_review_required",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
    "MULTI_SLEEVE",
]

REQUIRED_SAFETY_TOKENS = [
    "seed_changed",
    "seed_change_implemented",
    "order_instructions_created",
    "execution_approved",
    "paper_execution_approved",
    "scheduling_approved",
    "never_schedule_order_capable_commands",
    "qqq_100_trend_gate",
    "higher_growth_multi_sleeve_target_vol_15_win_20_cap_1x",
]

FORBIDDEN_SOURCE_TOKENS = [
    "TradingClient(",
    "MarketOrderRequest(",
    ".submit_order(",
    ".cancel_order(",
    ".replace_order(",
    "get_all_positions(",
    "get_alpaca_positions(",
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
    run_focused_verifiers(failures)
    if failures:
        print("Volatility-targeted seed-change chain checkpoint failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Volatility-targeted seed-change chain checkpoint passed.")
    print("Verified saved-output seed-change review, status-only seed switch, and active-seed readiness, with order/execution/scheduling boundaries preserved.")
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
        for token in FORBIDDEN_SOURCE_TOKENS:
            if token in source:
                failures.append(f"forbidden token in {path.relative_to(ROOT)}: {token}")
        show_start = source.find("def show_")
        if show_start >= 0:
            show_end = source.find("\ndef ", show_start + 1)
            show_body = source[show_start : show_end if show_end >= 0 else len(source)]
            if "write_rows" in show_body or "generate_" in show_body:
                failures.append(f"show command may regenerate output: {path.relative_to(ROOT)}")
    for token in EXPECTED_STATUS_TOKENS + REQUIRED_SAFETY_TOKENS:
        if token not in combined:
            failures.append(f"missing required seed-change chain token: {token}")


def run_focused_verifiers(failures: list[str]) -> None:
    for verifier in FOCUSED_VERIFIERS:
        result = subprocess.run(
            [sys.executable, verifier],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=90,
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
