from __future__ import annotations

import fnmatch
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GIT_EXECUTABLE = shutil.which("git") or next(
    (
        str(path)
        for path in [
            Path("C:/Program Files/Git/bin/git.exe"),
            Path("C:/Program Files/Git/cmd/git.exe"),
            Path("C:/Program Files (x86)/Git/bin/git.exe"),
            Path("C:/Program Files (x86)/Git/cmd/git.exe"),
        ]
        if path.exists()
    ),
    None,
)

REQUIRED_GITIGNORE_PATTERNS = [
    "config.json",
    ".env",
    ".env.*",
    ".venv/",
    "logs/*",
    "!logs/.gitkeep",
    "*.log",
    "data/*",
    "!data/.gitkeep",
    "*.db",
]

DANGEROUS_PATH_PATTERNS = [
    "config.json",
    ".env",
    ".env.*",
    ".venv/*",
    "data/*.db",
    "data/*.csv",
    "data/charts/*",
    "logs/*.log",
]

SECRET_MARKERS = [
    "secret",
    "api_key",
    "webhook",
    "token",
    "password",
    "credentials",
]

ALLOWED_PLACEHOLDERS = {
    "data/.gitkeep",
    "logs/.gitkeep",
}


def main() -> int:
    print("REPO SAFETY VERIFICATION")
    failures: list[str] = []
    warnings: list[str] = []

    try:
        tracked_files = git_lines(["ls-files"])
        staged_files = git_lines(["diff", "--cached", "--name-only"])
        status_lines = git_lines(["status", "--short"])
    except RuntimeError as exc:
        print(f"FAILED: {exc}")
        print("Result: failed")
        return 1

    tracked_dangerous = dangerous_paths(tracked_files)
    staged_dangerous = dangerous_paths(staged_files)
    untracked_dangerous = dangerous_untracked_paths(status_lines)
    missing_gitignore = missing_required_gitignore_patterns(ROOT / ".gitignore")

    print_dangerous_section("Tracked dangerous files", tracked_dangerous)
    print_dangerous_section("Staged dangerous files", staged_dangerous)

    if untracked_dangerous:
        warnings.append("Dangerous-looking untracked files exist. If they are ignored by .gitignore, this is only a warning.")
        print("Dangerous untracked files: warning")
        for path in untracked_dangerous:
            print(f"- {path}")
    else:
        print("Dangerous untracked files: none")

    if missing_gitignore:
        print("Required .gitignore patterns: failed")
        for pattern in missing_gitignore:
            print(f"- missing {pattern}")
    else:
        print("Required .gitignore patterns: pass")

    if tracked_dangerous:
        failures.append("tracked dangerous files found")
    if staged_dangerous:
        failures.append("staged dangerous files found")
    if missing_gitignore:
        failures.append("required .gitignore patterns missing")

    if failures:
        print("")
        print("Suggested fixes:")
        for path in sorted(set(tracked_dangerous + staged_dangerous)):
            print(f"- If already tracked: git rm --cached {path}")
        print("- If the file should never be committed, add or confirm the matching .gitignore pattern.")
        print("Result: failed")
        return 1

    for warning in warnings:
        print(f"Warning: {warning}")
    print("Result: passed")
    return 0


def git_lines(args: list[str]) -> list[str]:
    if GIT_EXECUTABLE is None:
        raise RuntimeError("git is not available on PATH or common Windows install paths; repo safety cannot be verified.")
    command = [GIT_EXECUTABLE, *args]
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git is not available; repo safety cannot be verified.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git {' '.join(args)} timed out.") from exc
    if result.returncode != 0:
        output = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {output}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def dangerous_paths(paths: list[str]) -> list[str]:
    return sorted(path for path in normalize_paths(paths) if is_dangerous_path(path))


def dangerous_untracked_paths(status_lines: list[str]) -> list[str]:
    paths: list[str] = []
    for line in status_lines:
        if not line.startswith("?? "):
            continue
        path = line[3:].strip()
        if is_dangerous_path(normalize_path(path)):
            paths.append(normalize_path(path))
    return sorted(paths)


def is_dangerous_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in ALLOWED_PLACEHOLDERS:
        return False
    if any(fnmatch.fnmatch(normalized, pattern) for pattern in DANGEROUS_PATH_PATTERNS):
        return True
    lower_path = normalized.lower()
    return any(marker in lower_path for marker in SECRET_MARKERS)


def missing_required_gitignore_patterns(path: Path) -> list[str]:
    if not path.exists():
        return REQUIRED_GITIGNORE_PATTERNS[:]
    lines = {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return [pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in lines]


def print_dangerous_section(label: str, paths: list[str]) -> None:
    if not paths:
        print(f"{label}: none")
        return
    print(f"{label}: failed")
    for path in paths:
        print(f"- {path}")


def normalize_paths(paths: list[str]) -> list[str]:
    return [normalize_path(path) for path in paths]


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


if __name__ == "__main__":
    raise SystemExit(main())
