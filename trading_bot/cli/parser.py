from __future__ import annotations

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market monitoring and Alpaca paper trading bot.")
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json. Defaults to config.json in the current folder.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run mode, even if config.json has dry_run set to false.",
    )
    parser.add_argument(
        "--paper-order-test",
        nargs=3,
        metavar=("TICKER", "SIDE", "QTY"),
        help="Submit one manual Alpaca paper market DAY order, for example: --paper-order-test AAPL buy 1.",
    )
    parser.add_argument(
        "--confirm-paper-order",
        action="store_true",
        help="Required for --paper-order-test when config.json has dry_run set to true.",
    )
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run a simple long-only SMA backtest for the configured tickers.",
    )
    parser.add_argument(
        "--compare-strategies",
        action="store_true",
        help="Compare several long-only daily strategies for the configured tickers.",
    )
    parser.add_argument(
        "--sma-sensitivity",
        action="store_true",
        help="Test several long-only SMA trend parameter pairs.",
    )
    parser.add_argument(
        "--trend-stress-test",
        action="store_true",
        help="Stress test slow SMA trend pairs across several slippage assumptions.",
    )
    parser.add_argument(
        "--etf-rotation-backtest",
        action="store_true",
        help="Run a research-only monthly ETF momentum rotation backtest.",
    )
    parser.add_argument(
        "--etf-rotation-robustness",
        action="store_true",
        help="Create a saved-data-only fixed-split robustness report for ETF rotation.",
    )
    parser.add_argument(
        "--etf-breadth-regime-backtest",
        action="store_true",
        help="Run a research-only saved-data ETF breadth regime backtest without execution.",
    )
    parser.add_argument(
        "--etf-breadth-regime-decision-report",
        action="store_true",
        help="Create a saved-data-only decision report for ETF breadth regime research.",
    )
    parser.add_argument(
        "--etf-breadth-regime-robustness",
        action="store_true",
        help="Create a saved-data-only fixed-split robustness report for ETF breadth regime research.",
    )
    parser.add_argument(
        "--build-etf-breadth-price-history",
        action="store_true",
        help="Build saved ETF close-history input for the ETF breadth regime backtest.",
    )
    parser.add_argument(
        "--adaptive-momentum-backtest",
        action="store_true",
        help="Run a research-only adaptive risk-on/off momentum backtest.",
    )
    parser.add_argument(
        "--research-report",
        action="store_true",
        help="Create a consolidated research ranking report from saved CSV outputs.",
    )
    parser.add_argument(
        "--walk-forward-report",
        action="store_true",
        help="Create a walk-forward validation report from saved in/out-of-sample CSV outputs.",
    )
    parser.add_argument(
        "--strategy-promotion-report",
        action="store_true",
        help="Create a conservative strategy promotion checklist from saved research reports.",
    )
    parser.add_argument(
        "--defensive-strategy-report",
        action="store_true",
        help="Create a research-only defensive usefulness report from saved research reports.",
    )
    parser.add_argument(
        "--defensive-candidate-comparison",
        action="store_true",
        help="Compare ETF rotation and adaptive momentum as research-only defensive candidates.",
    )
    parser.add_argument(
        "--defensive-research-state-report",
        action="store_true",
        help="Create a saved-data-only defensive research state checkpoint report.",
    )
    parser.add_argument(
        "--defensive-allocation-preview",
        action="store_true",
        help="Create a saved-data-only defensive allocation posture preview without execution.",
    )
    parser.add_argument(
        "--defensive-allocation-risk-preview",
        action="store_true",
        help="Create a saved-data-only defensive allocation risk checkpoint without execution.",
    )
    parser.add_argument(
        "--defensive-allocation-decision-report",
        action="store_true",
        help="Create a saved-data-only defensive allocation decision report without execution.",
    )
    parser.add_argument(
        "--defensive-execution-readiness-report",
        action="store_true",
        help="Create a saved-data-only defensive execution readiness report without execution design.",
    )
    parser.add_argument(
        "--drawdown-period-report",
        action="store_true",
        help="Create a research-only drawdown period analysis report from saved equity curves.",
    )
    parser.add_argument(
        "--etf-defensive-drawdown-comparison",
        action="store_true",
        help="Compare saved ETF rotation and vol-managed ETF drawdown periods without execution.",
    )
    parser.add_argument(
        "--plot-etf-defensive-comparison",
        action="store_true",
        help="Create saved-CSV-only ETF rotation versus vol-managed ETF comparison charts.",
    )
    parser.add_argument(
        "--refresh-defensive-research",
        action="store_true",
        help="Refresh saved defensive research reports and charts without execution.",
    )
    parser.add_argument(
        "--short-selling-readiness-report",
        action="store_true",
        help="Create a research-only short-selling readiness audit without enabling shorting.",
    )
    parser.add_argument(
        "--short-hedge-backtest",
        action="store_true",
        help="Run a research-only synthetic SPY short hedge backtest without enabling short execution.",
    )
    parser.add_argument(
        "--short-strategy-lab",
        action="store_true",
        help="Run a research-only multi-ETF synthetic short strategy lab without enabling short execution.",
    )
    parser.add_argument(
        "--short-leverage-research-lab",
        action="store_true",
        help="Run a research-only synthetic short/leverage hypothesis lab without approving shorting, margin, leverage, or execution.",
    )
    parser.add_argument(
        "--show-short-leverage-research-lab",
        action="store_true",
        help="Display the saved short/leverage research lab summary without refreshing data.",
    )
    parser.add_argument(
        "--qqq-leverage-validation-report",
        action="store_true",
        help="Run a research-only fixed QQQ synthetic leverage validation report without approving leverage or execution.",
    )
    parser.add_argument(
        "--show-qqq-leverage-validation-report",
        action="store_true",
        help="Display the saved QQQ leverage validation report without refreshing data.",
    )
    parser.add_argument(
        "--qqq-adaptive-leverage-lab",
        action="store_true",
        help="Run a research-only fixed QQQ adaptive trend/leverage lab without approving leverage or execution.",
    )
    parser.add_argument(
        "--show-qqq-adaptive-leverage-lab",
        action="store_true",
        help="Display the saved QQQ adaptive leverage lab without refreshing data.",
    )
    parser.add_argument(
        "--qqq-lead-decision-report",
        action="store_true",
        help="Create a saved-output QQQ branch lead decision report without execution approval.",
    )
    parser.add_argument(
        "--show-qqq-lead-decision-report",
        action="store_true",
        help="Display the saved QQQ branch lead decision report without refreshing data.",
    )
    parser.add_argument(
        "--qqq-trend-gate-manual-review-pack",
        action="store_true",
        help="Create a saved-output manual review pack for the QQQ trend-gate research lead.",
    )
    parser.add_argument(
        "--show-qqq-trend-gate-manual-review-pack",
        action="store_true",
        help="Display the saved QQQ trend-gate manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--qqq-preview-candidate-readiness-report",
        action="store_true",
        help="Create a saved-output preview-candidate readiness report for the QQQ trend-gate research lead.",
    )
    parser.add_argument(
        "--show-qqq-preview-candidate-readiness-report",
        action="store_true",
        help="Display the saved QQQ preview-candidate readiness report without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-preview-candidate-readiness-pack",
        action="store_true",
        help="Create a saved-output QQQ100 preview-candidate readiness pack without refreshing data.",
    )
    parser.add_argument(
        "--show-qqq100-preview-candidate-readiness-pack",
        action="store_true",
        help="Display the saved QQQ100 preview-candidate readiness pack without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-preview-signal-pack",
        action="store_true",
        help="Create a non-execution QQQ100 preview signal pack.",
    )
    parser.add_argument(
        "--show-qqq100-preview-signal-pack",
        action="store_true",
        help="Display the saved QQQ100 preview signal pack without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-action-preview",
        action="store_true",
        help="Create a saved-signal-only QQQ100 action preview; optional paper positions require explicit read-only confirmation.",
    )
    parser.add_argument(
        "--show-qqq100-action-preview",
        action="store_true",
        help="Display the saved QQQ100 action preview without refreshing data or reading positions.",
    )
    parser.add_argument(
        "--multi-strategy-portfolio-preview",
        action="store_true",
        help="Create a saved-output-only combined strategy sleeve exposure/conflict preview.",
    )
    parser.add_argument(
        "--show-multi-strategy-portfolio-preview",
        action="store_true",
        help="Display the saved multi-strategy portfolio preview without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-paper-readiness-blocker-report",
        action="store_true",
        help="Create a saved-output QQQ100 paper-readiness blocker report without execution.",
    )
    parser.add_argument(
        "--show-qqq100-paper-readiness-blocker-report",
        action="store_true",
        help="Display the saved QQQ100 paper-readiness blocker report without refreshing data.",
    )
    parser.add_argument(
        "--qqq100-paper-execution-readiness-report",
        action="store_true",
        help="Create a saved-output-only QQQ100 paper execution design-readiness report without approving execution.",
    )
    parser.add_argument(
        "--show-qqq100-paper-execution-readiness-report",
        action="store_true",
        help="Display the saved QQQ100 paper execution readiness report without refreshing data.",
    )
    parser.add_argument(
        "--paper-live-promotion-gate",
        action="store_true",
        help="Create a saved-output paper-live candidate promotion gate for qqq_100_trend_gate without approving execution.",
    )
    parser.add_argument(
        "--show-paper-live-promotion-gate",
        action="store_true",
        help="Display the saved paper-live promotion gate without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--paper-live-readiness-report",
        action="store_true",
        help="Create a saved-output paper-live readiness report for future manual QQQ100 paper action discussion.",
    )
    parser.add_argument(
        "--show-paper-live-readiness-report",
        action="store_true",
        help="Display the saved paper-live readiness report without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--paper-live-state-summary",
        action="store_true",
        help="Create a saved-output paper-live state summary before any future manual QQQ100 paper action discussion.",
    )
    parser.add_argument(
        "--show-paper-live-state-summary",
        action="store_true",
        help="Display the saved paper-live state summary without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--paper-live-evidence-audit",
        action="store_true",
        help="Create a saved-output paper-live evidence audit for QQQ100 saved-state reconciliation.",
    )
    parser.add_argument(
        "--show-paper-live-evidence-audit",
        action="store_true",
        help="Display the saved paper-live evidence audit without refreshing data or reading broker state.",
    )
    parser.add_argument(
        "--qqq100-postcheck-readiness-report",
        action="store_true",
        help="Create a saved-output runbook for the manual read-only QQQ100 postcheck evidence step.",
    )
    parser.add_argument(
        "--show-qqq100-postcheck-readiness-report",
        action="store_true",
        help="Display the saved QQQ100 postcheck readiness runbook without broker reads.",
    )
    parser.add_argument(
        "--qqq100-followup-policy-report",
        action="store_true",
        help="Create a saved-output QQQ100 follow-up/no-action policy report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-followup-policy-report",
        action="store_true",
        help="Display the saved QQQ100 follow-up/no-action policy report without broker reads.",
    )
    parser.add_argument(
        "--qqq100-daily-decision-report",
        action="store_true",
        help="Create a saved-output QQQ100 daily decision report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-daily-decision-report",
        action="store_true",
        help="Display the saved QQQ100 daily decision report without broker reads.",
    )
    parser.add_argument(
        "--qqq100-manual-flatten-readiness-report",
        action="store_true",
        help="Create a saved-output QQQ100 manual flatten readiness report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-manual-flatten-readiness-report",
        action="store_true",
        help="Display the saved QQQ100 manual flatten readiness report without broker reads.",
    )
    parser.add_argument(
        "--qqq100-manual-flatten-runbook-report",
        action="store_true",
        help="Create a saved-output QQQ100 manual flatten runbook/design report without broker reads.",
    )
    parser.add_argument(
        "--show-qqq100-manual-flatten-runbook-report",
        action="store_true",
        help="Display the saved QQQ100 manual flatten runbook/design report without broker reads.",
    )
    parser.add_argument(
        "--paper-live-monitoring-status",
        action="store_true",
        help="Create a saved-output paper-live monitoring status for QQQ100 without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--show-paper-live-monitoring-status",
        action="store_true",
        help="Display the saved paper-live monitoring status without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--paper-live-checklist-status",
        action="store_true",
        help="Create a saved-output paper-live checklist closeout status without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--show-paper-live-checklist-status",
        action="store_true",
        help="Display the saved paper-live checklist status without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--paper-live-go-no-go-dashboard",
        action="store_true",
        help="Create a saved-output paper-live go/no-go dashboard without broker reads or execution approval.",
    )
    parser.add_argument(
        "--show-paper-live-go-no-go-dashboard",
        action="store_true",
        help="Display the saved paper-live go/no-go dashboard without broker reads or execution approval.",
    )
    parser.add_argument(
        "--vol-targeted-growth-post-gate-review",
        action="store_true",
        help="Create a saved-output post-gate review for the active volatility seed without broker reads or execution approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-post-gate-review",
        action="store_true",
        help="Display the saved volatility-targeted growth post-gate review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-manual-ticket-value-design",
        action="store_true",
        help="Create a saved-output manual ticket-value design checkpoint without populating executable order values.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-manual-ticket-value-design",
        action="store_true",
        help="Display the saved volatility-targeted growth manual ticket-value design checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-prerequisites-closeout",
        action="store_true",
        help="Create a saved-output executable-ticket prerequisites closeout without approving execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-prerequisites-closeout",
        action="store_true",
        help="Display the saved executable-ticket prerequisites closeout.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-approval-readiness",
        action="store_true",
        help="Create a saved-output executable-ticket approval-readiness checkpoint without requesting approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-approval-readiness",
        action="store_true",
        help="Display the saved executable-ticket approval-readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-execution-approval-request-readiness",
        action="store_true",
        help="Create a saved-output readiness checkpoint for a future separate execution approval request.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-execution-approval-request-readiness",
        action="store_true",
        help="Display the saved execution approval request readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-execution-design-approval-wording",
        action="store_true",
        help="Create saved wording for execution-design-only approval without approving orders.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-execution-design-approval-wording",
        action="store_true",
        help="Display saved wording for execution-design-only approval.",
    )
    parser.add_argument(
        "--vol-targeted-growth-execution-design-approval-record",
        action="store_true",
        help="Create a saved execution-design-only approval record without approving orders.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-execution-design-approval-record",
        action="store_true",
        help="Display the saved execution-design-only approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-executable-ticket-design",
        action="store_true",
        help="Create a saved non-submitting executable-ticket design without order values or execution approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-executable-ticket-design",
        action="store_true",
        help="Display the saved non-submitting executable-ticket design.",
    )
    parser.add_argument("--vol-targeted-growth-ticket-values-approval-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-values-approval-readiness", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-values-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-values-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-values-approval-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-values-approval-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-placeholders", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-placeholders", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-proposal-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-proposal-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-ticket-value-proposal-approval-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-ticket-value-proposal-approval-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-proposed-ticket-values", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-proposed-ticket-values", action="store_true")
    parser.add_argument("--vol-targeted-growth-proposed-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-proposed-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-executable-ticket-draft-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-executable-ticket-draft-readiness", action="store_true")
    parser.add_argument("--vol-targeted-growth-non-submitting-executable-ticket-draft", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-non-submitting-executable-ticket-draft", action="store_true")
    parser.add_argument("--vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-non-submitting-executable-ticket-draft-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-draft-ticket-value-approval-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-draft-ticket-value-approval-readiness", action="store_true")
    parser.add_argument("--vol-targeted-growth-draft-ticket-value-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-draft-ticket-value-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-draft-ticket-value-approval-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-draft-ticket-value-approval-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-review-only-draft-ticket-values", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-review-only-draft-ticket-values", action="store_true")
    parser.add_argument("--vol-targeted-growth-review-only-draft-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-review-only-draft-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-draft-ticket-values-manual-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-draft-ticket-values-manual-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-executable-ticket-values-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-executable-ticket-values-readiness", action="store_true")
    parser.add_argument("--vol-targeted-growth-executable-ticket-values-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-executable-ticket-values-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-executable-ticket-values-approval-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-executable-ticket-values-approval-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-non-submitting-executable-ticket-values", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-non-submitting-executable-ticket-values", action="store_true")
    parser.add_argument("--vol-targeted-growth-non-submitting-executable-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-non-submitting-executable-ticket-values-quality-gate", action="store_true")
    parser.add_argument("--vol-targeted-growth-non-submitting-executable-ticket-values-manual-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-non-submitting-executable-ticket-values-manual-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-non-submitting-ticket-creation-readiness", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-non-submitting-ticket-creation-readiness", action="store_true")
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-approval-criteria",
        action="store_true",
        help="Create saved-output executable-ticket approval criteria without requesting approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-approval-criteria",
        action="store_true",
        help="Display saved executable-ticket approval criteria.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-criteria-resolution-plan",
        action="store_true",
        help="Create a saved-output resolution plan for executable-ticket approval criteria blockers.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-criteria-resolution-plan",
        action="store_true",
        help="Display the saved executable-ticket criteria resolution plan.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-criteria-source-review",
        action="store_true",
        help="Create a saved-output source review for executable-ticket approval criteria.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-criteria-source-review",
        action="store_true",
        help="Display the saved executable-ticket criteria source review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review",
        action="store_true",
        help="Create a saved-output blocker closeout review for executable-ticket criteria.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-criteria-blocker-closeout-review",
        action="store_true",
        help="Display the saved executable-ticket criteria blocker closeout review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-criteria-source-blocker-review",
        action="store_true",
        help="Create a saved-output criteria source blocker review without closing blockers.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-criteria-source-blocker-review",
        action="store_true",
        help="Display the saved criteria source blocker review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-criteria-resolution-plan-blocker-review",
        action="store_true",
        help="Create a saved-output criteria resolution plan blocker review without closing blockers.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-criteria-resolution-plan-blocker-review",
        action="store_true",
        help="Display the saved criteria resolution plan blocker review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-approval-criteria-not-approval-blocker-review",
        action="store_true",
        help="Create a saved-output approval criteria blocker review without requesting approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-approval-criteria-not-approval-blocker-review",
        action="store_true",
        help="Display the saved approval criteria blocker review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-criteria-blocker-specific-review-rollup",
        action="store_true",
        help="Create a saved-output rollup of criteria blocker-specific reviews.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-criteria-blocker-specific-review-rollup",
        action="store_true",
        help="Display the saved criteria blocker-specific review rollup.",
    )
    parser.add_argument("--vol-targeted-growth-criteria-source-closeout-candidate-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-source-closeout-candidate-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-resolution-plan-closeout-candidate-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-approval-criteria-not-approval-closeout-candidate-review", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-closeout-candidate-review-rollup", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-closeout-candidate-review-rollup", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-resolution-plan-closeout-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-criteria-resolution-plan-closeout-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-criteria-resolution-plan-closeout-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-approval-criteria-closeout-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-approval-criteria-closeout-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-approval-criteria-closeout-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-approval-criteria-closeout-record", action="store_true")
    parser.add_argument("--vol-targeted-growth-final-ticket-blockers-closeout-approval-wording", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-final-ticket-blockers-closeout-approval-wording", action="store_true")
    parser.add_argument("--vol-targeted-growth-final-ticket-blockers-closeout-record", action="store_true")
    parser.add_argument("--show-vol-targeted-growth-final-ticket-blockers-closeout-record", action="store_true")
    parser.add_argument(
        "--paper-live-f6-f7-audit",
        action="store_true",
        help="Create a saved-output F6/F7 audit for paper-live promotion readiness without broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-f6-f7-audit",
        action="store_true",
        help="Display the saved paper-live F6/F7 audit without broker reads or scheduling changes.",
    )
    parser.add_argument(
        "--paper-live-promotion-ladder-design",
        action="store_true",
        help="Create a saved-output generic promotion ladder design checkpoint without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-promotion-ladder-design",
        action="store_true",
        help="Display the saved generic promotion ladder design checkpoint without broker reads.",
    )
    parser.add_argument(
        "--paper-live-promotion-ladder-status",
        action="store_true",
        help="Create a saved-output paper-live promotion ladder status scaffold without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-promotion-ladder-status",
        action="store_true",
        help="Display the saved paper-live promotion ladder status scaffold without broker reads.",
    )
    parser.add_argument(
        "--paper-live-f7-accounting-proof",
        action="store_true",
        help="Create a saved-output F7 accounting proof checkpoint without rerunning backtests or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-f7-accounting-proof",
        action="store_true",
        help="Display the saved F7 accounting proof checkpoint without broker reads.",
    )
    parser.add_argument(
        "--paper-live-next-ladder-candidate-scope",
        action="store_true",
        help="Create a saved-output next ladder candidate scope report without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-next-ladder-candidate-scope",
        action="store_true",
        help="Display the saved next ladder candidate scope report without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-ladder-scope-review",
        action="store_true",
        help="Create a saved-output defensive sleeve ladder-scope review without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-ladder-scope-review",
        action="store_true",
        help="Display the saved defensive sleeve ladder-scope review without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-manual-review",
        action="store_true",
        help="Create a saved-output defensive sleeve manual review pack without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-manual-review",
        action="store_true",
        help="Display the saved defensive sleeve manual review pack without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-preview-readiness",
        action="store_true",
        help="Create a saved-output defensive sleeve preview-readiness checkpoint without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-preview-readiness",
        action="store_true",
        help="Display the saved defensive sleeve preview-readiness checkpoint without broker reads.",
    )
    parser.add_argument(
        "--paper-live-defensive-sleeve-evidence-quality",
        action="store_true",
        help="Create a saved-output defensive sleeve evidence-quality review without promotion or broker reads.",
    )
    parser.add_argument(
        "--show-paper-live-defensive-sleeve-evidence-quality",
        action="store_true",
        help="Display the saved defensive sleeve evidence-quality review without broker reads.",
    )
    parser.add_argument(
        "--paper-live-multi-sleeve-roadmap",
        action="store_true",
        help="Create a saved-output QQQ-led multi-sleeve paper-live roadmap without portfolio execution.",
    )
    parser.add_argument(
        "--show-paper-live-multi-sleeve-roadmap",
        action="store_true",
        help="Display the saved QQQ-led multi-sleeve paper-live roadmap without broker reads.",
    )
    parser.add_argument(
        "--paper-live-next-phase-backlog",
        action="store_true",
        help="Create a saved-output paper-live next-phase backlog without promotion or execution wiring.",
    )
    parser.add_argument(
        "--show-paper-live-next-phase-backlog",
        action="store_true",
        help="Display the saved paper-live next-phase backlog without broker reads.",
    )
    parser.add_argument(
        "--paper-live-multi-sleeve-evidence-gap",
        action="store_true",
        help="Create a saved-output QQQ-led multi-sleeve evidence-gap audit without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-multi-sleeve-evidence-gap",
        action="store_true",
        help="Display the saved QQQ-led multi-sleeve evidence-gap audit without broker reads.",
    )
    parser.add_argument(
        "--paper-live-high-growth-evidence-gap",
        action="store_true",
        help="Create a saved-output high-growth sleeve evidence-gap audit without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-high-growth-evidence-gap",
        action="store_true",
        help="Display the saved high-growth sleeve evidence-gap audit without broker reads.",
    )
    parser.add_argument(
        "--paper-live-high-growth-evidence-quality",
        action="store_true",
        help="Create a saved-output high-growth evidence quality review without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-high-growth-evidence-quality",
        action="store_true",
        help="Display the saved high-growth evidence quality review without broker reads.",
    )
    parser.add_argument(
        "--paper-live-high-growth-manual-review-decision",
        action="store_true",
        help="Create a saved-output high-growth manual-review decision without rerunning research.",
    )
    parser.add_argument(
        "--show-paper-live-high-growth-manual-review-decision",
        action="store_true",
        help="Display the saved high-growth manual-review decision without broker reads.",
    )
    parser.add_argument(
        "--qqq100-paper-postcheck",
        action="store_true",
        help="Create a read-only QQQ100 paper postcheck; broker reads require --confirm-readonly-alpaca-check.",
    )
    parser.add_argument(
        "--show-qqq100-paper-postcheck",
        action="store_true",
        help="Display the saved QQQ100 paper postcheck without broker reads.",
    )
    parser.add_argument(
        "--qqq100-repeat-alignment-workflow-design",
        action="store_true",
        help="Create a saved-output-only QQQ100 repeat/alignment workflow design report.",
    )
    parser.add_argument(
        "--show-qqq100-repeat-alignment-workflow-design",
        action="store_true",
        help="Display the saved QQQ100 repeat/alignment workflow design without broker reads.",
    )
    parser.add_argument(
        "--multi-sleeve-strategy-monitor",
        action="store_true",
        help="Create a saved-output-only multi-sleeve strategy monitoring/design report.",
    )
    parser.add_argument(
        "--show-multi-sleeve-strategy-monitor",
        action="store_true",
        help="Display the saved multi-sleeve strategy monitor without broker or market-data reads.",
    )
    parser.add_argument(
        "--sleeve-research-scoreboard",
        action="store_true",
        help="Create a saved-output-only research scoreboard for candidate strategy sleeves.",
    )
    parser.add_argument(
        "--show-sleeve-research-scoreboard",
        action="store_true",
        help="Display the saved sleeve research scoreboard without broker or market-data reads.",
    )
    parser.add_argument(
        "--codex-qqq-defensive-crash-gate-research-pack",
        action="store_true",
        help="Create a saved-output-only Codex QQQ defensive crash-gate research pack.",
    )
    parser.add_argument(
        "--show-codex-qqq-defensive-crash-gate-research-pack",
        action="store_true",
        help="Display the saved Codex QQQ defensive crash-gate research pack without broker reads.",
    )
    parser.add_argument(
        "--sleeve-return-streams",
        action="store_true",
        help="Create research-only saved daily return streams for portfolio sleeves.",
    )
    parser.add_argument(
        "--show-sleeve-return-streams",
        action="store_true",
        help="Display the saved sleeve return-stream summary without broker reads.",
    )
    parser.add_argument(
        "--qqq100-stream-reconciliation",
        action="store_true",
        help="Create a research-only QQQ100 generated-stream reconciliation report.",
    )
    parser.add_argument(
        "--show-qqq100-stream-reconciliation",
        action="store_true",
        help="Display the saved QQQ100 stream reconciliation summary without broker reads.",
    )
    parser.add_argument(
        "--qqq100-benchmark-inputs-report",
        action="store_true",
        help="Create a saved-output-only report documenting the likely original QQQ100 benchmark inputs.",
    )
    parser.add_argument(
        "--show-qqq100-benchmark-inputs",
        action="store_true",
        help="Display the saved QQQ100 benchmark-input reconstruction without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-return-streams",
        action="store_true",
        help="Create research-only saved daily return streams for high-growth stock candidates.",
    )
    parser.add_argument(
        "--show-high-growth-return-streams",
        action="store_true",
        help="Display saved high-growth return-stream metrics without refreshing broker state.",
    )
    parser.add_argument(
        "--crypto-return-streams",
        action="store_true",
        help="Create research-only saved daily return streams for BTC/ETH crypto sleeves.",
    )
    parser.add_argument(
        "--show-crypto-return-streams",
        action="store_true",
        help="Display saved crypto return-stream metrics without refreshing market or broker state.",
    )
    parser.add_argument(
        "--multi-sleeve-portfolio-backtest",
        action="store_true",
        help="Create a saved-output-only multi-sleeve portfolio research backtest checkpoint.",
    )
    parser.add_argument(
        "--show-multi-sleeve-portfolio-backtest",
        action="store_true",
        help="Display the saved multi-sleeve portfolio backtest without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-robustness",
        action="store_true",
        help="Create a saved-output-only split robustness report for the high-growth multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-robustness",
        action="store_true",
        help="Display the saved multi-sleeve robustness report without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-crypto-review",
        action="store_true",
        help="Create a saved-output-only crypto split/cost/volatility review for the multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-crypto-review",
        action="store_true",
        help="Display the saved multi-sleeve crypto review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-crypto-containment-review",
        action="store_true",
        help="Create a saved-output-only crypto containment review for the current multi-sleeve lead.",
    )
    parser.add_argument(
        "--show-multi-sleeve-crypto-containment-review",
        action="store_true",
        help="Display the saved multi-sleeve crypto containment review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-allocation-policy-review",
        action="store_true",
        help="Create a saved-output-only allocation policy review for the crypto multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-allocation-policy-review",
        action="store_true",
        help="Display the saved multi-sleeve allocation policy review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-weight-sensitivity",
        action="store_true",
        help="Create a saved-output-only fixed weight-sensitivity review for the multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-weight-sensitivity",
        action="store_true",
        help="Display the saved multi-sleeve weight sensitivity review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-higher-growth-review",
        action="store_true",
        help="Create a saved-output-only higher-growth challenger review for the multi-sleeve candidate.",
    )
    parser.add_argument(
        "--show-multi-sleeve-higher-growth-review",
        action="store_true",
        help="Display the saved multi-sleeve higher-growth challenger review without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-research-lead-decision",
        action="store_true",
        help="Create a saved-output-only research lead decision checkpoint for the multi-sleeve allocation.",
    )
    parser.add_argument(
        "--show-multi-sleeve-research-lead-decision",
        action="store_true",
        help="Display the saved multi-sleeve research lead decision without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-lead-state-refresh",
        action="store_true",
        help="Create a saved-output-only canonical lead-state checkpoint for the multi-sleeve research lead.",
    )
    parser.add_argument(
        "--show-multi-sleeve-lead-state",
        action="store_true",
        help="Display the saved canonical multi-sleeve lead state without broker or market-data reads.",
    )
    parser.add_argument(
        "--multi-sleeve-high-growth-drawdown-decomposition",
        action="store_true",
        help="Create a saved-output-only high-growth drawdown decomposition for the multi-sleeve lead.",
    )
    parser.add_argument(
        "--show-multi-sleeve-high-growth-drawdown-decomposition",
        action="store_true",
        help="Display the saved multi-sleeve high-growth drawdown decomposition without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-sleeve-quality-review",
        action="store_true",
        help="Create a saved-output-only quality review for the high-growth research sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-sleeve-quality-review",
        action="store_true",
        help="Display the saved high-growth sleeve quality review without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-component-attribution",
        action="store_true",
        help="Create a saved-output-only component attribution readiness review for the high-growth sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-component-attribution",
        action="store_true",
        help="Display the saved high-growth component attribution review without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-component-streams",
        action="store_true",
        help="Create research-only component streams for the selected high-growth sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-component-streams",
        action="store_true",
        help="Display the saved high-growth component streams summary without broker reads.",
    )
    parser.add_argument(
        "--high-growth-sleeve-concentration-review",
        action="store_true",
        help="Create a saved-output-only concentration review for the high-growth research sleeve.",
    )
    parser.add_argument(
        "--show-high-growth-sleeve-concentration-review",
        action="store_true",
        help="Display the saved high-growth sleeve concentration review without broker or market-data reads.",
    )
    parser.add_argument(
        "--high-growth-research-checkpoint",
        action="store_true",
        help="Create a saved-output-only checkpoint for the completed high-growth research chain.",
    )
    parser.add_argument(
        "--show-high-growth-research-checkpoint",
        action="store_true",
        help="Display the saved high-growth research checkpoint without broker or market-data reads.",
    )
    parser.add_argument(
        "--paper-execution-state-summary",
        action="store_true",
        help="Create a saved-output-only paper execution milestone/state summary without broker calls.",
    )
    parser.add_argument(
        "--show-paper-execution-state-summary",
        action="store_true",
        help="Display the saved paper execution state summary without reading broker state.",
    )
    parser.add_argument(
        "--execute-qqq100-paper",
        action="store_true",
        help="Manually align the saved QQQ100 preview signal with exactly one QQQ paper share; requires --confirm-qqq100-paper.",
    )
    parser.add_argument(
        "--confirm-qqq100-paper",
        action="store_true",
        help="Required confirmation for --execute-qqq100-paper.",
    )
    parser.add_argument(
        "--high-growth-stock-lab",
        action="store_true",
        help="Run a research-only concentrated single-stock growth/momentum lab without execution.",
    )
    parser.add_argument(
        "--show-high-growth-stock-lab",
        action="store_true",
        help="Display the saved high-growth stock lab summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-universe-expansion-report",
        action="store_true",
        help="Run a research-only fixed stock universe breadth sensitivity report without execution.",
    )
    parser.add_argument(
        "--show-high-growth-stock-universe-expansion-report",
        action="store_true",
        help="Display the saved high-growth stock universe expansion summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-drawdown-control-report",
        action="store_true",
        help="Run a research-only broad high-growth stock drawdown-control report without execution.",
    )
    parser.add_argument(
        "--show-high-growth-stock-drawdown-control-report",
        action="store_true",
        help="Display the saved high-growth stock drawdown-control summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-lead-decision-report",
        action="store_true",
        help="Create a saved-output high-growth stock lead decision report without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-lead-decision-report",
        action="store_true",
        help="Display the saved high-growth stock lead decision summary without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-manual-review-pack",
        action="store_true",
        help="Create a saved-output high-growth stock manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-manual-review-pack",
        action="store_true",
        help="Display the saved high-growth stock manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-risk-review-pack",
        action="store_true",
        help="Create a saved-output high-growth stock risk review pack without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-risk-review-pack",
        action="store_true",
        help="Display the saved high-growth stock risk review pack without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-risk-evidence-review",
        action="store_true",
        help="Create a saved-output high-growth stock risk evidence review without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-risk-evidence-review",
        action="store_true",
        help="Display the saved high-growth stock risk evidence review without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-branch-decision-checkpoint",
        action="store_true",
        help="Create a saved-output high-growth stock branch decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-branch-decision-checkpoint",
        action="store_true",
        help="Display the saved high-growth stock branch decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-stock-final-validation-pack",
        action="store_true",
        help="Create a saved-output high-growth stock final validation pack without refreshing data.",
    )
    parser.add_argument(
        "--show-high-growth-stock-final-validation-pack",
        action="store_true",
        help="Display the saved high-growth stock final validation pack without refreshing data.",
    )
    parser.add_argument(
        "--high-growth-strategy-discovery-sprint",
        action="store_true",
        help="Create a saved-output-only high-growth strategy discovery sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--show-high-growth-strategy-discovery-sprint",
        action="store_true",
        help="Display the saved high-growth strategy discovery sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--higher-growth-preview-readiness-pack",
        action="store_true",
        help="Create a saved-output-only manual preview-readiness pack for higher_growth_70_20_5_5 without broker reads or execution.",
    )
    parser.add_argument(
        "--show-higher-growth-preview-readiness-pack",
        action="store_true",
        help="Display the saved higher-growth preview-readiness pack without broker reads or execution.",
    )
    parser.add_argument(
        "--higher-growth-candidate-selection-decision",
        action="store_true",
        help="Create a saved-output-only decision choosing the next higher-growth preview-design review candidate.",
    )
    parser.add_argument(
        "--show-higher-growth-candidate-selection-decision",
        action="store_true",
        help="Display the saved higher-growth candidate selection decision without broker reads or execution.",
    )
    parser.add_argument(
        "--higher-growth-preview-design",
        action="store_true",
        help="Create a saved-output-only preview design for higher_growth_70_20_5_5 without creating signals, orders, or execution.",
    )
    parser.add_argument(
        "--show-higher-growth-preview-design",
        action="store_true",
        help="Display the saved higher-growth preview design without broker reads or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-research-sprint",
        action="store_true",
        help="Create a saved-output-only volatility-targeted growth research sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-research-sprint",
        action="store_true",
        help="Display the saved volatility-targeted growth research sprint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-manual-review-pack",
        action="store_true",
        help="Create a saved-output-only manual review pack for volatility-targeted growth candidates.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-manual-review-pack",
        action="store_true",
        help="Display the saved volatility-targeted growth manual review pack without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-robustness-checkpoint",
        action="store_true",
        help="Create a saved-output-only robustness checkpoint for the preferred volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-robustness-checkpoint",
        action="store_true",
        help="Display the saved volatility-targeted growth robustness checkpoint without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-nearby-variants-review",
        action="store_true",
        help="Create a saved-output-only nearby-variants review for the preferred volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-nearby-variants-review",
        action="store_true",
        help="Display the saved volatility-targeted growth nearby-variants review without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-preview-readiness-decision",
        action="store_true",
        help="Create a saved-output-only preview-readiness decision for the volatility-targeted growth 15/20 candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-preview-readiness-decision",
        action="store_true",
        help="Display the saved volatility-targeted growth preview-readiness decision without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-preview-design",
        action="store_true",
        help="Create a saved-output-only preview design checkpoint for the selected volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-preview-design",
        action="store_true",
        help="Display the saved volatility-targeted growth preview design without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-preview-signal",
        action="store_true",
        help="Create a saved-output-only preview signal for the selected volatility-targeted growth candidate without action preview, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-preview-signal",
        action="store_true",
        help="Display the saved volatility-targeted growth preview signal without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-action-preview-design",
        action="store_true",
        help="Create a saved-output-only action-preview design for the selected volatility-targeted growth candidate without creating actions, broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-action-preview-design",
        action="store_true",
        help="Display the saved volatility-targeted growth action-preview design without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-action-preview",
        action="store_true",
        help="Create a saved-output-only action preview for the selected volatility-targeted growth candidate without broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-action-preview",
        action="store_true",
        help="Display the saved volatility-targeted growth action preview without market refresh, broker reads, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-action-preview-quality-gate",
        action="store_true",
        help="Create a saved-output-only quality gate for the volatility-targeted growth action preview without broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-action-preview-quality-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth action-preview quality gate without broker reads, orders, or execution.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-position-comparison-design",
        action="store_true",
        help="Create a saved-output-only broker-position comparison design for volatility-targeted growth without broker reads or execution.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-position-comparison-design",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-position comparison design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-portfolio-risk-review",
        action="store_true",
        help="Create a saved-output-only portfolio-risk/manual-review report for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-portfolio-risk-review",
        action="store_true",
        help="Display the saved volatility-targeted growth portfolio-risk review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-portfolio-risk-policy-design",
        action="store_true",
        help="Create a saved-output-only portfolio-risk policy design for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-portfolio-risk-policy-design",
        action="store_true",
        help="Display the saved volatility-targeted growth portfolio-risk policy design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-decision",
        action="store_true",
        help="Create a saved-output-only paper-live/manual-review decision checkpoint for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-decision",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live decision checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-comparison-run-readiness",
        action="store_true",
        help="Create a saved-output-only run-readiness checkpoint before any future read-only broker-position comparison for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-comparison-run-readiness",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-comparison run-readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-position-comparison",
        action="store_true",
        help="Create a read-only/manual-review broker-position comparison for volatility-targeted growth; broker reads require --confirm-readonly-alpaca-check.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-position-comparison",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-position comparison.",
    )
    parser.add_argument(
        "--vol-targeted-growth-post-comparison-decision",
        action="store_true",
        help="Create a saved-output-only post-comparison decision checkpoint for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-post-comparison-decision",
        action="store_true",
        help="Display the saved volatility-targeted growth post-comparison decision checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-stricter-paper-live-gate-design",
        action="store_true",
        help="Create a saved-output-only stricter manual paper-live gate design for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-stricter-paper-live-gate-design",
        action="store_true",
        help="Display the saved volatility-targeted growth stricter paper-live gate design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-gate-review",
        action="store_true",
        help="Create a saved-output-only gate review for limited manual candidate discussion of the volatility-targeted growth strategy.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-gate-review",
        action="store_true",
        help="Display the saved volatility-targeted growth gate review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-candidate-discussion-blocker-checklist",
        action="store_true",
        help="Create a saved-output-only final blocker checklist before volatility-targeted implementation work.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-candidate-discussion-blocker-checklist",
        action="store_true",
        help="Display the saved volatility-targeted growth candidate discussion blocker checklist.",
    )
    parser.add_argument(
        "--vol-targeted-growth-candidate-decision-record",
        action="store_true",
        help="Create a saved-output-only formal decision record for volatility-targeted manual candidate discussion.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-candidate-decision-record",
        action="store_true",
        help="Display the saved volatility-targeted growth candidate decision record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-candidate-discussion",
        action="store_true",
        help="Create a saved-output-only limited manual candidate discussion report for the volatility-targeted growth strategy.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-candidate-discussion",
        action="store_true",
        help="Display the saved volatility-targeted growth candidate discussion report.",
    )
    parser.add_argument(
        "--vol-targeted-growth-proposal-implementation-design",
        action="store_true",
        help="Create a saved-output-only implementation design checkpoint for the volatility-targeted growth proposal.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-proposal-implementation-design",
        action="store_true",
        help="Display the saved volatility-targeted growth proposal implementation design checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-proposal-preview-schema",
        action="store_true",
        help="Create a saved-output-only schema checkpoint for a future volatility-targeted proposal preview.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-proposal-preview-schema",
        action="store_true",
        help="Display the saved volatility-targeted growth proposal preview schema checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-proposal-preview",
        action="store_true",
        help="Create a saved-output-only non-executable proposal preview for the volatility-targeted growth candidate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-proposal-preview",
        action="store_true",
        help="Display the saved volatility-targeted growth proposal preview.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-review",
        action="store_true",
        help="Create a saved-output-only seed-change review for the volatility-targeted growth proposal.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-evidence-pack",
        action="store_true",
        help="Create a saved-output-only evidence pack for a future volatility-targeted growth seed-change proposal.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-evidence-pack",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change evidence pack.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-risk-reward-comparison",
        action="store_true",
        help="Create a saved-output-only QQQ100 versus volatility risk/reward comparison for seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-risk-reward-comparison",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change risk/reward comparison.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-drawdown-stress-review",
        action="store_true",
        help="Create a saved-output-only drawdown/stress review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-drawdown-stress-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change drawdown/stress review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-cost-turnover-review",
        action="store_true",
        help="Create a saved-output-only cost/turnover review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-cost-turnover-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change cost/turnover review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-split-stability-review",
        action="store_true",
        help="Create a saved-output-only split-stability review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-split-stability-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change split-stability review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-component-sleeve-review",
        action="store_true",
        help="Create a saved-output-only component-sleeve review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-component-sleeve-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change component-sleeve review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-action-preview-design",
        action="store_true",
        help="Create a saved-output-only action-preview design checkpoint for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-action-preview-design",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change action-preview design checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-proposal-document",
        action="store_true",
        help="Create a saved-output-only proposal-document draft checkpoint for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-proposal-document",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change proposal-document checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-broker-exposure-review",
        action="store_true",
        help="Create a saved-output-only broker-exposure review for volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-broker-exposure-review",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change broker-exposure review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-manual-review-checkpoint",
        action="store_true",
        help="Create a saved-output-only manual-review checkpoint for completed volatility seed-change evidence.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-manual-review-checkpoint",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change manual-review checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-formal-seed-change-proposal",
        action="store_true",
        help="Create a saved-output-only formal proposal document for volatility seed-change manual review.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-formal-seed-change-proposal",
        action="store_true",
        help="Display the saved volatility-targeted growth formal seed-change proposal.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-manual-approval-record",
        action="store_true",
        help="Create a saved-output-only manual approval record for volatility seed-change implementation design.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-manual-approval-record",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change manual approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-implementation-design",
        action="store_true",
        help="Create a saved-output-only implementation design for a future volatility seed change.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-implementation-design",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change implementation design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-seed-change-dry-run-diff",
        action="store_true",
        help="Create a saved-output-only dry-run diff for a future volatility seed switch.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-seed-change-dry-run-diff",
        action="store_true",
        help="Display the saved volatility-targeted growth seed-change dry-run diff.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-manual-approval-gate",
        action="store_true",
        help="Create a saved-output-only manual paper-live approval gate for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-manual-approval-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live manual approval gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-action-preview-pack",
        action="store_true",
        help="Create a saved-output-only paper-live action-preview pack for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-action-preview-pack",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live action-preview pack.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-comparison-reconciliation",
        action="store_true",
        help="Create a saved-output-only broker-comparison reconciliation for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-comparison-reconciliation",
        action="store_true",
        help="Display the saved volatility-targeted growth broker-comparison reconciliation.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-candidate-approval-record",
        action="store_true",
        help="Create a saved-output-only candidate-discussion approval record for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-candidate-approval-record",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live candidate approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-allocation-cap-sleeve-mapping-policy",
        action="store_true",
        help="Create a saved-output-only allocation cap and sleeve mapping policy for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-allocation-cap-sleeve-mapping-policy",
        action="store_true",
        help="Display the saved volatility-targeted growth allocation cap and sleeve mapping policy.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-executable-target-position-plan",
        action="store_true",
        help="Create a saved-output-only non-executable target-position plan for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-executable-target-position-plan",
        action="store_true",
        help="Display the saved volatility-targeted growth non-executable target-position plan.",
    )
    parser.add_argument(
        "--vol-targeted-growth-order-ticket-boundary-design",
        action="store_true",
        help="Create a saved-output-only order-ticket boundary design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-order-ticket-boundary-design",
        action="store_true",
        help="Display the saved volatility-targeted growth order-ticket boundary design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-prerequisites-review",
        action="store_true",
        help="Create a saved-output-only executable ticket prerequisites review for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-prerequisites-review",
        action="store_true",
        help="Display the saved volatility-targeted growth executable ticket prerequisites review.",
    )
    parser.add_argument(
        "--vol-targeted-growth-executable-ticket-gap-list",
        action="store_true",
        help="Create a saved-output-only executable ticket gap list for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-executable-ticket-gap-list",
        action="store_true",
        help="Display the saved volatility-targeted growth executable ticket gap list.",
    )
    parser.add_argument(
        "--vol-targeted-growth-manual-execution-design-approval-gate",
        action="store_true",
        help="Create a saved-output-only manual execution-design approval gate for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-manual-execution-design-approval-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth manual execution-design approval gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-ticket-schema-design",
        action="store_true",
        help="Create a saved-output-only non-submitting ticket schema design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-ticket-schema-design",
        action="store_true",
        help="Display the saved volatility-targeted growth non-submitting ticket schema design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-ticket-instance-design",
        action="store_true",
        help="Create a saved-output-only non-submitting ticket-instance design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-ticket-instance-design",
        action="store_true",
        help="Display the saved volatility-targeted growth non-submitting ticket-instance design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-ticket-instance-checkpoint",
        action="store_true",
        help="Create a saved-output-only non-submitting ticket-instance checkpoint for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-ticket-instance-checkpoint",
        action="store_true",
        help="Display the saved volatility-targeted growth non-submitting ticket-instance checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-non-submitting-ticket-instance-quality-gate",
        action="store_true",
        help="Create a saved-output-only quality gate for the volatility-targeted growth non-submitting ticket-instance checkpoint.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-non-submitting-ticket-instance-quality-gate",
        action="store_true",
        help="Display the saved volatility-targeted growth non-submitting ticket-instance quality gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-sleeve-symbol-mapping",
        action="store_true",
        help="Create a saved-output-only sleeve-to-symbol mapping for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-sleeve-symbol-mapping",
        action="store_true",
        help="Display the saved volatility-targeted growth sleeve-to-symbol mapping.",
    )
    parser.add_argument(
        "--vol-targeted-growth-broker-ready-action-proposal",
        action="store_true",
        help="Create a saved-output-only real-symbol action proposal without order instructions.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-broker-ready-action-proposal",
        action="store_true",
        help="Display the saved volatility-targeted growth real-symbol action proposal.",
    )
    parser.add_argument(
        "--vol-targeted-growth-calculated-order-values",
        action="store_true",
        help="Create saved-output-only calculated target-dollar values without executable quantities.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-calculated-order-values",
        action="store_true",
        help="Display saved volatility-targeted calculated target-dollar values.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-readiness",
        action="store_true",
        help="Create a saved-output-only readiness review for a future saved-price snapshot.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-readiness",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot readiness.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-approval-wording",
        action="store_true",
        help="Create saved-output-only wording for future saved-price snapshot method discussion.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-approval-wording",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot approval wording.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-approval-record",
        action="store_true",
        help="Record saved-output-only approval for future saved-price snapshot method discussion.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-approval-record",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-runner-design",
        action="store_true",
        help="Create a saved-output-only design for a future saved-price snapshot runner.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-runner-design",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot runner design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-runner-readiness",
        action="store_true",
        help="Create a saved-output-only readiness review for future saved-price snapshot runner implementation.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-runner-readiness",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot runner implementation readiness.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-runner-approval-wording",
        action="store_true",
        help="Create saved-output-only wording for future saved-price snapshot runner implementation approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-runner-approval-wording",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot runner implementation approval wording.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-runner-approval-record",
        action="store_true",
        help="Record saved-output-only approval for future saved-price snapshot runner implementation.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-runner-approval-record",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot runner implementation approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot",
        action="store_true",
        help="Create a guarded saved-price snapshot; fetches prices only with --confirm-saved-price-snapshot-run.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot",
        action="store_true",
        help="Display the saved volatility-targeted price snapshot report.",
    )
    parser.add_argument(
        "--confirm-saved-price-snapshot-run",
        action="store_true",
        help="Required confirmation for --vol-targeted-growth-saved-price-snapshot to fetch prices.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-run-approval-wording",
        action="store_true",
        help="Create saved-output-only wording for a future guarded saved-price snapshot run.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-run-approval-wording",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot run approval wording.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-run-approval-record",
        action="store_true",
        help="Record saved-output-only approval for a future guarded saved-price snapshot run.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-run-approval-record",
        action="store_true",
        help="Display saved volatility-targeted saved-price snapshot run approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-saved-price-snapshot-quality-gate",
        action="store_true",
        help="Create a saved-output-only quality gate for the saved-price snapshot.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-saved-price-snapshot-quality-gate",
        action="store_true",
        help="Display the saved volatility-targeted saved-price snapshot quality gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-quantity-calculation-readiness",
        action="store_true",
        help="Create a saved-output-only readiness review for future quantity calculation.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-quantity-calculation-readiness",
        action="store_true",
        help="Display saved volatility-targeted quantity-calculation readiness.",
    )
    parser.add_argument(
        "--vol-targeted-growth-quantity-calculation-approval-wording",
        action="store_true",
        help="Create saved-output-only wording for review quantity calculation approval.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-quantity-calculation-approval-wording",
        action="store_true",
        help="Display saved volatility-targeted quantity-calculation approval wording.",
    )
    parser.add_argument(
        "--vol-targeted-growth-quantity-calculation-approval-record",
        action="store_true",
        help="Record saved-output-only approval for review quantity calculation.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-quantity-calculation-approval-record",
        action="store_true",
        help="Display saved volatility-targeted quantity-calculation approval record.",
    )
    parser.add_argument(
        "--vol-targeted-growth-review-quantity-estimates",
        action="store_true",
        help="Create saved-output-only review share quantity estimates.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-review-quantity-estimates",
        action="store_true",
        help="Display saved volatility-targeted review share quantity estimates.",
    )
    parser.add_argument(
        "--vol-targeted-growth-review-quantity-quality-gate",
        action="store_true",
        help="Create a saved-output-only quality gate for review quantity estimates.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-review-quantity-quality-gate",
        action="store_true",
        help="Display saved volatility-targeted review quantity quality gate.",
    )
    parser.add_argument(
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-design",
        action="store_true",
        help="Create a saved-output-only fresh broker pre-ticket gate design for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-design",
        action="store_true",
        help="Display the saved volatility-targeted growth fresh broker pre-ticket gate design.",
    )
    parser.add_argument(
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness",
        action="store_true",
        help="Create a saved-output-only run-readiness checkpoint for the future fresh broker pre-ticket gate.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run-readiness",
        action="store_true",
        help="Display the saved volatility-targeted growth fresh broker pre-ticket gate run-readiness checkpoint.",
    )
    parser.add_argument(
        "--vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
        action="store_true",
        help="Run the explicitly confirmed read-only fresh broker pre-ticket gate for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-fresh-broker-pre-ticket-gate-run",
        action="store_true",
        help="Display the saved volatility-targeted growth fresh broker pre-ticket gate run.",
    )
    parser.add_argument(
        "--vol-targeted-growth-paper-live-execution-blocker-rollup",
        action="store_true",
        help="Create a saved-output-only paper-live execution blocker rollup for the active volatility seed.",
    )
    parser.add_argument(
        "--show-vol-targeted-growth-paper-live-execution-blocker-rollup",
        action="store_true",
        help="Display the saved volatility-targeted growth paper-live execution blocker rollup.",
    )
    parser.add_argument(
        "--vol-managed-etf-backtest",
        action="store_true",
        help="Run a research-only volatility-managed ETF dual momentum backtest without execution.",
    )
    parser.add_argument(
        "--vol-managed-etf-robustness",
        action="store_true",
        help="Create a research-only fixed-split robustness report for the vol-managed ETF strategy.",
    )
    parser.add_argument(
        "--strategy-improvement-lab",
        action="store_true",
        help="Run a fixed research-only growth-aware ETF strategy improvement lab without execution.",
    )
    parser.add_argument(
        "--show-strategy-improvement-lab",
        action="store_true",
        help="Display the saved strategy improvement lab summary CSV without refreshing data.",
    )
    parser.add_argument(
        "--strategy-improvement-robustness",
        action="store_true",
        help="Create research-only robustness, cost, drawdown, and comparison reports for strategy improvement candidates.",
    )
    parser.add_argument(
        "--show-strategy-improvement-robustness",
        action="store_true",
        help="Display saved strategy improvement robustness comparison CSV without refreshing data.",
    )
    parser.add_argument(
        "--strategy-improvement-diagnostics",
        action="store_true",
        help="Create saved-CSV diagnostics explaining strategy improvement split sensitivity without execution.",
    )
    parser.add_argument(
        "--show-strategy-improvement-diagnostics",
        action="store_true",
        help="Display saved strategy improvement diagnostics CSV without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-validation",
        action="store_true",
        help="Create saved research-only validation for the stricter growth-biased breadth-gate lead.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-validation",
        action="store_true",
        help="Display saved stricter growth-biased validation CSVs without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-promotion-readiness",
        action="store_true",
        help="Create a research-only blocker report for stricter-gate preview promotion readiness.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-promotion-readiness",
        action="store_true",
        help="Display the saved stricter-gate promotion-readiness blocker report without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-manual-review-pack",
        action="store_true",
        help="Create a saved-output manual review pack for the stricter growth-biased research lead.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-manual-review-pack",
        action="store_true",
        help="Display the saved stricter-gate manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-threshold-neighbourhood",
        action="store_true",
        help="Run a fixed research-only threshold neighbourhood check for the stricter growth-biased breadth gate.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-threshold-neighbourhood",
        action="store_true",
        help="Display the saved stricter-gate threshold neighbourhood report without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-cost-turnover-stress",
        action="store_true",
        help="Create a saved-output turnover and cost stress report for the stricter 55%% breadth-gate cluster.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-cost-turnover-stress",
        action="store_true",
        help="Display the saved stricter-gate turnover and cost stress report without refreshing data.",
    )
    parser.add_argument(
        "--growth-biased-stricter-persistence-filter",
        action="store_true",
        help="Create a research-only persistence-filter report for the stricter 55%% breadth-gate cluster.",
    )
    parser.add_argument(
        "--show-growth-biased-stricter-persistence-filter",
        action="store_true",
        help="Display the saved stricter-gate persistence-filter report without refreshing data.",
    )
    parser.add_argument(
        "--codex-ambitious-validation",
        action="store_true",
        help="Create a saved-output validation checkpoint for the Codex ambitious persistence candidate.",
    )
    parser.add_argument(
        "--show-codex-ambitious-validation",
        action="store_true",
        help="Display the saved Codex ambitious validation checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--codex-ambitious-split-drawdown-validation",
        action="store_true",
        help="Create a research-only split and drawdown-window validation for the Codex ambitious candidate.",
    )
    parser.add_argument(
        "--show-codex-ambitious-split-drawdown-validation",
        action="store_true",
        help="Display the saved Codex ambitious split/drawdown validation without refreshing data.",
    )
    parser.add_argument(
        "--codex-ambitious-lead-decision",
        action="store_true",
        help="Create a saved-output final research lead decision checkpoint for the Codex ambitious candidate.",
    )
    parser.add_argument(
        "--show-codex-ambitious-lead-decision",
        action="store_true",
        help="Display the saved Codex ambitious lead decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--crypto-research-preview",
        action="store_true",
        help="Create a research-only crypto scaffold preview without execution.",
    )
    parser.add_argument(
        "--crypto-universe-readiness-report",
        action="store_true",
        help="Create a research-only crypto universe data-readiness report without strategy signals.",
    )
    parser.add_argument(
        "--show-crypto-universe-readiness-report",
        action="store_true",
        help="Display the saved crypto universe readiness report without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-strategy-lab",
        action="store_true",
        help="Run a research-only expanded crypto strategy lab over readiness-eligible symbols.",
    )
    parser.add_argument(
        "--show-expanded-crypto-strategy-lab",
        action="store_true",
        help="Display the saved expanded crypto strategy lab without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-robustness-report",
        action="store_true",
        help="Create a research-only expanded crypto robustness and equal-weight reality-check report.",
    )
    parser.add_argument(
        "--show-expanded-crypto-robustness-report",
        action="store_true",
        help="Display the saved expanded crypto robustness report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-equal-weight-crash-gate",
        action="store_true",
        help="Run a research-only equal-weight crypto crash-gate report without execution.",
    )
    parser.add_argument(
        "--show-crypto-equal-weight-crash-gate",
        action="store_true",
        help="Display the saved equal-weight crypto crash-gate report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-equal-weight-volatility-scaling",
        action="store_true",
        help="Run a research-only equal-weight crypto volatility-scaling report without execution.",
    )
    parser.add_argument(
        "--show-crypto-equal-weight-volatility-scaling",
        action="store_true",
        help="Display the saved equal-weight crypto volatility-scaling report without refreshing data.",
    )
    parser.add_argument(
        "--crypto-equal-weight-capped-risk-report",
        action="store_true",
        help="Run a research-only equal-weight crypto capped/equal-risk contribution report without execution.",
    )
    parser.add_argument(
        "--show-crypto-equal-weight-capped-risk-report",
        action="store_true",
        help="Display the saved equal-weight crypto capped/equal-risk report without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-lead-decision",
        action="store_true",
        help="Create a saved-output research-only expanded crypto lead decision checkpoint.",
    )
    parser.add_argument(
        "--show-expanded-crypto-lead-decision",
        action="store_true",
        help="Display the saved expanded crypto lead decision checkpoint without refreshing data.",
    )
    parser.add_argument(
        "--crypto-lead-split-sensitivity-diagnosis",
        action="store_true",
        help="Create a saved-output research-only split-sensitivity diagnosis for the current crypto research lead.",
    )
    parser.add_argument(
        "--show-crypto-lead-split-sensitivity-diagnosis",
        action="store_true",
        help="Display the saved crypto lead split-sensitivity diagnosis without refreshing data.",
    )
    parser.add_argument(
        "--expanded-crypto-manual-review-pack",
        action="store_true",
        help="Create a saved-output research-only manual review pack for the expanded crypto branch.",
    )
    parser.add_argument(
        "--show-expanded-crypto-manual-review-pack",
        action="store_true",
        help="Display the saved expanded crypto manual review pack without refreshing data.",
    )
    parser.add_argument(
        "--project-research-state-refresh",
        action="store_true",
        help="Create a saved-output research-only project-wide stock/ETF and crypto state refresh.",
    )
    parser.add_argument(
        "--show-project-research-state-refresh",
        action="store_true",
        help="Display the saved project research state refresh without refreshing data.",
    )
    parser.add_argument(
        "--show-current-research-state",
        action="store_true",
        help="Display a concise saved-state summary of the current stock/ETF and crypto research branches.",
    )
    parser.add_argument(
        "--project-research-state-quality-report",
        action="store_true",
        help="Create a report-only quality check for saved project research state files.",
    )
    parser.add_argument(
        "--stock-etf-paper-execution-readiness-report",
        action="store_true",
        help="Create a saved-data report-only stock/ETF paper execution discussion readiness review.",
    )
    parser.add_argument(
        "--alpaca-paper-readiness-report",
        action="store_true",
        help="Create an Alpaca paper readiness/preflight report without approving execution.",
    )
    parser.add_argument(
        "--alpaca-connectivity-diagnostics",
        action="store_true",
        help="Create unauthenticated DNS/TCP 443 diagnostics for Alpaca API and general HTTPS endpoints.",
    )
    parser.add_argument(
        "--show-alpaca-connectivity-diagnostics",
        action="store_true",
        help="Display the saved Alpaca connectivity diagnostics summary without refreshing checks.",
    )
    parser.add_argument(
        "--confirm-readonly-alpaca-check",
        action="store_true",
        help="With --alpaca-paper-readiness-report only, explicitly allow a read-only Alpaca paper account/status check.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-readiness-pack",
        action="store_true",
        help="Create a report-only readiness pack for discussing a future tiny manual paper-order smoke test.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-live-preflight",
        action="store_true",
        help="Create a read-only/report-only live preflight for a future tiny manual paper-order smoke test.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-postcheck",
        action="store_true",
        help="Create a read-only/report-only postcheck after a future tiny manual paper-order smoke test.",
    )
    parser.add_argument(
        "--future-refresh-cron-readiness-pack",
        action="store_true",
        help="Create a report-only readiness pack for a future safe refresh Hermes cron review.",
    )
    parser.add_argument(
        "--paper-order-smoke-test-runbook-check",
        action="store_true",
        help="Create a static report-only check for the manual paper-order smoke-test runbook.",
    )
    parser.add_argument(
        "--paper-smoke-test-kill-switch-diagnosis",
        action="store_true",
        help="Create a saved-output diagnosis for paper smoke-test kill-switch blockers without execution.",
    )
    parser.add_argument(
        "--show-paper-smoke-test-kill-switch-diagnosis",
        action="store_true",
        help="Display the saved paper smoke-test kill-switch diagnosis without refreshing data.",
    )
    parser.add_argument(
        "--ticker",
        default="",
        help="Ticker for read-only/report-only smoke-test preflight commands.",
    )
    parser.add_argument(
        "--side",
        default="",
        help="Side for read-only/report-only smoke-test preflight commands: buy or sell.",
    )
    parser.add_argument(
        "--quantity",
        default="",
        help="Quantity for read-only/report-only smoke-test preflight commands.",
    )
    parser.add_argument(
        "--crypto-strategy-lab",
        action="store_true",
        help="Run a research-only crypto strategy lab with daily yfinance-compatible history.",
    )
    parser.add_argument(
        "--crypto-strategy-report",
        action="store_true",
        help="Create a research-only crypto strategy summary report from saved lab results.",
    )
    parser.add_argument(
        "--crypto-strategy-decision-report",
        action="store_true",
        help="Create a research-only crypto strategy decision report from saved crypto reports.",
    )
    parser.add_argument(
        "--crypto-cost-stress-report",
        action="store_true",
        help="Create a research-only crypto strategy cost stress report.",
    )
    parser.add_argument(
        "--crypto-robustness-report",
        action="store_true",
        help="Create a research-only crypto robustness report across fixed chronological splits.",
    )
    parser.add_argument(
        "--crypto-period-diagnostics",
        action="store_true",
        help="Create a research-only diagnostic report for weak crypto robustness periods.",
    )
    parser.add_argument(
        "--preview-crypto-signals",
        action="store_true",
        help="Preview current crypto research candidate signals without execution.",
    )
    parser.add_argument(
        "--show-crypto-monitor",
        action="store_true",
        help="Display saved crypto signal and research status CSVs without refreshing data.",
    )
    parser.add_argument(
        "--crypto-research-state-report",
        action="store_true",
        help="Create a saved-data-only crypto research checkpoint report.",
    )
    parser.add_argument(
        "--ticker-universe-readiness-report",
        action="store_true",
        help="Create a research-only larger ticker universe readiness report without execution.",
    )
    parser.add_argument(
        "--market-monitor-snapshot",
        action="store_true",
        help="Create a research-only intraday market monitoring snapshot without execution.",
    )
    parser.add_argument(
        "--show-market-monitor",
        action="store_true",
        help="Display the saved market monitor snapshot CSV without refreshing data.",
    )
    parser.add_argument(
        "--market-monitor-quality-report",
        action="store_true",
        help="Create a saved-CSV quality report for the market monitor snapshot without refreshing data.",
    )
    parser.add_argument(
        "--refresh-market-monitor",
        action="store_true",
        help="Refresh the safe market monitor report/display chain without execution.",
    )
    parser.add_argument(
        "--market-monitor-scheduling-readiness-report",
        action="store_true",
        help="Create a report-only scheduling readiness audit for market monitor refresh.",
    )
    parser.add_argument(
        "--monitor-lockfile-readiness-report",
        action="store_true",
        help="Create a static report-only no-overlap/lockfile readiness design audit.",
    )
    parser.add_argument(
        "--preview-promoted-strategies",
        action="store_true",
        help="Preview current signals for promoted research candidates without trading.",
    )
    parser.add_argument(
        "--preview-promoted-actions",
        action="store_true",
        help="Compare promoted desired positions with paper positions without trading.",
    )
    parser.add_argument(
        "--use-paper-positions-readonly",
        action="store_true",
        help="With --preview-promoted-actions or --qqq100-action-preview only, read Alpaca paper positions for preview context without trading.",
    )
    parser.add_argument(
        "--show-promoted-actions",
        action="store_true",
        help="Display the saved promoted action preview CSV without trading.",
    )
    parser.add_argument(
        "--promoted-risk-preview",
        action="store_true",
        help="Create a research-only risk preview from saved promoted strategy CSVs.",
    )
    parser.add_argument(
        "--promoted-consensus-preview",
        action="store_true",
        help="Create a research-only consensus preview from saved promoted strategy rows.",
    )
    parser.add_argument(
        "--promoted-decision-preview",
        action="store_true",
        help="Create a research-only decision policy preview from saved promoted reports.",
    )
    parser.add_argument(
        "--show-promoted-decision",
        action="store_true",
        help="Display the saved promoted decision preview CSV without trading.",
    )
    parser.add_argument(
        "--refresh-promoted-review",
        action="store_true",
        help="Refresh the promoted strategy review chain without execution.",
    )
    parser.add_argument(
        "--deployment-readiness-report",
        action="store_true",
        help="Create a local VPS/server deployment readiness audit without deploying or executing.",
    )
    parser.add_argument(
        "--vps-operations-readiness-report",
        action="store_true",
        help="Create a report-only VPS/Hermes operations readiness audit without scheduling or execution.",
    )
    parser.add_argument(
        "--vps-monitoring-status",
        action="store_true",
        help="Display a VPS-safe monitoring status summary without Alpaca, scheduling, or execution.",
    )
    parser.add_argument(
        "--vps-daily-monitoring-summary",
        action="store_true",
        help="Display a concise VPS-safe daily monitoring summary without refresh, scheduling, or execution.",
    )
    parser.add_argument(
        "--portfolio-risk-policy-report",
        action="store_true",
        help="Create a research-only portfolio risk policy audit without enforcing execution gates.",
    )
    parser.add_argument(
        "--show-portfolio-risk-policy",
        action="store_true",
        help="Display the saved portfolio risk policy report CSV without enforcing risk or trading.",
    )
    parser.add_argument(
        "--paper-kill-switch-readiness-report",
        action="store_true",
        help="Create a reporting-only readiness audit for future paper kill-switch design.",
    )
    parser.add_argument(
        "--paper-kill-switch-gate-report",
        action="store_true",
        help="Create a design/report-only paper kill-switch gate scaffold without execution.",
    )
    parser.add_argument(
        "--paper-execution-protection-report",
        action="store_true",
        help="Create a saved-data/static paper execution protection checkpoint without execution.",
    )
    parser.add_argument(
        "--normal-bot-execution-policy-report",
        action="store_true",
        help="Create a saved-data/static Option A normal bot execution policy report without execution.",
    )
    parser.add_argument(
        "--execution-eligibility-report",
        action="store_true",
        help="Create a saved-data-only execution eligibility report without approving execution.",
    )
    parser.add_argument(
        "--build-research-dashboard",
        action="store_true",
        help="Build a static saved-CSV research dashboard HTML file without running a server.",
    )
    parser.add_argument(
        "--show-promoted-risk",
        action="store_true",
        help="Display the saved promoted risk preview CSV without trading.",
    )
    parser.add_argument(
        "--preview-slow-sma-signals",
        action="store_true",
        help="Preview today's slow SMA crossover signals without trading.",
    )
    parser.add_argument(
        "--preview-slow-sma-actions",
        action="store_true",
        help="Preview target-position actions for the slow SMA strategy without trading.",
    )
    parser.add_argument(
        "--execute-slow-sma-paper",
        action="store_true",
        help="Align Alpaca paper positions with slow SMA target positions.",
    )
    parser.add_argument(
        "--confirm-slow-sma-paper",
        action="store_true",
        help="Required with --execute-slow-sma-paper before any paper orders can be submitted.",
    )
    parser.add_argument(
        "--research-universe",
        action="store_true",
        help="Use the broader research universe for research commands.",
    )
    parser.add_argument(
        "--etf-universe",
        action="store_true",
        help="Use the ETF-only research universe for supported research commands.",
    )
    parser.add_argument(
        "--plot-strategy-results",
        action="store_true",
        help="Create simple PNG charts from saved strategy comparison CSV files.",
    )
    return parser.parse_args(argv)
