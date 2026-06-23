from src.eldermove.analysis.reasoning import infer_hand_use


def test_reasoning_flags_mismatch_between_prediction_and_observed_choice() -> None:
    metrics = {
        "left_mean_speed": 1.0, "right_mean_speed": 0.5,
        "left_trajectory_control": 90.0, "right_trajectory_control": 45.0,
        "left_path_efficiency": 90.0, "right_path_efficiency": 45.0,
        "left_smoothness_score": 85.0, "right_smoothness_score": 40.0,
        "left_activity": 1.0, "right_activity": 8.0,
    }
    result = infer_hand_use(metrics)
    assert result["predicted_natural_dominance"] == "left"
    assert result["observed_hand_choice"] == "right"
    assert result["learned_non_use_hypothesis"] == "possible_left_learned_non_use"
