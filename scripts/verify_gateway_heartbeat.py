from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "trading_bot" / "gateway_heartbeat.py"
CONFIGURATOR = ROOT / "scripts" / "configure_gateway_heartbeat.py"
SENDER = ROOT / "scripts" / "send_gateway_heartbeat.py"
RUNBOOK = ROOT / "docs" / "HERMES_GATEWAY_HEARTBEAT.md"


def main() -> int:
    failures: list[str] = []
    module = read(MODULE)
    configurator = read(CONFIGURATOR)
    sender = read(SENDER)
    runbook = read(RUNBOOK)

    for path in [MODULE, CONFIGURATOR, SENDER, RUNBOOK]:
        if not path.exists():
            failures.append(f"missing heartbeat artifact: {path.relative_to(ROOT)}")
    for token in [
        "PAPER_BOT_HEARTBEAT_URL",
        ".env.gateway-heartbeat",
        'parsed.scheme.lower() != "https"',
        "HEARTBEAT_TIMEOUT_SECONDS = 10",
        "gateway_heartbeat=failed",
        "gateway_heartbeat=configuration_error",
    ]:
        if token not in module:
            failures.append(f"heartbeat module missing safety token: {token}")
    if "config.json" in module or "config.json" in sender:
        failures.append("heartbeat sender must not read bot config.json")
    if "getpass.getpass" not in configurator:
        failures.append("heartbeat configurator must hide interactive URL input")
    if "run_gateway_heartbeat" not in sender:
        failures.append("heartbeat sender is not wired to the isolated helper")
    for token in [
        "paper-bot-gateway-heartbeat",
        "*/5 * * * *",
        ".venv\\Scripts\\python.exe scripts\\send_gateway_heartbeat.py",
        "roughly 15",
        "external",
        "no output on success",
    ]:
        if token not in runbook:
            failures.append(f"heartbeat runbook missing: {token}")

    if failures:
        print("Gateway heartbeat verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Gateway heartbeat verification passed.")
    print("Verified private URL handling, HTTPS-only delivery, silent success, and external dead-man monitoring scope.")
    return 0


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
