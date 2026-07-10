from __future__ import annotations

import sys

from trading_bot.cli.entrypoint import run


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
