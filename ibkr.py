# -*- coding: utf-8 -*-
"""
IBKR Flex Web Service —— 只读拉取持仓(含成本价)。不下单、不动钱。
流程(IBKR官方两步):
  1) SendRequest(token, queryId) -> ReferenceCode + Url
  2) GetStatement(token, ReferenceCode) -> XML 报表(轮询直到生成完)
配置存在 ib_config.json: {"token": "...", "query_id": "..."}。
令牌是只读的、会过期;放本地即可。
"""
import os
import time
import json
import xml.etree.ElementTree as ET
import requests
import pandas as pd

BASE = "https://ndcdyn.interactivebrokers.com/AccountManagement/FlexWebService"
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ib_config.json")
_S = requests.Session()
_S.headers.update({"User-Agent": "stockapp-flex/1.0"})


def load_config():
    if os.path.exists(CONFIG):
        try:
            c = json.load(open(CONFIG, encoding="utf-8"))
            if c.get("token") and c.get("query_id"):
                return c
        except Exception:
            pass
    return None


def save_config(token, query_id):
    json.dump({"token": token.strip(), "query_id": str(query_id).strip()},
              open(CONFIG, "w", encoding="utf-8"))


def fetch_positions(token, query_id, timeout=90):
    """跑一次 Flex 查询,返回持仓 DataFrame(ticker, shares, cost, currency, 类别)。"""
    r = _S.get(f"{BASE}/SendRequest",
               params={"t": token.strip(), "q": str(query_id).strip(), "v": 3}, timeout=25)
    root = ET.fromstring(r.text)
    if (root.findtext("Status") or "").strip() != "Success":
        raise RuntimeError("SendRequest失败: " + (root.findtext("ErrorMessage") or r.text[:200]))
    ref = root.findtext("ReferenceCode")
    url = root.findtext("Url") or f"{BASE}/GetStatement"

    deadline = time.time() + timeout
    while time.time() < deadline:
        s = _S.get(url, params={"t": token.strip(), "q": ref, "v": 3}, timeout=25)
        txt = s.text
        if "<FlexQueryResponse" in txt:
            return _parse(txt)
        # 报表还在生成中 -> 等
        if "in progress" in txt.lower() or "Warn" in txt[:300]:
            time.sleep(4)
            continue
        raise RuntimeError("GetStatement失败: " + txt[:200])
    raise TimeoutError("Flex 报表生成超时")


def _parse(xml_text):
    root = ET.fromstring(xml_text)
    rows = []
    for op in root.iter("OpenPosition"):
        a = op.attrib
        # 优先用每股成本 costBasisPrice;没有就用 costBasisMoney/position 反算
        cost = a.get("costBasisPrice")
        pos = float(a.get("position") or 0)
        if (not cost or float(cost) == 0) and a.get("costBasisMoney") and pos:
            try:
                cost = abs(float(a["costBasisMoney"]) / pos)
            except Exception:
                cost = None
        rows.append({
            "ticker": a.get("symbol"),
            "shares": pos,
            "cost": float(cost) if cost else None,
            "currency": a.get("currency"),
            "类别": a.get("assetCategory"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        # 同标的多条(多账户/多批)合并:股数相加,成本按金额加权
        df = df.groupby(["ticker", "currency", "类别"], as_index=False).agg(
            shares=("shares", "sum"), cost=("cost", "mean"))
    return df


def sync_to_holdings(token, query_id, out_csv):
    """拉持仓并写入 holdings.csv(只保留股票类,代码原样)。返回写入的 DataFrame。"""
    df = fetch_positions(token, query_id)
    if df.empty:
        return df
    stocks = df[df["类别"].isin(["STK", "ETF", None])] if "类别" in df else df
    keep = stocks[["ticker", "shares", "cost"]].copy()
    keep = keep[keep["shares"] != 0]
    keep.to_csv(out_csv, index=False, encoding="utf-8-sig")
    return keep


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    # 解析自测(用一段样例XML,不需要真令牌)
    sample = """<FlexQueryResponse><FlexStatements><FlexStatement>
    <OpenPositions>
    <OpenPosition symbol="AVGO" position="112" costBasisPrice="180.5" currency="USD" assetCategory="STK"/>
    <OpenPosition symbol="USO" position="-50" costBasisPrice="76.2" currency="USD" assetCategory="ETF"/>
    </OpenPositions></FlexStatement></FlexStatements></FlexQueryResponse>"""
    print(_parse(sample).to_string(index=False))
    print("config:", load_config())
