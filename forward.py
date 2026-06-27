# -*- coding: utf-8 -*-
"""
前瞻信号模块(美股)—— 数据源:纳斯达克 analyst/earnings 端点 + stockanalysis,均稳定、云端可用。
给出四类前瞻:
  业绩前瞻 : 明年共识EPS、EPS预期增速、前瞻PE
  预期修正 : 近4周分析师上调/下调次数(净修正方向)—— 股价领先信号
  催化日历 : 下次财报(近似,按下一财季)
  预期差   : 过去4季超预期次数/平均超预期幅度
仅美股(纳斯达克覆盖);A股/外股返回空。
"""
import re
import requests
from concurrent.futures import ThreadPoolExecutor

_S = requests.Session()
_S.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                   "Accept": "application/json"})


def _get(url):
    try:
        return _S.get(url, timeout=12).json().get("data") or {}
    except Exception:
        return {}


def _f(x):
    try:
        return float(str(x).replace(",", "").replace("$", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


def fetch(ticker):
    """美股前瞻信号。返回 dict;非美股或拉取失败返回 {}。"""
    t = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z.]{1,6}", t) or "." in t:
        return {}

    out = {"代码": t}
    # 1) 年度预测 + 修正
    ef = _get(f"https://api.nasdaq.com/api/analyst/{t}/earnings-forecast")
    yr = (ef.get("yearlyForecast") or {}).get("rows") or []
    if len(yr) >= 2:
        this_eps = _f(yr[0].get("consensusEPSForecast"))
        next_eps = _f(yr[1].get("consensusEPSForecast"))
        out["本年EPS"] = this_eps
        out["明年EPS"] = next_eps
        if this_eps and next_eps and this_eps != 0:
            out["明年EPS增速%"] = round((next_eps / abs(this_eps) - 1) * 100)
        up = yr[1].get("up") or 0
        down = yr[1].get("down") or 0
        out["上调"] = up
        out["下调"] = down
        out["净修正"] = up - down
    # 2) 超预期历史
    su = _get(f"https://api.nasdaq.com/api/company/{t}/earnings-surprise")
    rows = (su.get("earningsSurpriseTable") or {}).get("rows") or []
    beats = tot = 0
    pcts = []
    for r in rows[:4]:
        p = _f(r.get("percentageSurprise"))
        if p is not None:
            tot += 1
            pcts.append(p)
            if p > 0:
                beats += 1
    if tot:
        out["近4季超预期"] = f"{beats}/{tot}"
        out["平均超预期%"] = round(sum(pcts) / len(pcts), 1)
    # 3) 下次财报(近似:下一财季末)
    qr = (ef.get("quarterlyForecast") or {}).get("rows") or []
    if qr:
        out["下一财季"] = qr[0].get("fiscalEnd")
    return out


def signal(row):
    """综合前瞻标签。"""
    g = row.get("明年EPS增速%")
    net = row.get("净修正")
    beat = row.get("近4季超预期", "")
    bn = int(beat.split("/")[0]) if "/" in beat else 0
    score = 0
    if g is not None and g >= 20:
        score += 1
    if g is not None and g < 0:
        score -= 1
    if net is not None and net >= 3:
        score += 1
    if net is not None and net <= -2:
        score -= 1
    if bn >= 3:
        score += 1
    if score >= 2:
        return "🔥 强前瞻"
    if score == 1:
        return "👍 偏正"
    if score <= -1:
        return "⚠️ 转弱"
    return "⚪ 一般"


def fetch_many(tickers):
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(lambda t: (t, fetch(t)), tickers))
    return {t: r for t, r in res}


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for t in ["AVGO", "NVDA", "CRDO", "QCOM", "MU", "PLTR"]:
        r = fetch(t)
        if r:
            print(f"{t:<6} {signal(r):<8} 明年增速{r.get('明年EPS增速%')}% "
                  f"修正(+{r.get('上调')}/-{r.get('下调')}) 超预期{r.get('近4季超预期')} "
                  f"均{r.get('平均超预期%')}%")
        else:
            print(t, "无数据")
