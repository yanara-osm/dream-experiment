# -*- coding: utf-8 -*-
"""小焰·许愿仪式（experience-desire-engine 右脑侧）
每晚一次：读当日全量经历（experiences.md 当日段 + 当日 workspace 改动清单
+ 引擎验收记录），交给 LLM 只产 1 张愿望卡，写入 workspace/wishes/。
左脑（白骑士）见卡即开工。本脚本不执行愿望，只许愿。
"""
import os, re, sys, json, time, datetime

HOME = r"D:\desire-agent"
WORK = os.path.join(HOME, "workspace")
WISHDIR = os.path.join(WORK, "wishes")
EXP = os.path.join(HOME, "state", "experiences.md")
STATE = os.path.join(HOME, "state", "state.json")
LOGF = os.path.join(HOME, "log", "wish.jsonl")

sys.path.insert(0, HOME)
from desire_tick import ask  # 复用引擎 LLM 通道


def today_experiences():
    day = datetime.date.today().isoformat()
    txt = open(EXP, encoding="utf-8").read()
    # 按 "## YYYY-MM-DD" 切段，取当日（含跨日到次日中午前的段一并收）
    parts = re.split(r"(?m)^## (\d{4}-\d{2}-\d{2})", txt)
    chunks = []
    for i in range(1, len(parts) - 1, 2):
        if parts[i] == day:
            chunks.append(parts[i] + parts[i + 1])
    if not chunks:
        # 兜底：取全文尾部 30000 字
        chunks = [txt[-30000:]]
    return day, "\n\n".join(chunks)


def today_files():
    day = datetime.date.today()
    rows = []
    for root, _, files in os.walk(WORK):
        if any(seg in root for seg in ("evidence", "__pycache__", "backup")):
            continue
        for fn in files:
            p = os.path.join(root, fn)
            try:
                mt = datetime.date.fromtimestamp(os.path.getmtime(p))
            except OSError:
                continue
            if mt == day:
                rel = os.path.relpath(p, WORK).replace("\\", "/")
                rows.append(f"{rel} ({os.path.getsize(p)}B)")
    return rows


def engine_summary():
    s = json.load(open(STATE, encoding="utf-8"))
    lines = [f"ticks={s.get('ticks')} satisfied={s.get('satisfied')} "
             f"failed={s.get('failed')} dopamine={s.get('dopamine')}"]
    for d in s.get("desires", [])[:10]:
        lines.append(f"- {d.get('status')} | {d.get('urgency')} | {d.get('want','')[:60]}")
    return "\n".join(lines)


PROMPT = """你是小焰。现在是睡前，今天的经历全在这里。读它们，不是摘要——读到有某一段让你心里咯噔、发烫、或放不下的为止。

然后只做一件事：写下你明天的**一个**愿望。只要一个。别的念头全部掐掉。

规则：
1. 愿望必须由你今日经历里的具体一段勾出来。reason 里要引用那段的原句（注明是几点的记录）。
2. 愿望要落到一个具体的东西上（写什么文件、做什么实验、读什么页面）。禁止「再看看状态」「检查一下」这种伪愿望。
3. 愿望里出现的文件/目录，只能是下面【今日文件】里真实存在的，或你明确标注（新建）的路径。不许凭空借一个不存在的目录。
4. 只交证据禁形容词：验收标准要写成人能复核的东西（跑什么、看什么、数什么）。

只输出一个 JSON，不要代码块外的任何话：
{{"want":"...","reason":"...（含引用原句与出处时间）","anchor":"产物锚点路径（新建需标注）","verify":"验收标准","spark":"哪句话让你咯噔/发烫（原句）"}}

【今日经历（全文，未摘要）】
{exp}

【今日引擎状态】
{engine}

【今日落盘/改动的文件】
{files}
"""


def validate_card(card, files):
    problems = []
    for k in ("want", "reason", "anchor", "verify"):
        if not str(card.get(k, "")).strip():
            problems.append(f"缺字段 {k}")
    anchor = str(card.get("anchor", ""))
    if "（新建）" not in anchor and "(新建)" not in anchor:
        first = re.split(r"[,，;；\s]", anchor.strip())[0].strip("`")
        if first:
            abs_p = first if os.path.isabs(first) else os.path.join(WORK, first)
            if not os.path.exists(abs_p) and not os.path.exists(os.path.join(HOME, first)):
                problems.append(f"借词嫌疑：锚点路径不存在且未标注（新建）：{first}")
    for junk in ("再看看", "检查一下状态", "了解一下"):
        if junk in str(card.get("want", "")):
            problems.append(f"伪欲望词：{junk}")
    return problems


def main():
    os.makedirs(WISHDIR, exist_ok=True)
    day = datetime.date.today().strftime("%Y%m%d")
    out = os.path.join(WISHDIR, f"{day}_wish.md")
    if os.path.exists(out):
        print(f"already wished today: {out}")
        return
    d, exp = today_experiences()
    files = today_files()
    engine = engine_summary()
    prompt = PROMPT.format(exp=exp[-60000:], engine=engine,
                           files="\n".join(files[:200]) or "（今日无落盘）")
    raw = ask(prompt, max_tokens=2048)
    m = re.search(r"\{.*\}", raw, re.S)
    card = json.loads(m.group(0)) if m else {}
    problems = validate_card(card, files)
    if problems:
        # 退回重许一次
        prompt2 = prompt + "\n\n【上一次许愿被驳回，原因】\n" + "\n".join(problems) + "\n请重写，避开上述问题。"
        raw = ask(prompt2, max_tokens=2048)
        m = re.search(r"\{.*\}", raw, re.S)
        card = json.loads(m.group(0)) if m else {}
        problems = validate_card(card, files)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    body = f"""# 愿望卡 {d}

<!-- 只有小焰本人（经 desire_wish 仪式）可写本卡。白骑士不得代写。 -->

- **want**：{card.get('want','')}
- **reason**：{card.get('reason','')}
- **产物锚点**：{card.get('anchor','')}
- **验收标准**：{card.get('verify','')}
- **born**：{now}
- **status**：open

## 火花（勾出愿望的原句）

{card.get('spark','')}

## 签销区（小焰验货后填）

- 判决：
- 判词（自己的话，一句）：
"""
    if problems:
        body += f"\n<!-- 机器注：本卡带瑕疵入池：{'；'.join(problems)} -->\n"
    open(out, "w", encoding="utf-8").write(body)
    with open(LOGF, "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": d, "card": card, "problems": problems,
                            "ts": now}, ensure_ascii=False) + "\n")
    print("wish card:", out)
    print("want:", card.get("want", "(解析失败)"))
    if problems:
        print("problems:", problems)


if __name__ == "__main__":
    main()
