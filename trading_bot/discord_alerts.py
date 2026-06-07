"""Discord webhook alert helpers for the paper trading bot."""

from __future__ import annotations

import logging
import re

import requests

from trading_bot.config import AppConfig


DISCORD_WEBHOOK_PATTERN = re.compile(
    r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/api/webhooks/[^\s)\"']+",
    re.IGNORECASE,
)
DISCORD_WEBHOOK_PATH_PATTERN = re.compile(r"/api/webhooks/[^\s)\"']+", re.IGNORECASE)


def redact_discord_webhook(value: str) -> str:
    """Remove webhook URLs from text before writing Discord failures to logs."""
    redacted = DISCORD_WEBHOOK_PATTERN.sub(
        "https://discord.com/api/webhooks/[REDACTED]",
        value,
    )
    return DISCORD_WEBHOOK_PATH_PATTERN.sub("/api/webhooks/[REDACTED]", redacted)


def send_discord_alert(config: AppConfig, logger: logging.Logger, message: str) -> None:
    if not config.discord_enabled:
        return

    content = message if len(message) <= 1900 else message[:1900] + "..."
    try:
        response = requests.post(
            config.discord_webhook_url,
            json={"content": content},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Discord alert failed: %s", redact_discord_webhook(str(exc)))
