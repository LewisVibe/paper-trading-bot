from trading_bot.research.paper_live_evidence_audit import (
    INPUT_FILES,
    evaluate_paper_live_saved_evidence,
)


def empty_inputs() -> dict[str, list[dict[str, str]]]:
    return {name: [] for name in INPUT_FILES}


def test_missing_postcheck_quantity_makes_alignment_unverified():
    inputs = empty_inputs()
    inputs["qqq100_preview_signal"] = [{"desired_position": "long"}]
    inputs["qqq100_action_preview"] = [
        {
            "current_position_status": "paper_position_long",
            "alignment_state": "aligned_long",
        }
    ]
    inputs["qqq100_paper_execution_result"] = [{"order_status": "filled"}]

    snapshot = evaluate_paper_live_saved_evidence(inputs=inputs)

    assert snapshot.saved_current_position_state == "paper_position_long"
    assert snapshot.saved_current_position_quantity == "unavailable"
    assert snapshot.current_alignment_state == "qqq100_alignment_unverified_missing_saved_quantity"
    assert snapshot.aligned_long_after_saved_fill is False
    assert snapshot.complete_for_state_reconciliation is False
    assert "missing_file:data\\qqq100_paper_postcheck.csv" in snapshot.exact_missing_items
    assert "missing_field:position_quantity_abs_or_current_position_quantity_abs" in snapshot.exact_missing_items


def test_postcheck_quantity_allows_aligned_long_after_saved_fill():
    inputs = empty_inputs()
    inputs["qqq100_preview_signal"] = [{"desired_position": "long"}]
    inputs["qqq100_action_preview"] = [{"current_position_status": "paper_position_long"}]
    inputs["qqq100_paper_postcheck"] = [
        {
            "position_status": "paper_position_long",
            "position_quantity_abs": "1",
            "alignment_state": "aligned_long",
        }
    ]
    inputs["qqq100_paper_execution_result"] = [{"order_status": "filled"}]

    snapshot = evaluate_paper_live_saved_evidence(inputs=inputs)

    assert snapshot.saved_current_position_quantity == "1"
    assert snapshot.current_alignment_state == "aligned_long"
    assert snapshot.aligned_long_after_saved_fill is True
    assert snapshot.complete_for_state_reconciliation is True
