"""Saved-output freshness helpers for VPS monitoring reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


FRESHNESS_FRESH_HOURS = 24
FRESHNESS_WARNING_HOURS = 72

FRESHNESS_OUTPUT_PATHS = [
    "data/promoted_review_refresh_summary.csv",
    "data/promoted_decision_preview.csv",
    "data/defensive_research_refresh_summary.csv",
    "data/market_monitor_scheduling_readiness_report.csv",
    "data/monitor_lockfile_readiness_report.csv",
]

FRESHNESS_LABELS = {"fresh", "warning_stale", "stale", "missing"}


@dataclass(frozen=True)
class FreshnessStatus:
    path: str
    label: str
    age_hours: float | None
    modified_at: str


def build_freshness_statuses(root: Path | str = ".", now: datetime | None = None) -> list[FreshnessStatus]:
    root_path = Path(root)
    checked_at = now or datetime.now(timezone.utc)
    return [freshness_for_path(root_path, path, checked_at) for path in FRESHNESS_OUTPUT_PATHS]


def freshness_for_path(root: Path, relative_path: str, now: datetime) -> FreshnessStatus:
    path = root / relative_path
    if not path.exists():
        return FreshnessStatus(relative_path, "missing", None, "missing")

    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_hours = max((now - modified).total_seconds() / 3600, 0.0)
    if age_hours <= FRESHNESS_FRESH_HOURS:
        label = "fresh"
    elif age_hours <= FRESHNESS_WARNING_HOURS:
        label = "warning_stale"
    else:
        label = "stale"
    return FreshnessStatus(relative_path, label, age_hours, modified.isoformat(timespec="seconds"))


def format_freshness_lines(statuses: list[FreshnessStatus]) -> list[str]:
    lines = []
    for status in statuses:
        age = "missing" if status.age_hours is None else f"{status.age_hours:.1f}h"
        lines.append(f"- {status.label}: {status.path}: age={age}; modified_at={status.modified_at}")
    return lines


def has_stale_or_missing(statuses: list[FreshnessStatus]) -> bool:
    return any(status.label in {"missing", "stale"} for status in statuses)


def has_warning(statuses: list[FreshnessStatus]) -> bool:
    return any(status.label == "warning_stale" for status in statuses)
