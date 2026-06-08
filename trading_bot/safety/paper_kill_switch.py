"""Pure paper kill-switch gate evaluation helper.

This module is intentionally pure and isolated from order mechanics. It accepts
plain Python values only and returns a local decision object for safety checks.
"""

from __future__ import annotations

from dataclasses import dataclass


STATUS_ALLOWED = "allowed"
STATUS_BLOCKED = "blocked"

NORMAL_RUN_COMMAND_NAMES = {
    "",
    "bot.py",
    "python bot.py",
    "default",
    "normal",
    "normal_bot",
    "normal_bot_run",
}


@dataclass(frozen=True)
class PaperKillSwitchGateDecision:
    allowed: bool
    status: str
    reasons: list[str]
    required_next_step: str


def evaluate_paper_kill_switch_gate(
    *,
    alpaca_paper: bool,
    allow_shorting: bool,
    paper_kill_switch_enabled: bool | None,
    execution_eligibility_blocked: bool,
    defensive_decision_blocked: bool,
    explicit_confirmation: bool,
    command_name: str,
    dry_run: bool | None = None,
    explicit_paper_execution_requested: bool | None = None,
) -> PaperKillSwitchGateDecision:
    """Evaluate a future paper-execution safety context without side effects."""

    reasons: list[str] = []

    if alpaca_paper is not True:
        reasons.append("alpaca_paper must be True")
    if allow_shorting is True:
        reasons.append("allow_shorting must be False")
    if paper_kill_switch_enabled is not True:
        reasons.append("paper_kill_switch_enabled must be explicitly True")
    if execution_eligibility_blocked is True:
        reasons.append("execution eligibility is blocked")
    if defensive_decision_blocked is True:
        reasons.append("defensive allocation decision is blocked")
    if explicit_confirmation is not True:
        reasons.append("explicit confirmation is required")
    if is_normal_or_missing_command(command_name):
        reasons.append("command_name must identify a future dedicated paper-execution command")
    if dry_run is False and explicit_paper_execution_requested is not True:
        reasons.append("dry_run=False requires explicit_paper_execution_requested=True")

    if reasons:
        return PaperKillSwitchGateDecision(
            allowed=False,
            status=STATUS_BLOCKED,
            reasons=reasons,
            required_next_step="Keep blocked; satisfy every paper kill-switch prerequisite before future execution design.",
        )
    return PaperKillSwitchGateDecision(
        allowed=True,
        status=STATUS_ALLOWED,
        reasons=["all isolated paper kill-switch prerequisites passed"],
        required_next_step="Allowed only inside this isolated helper result; this does not approve execution globally.",
    )


def is_normal_or_missing_command(command_name: str) -> bool:
    normalized = str(command_name or "").strip().lower()
    return normalized in NORMAL_RUN_COMMAND_NAMES
