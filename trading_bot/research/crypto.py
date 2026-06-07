"""Research-only crypto preview helpers.

This module defines the first crypto research scaffold. It only writes a saved
CSV preview and does not fetch data, call Alpaca, read positions, or create
orders.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CRYPTO_RESEARCH_SYMBOLS = ["BTC/USD", "ETH/USD", "LTC/USD"]

CRYPTO_RESEARCH_COLUMNS = [
    "created_at",
    "symbol",
    "asset_class",
    "research_status",
    "execution_enabled",
    "shorting_enabled",
    "margin_enabled",
    "data_source_status",
    "fee_model_status",
    "notes",
    "research_only",
    "preview_only",
    "execution_approved",
]


@dataclass
class CryptoResearchPreviewResult:
    output_path: Path
    rows: list[dict[str, Any]]
    summary_lines: list[str]


def run_crypto_research_preview_files(
    data_dir: Path | str = "data",
    output_filename: str = "crypto_research_preview.csv",
) -> CryptoResearchPreviewResult:
    data_path = Path(data_dir)
    rows = build_crypto_research_preview_rows()
    output_path = data_path / output_filename
    write_crypto_research_preview(output_path, rows)
    return CryptoResearchPreviewResult(
        output_path=output_path,
        rows=rows,
        summary_lines=build_crypto_research_preview_summary(rows, output_path),
    )


def build_crypto_research_preview_rows(
    symbols: list[str] | None = None,
    created_at: str | None = None,
) -> list[dict[str, Any]]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    return [
        {
            "created_at": timestamp,
            "symbol": symbol,
            "asset_class": "crypto",
            "research_status": "research_candidate",
            "execution_enabled": False,
            "shorting_enabled": False,
            "margin_enabled": False,
            "data_source_status": "not_configured_research_scaffold",
            "fee_model_status": "not_configured_research_scaffold",
            "notes": "Research scaffold only. Crypto execution, shorting, and margin are disabled.",
            "research_only": True,
            "preview_only": True,
            "execution_approved": False,
        }
        for symbol in (symbols or CRYPTO_RESEARCH_SYMBOLS)
    ]


def write_crypto_research_preview(output_path: Path, rows: list[dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CRYPTO_RESEARCH_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CRYPTO_RESEARCH_COLUMNS})


def build_crypto_research_preview_summary(rows: list[dict[str, Any]], output_path: Path) -> list[str]:
    symbols = ", ".join(str(row["symbol"]) for row in rows)
    return [
        "CRYPTO RESEARCH ONLY. NOT EXECUTION.",
        f"Symbols previewed: {symbols}",
        "Execution enabled: false",
        "Shorting enabled: false",
        "Margin enabled: false",
        f"Saved crypto research preview to {output_path}",
    ]
