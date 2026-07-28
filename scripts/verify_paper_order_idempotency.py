"""Static fail-closed audit for paper-order gateway ownership and client IDs."""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_PATHS = [ROOT / "bot.py", *sorted((ROOT / "trading_bot").rglob("*.py"))]
EXPECTED_GATEWAY_CALLERS = {
    ("trading_bot/cli/application.py", "run_paper_order_test", "MANUAL_TEST"),
    ("trading_bot/cli/application.py", "run_execute_qqq100_paper", "QQQ100"),
    ("trading_bot/cli/application.py", "process_slow_sma_execution_ticker", "SLOW_SMA"),
    (
        "trading_bot/runners/vol_targeted_growth_paper.py",
        "run_execute_vol_targeted_growth_paper",
        "VOL_TARGETED_GROWTH",
    ),
    (
        "trading_bot/runners/vol_targeted_growth_paper.py",
        "run_vol_targeted_growth_auto_paper",
        "VOL_TARGETED_GROWTH",
    ),
}


def enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent.name
        parent = parents.get(parent)
    return "<module>"


def main() -> int:
    direct_submitters: list[tuple[str, str]] = []
    gateway_callers: set[tuple[str, str, str]] = set()
    missing_client_ids: list[tuple[str, str]] = []
    manual_recent_order_checks: list[tuple[int, bool]] = []
    manual_gateway_submissions: list[int] = []

    for path in PRODUCTION_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            owner = enclosing_function(node, parents)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "submit_order":
                direct_submitters.append((relative, owner))
            if (
                relative == "trading_bot/cli/application.py"
                and owner == "run_paper_order_test"
                and isinstance(node.func, ast.Name)
            ):
                if node.func.id == "recent_matching_manual_smoke_test_order_check":
                    ancestor = parents.get(node)
                    nested_in_special_smoke_gate = False
                    while ancestor is not None:
                        if (
                            isinstance(ancestor, ast.If)
                            and ast.unparse(ancestor.test) == "smoke_test_gate_decision is not None"
                        ):
                            nested_in_special_smoke_gate = True
                        ancestor = parents.get(ancestor)
                    manual_recent_order_checks.append((node.lineno, nested_in_special_smoke_gate))
                elif node.func.id == "submit_paper_order":
                    manual_gateway_submissions.append(node.lineno)
            if not (isinstance(node.func, ast.Name) and node.func.id == "PaperOrderRequest"):
                continue
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            route = keywords.get("route")
            if not isinstance(route, ast.Attribute):
                continue
            gateway_callers.add((relative, owner, route.attr))
            if keywords.get("client_order_id") is None:
                missing_client_ids.append((relative, owner))

    failures: list[str] = []
    expected_submitters = [("trading_bot/paper_orders.py", "submit_paper_order")]
    if direct_submitters != expected_submitters:
        failures.append(f"direct submit_order ownership changed: {direct_submitters!r}")
    if gateway_callers != EXPECTED_GATEWAY_CALLERS:
        failures.append(
            "paper-order caller inventory changed: "
            f"expected={sorted(EXPECTED_GATEWAY_CALLERS)!r} actual={sorted(gateway_callers)!r}"
        )
    if missing_client_ids:
        failures.append(f"PaperOrderRequest calls missing client_order_id: {missing_client_ids!r}")
    if len(manual_recent_order_checks) != 1:
        failures.append(
            "manual paper-order route must have exactly one recent matching-order check: "
            f"{manual_recent_order_checks!r}"
        )
    elif manual_recent_order_checks[0][1]:
        failures.append("manual recent matching-order check is nested in the special smoke-test gate")
    if len(manual_gateway_submissions) != 1:
        failures.append(
            "manual paper-order route must have exactly one gateway submission: "
            f"{manual_gateway_submissions!r}"
        )
    elif (
        manual_recent_order_checks
        and manual_recent_order_checks[0][0] >= manual_gateway_submissions[0]
    ):
        failures.append("manual recent matching-order check must occur before gateway submission")

    if failures:
        print("PAPER ORDER IDEMPOTENCY AUDIT: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("PAPER ORDER IDEMPOTENCY AUDIT: PASS")
    print("Direct broker submit owner: trading_bot/paper_orders.py::submit_paper_order")
    print(f"Gateway callers with client IDs: {len(gateway_callers)}")
    print("Manual recent matching-order check: unconditional and before gateway submission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
