from __future__ import annotations

from trading_bot.cli.report_only import dispatch_early_command


def run(argv: list[str]) -> int:
    """Run the CLI while keeping report-only routes isolated from heavy dependencies."""
    early_exit_code = dispatch_early_command(argv)
    if early_exit_code is not None:
        return early_exit_code

    from trading_bot.cli.application import run as run_application

    return run_application(argv)
