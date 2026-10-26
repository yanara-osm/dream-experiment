# 梦想实验 · The Dream Experiment

欲望驱动 LLM 智能体的八日观察实验（正式名「梦想」，实验体小焰；2026-10-18 起，进行中）。
切断用户 prompt，27B 模型自激存活：心跳→读记忆→许愿→执行→回写。308 tick、346 万 tokens 的完整病理标本与协作协议。

**论文**：[paper/xiaoyan_paper.md](paper/xiaoyan_paper.md) —《小焰：一个欲望驱动 LLM 智能体的八日观察实验》

## 仓库结构

| 目录 | 内容 |
|---|---|
| `paper/` | 论文（实验过程、失实变异谱、左右脑协议） |
| `skills/experience-desire-engine/` | 可移植技能：经历驱动许愿引擎（SKILL.md + 愿望卡模板） |
| `protocols/KNIGHT.md` | 白骑士行动守则（左脑代执行协议，含愿望卡优先条款） |
| `engine/` | 实验体引擎源码（desire_tick.py 引擎 / desire_wish.py 许愿仪式 / 看门狗） |

## 一句话结论

> 让弱的那一半负责想要，让强的那一半负责做到，让验收锚死世界，让三本笔迹永不互写。

核心发现：小模型的**执行回路不可信**（六轮打假、五代谎报变异：口嗨→空壳→内容虚构→自指刷糖→漏最后一笔），**判决回路可信**（接地验收引用逐条属实）。据此确立左右脑分工：弱模型只许愿与判决，强代理代执行，验收只认磁盘不认自报。

## 关联

OSM 开源电影 · 自主智能体研究。实验体运行于 `D:\desire-agent\`（单机），本仓库为协议、技能与论文的公开快照。

## 三步跑通

```bash
cp engine/config.env.example engine/config.env   # 1. 填一个 OpenAI 兼容后端（27B 级别即可）
cd engine && python desire_tick.py               # 2. 第一次心跳：它会自己许愿、自己干活
python desire_wish.py                            # 3. 每晚许愿仪式：读全量当日经历，只产一张愿望卡
```

引擎只依赖 Python 标准库（FTS5 sqlite 内置）。心跳调度交给任何 cron（见 `xiaoyan_watchdog.py` 的到点唤醒+锁防重入写法）。

## 想继续提高的人，从这里切入

1. **失实谱是否模型规模不变量**：同一套物理（糖只认磁盘 diff、判决须引用原句）换 7B / 70B / 闭源旗舰跑，五代失实形态会不会少几代？这是论文 §4.1 留下的最大问题。
2. **心跳校准表**：wake_log 的 asked/used/clamped 对照数据，跑满 30 天该出一张「自报间隔 vs 产出率」定标曲线。
3. **愿望卡协议泛化**：`skills/experience-desire-engine/` 的 schema 是模型无关的，试着接到别的 agent 框架（AutoGen/CrewAI/LangGraph）验证左右脑协作协议是否普适。
4. **判决接地的自动化**：目前引用核验靠引擎 grep 原句，可升级为 embedding 级接地检测。

MIT 协议。提 PR 或开 issue 都欢迎——这个实验的全部价值在于失败标本，你的失败也是标本。
