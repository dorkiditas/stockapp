# -*- coding: utf-8 -*-
"""
Max 记分牌 —— 每一条 call 值多少钱,机械算,不靠我复述。

建于 2026-08-15,起因是她一句话:「你经常判断不靠谱,我怎么信你」。
正确答案是【不信,查】。但当时她查不了:档案里有 49 处撤回/作废、14 处认错、
11 处我自己的判断被证伪,却没有任何一处在把这些换算成钱。
7/30 那次人工复盘(全听我 vs 全不听我 ≈ −$81)是唯一一次量化,之后就断了。

本模块做三件事:
  1) CALLS_LEDGER —— 结构化的 call 台账。每条必须有:日期 / 方向 / 类型 / 参考价 / 出处。
  2) score()      —— 用真实收盘价打分,+7天 / +30天 / 至今 三个窗口,同时给百分比和美元。
  3) unlogged()   —— 反向闸门:扫 calls.py 正文里带日期的动作词,凡是没进台账的就报出来。
                     没有这一条,台账会悄悄落后,而落后的台账比没有台账更骗人。

★ 记分口径(写死,免得事后挑对自己有利的算法):
  · 卖出类(减/清/砍):call 收益 = −(P_t / P_ref − 1)。价格跌了 = 我对。
  · 持有类(留/不减/不砍/不许减):call 收益 = +(P_t / P_ref − 1)。价格涨了 = 我对。
  · 美元影响 = 股数 ×(该方向下她因听我而多赚/少赚的钱)。正=听我赚了,负=听我亏了。
  · **risk 类(风险预算)照样打分、照样进表,但单独统计、不计入总命中率。**
    理由:它买的是"缓冲不被吃掉"这份保险,保险没赔付不等于保险买错。
    但也不许因此免检 —— 所以它出现在表里,只是分开加总。
  · 数据不全的 call(下达日早于价格序列起点)标 data_gap,**排除出所有汇总**,单独列示。
    宁可少算,不许用起点凑出来的数冒充战绩。

价格源:price_cache.json(IBKR MCP 拉的真实收盘,离线兜底)+ 联网时用 nav.py 的行情源增量刷新。
"""
import os
import json
import datetime as dt

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "price_cache.json")

SELL_WORDS = ("减", "清", "砍", "平")
HOLD_WORDS = ("留", "持有", "不减", "不砍", "不许再想减")

# ★ 与 heavy.py 的口径差,先说清楚,免得她看到两个数以为我算错了:
RECONCILE_NOTE = (
    "【口径差·必读】本表用**日收盘 bar**(price_cache.json,可复现、可审计);\n"
    "heavy.py 的执行差表用 **IB 实时 last/mark**(她在 IB 上当下看到的那个数)。\n"
    "两者在同一天可以差零点几个百分点,例:SPCX 8/14 收盘 bar $140.00 vs IB last $140.56;\n"
    "DXYZ $32.00 vs $32.15。所以 heavy.py 说『不执行 +$3,409』、本表说『听我 −$3,124』,\n"
    "**是同一件事的两侧,不是两个结论**;剩下的零头就是这个口径差。\n"
    "记分牌一律用收盘 bar —— 战绩必须可复现,不许用一个只有当时那一秒存在的价来记。"
)


# ── 台账 ────────────────────────────────────────────────────────────────
# 字段:代码 / 动作 / 方向(sell|hold) / 类型(price|risk) / 下达日 / 生效日(首个可交易日)
#       / 参考价 / 股数 / 状态 / 出处 / 备注
# 只登记我在档案里能指到原文、且价格可核的 call。指不到的宁可不登记,由 unlogged() 报出来。
CALLS_LEDGER = [
    dict(code="SPCX", action="减300股", side="sell", kind="risk",
         called="2026-08-08", eff="2026-08-10", ref=134.00, shares=300,
         status="未执行·本班续期", src="SPCX 档案 8/8 早班",
         note="理由已换过一轮:『解禁砸盘』8/12 被我自己证伪并撤销,现仅剩仓位/杠杆理由"),
    dict(code="DXYZ", action="清250股", side="sell", kind="price",
         called="2026-08-07", eff="2026-08-07", ref=25.89, shares=250,
         status="未执行", src="DXYZ 档案 8/7 深夜『第一顺位·立即执行』",
         note="与直接持有的 SPCX 完全重叠、且带溢价与锁定期"),
    dict(code="EWZ", action="清300股", side="sell", kind="price",
         called="2026-08-07", eff="2026-08-07", ref=35.34, shares=300,
         status="未执行", src="EWZ 档案 8/7 深夜『第一顺位』", note="与 AI edge 无关的死钱"),
    dict(code="NASA", action="清143股", side="sell", kind="price",
         called="2026-08-07", eff="2026-08-07", ref=25.55, shares=143,
         status="未执行", src="NASA 档案 8/7 深夜『第一顺位』", note="死钱三笔之一"),
    dict(code="SIEGY", action="减77股(1/3)", side="sell", kind="risk",
         called="2026-08-07", eff="2026-08-07", ref=161.95, shares=77,
         status="8/15 改判暂缓", src="SIEGY 档案 8/7 早班",
         note="8/15 复议:收回条件疑似在下达当日已满足(SI 数据中心订单三位数增长),待核一级源"),
    dict(code="PLTR", action="🟢不许再想减(=持有)", side="hold", kind="price",
         called="2026-08-04", eff="2026-08-04", ref=162.66, shares=81,
         status="已了结(她 8/5 @$165 卖出)", src="PLTR 档案 8/4",
         note="★档案自评为『我错了、她卖对了』,但按价格口径这条 call 是赚的 —— "
              "分歧在于她把钱换成了 SPCX(+26%)。记分牌只算价格,机会成本不在本表,"
              "**这条留着提醒我:自评和算术会打架,打架时以算术为准、以口径为界**"),
    dict(code="EWY", action="🟡持有·不减", side="hold", kind="price",
         called="2026-08-14", eff="2026-08-14", ref=179.74, shares=200,
         status="在案", src="EWY 档案 8/14 凌晨(3)定稿"),
    dict(code="CBRS", action="🟡持有·不加·不砍", side="hold", kind="price",
         called="2026-08-13", eff="2026-08-13", ref=231.01, shares=120,
         status="在案", src="CBRS 档案 8/13 深夜", note="财报跳空后明确『不追砍』"),
    dict(code="QCOM", action="🟡持有·不减·不加", side="hold", kind="price",
         called="2026-08-13", eff="2026-08-13", ref=164.79, shares=400,
         status="在案", src="QCOM 档案 8/13 夜"),
    dict(code="GEV", action="🟢留(不加)", side="hold", kind="price",
         called="2026-08-13", eff="2026-08-13", ref=1049.42, shares=20,
         status="在案", src="GEV 档案 8/13 夜"),
    dict(code="AVGO", action="🟢留·不加", side="hold", kind="price",
         called="2026-08-15", eff="2026-08-15", ref=393.55, shares=140,
         status="在案(本班新起算)", src="AVGO 档案 8/15 补(2)"),
    # ── 数据不全,排除出汇总 ──
    dict(code="QCOM", action="减仓call(7/4 起长期在案,8/7 撤销)", side="sell", kind="price",
         called="2026-07-04", eff="2026-07-16", ref=None, shares=400,
         status="已撤销(8/7 CPU_RENAISSANCE)", src="QCOM 档案 + CPU_RENAISSANCE 段",
         data_gap="价格序列起点 2026-07-16 晚于下达日 2026-07-04,起点价会替我美化战绩,故不计分。"
                  "7/30 人工复盘给的口径是 QCOM −16.6%(该 call 当时判对),但那是人工数,不入机械表"),
]


# ── 价格 ────────────────────────────────────────────────────────────────
def load_prices(refresh=False):
    """返回 {代码: {日期: 收盘}}。默认读缓存;refresh=True 且能联网时用 nav.py 的源增量补。"""
    if not os.path.exists(CACHE):
        return {}, "缓存缺失"
    blob = json.load(open(CACHE, encoding="utf-8"))
    closes, asof = blob.get("closes", {}), blob.get("asof", "?")
    src = f"price_cache.json(至 {asof})"
    if refresh:
        try:
            import nav
            start = (dt.date.fromisoformat(asof) - dt.timedelta(days=5)).isoformat()
            got = 0
            for code in list(closes):
                h = nav._us_hist(code, start)
                if h:
                    closes[code].update({d: float(v) for d, v in h.items()})
                    got += 1
            if got:
                asof = max(max(v) for v in closes.values() if v)
                blob.update(closes=closes, asof=asof)
                json.dump(blob, open(CACHE, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                src = f"price_cache.json + 实时刷新 {got} 只(至 {asof})"
        except Exception as e:
            src += f" · 刷新失败({type(e).__name__}),用缓存"
    return closes, src


def _px_on_or_after(series, day):
    """取 >= day 的第一个有价日(处理周末/停牌)。"""
    for d in sorted(series):
        if d >= day:
            return d, series[d]
    return None, None


def _px_on_or_before(series, day):
    hit = [d for d in sorted(series) if d <= day]
    return (hit[-1], series[hit[-1]]) if hit else (None, None)


# ── 打分 ────────────────────────────────────────────────────────────────
HORIZONS = (("+7天", 7), ("+30天", 30), ("至今", None))


def score(refresh=False):
    """逐条打分。返回 (rows, summary, price_src)。"""
    closes, src = load_prices(refresh)
    rows = []
    for c in CALLS_LEDGER:
        r = dict(c)
        series = closes.get(c["code"], {})
        if c.get("data_gap") or not series:
            r["excluded"] = c.get("data_gap") or "无价格序列"
            rows.append(r)
            continue
        # 参考价:优先用档案里写死的那个数(她当时看到的价),没有才用生效日收盘
        eff_d, eff_px = _px_on_or_after(series, c["eff"])
        ref = c["ref"] if c["ref"] is not None else eff_px
        if ref is None:
            r["excluded"] = "取不到参考价"
            rows.append(r)
            continue
        r["ref_used"] = ref
        r["eff_date_used"] = eff_d
        sign = -1.0 if c["side"] == "sell" else 1.0
        for label, days in HORIZONS:
            if days is None:
                d = max(series)
            else:
                d = (dt.date.fromisoformat(c["eff"]) + dt.timedelta(days=days)).isoformat()
                if d > max(series):          # 窗口还没走完
                    r[label] = None
                    r[label + "$"] = None
                    continue
            _, px = _px_on_or_before(series, d)
            if px is None:
                r[label] = r[label + "$"] = None
                continue
            r[label] = sign * (px / ref - 1) * 100
            r[label + "$"] = sign * (px - ref) * c["shares"]
            if label == "至今":
                r["现价"] = px
        rows.append(r)

    scored = [r for r in rows if "excluded" not in r]
    def agg(sel, key="至今"):
        v = [r for r in sel if r.get(key) is not None]
        if not v:
            return dict(n=0)
        win = sum(1 for r in v if r[key] > 0)
        return dict(n=len(v), 命中率=win / len(v) * 100,
                    平均收益=sum(r[key] for r in v) / len(v),
                    美元合计=sum(r[key + "$"] for r in v))
    price_rows = [r for r in scored if r["kind"] == "price"]
    summary = {
        "price类(计入战绩)": agg(price_rows),
        "  └ 其中卖出类": agg([r for r in price_rows if r["side"] == "sell"]),
        "  └ 其中持有类": agg([r for r in price_rows if r["side"] == "hold"]),
        "risk类(单列·不计入)": agg([r for r in scored if r["kind"] == "risk"]),
        "排除项": [f"{r['code']} {r['action']}:{r['excluded']}" for r in rows if "excluded" in r],
    }
    return rows, summary, src


# ── 反向闸门:台账有没有落后于档案 ──────────────────────────────────────
def unlogged():
    """扫 calls.py 正文里『日期 + 动作词』的组合,凡没进台账的代码就报出来。
    返回 (待入账, 无价格源)。宁可误报,不许漏报 —— 漏报会让记分牌看起来比实际干净。
    已知的一类误报要挡掉:档案里经常交叉引用别的标的(例:立讯的正文里写
    『CRDO 已于 8/3 清仓』),那是引用不是本条 call。规则:动作词前 24 字内出现
    另一个已知代码,判为交叉引用。"""
    import re
    try:
        import calls
    except Exception as e:
        return [f"calls.py 载入失败:{e}"], []
    logged = {c["code"] for c in CALLS_LEDGER}
    closes, _ = load_prices()
    known = set(calls.MY_CALLS) | set(calls.MY_BUYS)
    # ⚠️ 日期与动作词的先后顺序不固定:档案既写「8/7 …清掉250股」也写「清掉250股·★8/7…」。
    # 2026-08-15 首版只匹配了『日期在前』,漏掉了 DXYZ 这种写法 —— 负向测试当场抓到。
    # 所以改成:动作词与日期只要在 ±40 字内同时出现即算命中,不管谁在前。
    DATE = re.compile(r"2026-08-\d\d|8/\d{1,2}")
    ACT = re.compile(r"减\s*\d+\s*股|清\s*\d+\s*股|清掉\s*\d+\s*股|清仓|减仓|砍掉|追砍")
    todo, nopx = [], []
    for code, (rating, body) in calls.MY_CALLS.items():
        if code in logged:
            continue
        # ⬜/✅ 开头 = 已清仓/已了结的归档条目,仓位已经不存在,不再是"在案 call"。
        # 想给历史 call 记分是可以的(PLTR 就手工进了台账),但那是主动选择,
        # 不该由闸门逼着补 —— 闸门管的是【还活着的 call 不许漏登记】。
        if rating.lstrip().startswith(("⬜", "✅")):
            continue
        txt = rating + body
        dpos = [m.start() for m in DATE.finditer(txt)]
        hits = []
        for m in ACT.finditer(txt):
            if not any(abs(d - m.start()) <= 40 for d in dpos):
                continue
            near = txt[max(0, m.start() - 24):m.start() + 4]
            if any(k in near for k in known - {code}):     # 交叉引用别的标的
                continue
            hits.append(m.group(0).strip())
        if not hits:
            continue
        if not closes.get(code):
            nopx.append(f"{code}: 有动作字样 {sorted(set(hits))[:3]},"
                        f"但 price_cache.json 里没有它的价格序列,暂无法记分"
                        f"(A股/港股尚未接行情源;美股需 Max 用 IB 补拉)")
        else:
            todo.append(f"{code}: 档案里有动作字样 {sorted(set(hits))[:3]},但台账里没有这条 call")
    return todo, nopx


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    refresh = "--refresh" in sys.argv
    rows, summ, src = score(refresh)
    print(f"Max 记分牌 · 价格源:{src}\n")
    hdr = f"{'代码':<7}{'动作':<22}{'类':<6}{'下达':<12}{'参考':>9}{'现价':>9}" \
          f"{'+7天':>9}{'+30天':>9}{'至今':>9}{'至今$':>10}  状态"
    print(hdr); print("-" * len(hdr))
    for r in rows:
        if "excluded" in r:
            continue
        f = lambda k: f"{r[k]:+.1f}%" if r.get(k) is not None else "—"
        d = f"{r['至今$']:+,.0f}" if r.get("至今$") is not None else "—"
        print(f"{r['code']:<7}{r['action']:<22}{r['kind']:<6}{r['called']:<12}"
              f"{r['ref_used']:>9.2f}{r.get('现价', 0):>9.2f}"
              f"{f('+7天'):>9}{f('+30天'):>9}{f('至今'):>9}{d:>10}  {r['status']}")
    print()
    for k, v in summ.items():
        if k == "排除项":
            continue
        if v.get("n"):
            print(f"{k:<24} n={v['n']:<3} 命中率 {v['命中率']:5.1f}%  "
                  f"平均 {v['平均收益']:+6.2f}%  美元合计 {v['美元合计']:+,.0f}")
        else:
            print(f"{k:<24} n=0")
    if summ["排除项"]:
        print("\n排除出汇总(数据不全,不许用起点凑数):")
        for x in summ["排除项"]:
            print("  ·", x)
    todo, nopx = unlogged()
    print("\n台账完整性闸门:", "✅ 档案里的动作 call 都已入账" if not todo else "⚠️ 有未入账的 call")
    for g in todo:
        print("  ·", g)
    for g in nopx:
        print("  ○", g)
    print("\n" + RECONCILE_NOTE)
