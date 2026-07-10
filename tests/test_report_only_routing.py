from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from trading_bot.cli import entrypoint, report_only
from trading_bot.research import vps_monitoring_status


ROOT = Path(__file__).resolve().parents[1]


def test_saved_output_route_dispatches_to_focused_runner(monkeypatch: pytest.MonkeyPatch):
    calls: list[str] = []
    monkeypatch.setattr(
        vps_monitoring_status,
        "print_vps_monitoring_status",
        lambda: calls.append("vps_monitoring_status") or 17,
    )

    assert report_only.dispatch_report_only(["--vps-monitoring-status"]) == 17
    assert calls == ["vps_monitoring_status"]


def test_unknown_report_only_route_is_not_handled():
    assert report_only.dispatch_report_only(["--not-a-command"]) is None


@pytest.mark.parametrize(
    ("argv", "expected_class"),
    [
        (
            ["--alpaca-paper-readiness-report", "--confirm-readonly-alpaca-check"],
            report_only.BROKER_READ,
        ),
        (["--paper-order-smoke-test-postcheck"], report_only.BROKER_READ),
        (
            ["--qqq100-action-preview", "--use-paper-positions-readonly"],
            report_only.BROKER_READ,
        ),
        (
            ["--vol-targeted-growth-broker-position-comparison"],
            report_only.BROKER_READ,
        ),
        (["--alpaca-connectivity-diagnostics"], report_only.NETWORK_DIAGNOSTIC),
        (["--qqq100-action-preview"], report_only.REPORT_ONLY),
        (["--show-alpaca-connectivity-diagnostics"], report_only.REPORT_ONLY),
    ],
)
def test_early_route_side_effect_classification(argv: list[str], expected_class: str):
    assert report_only.classify_early_route(argv) == expected_class


@pytest.mark.parametrize(
    "argv",
    [
        ["--alpaca-paper-readiness-report", "--confirm-readonly-alpaca-check"],
        ["--alpaca-connectivity-diagnostics"],
        ["--qqq100-action-preview", "--use-paper-positions-readonly"],
        ["--vol-targeted-growth-fresh-broker-pre-ticket-gate-run"],
    ],
)
def test_report_only_dispatch_refuses_external_dependency_routes(
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
):
    monkeypatch.setattr(
        report_only,
        "_dispatch_early_command",
        lambda _: pytest.fail("external dependency route reached report-only dispatcher"),
    )

    assert report_only.dispatch_report_only(argv) is None


def test_entrypoint_delegates_to_compatibility_dispatcher(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(
        entrypoint,
        "dispatch_early_command",
        lambda argv: calls.append(argv) or 23,
    )

    assert entrypoint.run(["--saved-output-command"]) == 23
    assert calls == [["--saved-output-command"]]


def test_importing_bot_does_not_execute_an_early_route():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.argv = ['bot.py', '--vps-monitoring-status']; "
                "import bot; "
                "print('bot imported')"
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "bot imported"
