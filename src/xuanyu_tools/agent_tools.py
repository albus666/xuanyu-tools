"""把排盘函数收成 Agent Runtime 能登记的工具。返回值是 JSON 字符串。"""
import json

from agent_runtime.tools.registry import ToolSpec

from .bazi import calculate_bazi
from .registry import tool_schemas
from .ziwei import calculate_ziwei

_HANDLERS = {
    "calculate_bazi": calculate_bazi,
    "calculate_ziwei": calculate_ziwei,
}

SYSTEM_PROMPT = """请只通过已注册工具排盘，不要自己推算干支或星曜。
八字只调用一次 calculate_bazi。它会返回完整命盘。
最终回答只写用户问到的字段，不要复述未问到的纳音、空亡、十神、大运、流年或交运。
问紫微、命宫或十二宫时，调用 calculate_ziwei。
回答只能引用工具返回的 data 和 evidence。任务完成后直接给出最终说明。"""


def domain_tools() -> dict[str, ToolSpec]:
    """
    :return: 以工具名为键的登记表，可传给 DefaultAgent 的 tools
    """
    specs = []
    for item in tool_schemas():
        function = item["function"]
        name = function["name"]
        specs.append(ToolSpec(
            name=name,
            description=function["description"],
            parameters=function["parameters"],
            handler=_json_handler(_HANDLERS[name]),
            permission="allow",
            read_only=True,
        ))
    return {spec.name: spec for spec in specs}


def _json_handler(function):
    """
    :param function: 返回字典的排盘函数
    :return: 把同一结果写成 JSON 字符串的处理函数
    """
    def handler(arguments: dict) -> str:
        return json.dumps(function(arguments), ensure_ascii=False)
    return handler
