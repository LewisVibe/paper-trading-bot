from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

REQUIRED_COMMANDS = [
    "--backtest",
    "--compare-strategies",
    "--sma-sensitivity",
    "--trend-stress-test",
    "--etf-rotation-backtest",
    "--etf-rotation-robustness",
    "--build-etf-breadth-price-history",
    "--etf-breadth-regime-backtest",
    "--etf-breadth-regime-decision-report",
    "--etf-breadth-regime-robustness",
    "--adaptive-momentum-backtest",
    "--research-report",
    "--walk-forward-report",
    "--strategy-promotion-report",
    "--defensive-strategy-report",
    "--defensive-candidate-comparison",
    "--defensive-research-state-report",
    "--defensive-allocation-preview",
    "--defensive-allocation-risk-preview",
    "--defensive-allocation-decision-report",
    "--defensive-execution-readiness-report",
    "--drawdown-period-report",
    "--etf-defensive-drawdown-comparison",
    "--plot-etf-defensive-comparison",
    "--refresh-defensive-research",
    "--short-selling-readiness-report",
    "--short-hedge-backtest",
    "--short-strategy-lab",
    "--vol-managed-etf-backtest",
    "--vol-managed-etf-robustness",
    "--crypto-research-preview",
    "--crypto-strategy-lab",
    "--crypto-strategy-report",
    "--crypto-strategy-decision-report",
    "--crypto-cost-stress-report",
    "--crypto-robustness-report",
    "--crypto-period-diagnostics",
    "--preview-crypto-signals",
    "--show-crypto-monitor",
    "--crypto-research-state-report",
    "--preview-promoted-strategies",
    "--preview-promoted-actions",
    "--use-paper-positions-readonly",
    "--show-promoted-actions",
    "--promoted-risk-preview",
    "--show-promoted-risk",
    "--promoted-consensus-preview",
    "--promoted-decision-preview",
    "--show-promoted-decision",
    "--refresh-promoted-review",
    "--deployment-readiness-report",
    "--portfolio-risk-policy-report",
    "--show-portfolio-risk-policy",
    "--paper-kill-switch-readiness-report",
    "--paper-kill-switch-gate-report",
    "--paper-execution-protection-report",
    "--normal-bot-execution-policy-report",
    "--execution-eligibility-report",
    "--build-research-dashboard",
    "--preview-slow-sma-signals",
    "--preview-slow-sma-actions",
    "--execute-slow-sma-paper",
    "--confirm-slow-sma-paper",
    "--paper-order-test",
    "--confirm-paper-order",
]


def main() -> int:
    failures: list[str] = []
    try:
        result = subprocess.run(
            [PYTHON, "bot.py", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("Command inventory verification failed.")
        print("- python bot.py --help timed out")
        return 1

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0:
        failures.append(f"python bot.py --help failed with exit code {result.returncode}")

    for command in REQUIRED_COMMANDS:
        if command not in output:
            failures.append(f"missing command from help output: {command}")

    if "--paper-order-test" in output and "--confirm-paper-order" not in output:
        failures.append("--paper-order-test must remain paired with --confirm-paper-order in help output")
    if "--execute-slow-sma-paper" in output and "--confirm-slow-sma-paper" not in output:
        failures.append("--execute-slow-sma-paper must remain paired with --confirm-slow-sma-paper in help output")

    readonly_context = help_line_for(output, "--use-paper-positions-readonly").lower()
    if "--use-paper-positions-readonly" not in readonly_context:
        failures.append("--use-paper-positions-readonly help line was not found")
    else:
        for expected in ["preview", "without trading"]:
            if expected not in readonly_context:
                failures.append(f"--use-paper-positions-readonly help should mention {expected!r}")

    paper_order_context = help_line_for(output, "--paper-order-test").lower()
    if "paper" not in paper_order_context or "order" not in paper_order_context:
        failures.append("--paper-order-test help should clearly describe a paper order test")

    slow_sma_context = help_line_for(output, "--confirm-slow-sma-paper").lower()
    if "required" not in slow_sma_context:
        failures.append("--confirm-slow-sma-paper help should clearly say it is required")

    if failures:
        print("Command inventory verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Command inventory verification passed.")
    return 0


def help_line_for(output: str, command: str) -> str:
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if line.lstrip().startswith(command):
            context = [line]
            for next_line in lines[index + 1:]:
                stripped = next_line.strip()
                if stripped.startswith("--"):
                    break
                if stripped:
                    context.append(next_line)
            return " ".join(context)
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
