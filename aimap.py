# -*- coding: utf-8 -*-
"""
AI机会地图数据模块 —— 估值(PE/前瞻PE/PS) + 拥挤度(卖方目标隐含涨幅/52周位置) + 决断标签。
数据源(本机实测可用):
  · 美股估值: stockanalysis.com /overview (PE/forwardPE/营收→PS/评级)
  · 美股拥挤代理: 纳斯达克 summary (1年目标价隐含涨幅, 52周区间位置)
  · A股估值: 腾讯 qt.gtimg.cn (PE/PB/市值)
  · 韩股/其它: 无免费源,仅留逻辑备注
配套深度研究结论(2026-06):芯片是史上最拥挤交易(BofA 80%),从拥挤核心往洼地换仓。
"""
import re
import requests
from concurrent.futures import ThreadPoolExecutor
import tencent
import yahoo

_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"})

# 三档决断 → {代码: (名称, 备注)}。代码:美股字母 / A股6位 / 韩股.KS(无源)
TIERS = {
    "🟢 机会(估值过关+不拥挤)": {
        "MU":   ("美光", "前瞻PE仅11,卖到2028缺货,基本面最硬;别追大涨日,回调拿"),
        "SNDK": ("闪迪", "存储同逻辑,前瞻PE低;比追龙头SK海力士更不挤"),
        "CRM":  ("赛富时", "PS2.9/前瞻PE11,又便宜又被恨的逆向注"),
        "MSFT": ("微软", "PE23,软件里被冷落的优质核心"),
        "009150.KS": ("三星电机", "玻璃基板,~30%成本优势抢CoWoS;2027放量,埋伏(韩股无实时源)"),
        "011070.KS": ("LG Innotek", "玻璃基板先进封装,同上(韩股无实时源)"),
    },
    "🟡 持有/你的仓(按估值给动作)": {
        "CRDO": ("Credo", "★该减:107倍PE、比DCF高59%,估值+拥挤双顶(兑现,非看空)"),
        "AVGO": ("博通", "留:前瞻PE26,质量在"),
        "QCOM": ("高通", "便宜(PE25)但Hold评级没催化;价值持有可,别当AI加仓"),
        "GEV":  ("GE Vernova", "前瞻PE60开始贵,留但别加"),
    },
    "🔴 避开/别加(贵+挤+高位)": {
        "300308": ("中际旭创", "全球最挤:公募通信仓位创纪录13.1%、超2021宁德峰值"),
        "688498": ("源杰科技", "PS585,A股光模块估值离谱"),
        "ALAB": ("Astera Labs", "PS71、超最高卖方目标价"),
        "ARM":  ("Arm", "PS95,估值脱离引力"),
        "ASML": ("阿斯麦", "设备:52周94%高位+股价超目标价"),
        "KLAC": ("科磊", "设备:同上,别追高"),
        "PLTR": ("Palantir", "低价陷阱:跌到52周低但PS仍59"),
    },
}


def _num(x, unit=False):
    if x is None:
        return None
    s = str(x).replace(",", "").replace("$", "")
    m = re.search(r"-?[\d.]+", s)
    if not m:
        return None
    v = float(m.group())
    if unit:
        if "T" in s: v *= 1e12
        elif "B" in s: v *= 1e9
        elif "M" in s: v *= 1e6
    return v


def _us_valuation(sym):
    try:
        d = _S.get(f"https://stockanalysis.com/api/symbol/s/{sym}/overview",
                   timeout=12).json().get("data") or {}
    except Exception:
        return {}
    mc, rev = _num(d.get("marketCap"), True), _num(d.get("revenue"), True)
    return {"pe": _num(d.get("peRatio")), "fpe": _num(d.get("forwardPE")),
            "ps": round(mc / rev, 1) if (mc and rev) else None,
            "rating": d.get("analysts")}


def _us_crowding(sym):
    try:
        sd = (_S.get(f"https://api.nasdaq.com/api/quote/{sym}/summary?assetclass=stocks",
              headers={"Accept": "application/json"}, timeout=12).json()
              .get("data") or {}).get("summaryData") or {}
    except Exception:
        return {}
    g = lambda k: (sd.get(k) or {}).get("value")
    price, tgt = _num(g("PreviousClose")), _num(g("OneYrTarget"))
    hl = g("FiftTwoWeekHighLow") or ""
    hi = _num(hl.split("/")[0]) if "/" in hl else None
    lo = _num(hl.split("/")[1]) if "/" in hl else None
    return {"upside": round((tgt / price - 1) * 100) if (price and tgt) else None,
            "pos52": round((price - lo) / (hi - lo) * 100) if (price and hi and lo and hi > lo) else None}


def _one(code, name, note):
    row = {"代码": code, "名称": name, "现价": None, "PE": None, "前瞻PE": None,
           "PS": None, "隐含涨幅%": None, "52周位置%": None, "评级": None, "判定理由": note}
    up = code.upper()
    if ("." in code) and not up.endswith(".HK"):  # 台/日/韩/欧 等带后缀 → Yahoo
        y = yahoo.quote(up)
        if y:
            row.update({"名称": y.get("name") or name, "现价": y.get("price"),
                        "PE": y.get("pe"), "前瞻PE": y.get("fpe"), "PS": y.get("ps"),
                        "隐含涨幅%": y.get("upside"), "52周位置%": y.get("pos52")})
        return row
    if code.isdigit():  # A股 → 腾讯
        q = tencent.quote([code])
        if not q.empty and q.iloc[0].get("price") is not None:
            r = q.iloc[0]
            row.update({"现价": r["price"], "PE": r.get("pe"),
                        "名称": r["name"] or name})
        return row
    # 美股
    q = tencent.quote([code])
    if not q.empty and q.iloc[0].get("price") is not None:
        row["现价"] = q.iloc[0]["price"]
        if not row["名称"]:
            row["名称"] = q.iloc[0]["name"] or code
    v, c = _us_valuation(code), _us_crowding(code)
    row.update({"PE": v.get("pe"), "前瞻PE": v.get("fpe"), "PS": v.get("ps"),
                "评级": v.get("rating"), "隐含涨幅%": c.get("upside"),
                "52周位置%": c.get("pos52")})
    return row


def us_val_many(symbols):
    """批量拉美股 forward PE(给全球选股的价值筛选补估值)。返回 {sym: {pe,fpe,ps}}。"""
    with ThreadPoolExecutor(max_workers=12) as ex:
        res = list(ex.map(lambda s: (s, _us_valuation(s)), symbols))
    return dict(res)


def build_many(items):
    """通用:items=[(代码,备注),...] -> [行dict],并发拉估值+拥挤。供任意主题页复用。"""
    with ThreadPoolExecutor(max_workers=10) as ex:
        return list(ex.map(lambda kv: _one(kv[0], "", kv[1]), items))


def build():
    """返回 {档位: [行dict,...]}，并发拉取。"""
    jobs = []
    for tier, mp in TIERS.items():
        for code, (name, note) in mp.items():
            jobs.append((tier, code, name, note))
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(lambda a: (a[0], _one(a[1], a[2], a[3])), jobs))
    out = {t: [] for t in TIERS}
    for tier, row in results:
        out[tier].append(row)
    return out


if __name__ == "__main__":
    import sys, pandas as pd
    sys.stdout.reconfigure(encoding="utf-8")
    data = build()
    for tier, rows in data.items():
        print(f"\n=== {tier} ===")
        df = pd.DataFrame(rows)[["名称", "代码", "现价", "PE", "前瞻PE", "PS",
                                 "隐含涨幅%", "52周位置%", "评级"]]
        print(df.to_string(index=False))
