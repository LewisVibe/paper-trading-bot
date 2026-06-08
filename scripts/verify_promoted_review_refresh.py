from __future__ import annotations

import csv
import inspect
import io
import sys
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bot
import trading_bot.research.promoted_review_refresh as refresh
from trading_bot.research.promoted_review_refresh import PromotedReviewStep, refresh_promoted_review


FORBIDDEN_SOURCE_TOKENS = [
    "MarketOrderRequest",
    "submit_order",
    "cancel_order",
    "insert_trade_log",
    "send_discord_alert",
    "decide_trade",
    "init_database",
    "sqlite3",
]


def main() -> int:
    failures: list[str] = []
    verify_step_order_and_summary(failures)
    verify_missing_prerequisite(failures)
    verify_no_forbidden_source_paths(failures)

    if failures:
        print("Promoted review refresh verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Promoted review refresh verification passed.")
    return 0


def verify_step_order_and_summary(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        decision_path = data_dir / "promoted_decision_preview.csv"
        write_decision_fixture(decision_path)
        calls: list[str] = []
        steps = [
            mocked_step("preview_promoted_strategies", "python bot.py --preview-promoted-strategies", data_dir / "promoted_strategy_preview.csv", calls),
            mocked_step("preview_promoted_actions_readonly", "python bot.py --preview-promoted-actions --use-paper-positions-readonly", data_dir / "promoted_strategy_action_preview.csv", calls),
            mocked_step("promoted_risk_preview", "python bot.py --promoted-risk-preview", data_dir / "promoted_risk_preview.csv", calls),
            mocked_step("promoted_consensus_preview", "python bot.py --promoted-consensus-preview", data_dir / "promoted_consensus_preview.csv", calls),
            mocked_step("promoted_decision_preview", "python bot.py --promoted-decision-preview", decision_path, calls),
            mocked_step("show_promoted_decision", "python bot.py --show-promoted-decision", decision_path, calls),
        ]
        result = refresh_promoted_review(steps, decision_path, data_dir / "promoted_review_refresh_summary.csv")
        expected_order = [step.step_name for step in steps]
        if calls != expected_order:
            failures.append(f"promoted review steps ran out of order: {calls}")
        if result.status_code != 0:
            failures.append("all mocked promoted review steps should pass")
        if not result.output_path.exists():
            failures.append("promoted_review_refresh_summary.csv was not created")
        with result.output_path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != refresh.PROMOTED_REVIEW_REFRESH_COLUMNS:
                failures.append("promoted review refresh columns changed unexpectedly")
            rows = list(reader)
        for row in rows:
            if row["research_only"] != "True" or row["preview_only"] != "True" or row["execution_approved"] != "False":
                failures.append(f"safety flags failed for {row['step_name']}")
        summary = "\n".join(result.summary_lines)
        for expected_text in [
            "PROMOTED REVIEW REFRESH. PREVIEW ONLY. NOT EXECUTION.",
            "blocked_strategy_disagreement=2",
            "no_action_unanimous_flat=1",
            "Execution approved: False for all rows.",
        ]:
            if expected_text not in summary:
                failures.append(f"summary missing expected text: {expected_text}")


def verify_missing_prerequisite(failures: list[str]) -> None:
    with TemporaryDirectory() as tmp:
        data_dir = Path(tmp)

        def missing_step() -> int:
            print("Missing strategy promotion report: data/strategy_promotion_report.csv", file=sys.stderr)
            return 1

        stderr_buffer = io.StringIO()
        steps = [
            PromotedReviewStep(
                "preview_promoted_strategies",
                "python bot.py --preview-promoted-strategies",
                data_dir / "promoted_strategy_preview.csv",
                lambda: missing_step(),
            )
        ]
        with redirect_stderr(stderr_buffer):
            result = refresh_promoted_review(steps, data_dir / "promoted_decision_preview.csv", data_dir / "summary.csv")
        if result.status_code != 1:
            failures.append("missing prerequisite should make refresh return status 1")
        message = "\n".join(result.summary_lines + [str(row["message"]) for row in result.rows])
        for expected_text in [
            "python bot.py --research-report",
            "python bot.py --walk-forward-report",
            "python bot.py --strategy-promotion-report",
        ]:
            if expected_text not in message:
                failures.append(f"missing prerequisite message should mention {expected_text}")


def verify_no_forbidden_source_paths(failures: list[str]) -> None:
    helper_source = inspect.getsource(refresh)
    command_source = inspect.getsource(bot.run_refresh_promoted_review)
    for token in FORBIDDEN_SOURCE_TOKENS:
        if token in helper_source:
            failures.append(f"promoted review refresh helper should not reference {token}")
        if token in command_source:
            failures.append(f"run_refresh_promoted_review should not reference {token}")
    command_source_lower = command_source.lower()
    if "use_paper_positions_readonly=true" not in command_source_lower:
        failures.append("refresh command should use the existing read-only paper-position action preview path")
    if "force_dry_run=false" in command_source_lower or "dry_run = false" in command_source_lower:
        failures.append("refresh command must not change dry_run behavior")


def mocked_step(step_name: str, command: str, output_path: Path, calls: list[str]) -> PromotedReviewStep:
    def run() -> int:
        calls.append(step_name)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not output_path.exists():
            output_path.write_text("ok\n", encoding="utf-8")
        return 0

    return PromotedReviewStep(step_name, command, output_path, run)


def write_decision_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        decision_row("AAPL", "blocked_strategy_disagreement", "False"),
        decision_row("MSFT", "no_action_unanimous_flat", "False"),
        decision_row("SPY", "blocked_strategy_disagreement", "False"),
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def decision_row(ticker: str, decision_state: str, execution_approved: str) -> dict[str, str]:
    return {
        "created_at": "2026-06-08T00:00:00+00:00",
        "ticker": ticker,
        "consensus_state": "mixed_long_flat",
        "long_votes": "2",
        "flat_votes": "1",
        "risk_status_summary": "ok,warning",
        "action_summary": "would_open_long,no_action_already_flat",
        "decision_state": decision_state,
        "execution_approved": execution_approved,
        "reason": "Fixture decision row.",
        "research_only": "True",
        "preview_only": "True",
    }


if __name__ == "__main__":
    raise SystemExit(main())
