from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PATH = ROOT / "docs" / "HERMES_PROMOTED_REVIEW_CRON_DESIGN.md"
CANONICAL_DOC = "docs/HERMES_PROMOTED_REVIEW_REFRESH_CRON_DESIGN.md"
CANONICAL_VERIFIER = "python scripts\\verify_hermes_promoted_review_refresh_cron_design.py"


def main() -> int:
    text = read_text(LEGACY_PATH)
    normalized = normalize_text(text)
    required = [
        "legacy pointer only",
        CANONICAL_DOC,
        CANONICAL_VERIFIER,
        "does not approve scheduling, execution, orders, paper execution, live trading, or any cron changes",
    ]
    missing = [phrase for phrase in required if normalize_text(phrase) not in normalized]
    if missing:
        print("Legacy Hermes promoted review cron design verification failed:")
        for phrase in missing:
            print(f"- Missing phrase: {phrase}")
        return 1

    print("Legacy Hermes promoted review cron design verification passed.")
    print("Verified old promoted-review cron design doc points to the canonical refresh-specific design.")
    return 0


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def normalize_text(text: str) -> str:
    return " ".join(text.split())


if __name__ == "__main__":
    raise SystemExit(main())
