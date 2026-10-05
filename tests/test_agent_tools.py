import sys
from pathlib import Path

AGENT_SRC = Path(__file__).resolve().parents[1].parent / "agent-runtime" / "src"
sys.path.insert(0, str(AGENT_SRC))

from agent_runtime.agent import DefaultAgent
from agent_runtime.environment import LocalEnvironment

from xuanyu_tools.agent_tools import domain_tools


class ScriptedModel:
    def __init__(self, replies):
        self._replies = list(replies)

    def query(self, messages, tools=None):
        reply = self._replies.pop(0)
        if isinstance(reply, dict):
            return reply
        return {"role": "assistant", "content": reply}


def _call(name, arguments, call_id="c1"):
    return {
        "role": "assistant",
        "content": "排盘",
        "tool_calls": [{"id": call_id, "name": name, "arguments": arguments}],
    }


def test_agent_reply_can_omit_fields_present_in_chart(tmp_path):
    model = ScriptedModel([
        _call("calculate_bazi", {
            "birth_date": "2000-08-16",
            "birth_time": "14:30",
            "gender": "女",
        }),
        "年柱庚辰，日主丙。",
    ])
    result = DefaultAgent(
        model,
        LocalEnvironment(tmp_path),
        tools=domain_tools(),
        max_steps=4,
    ).run("只要四柱和日主")
    names = [message["name"] for message in result.messages if message.get("role") == "tool"]
    blob = "\n".join(message["content"] for message in result.messages)
    assert names == ["calculate_bazi"]
    assert "白蜡金" in blob
    assert result.final_text == "年柱庚辰，日主丙。"
    assert "白蜡金" not in result.final_text


def test_agent_can_quote_nayin_from_the_same_chart(tmp_path):
    model = ScriptedModel([
        _call("calculate_bazi", {
            "birth_date": "2000-08-16",
            "birth_time": "14:30",
            "gender": "女",
            "for_year": 2005,
        }),
        "年柱纳音是白蜡金。",
    ])
    result = DefaultAgent(
        model,
        LocalEnvironment(tmp_path),
        tools=domain_tools(),
        max_steps=4,
    ).run("请给出纳音和交运")
    blob = "\n".join(message["content"] for message in result.messages)
    assert "白蜡金" in blob
    assert "2003-08-16 14:30:00" in blob
    assert result.final_text == "年柱纳音是白蜡金。"
