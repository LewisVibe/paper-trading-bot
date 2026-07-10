from __future__ import annotations

from trading_bot.cli.report_only import dispatch_early_command


def run(argv: list[str]) -> int | None:
    """Run an early CLI route, or return None so the compatibility entry point continues."""
    return dispatch_early_command(argv)
