# -*- coding: utf-8 -*-
"""
六十甲子论（60decline.json）用神条文 → 缘分匹配用的「用神」「喜神」单字五行。

条文惯例：首用/首取…为「用神」所主天干；其次/次之/次选…为「喜神」；仅一条时二者相同。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

logger = __import__("logging").getLogger(__name__)

_GAN_TO_WX = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}
_GANS = frozenset(_GAN_TO_WX.keys())

# 地支本气五行（条文偶见「首用寅木」等，无天干可扫）
_ZHI_WX = {
    "寅": "木",
    "卯": "木",
    "巳": "火",
    "午": "火",
    "申": "金",
    "酉": "金",
    "亥": "水",
    "子": "水",
    "辰": "土",
    "戌": "土",
    "丑": "土",
    "未": "土",
}

_DATA_PATH = Path(__file__).resolve().parent / "data" / "60decline.json"
_decline_cache: dict | None = None


def _load_60decline() -> dict:
    global _decline_cache
    if _decline_cache is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _decline_cache = json.load(f)
    return _decline_cache


def _scan_first_gan(text: str) -> str | None:
    for c in text:
        if c in _GANS:
            return c
    return None


def _scan_first_wx_symbol(text: str) -> tuple[str, str] | None:
    """返回 (记号, 五行)。先扫十天干，再扫地支本气（避免「辰中乙」误取辰土）。"""
    for c in text:
        if c in _GAN_TO_WX:
            return (c, _GAN_TO_WX[c])
    for c in text:
        if c in _ZHI_WX:
            return (c, _ZHI_WX[c])
    return None


_SECONDARY_SPLIT = re.compile(
    r"(?:其次|次而|次之|次选|次用|再次|再而|再选)"
)


def parse_yongshen_ys_to_xiyong(ys: str) -> dict[str, str] | None:
    """
    从「用神」条文解析出 {\"用神\",\"喜神\"}，值为 金木水火土 之一。
    解析失败返回 None（调用方回退量化算法）。
    """
    s = (ys or "").strip()
    if not s:
        return None

    sec_m = _SECONDARY_SPLIT.search(s)
    head = s[: sec_m.start()] if sec_m else s
    tail = s[sec_m.end() :] if sec_m else ""

    yong_sym: str | None = None
    yong_wx: str | None = None
    for kw in ("首用", "首取", "首喜", "最喜"):
        i = head.find(kw)
        if i >= 0:
            chunk = head[i + len(kw) : i + len(kw) + 30]
            got = _scan_first_wx_symbol(chunk)
            if got:
                yong_sym, yong_wx = got
                break

    if not yong_wx:
        m = re.search(r"([甲乙丙丁戊己庚辛壬癸])[水火木金土]?(?:为先|为要)", head)
        if m:
            yong_sym = m.group(1)
            yong_wx = _GAN_TO_WX.get(yong_sym)

    if not yong_wx:
        return None

    xi_wx: str | None = None
    if tail.strip():
        got2 = _scan_first_wx_symbol(tail)
        if got2:
            xi_wx = got2[1]

    if xi_wx is None and yong_sym:
        idx = head.find(yong_sym)
        if idx >= 0:
            rest = head[idx + len(yong_sym) : idx + len(yong_sym) + 44]
            for c in rest:
                if c in _GAN_TO_WX and _GAN_TO_WX[c] != yong_wx:
                    xi_wx = _GAN_TO_WX[c]
                    break
                if c in _ZHI_WX and _ZHI_WX[c] != yong_wx:
                    xi_wx = _ZHI_WX[c]
                    break
    if xi_wx is None:
        xi_wx = yong_wx

    return {"用神": yong_wx, "喜神": xi_wx}


def lookup_xiyongshen_from_60decline(day_gan: str, month_pillar: str) -> dict[str, str] | None:
    """
    day_gan: 日干一字；month_pillar: 月柱干支如「壬辰」（与 60decline.json 键一致）。
    """
    if not day_gan or len(month_pillar) < 2:
        return None
    try:
        data = _load_60decline()
        by_day = data.get(day_gan)
        if not isinstance(by_day, dict):
            return None
        entry = by_day.get(month_pillar)
        if not isinstance(entry, dict):
            return None
        ys = str(entry.get("ys") or "").strip()
        if not ys:
            return None
        return parse_yongshen_ys_to_xiyong(ys)
    except OSError as e:
        logger.warning("60decline 数据读取失败: %s", e)
        return None
    except Exception as e:
        logger.warning("60decline 查表异常: %s", e)
        return None
