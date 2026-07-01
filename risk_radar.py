# -*- coding: utf-8 -*-
"""
风险雷达 —— 每日扫宏观/汇率红线,给日报和App提示(只报警,不替他决策)。
汇率用 open.er-api.com(免key、哪都能用)。账户保证金风险由自动研究员经IB MCP另补。
"""
import requests

_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120"})


def fx_risk():
    """返回警告字符串列表(无风险则空)。"""
    out = []
    try:
        d = _S.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()["rates"]
    except Exception:
        return out
    krw, cny = d.get("KRW"), d.get("CNY")
    if krw:
        if krw >= 1550:
            out.append(f"🔴 韩元 {krw:.0f}(≥1550危机级,2009来最低)——压韩国存储(EWY/海力士/三星)、加剧外资抛A股科技")
        elif krw >= 1500:
            out.append(f"🟡 韩元 {krw:.0f}(偏弱,逼近1550危机线)——盯韩国存储与成长股估值压力")
    if cny and cny >= 7.25:
        out.append(f"🟡 人民币 {cny:.2f}(走弱)——利好出口、但外资情绪偏空")
    return out


def all_risks():
    return fx_risk()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    r = all_risks()
    print("风险雷达:", r if r else "暂无红线")
