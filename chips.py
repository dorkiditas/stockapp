# -*- coding: utf-8 -*-
"""
芯片战情室 —— AI芯片核心股的决策面板(不是报价表)。
两把尺子:PEG(前瞻PE÷明年增速,越低越便宜) + 超预期质量(过去4季beat次数×幅度)。
再叠 Max 的判定。数据实时:估值走 stockanalysis,前瞻/超预期走纳斯达克(forward.py)。
"""
import aimap
import forward

# 覆盖池:代码 → (中文名, 一句话卡位, Max判定标签)
UNIVERSE = [
    ("NVDA", "英伟达",   "GPU+整机柜系统,护城河从芯片上移到AI工厂", "🥈 便宜防御(误当贵)"),
    ("AVGO", "博通",     "定制硅+网络双年金,凸性:算力架构之争两边都赢", "🥇 核心·凸性"),
    ("AMD",  "超微",     "GPU第二供应商,但执行弱+同受定制硅侵蚀", "🔴 被挤的中间"),
    ("QCOM", "高通",     "手机盘6月季见底(待证)+数据中心期权(Meta已签)", "🟡 等7月底手机裁判"),
    ("INTC", "英特尔",   "18A/代工翻身+政策背书,已price;盈利near-zero", "🔴 政策彩票·非格局"),
    ("MRVL", "迈威尔",   "定制硅+1.6T DSP,同AVGO逻辑但更贵执行更弱", "🟡 不如AVGO"),
    ("MU",   "美光",     "存储超周期,前瞻~7x,take-or-pay地板", "🟢 头号·存储"),
    ("TSM",  "台积电",   "代工垄断+CoWoS售罄,全链质价比最佳", "🟢 压舱·代工"),
    ("ARM",  "Arm",     "IP授权,估值极高", "⚪ 贵·观察"),
]


def _peg(fpe, g):
    try:
        if fpe and g and g > 0:
            return round(fpe / g, 2)
    except Exception:
        pass
    return None


def build():
    """返回按PEG升序(越便宜越前)的芯片决策行。"""
    out = []
    for code, name, note, verdict in UNIVERSE:
        v = aimap._us_valuation(code) or {}
        f = forward.fetch(code) or {}
        fpe = v.get("fpe")
        g = f.get("明年EPS增速%")
        beat = f.get("近4季超预期", "")
        avg = f.get("平均超预期%")
        out.append({
            "标的": name, "代码": code,
            "前瞻PE": fpe, "明年增速%": g,
            "PEG": _peg(fpe, g),
            "超预期": beat, "均超%": avg,
            "PS": v.get("ps"),
            "卖方评级": v.get("rating"),
            "卡位": note, "Max判定": verdict,
        })
    # PEG有值的按PEG升序排前,无PEG(如INTC盈利近零)排后
    out.sort(key=lambda r: (r["PEG"] is None, r["PEG"] if r["PEG"] is not None else 999))
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for r in build():
        print(f"{r['标的']:<6} PEG={r['PEG']} 前瞻{r['前瞻PE']} +{r['明年增速%']}% "
              f"beat{r['超预期']}均{r['均超%']}% | {r['Max判定']}")
