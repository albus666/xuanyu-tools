"""固定版本 iztro 的安全调用封装。"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

def _node_binary() -> str:
    try:
        from django.conf import settings
        return getattr(settings, "ZIWEI_NODE_BINARY", "node")
    except Exception:
        return "node"


ENGINE_NAME = "iztro"
ENGINE_VERSION = "2.5.8"
_RUNNER = Path(__file__).resolve().parent / "runner.js"


class ZiweiInputError(ValueError):
    """用户提交的排盘参数无效。"""


class ZiweiEngineError(RuntimeError):
    """底层排盘引擎不可用或返回异常。"""


@dataclass(frozen=True)
class ZiweiRequest:
    birth_date: str
    birth_time_index: int
    gender: str
    target_date: str
    target_time_index: int
    fix_leap: bool
    astro_type: str
    config: dict[str, str]

    @property
    def rule_code(self) -> str:
        config = self.config
        return ":".join(
            [
                f"{ENGINE_NAME}-{ENGINE_VERSION}",
                config["algorithm"],
                self.astro_type,
                config["yearDivide"],
                config["horoscopeDivide"],
                config["ageDivide"],
                config["dayDivide"],
                "leap-split" if self.fix_leap else "leap-original",
            ]
        )

    def as_engine_input(self) -> dict[str, Any]:
        return {
            "birthDate": self.birth_date,
            "birthTimeIndex": self.birth_time_index,
            "gender": self.gender,
            "targetDate": self.target_date,
            "targetTimeIndex": self.target_time_index,
            "fixLeap": self.fix_leap,
            "astroType": self.astro_type,
            "config": self.config,
        }


def _date_string(
    value: Any,
    field: str,
    *,
    min_year: int = 1900,
    max_year: int = 2099,
) -> str:
    raw = str(value or "").strip()
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise ZiweiInputError(f"{field}格式不正确") from exc
    if parsed.year < min_year or parsed.year > max_year:
        raise ZiweiInputError(f"{field}仅支持{min_year}年至{max_year}年")
    return parsed.isoformat()


def _choice(value: Any, field: str, allowed: set[str], default: str) -> str:
    raw = str(value or default).strip()
    if raw not in allowed:
        raise ZiweiInputError(f"{field}参数不支持")
    return raw


def _time_index(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ZiweiInputError(f"{field}参数不正确")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ZiweiInputError(f"{field}参数不正确") from exc
    if not 0 <= result <= 12:
        raise ZiweiInputError(f"{field}必须在0至12之间")
    return result


def parse_ziwei_request(payload: Any) -> ZiweiRequest:
    if not isinstance(payload, dict):
        raise ZiweiInputError("请求参数不正确")
    config_payload = payload.get("config")
    if config_payload is None:
        config_payload = {}
    if not isinstance(config_payload, dict):
        raise ZiweiInputError("config参数不正确")

    algorithm = _choice(
        config_payload.get("algorithm"),
        "algorithm",
        {"default", "zhongzhou"},
        "default",
    )
    astro_type = _choice(
        payload.get("astroType"),
        "astroType",
        {"heaven", "earth", "human"},
        "heaven",
    )
    if algorithm != "zhongzhou" and astro_type != "heaven":
        raise ZiweiInputError("地盘和人盘仅支持中州排法")

    config = {
        "algorithm": algorithm,
        "yearDivide": _choice(
            config_payload.get("yearDivide"),
            "yearDivide",
            {"normal", "exact"},
            "normal",
        ),
        "horoscopeDivide": _choice(
            config_payload.get("horoscopeDivide"),
            "horoscopeDivide",
            {"normal", "exact"},
            "normal",
        ),
        "ageDivide": _choice(
            config_payload.get("ageDivide"),
            "ageDivide",
            {"normal", "birthday"},
            "normal",
        ),
        "dayDivide": _choice(
            config_payload.get("dayDivide"),
            "dayDivide",
            {"current", "forward"},
            "forward",
        ),
    }
    return ZiweiRequest(
        birth_date=_date_string(payload.get("birthDate"), "出生日期"),
        birth_time_index=_time_index(payload.get("birthTimeIndex"), "出生时辰"),
        gender=_choice(payload.get("gender"), "gender", {"男", "女"}, "男"),
        target_date=_date_string(
            payload.get("targetDate"),
            "运限日期",
            min_year=1800,
            max_year=2299,
        ),
        target_time_index=_time_index(payload.get("targetTimeIndex"), "运限时辰"),
        fix_leap=payload.get("fixLeap", True) is not False,
        astro_type=astro_type,
        config=config,
    )


def calculate_ziwei(request: ZiweiRequest) -> dict[str, Any]:
    if not _RUNNER.is_file():
        raise ZiweiEngineError("紫微排盘程序缺失")
    try:
        completed = subprocess.run(
            [_node_binary(), str(_RUNNER)],
            input=json.dumps(request.as_engine_input(), ensure_ascii=False),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ZiweiEngineError("紫微排盘服务暂不可用") from exc
    if completed.returncode != 0:
        raise ZiweiEngineError("紫微排盘计算失败")
    try:
        result = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ZiweiEngineError("紫微排盘结果异常") from exc
    if not isinstance(result, dict) or not isinstance(result.get("astrolabe"), dict):
        raise ZiweiEngineError("紫微排盘结果不完整")
    result["ruleCode"] = request.rule_code
    return result
