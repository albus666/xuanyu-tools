from xuanyu_tools.bazi import calculate_bazi
from xuanyu_tools.registry import tool_schemas
from xuanyu_tools.ziwei import calculate_ziwei, _time_index


def test_bazi_rejects_bad_date():
    result = calculate_bazi({"birth_date": "2000-13-40", "gender": "女"})
    assert result["ok"] is False
    assert result["error"] == "invalid_date"


def test_bazi_rejects_true_solar_without_changing_chart():
    result = calculate_bazi({
        "birth_date": "2000-08-16",
        "birth_time": "14:30",
        "gender": "女",
        "use_true_solar": True,
    })
    assert result["ok"] is False
    assert result["error"] == "true_solar_unsupported"


def test_bazi_requires_gender():
    result = calculate_bazi({"birth_date": "2000-08-16", "birth_time": "14:30"})
    assert result["ok"] is False
    assert result["error"] == "invalid_gender"


def test_bazi_returns_complete_chart():
    result = calculate_bazi({
        "birth_date": "2000-08-16",
        "birth_time": "14:30",
        "gender": "女",
        "place": "杭州",
        "for_year": 2005,
    })
    assert result["ok"] is True
    data = result["data"]
    assert len(data["pillars"]["year"]) == 2
    assert data["day_master"]
    assert data["wuxing_scores"]
    assert data["xiyongshen"]["用神"]
    assert data["nayin"]["year"] == "白蜡金"
    assert data["kongwang"]["day"] == "寅卯"
    assert data["shishen"]["stem"]["year"] == "偏财"
    assert data["jiaoyun"]["start_solar"] == "2003-08-16 14:30:00"
    current = next(item for item in data["dayun"] if item.get("current"))
    assert current["pillar"] == "癸未"
    assert data["liunian"][0]["year"] == 2003
    assert "地点已记录，但未参与排盘" in result["warnings"]
    names = [item["function"]["name"] for item in tool_schemas()]
    assert names == ["calculate_bazi", "calculate_ziwei"]


def test_time_index_matches_xuanyu_rule():
    assert _time_index(23) == 12
    assert _time_index(0) == 0
    assert _time_index(14) == 7


def test_ziwei_rejects_missing_gender():
    result = calculate_ziwei({"birth_date": "2000-08-16", "birth_time": "14:30"})
    assert result["ok"] is False
    assert result["error"] == "invalid_gender"


def test_ziwei_returns_twelve_palaces():
    result = calculate_ziwei({
        "birth_date": "2000-08-16",
        "birth_time": "14:30",
        "gender": "女",
        "target_date": "2020-08-16",
    })
    assert result["ok"] is True
    assert len(result["data"]["palaces"]) == 12
    assert result["data"]["five_elements_class"]
    assert "iztro" in result["evidence"][0]
