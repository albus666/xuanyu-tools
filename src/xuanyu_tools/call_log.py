"""把一次工具调用写成可公开的参数日志。不打印密钥，也不把未传入的时区说成已使用。"""
import json
import re

from .ziwei import _time_index


def format_tool_log(name: str, arguments: dict | None, content: str) -> str:
    """
    :param name: 工具名。例如 "calculate_bazi"
    :param arguments: 模型传入的参数。例如 {"birth_date": "2005-05-09", "gender": "男"}
    :param content: 工具返回的 JSON 字符串
    :return: 多行日志。缺省项写「未提供」
    """
    arguments = arguments or {}
    lines = [f"[tool-call] {name}("]
    for key, value in _fields(name, arguments):
        lines.append(f"  {key}={value},")
    lines.append(")")
    lines.append(f"→ {_outcome(content)}")
    return "\n".join(lines)


def _fields(name: str, arguments: dict) -> list[tuple[str, str]]:
    """
    :param name: 工具名
    :param arguments: 模型传入的参数
    :return: 要打印的键和值。时区没有对应参数
    """
    birth_time = str(arguments.get("birth_time", "")).strip()
    true_solar = arguments.get("use_true_solar") is True
    rows = [
        ("birth_date", _shown(arguments.get("birth_date"))),
        ("birth_time", _shown(birth_time)),
        ("gender", _shown(arguments.get("gender"))),
        ("place", _shown(arguments.get("place"))),
        ("timezone", "未提供，不参与排盘"),
        ("time_basis", "true_solar" if true_solar else "clock_time"),
        ("use_true_solar", "true" if true_solar else "false"),
        ("birth_time_index", _index(name, arguments, birth_time)),
    ]
    if "for_year" in arguments:
        rows.append(("for_year", str(arguments.get("for_year"))))
    if name == "calculate_ziwei":
        rows.append(("target_date", _shown(arguments.get("target_date"))))
    return rows


def _index(name: str, arguments: dict, birth_time: str) -> str:
    """
    :param name: 工具名
    :param arguments: 模型传入的参数
    :param birth_time: 已去掉空白的钟点
    :return: 时辰序号说明
    """
    if "birth_time_index" in arguments:
        return str(arguments.get("birth_time_index"))
    matched = re.fullmatch(r"(\d{1,2}):(\d{2})", birth_time)
    if matched is None:
        return "未提供"
    hour = int(matched.group(1))
    if hour > 23:
        return "未提供"
    derived = _time_index(hour)
    if name == "calculate_ziwei":
        return f"{derived}，由出生时间换算"
    return f"{derived}，仅供对照，八字按钟点排盘"


def _outcome(content: str) -> str:
    """
    :param content: 工具返回文本
    :return: success，或错误码和说明
    """
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return "failed: 返回不是 JSON"
    if not isinstance(payload, dict):
        return "failed: 返回不是 JSON"
    if payload.get("ok") is True:
        return "success"
    code = payload.get("error") or "failed"
    message = payload.get("message") or ""
    return f"{code}: {message}" if message else str(code)


def _shown(value) -> str:
    """
    :param value: 参数原值
    :return: 可打印文本。空值写成「未提供」
    """
    text = str(value or "").strip()
    return text or "未提供"
