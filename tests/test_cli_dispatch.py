from __future__ import annotations

import ast
import inspect
from types import SimpleNamespace

import pytest

from trading_bot.cli import application, dispatch, report_only
from trading_bot.runners import previews


def namespace_for(selected: str, descriptors: tuple[dispatch.CommandDescriptor, ...]):
    values = {descriptor.dest: False for descriptor in descriptors}
    values.update(
        {
            "confirm_readonly_alpaca_check": False,
            "confirm_saved_price_snapshot_run": False,
            "ticker": "",
            "side": "",
            "quantity": "",
            "use_paper_positions_readonly": False,
        }
    )
    values[selected] = ["AAPL", "buy", "1"] if selected == "paper_order_test" else True
    return SimpleNamespace(**values)


def test_pre_config_registry_is_ordered_unique_and_complete():
    destinations = [descriptor.dest for descriptor in dispatch.PRE_CONFIG_COMMANDS]

    assert len(destinations) == 358
    assert len(destinations) == len(set(destinations))
    route_source = inspect.getsource(report_only)
    assert all(descriptor.option in route_source for descriptor in dispatch.PRE_CONFIG_COMMANDS)


def test_config_registry_is_unique_and_has_explicit_handlers():
    destinations = [descriptor.dest for descriptor in dispatch.CONFIG_COMMANDS]

    assert len(destinations) == 23
    assert len(destinations) == len(set(destinations))
    assert set(application.build_config_handlers()) == set(destinations)
    assert set(destinations).isdisjoint(descriptor.dest for descriptor in dispatch.PRE_CONFIG_COMMANDS)


def test_application_uses_extracted_saved_preview_runners():
    assert application.run_promoted_risk_preview is previews.run_promoted_risk_preview
    assert application.run_promoted_consensus_preview is previews.run_promoted_consensus_preview
    assert application.run_promoted_decision_preview is previews.run_promoted_decision_preview


def test_every_pre_config_descriptor_routes_once(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(
        dispatch,
        "dispatch_early_command",
        lambda argv: calls.append(argv) or 0,
    )

    for descriptor in dispatch.PRE_CONFIG_COMMANDS:
        calls.clear()
        result = dispatch.dispatch_pre_config(
            namespace_for(descriptor.dest, dispatch.PRE_CONFIG_COMMANDS)
        )

        assert result.handled is True
        assert result.descriptor is descriptor
        assert calls == [[descriptor.option]]


def test_forwarded_arguments_are_explicit(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []
    monkeypatch.setattr(
        dispatch,
        "dispatch_early_command",
        lambda argv: calls.append(argv) or 0,
    )
    args = namespace_for("paper_order_smoke_test_live_preflight", dispatch.PRE_CONFIG_COMMANDS)
    args.ticker = "AAPL"
    args.side = "buy"
    args.quantity = "1"
    args.confirm_readonly_alpaca_check = True

    dispatch.dispatch_pre_config(args)

    assert calls == [
        [
            "--paper-order-smoke-test-live-preflight",
            "--ticker",
            "AAPL",
            "--side",
            "buy",
            "--quantity",
            "1",
            "--confirm-readonly-alpaca-check",
        ]
    ]


def test_every_config_descriptor_invokes_one_matching_handler():
    calls: list[str] = []
    handlers = {
        descriptor.dest: (
            lambda _args, _config, _logger, name=descriptor.dest: calls.append(name) or 0
        )
        for descriptor in dispatch.CONFIG_COMMANDS
    }

    for descriptor in dispatch.CONFIG_COMMANDS:
        calls.clear()
        result = dispatch.dispatch_config_command(
            namespace_for(descriptor.dest, dispatch.CONFIG_COMMANDS),
            object(),
            object(),
            handlers,
        )

        assert result.handled is True
        assert result.descriptor is descriptor
        assert calls == [descriptor.dest]


def test_execution_commands_are_explicitly_classified():
    effects = {descriptor.dest: descriptor.side_effect for descriptor in dispatch.CONFIG_COMMANDS}

    assert effects["execute_qqq100_paper"] is dispatch.SideEffect.PAPER_EXECUTION
    assert effects["execute_slow_sma_paper"] is dispatch.SideEffect.PAPER_EXECUTION
    assert effects["execute_vol_targeted_growth_paper"] is dispatch.SideEffect.PAPER_EXECUTION
    assert effects["prepare_vol_targeted_growth_paper_ticket"] is dispatch.SideEffect.BROKER_READ
    assert effects["vol_targeted_growth_paper_postcheck"] is dispatch.SideEffect.BROKER_READ
    assert effects["paper_order_test"] is dispatch.SideEffect.PAPER_EXECUTION
    assert dispatch.NORMAL_RUN.side_effect is dispatch.SideEffect.PAPER_EXECUTION


def test_report_only_wrapper_refuses_non_report_descriptors(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        report_only,
        "_dispatch_early_command",
        lambda _: pytest.fail("non-report command reached report-only dispatcher"),
    )

    for descriptor in dispatch.PRE_CONFIG_COMMANDS:
        if descriptor.side_effect is dispatch.SideEffect.REPORT_ONLY:
            continue
        argv = [descriptor.option]
        if descriptor.dest == "qqq100_action_preview":
            argv.append("--use-paper-positions-readonly")
        assert report_only.dispatch_report_only(argv) is None


def test_application_run_has_no_command_if_chain():
    tree = ast.parse(inspect.getsource(application.run))
    direct_arg_checks = [
        node
        for node in tree.body[0].body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Attribute)
        and isinstance(node.test.value, ast.Name)
        and node.test.value.id == "args"
    ]

    assert direct_arg_checks == []
