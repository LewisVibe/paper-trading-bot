"""Secret-safe external heartbeat for detecting a stopped Hermes gateway."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


HEARTBEAT_ENV_NAME = "PAPER_BOT_HEARTBEAT_URL"
HEARTBEAT_ENV_FILE = Path(".env.gateway-heartbeat")
HEARTBEAT_TIMEOUT_SECONDS = 10


class HeartbeatConfigurationError(ValueError):
    """Raised when no valid private HTTPS heartbeat URL is configured."""


def validate_heartbeat_url(value: str) -> str:
    url = str(value or "").strip()
    parsed = urlsplit(url)
    if (
        len(url) > 2048
        or parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.fragment)
    ):
        raise HeartbeatConfigurationError("heartbeat URL must be an HTTPS URL without embedded credentials")
    return url


def load_heartbeat_url(
    *,
    root_dir: Path | str = ".",
    environ: Mapping[str, str] | None = None,
) -> str:
    environment = os.environ if environ is None else environ
    environment_value = str(environment.get(HEARTBEAT_ENV_NAME, "")).strip()
    if environment_value:
        return validate_heartbeat_url(environment_value)

    path = Path(root_dir) / HEARTBEAT_ENV_FILE
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HeartbeatConfigurationError("private heartbeat configuration is missing") from exc
    prefix = f"{HEARTBEAT_ENV_NAME}="
    matches = [line[len(prefix):].strip() for line in lines if line.startswith(prefix)]
    if len(matches) != 1:
        raise HeartbeatConfigurationError("private heartbeat configuration is invalid")
    return validate_heartbeat_url(matches[0])


def save_heartbeat_url(value: str, *, root_dir: Path | str = ".") -> Path:
    url = validate_heartbeat_url(value)
    root = Path(root_dir)
    path = root / HEARTBEAT_ENV_FILE
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(f"{HEARTBEAT_ENV_NAME}={url}\n", encoding="utf-8")
    try:
        temporary.chmod(0o600)
    except OSError:
        pass
    temporary.replace(path)
    return path


def run_gateway_heartbeat(
    *,
    root_dir: Path | str = ".",
    environ: Mapping[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
    stderr: TextIO = sys.stderr,
) -> int:
    try:
        heartbeat_url = load_heartbeat_url(root_dir=root_dir, environ=environ)
    except HeartbeatConfigurationError:
        print("gateway_heartbeat=configuration_error", file=stderr)
        return 2

    request = Request(
        heartbeat_url,
        method="GET",
        headers={"User-Agent": "paper-trading-bot-gateway-heartbeat/1"},
    )
    try:
        response = opener(request, timeout=HEARTBEAT_TIMEOUT_SECONDS)
        with response:
            status = int(getattr(response, "status", response.getcode()))
            if not 200 <= status < 300:
                raise OSError("heartbeat endpoint returned a non-success status")
            if urlsplit(heartbeat_url).hostname == "hc-ping.com":
                body = response.read(32)
                if body.strip() != b"OK":
                    raise OSError("Healthchecks did not confirm the ping")
    except Exception:  # noqa: BLE001 - never expose a token-bearing URL in a traceback
        print("gateway_heartbeat=failed", file=stderr)
        return 1
    return 0
