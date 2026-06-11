from __future__ import annotations

import inspect
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import trading_bot.safety.monitor_lockfile as monitor_lockfile
from trading_bot.safety.monitor_lockfile import (
    LOCK_VERSION,
    SAFE_LOCK_COMMAND_NAMES,
    acquire_monitor_lock,
    build_lock_metadata,
    evaluate_existing_lock,
    release_monitor_lock,
    validate_lock_metadata,
)


NOW = datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)


def main() -> int:
    failures: list[str] = []
    verify_helper_source_is_pure(failures)
    verify_safe_command_metadata_passes(failures)
    verify_forbidden_command_metadata_blocks(failures)
    verify_forbidden_metadata_fields_block(failures)
    verify_forbidden_secret_like_values_block(failures)
    verify_fresh_existing_lock_blocks(failures)
    verify_stale_existing_lock_requires_manual_review(failures)
    verify_malformed_metadata_blocks(failures)
    verify_no_existing_lock_decision_is_non_executing(failures)
    verify_lock_acquire_release_uses_temp_files_and_cleans_up(failures)
    verify_lock_acquire_blocks_fresh_existing_file(failures)
    verify_lock_acquire_blocks_stale_existing_file(failures)
    verify_lock_acquire_blocks_malformed_existing_file(failures)

    if failures:
        print("Monitor lockfile helper verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Monitor lockfile helper verification passed.")
    print("Verified pure helper decisions, metadata validation, stale-lock policy, blocked commands, and approval flags.")
    return 0


def verify_helper_source_is_pure(failures: list[str]) -> None:
    source = inspect.getsource(monitor_lockfile)
    forbidden_terms = [
        "requests",
        "urllib",
        "http.client",
        "socket",
        "yfinance",
        "sqlite3",
    ]
    for term in forbidden_terms:
        if term in source:
            failures.append(f"helper must remain no-network/no-trading/no-database; found {term}")


def verify_safe_command_metadata_passes(failures: list[str]) -> None:
    metadata = build_lock_metadata(
        "--refresh-promoted-review",
        NOW,
        "vps-host",
        1234,
        stale_after_seconds=900,
    )
    decision = validate_lock_metadata(metadata)
    expect_decision(decision, True, "metadata_valid", failures, "safe command metadata")


def verify_forbidden_command_metadata_blocks(failures: list[str]) -> None:
    blocked_commands = [
        "python bot.py",
        "--paper-order-test",
        "--confirm-paper-order",
        "--execute-slow-sma-paper",
        "--confirm-slow-sma-paper",
        "--future-execute-orders",
    ]
    for command_name in blocked_commands:
        metadata = build_lock_metadata(command_name, NOW, "vps-host", 1234)
        decision = validate_lock_metadata(metadata)
        if decision.allowed:
            failures.append(f"blocked command should not be allowed: {command_name}")
        assert_false_flags(decision, failures, f"blocked command {command_name}")


def verify_forbidden_metadata_fields_block(failures: list[str]) -> None:
    metadata = {
        "command_name": "--refresh-promoted-review",
        "started_at": NOW.isoformat(),
        "hostname": "vps-host",
        "pid": 1234,
        "lock_version": LOCK_VERSION,
        "api_key": "redacted",
    }
    decision = validate_lock_metadata(metadata)
    if decision.allowed or decision.status != "invalid_metadata_requires_manual_review":
        failures.append("forbidden metadata field should block with manual-review status")
    assert_false_flags(decision, failures, "forbidden metadata fields")


def verify_forbidden_secret_like_values_block(failures: list[str]) -> None:
    metadata = {
        "command_name": "--refresh-promoted-review",
        "started_at": NOW.isoformat(),
        "hostname": "discord webhook value should not be here",
        "pid": 1234,
        "lock_version": LOCK_VERSION,
    }
    decision = validate_lock_metadata(metadata)
    if decision.allowed or decision.status != "invalid_metadata_requires_manual_review":
        failures.append("forbidden secret-like value should block with manual-review status")
    assert_false_flags(decision, failures, "forbidden secret-like values")


def verify_fresh_existing_lock_blocks(failures: list[str]) -> None:
    metadata = build_lock_metadata(
        "--show-crypto-monitor",
        NOW - timedelta(seconds=120),
        "vps-host",
        1234,
        stale_after_seconds=900,
    )
    decision = evaluate_existing_lock(metadata, NOW)
    expect_decision(decision, False, "fresh_existing_lock_blocks", failures, "fresh existing lock")


def verify_stale_existing_lock_requires_manual_review(failures: list[str]) -> None:
    metadata = build_lock_metadata(
        "--show-crypto-monitor",
        NOW - timedelta(seconds=1200),
        "vps-host",
        1234,
        stale_after_seconds=900,
    )
    decision = evaluate_existing_lock(metadata, NOW)
    expect_decision(decision, False, "stale_requires_manual_review", failures, "stale existing lock")
    if "silently delete" not in decision.required_next_step.lower():
        failures.append("stale lock decision should explicitly refuse silent deletion")


def verify_malformed_metadata_blocks(failures: list[str]) -> None:
    malformed_cases = [
        {"command_name": "--show-crypto-monitor"},
        build_lock_metadata("--show-crypto-monitor", "not-a-date", "vps-host", 1234),
        build_lock_metadata("--show-crypto-monitor", NOW + timedelta(seconds=30), "vps-host", 1234),
        build_lock_metadata("--unknown-report", NOW, "vps-host", 1234),
    ]
    for metadata in malformed_cases:
        decision = evaluate_existing_lock(metadata, NOW)
        if decision.allowed:
            failures.append(f"malformed/unknown metadata should block: {metadata}")
        if decision.status not in {"malformed_existing_lock_blocks"}:
            failures.append(f"malformed metadata should use malformed_existing_lock_blocks, got {decision.status}")
        assert_false_flags(decision, failures, f"malformed metadata {metadata}")


def verify_no_existing_lock_decision_is_non_executing(failures: list[str]) -> None:
    decision = evaluate_existing_lock(None, NOW)
    expect_decision(decision, True, "no_existing_lock", failures, "no existing lock")


def verify_lock_acquire_release_uses_temp_files_and_cleans_up(failures: list[str]) -> None:
    for command_name in [
        "--monitor-lockfile-readiness-report",
        "--refresh-promoted-review",
        "--refresh-defensive-research",
    ]:
        with tempfile.TemporaryDirectory() as tmpdir:
            lock_path = Path(tmpdir) / "monitor.lock"
            acquire_result = acquire_monitor_lock(
                lock_path,
                command_name,
                now=NOW,
                hostname="vps-host",
                pid=1234,
                stale_after_seconds=900,
            )
            expect_decision(acquire_result.decision, True, "lock_acquired", failures, f"lock acquire {command_name}")
            if not acquire_result.acquired:
                failures.append(f"lock acquire should mark acquired=True for {command_name}")
                continue
            if not lock_path.exists():
                failures.append(f"lock acquire should create a temp lock file for {command_name}")
            release_decision = release_monitor_lock(lock_path, acquire_result.metadata)
            expect_decision(release_decision, True, "lock_released", failures, f"lock release {command_name}")
            if lock_path.exists():
                failures.append(f"lock release should clean up the temp lock file for {command_name}")


def verify_lock_acquire_blocks_fresh_existing_file(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "monitor.lock"
        metadata = build_lock_metadata(
            "--monitor-lockfile-readiness-report",
            NOW - timedelta(seconds=120),
            "vps-host",
            1234,
            stale_after_seconds=900,
        )
        lock_path.write_text(json.dumps(metadata.to_dict()), encoding="utf-8")
        acquire_result = acquire_monitor_lock(lock_path, "--monitor-lockfile-readiness-report", now=NOW)
        expect_decision(
            acquire_result.decision,
            False,
            "fresh_existing_lock_blocks",
            failures,
            "fresh existing lock file",
        )
        if acquire_result.acquired:
            failures.append("fresh existing lock file should not be acquired")
        if not lock_path.exists():
            failures.append("fresh existing lock file should not be removed")


def verify_lock_acquire_blocks_stale_existing_file(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "monitor.lock"
        metadata = build_lock_metadata(
            "--monitor-lockfile-readiness-report",
            NOW - timedelta(seconds=1200),
            "vps-host",
            1234,
            stale_after_seconds=900,
        )
        lock_path.write_text(json.dumps(metadata.to_dict()), encoding="utf-8")
        acquire_result = acquire_monitor_lock(lock_path, "--monitor-lockfile-readiness-report", now=NOW)
        expect_decision(
            acquire_result.decision,
            False,
            "stale_requires_manual_review",
            failures,
            "stale existing lock file",
        )
        if acquire_result.acquired:
            failures.append("stale existing lock file should not be acquired")
        if not lock_path.exists():
            failures.append("stale existing lock file should not be silently removed")


def verify_lock_acquire_blocks_malformed_existing_file(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_path = Path(tmpdir) / "monitor.lock"
        lock_path.write_text("not-json", encoding="utf-8")
        acquire_result = acquire_monitor_lock(lock_path, "--monitor-lockfile-readiness-report", now=NOW)
        expect_decision(
            acquire_result.decision,
            False,
            "malformed_existing_lock_blocks",
            failures,
            "malformed existing lock file",
        )
        if acquire_result.acquired:
            failures.append("malformed existing lock file should not be acquired")
        if not lock_path.exists():
            failures.append("malformed existing lock file should not be silently removed")


def expect_decision(decision, allowed: bool, status: str, failures: list[str], label: str) -> None:
    if decision.allowed is not allowed:
        failures.append(f"{label}: expected allowed={allowed}, got {decision.allowed}")
    if decision.status != status:
        failures.append(f"{label}: expected status={status}, got {decision.status}")
    if not decision.reasons:
        failures.append(f"{label}: decision should include reasons")
    if not decision.required_next_step:
        failures.append(f"{label}: decision should include required_next_step")
    assert_false_flags(decision, failures, label)


def assert_false_flags(decision, failures: list[str], label: str) -> None:
    if decision.execution_approved is not False:
        failures.append(f"{label}: execution_approved must remain False")
    if decision.scheduling_approved is not False:
        failures.append(f"{label}: scheduling_approved must remain False")


if __name__ == "__main__":
    sys.exit(main())
