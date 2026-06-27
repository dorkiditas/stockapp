# -*- coding: utf-8 -*-
"""
催化模块 —— 扫个股近14天新闻(Google News RSS,免费),判定近期是否有正向催化。
美股按 "TICKER stock" 英文搜;A股(6位数字)按中文名搜。
输出:label(🟢有正向催化/⚪中性/🔴近期负面) + 最具代表性的标题 + 日期。
"""
import re
import html
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor

_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"})

POS = ["beat", "beats", "raise", "raises", "hike", "hikes", "upgrade", "upgraded",
       "surge", "surges", "rips", "rip", "jump", "jumps", "soar", "soars", "record",
       "all-time high", "wins", "win", "contract", "deal", "partnership", "expansion",
       "monster target", "boost", "boosts", "rally", "rallies", "outperform", "tops",
       "strong", "beat estimates", "price target", "buy rating", "initiates buy",
       # 中文
       "大涨", "涨停", "超预期", "上调", "中标", "签约", "增持", "回购", "创新高",
       "突破", "订单", "扩产", "放量", "买入评级", "目标价上调", "业绩预增",
       "大增", "增长", "翻倍", "翻番", "高增", "猛增", "暴增", "净利润超", "同比增"]
NEG = ["plunge", "plunges", "miss", "misses", "cut", "cuts", "downgrade", "downgraded",
       "falls", "fall", "drop", "drops", "sink", "sinks", "slump", "slumps", "warning",
       "warn", "lawsuit", "probe", "weak", "disappoint", "disappoints", "halts", "recall",
       "fraud", "investigation", "tumble", "tumbles", "selloff", "sell-off",
       # 中文
       "大跌", "跌停", "下调", "减持", "亏损", "暴跌", "不及预期", "立案", "诉讼",
       "业绩预减", "商誉减值", "退市", "处罚", "质押爆仓"]


def _feed(query, zh=False):
    hl = "zh-CN&gl=CN&ceid=CN:zh-Hans" if zh else "en-US&gl=US&ceid=US:en"
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(f"{query} when:14d") + f"&hl={hl}")
    try:
        r = _S.get(url, timeout=12)
    except Exception:
        return []
    out = []
    for it in re.findall(r"<item>(.*?)</item>", r.text, re.S)[:8]:
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        d = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
        if t:
            title = html.unescape(re.sub(r"<.*?>", "", t.group(1)))
            out.append((d.group(1)[:16] if d else "", title))
    return out


def classify(ticker, name="", is_a=False):
    """返回 dict: 催化, 评分, 头条, 日期。"""
    if is_a:  # A股用中文名搜
        items = _feed(name or ticker, zh=True)
    elif ticker.upper().endswith((".T", ".KS", ".KQ")):  # 日韩用公司名搜
        items = _feed(f"{name} stock") if name else _feed(ticker)
    else:     # 美股/港股用代码搜
        items = _feed(f"{ticker} stock")
    if not items:
        return {"催化": "—无数据", "评分": 0, "头条": "", "日期": ""}

    best_pos, best_score = None, 0
    pos_n = neg_n = 0
    for d, title in items:
        low = title.lower()
        p = sum(1 for k in POS if k in low or k in title)
        n = sum(1 for k in NEG if k in low or k in title)
        pos_n += p
        neg_n += n
        if p - n > best_score:
            best_score, best_pos = p - n, (d, title)
    net = pos_n - neg_n
    if net >= 2 and best_pos:
        label = "🟢强正向"
    elif net >= 1:
        label = "🟢有催化"
    elif net <= -2:
        label = "🔴近期负面"
    elif net < 0:
        label = "🟡偏负面"
    else:
        label = "⚪中性"
    head = best_pos or items[0]
    return {"催化": label, "评分": net, "头条": head[1][:80], "日期": head[0]}


def classify_many(rows):
    """rows: [(ticker, name, is_a),...] -> {ticker: result}。并发。"""
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(lambda r: (r[0], classify(*r)), rows))
    return dict(res)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    tests = [("AVGO", "博通", False), ("MU", "美光", False), ("CRDO", "Credo", False),
             ("300308", "中际旭创", True), ("PLTR", "Palantir", False)]
    for tk, res in classify_many(tests).items():
        print(f"{tk:<8}{res['催化']:<8} 评分{res['评分']:+d}  [{res['日期']}] {res['头条']}")
