# -*- coding: utf-8 -*-
"""
Yahoo Finance 数据源 —— 专给日股(.T)/韩股(.KS/.KQ)补估值,本机其它源不覆盖。
用 cookie+crumb 流程拿授权。返回 价格/涨跌/PE/前瞻PE/PS/市值/目标隐含涨幅/52周位置。
注意:日股价以日元、韩股以韩元计;PE/PS 与货币无关可直接横向比。
"""
import requests

_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"})
_CRUMB = None


def _ensure_crumb():
    global _CRUMB
    if _CRUMB:
        return _CRUMB
    # fc.yahoo.com 已失效,多源兜底取 cookie(云端美国IP可成功)
    for seed in ("https://fc.yahoo.com", "https://finance.yahoo.com/quote/AAPL",
                 "https://finance.yahoo.com"):
        try:
            _S.get(seed, timeout=12)
        except Exception:
            pass
    try:
        c = _S.get("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=12).text
        if c and "<" not in c and "{" not in c:
            _CRUMB = c
    except Exception:
        _CRUMB = None
    return _CRUMB


# region 代码:us 美 / jp 日 / kr 韩 / tw 台 / hk 港 / in 印 / gb 英 / de 德 / fr 法
def global_screen(region, size=100):
    """Yahoo 筛选器:按市场拉市值前 N 只(带 PE/前瞻PE/市值)。返回 DataFrame。
    云端可用;本机VPN下crumb常失败会返回空。"""
    import pandas as pd
    crumb = _ensure_crumb()
    if not crumb:
        return pd.DataFrame()
    rows = []
    for off in range(0, size, 100):
        body = {"size": min(100, size - off), "offset": off,
                "sortField": "intradaymarketcap", "sortType": "DESC",
                "quoteType": "EQUITY",
                "query": {"operator": "AND",
                          "operands": [{"operator": "EQ", "operands": ["region", region]}]}}
        try:
            r = _S.post("https://query2.finance.yahoo.com/v1/finance/screener",
                        params={"crumb": crumb}, json=body,
                        headers={"Content-Type": "application/json"}, timeout=15)
            qs = r.json()["finance"]["result"][0]["quotes"]
        except Exception:
            break
        if not qs:
            break
        for q in qs:
            mc = q.get("marketCap")
            rows.append({
                "代码": q.get("symbol"), "名称": q.get("shortName") or q.get("longName"),
                "现价": q.get("regularMarketPrice"),
                "今日%": q.get("regularMarketChangePercent"),
                "PE": q.get("trailingPE"), "前瞻PE": q.get("forwardPE"),
                "市值(亿)": round(mc / 1e8) if mc else None,
                "币种": q.get("currency"),
            })
    return pd.DataFrame(rows)


def quote(sym):
    """返回单只日/韩股的关键字段(失败返回 {})。并发下偶发丢包,重试2次。"""
    res = None
    for attempt in range(3):
        crumb = _ensure_crumb()
        if not crumb:
            continue
        try:
            r = _S.get(f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{sym}",
                       params={"modules": "summaryDetail,defaultKeyStatistics,price,financialData",
                               "crumb": crumb}, timeout=12)
            j = r.json()
            res = j["quoteSummary"]["result"][0]
            break
        except Exception:
            globals()["_CRUMB"] = None if attempt == 1 else _CRUMB  # 第2次失败刷新crumb
            continue
    if res is None:
        return {}
    sd = res.get("summaryDetail", {})
    ks = res.get("defaultKeyStatistics", {})
    pr = res.get("price", {})
    fd = res.get("financialData", {})

    def g(d, k):
        return (d.get(k) or {}).get("raw")

    price = g(pr, "regularMarketPrice") or g(fd, "currentPrice")
    prev = g(sd, "previousClose")
    tgt = g(fd, "targetMeanPrice")
    hi, lo = g(sd, "fiftyTwoWeekHigh"), g(sd, "fiftyTwoWeekLow")
    return {
        "name": pr.get("shortName"),
        "price": price,
        "chg_pct": round((price / prev - 1) * 100, 1) if (price and prev) else None,
        "pe": g(sd, "trailingPE") or g(ks, "trailingPE"),
        "fpe": g(sd, "forwardPE") or g(ks, "forwardPE"),
        "ps": g(ks, "priceToSalesTrailing12Months") or g(sd, "priceToSalesTrailing12Months"),
        "mcap": g(pr, "marketCap"),
        "upside": round((tgt / price - 1) * 100) if (tgt and price) else None,
        "pos52": round((price - lo) / (hi - lo) * 100) if (price and hi and lo and hi > lo) else None,
        "currency": pr.get("currency"),
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for s in ["6857.T", "8035.T", "4063.T", "000660.KS", "005930.KS", "009150.KS"]:
        q = quote(s)
        print(f"{s:<12}{q.get('name','?'):<16} 价{q.get('price')} PE{q.get('pe')} "
              f"前瞻{q.get('fpe')} PS{q.get('ps')} 隐含{q.get('upside')}% 52周{q.get('pos52')}%")
