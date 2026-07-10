from __future__ import annotations

import importlib.util
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from trading_bot.cli import application, entrypoint, parser as cli_parser
from trading_bot.research import reporting


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
    cli_parser.parse_args([])

    assert CapturingParser.instance is not None
    return {
        option
        for action in CapturingParser.instance._actions
        for option in action.option_strings
        if option not in {"-h", "--help"}
    }


def parse_cli(monkeypatch: pytest.MonkeyPatch, *argv: str):
    return cli_parser.parse_args(list(argv))


def configure_main_dependencies(monkeypatch: pytest.MonkeyPatch):
    config = SimpleNamespace(log_file=ROOT / "test.log")
    logger = object()
    monkeypatch.setattr(application, "load_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(application, "setup_logging", lambda *args, **kwargs: logger)
    return config, logger


def test_parser_option_inventory_matches_saved_baseline(monkeypatch: pytest.MonkeyPatch):
    assert parser_options(monkeypatch) == saved_command_inventory()


def test_bot_is_a_thin_compatibility_facade():
    source = (ROOT / "bot.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    assert len(source.splitlines()) <= 10
    assert "from trading_bot.cli.entrypoint import run" in source
    assert "run(sys.argv[1:])" in source
    assert not any(isinstance(node, (ast.FunctionDef, ast.ClassDef)) for node in tree.body)
    assert "TradingClient" not in source
    assert "submit_order" not in source


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
    monkeypatch.setattr(
        reporting,
        "generate_research_report",
        lambda: SimpleNamespace(warnings=[], summary_lines=["report"], output_path="report.csv"),
    )
    monkeypatch.setattr(
        application,
        "load_config",
        lambda *args, **kwargs: pytest.fail("config must not load"),
    )

    assert entrypoint.run(["--research-report"]) == 0


def test_normal_run_dispatches_to_bot_runner(monkeypatch: pytest.MonkeyPatch):
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(
        application,
        "run_bot",
        lambda actual_config, actual_logger: calls.append((actual_config, actual_logger)) or 7,
    )

    assert application.run([]) == 7
    assert calls == [(config, logger)]


def test_backtest_dispatches_to_research_runner(monkeypatch: pytest.MonkeyPatch):
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(
        application,
        "run_backtest",
        lambda actual_config, actual_logger: calls.append((actual_config, actual_logger)) or 8,
    )

    assert application.run(["--backtest"]) == 8
    assert calls == [(config, logger)]


def test_preview_dispatches_to_preview_runner(monkeypatch: pytest.MonkeyPatch):
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[tuple[object, object]] = []
    monkeypatch.setattr(
        application,
        "run_promoted_strategy_preview",
        lambda actual_config, actual_logger: calls.append((actual_config, actual_logger)) or 9,
    )

    assert application.run(["--preview-promoted-strategies"]) == 9
    assert calls == [(config, logger)]


def test_confirmed_paper_order_dispatches_to_paper_runner(monkeypatch: pytest.MonkeyPatch):
    config, logger = configure_main_dependencies(monkeypatch)
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        application,
        "run_paper_order_test",
        lambda **kwargs: calls.append(kwargs) or 10,
    )

    assert application.run(
        ["--paper-order-test", "AAPL", "buy", "1", "--confirm-paper-order"]
    ) == 10
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
