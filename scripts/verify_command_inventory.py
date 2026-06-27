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
    "--short-leverage-research-lab",
    "--show-short-leverage-research-lab",
    "--qqq-leverage-validation-report",
    "--show-qqq-leverage-validation-report",
    "--qqq-adaptive-leverage-lab",
    "--show-qqq-adaptive-leverage-lab",
    "--qqq-lead-decision-report",
    "--show-qqq-lead-decision-report",
    "--qqq-trend-gate-manual-review-pack",
    "--show-qqq-trend-gate-manual-review-pack",
    "--qqq-preview-candidate-readiness-report",
    "--show-qqq-preview-candidate-readiness-report",
    "--qqq100-preview-candidate-readiness-pack",
    "--show-qqq100-preview-candidate-readiness-pack",
    "--qqq100-preview-signal-pack",
    "--show-qqq100-preview-signal-pack",
    "--qqq100-action-preview",
    "--show-qqq100-action-preview",
    "--multi-strategy-portfolio-preview",
    "--show-multi-strategy-portfolio-preview",
    "--qqq100-paper-readiness-blocker-report",
    "--show-qqq100-paper-readiness-blocker-report",
    "--qqq100-paper-execution-readiness-report",
    "--show-qqq100-paper-execution-readiness-report",
    "--paper-live-promotion-gate",
    "--show-paper-live-promotion-gate",
    "--paper-live-readiness-report",
    "--show-paper-live-readiness-report",
    "--paper-live-state-summary",
    "--show-paper-live-state-summary",
    "--paper-live-evidence-audit",
    "--show-paper-live-evidence-audit",
    "--qqq100-postcheck-readiness-report",
    "--show-qqq100-postcheck-readiness-report",
    "--qqq100-followup-policy-report",
    "--show-qqq100-followup-policy-report",
    "--qqq100-daily-decision-report",
    "--show-qqq100-daily-decision-report",
    "--qqq100-manual-flatten-readiness-report",
    "--show-qqq100-manual-flatten-readiness-report",
    "--qqq100-manual-flatten-runbook-report",
    "--show-qqq100-manual-flatten-runbook-report",
    "--paper-live-monitoring-status",
    "--show-paper-live-monitoring-status",
    "--paper-live-checklist-status",
    "--show-paper-live-checklist-status",
    "--paper-live-f6-f7-audit",
    "--show-paper-live-f6-f7-audit",
    "--paper-live-promotion-ladder-design",
    "--show-paper-live-promotion-ladder-design",
    "--paper-live-promotion-ladder-status",
    "--show-paper-live-promotion-ladder-status",
    "--paper-live-f7-accounting-proof",
    "--show-paper-live-f7-accounting-proof",
    "--paper-live-next-ladder-candidate-scope",
    "--show-paper-live-next-ladder-candidate-scope",
    "--paper-live-defensive-sleeve-ladder-scope-review",
    "--show-paper-live-defensive-sleeve-ladder-scope-review",
    "--paper-live-defensive-sleeve-manual-review",
    "--show-paper-live-defensive-sleeve-manual-review",
    "--paper-live-defensive-sleeve-preview-readiness",
    "--show-paper-live-defensive-sleeve-preview-readiness",
    "--paper-live-defensive-sleeve-evidence-quality",
    "--show-paper-live-defensive-sleeve-evidence-quality",
    "--paper-live-multi-sleeve-roadmap",
    "--show-paper-live-multi-sleeve-roadmap",
    "--paper-live-next-phase-backlog",
    "--show-paper-live-next-phase-backlog",
    "--paper-live-multi-sleeve-evidence-gap",
    "--show-paper-live-multi-sleeve-evidence-gap",
    "--paper-live-high-growth-evidence-gap",
    "--show-paper-live-high-growth-evidence-gap",
    "--paper-live-high-growth-evidence-quality",
    "--show-paper-live-high-growth-evidence-quality",
    "--paper-live-high-growth-manual-review-decision",
    "--show-paper-live-high-growth-manual-review-decision",
    "--qqq100-paper-postcheck",
    "--show-qqq100-paper-postcheck",
    "--qqq100-repeat-alignment-workflow-design",
    "--show-qqq100-repeat-alignment-workflow-design",
    "--multi-sleeve-strategy-monitor",
    "--show-multi-sleeve-strategy-monitor",
    "--sleeve-research-scoreboard",
    "--show-sleeve-research-scoreboard",
    "--codex-qqq-defensive-crash-gate-research-pack",
    "--show-codex-qqq-defensive-crash-gate-research-pack",
    "--sleeve-return-streams",
    "--show-sleeve-return-streams",
    "--qqq100-stream-reconciliation",
    "--show-qqq100-stream-reconciliation",
    "--qqq100-benchmark-inputs-report",
    "--show-qqq100-benchmark-inputs",
    "--high-growth-return-streams",
    "--show-high-growth-return-streams",
    "--crypto-return-streams",
    "--show-crypto-return-streams",
    "--multi-sleeve-portfolio-backtest",
    "--show-multi-sleeve-portfolio-backtest",
    "--multi-sleeve-robustness",
    "--show-multi-sleeve-robustness",
    "--multi-sleeve-crypto-review",
    "--show-multi-sleeve-crypto-review",
    "--multi-sleeve-crypto-containment-review",
    "--show-multi-sleeve-crypto-containment-review",
    "--multi-sleeve-allocation-policy-review",
    "--show-multi-sleeve-allocation-policy-review",
    "--multi-sleeve-weight-sensitivity",
    "--show-multi-sleeve-weight-sensitivity",
    "--multi-sleeve-higher-growth-review",
    "--show-multi-sleeve-higher-growth-review",
    "--multi-sleeve-research-lead-decision",
    "--show-multi-sleeve-research-lead-decision",
    "--multi-sleeve-lead-state-refresh",
    "--show-multi-sleeve-lead-state",
    "--multi-sleeve-high-growth-drawdown-decomposition",
    "--show-multi-sleeve-high-growth-drawdown-decomposition",
    "--high-growth-sleeve-quality-review",
    "--show-high-growth-sleeve-quality-review",
    "--high-growth-component-attribution",
    "--show-high-growth-component-attribution",
    "--high-growth-component-streams",
    "--show-high-growth-component-streams",
    "--high-growth-sleeve-concentration-review",
    "--show-high-growth-sleeve-concentration-review",
    "--high-growth-research-checkpoint",
    "--show-high-growth-research-checkpoint",
    "--paper-execution-state-summary",
    "--show-paper-execution-state-summary",
    "--execute-qqq100-paper",
    "--confirm-qqq100-paper",
    "--high-growth-stock-lab",
    "--show-high-growth-stock-lab",
    "--high-growth-stock-universe-expansion-report",
    "--show-high-growth-stock-universe-expansion-report",
    "--high-growth-stock-drawdown-control-report",
    "--show-high-growth-stock-drawdown-control-report",
    "--high-growth-stock-lead-decision-report",
    "--show-high-growth-stock-lead-decision-report",
    "--high-growth-stock-manual-review-pack",
    "--show-high-growth-stock-manual-review-pack",
    "--high-growth-stock-risk-review-pack",
    "--show-high-growth-stock-risk-review-pack",
    "--high-growth-stock-risk-evidence-review",
    "--show-high-growth-stock-risk-evidence-review",
    "--high-growth-stock-branch-decision-checkpoint",
    "--show-high-growth-stock-branch-decision-checkpoint",
    "--high-growth-stock-final-validation-pack",
    "--show-high-growth-stock-final-validation-pack",
    "--high-growth-strategy-discovery-sprint",
    "--show-high-growth-strategy-discovery-sprint",
    "--higher-growth-preview-readiness-pack",
    "--show-higher-growth-preview-readiness-pack",
    "--higher-growth-candidate-selection-decision",
    "--show-higher-growth-candidate-selection-decision",
    "--higher-growth-preview-design",
    "--show-higher-growth-preview-design",
    "--vol-targeted-growth-research-sprint",
    "--show-vol-targeted-growth-research-sprint",
    "--vol-targeted-growth-manual-review-pack",
    "--show-vol-targeted-growth-manual-review-pack",
    "--vol-targeted-growth-robustness-checkpoint",
    "--show-vol-targeted-growth-robustness-checkpoint",
    "--vol-targeted-growth-nearby-variants-review",
    "--show-vol-targeted-growth-nearby-variants-review",
    "--vol-targeted-growth-preview-readiness-decision",
    "--show-vol-targeted-growth-preview-readiness-decision",
    "--vol-targeted-growth-preview-design",
    "--show-vol-targeted-growth-preview-design",
    "--vol-targeted-growth-preview-signal",
    "--show-vol-targeted-growth-preview-signal",
    "--vol-targeted-growth-action-preview-design",
    "--show-vol-targeted-growth-action-preview-design",
    "--vol-targeted-growth-action-preview",
    "--show-vol-targeted-growth-action-preview",
    "--vol-targeted-growth-action-preview-quality-gate",
    "--show-vol-targeted-growth-action-preview-quality-gate",
    "--vol-targeted-growth-broker-position-comparison-design",
    "--show-vol-targeted-growth-broker-position-comparison-design",
    "--vol-targeted-growth-portfolio-risk-review",
    "--show-vol-targeted-growth-portfolio-risk-review",
    "--vol-targeted-growth-portfolio-risk-policy-design",
    "--show-vol-targeted-growth-portfolio-risk-policy-design",
    "--vol-targeted-growth-paper-live-decision",
    "--show-vol-targeted-growth-paper-live-decision",
    "--vol-targeted-growth-broker-comparison-run-readiness",
    "--show-vol-targeted-growth-broker-comparison-run-readiness",
    "--vol-targeted-growth-broker-position-comparison",
    "--show-vol-targeted-growth-broker-position-comparison",
    "--vol-targeted-growth-post-comparison-decision",
    "--show-vol-targeted-growth-post-comparison-decision",
    "--vol-targeted-growth-stricter-paper-live-gate-design",
    "--show-vol-targeted-growth-stricter-paper-live-gate-design",
    "--vol-targeted-growth-gate-review",
    "--show-vol-targeted-growth-gate-review",
    "--vol-targeted-growth-candidate-discussion-blocker-checklist",
    "--show-vol-targeted-growth-candidate-discussion-blocker-checklist",
    "--vol-targeted-growth-candidate-discussion",
    "--show-vol-targeted-growth-candidate-discussion",
    "--vol-targeted-growth-proposal-implementation-design",
    "--show-vol-targeted-growth-proposal-implementation-design",
    "--vol-targeted-growth-proposal-preview-schema",
    "--show-vol-targeted-growth-proposal-preview-schema",
    "--vol-targeted-growth-proposal-preview",
    "--show-vol-targeted-growth-proposal-preview",
    "--vol-targeted-growth-seed-change-review",
    "--show-vol-targeted-growth-seed-change-review",
    "--vol-targeted-growth-seed-change-evidence-pack",
    "--show-vol-targeted-growth-seed-change-evidence-pack",
    "--vol-targeted-growth-seed-change-risk-reward-comparison",
    "--show-vol-targeted-growth-seed-change-risk-reward-comparison",
    "--vol-targeted-growth-seed-change-drawdown-stress-review",
    "--show-vol-targeted-growth-seed-change-drawdown-stress-review",
    "--vol-targeted-growth-seed-change-cost-turnover-review",
    "--show-vol-targeted-growth-seed-change-cost-turnover-review",
    "--vol-targeted-growth-seed-change-split-stability-review",
    "--show-vol-targeted-growth-seed-change-split-stability-review",
    "--vol-targeted-growth-seed-change-component-sleeve-review",
    "--show-vol-targeted-growth-seed-change-component-sleeve-review",
    "--vol-targeted-growth-seed-change-action-preview-design",
    "--show-vol-targeted-growth-seed-change-action-preview-design",
    "--vol-targeted-growth-seed-change-proposal-document",
    "--show-vol-targeted-growth-seed-change-proposal-document",
    "--vol-targeted-growth-seed-change-broker-exposure-review",
    "--show-vol-targeted-growth-seed-change-broker-exposure-review",
    "--vol-targeted-growth-seed-change-manual-review-checkpoint",
    "--show-vol-targeted-growth-seed-change-manual-review-checkpoint",
    "--vol-targeted-growth-formal-seed-change-proposal",
    "--show-vol-targeted-growth-formal-seed-change-proposal",
    "--vol-targeted-growth-seed-change-manual-approval-record",
    "--show-vol-targeted-growth-seed-change-manual-approval-record",
    "--vol-targeted-growth-seed-change-implementation-design",
    "--show-vol-targeted-growth-seed-change-implementation-design",
    "--vol-targeted-growth-seed-change-dry-run-diff",
    "--show-vol-targeted-growth-seed-change-dry-run-diff",
    "--vol-targeted-growth-active-seed-readiness",
    "--show-vol-targeted-growth-active-seed-readiness",
    "--vol-managed-etf-backtest",
    "--vol-managed-etf-robustness",
    "--strategy-improvement-lab",
    "--show-strategy-improvement-lab",
    "--strategy-improvement-robustness",
    "--show-strategy-improvement-robustness",
    "--strategy-improvement-diagnostics",
    "--show-strategy-improvement-diagnostics",
    "--growth-biased-stricter-validation",
    "--show-growth-biased-stricter-validation",
    "--growth-biased-stricter-promotion-readiness",
    "--show-growth-biased-stricter-promotion-readiness",
    "--growth-biased-stricter-manual-review-pack",
    "--show-growth-biased-stricter-manual-review-pack",
    "--growth-biased-stricter-threshold-neighbourhood",
    "--show-growth-biased-stricter-threshold-neighbourhood",
    "--growth-biased-stricter-cost-turnover-stress",
    "--show-growth-biased-stricter-cost-turnover-stress",
    "--growth-biased-stricter-persistence-filter",
    "--show-growth-biased-stricter-persistence-filter",
    "--codex-ambitious-validation",
    "--show-codex-ambitious-validation",
    "--codex-ambitious-split-drawdown-validation",
    "--show-codex-ambitious-split-drawdown-validation",
    "--codex-ambitious-lead-decision",
    "--show-codex-ambitious-lead-decision",
    "--crypto-research-preview",
    "--crypto-universe-readiness-report",
    "--show-crypto-universe-readiness-report",
    "--expanded-crypto-strategy-lab",
    "--show-expanded-crypto-strategy-lab",
    "--expanded-crypto-robustness-report",
    "--show-expanded-crypto-robustness-report",
    "--crypto-equal-weight-crash-gate",
    "--show-crypto-equal-weight-crash-gate",
    "--crypto-equal-weight-volatility-scaling",
    "--show-crypto-equal-weight-volatility-scaling",
    "--crypto-equal-weight-capped-risk-report",
    "--show-crypto-equal-weight-capped-risk-report",
    "--expanded-crypto-lead-decision",
    "--show-expanded-crypto-lead-decision",
    "--crypto-lead-split-sensitivity-diagnosis",
    "--show-crypto-lead-split-sensitivity-diagnosis",
    "--expanded-crypto-manual-review-pack",
    "--show-expanded-crypto-manual-review-pack",
    "--project-research-state-refresh",
    "--show-project-research-state-refresh",
    "--show-current-research-state",
    "--project-research-state-quality-report",
    "--stock-etf-paper-execution-readiness-report",
    "--alpaca-paper-readiness-report",
    "--alpaca-connectivity-diagnostics",
    "--show-alpaca-connectivity-diagnostics",
    "--confirm-readonly-alpaca-check",
    "--paper-order-smoke-test-readiness-pack",
    "--paper-order-smoke-test-live-preflight",
    "--paper-order-smoke-test-postcheck",
    "--future-refresh-cron-readiness-pack",
    "--paper-order-smoke-test-runbook-check",
    "--paper-smoke-test-kill-switch-diagnosis",
    "--show-paper-smoke-test-kill-switch-diagnosis",
    "--ticker",
    "--side",
    "--quantity",
    "--crypto-strategy-lab",
    "--crypto-strategy-report",
    "--crypto-strategy-decision-report",
    "--crypto-cost-stress-report",
    "--crypto-robustness-report",
    "--crypto-period-diagnostics",
    "--preview-crypto-signals",
    "--show-crypto-monitor",
    "--crypto-research-state-report",
    "--ticker-universe-readiness-report",
    "--market-monitor-snapshot",
    "--show-market-monitor",
    "--market-monitor-quality-report",
    "--refresh-market-monitor",
    "--market-monitor-scheduling-readiness-report",
    "--monitor-lockfile-readiness-report",
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
    "--vps-operations-readiness-report",
    "--vps-monitoring-status",
    "--vps-daily-monitoring-summary",
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
    bot_source = (ROOT / "bot.py").read_text(encoding="utf-8")
    help_available = True
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
        help_available = False
        output = ""

    for command in REQUIRED_COMMANDS:
        if command not in output and command not in bot_source:
            failures.append(f"missing command from help output: {command}")

    command_source = output if help_available else bot_source
    if "--paper-order-test" in command_source and "--confirm-paper-order" not in command_source:
        failures.append("--paper-order-test must remain paired with --confirm-paper-order in help output")
    if "--execute-slow-sma-paper" in command_source and "--confirm-slow-sma-paper" not in command_source:
        failures.append("--execute-slow-sma-paper must remain paired with --confirm-slow-sma-paper in help output")

    readonly_context = command_context_for(output, bot_source, "--use-paper-positions-readonly").lower()
    if "--use-paper-positions-readonly" not in readonly_context:
        failures.append("--use-paper-positions-readonly help line was not found")
    else:
        for expected in ["preview", "without trading"]:
            if expected not in readonly_context:
                failures.append(f"--use-paper-positions-readonly help should mention {expected!r}")

    paper_order_context = command_context_for(output, bot_source, "--paper-order-test").lower()
    if "paper" not in paper_order_context or "order" not in paper_order_context:
        failures.append("--paper-order-test help should clearly describe a paper order test")

    slow_sma_context = command_context_for(output, bot_source, "--confirm-slow-sma-paper").lower()
    if "required" not in slow_sma_context:
        failures.append("--confirm-slow-sma-paper help should clearly say it is required")

    if failures:
        print("Command inventory verification failed.")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Command inventory verification passed.")
    if not help_available:
        print("Used static bot.py fallback because python bot.py --help could not import optional runtime dependencies.")
    return 0


def command_context_for(help_output: str, source: str, command: str) -> str:
    return help_line_for(help_output, command) or source_context_for(source, command)


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


def source_context_for(source: str, command: str) -> str:
    lines = source.splitlines()
    fallback = ""
    for index, line in enumerate(lines):
        if command in line:
            context = " ".join(lines[max(0, index - 3) : index + 18])
            if "parser.add_argument" in context and "help=" in context:
                return context
            if not fallback:
                fallback = context
    return fallback


if __name__ == "__main__":
    raise SystemExit(main())
