from xuanyu_tools.bazi import calculate_bazi
from xuanyu_tools.call_log import format_tool_log
import json


def test_log_shows_arguments_and_marks_missing_timezone():
    result = calculate_bazi({
        "birth_date": "2005-05-09",
        "birth_time": "14:30",
        "gender": "男",
    })
    text = format_tool_log("calculate_bazi", {
        "birth_date": "2005-05-09",
        "birth_time": "14:30",
        "gender": "男",
    }, json.dumps(result, ensure_ascii=False))
    assert "birth_date=2005-05-09" in text
    assert "birth_time=14:30" in text
    assert "gender=男" in text
    assert "place=未提供" in text
    assert "timezone=未提供，不参与排盘" in text
    assert "time_basis=clock_time" in text
    assert "use_true_solar=false" in text
    assert "birth_time_index=7，仅供对照，八字按钟点排盘" in text
    assert text.endswith("→ success")


def test_log_shows_validation_error():
    result = calculate_bazi({
        "birth_date": "2005-05-09",
        "birth_time": "14:30",
        "gender": "男",
        "use_true_solar": True,
    })
    text = format_tool_log("calculate_bazi", {
        "birth_date": "2005-05-09",
        "birth_time": "14:30",
        "gender": "男",
        "use_true_solar": True,
    }, json.dumps(result, ensure_ascii=False))
    assert "time_basis=true_solar" in text
    assert "→ true_solar_unsupported:" in text
