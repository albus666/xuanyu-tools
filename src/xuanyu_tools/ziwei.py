"""紫微工具。参数校验和排盘都使用本项目 rules/ziwei 里的算法副本。"""
from datetime import date

from .bazi import _clock, _date
from .envelope import fail, ok
from .engines import load_ziwei


def calculate_ziwei(arguments: dict) -> dict:
    """按出生日期、时辰和性别排紫微命盘。

    :param arguments: 例如 {"birth_date": "2000-08-16", "birth_time": "14:30", "gender": "女"}
    :return: 十二宫、主星、命身和五行局。地点和真太阳时不参与计算
    """
    if arguments.get("use_true_solar") is True:
        return fail("true_solar_unsupported", "当前工具不校正真太阳时")
    birth_date = str(arguments.get("birth_date", "")).strip()
    if _date(birth_date) is None:
        return fail("invalid_date", "出生日期格式不正确，需要 YYYY-MM-DD")
    gender = str(arguments.get("gender", "")).strip()
    if gender not in {"男", "女"}:
        return fail("invalid_gender", "性别需要是男或女")

    if "birth_time_index" in arguments:
        index = arguments.get("birth_time_index")
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= 12:
            return fail("invalid_time", "出生时辰序号需要是 0 到 12")
    else:
        clock = _clock(str(arguments.get("birth_time", "")).strip())
        if clock is None:
            return fail("invalid_time", "出生时间格式不正确，需要 HH:MM")
        index = _time_index(clock[0])

    target = str(arguments.get("target_date", "")).strip() or date.today().isoformat()
    if _date(target) is None:
        return fail("invalid_date", "运限日期格式不正确，需要 YYYY-MM-DD")

    warnings = []
    if str(arguments.get("place", "")).strip():
        warnings.append("地点已记录，但未参与排盘")

    payload = {
        "birthDate": birth_date,
        "birthTimeIndex": index,
        "gender": gender,
        "targetDate": target,
        "targetTimeIndex": index,
    }
    try:
        parse, calculate, input_error, engine_error = load_ziwei()
    except Exception:
        return fail("engine_unavailable", "紫微排盘模块不可用")
    try:
        chart = calculate(parse(payload))
    except input_error as exc:
        return fail("invalid_argument", str(exc))
    except engine_error:
        return fail("engine_unavailable", "紫微排盘模块不可用")

    astrolabe = chart["astrolabe"]
    palaces = [
        {
            "name": palace.get("name", ""),
            "heavenly_stem": palace.get("heavenlyStem", ""),
            "earthly_branch": palace.get("earthlyBranch", ""),
            "major_stars": [star.get("name", "") for star in palace.get("majorStars") or []],
            "is_body_palace": bool(palace.get("isBodyPalace")),
        }
        for palace in astrolabe.get("palaces") or []
    ]
    data = {
        "gender": astrolabe.get("gender"),
        "solar_date": astrolabe.get("solarDate"),
        "lunar_date": astrolabe.get("lunarDate"),
        "time": astrolabe.get("time"),
        "time_range": astrolabe.get("timeRange"),
        "soul": astrolabe.get("soul"),
        "body": astrolabe.get("body"),
        "five_elements_class": astrolabe.get("fiveElementsClass"),
        "palaces": palaces,
        "rule_code": chart.get("ruleCode"),
    }
    evidence = [
        "命盘来自本项目的紫微算法副本，引擎为 iztro 2.5.8",
        f"出生时辰序号为 {index}",
    ]
    return ok(data, evidence, warnings)


def _time_index(hour: int) -> int:
    """把钟点换成玄遇使用的 0 到 12。23 点为 12，0 点为 0。

    :param hour: 0 到 23
    :return: 时辰序号
    """
    if hour == 23:
        return 12
    if hour == 0:
        return 0
    return min(11, max(1, (hour + 1) // 2))
