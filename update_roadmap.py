# -*- coding: utf-8 -*-
"""值守每班运行:把 account_risk.json / offmarket_assets.csv 的最新数字回填进桌面基金路线图.html。
教训:close-the-loop——更新源文件≠交付,她打开的是HTML。此脚本让路线图永不停更。"""
import json
import re
import sys
from pathlib import Path

STOCKAPP = Path(__file__).resolve().parent
ROADMAP = Path(r"C:\Users\xiaoy\OneDrive\Desktop\基金路线图.html")
RISK = STOCKAPP / "account_risk.json"
OFFMARKET = STOCKAPP / "offmarket_assets.csv"
CNY_USD = 7.1
GOAL = 1_000_000.0


def ant_usd_and_date():
    """场外(蚂蚁)总额USD及其数据日期;文件缺失时返回(0, '无')。"""
    try:
        for line in OFFMARKET.read_text(encoding="utf-8").splitlines():
            parts = line.split(",")
            if len(parts) >= 5 and parts[0].strip() == "蚂蚁理财账户总计":
                return float(parts[3]) / CNY_USD, parts[4].strip()
    except FileNotFoundError:
        pass
    return 0.0, "无"


def sub_once(html, pattern, repl, name):
    new, n = re.subn(pattern, repl, html, count=1, flags=re.S)
    if n != 1:
        print(f"WARN: 锚点未命中 [{name}] — 页面结构可能被改动,请人工检查", file=sys.stderr)
        return html, False
    return new, True


def main():
    risk = json.loads(RISK.read_text(encoding="utf-8"))
    date = risk["date"]
    net_liq = risk["net_liq"]
    lev = float(risk["leverage"])
    buf = risk["excess_liquidity"]
    a_usd = risk.get("a_share_usd", 0.0)
    true_nav = risk.get("true_nav", net_liq + a_usd)
    buf_pct = risk.get("buffer_pct_of_nav")
    dd_zero = risk.get("longs_drawdown_to_zero_buffer_pct")

    ant, ant_date = ant_usd_and_date()
    total = true_nav + ant
    pct = total / GOAL * 100
    star = "*" if ant_date not in (date,) else ""
    ant_note = f"蚂蚁¥{ant * CNY_USD / 10000:.1f}万(*{ant_date}旧数,待截图)" if ant else "蚂蚁待录入"

    html = ROADMAP.read_text(encoding="utf-8")
    ok = []

    html, hit = sub_once(html, r'(id="kpi-date">)[^<]*', rf"\g<1>总流动资产（更新 {date}）", "kpi-date"); ok.append(hit)
    html, hit = sub_once(html, r'(id="kpi-total">)[^<]*', rf"\g<1>~${total / 10000:.1f}万{star}", "kpi-total"); ok.append(hit)
    html, hit = sub_once(html, r'(id="kpi-total-note">)[^<]*',
                         rf"\g<1>IB ${net_liq / 10000:.1f}万 + A股 ${a_usd / 10000:.1f}万 + {ant_note}", "kpi-total-note"); ok.append(hit)
    html, hit = sub_once(html, r'(id="kpi-lev">)[^<]*', rf"\g<1>{lev:.2f}×", "kpi-lev"); ok.append(hit)
    gate = "距解锁线(<2.5x)只差一线" if 2.5 <= lev < 2.6 else ("已低于2.5x——解锁计时中(需连续达标)" if lev < 2.5 else "gate深锁:只准减仓")
    html, hit = sub_once(html, r'(id="kpi-lev-note">)[^<]*', rf"\g<1>{gate}", "kpi-lev-note"); ok.append(hit)
    html, hit = sub_once(html, r'(id="kpi-truenav">)[^<]*', rf"\g<1>${true_nav / 10000:.1f}万", "kpi-truenav"); ok.append(hit)
    html, hit = sub_once(html, r'(id="kpi-buffer">)[^<]*', rf"\g<1>${buf:,.0f}", "kpi-buffer"); ok.append(hit)
    if buf_pct is not None and dd_zero is not None:
        html, hit = sub_once(html, r'(id="kpi-buffer-flag">)[^<]*',
                             rf"\g<1>净值的{buf_pct}% · 多头再跌{dd_zero}%缓冲才归零", "kpi-buffer-flag"); ok.append(hit)
    html, hit = sub_once(html, r'(id="pb-label">)[^<]*',
                         rf"\g<1>${total / 10000:.1f}万{star} / $100万 · {pct:.1f}%（*蚂蚁按{ant_date}旧数）" if star
                         else rf"\g<1>${total / 10000:.1f}万 / $100万 · {pct:.1f}%", "pb-label"); ok.append(hit)
    html, hit = sub_once(html, r'(id="pb-fill" style="width:)[0-9.]+%', rf"\g<1>{pct:.1f}%", "pb-fill"); ok.append(hit)
    mmdd = f"{int(date[5:7])}/{int(date[8:10])}"
    html, hit = sub_once(html, r'(id="pb-now">)[^<]*', rf"\g<1>{mmdd} {pct:.1f}%{star}", "pb-now"); ok.append(hit)

    ROADMAP.write_text(html, encoding="utf-8")
    print(f"roadmap updated: {date} | total ${total:,.0f} ({pct:.1f}%) | lev {lev:.2f} | buffer ${buf:,.0f} | anchors {sum(ok)}/{len(ok)}")


if __name__ == "__main__":
    main()
