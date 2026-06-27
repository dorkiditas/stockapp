# -*- coding: utf-8 -*-
"""
全市场数据模块 —— 真正的"全市场扫描"地基，不依赖用户自选清单。
A股全量：新浪 Market_Center（5500+ 只，带 PE/PB/市值/换手）。
美股全量：纳斯达克 screener API（7000+ 只，带市值）。
两者本机实测可用（东财批量被封、Yahoo 429，故走这两个）。
"""
import json
import re
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

_S = requests.Session()
_S.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
})

_SINA = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
         "Market_Center.getHQNodeData")


def _a_page(page):
    url = f"{_SINA}?page={page}&num=100&sort=mktcap&asc=0&node=hs_a"
    try:
        r = _S.get(url, headers={"Referer": "https://finance.sina.com.cn"}, timeout=15)
        return json.loads(r.text) or []
    except Exception:
        return []


def a_share_universe(node="hs_a"):
    """全 A股快照（并发分页）。约 5500 只，~10s。"""
    # 总数 -> 页数
    try:
        cnt = _S.get(f"{_SINA.replace('getHQNodeData','getHQNodeStockCount')}?node={node}",
                     headers={"Referer": "https://finance.sina.com.cn"}, timeout=15)
        total = int(re.sub(r"[^0-9]", "", cnt.text))
    except Exception:
        total = 5600
    pages = total // 100 + 2
    rows = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for data in ex.map(_a_page, range(1, pages + 1)):
            for d in data:
                mc = _f(d.get("mktcap"))
                nmc = _f(d.get("nmc"))
                rows.append({
                    "code": d.get("code"),
                    "symbol": d.get("symbol"),
                    "name": d.get("name"),
                    "price": _f(d.get("trade")),
                    "chg_pct": _f(d.get("changepercent")),
                    "pe": _f(d.get("per")),
                    "pb": _f(d.get("pb")),
                    "mktcap_yi": mc / 1e4 if mc else None,   # 万元->亿
                    "float_yi": nmc / 1e4 if nmc else None,
                    "turnover": _f(d.get("turnoverratio")),
                })
    # 去重(并发可能页边界重复)
    return pd.DataFrame(rows).drop_duplicates(subset="code").reset_index(drop=True)


def us_universe(limit=8000):
    """全美股快照（纳斯达克 screener，含 NYSE/Nasdaq/AMEX）。"""
    url = (f"https://api.nasdaq.com/api/screener/stocks?"
           f"tableonly=true&limit={limit}&offset=0")
    r = _S.get(url, headers={"Accept": "application/json"}, timeout=30)
    rows = r.json()["data"]["table"]["rows"]
    out = []
    for d in rows:
        mc = _money(d.get("marketCap"))
        out.append({
            "symbol": d.get("symbol"),
            "name": d.get("name"),
            "price": _money(d.get("lastsale")),
            "chg_pct": _f(str(d.get("pctchange", "")).replace("%", "")),
            "mktcap_b": mc / 1e9 if mc else None,
            "sector": d.get("sector"),
            "industry": d.get("industry"),
        })
    return pd.DataFrame(out)


def _f(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return None


def _money(x):
    """'$210.69' / '5,098,698,000,000' -> float。"""
    if x is None:
        return None
    s = re.sub(r"[^0-9.\-]", "", str(x))
    try:
        return float(s) if s else None
    except ValueError:
        return None


if __name__ == "__main__":
    import sys, time
    sys.stdout.reconfigure(encoding="utf-8")
    t = time.time()
    a = a_share_universe()
    print(f"A股 {len(a)} 只, 用时 {time.time()-t:.1f}s")
    print(a.head(5).to_string(index=False))
    t = time.time()
    u = us_universe()
    print(f"\n美股 {len(u)} 只, 用时 {time.time()-t:.1f}s, sector非空 {u['sector'].notna().sum()}")
    print(u.head(5).to_string(index=False))
