from src.eldermove.session import build_session_report

def report(mode, left_speed, right_speed, left_accuracy, right_accuracy):
    return {"context":{"task_mode":mode,"dominant_hand":"right","affected_hand":"right"}, "screening":{"observed_primary_hand":"left"}, "metrics":{"left_mean_speed":left_speed,"right_mean_speed":right_speed,"left_smoothness_score":80,"right_smoothness_score":80,"left_accuracy_score":left_accuracy,"right_accuracy_score":right_accuracy}}

def test_session_uses_guided_performance_and_flags_possible_nonuse():
    result = build_session_report({"free_choice":report("free_choice",1,1,80,80),"left_guided":report("left_guided",2,1,90,50),"right_guided":report("right_guided",1,1,50,90)})
    assert result["accuracy_available"] is True
    assert result["possible_learned_nonuse"] == "มีสัญญาณให้ตรวจต่อ"
