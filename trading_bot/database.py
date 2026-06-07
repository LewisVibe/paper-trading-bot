from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_bot.config import AppConfig


def init_database(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            ticker TEXT NOT NULL,
            signal TEXT NOT NULL,
            side TEXT,
            action TEXT,
            position_before TEXT,
            position_after TEXT,
            position_before_qty REAL,
            position_after_qty REAL,
            quantity REAL,
            last_close REAL,
            short_ma REAL,
            long_ma REAL,
            dry_run INTEGER NOT NULL,
            order_id TEXT,
            order_status TEXT,
            error TEXT
        )
        """
    )
    ensure_database_columns(conn)
    conn.commit()
    return conn


def ensure_database_columns(conn: sqlite3.Connection) -> None:
    existing_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(trade_log)").fetchall()
    }
    needed_columns = {
        "position_before_qty": "REAL",
        "position_after_qty": "REAL",
    }

    for column_name, column_type in needed_columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE trade_log ADD COLUMN {column_name} {column_type}")


def insert_trade_log(
    conn: sqlite3.Connection,
    config: AppConfig,
    ticker: str,
    signal: str,
    side: str = "",
    action: str = "",
    position_before: Any | None = None,
    position_after: Any | None = None,
    quantity: float | None = None,
    last_close: float | None = None,
    short_ma: float | None = None,
    long_ma: float | None = None,
    order_id: str = "",
    order_status: str = "",
    error: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO trade_log (
            created_at, ticker, signal, side, action, position_before, position_after,
            position_before_qty, position_after_qty, quantity, last_close, short_ma,
            long_ma, dry_run, order_id, order_status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now_utc(),
            ticker,
            signal,
            side,
            action,
            position_label(position_before),
            position_label(position_after),
            position_quantity(position_before),
            position_quantity(position_after),
            quantity,
            last_close,
            short_ma,
            long_ma,
            1 if config.dry_run else 0,
            order_id,
            order_status,
            error,
        ),
    )
    conn.commit()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def position_label(position: Any | None) -> str:
    if position is None:
        return "flat 0"
    label = getattr(position, "label", None)
    if callable(label):
        return str(label())
    return "flat 0"


def position_quantity(position: Any | None) -> float:
    if position is None:
        return 0.0
    return float(getattr(position, "quantity", 0))
