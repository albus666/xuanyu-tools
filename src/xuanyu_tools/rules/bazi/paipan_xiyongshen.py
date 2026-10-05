# -*- coding: utf-8 -*-
"""
与 Flutter `paipan/utils/wu_xing_liang_hua.dart` 对齐的五行量化 + 喜用神推导。
四柱由 lunar_python（与 6tail 逻辑一致）从公历出生日期时辰起盘。
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)

_WX_MU_HUO_TU_JIN_SHUI = ["木", "火", "土", "金", "水"]

_GAN_WUXING = {"甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2, "己": 2, "庚": 3, "辛": 3, "壬": 4, "癸": 4}

_ZHI_CANG_GAN = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}

_ZHI_CANG_SCORE = {
    "子": [100],
    "丑": [60, 30, 10],
    "寅": [60, 30, 10],
    "卯": [100],
    "辰": [60, 30, 10],
    "巳": [60, 30, 10],
    "午": [70, 30],
    "未": [60, 30, 10],
    "申": [60, 30, 10],
    "酉": [100],
    "戌": [60, 30, 10],
    "亥": [70, 30],
}

_STEM_WEIGHTS = [0.8, 0.8, 1.2, 1.0]
_BRANCH_WEIGHTS = [1.0, 1.2, 1.8, 1.0]


def _parse_ymd_hm(birth_date, birth_time) -> tuple[int, int, int, int, int]:
    if isinstance(birth_date, datetime):
        y, m, d = birth_date.year, birth_date.month, birth_date.day
    elif isinstance(birth_date, date):
        y, m, d = birth_date.year, birth_date.month, birth_date.day
    else:
        s = str(birth_date).strip()[:10]
        parts = s.split("-")
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    h, mi = 0, 0
    if birth_time:
        t = str(birth_time).strip().replace("：", ":")
        mp = re.match(r"^(\d{1,2}):(\d{1,2})", t)
        if mp:
            h = int(mp.group(1)) % 24
            mi = int(mp.group(2)) % 60
    return y, m, d, h, mi


def app_bazi_datetime_parts(birth_date, birth_time) -> tuple[int, int, int, int, int]:
    """Mirror Flutter's fixed late-rat-hour rule exactly.

    The APP uses sect=1 and normalises 23:xx to 00:xx of the next civil day
    before asking the lunar library for all four pillars.  Keeping the
    normalisation here also makes the hour stem follow the same next-day stem.
    """
    y, m, d, h, mi = _parse_ymd_hm(birth_date, birth_time)
    if h >= 23:
        effective = datetime(y, m, d, h, mi) + timedelta(days=1)
        return effective.year, effective.month, effective.day, h - 23, mi
    return y, m, d, h, mi


def _four_pillars_from_solar(y, m, d, h, mi):
    try:
        from lunar_python import Solar

        y, m, d, h, mi = app_bazi_datetime_parts(date(y, m, d), f"{h:02d}:{mi:02d}")
        ec = Solar.fromYmdHms(y, m, d, h, mi, 0).getLunar().getEightChar()
        # Flutter 固定 sect=1：23:00 起按次日，且已在上方归一化。
        if hasattr(ec, "setSect"):
            try:
                ec.setSect(1)
            except Exception:
                pass
        gans = [ec.getYearGan(), ec.getMonthGan(), ec.getDayGan(), ec.getTimeGan()]
        zhis = [ec.getYearZhi(), ec.getMonthZhi(), ec.getDayZhi(), ec.getTimeZhi()]
        return gans, zhis
    except Exception as e:
        logger.warning("lunar_python 排盘失败: %s", e)
        return None


def _compute_wuxing_scores(gans: list[str], zhis: list[str]) -> list[float]:
    raw = [0.0, 0.0, 0.0, 0.0, 0.0]
    for i in range(4):
        w_g = _STEM_WEIGHTS[i] if i < len(_STEM_WEIGHTS) else 1.0
        wx = _GAN_WUXING.get(gans[i])
        if wx is not None:
            raw[wx] += w_g
    for i in range(4):
        w_b = _BRANCH_WEIGHTS[i] if i < len(_BRANCH_WEIGHTS) else 1.0
        z = zhis[i]
        g_list = _ZHI_CANG_GAN.get(z)
        s_list = _ZHI_CANG_SCORE.get(z)
        if not g_list or not s_list or len(g_list) != len(s_list):
            continue
        total = sum(s_list)
        if total <= 0:
            continue
        for k, gan in enumerate(g_list):
            wx = _GAN_WUXING.get(gan)
            if wx is None:
                continue
            raw[wx] += w_b * (s_list[k] / total)
    return raw


def _tong_lei(scores: list[float], day_gan: str) -> float:
    dw = _GAN_WUXING.get(day_gan)
    if dw is None:
        return 0.0
    yin = (dw - 1 + 5) % 5
    return scores[dw] + scores[yin]


def _xi_yong_yin_bijie(scores: list[float], yin_wx: int, dw: int) -> str:
    sy = scores[yin_wx]
    sb = scores[dw]
    yn = _WX_MU_HUO_TU_JIN_SHUI[yin_wx]
    bn = _WX_MU_HUO_TU_JIN_SHUI[dw]
    if abs(sy - sb) < 1e-9:
        return f"{yn}、{bn}"
    return yn if sy < sb else bn


def _xi_yong_yilei_max(scores: list[float], guan_sha: int, shi_shang: int, cai: int) -> str:
    best = guan_sha
    best_v = scores[guan_sha]
    b2 = scores[shi_shang]
    if b2 > best_v + 1e-9:
        best_v = b2
        best = shi_shang
    b3 = scores[cai]
    if b3 > best_v + 1e-9:
        best = cai
    return _WX_MU_HUO_TU_JIN_SHUI[best]


def _analyze_xi_yong_shen_str(scores: list[float], day_gan: str, gans: list[str], zhis: list[str]) -> str:
    dw = _GAN_WUXING.get(day_gan)
    if dw is None:
        return ""
    tong = _tong_lei(scores, day_gan)
    total = sum(scores)
    if total < 1e-9:
        return ""
    yi = total - tong
    balance = tong - yi
    rel = abs(balance) / total
    zhong_he_ratio = 0.06
    zhong_he_abs = 3.5
    yin_wx = (dw - 1 + 5) % 5
    guan_sha = (dw + 3) % 5
    shi_shang = (dw + 1) % 5
    cai = (dw + 2) % 5

    if abs(balance) <= zhong_he_abs or rel < zhong_he_ratio:
        return _xi_yong_yin_bijie(scores, yin_wx, dw)
    if balance > 0:
        return _xi_yong_yilei_max(scores, guan_sha, shi_shang, cai)
    return _xi_yong_yin_bijie(scores, yin_wx, dw)


def _xi_yong_str_to_dict(xi_yong_shen: str) -> dict:
    """将排盘展示用喜用神字符串拆成 喜神/用神（与缘分匹配字段一致）。"""
    s = (xi_yong_shen or "").strip()
    if not s:
        return {"喜神": "木", "用神": "水"}
    parts = re.split(r"[、，,]\s*", s)
    picked: list[str] = []
    for p in parts:
        p = p.strip()
        for w in ("金", "木", "水", "火", "土"):
            if w in p:
                picked.append(w)
                break
    if not picked:
        for w in ("金", "木", "水", "火", "土"):
            if w in s:
                picked.append(w)
                break
    if not picked:
        return {"喜神": "木", "用神": "水"}
    if len(picked) == 1:
        return {"喜神": picked[0], "用神": picked[0]}
    return {"喜神": picked[0], "用神": picked[1]}


def compute_xiyongshen_from_paipan(birth_date, birth_time):
    """
    返回 {"喜神":"x","用神":"y"}。
    优先：六十甲子论（60decline.json，日干+月柱）；失败则回退五行量化推论（与 App 一致）。
    """
    try:
        y, m, d, h, mi = _parse_ymd_hm(birth_date, birth_time)
        pillars = _four_pillars_from_solar(y, m, d, h, mi)
        if not pillars:
            return None
        gans, zhis = pillars
        day_gan = gans[2]
        month_pillar = gans[1] + zhis[1]
        from .paipan_60decline_xiyongshen import lookup_xiyongshen_from_60decline

        xy60 = lookup_xiyongshen_from_60decline(day_gan, month_pillar)
        if xy60 and xy60.get("用神") and xy60.get("喜神"):
            return {"喜神": xy60["喜神"], "用神": xy60["用神"]}
        scores = _compute_wuxing_scores(gans, zhis)
        xy_str = _analyze_xi_yong_shen_str(scores, day_gan, gans, zhis)
        if not xy_str:
            return None
        return _xi_yong_str_to_dict(xy_str)
    except Exception as e:
        logger.exception("排盘喜用神计算失败: %s", e)
        return None


def compute_paipan_detail(birth_date, birth_time) -> dict | None:
    """返回命主四柱、日主、喜用神与五行量化，供今日能量等 AI 场景使用。"""
    try:
        y, m, d, h, mi = _parse_ymd_hm(birth_date, birth_time)
        pillars = _four_pillars_from_solar(y, m, d, h, mi)
        if not pillars:
            return None
        gans, zhis = pillars
        scores = _compute_wuxing_scores(gans, zhis)
        day_gan = gans[2]
        xy = compute_xiyongshen_from_paipan(birth_date, birth_time) or {"喜神": "木", "用神": "水"}
        wuxing_quant = {
            _WX_MU_HUO_TU_JIN_SHUI[i]: round(scores[i], 2) for i in range(5)
        }
        return {
            "birthDate": str(birth_date)[:10],
            "birthTime": str(birth_time or "").strip() or "未知",
            "pillars": {
                "year": gans[0] + zhis[0],
                "month": gans[1] + zhis[1],
                "day": gans[2] + zhis[2],
                "hour": gans[3] + zhis[3],
            },
            "dayMaster": day_gan,
            "xiyongshen": xy,
            "wuxingScores": wuxing_quant,
        }
    except Exception as e:
        logger.exception("compute_paipan_detail 失败: %s", e)
        return None


def compute_current_dayun(birth_date, birth_time, gender, for_date: date | None = None) -> dict | None:
    """按 lunar_python 的起运规则取得当前大运。

    大运顺逆需要性别；资料缺失时返回 ``None``，由调用方明确标注，而非
    以默认性别补算。日期按大运库提供的起止公历年落位，和 App 的大运表
    使用同一套 lunar_python 规则。
    """
    raw_gender = str(gender or "").strip().lower()
    if raw_gender in {"男", "male", "m", "1"}:
        is_male = 1
    elif raw_gender in {"女", "female", "f", "2"}:
        is_male = 0
    else:
        return None
    try:
        from lunar_python import Solar

        y, m, d, h, mi = app_bazi_datetime_parts(birth_date, birth_time)
        eight_char = Solar.fromYmdHms(y, m, d, h, mi, 0).getLunar().getEightChar()
        eight_char.setSect(1)
        yun = eight_char.getYun(is_male, 1)
        target_year = (for_date or date.today()).year
        da_yun_list = [item for item in yun.getDaYun(13) if item.getIndex() >= 1]
        current = next(
            (
                item
                for item in da_yun_list
                if item.getStartYear() <= target_year <= item.getEndYear()
            ),
            None,
        )
        if current is None:
            return None
        pillar = str(current.getGanZhi() or "").strip()
        if len(pillar) < 2:
            return None
        return {
            "pillar": pillar,
            "startAge": current.getStartAge(),
            "endAge": current.getEndAge(),
            "startYear": current.getStartYear(),
            "endYear": current.getEndYear(),
        }
    except Exception as e:
        logger.warning("当前大运计算失败: %s", e)
        return None


def compute_flow_pillars(for_date: date | None = None) -> dict | None:
    """当日流年、流月、流日干支（正午起盘，与 App 日柱一致）。"""
    try:
        d = for_date or date.today()
        pillars = _four_pillars_from_solar(d.year, d.month, d.day, 12, 0)
        if not pillars:
            return None
        gans, zhis = pillars
        return {
            "year": gans[0] + zhis[0],
            "month": gans[1] + zhis[1],
            "day": gans[2] + zhis[2],
        }
    except Exception as e:
        logger.exception("compute_flow_pillars 失败: %s", e)
        return None
