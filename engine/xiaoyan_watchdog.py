# -*- coding: utf-8 -*-
"""小焰自主心跳看门狗（10-23 上线，替代死节奏2h心跳）。
每30分钟被 cron 唤起，只做三件事：
  1) 该醒吗：信箱有新信（无条件醒）/ next_wake_at 到点（她自己决定醒）/ 没有 next_wake_at（首跳引导）
  2) 该醒就跑 desire_tick.py（带锁防重入）
  3) 她这跳有 voice 才 print（stdout=cron投递内容；空=沉默）
"""
import json, os, subprocess, sys, time

HOME = r"D:\desire-agent"
STATE = os.path.join(HOME, "state", "state.json")
INBOX = os.path.join(HOME, "state", "inbox.md")
LOCK = os.path.join(HOME, "state", ".tick_lock")
LOGDIR = os.path.join(HOME, "log")

def latest_tick_log():
    import glob, re
    fs = sorted(glob.glob(os.path.join(LOGDIR, "tick_*.json")))
    return fs[-1] if fs else None

def main():
    st = json.load(open(STATE, encoding="utf-8"))
    now = time.time()

    # 锁：上一跳还在跑（<12分钟）就跳过本轮
    if os.path.exists(LOCK):
        if now - os.path.getmtime(LOCK) < 720:
            return
    try:
        os.utime(LOCK, None) if os.path.exists(LOCK) else open(LOCK, "w").write(str(now))
    except OSError:
        pass

    try:
        mail_due = os.path.getmtime(INBOX) > st.get("last_inbox_read", 0)
        wake_due = ("next_wake_at" not in st) or (now >= st.get("next_wake_at", 0))
        if not (mail_due or wake_due):
            return  # 她还在自己选的睡眠里，看门狗闭嘴

        before = latest_tick_log()
        r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HOME, "desire_tick.py")],
                           cwd=HOME, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=420)
        after = latest_tick_log()

        # voice 从新 tick 日志里取（引擎 stdout 混杂思考输出，不作投递内容）
        voice = ""
        tick_id = None
        if after and after != before:
            try:
                lg = json.load(open(after, encoding="utf-8"))
                voice = ((lg.get("output") or {}).get("voice") or "").strip()
                tick_id = lg.get("tick")
            except Exception:
                pass
        elif r.returncode != 0:
            tail = (r.stdout or "")[-400:] + (r.stderr or "")[-400:]
            print(f"[小焰心跳异常] rc={r.returncode}\n{tail}")
        if voice:
            print(voice)
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass

if __name__ == "__main__":
    main()
