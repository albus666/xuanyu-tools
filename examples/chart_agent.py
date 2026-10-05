"""用 Coding Agent 的同一个循环跑排盘工具。pytest 不执行这个文件。

在 projects/agent-runtime/.env 准备好三个 LLM 变量后：

    python examples/chart_agent.py
    python examples/chart_agent.py 1990-01-01 08:30 男，只要四柱和喜用神
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT.parent / "agent-runtime"
sys.path.insert(0, str(AGENT_ROOT / "src"))
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(AGENT_ROOT / ".env")
load_dotenv(ROOT / ".env")

from agent_runtime.agent import DefaultAgent
from agent_runtime.environment import LocalEnvironment
from agent_runtime.llm import OpenAICompatModel

from xuanyu_tools.agent_tools import SYSTEM_PROMPT, domain_tools
from xuanyu_tools.call_log import format_tool_log

PROMPT = "公历 2005-05-09 10:47 出生，男性。请给出四柱，并说明年柱纳音、日柱空亡和交运时间，以及近十年流年。并且分析一下紫薇命盘"


def main() -> None:
    task = " ".join(sys.argv[1:]).strip() or PROMPT
    agent = DefaultAgent(
        OpenAICompatModel.from_env(),
        LocalEnvironment(ROOT),
        tools=domain_tools(),
        system_prompt=SYSTEM_PROMPT,
        max_steps=6,
        event_log=ROOT / "logs" / ("chart-demo.events.jsonl" if task == PROMPT else "last-chart.events.jsonl"),
    )
    result = agent.run(task)
    lines = ["示例中的出生信息为虚构数据，只用于演示，不对应真实的人。", ""]
    pending = []
    for message in result.messages:
        calls = message.get("tool_calls") or []
        if message.get("role") == "assistant" and calls:
            pending.extend(calls)
        elif message.get("role") == "tool" and pending:
            call = pending.pop(0)
            lines.append(format_tool_log(
                message.get("name") or call.get("name") or "tool",
                call.get("arguments") or {},
                message.get("content") or "",
            ))
            lines.append("")
    lines.append(f"[final] {result.final_text}")
    lines.append(f"[status] {result.status} steps={result.steps}")
    text = "\n".join(lines)
    print(text)
    trace = ROOT / "examples" / "traces" / ("chart_demo.txt" if task == PROMPT else "last_chart.txt")
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text(text + "\n", encoding="utf-8")
    print(f"[trace] {trace}")


if __name__ == "__main__":
    main()
