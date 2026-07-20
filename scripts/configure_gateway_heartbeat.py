from __future__ import annotations

import getpass
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trading_bot.gateway_heartbeat import (  # noqa: E402
    HeartbeatConfigurationError,
    save_heartbeat_url,
)


def main() -> int:
    value = getpass.getpass("Private HTTPS heartbeat URL (input hidden): ")
    try:
        path = save_heartbeat_url(value, root_dir=ROOT)
    except HeartbeatConfigurationError:
        print("Heartbeat configuration rejected: enter one valid HTTPS ping URL.", file=sys.stderr)
        return 2
    print(f"Heartbeat configuration saved privately to {path.name}; URL not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
