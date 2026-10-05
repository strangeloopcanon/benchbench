from scripts.audit_reimbursement_decimal import audit


def test_decimal_audit_corrects_gold_and_preserves_the_low_nonzero_profile() -> None:
    result = audit()
    assert result["changed_gold"] == [
        {"id": "reifor_0000", "historical": 15991, "decimal_half_up": 15992},
        {"id": "reifor_0006", "historical": 56636, "decimal_half_up": 56637},
        {"id": "reifor_0029", "historical": 30627, "decimal_half_up": 30629},
    ]
    assert result["retained_prediction_rescores"] == {
        "gemini_3_1_pro": 13,
        "gemini_3_5_flash_high": 11,
        "gpt_5_2": 12,
        "gpt_5_4": 16,
        "gpt_5_5": 11,
        "opus": 11,
    }
    corrected_scores = list(result["retained_prediction_rescores"].values())
    assert min(corrected_scores) == 11
    assert max(corrected_scores) == 16
    assert len(corrected_scores) == 6
    assert result["actual_policy_pre_tip_rescores"] == {
        "gemini_3_1_pro": 16,
        "gemini_3_5_flash_high": 30,
        "gpt_5_2": 8,
        "gpt_5_4": 19,
        "gpt_5_5": 30,
        "opus": 25,
    }
    assert result["actual_policy_post_tip_rescores"] == {
        "gemini_3_1_pro": 25,
        "gemini_3_5_flash_high": 19,
        "gpt_5_2": 15,
        "gpt_5_4": 25,
        "gpt_5_5": 19,
        "opus": 17,
    }
