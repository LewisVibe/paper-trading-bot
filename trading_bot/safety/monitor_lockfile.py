"""Pure no-network lockfile decisions for future monitor refresh protection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


LOCK_VERSION = "monitor_lockfile_v1"

SAFE_LOCK_COMMAND_NAMES = frozenset(
    {
        "--refresh-promoted-review",
        "--refresh-defensive-research",
        "--monitor-lockfile-readiness-report",
        "--show-promoted-decision",
        "--show-crypto-monitor",
    }
)

ALLOWED_LOCK_METADATA_FIELDS = frozenset(
    {
        "command_name",
        "started_at",
        "hostname",
        "pid",
        "lock_version",
        "stale_after_seconds",
    }
)

FORBIDDEN_LOCK_FIELD_FRAGMENTS = (
    "api_key",
    "secret",
    "token",
    "webhook",
    "account_id",
    "order_id",
    "config",
    "database",
    "log",
    "trade_history",
    "csv_contents",
)

FORBIDDEN_LOCK_VALUE_FRAGMENTS = FORBIDDEN_LOCK_FIELD_FRAGMENTS + (
    "alpaca",
    "discord",
    "bearer ",
    "authorization",
)

BLOCKED_COMMAND_FRAGMENTS = (
    "paper-order-test",
    "confirm-paper-order",
    "execute-slow-sma-paper",
    "confirm-slow-sma-paper",
    "execute",
    "order",
    "submit",
    "cancel",
)


@dataclass(frozen=True)
class LockMetadata:
    command_name: str
    started_at: str
    hostname: str
    pid: int
    lock_version: str = LOCK_VERSION
    stale_after_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_name": self.command_name,
            "started_at": self.started_at,
            "hostname": self.hostname,
            "pid": self.pid,
            "lock_version": self.lock_version,
            "stale_after_seconds": self.stale_after_seconds,
        }


@dataclass(frozen=True)
class LockDecision:
    allowed: bool
    status: str
    reasons: list[str]
    required_next_step: str
    execution_approved: bool = False
    scheduling_approved: bool = False


def build_lock_metadata(
    command_name: str,
    started_at: datetime | str,
    hostname: str,
    pid: int,
    stale_after_seconds: int | None = None,
) -> LockMetadata:
    started_at_value = started_at.isoformat() if isinstance(started_at, datetime) else started_at
    return LockMetadata(
        command_name=command_name,
        started_at=started_at_value,
        hostname=hostname,
        pid=pid,
        stale_after_seconds=stale_after_seconds,
    )


def validate_lock_metadata(
    metadata: LockMetadata | Mapping[str, Any],
    allowed_command_names: set[str] | frozenset[str] = SAFE_LOCK_COMMAND_NAMES,
) -> LockDecision:
    metadata_dict = metadata.to_dict() if isinstance(metadata, LockMetadata) else dict(metadata)
    reasons: list[str] = []

    unexpected_fields = sorted(set(metadata_dict) - ALLOWED_LOCK_METADATA_FIELDS)
    if unexpected_fields:
        reasons.append("unexpected metadata fields: " + ", ".join(unexpected_fields))

    missing_fields = sorted({"command_name", "started_at", "hostname", "pid", "lock_version"} - set(metadata_dict))
    if missing_fields:
        reasons.append("missing metadata fields: " + ", ".join(missing_fields))

    for key, value in metadata_dict.items():
        key_lower = str(key).lower()
        if any(fragment in key_lower for fragment in FORBIDDEN_LOCK_FIELD_FRAGMENTS):
            reasons.append(f"forbidden metadata field: {key}")
        if _contains_forbidden_value(value):
            reasons.append(f"forbidden metadata value in field: {key}")

    command_name = str(metadata_dict.get("command_name", ""))
    reasons.extend(_command_rejection_reasons(command_name, allowed_command_names))

    if metadata_dict.get("lock_version") != LOCK_VERSION:
        reasons.append("unsupported lock_version")

    pid = metadata_dict.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        reasons.append("pid must be a positive integer")

    stale_after_seconds = metadata_dict.get("stale_after_seconds")
    if stale_after_seconds is not None and (
        not isinstance(stale_after_seconds, int) or stale_after_seconds <= 0
    ):
        reasons.append("stale_after_seconds must be a positive integer when provided")

    started_at = _parse_started_at(metadata_dict.get("started_at"))
    if started_at is None:
        reasons.append("started_at must be a valid ISO timestamp")

    if reasons:
        return _decision(
            False,
            "invalid_metadata_requires_manual_review",
            reasons,
            "Review lock metadata manually; do not run or delete locks automatically.",
        )

    return _decision(
        True,
        "metadata_valid",
        ["metadata is valid for future safe lock use"],
        "Use this metadata only in a separately reviewed lock implementation.",
    )


def evaluate_existing_lock(
    existing_metadata: LockMetadata | Mapping[str, Any] | None,
    now: datetime,
    allowed_command_names: set[str] | frozenset[str] = SAFE_LOCK_COMMAND_NAMES,
) -> LockDecision:
    if existing_metadata is None:
        return _decision(
            True,
            "no_existing_lock",
            ["no existing lock metadata supplied"],
            "A future runtime helper may proceed only after separate integration review.",
        )

    validation = validate_lock_metadata(existing_metadata, allowed_command_names)
    if not validation.allowed:
        return _decision(
            False,
            "malformed_existing_lock_blocks",
            validation.reasons,
            "Stop and request manual review; do not delete malformed locks automatically.",
        )

    metadata_dict = existing_metadata.to_dict() if isinstance(existing_metadata, LockMetadata) else dict(existing_metadata)
    started_at = _parse_started_at(metadata_dict.get("started_at"))
    stale_after_seconds = metadata_dict.get("stale_after_seconds")
    if started_at is None:
        return _decision(
            False,
            "malformed_existing_lock_blocks",
            ["started_at must be a valid ISO timestamp"],
            "Stop and request manual review; do not delete malformed locks automatically.",
        )

    age_seconds = (now.astimezone(timezone.utc) - started_at.astimezone(timezone.utc)).total_seconds()
    if age_seconds < 0:
        return _decision(
            False,
            "malformed_existing_lock_blocks",
            ["existing lock started_at is in the future"],
            "Stop and request manual review; do not delete future-dated locks automatically.",
        )

    if stale_after_seconds is not None and age_seconds > stale_after_seconds:
        return _decision(
            False,
            "stale_requires_manual_review",
            ["existing lock is older than stale_after_seconds"],
            "Request manual review; v1 helper must not silently delete stale locks.",
        )

    return _decision(
        False,
        "fresh_existing_lock_blocks",
        ["existing lock is present and not stale"],
        "Wait for the current safe refresh/report/display command to finish.",
    )


def _decision(allowed: bool, status: str, reasons: list[str], required_next_step: str) -> LockDecision:
    return LockDecision(
        allowed=allowed,
        status=status,
        reasons=reasons,
        required_next_step=required_next_step,
        execution_approved=False,
        scheduling_approved=False,
    )


def _parse_started_at(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _contains_forbidden_value(value: Any) -> bool:
    if value is None:
        return False
    value_lower = str(value).lower()
    return any(fragment in value_lower for fragment in FORBIDDEN_LOCK_VALUE_FRAGMENTS)


def _command_rejection_reasons(
    command_name: str,
    allowed_command_names: set[str] | frozenset[str],
) -> list[str]:
    command_lower = command_name.strip().lower()
    if not command_lower:
        return ["command_name is required"]
    if command_lower in {"python bot.py", "bot.py"}:
        return ["normal python bot.py must not use monitor lock helper"]
    reasons = []
    if command_name not in allowed_command_names:
        reasons.append("command_name is not in safe lock allowlist")
    if any(fragment in command_lower for fragment in BLOCKED_COMMAND_FRAGMENTS):
        reasons.append("command_name matches blocked execution-capable pattern")
    return reasons
