"""八字工具。一次返回完整命盘，回答时再按问题选取字段。"""
import re
from datetime import date

from lunar_python import Solar
from lunar_python.util import LunarUtil

from .envelope import fail, ok
from .engines import load_bazi
from .rules.bazi.paipan_xiyongshen import app_bazi_datetime_parts

_PILLARS = ("year", "month", "day", "hour")


def calculate_bazi(arguments: dict) -> dict:
    """按公历出生时间返回四柱、五行、喜用神、纳音、空亡、十神、大运、流年和交运。

    :param arguments: 例如 {"birth_date": "2000-08-16", "birth_time": "14:30", "gender": "女", "for_year": 2005}
    :return: 统一工具结果。性别必填。真太阳时请求会直接拒绝
    """
    if arguments.get("use_true_solar") is True:
        return fail("true_solar_unsupported", "当前工具不校正真太阳时")
    birth_date = str(arguments.get("birth_date", "")).strip()
    birth_time = str(arguments.get("birth_time", "12:00")).strip() or "12:00"
    parsed = _date(birth_date)
    if parsed is None:
        return fail("invalid_date", "出生日期格式不正确，需要 YYYY-MM-DD")
    if _clock(birth_time) is None:
        return fail("invalid_time", "出生时间格式不正确，需要 HH:MM")
    is_male = _is_male(str(arguments.get("gender", "")).strip())
    if is_male is None:
        return fail("invalid_gender", "性别需要是男或女，大运和交运依赖性别")
    for_year = arguments.get("for_year", date.today().year)
    if isinstance(for_year, bool) or not isinstance(for_year, int):
        return fail("invalid_year", "for_year 需要是公历年份")

    warnings = []
    if str(arguments.get("place", "")).strip():
        warnings.append("地点已记录，但未参与排盘")
    try:
        detail_fn, _dayun_fn = load_bazi()
        detail = detail_fn(parsed.isoformat(), birth_time)
        chart = _chart(parsed, birth_time, is_male, for_year)
    except Exception:
        return fail("engine_unavailable", "八字排盘模块不可用")
    if not detail or not chart:
        return fail("engine_unavailable", "八字排盘没有得到四柱")
    if chart["liunian"] == []:
        warnings.append(f"{for_year} 年不在返回的大运范围内，未附流年")

    chart["birth_date"] = detail.get("birthDate")
    chart["birth_time"] = detail.get("birthTime")
    chart["day_master"] = detail.get("dayMaster")
    chart["wuxing_scores"] = detail.get("wuxingScores")
    chart["xiyongshen"] = detail.get("xiyongshen")
    return ok(
        chart,
        ["四柱、五行、喜用神、纳音、空亡、十神、大运、流年和交运一次算完，使用钟表时间和 sect=1"],
        warnings,
    )


def _chart(parsed: date, birth_time: str, is_male: int, for_year: int) -> dict:
    """
    :param parsed: 公历出生日期
    :param birth_time: HH:MM
    :param is_male: 1 为男，0 为女
    :param for_year: 用来选取所在大运及其流年
    :return: 不含五行分数的命盘字段
    """
    y, m, d, h, mi = app_bazi_datetime_parts(parsed, birth_time)
    eight = Solar.fromYmdHms(y, m, d, h, mi, 0).getLunar().getEightChar()
    eight.setSect(1)
    getters = {
        "nayin": (eight.getYearNaYin, eight.getMonthNaYin, eight.getDayNaYin, eight.getTimeNaYin),
        "kongwang": (eight.getYearXunKong, eight.getMonthXunKong, eight.getDayXunKong, eight.getTimeXunKong),
        "stem": (eight.getYearShiShenGan, eight.getMonthShiShenGan, eight.getDayShiShenGan, eight.getTimeShiShenGan),
        "branch": (eight.getYearShiShenZhi, eight.getMonthShiShenZhi, eight.getDayShiShenZhi, eight.getTimeShiShenZhi),
        "pillar": (eight.getYear, eight.getMonth, eight.getDay, eight.getTime),
    }
    yun = eight.getYun(is_male, 1)
    start = yun.getStartSolar()
    dayun = []
    selected = None
    for item in yun.getDaYun(9):
        if item.getIndex() < 1:
            continue
        row = {
            "pillar": item.getGanZhi(),
            "start_age": item.getStartAge(),
            "end_age": item.getEndAge(),
            "start_year": item.getStartYear(),
            "end_year": item.getEndYear(),
            "kongwang": item.getXunKong(),
        }
        if row["start_year"] <= for_year <= row["end_year"]:
            selected = item
            row["current"] = True
        dayun.append(row)
    liunian = []
    if selected is not None:
        day_gan = eight.getDayGan()
        for item in selected.getLiuNian():
            pillar = item.getGanZhi()
            liunian.append({
                "year": item.getYear(),
                "age": item.getAge(),
                "pillar": pillar,
                "kongwang": item.getXunKong(),
                "stem_shishen": LunarUtil.SHI_SHEN.get(day_gan + pillar[:1], ""),
            })
    return {
        "pillars": {name: getters["pillar"][i]() for i, name in enumerate(_PILLARS)},
        "nayin": {name: getters["nayin"][i]() for i, name in enumerate(_PILLARS)},
        "kongwang": {name: getters["kongwang"][i]() for i, name in enumerate(_PILLARS)},
        "shishen": {
            "stem": {name: getters["stem"][i]() for i, name in enumerate(_PILLARS)},
            "branch": {name: list(getters["branch"][i]()) for i, name in enumerate(_PILLARS)},
        },
        "jiaoyun": {
            "start_years": yun.getStartYear(),
            "start_months": yun.getStartMonth(),
            "start_days": yun.getStartDay(),
            "start_hours": yun.getStartHour(),
            "start_solar": start.toYmdHms(),
        },
        "dayun": dayun,
        "liunian": liunian,
        "for_year": for_year,
    }


def _date(value: str):
    """
    :param value: 例如 "2000-08-16"
    :return: 合法公历日期，否则 None
    """
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _clock(value: str):
    """
    :param value: 例如 "14:30"
    :return: (hour, minute)，格式不对时为 None
    """
    matched = re.fullmatch(r"(\d{1,2}):(\d{2})", value)
    if matched is None:
        return None
    hour, minute = int(matched.group(1)), int(matched.group(2))
    if hour > 23 or minute > 59:
        return None
    return hour, minute


def _is_male(gender: str):
    """
    :param gender: 例如 "女"
    :return: 男为 1，女为 0，无法识别时为 None
    """
    if gender in {"男", "male", "m"}:
        return 1
    if gender in {"女", "female", "f"}:
        return 0
    return None
