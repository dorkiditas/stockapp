# -*- coding: utf-8 -*-
"""
每日微信推送 —— 把"操作建议+持仓盈亏+买入候选"发到微信(Server酱)。
国内直达、不用VPN、不用装app。由 GitHub Actions 每天定时云端跑。
SendKey 从环境变量 SERVERCHAN_KEY 读取(GitHub repo secret)。
本地直接运行=只打印不发送(没设key时)。
"""
import os
import requests


BASE = os.path.dirname(os.path.abspath(__file__))
HOLDINGS = os.path.join(BASE, "holdings.csv")


def build_digest():
    """日报正文 = daily_brief.render() 的输出 + App 入口。

    ⚠️ 2026-08-15 重写。旧版这里有一整段【写死】的"最该动的":
        「🟢 建 MU 仓」「🔴 平掉 BE 空单」「🔴 砍 QCOM」「🟡 CRDO 减一部分换 CIEN」。
    到 8/15 这四条是三条错、一条违规:
        · 建 MU  → **违反她 7/30 自订的 BUY_SIDE_LOCKED**(杠杆≥1.5x 不许出买方建议)
        · 平 BE  → BE 空头 7/28 已平,仓位不存在
        · CRDO   → 8/3 已清仓
        · 砍 QCOM→ 8/7 CPU_RENAISSANCE 已写死【不许再对 QCOM 出减仓 call】
    一份每天自动发出、内容却停在一个月前的日报,比不发更危险。
    现在改成:**一个字都不写死**,全部由 daily_brief 当天重算,并带买方措辞闸门。
    """
    import daily_brief
    title, md = daily_brief.render()          # 闸门在 render 里,违规会抛 AssertionError
    lines = [md, "", "### 📱 打开工作台",
             "- 永久网址(云端,笔记本无关):https://stockapp-99rbhabczaebwv2fkzqm9a.streamlit.app",
             "- 家里WiFi(固定):http://10.0.66.237:8501"]
    try:
        turl = open(os.path.join(BASE, "tunnel_url.txt"), encoding="utf-8").read().strip()
        if turl:
            lines.append(f"- 本机直连(最快,需笔记本开机):{turl}")
    except Exception:
        pass
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
    # 2026-08-07 傍晚:sctapi.ftqq.com 从她这台机器连接被重置(ConnectionResetError 10054,
    # 沙箱内外一致、同时 baidu 200 = 不是断网,是这个 host 不通)。旧域名 sc.ftqq.com 实测可用。
    # 因此改为双端点依次尝试,任一成功即算发出,避免风险推送因单一线路挂掉而静默丢失。
    r = None
    for url in (f"https://sctapi.ftqq.com/{key}.send", f"https://sc.ftqq.com/{key}.send"):
        try:
            r = requests.post(url, data={"text": title, "title": title, "desp": md}, timeout=20)
            if r.status_code == 200 and '"code":0' in r.text:
                break
        except requests.RequestException as e:
            print(f"[push] {url.split('/')[2]} 不可用: {type(e).__name__}")
            r = None
    if r is None:
        print("[push] 两个端点都失败,本次推送未发出")
        return False
    ok = r.status_code == 200 and '"code":0' in r.text
    # Windows 控制台默认 cp1252,中文 print 会抛 UnicodeEncodeError 让调用脚本 exit(1)
    # (2026-08-02 夜:周日复盘推送已发出但脚本仍报错退出)。发送成败不该被打印毁掉。
    try:
        print("发送", "成功" if ok else f"失败 {r.status_code} {r.text[:120]}")
    except UnicodeEncodeError:
        print("SEND", "OK" if ok else f"FAIL {r.status_code}")
    return ok


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    # 净值快照改由"自动研究员"(有IB MCP连接)记真实Net Liq,这里不再记gross,避免曲线失真。
    t, md = build_digest()
    send(t, md)
