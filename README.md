# 玄遇规则工具

把玄遇里已经写好的八字和紫微计算收成两个工具。这是 Coding Agent Runtime 旁边的副项目，不替代主项目。

八字和紫微的算法已经复制到 `src/xuanyu_tools/rules`。运行时不再读取 `projects/xuanyu`。紫微副本在调用 Node 时使用 UTF-8，避免中文 Windows 按系统编码解码失败。`lunar_python` 和 iztro 仍是外部依赖，不是玄遇自己的源码。

## 工具

| 工具 | 作用 |
| --- | --- |
| `calculate_bazi` | 一次返回四柱、五行、喜用神、纳音、空亡、十神、大运、流年和交运 |
| `calculate_ziwei` | 十二宫、主星、命身和五行局 |

模型只负责选择工具和转述 `data` 与 `evidence`。干支和星曜不由模型自己推算。八字只调用一次 `calculate_bazi`。最终回答只写用户问到的字段，不复述整份命盘。问紫微时再调用 `calculate_ziwei`。

接到 `projects/agent-runtime` 的 `DefaultAgent` 时，传入 `domain_tools()`，不要改 Coding Agent 的默认工具表。真实模型示例读取 `projects/agent-runtime/.env`：

```powershell
python examples/chart_agent.py
python examples/chart_agent.py 1990-01-01 08:30 男，只要四柱和喜用神
```

地点可以传入，但当前引擎不用它排盘，结果里会有警告。`use_true_solar: true` 直接返回失败，避免把钟表时间说成真太阳时。

## 测试

在本目录运行。八字需要 `lunar_python`，紫微需要本机 `node`。

```powershell
cd projects/xuanyu-tools
python -m pytest -q
```

## 边界

这是结构化规则工具，不是命理产品，也不是生产接口。没有账户、多 Agent、记忆和向量库。
