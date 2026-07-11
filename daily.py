# -*- coding: utf-8 -*-
"""每日操作建议:从 calls_log.csv 提取"仍未了结"的操作,判定方向,供 app 计算实时拖延盈亏。

设计:daily.py 只做解析+去重+方向判定(纯逻辑、可测),
现价/拖延盈亏由 app.py 注入实时行情后计算,与 page_actions 的既有取数模式一致。
"""
import os
import csv

# 状态里出现这些 = 该操作仍需执行/仍在建议中 → 进"今日待执行"
_OPEN_HINTS = ("未执行", "建议中", "建议启动", "可启动", "启动首笔",
               "待缓冲", "待上市", "待观察", "剩余", "仍建议", "仍")
# 状态里出现这些 = 已了结/仅为事后兑现记录 → 不进
_CLOSED_HINTS = ("框架兑现", "兑现·首日未接", "首日未接")


def _is_open(status):
    s = status or ""
    if any(h in s for h in _CLOSED_HINTS):
        return False
    # "已执行50%(...剩余半仍建议平)" 这类半执行、仍有剩余 → 仍算未了结
    if s.startswith("已执行") and not any(k in s for k in ("剩余", "仍")):
        return False
    return any(h in s for h in _OPEN_HINTS)


def _side(call, ticker):
    """方向:'卖'(减/砍/平多/清)|'买'(建/加/买/启动)|'补空'(平空/平掉空单)。
    返回 (side, 动作emoji标签)。"""
    c = call or ""
    t = (ticker or "").upper()
    if "平空" in c or "补空" in c or (t == "BE" and ("平" in c)):
        return "补空", "🟩 平空(买回)"
    if any(k in c for k in ("买", "建", "加仓", "启动", "建仓", "接", "首笔")):
        return "买", "🟢 买/建"
    return "卖", "🔴 减/砍/平"


def _short_thesis(text, n=64):
    t = (text or "").replace("\n", " ").strip()
    return t if len(t) <= n else t[: n - 1] + "…"


def open_actions(calls_csv):
    """返回"仍未了结"的操作列表,每个 ticker 只保留最新一条。
    字段:date, ticker, call, price0(float|None), side, side_label, status, thesis, horizon。
    """
    if not os.path.exists(calls_csv):
        return []
    # 关键:先按 ticker 取"最新一条"(不论开/关),再判定该最新条是否仍未了结。
    # 这样"新写的『已了结/框架兑现』行"能正确压掉同标的的旧未执行行。
    latest = {}
    with open(calls_csv, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            tk = (r.get("ticker") or "").strip()
            if tk:
                latest[tk] = r  # 后写覆盖 → 每个 ticker 保留文件中最后(最新)一条
    out = []
    for tk, r in latest.items():
        if not _is_open(r.get("status", "")):
            continue
        side, label = _side(r.get("call", ""), tk)
        p0 = (r.get("price_at_call") or "").strip()
        try:
            p0v = float(p0) if p0 else None
        except ValueError:
            p0v = None
        out.append({
            "date": r.get("date", ""),
            "ticker": tk,
            "call": r.get("call", ""),
            "price0": p0v,
            "side": side,
            "side_label": label,
            "status": r.get("status", ""),
            "thesis": _short_thesis(r.get("thesis", "")),
            "horizon": r.get("horizon", ""),
        })
    # 卖/补空(该立刻了结的)排前,买/建其次;同组按日期倒序
    order = {"卖": 0, "补空": 1, "买": 2}
    out.sort(key=lambda x: (order.get(x["side"], 3), x["date"]), reverse=False)
    return out


def delay_pnl_pct(side, price0, cur):
    """拖延盈亏%:>0 = 拖到现在偶然占了便宜;<0 = 拖延吃了亏。
    卖侧:价涨=当时该卖没卖但现价更高→占便宜(cur-p0)/p0。
    买/补空侧:价跌=当时该动没动但现价更低→占便宜(p0-cur)/p0。
    (注:占便宜 ≠ 别做——逻辑没变就仍该执行,只是择时上运气而已。)
    """
    if price0 is None or cur is None or price0 == 0:
        return None
    if side == "卖":
        return (cur - price0) / price0 * 100.0
    return (price0 - cur) / price0 * 100.0
