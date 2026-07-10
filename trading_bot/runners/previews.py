"""Saved-output preview runners."""

from __future__ import annotations

from pathlib import Path

from trading_bot.research.promoted_consensus import run_promoted_consensus_preview_files
from trading_bot.research.promoted_decision import run_promoted_decision_preview_files
from trading_bot.research.promoted_risk import run_promoted_risk_preview_files


def run_promoted_risk_preview() -> int:
    status_code, lines = run_promoted_risk_preview_files(
        Path("data") / "promoted_strategy_preview.csv",
        Path("data") / "promoted_strategy_action_preview.csv",
        Path("data") / "promoted_risk_preview.csv",
    )
    for line in lines:
        print(line)
    return status_code


def run_promoted_consensus_preview() -> int:
    status_code, lines = run_promoted_consensus_preview_files(
        Path("data") / "promoted_strategy_preview.csv",
        Path("data") / "promoted_consensus_preview.csv",
    )
    for line in lines:
        print(line)
    return status_code


def run_promoted_decision_preview() -> int:
    status_code, lines = run_promoted_decision_preview_files(
        Path("data") / "promoted_consensus_preview.csv",
        Path("data") / "promoted_strategy_action_preview.csv",
        Path("data") / "promoted_risk_preview.csv",
        Path("data") / "promoted_decision_preview.csv",
    )
    for line in lines:
        print(line)
    return status_code
