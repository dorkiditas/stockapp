# -*- coding: utf-8 -*-
"""
持仓日报 —— 每天一份,只讲她的仓位,不讲行情八卦。

建于 2026-08-15,起因:她说「每天都要出个我持仓股的日报」。
本仓库原本已有 wechat_push.build_digest(),但它的『最该动的』整段是**写死的**,
写死在大约 7 月的判断上,到今天已经三条错、一条违规:
  · 「🟢 建 MU 仓」        → **违反她 7/30 自订的 BUY_SIDE_LOCKED**(杠杆≥1.5x 不许出买方建议)
  · 「🔴 平掉 BE 空单」    → BE 空头已于 7/28 平掉,仓位不存在
  · 「🟡 CRDO 减一部分」   → CRDO 已于 8/3 清仓
  · 「🔴 砍 QCOM」        → 8/7 CPU_RENAISSANCE 段已写死【不许再对 QCOM 出减仓 call】
一份每天自动发出去、内容却停在一个月前的日报,比不发更危险。
所以本模块的第一条设计原则是:**日报里不许有任何写死的判断,每一句都必须能追到
calls.py / heavy.py / scorecard.py 里某个当天重算出来的数。**

第二条原则:**出厂带闸门。**render() 最后会跑 _gate() ——
BUY_SIDE_LOCKED 为真时,正文里出现买方措辞就直接抛异常,宁可今天不发,也不发违规的。

数据源优先级:
  实时行情(tencent)> account_risk.json / holdings.csv(本地实盘,不进仓库)> heavy.py 快照
取不到实时价时不假装,顶部直接打【数据陈旧】横幅并写明快照日期。
"""
import os
import datetime as dt

import calls
import heavy

BASE = os.path.dirname(os.path.abspath(__file__))

# ── 有日期的催化(只登记【已确认日期】的;猜的日期不许进) ──────────────────
# 每条必须写出处,过期的由 upcoming() 自动滤掉,不用手工清。
CATALYSTS = [
    ("2026-08-17", "DeepSeek API 全面涨价生效(北京时间零时)", "AVGO/token 经济",
     "多家中国媒体一致;见 AVGO 档案 8/15 补(1)"),
    ("2026-08-20", "SPCX 第二批解禁约 3.19 亿股(约受限股 7%)", "SPCX",
     "CNBC/解禁时间表;第一批 8/6 已被市场完整吸收"),
    ("2026-09-02", "AVGO FQ3 财报(盘后)", "AVGO",
     "AVGO 档案已写死必问清单五条"),
    ("2026-09-15", "FOMC(9/15-16)", "全书(长久期)",
     "档案已把 9 月中旬标为全年最需要低杠杆的窗口"),
    ("2026-11-01", "CBRS Q3 财报(11 月,日期待公司确认)", "CBRS",
     "CBRS 档案三条证伪线在这一份一次揭晓"),
    ("2026-11-01", "SIEGY FY26 Q4(11 月,日期待确认)", "SIEGY",
     "SIEGY 复议的一级源验证点"),
    ("2026-12-08", "SPCX 180 天全解禁(约 40% 总股本可流通)", "SPCX",
     "GS 供给日历"),
]

BUY_WORDS = ("建仓", "加仓", "买入", "部署", "首笔", "分批建", "建 ", "可买", "抄底")


def upcoming(days=21, today=None):
    """未来 N 天内、且已确认日期的催化。过期的自动消失。"""
    t = today or dt.date.today()
    out = []
    for d, what, who, src in CATALYSTS:
        dd = dt.date.fromisoformat(d)
        gap = (dd - t).days
        if 0 <= gap <= days:
            out.append((d, gap, what, who, src))
    return sorted(out, key=lambda x: x[0])


_MARKS = "🟢🟡🔴🟠⚪⬜✅"


def _rating_of(code):
    """从档案 element0 里取出评级短语。
    注意:有些条目(SPCX/600522)的 element0 是以『★★★…』或日期开头的,
    直接截前 18 字会得到一串星号 —— 所以先定位第一个评级 emoji,没有才退回截断。"""
    txt = calls.MY_CALLS.get(code, ("—", ""))[0]
    i = next((j for j, ch in enumerate(txt) if ch in _MARKS), -1)
    seg = txt[i:] if i >= 0 else txt
    seg = seg.split("【")[0].split("\n")[0]
    for sep in ("·★", "★"):
        seg = seg.split(sep)[0]
    return seg.strip(" ·")[:20] or "—"


def _quotes(codes):
    """尝试拉实时价。拿不到就返回 {} —— 由调用方打陈旧横幅,不许假装。"""
    try:
        import tencent
        q = tencent.quote(list(codes))
        out = {}
        for _, r in q.iterrows():
            sym = str(r.get("code") or "")
            for c in codes:
                if tencent.to_symbol(c) == sym and r.get("price"):
                    out[c] = (float(r["price"]),
                              float(r["prev_close"]) if r.get("prev_close") else None)
        return out
    except Exception:
        return {}


def render(today=None, live=True):
    """返回 (title, markdown)。"""
    t = today or dt.date.today()
    acct, asrc = heavy.load_account()
    pos = heavy.positions()
    live_px = _quotes([p["代码"] for p in pos]) if live else {}
    stale = not live_px

    s, c = heavy.stress(), heavy.concentration()
    L = [f"# 持仓日报 · {t.isoformat()}", ""]
    if stale:
        L += [f"> ⚠️ **数据陈旧**:没取到实时行情,以下为 **{heavy.ASOF}** 的 IB 快照"
              f"(来源:{asrc})。**今日涨跌一栏为空,不是 0。**", ""]

    # ① 账户
    L += ["## ① 账户", "",
          f"- 净值 **${acct['net_liquidation']:,.0f}** · gross ${acct['gross_position_value']:,.0f}",
          f"- 杠杆 **{s['杠杆']:.2f}x** · 缓冲 **${s['缓冲']:,.0f}**(净值的 {s['缓冲/净值%']:.1f}%)",
          f"- 全书同步跌 **{s['同步跌归零%_保守']:.2f}%** 缓冲归零"
          f"(保守口径;计入维持保证金同步释放为 {s['同步跌归零%_计入保证金释放']:.2f}%)",
          f"- 集中度:第一大仓 **{c['第一大仓'][0]} {c['第一大仓'][2]:.1f}%** · "
          f"top3 {c['top3']:.1f}% · 太空因子 {c['太空因子']:.1f}%",
          ""]
    gate = "🔒 **买方权限锁死**" if calls.BUY_SIDE_LOCKED else "🔓 买方权限已解锁"
    L += [f"- {gate} —— 解锁线:{calls.BUY_SIDE_UNLOCK}。"
          f"**本日报不会、也不许出现任何建仓/加仓建议。**", ""]

    # ② 逐仓
    L += ["## ② 逐仓", "",
          "| 标的 | 股数 | 现价 | 今日 | 浮动 | 浮动% | 占净值 | 在案评级 |",
          "|---|---|---|---|---|---|---|---|"]
    for p in pos:
        code = p["代码"]
        px, prev = live_px.get(code, (p["现价"], None))
        chg = f"{(px/prev-1)*100:+.2f}%" if prev else "—"
        rating = _rating_of(code)
        star = "★" if p["重仓"] else ""
        L.append(f"| {star}**{code}** | {p['股数']:,} | {px:,.2f} | {chg} | "
                 f"{p['浮动盈亏']:+,.0f} | {p['浮动%']:+.1f}% | {p['%净值']:.1f}% | {rating} |")
    L += ["", f"★ = 单票 ≥ 净值 {heavy.HEAVY_THRESHOLD:.0%}。全书浮动盈亏合计 "
              f"**${c['浮动盈亏合计']:,.0f}**。", ""]

    # ③ 在案未执行 —— 唯一会随时间恶化的一栏
    rows, tot, tot_price = heavy.execution_gap(
        {k: v[0] for k, v in live_px.items()} or None)
    L += ["## ③ 今天该动的(在案未执行)", ""]
    if rows:
        L += ["| 标的 | 动作 | 下达 | 挂了几天 | 下达价 | 现价 | 不执行盈亏 | 类型 |",
              "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            age = (t - dt.date.fromisoformat(r["下达日"])).days
            flag = " ⚠️" if age >= 5 else ""
            L.append(f"| **{r['代码']}** | {r['在案动作']} | {r['下达日']} | {age} 天{flag} | "
                     f"{r['下达价']:.2f} | {r['现价']:.2f} | {r['未执行盈亏']:+,.0f} | {r['类型']} |")
        L += ["", f"合计 **{tot:+,.0f}**(价格判断类 {tot_price:+,.0f};风险预算类不按择时记分)。",
              "⚠️ = 已挂满 5 个日历日,按 `EXECUTION_RATE_RULE` 必须重新论证或撤回。", ""]
    else:
        L += ["- 在案卖出 call 已全部了结。", ""]

    # ④ 有日期的催化
    up = upcoming(today=t)
    L += ["## ④ 未来三周有日期的事", ""]
    L += ([f"- **{d}**(T+{g})· {what} — 关联 {who}" for d, g, what, who, _ in up]
          or ["- 未来三周没有已确认日期的催化。"])
    L.append("")

    # ⑤ 记分牌(我自己的成绩,天天挂着)
    try:
        import scorecard
        _, summ, _ = scorecard.score()
        p = summ.get("price类(计入战绩)", {})
        if p.get("n"):
            L += ["## ⑤ 我的记分牌", "",
                  f"- price 类 n={p['n']} · 命中率 **{p['命中率']:.0f}%** · "
                  f"平均 {p['平均收益']:+.2f}% · 美元合计 **{p['美元合计']:+,.0f}**",
                  "- 完整表在 App「🧾 Max记分牌」页。**这一行天天挂着,是给你用来给我打折的。**", ""]
    except Exception as e:
        L += ["## ⑤ 我的记分牌", "", f"- ⚠️ 记分牌今天跑不起来({type(e).__name__}),视同没有成绩。", ""]

    # ⑥ 风险雷达
    try:
        import risk_radar
        rs = risk_radar.all_risks()
        if rs:
            L += ["## ⑥ 风险雷达", ""] + [f"- {x}" for x in rs] + [""]
    except Exception:
        pass

    L += ["---", "> 本日报由 daily_brief.py 每天重算,**没有任何写死的判断**;"
          "每一句都能追到 calls.py / heavy.py / scorecard.py。我的判断不是保证,记分牌在第⑤节。"]

    md = "\n".join(L)
    _gate(md)
    title = (f"持仓日报 {t.strftime('%m-%d')} · 杠杆{s['杠杆']:.2f} 缓冲${s['缓冲']:,.0f}"
             + (f" · {len(rows)}条待执行" if rows else ""))
    return title, md


def _gate(md):
    """出厂闸门:锁着买方权限时,正文不许出现买方措辞。
    宁可今天不发,也不发一份违反她自己订的条款的日报。"""
    if not calls.BUY_SIDE_LOCKED:
        return
    body = md.split("## ①", 1)[-1]
    # 只查"动作句",放过声明本身(声明里必然出现这些词)
    body = body.replace("不会、也不许出现任何建仓/加仓建议", "")
    hits = [w for w in BUY_WORDS if w in body]
    if hits:
        raise AssertionError(
            f"日报闸门:BUY_SIDE_LOCKED=True,但正文出现买方措辞 {hits}。"
            f"这正是 wechat_push.py 旧版写死『建 MU 仓』犯的错,不许再犯。")


def save(md, today=None):
    """存一份到 reports/,每天一个文件,同日覆盖。返回路径。"""
    t = today or dt.date.today()
    d = os.path.join(BASE, "reports")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"{t.isoformat()}_持仓日报.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(md)
    return p


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    title, md = render(live="--offline" not in sys.argv)
    if "--save" in sys.argv:
        print("已存:", save(md))
    if "--push" in sys.argv:
        import wechat_push
        wechat_push.send(title, md)
    else:
        print(title)
        print()
        print(md)
