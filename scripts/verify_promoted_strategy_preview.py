from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.research.promoted_preview import (
    build_promoted_preview_rows,
    read_preview_candidates,
)
from trading_bot.research.promotion import generate_strategy_promotion_report


class FakePriceData:
    def __init__(self, closes: list[float], volumes: list[float] | None = None):
        if volumes is None:
            volumes = [1000000 for _ in closes]
        self.rows = [
            {
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": volumes[index],
            }
            for index, close in enumerate(closes)
        ]

    def iterrows(self):
        for index, row in enumerate(self.rows):
            yield index, row


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "strategy_promotion_report.csv",
            [
                {
                    "strategy_name": "sma_50_200_trend",
                    "strategy_family": "trend",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "preview_candidate",
                    "required_next_step": "Future preview-mode research only; not approved for paper execution.",
                },
                {
                    "strategy_name": "buy_above_200_exit_below_200",
                    "strategy_family": "trend",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "preview_candidate",
                    "required_next_step": "Future preview-mode research only; not approved for paper execution.",
                },
                {
                    "strategy_name": "fifty_two_week_high_breakout",
                    "strategy_family": "breakout",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "preview_candidate",
                    "required_next_step": "Future preview-mode research only; not approved for paper execution.",
                },
                {
                    "strategy_name": "sma_20_50_basic",
                    "strategy_family": "trend",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "pause",
                    "required_next_step": "Pause strategy work.",
                },
                {
                    "strategy_name": "unsupported_strategy",
                    "strategy_family": "unknown",
                    "ticker_or_portfolio": "portfolio",
                    "promotion_status": "preview_candidate",
                    "required_next_step": "Future preview-mode research only.",
                },
            ],
        )

        candidates = read_preview_candidates(data_dir / "strategy_promotion_report.csv")
        candidate_names = {candidate["strategy_name"] for candidate in candidates}
        if "sma_20_50_basic" in candidate_names:
            failures.append("non-preview candidates should be ignored")
        if "buy_above_200_exit_below_200" not in candidate_names:
            failures.append("buy_above_200_exit_below_200 preview candidate was missing")
        buy_above = [candidate for candidate in candidates if candidate["strategy_name"] == "buy_above_200_exit_below_200"][0]
        if buy_above["strategy_family"] == "unknown":
            failures.append("buy_above_200_exit_below_200 should not have unknown strategy_family")

        disagreement_closes = [100.0] * 202 + [80.0] * 49 + [101.0]
        data_by_ticker = {"SPY": FakePriceData(disagreement_closes)}
        regime_data = FakePriceData([float(value) for value in range(1, 261)])
        rows, warnings = build_promoted_preview_rows(
            candidates,
            data_by_ticker,
            regime_ticker="SPY",
            regime_price_data=regime_data,
            created_at="2026-06-06T00:00:00Z",
        )
        if not rows:
            failures.append("preview rows were not created")
        if any(row.get("preview_only") is not True for row in rows):
            failures.append("preview_only should always be true")
        if not any(row.get("strategy_name") == "unsupported_strategy" and row.get("signal") == "SKIP" for row in rows):
            failures.append("unsupported strategies should be skipped with a clear row")
        if not any("Unsupported preview strategy skipped" in warning for warning in warnings):
            failures.append("unsupported strategy warning was missing")
        sma_row = [row for row in rows if row.get("strategy_name") == "sma_50_200_trend"][0]
        buy_above_row = [row for row in rows if row.get("strategy_name") == "buy_above_200_exit_below_200"][0]
        if sma_row.get("desired_position") != "flat":
            failures.append("sma_50_200_trend should use 50-day SMA versus 200-day SMA")
        if buy_above_row.get("desired_position") != "long":
            failures.append("buy_above_200_exit_below_200 should still use close versus 200-day SMA")
        if sma_row.get("desired_position") == buy_above_row.get("desired_position"):
            failures.append("the two trend previews should be able to disagree on synthetic data")
        if sma_row["sma_50"] != 80.42 or sma_row["sma_200"] != 95.105:
            failures.append("SMA diagnostics should be deterministic")
        if sma_row["sma_50_vs_200_state"] != "bearish":
            failures.append("sma_50_vs_200_state should be deterministic")
        if sma_row["distance_sma_50_to_sma_200_pct"] != -15.4408:
            failures.append("distance_sma_50_to_sma_200_pct should be deterministic")
        if buy_above_row["close_above_sma_200"] is not True:
            failures.append("close_above_sma_200 should be context for buy_above strategy")
        if not any(row.get("strategy_name") == "fifty_two_week_high_breakout" for row in rows):
            failures.append("breakout preview row was missing")
        if sma_row["regime_state"] != "bullish":
            failures.append("regime_state should be calculated from synthetic SPY data")
        if sma_row["distance_to_sma_200_pct"] != 6.1984:
            failures.append("trend distance_to_sma_200_pct should be deterministic")
        breakout_row = [row for row in rows if row.get("strategy_name") == "fifty_two_week_high_breakout"][0]
        if breakout_row["distance_to_252_high_pct"] != 0.0:
            failures.append("breakout distance_to_252_high_pct should be deterministic")
        if breakout_row["volume_confirmation"] is not True:
            failures.append("volume_confirmation should be deterministic when volume exists")
        if breakout_row["volume_20_day_avg"] != 1000000.0:
            failures.append("20-day average volume should be deterministic")

        short_rows, short_warnings = build_promoted_preview_rows(
            [candidate for candidate in candidates if candidate["strategy_name"] == "sma_50_200_trend"],
            {"MSFT": FakePriceData([1.0, 2.0, 3.0])},
            regime_ticker="SPY",
            regime_price_data=None,
            created_at="2026-06-06T00:00:00Z",
        )
        if not short_rows or "not_enough_history_for_preview" not in short_rows[0].get("diagnostic_warning", ""):
            failures.append("missing data should create a clear diagnostic_warning")
        if any(row.get("preview_only") is not True for row in short_rows):
            failures.append("missing-data rows should keep preview_only true")

    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        write_csv(
            data_dir / "research_report.csv",
            [
                {
                    "strategy_name": "buy_above_200_exit_below_200",
                    "ticker_or_portfolio": "portfolio",
                    "strategy_family": "unknown",
                    "strategy_role": "unknown",
                    "report_view": "portfolio_full_period",
                    "cagr_pct": 8,
                    "sharpe_ratio": 0.8,
                    "calmar_ratio": 0.4,
                    "max_drawdown_pct": 20,
                    "active_combined_rank_score": 1,
                    "beats_best_benchmark_cagr": False,
                    "beats_best_benchmark_sharpe": False,
                    "beats_best_benchmark_calmar": False,
                    "has_lower_drawdown_than_best_benchmark": True,
                    "number_of_trades": 5,
                }
            ],
        )
        write_csv(
            data_dir / "walk_forward_report.csv",
            [
                {
                    "strategy_name": "buy_above_200_exit_below_200",
                    "ticker_or_portfolio": "portfolio",
                    "walk_forward_view": "portfolio_active",
                    "robustness_label": "moderate_decay",
                    "out_of_sample_cagr_pct": 8,
                    "out_of_sample_sharpe": 0.8,
                    "out_of_sample_calmar": 0.4,
                    "out_of_sample_max_drawdown_pct": 20,
                }
            ],
        )
        result = generate_strategy_promotion_report(data_dir)
        row = result.rows[0]
        if row["strategy_name"] != "buy_above_200_exit_below_200" or row["strategy_family"] == "unknown":
            failures.append("promotion report should normalize buy_above_200_exit_below_200 family")

    if failures:
        print("Promoted strategy preview verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Promoted strategy preview verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
