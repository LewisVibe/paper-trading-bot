from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.gateway_heartbeat import run_gateway_heartbeat  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run_gateway_heartbeat(root_dir=ROOT))
