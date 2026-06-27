# -*- coding: utf-8 -*-
"""
腾讯行情数据源（qt.gtimg.cn）—— A股 / 港股 / 美股统一接口，免 token、无限流。
本机网络实测：东方财富批量接口被封、Yahoo 持续 429，唯腾讯可用，故全部走腾讯。

用户代码 -> 腾讯符号 规则：
  6位数字   600/601/603/605/688 -> sh######   ；000/001/002/003/300 -> sz######；
            8/4 开头 -> bj######（北交所）
  显式前缀   sh / sz / bj 原样保留
  港股       0700.HK / 00700 / hk00700 -> hk00700（补足5位）
  美股       AVGO / AAPL（纯字母）     -> usAVGO
"""
import requests
import pandas as pd

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Referer": "https://gu.qq.com/",
})


def to_symbol(code: str) -> str:
    """把用户输入的代码标准化成腾讯符号。"""
    c = code.strip()
    low = c.lower()
    if low.startswith(("sh", "sz", "bj", "hk", "us")):
        return low if low.startswith(("sh", "sz", "bj", "us")) else "hk" + c[2:]
    # 港股：000700.HK / 0700.HK / 700.HK
    if low.endswith(".hk"):
        num = c[:-3].lstrip("0") or "0"
        return "hk" + num.zfill(5)
    # 纯数字 -> A股
    if c.isdigit():
        if len(c) <= 5 and not c.startswith(("0", "3", "6", "8")):
            pass  # 兜底
        if c.startswith("6"):
            return "sh" + c.zfill(6)
        if c.startswith(("0", "3")):
            return "sz" + c.zfill(6)
        if c.startswith(("4", "8")):
            return "bj" + c.zfill(6)
        return "sh" + c.zfill(6)
    # 其余当美股
    return "us" + c.upper()


def market_of(symbol: str) -> str:
    if symbol.startswith(("sh", "sz", "bj")):
        return "A股"
    if symbol.startswith("hk"):
        return "港股"
    return "美股"


def quote(codes):
    """
    批量拉行情。codes 可为字符串列表或单个字符串。
    返回 DataFrame：code,name,market,price,prev_close,change,chg_pct,pe,pb,mktcap_yi,turnover
    A股带 PE/PB/市值；港美股一般只有价格与涨跌（腾讯不全给基本面）。
    """
    if isinstance(codes, str):
        codes = [codes]
    symbols = [to_symbol(c) for c in codes if c and c.strip()]
    if not symbols:
        return pd.DataFrame()

    rows = []
    # 分批，每批 60 个，避免 URL 过长
    for i in range(0, len(symbols), 60):
        batch = symbols[i:i + 60]
        url = "https://qt.gtimg.cn/q=" + ",".join(batch)
        r = _SESSION.get(url, timeout=15)
        r.encoding = "gbk"
        for line in r.text.strip().split(";"):
            line = line.strip()
            if "=" not in line or '"' not in line:
                continue
            sym = line.split("=")[0].replace("v_", "").strip()
            payload = line.split('"', 1)[1].rsplit('"', 1)[0]
            f = payload.split("~")
            if len(f) < 33:
                continue
            mkt = market_of(sym)
            row = {
                "code": sym,
                "name": f[1],
                "market": mkt,
                "price": _num(f[3]),
                "prev_close": _num(f[4]),
                "change": _num(f[31]),
                "chg_pct": _num(f[32]),
                "time": f[30] if len(f) > 30 else "",   # 行情时间戳
                "pe": None, "pb": None, "mktcap_yi": None, "turnover": None,
            }
            # A股字段更全
            if mkt == "A股" and len(f) > 46:
                row["turnover"] = _num(f[38])     # 换手率%
                row["pe"] = _num(f[39])           # 市盈率(动态)
                row["mktcap_yi"] = _num(f[45])    # 总市值(亿)
                row["pb"] = _num(f[46])           # 市净率
            rows.append(row)
    return pd.DataFrame(rows)


def _num(x):
    try:
        return float(x)
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    # 自测
    test = ["000338", "600000", "0700.HK", "AVGO", "AAPL"]
    df = quote(test)
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print(df.to_string())
