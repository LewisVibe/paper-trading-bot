from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import bot
from trading_bot.cli import parser as cli_parser


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "scripts" / "verify_command_inventory.py"


def saved_command_inventory() -> set[str]:
    spec = importlib.util.spec_from_file_location("command_inventory", INVENTORY_PATH)
    assert spec and spec.loader
    inventory = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(inventory)
    return set(inventory.REQUIRED_COMMANDS)


def parser_options(monkeypatch: pytest.MonkeyPatch) -> set[str]:
    original_parser = cli_parser.argparse.ArgumentParser

    class CapturingParser(original_parser):
        instance: "CapturingParser | None" = None

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            CapturingParser.instance = self

    monkeypatch.setattr(cli_parser, "argparse", SimpleNamespace(ArgumentParser=CapturingParser))
    monkeypatch.setattr(sys, "argv", ["bot.py"])
    bot.parse_args()

    assert CapturingParser.instance is not None
    return {
        option
        for action in CapturingParser.instance._actions
        for option in action.option_strings
        if option not in {"-h", "--help"}
    }


def parse_cli(monkeypatch: pytest.MonkeyPatch, *argv: str):
    monkeypatch.setattr(sys, "argv", ["bot.py", *argv])
    return bot.parse_args()


def configure_main_dependencies(monkeypatch: pytest.MonkeyPatch):
    config = SimpleNamespace(log_file=ROOT / "test.log")
    logger = object()
    monkeypatch.setattr(bot, "load_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(bot, "setup_logging", lambda *args, **kwargs: logger)
    return config, logger


def test_parser_option_inventory_matches_saved_baseline(monkeypatch: pytest.MonkeyPatch):
    assert parser_options(monkeypatch) == saved_command_inventory()


def test_bot_reexports_extracted_parser_for_compatibility():
    assert bot.parse_args is cli_parser.parse_args


def test_parser_defaults_for_normal_run(monkeypatch: pytest.MonkeyPatch):
    args = parse_cli(monkeypatch)

    assert args.config == "config.json"
    assert args.dry_run is False
    assert args.backtest is False
    assert args.paper_order_test is None


@pytest.mark.parametrize(
    ("argv", "attribute", "expected"),
    [
        (("--research-report",), "research_report", True),
        (("--backtest",), "backtest", True),
        (("--preview-promoted-strategies",), "preview_promoted_strategies", True),
        (
            ("--paper-order-test", "AAPL", "buy", "1", "--confirm-paper-order"),
            "paper_order_test",
            ["AAPL", "buy", "1"],
        ),
        (
            ("--execute-slow-sma-paper", "--confirm-slow-sma-paper"),
            "confirm_slow_sma_paper",
            True,
        ),
    ],
)
def test_parser_characterizes_representative_command_families(
    monkeypatch: pytest.MonkeyPatch,
    argv: tuple[str, ...],
    attribute: str,
    expected: object,
):
    assert getattr(parse_cli(monkeypatch, *argv), attribute) == expected


def test_report_only_flag_dispatches_without_loading_config(monkeypatch: pytest.MonkeyPatch):
    args = parse_cli(monkeypatch, "--research-report")
    monkeypatch.setattr(bot, "parse_args", lambda: args)
    monkeypatch.setattr(
        bot,
        "generate_research_report",
        lambda: SimpleNamespace(warnings=[], summary_lines=["report"], output_path="report.csv"),
    )
    monkeypatch.setattr(bot, "load_config", lambda *args, **kwargs: pytest.fail("config must not load"))

    assert bot.main() == 0


def test_normal_run_dispatches_to_bot_runner(monkeypatch: pytest.MonkeyPatch):
    args = parse_cli(monkeypatch)
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(bot, "parse_args", lambda: args)
    monkeypatch.setattr(bot, "run_bot", lambda actual_config, actual_logger: calls.append((actual_config, actual_logger)) or 7)

    assert bot.main() == 7
    assert calls == [(config, logger)]


def test_backtest_dispatches_to_research_runner(monkeypatch: pytest.MonkeyPatch):
    args = parse_cli(monkeypatch, "--backtest")
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(bot, "parse_args", lambda: args)
    monkeypatch.setattr(bot, "run_backtest", lambda actual_config, actual_logger: calls.append((actual_config, actual_logger)) or 8)

    assert bot.main() == 8
    assert calls == [(config, logger)]


def test_preview_dispatches_to_preview_runner(monkeypatch: pytest.MonkeyPatch):
    args = parse_cli(monkeypatch, "--preview-promoted-strategies")
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(bot, "parse_args", lambda: args)
    monkeypatch.setattr(bot, "run_promoted_strategy_preview", lambda actual_config, actual_logger: calls.append((actual_config, actual_logger)) or 9)

    assert bot.main() == 9
    assert calls == [(config, logger)]


def test_confirmed_paper_order_dispatches_to_paper_runner(monkeypatch: pytest.MonkeyPatch):
    args = parse_cli(monkeypatch, "--paper-order-test", "AAPL", "buy", "1", "--confirm-paper-order")
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(bot, "parse_args", lambda: args)
    monkeypatch.setattr(bot, "run_paper_order_test", lambda **kwargs: calls.append(kwargs) or 10)

    assert bot.main() == 10
    assert calls == [
        {
            "config": config,
            "logger": logger,
            "ticker": "AAPL",
            "side": "buy",
            "quantity_text": "1",
            "confirm_paper_order": True,
        }
    ]


@pytest.mark.parametrize(
    ("side", "expected_side"),
    [("buy", bot.OrderSide.BUY), ("sell", bot.OrderSide.SELL)],
)
def test_direct_order_submission_adapter_uses_mocked_client(side: str, expected_side):
    submitted: list[object] = []

    class Client:
        def submit_order(self, *, order_data):
            submitted.append(order_data)
            return "submitted"

    assert bot.submit_alpaca_order(Client(), "AAPL", side, bot.Decimal("2")) == "submitted"
    assert len(submitted) == 1
    assert submitted[0].symbol == "AAPL"
    assert submitted[0].qty == 2.0
    assert submitted[0].side == expected_side
    assert submitted[0].time_in_force == bot.TimeInForce.DAY
