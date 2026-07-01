# -*- coding: utf-8 -*-
"""
每日微信推送 —— 把"操作建议+持仓盈亏+买入候选"发到微信(Server酱)。
国内直达、不用VPN、不用装app。由 GitHub Actions 每天定时云端跑。
SendKey 从环境变量 SERVERCHAN_KEY 读取(GitHub repo secret)。
本地直接运行=只打印不发送(没设key时)。
"""
import os
import datetime as dt
import requests
import pandas as pd

import tencent
import forward
from calls import MY_CALLS, MY_BUYS

BASE = os.path.dirname(os.path.abspath(__file__))
HOLDINGS = os.path.join(BASE, "holdings.csv")
CUR = {"美股": "$", "A股": "¥", "港股": "HK$"}


def build_digest():
    today = dt.date.today().strftime("%m-%d")
    h = pd.read_csv(HOLDINGS, dtype={"ticker": str})
    q = tencent.quote(h["ticker"].tolist())
    h["symbol"] = h["ticker"].apply(tencent.to_symbol)
    m = h.merge(q[["code", "name", "market", "price", "prev_close"]],
                left_on="symbol", right_on="code", how="left")
    m["市值"] = m["price"] * m["shares"]
    m["今日盈亏"] = (m["price"] - m["prev_close"]) * m["shares"]
    m["盈亏%"] = (m["price"] / m["cost"] - 1) * 100

    lines = [f"## 📈 选股工作台 · {today}", ""]

    # 风险雷达(只报警,不替你决策)
    try:
        import risk_radar
        risks = risk_radar.all_risks()
        if risks:
            lines.append("### ⚠️ 风险雷达")
            for w in risks:
                lines.append(f"- {w}")
            lines.append("")
    except Exception:
        pass

    # 持仓快照(分币种)
    lines.append("### 💰 持仓")
    for g in ["美股", "A股", "港股"]:
        sub = m[m["market"] == g]
        if len(sub) and sub["市值"].notna().any():
            sym = CUR.get(g, "")
            lines.append(f"- **{g}**:市值 {sym}{sub['市值'].sum():,.0f} · "
                         f"今日 {sym}{sub['今日盈亏'].sum():+,.0f}")
    lines.append("")

    # 最该动的(🔴 平/砍 + 🟢买入头号)
    lines.append("### 🎯 最该动的")
    lines.append("- 🟢 **建 MU 仓**(存储,全链最佳风险收益:前瞻PE11/明年+96%/被低配)")
    lines.append("- 🔴 **平掉 BE 空单**(逆势流血,与你GEV多头矛盾)")
    lines.append("- 🔴 **砍 QCOM**(明年0增长)→ 腾钱;🟡 CRDO减一部分换CIEN")
    lines.append("")

    # 持仓操作快评(只列要动的:🔴/🟡)
    lines.append("### 📌 要动的持仓")
    act_rows = []
    for _, r in m.iterrows():
        act, reason = MY_CALLS.get(str(r["ticker"]).upper(), ("", ""))
        if act and act[0] in "🔴🟡":
            nm = r["name"] or r["ticker"]
            pl = f"{r['盈亏%']:+.0f}%" if pd.notna(r["盈亏%"]) else ""
            act_rows.append(f"- {act} **{nm}** {pl} — {reason.split(';')[0]}")
    lines += act_rows[:8] or ["- (无)"]
    lines.append("")

    # 买入候选
    lines.append("### 💡 买入候选(其他市场补缺口)")
    for code, (act, reason) in list(MY_BUYS.items())[:5]:
        lines.append(f"- {act} **{code}** — {reason.split(';')[0].split(',')[0]}")
    lines.append("")
    lines.append("> 我的判断,非保证。存储是周期股,加仓非all-in。")

    title = f"选股日报 {today} · 建MU/平BE"
    return title, "\n".join(lines)


def _load_key():
    k = os.environ.get("SERVERCHAN_KEY", "").strip()
    if k:
        return k
    # 本地配置兜底(server_chan.json,已gitignore不上传)
    cfg = os.path.join(BASE, "server_chan.json")
    if os.path.exists(cfg):
        import json
        try:
            return (json.load(open(cfg, encoding="utf-8")).get("key") or "").strip()
        except Exception:
            return ""
    return ""


def send(title, md):
    key = _load_key()
    if not key:
        print("[未设 SERVERCHAN_KEY,只打印不发送]\n")
        print(title, "\n")
        print(md)
        return False
    url = f"https://sctapi.ftqq.com/{key}.send"
    r = requests.post(url, data={"title": title, "desp": md}, timeout=15)
    ok = r.status_code == 200 and '"code":0' in r.text
    print("发送", "成功" if ok else f"失败 {r.status_code} {r.text[:120]}")
    return ok


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    # 净值快照改由"自动研究员"(有IB MCP连接)记真实Net Liq,这里不再记gross,避免曲线失真。
    t, md = build_digest()
    send(t, md)
