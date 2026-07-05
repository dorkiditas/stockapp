# -*- coding: utf-8 -*-
"""
存储周期驾驶舱 —— 把"我说的存储"变成"你信的存储"。
两层:
  1) 周期硬指标(事实):合约价/库存/稼动率/长协/HBM4。无免费合约价API,由研究员据研报+TrendForce板手动更新(带日期)。
  2) 标的实时估值:MU/SNDK 走 stockanalysis+纳斯达克(本机可用);韩股无免费源→用研报参考值。
前瞻PE 越低 = 市场越把它当"周期顶"给白菜价 = 认知差越大。
"""
import aimap
import forward

# ── 一句话逻辑(命根子)──
THESIS = ("内存过去是暴涨暴跌的烂周期股;这轮结构变了——①3寡头有纪律不自杀式扩产 "
          "②AI造出全新需求(HBM+更多DRAM+eSSD) ③长协+capex纪律把新供给锁到2029。"
          "但市场还用老眼光给白菜价(前瞻PE 6~11x)。这个认知差=edge。打法:拿到2027-28,盯2029供给。")

# ── 周期硬指标(事实 · 手动更新)──
FACTS_ASOF = "2026-07-04"
FACTS_SRC = "高盛存储跟踪 / TrendForce / 大摩NAND展望 / 华安·存储深度 / 美光长协纪要 / web(7/4)"

# (指标, 最新值, 方向 up/down/flat, 白话)
CONTRACT_PRICE = [
    ("DRAM常规 3Q26e", "+13~18% qoq", "up", "PC/服务器/手机全涨"),
    ("企业级eSSD 3Q26e", "+18~23% qoq", "up", "AI最相关、最强的一档"),
    ("NAND综合 3Q26e", "+10~15% qoq", "up", "唯一软点=手机NAND(+5~10%)"),
    ("DRAM合约 2H-May实测", "DDR4 +19~25% / DDR5 +2.75%", "up", "现货板实测,不是预测"),
    ("2Q26环比(已发生)", "服务器DRAM +53~58% / LPDDR +73~85%", "up", "涨幅史诗级"),
]
FUNDAMENTALS = [
    ("行业库存", "1.0~1.1 个月", "低=健康,去化快"),
    ("晶圆厂稼动率", "98~99%", "三家基本满产"),
    ("新增供给落地", "2029 年后", "长协+capex纪律,供给被锁死"),
    ("下行保护", "美光16份take-or-pay到2030、毛利下限>60%", "历史上从没有过"),
    ("HBM4 格局", "海力士唯一量产,拿下英伟达Vera Rubin订单2/3+;份额~60%", "海力士质量最高"),
    ("HBM vs DRAM", "DRAM价已反超HBM(倒挂);三星HBM合约价上调high-teens%", "原厂更愿扩DRAM→常规DRAM更紧"),
    ("HBM市场规模", "$35B(25)→$58B(26)→$100B(28E)", "三年近3倍,三家2026全售罄"),
    ("消费端软点", "手机/PC涨价后现砍单(大摩7/2)", "买AI内存别碰消费内存;DRAM>NAND"),
]

# ── 综合判断(研究员维护)──
VERDICT = ("🟢 周期仍硬:价在涨 + 库存极低 + 满产 + 长协锁到2029。"
           "没有见顶信号。软点只在手机NAND。")

# ── 牛/熊 盯什么 ──
WATCH_BULL = [
    "合约价继续环比涨(每月TrendForce板)",
    "三家capex仍克制、不抢跑扩产",
    "HBM4顺利上量、超大厂capex不砍",
]
WATCH_BEAR = [
    "⚠️ 合约价环比转平/转跌 = 第一根警报",
    "⚠️ 三家宣布大扩产(2029供给种子提前)",
    "⚠️ AI capex证伪 / 超大厂砍单",
    "⚠️ 韩元破1550(压韩国两家估值)",
]

# ── 标的:代码→(名称,旗,一句话edge,韩股参考前瞻PE)──
NAMES = [
    ("MU",         "美光",     "🇺🇸", "最干净+take-or-pay下行保护", None),
    ("SNDK",       "闪迪",     "🇺🇸", "NAND同逻辑,8月投资者日催化", None),
    ("000660.KS",  "SK海力士", "🇰🇷", "HBM4唯一量产,质量最高", 7),
    ("005930.KS",  "三星",     "🇰🇷", "最便宜+外资持股15年最低配", 6),
    ("EWY",        "韩国ETF",  "🇰🇷", "一键三星+海力士,认知浅时的入门仓", None),
]


def valuation():
    """返回每个标的的估值行。美股实时;韩股用研报参考值(无免费源)。"""
    out = []
    for code, name, flag, edge, kref in NAMES:
        row = {"标的": f"{flag} {name}", "代码": code, "一句话edge": edge}
        if code.endswith(".KS"):
            row["PE"] = None
            row["前瞻PE"] = kref
            row["明年EPS增速%"] = None
            row["前瞻信号"] = "研报参考(韩股无实时源)"
        elif code == "EWY":  # ETF无EPS前瞻,不跑analyst端点
            v = aimap._us_valuation(code)
            row["PE"] = v.get("pe")
            row["前瞻PE"] = v.get("fpe")
            row["明年EPS增速%"] = None
            row["前瞻信号"] = "ETF·一键三星+海力士"
        else:
            v = aimap._us_valuation(code)
            row["PE"] = v.get("pe")
            row["前瞻PE"] = v.get("fpe")
            f = forward.fetch(code)
            row["明年EPS增速%"] = f.get("明年EPS增速%") if f else None
            row["前瞻信号"] = forward.signal(f) if f else "—"
        out.append(row)
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("VERDICT:", VERDICT)
    for r in valuation():
        print(r)
