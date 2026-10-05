"""工具统一返回。排盘结果放在 data，依据放在 evidence。"""
VERSION = "rules-v1"


def ok(data: dict, evidence: list, warnings: list | None = None) -> dict:
    """
    :param data: 排盘结果。例如 {"pillars": {"year": "甲子"}}
    :param evidence: 计算依据。例如 ["四柱来自 lunar_python"]
    :param warnings: 未参与计算的输入。例如 ["地点未用于排盘"]
    :return: ok 为 true 的工具结果
    """
    return {
        "ok": True,
        "data": data,
        "evidence": evidence,
        "warnings": warnings or [],
        "version": VERSION,
    }


def fail(code: str, message: str) -> dict:
    """
    :param code: 错误码。例如 "invalid_date"
    :param message: 给人看的说明。例如 "出生日期格式不正确"
    :return: ok 为 false 的工具结果
    """
    return {
        "ok": False,
        "error": code,
        "message": message,
        "data": {},
        "evidence": [],
        "warnings": [],
        "version": VERSION,
    }
