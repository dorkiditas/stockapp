# -*- coding: utf-8 -*-
"""
组合 AUM / 净值回算 —— 用当前持仓×历史收盘价,回算过去一段时间的总资产曲线(模拟)。
美/A/港按固定汇率折成美元合成一条 AUM;净值=AUM归一到1.0。
历史源:美股=纳斯达克chart;A股/港股=腾讯K线(web.ifzq.gtimg.cn)。
说明:按"当前持仓恒定"回算,不含历史加减仓,是模拟净值不是真实交易记录。
"""
import os
import re
import datetime as dt
import requests
import pandas as pd
import tencent

USDCNY, USDHKD = 7.1, 7.85
BASE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(BASE, "nav_snapshots.csv")  # 真实每日AUM快照(本地,不上传)
_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                   "Accept": "application/json"})


def _us_hist(ticker, start):
    for ac in ("stocks", "etf"):
        try:
            r = _S.get(f"https://api.nasdaq.com/api/quote/{ticker}/chart",
                       params={"assetclass": ac, "fromdate": start,
                               "todate": dt.date.today().isoformat()}, timeout=15)
            ch = (r.json().get("data") or {}).get("chart") or []
            if ch:
                out = {}
                for p in ch:
                    z = p.get("z", {})
                    d = z.get("dateTime")  # 'M/D/YYYY'
                    c = z.get("close")
                    if d and c:
                        m, dd, y = d.split("/")
                        iso = f"{int(y):04d}-{int(m):02d}-{int(dd):02d}"
                        out[iso] = float(str(c).replace(",", ""))
                if out:
                    return out
        except Exception:
            continue
    return {}


def _cn_hist(symbol, count=320):
    # symbol: 腾讯符号 shXXXXXX/szXXXXXX/hkXXXXX
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param={symbol},day,,,{count},qfq")
    try:
        d = _S.get(url, timeout=15).json()["data"][symbol]
        k = d.get("qfqday") or d.get("day") or []
        return {row[0]: float(row[2]) for row in k if len(row) >= 3}
    except Exception:
        return {}


def build(holdings_df, days=250):
    """返回 DataFrame(index=日期, 'AUM', 'NAV') + 明细字典。"""
    start = (dt.date.today() - dt.timedelta(days=int(days * 1.5))).isoformat()
    series = {}
    skipped = []
    for _, r in holdings_df.iterrows():
        t = str(r["ticker"]).strip()
        sh = float(r["shares"])
        sym = tencent.to_symbol(t)
        if t.isdigit() or t.upper().endswith(".HK") or sym.startswith(("sh", "sz", "hk", "bj")):
            hist = _cn_hist(sym)
            fx = USDHKD if sym.startswith("hk") else USDCNY
        else:
            hist = _us_hist(t.upper(), start)
            fx = 1.0
        if not hist:
            skipped.append(t)
            continue
        s = pd.Series({pd.to_datetime(d): v / fx * sh for d, v in hist.items()})
        series[t] = s.sort_index()
    if not series:
        return pd.DataFrame(), skipped
    df = pd.DataFrame(series).sort_index().ffill().dropna()
    # 只留最近 days 个交易日
    df = df.tail(days)
    aum = df.sum(axis=1)
    out = pd.DataFrame({"AUM($)": aum.round(0), "净值": (aum / aum.iloc[0]).round(4)})
    return out, skipped


def record_snapshot():
    """记录当日实时AUM(美元)到 nav_snapshots.csv,每天一条(同日覆盖)。给'从今天起'的真实净值用。"""
    h = pd.read_csv(os.path.join(BASE, "holdings.csv"), dtype={"ticker": str})
    h["symbol"] = h["ticker"].apply(tencent.to_symbol)
    q = tencent.quote(h["ticker"].tolist())
    m = h.merge(q[["code", "market", "price"]], left_on="symbol", right_on="code", how="left")
    aum = 0.0
    for _, r in m.iterrows():
        p = r["price"]
        if p is None or pd.isna(p):
            continue
        v = p * r["shares"]
        if r["market"] == "A股":
            v /= USDCNY
        elif r["market"] == "港股":
            v /= USDHKD
        aum += v
    today = dt.date.today().isoformat()
    rows = {}
    if os.path.exists(SNAP):
        for ln in open(SNAP, encoding="utf-8").read().splitlines()[1:]:
            if "," in ln:
                d, a = ln.split(",", 1)
                rows[d] = a
    rows[today] = f"{aum:.0f}"
    with open(SNAP, "w", encoding="utf-8") as f:
        f.write("date,aum_usd\n")
        for d in sorted(rows):
            f.write(f"{d},{rows[d]}\n")
    return aum, today


def load_snapshots():
    if not os.path.exists(SNAP):
        return pd.DataFrame()
    df = pd.read_csv(SNAP)
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    h = pd.read_csv("holdings.csv", dtype={"ticker": str})
    df, sk = build(h, 180)
    print("跳过(无历史):", sk)
    print(df.head(3).to_string())
    print("...")
    print(df.tail(3).to_string())
    if len(df):
        ret = df["净值"].iloc[-1] - 1
        mdd = (df["净值"] / df["净值"].cummax() - 1).min()
        print(f"\n期间收益 {ret*100:+.1f}%  最大回撤 {mdd*100:.1f}%  当前AUM ${df['AUM($)'].iloc[-1]:,.0f}")
