"""排盘工具的 schema。模型只能通过这些参数调用，不能改算法。"""
from .bazi import calculate_bazi
from .ziwei import calculate_ziwei


def tool_schemas() -> list[dict]:
    """
    :return: OpenAI 兼容的 tools 列表
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "calculate_bazi",
                "description": "一次计算完整八字，含四柱、五行、喜用神、纳音、空亡、十神、大运、流年和交运。不要自行推算。最终回答只转述用户问到的字段。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birth_date": {"type": "string", "description": "公历日期，YYYY-MM-DD"},
                        "birth_time": {"type": "string", "description": "钟表时间，HH:MM。省略时按 12:00"},
                        "gender": {"type": "string", "enum": ["男", "女"]},
                        "for_year": {"type": "integer", "description": "要查看的公历年，用来选取所在大运和该步流年"},
                        "place": {"type": "string"},
                        "use_true_solar": {"type": "boolean"},
                    },
                    "required": ["birth_date", "gender"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_ziwei",
                "description": "用确定性规则计算紫微十二宫和主星。不要自行安星。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birth_date": {"type": "string", "description": "公历日期，YYYY-MM-DD"},
                        "birth_time": {"type": "string", "description": "钟表时间，HH:MM"},
                        "birth_time_index": {"type": "integer", "description": "0 到 12，与玄遇时辰序号一致"},
                        "gender": {"type": "string", "enum": ["男", "女"]},
                        "target_date": {"type": "string", "description": "运限公历日期，YYYY-MM-DD"},
                        "place": {"type": "string"},
                        "use_true_solar": {"type": "boolean"},
                    },
                    "required": ["birth_date", "gender"],
                    "additionalProperties": False,
                },
            },
        },
    ]


HANDLERS = {
    "calculate_bazi": calculate_bazi,
    "calculate_ziwei": calculate_ziwei,
}
