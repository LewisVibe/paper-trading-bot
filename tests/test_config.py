import json

import pytest

from trading_bot.config import ConfigError, load_config


def write_config(tmp_path, **overrides):
    data = {
        "tickers": ["AAPL"],
        "short_window": 20,
        "long_window": 50,
        "history_period": "6mo",
        "history_interval": "1d",
        "order_quantity": 1,
        "dry_run": True,
        "allow_shorting": False,
        "database_path": "trades.db",
        "log_file": "bot.log",
        "discord": {"enabled": False, "webhook_url": ""},
        "alpaca": {"paper": True, "api_key": "", "secret_key": ""},
    }
    data.update(overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_paper_kill_switch_enabled_defaults_false(tmp_path, monkeypatch):
    monkeypatch.delenv("PAPER_KILL_SWITCH_ENABLED", raising=False)

    config = load_config(write_config(tmp_path), force_dry_run=False)

    assert config.paper_kill_switch_enabled is False


def test_paper_kill_switch_enabled_loads_from_config(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_KILL_SWITCH_ENABLED", "false")

    config = load_config(
        write_config(tmp_path, paper_kill_switch_enabled=True),
        force_dry_run=False,
    )

    assert config.paper_kill_switch_enabled is True


def test_paper_kill_switch_enabled_loads_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_KILL_SWITCH_ENABLED", "true")

    config = load_config(write_config(tmp_path), force_dry_run=False)

    assert config.paper_kill_switch_enabled is True


def test_validate_config_rejects_live_alpaca_mode(tmp_path):
    with pytest.raises(ConfigError, match="alpaca.paper must be true"):
        load_config(
            write_config(tmp_path, alpaca={"paper": False, "api_key": "", "secret_key": ""}),
            force_dry_run=False,
        )
