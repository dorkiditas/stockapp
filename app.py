# -*- coding: utf-8 -*-
"""
选股工作台 v3  —  Streamlit（极简版）
三页：我的持仓 / 选股 / 查股票
数据：腾讯 qt.gtimg.cn（个股，A股/港股/美股）+ 新浪全A股 + 纳斯达克全美股
运行：双击 run.bat
"""
import os
import datetime as dt
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import tencent
import market
import aimap
import catalyst
import sectors
import ibkr
import forward

st.set_page_config(page_title="选股工作台", page_icon="📈", layout="wide")


def _check_password():
    """云端用:设了 APP_PASSWORD 密码才放行;本地无密码直接进。"""
    try:
        pw = st.secrets.get("APP_PASSWORD")
    except Exception:
        pw = None
    if not pw:
        return True
    if st.session_state.get("_authed"):
        return True
    st.title("📈 选股工作台")
    with st.form("login"):
        x = st.text_input("密码", type="password")
        if st.form_submit_button("进入"):
            if x == pw:
                st.session_state["_authed"] = True
                st.rerun()
            else:
                st.error("密码不对")
    return False


if not _check_password():
    st.stop()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_CSV = os.path.join(BASE_DIR, "holdings.csv")


@st.cache_data(ttl=55, show_spinner=False)
def quote(codes_tuple):
    return tencent.quote(list(codes_tuple))


@st.cache_data(ttl=600, show_spinner=False)
def a_universe():
    return market.a_share_universe()


@st.cache_data(ttl=1800, show_spinner=False)
def ai_map():
    return aimap.build()


@st.cache_data(ttl=900, show_spinner=False)
def catalysts(rows_tuple):
    return catalyst.classify_many(list(rows_tuple))


@st.cache_data(ttl=1800, show_spinner=False)
def forward_many(tickers_tuple):
    return forward.fetch_many(list(tickers_tuple))


@st.cache_data(ttl=900, show_spinner=False)
def sector_data(name):
    return sectors.build_one(name)


@st.cache_data(ttl=900, show_spinner=False)
def all_sector_data():
    return sectors.build_all()


# 我的操作判断(基于研报+实时数据+AI产业链规律,2026-06)。数字每天刷新,call是我的判断。
MY_CALLS = {
    # 持仓
    "AVGO": ("🟢 留/逢跌加", "全球仅5家真实LLM客户=护城河;+72%增速、分析师净+11上修(你全仓最强);前瞻PE26可接受"),
    "CRDO": ("🟡 减一部分", "107倍PE、比DCF高59%,上修只剩+1;光通信是真上行但CRDO已price完美→把钱换CIEN"),
    "CBRS": ("🟢 留", "Cerebras·AI算力核心线;高波动,维持小仓"),
    "QCOM": ("🔴 砍/大减", "明年0增长、Neutral,400股占太多资本;唯一指望6/24投资者日(AI200/HUMAIN)→腾出钱买MU"),
    "GEV":  ("🟢 留(不加)", "AI电力,需求2030+220%顺风;但前瞻PE60开始贵,留着别追"),
    "PLTR": ("🟡 留小仓", "AI软件,UBS Buy$200但PS59太贵;小仓可留,别加"),
    "SIEGY": ("⚪ 中性", "西门子·工业,非AI核心;可作压舱不必加"),
    "EWZ":  ("🔴 清理", "巴西ETF,与你AI edge无关,占资本分散注意力"),
    "USO":  ("🔴 平空", "油空·宏观噪音,跟你edge无关"),
    "BE":   ("🔴 平空", "做空AI电力,与你GEV多头自相矛盾,正逆势流血(AI电力2030+220%)"),
    "DXYZ": ("🟡 减", "SpaceX代理,溢价波动巨大,题材小仓即可"),
    "NASA": ("🟡 留小仓", "太空ETF,题材配置,别加"),
    # A股持仓(也几乎全是AI产业链)
    "600703": ("🟢 留(已+41%)", "三安光电·化合物半导体平台,InP光芯片已量产;仍亏损/估值高,别加,可分批止盈"),
    "600522": ("🟢 留", "中天科技·AI光纤需求顺风(长飞同逻辑)+海缆/电网;估值相对不贵"),
    "002475": ("🟢 留", "立讯精密·苹果链转AI服务器连接/电源/光模块,卡位好,估值合理"),
    "600584": ("🟢 留/可加", "长电科技·封测龙头,AI先进封装(CoWoS国产链);AI芯片材料里估值最讲得通的一簇(盈利PS3.5)"),
    "002428": ("🟡 减/谨慎", "云南锗业·纯正InP/锗稀缺,但PE天价、估值脱离基本面,题材属性强;反弹减"),
    "000725": ("⚪ 周期配置", "京东方A·面板周期股,与AI主线关系弱;面板涨价周期可博,非focus核心"),
}
# 买入候选(不在持仓,我建议建仓)
MY_BUYS = {
    "MU":   ("🟢 买入(头号)", "🇺🇸存储:前瞻PE11+明年96%增速+净+7上修+NAND紧到CY27+被低配,全链最佳风险收益"),
    "TSM":  ("🟢 买入", "🇹🇼台积电ADR·全AI链最佳质价比,前瞻PE~20、代工垄断、+41%目标空间;你IBKR直接买ADR最省事"),
    "CIEN": ("🟢 买入", "🇺🇸光互连里没人挤的:+57%增速、净+7上修、+40%到目标价、未贴高点;接CRDO的钱"),
    "000660.KS": ("🟢 买入", "🇰🇷SK海力士·HBM全球龙头,前瞻PE仅~7;存储缺口首选"),
    "005930.KS": ("🟢 买入", "🇰🇷三星·前瞻PE~6、外资持股2015来最低(被低配),内存+代工+玻璃基板"),
    "2345.TW": ("🟡 关注", "🇹🇼智邦Accton·白盒交换,后端交换+100%YoY,低调网络赢家"),
    "SNDK": ("🟡 关注", "🇺🇸闪迪·NAND同逻辑,Citi目标$2500;8月投资者日催化"),
}


def _faction(row):
    """老登/小登 派系(估值主导,不看动量):
    🧓老登=便宜成熟盈利(前瞻PE≤20);🐤小登=贵/亏损/高成长(前瞻PE≥45或亏损或无盈利且高PS)。"""
    pe, fpe, ps = row.get("PE"), row.get("前瞻PE"), row.get("PS")
    v = fpe if (fpe and fpe > 0) else pe
    # 小登:亏损 / 估值贵 / 无盈利但高PS
    if (pe is not None and pe < 0) or (v is not None and v >= 45) \
       or (v is None and ps is not None and ps >= 15):
        return "🐤小登"
    # 老登:前瞻/PE 便宜(≤20)
    if v is not None and 0 < v <= 20:
        return "🧓老登"
    return "—中间"


def _passes(row, cheap, uncrowded, has_cat, fac):
    """多条件 AND 过滤。"""
    if cheap:
        fpe, pe = row.get("前瞻PE"), row.get("PE")
        v = fpe if (fpe and fpe > 0) else pe
        if not (v is not None and 0 < v <= 30):
            return False
    if uncrowded:
        up, pos = row.get("隐含涨幅%"), row.get("52周位置%")
        if not (up is not None and up >= 0 and pos is not None and pos <= 85):
            return False
    if has_cat:
        if not str(row.get("近期催化", "")).startswith("🟢"):
            return False
    if fac and fac != "全部":
        if _faction(row) != fac:
            return False
    return True


def parse_codes(raw):
    return [x for x in raw.replace("\n", ",").replace("，", ",").split(",") if x.strip()]


# 陈立武押注的 5 大半导体新材料/封装方向 → 标的映射（含与持仓关联）
THEMES = {
    "① GaN 氮化镓（功率器件/数据中心电源）": {
        "600703": "三安光电·化合物半导体平台", "600460": "士兰微·IDM功率龙头",
        "688396": "华润微·功率IDM", "300623": "捷捷微电·功率器件",
        "605358": "立昂微·硅片/功率", "02577.HK": "英诺赛科·GaN龙头(胜英飞凌专利战)",
        "NVTS": "Navitas·GaN快充", "WOLF": "Wolfspeed·SiC/GaN(亏损)",
    },
    "② SiC 碳化硅（衬底+器件/散热）": {
        "688234": "天岳先进·8英寸衬底龙头(亏损)", "603260": "合盛硅业·工业硅全产业链",
        "COHR": "Coherent·光通信+SiC", "ON": "安森美·SiC器件",
        "WOLF": "Wolfspeed·SiC衬底全球龙头(亏损)",
    },
    "③ InP 磷化铟 ★你的AVGO/CRDO同主线": {
        "002428": "云南锗业·纯正InP衬底(PE极高)", "002975": "博杰股份·参股鼎泰芯源(InP衬底)",
        "600703": "三安光电·已量产6吋InP光芯片", "688498": "源杰科技·光芯片龙头(PS238!)",
        "688048": "长光华芯·高功率激光芯片(PE2043!)", "600105": "永鼎股份·光通信",
        "COHR": "Coherent·英伟达20亿投它扩InP产能", "LITE": "Lumentum·光收发器",
        "AXTI": "AXT·InP衬底(弹性大已大涨)",
    },
    "④ 人造金刚石（终极散热,热导≈铜5倍）": {
        "300179": "四方达·半导体级金刚石量产", "301071": "力量钻石·培育钻/工业金刚石",
        "600172": "黄河旋风·超硬材料(亏损)",
    },
    "⑤ 先进封装（CoWoS/玻璃基板,陈立武点名）": {
        "600584": "长电科技·封测龙头(盈利,PS仅3.8)", "002156": "通富微电·绑定AMD(盈利,PS3.5)",
        "002185": "华天科技·封测(盈利,PS3.5)", "601636": "旗滨集团·玻璃基板",
        "300088": "长信科技·玻璃基板", "603773": "沃格光电·玻璃基板(亏损)",
        "688079": "美迪凯·光学/玻璃基板(亏损)",
    },
}


# ============================================================================
# 页面 1：我的持仓（打开即自动显示，无需任何操作）
# ============================================================================
def _ib_section():
    """IBKR Flex 只读同步(可选)。"""
    cfg = ibkr.load_config()
    with st.expander("🔗 连接 IBKR(只读自动同步持仓 · 可选)", expanded=not cfg):
        if cfg:
            st.success("✅ 已连接 IBKR。点下面按钮把账户真实持仓(含成本)同步进来。")
            if st.button("🔄 从 IB 同步持仓"):
                try:
                    with st.spinner("从 IBKR 拉取持仓…(报表生成可能要十几秒)"):
                        df = ibkr.sync_to_holdings(cfg["token"], cfg["query_id"], HOLDINGS_CSV)
                    st.cache_data.clear()
                    st.success(f"同步成功,共 {len(df)} 只。")
                    st.rerun()
                except Exception as e:
                    st.error(f"同步失败:{e}")
            if st.button("断开(删除令牌)"):
                try:
                    os.remove(ibkr.CONFIG)
                except OSError:
                    pass
                st.rerun()
        else:
            st.caption("在 IBKR 网页生成只读的 Flex 令牌后填到这里(步骤问我)。只读,不能下单/转账。")
            tok = st.text_input("Flex Token", type="password")
            qid = st.text_input("Query ID")
            if st.button("保存并同步") and tok and qid:
                try:
                    with st.spinner("验证并拉取持仓…"):
                        df = ibkr.sync_to_holdings(tok, qid, HOLDINGS_CSV)
                    ibkr.save_config(tok, qid)
                    st.cache_data.clear()
                    st.success(f"连接成功,同步 {len(df)} 只持仓。")
                    st.rerun()
                except Exception as e:
                    st.error(f"失败:{e}(检查 token/Query ID,且 Query 里要包含 Open Positions)")


def page_portfolio():
    st.subheader("📊 我的持仓")
    # 每60秒自动重跑本页（自动拉新价，你什么都不用点）
    st_autorefresh(interval=60000, key="pf_auto")
    _ib_section()
    if not os.path.exists(HOLDINGS_CSV):
        st.info("还没有持仓表。去『查股票』页可以随时看行情。")
        return

    h = pd.read_csv(HOLDINGS_CSV, dtype={"ticker": str})
    h["symbol"] = h["ticker"].apply(tencent.to_symbol)
    with st.spinner("正在拉取最新价…"):
        q = quote(tuple(h["ticker"].tolist()))
    # 按腾讯代码精确匹配（缺数据的票留空，绝不错位）
    m = h.merge(q[["code", "name", "market", "price", "prev_close", "chg_pct", "time"]],
                left_on="symbol", right_on="code", how="left")

    # 行情时间戳 + 市场状态(让你知道数据新不新、为什么不动)
    times = [t for t in q.get("time", pd.Series(dtype=str)).tolist() if t]
    us_t = next((t for t, mk in zip(q["time"], q["market"]) if mk == "美股" and t), "")
    a_t = next((t for t, mk in zip(q["time"], q["market"]) if mk == "A股" and t), "")
    parts = []
    if us_t:
        parts.append(f"美股 {us_t}")
    if a_t:
        parts.append(f"A股 {a_t}")
    if parts:
        st.info("🕒 行情时间:" + " | ".join(parts) +
                " — 若与现在差很多,是该市场已**收盘**,显示最后成交价(收盘后不变属正常)。")

    m["市值"] = (m["price"] * m["shares"]).round(0)
    m["今日盈亏"] = ((m["price"] - m["prev_close"]) * m["shares"]).round(0)
    # 成本可选：有就算总盈亏
    has_cost = m["cost"].notna()
    m["盈亏"] = None
    m.loc[has_cost, "盈亏"] = ((m["price"] - m["cost"]) * m["shares"]).round(0)

    m["盈亏%"] = ((m["price"] / m["cost"] - 1) * 100).round(1)
    # 按币种分开统计(美元/人民币不能混加)
    cur = {"美股": "$", "A股": "¥", "港股": "HK$"}
    groups = [g for g in ["美股", "A股", "港股"] if (m["market"] == g).any()]
    cols = st.columns(len(groups) + 1)
    for i, g in enumerate(groups):
        sub = m[m["market"] == g]
        sym = cur.get(g, "")
        mv, pl = sub["市值"].sum(), sub["今日盈亏"].sum()
        cols[i].metric(f"{g}市值", f"{sym}{mv:,.0f}", f"今日 {sym}{pl:,.0f}")
    cols[-1].metric("持仓数", f"{(m['shares'] != 0).sum()} 只")

    tcol, bcol = st.columns([4, 1])
    tcol.caption(f"🟢 自动刷新中 · 上次更新 {dt.datetime.now().strftime('%H:%M:%S')}（每60秒自动拉新价）")
    if bcol.button("🔄 立即刷新"):
        st.cache_data.clear()
        st.rerun()

    # 展示表：红涨绿跌用箭头标注
    view = m.copy()
    view["方向"] = view["shares"].apply(lambda s: "🔻空" if s < 0 else "持有")
    show = view[["name", "market", "shares", "price", "chg_pct", "市值", "今日盈亏", "盈亏", "盈亏%"]].rename(
        columns={"name": "名称", "market": "市场", "shares": "股数",
                 "price": "现价", "chg_pct": "今日%"})
    show = show.sort_values("市值", ascending=False)
    st.dataframe(show, use_container_width=True, height=520,
                 column_config={"今日%": st.column_config.NumberColumn(format="%.2f%%"),
                                "盈亏%": st.column_config.NumberColumn(format="%.1f%%")})
    st.caption("💡 想看买入以来的总盈亏？在 stockapp/holdings.csv 的 cost 列填上成本价即可。"
               " USO 暂无数据源（油气ETF），显示为空。")


# ============================================================================
# 页面 2：选股（全 A股，点预设即可）
# ============================================================================
def page_pick():
    st.subheader("🌐 选股 · 全 A股扫描")
    st.write("点一个下面的思路，自动从全部 5500 只 A股里挑：")
    preset = st.radio("选股思路", [
        "💎 便宜的好公司（低PE低PB大市值）",
        "📉 破净股（股价低于净资产）",
        "🚀 今日强势（涨幅靠前）",
        "🐂 低估值小盘（市值50-200亿）",
    ], index=0)

    if st.button("开始选股", type="primary"):
        with st.spinner("扫描全市场（首次约15秒）…"):
            df = a_universe()
        if df.empty:
            st.error("数据拉取失败，稍后再试。")
            return
        f = df[df["pe"].notna()].copy()
        if preset.startswith("💎"):
            f = f[(f["pe"] > 0) & (f["pe"] <= 15) & (f["pb"] <= 2) & (f["mktcap_yi"] >= 500)]
            f = f.sort_values("mktcap_yi", ascending=False)
        elif preset.startswith("📉"):
            f = f[(f["pb"] > 0) & (f["pb"] < 1)].sort_values("pb")
        elif preset.startswith("🚀"):
            f = f.sort_values("chg_pct", ascending=False)
        else:
            f = f[(f["mktcap_yi"] >= 50) & (f["mktcap_yi"] <= 200) & (f["pe"] > 0)
                  & (f["pe"] <= 30)].sort_values("pe")
        st.success(f"挑出 {len(f)} 只，按思路排好序（显示前 50）：")
        st.dataframe(_fmt(f.head(50)), use_container_width=True, height=480)
        st.download_button("⬇️ 导出名单 Excel(CSV)",
                           f.to_csv(index=False).encode("utf-8-sig"),
                           "选股结果.csv", "text/csv")


# ============================================================================
# 页面 3：查股票（任意市场，随手查）
# ============================================================================
def page_lookup():
    st.subheader("🔍 查股票")
    st.write("输入代码看实时行情。A股填6位(000338)，港股加.HK(0700.HK)，美股填字母(AVGO)。")
    raw = st.text_input("代码（多个用逗号隔开）", "AVGO, NVDA, 000338, 0700.HK")
    if raw.strip():
        df = quote(tuple(parse_codes(raw)))
        if df.empty:
            st.warning("没查到，检查代码格式。")
        else:
            st.dataframe(_fmt(df, with_market=True), use_container_width=True,
                         column_config={"今日%": st.column_config.NumberColumn(format="%.2f%%")})


def page_themes():
    st.subheader("🔬 AI芯片材料（陈立武押注的5条线）")
    st.caption("英特尔CEO陈立武点名的后摩尔时代5大方向 → A股/美股标的实时映射。"
               "③InP线是你 AVGO/CRDO 的同主线。⚠️多数标的估值极高或亏损,属主题驱动。")
    st_autorefresh(interval=60000, key="th_auto")

    all_codes = list({c for m in THEMES.values() for c in m})
    with st.spinner("拉取全部标的实时行情…"):
        q = quote(tuple(all_codes))
    look = {r["code"]: r for _, r in q.iterrows()}

    for theme, mapping in THEMES.items():
        star = "★" in theme
        st.markdown(f"#### {theme}")
        rows = []
        for code, note in mapping.items():
            r = look.get(tencent.to_symbol(code))
            if r is None or r.get("price") is None:
                rows.append({"名称": note.split("·")[0], "代码": code, "现价": None,
                             "今日%": None, "PE": None, "总市值(亿)": None, "看点": note.split("·", 1)[-1]})
            else:
                rows.append({"名称": r["name"], "代码": code, "现价": r["price"],
                             "今日%": r["chg_pct"], "PE": r.get("pe"),
                             "总市值(亿)": r.get("mktcap_yi"), "看点": note.split("·", 1)[-1]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={"今日%": st.column_config.NumberColumn(format="%.1f%%")})
    st.caption("💡 我的判断:能直接买的延伸是美股 COHR(英伟达背书的InP);A股唯一估值讲得通的是"
               "封测三巨头 长电/通富/华天(盈利、PS仅3.5)。其余源杰/长光华芯等是资金面不是基本面。")


def page_actions():
    st.subheader("🎯 我的操作建议")
    st.caption("我的判断(基于研报+实时数据+AI产业链规律)+ 每天最新信号。"
               "核心打法:从挤爆的算力核心,换到便宜+预期上修+被低配的AI邻接(存储/CIEN)。")
    st_autorefresh(interval=120000, key="act_auto")

    # 收集持仓代码 + 候选
    hold = []
    if os.path.exists(HOLDINGS_CSV):
        hold = pd.read_csv(HOLDINGS_CSV, dtype={"ticker": str})["ticker"].tolist()
    buys = list(MY_BUYS.keys())
    allc = list(dict.fromkeys(hold + buys))
    with st.spinner("拉取最新价+前瞻信号…"):
        q = quote(tuple(allc))
        us = [c for c in allc if str(c).isalpha()]
        fwd = forward_many(tuple(us)) if us else {}
    qmap = {r["code"]: r for _, r in q.iterrows()}

    def build(code, action, reason):
        r = qmap.get(tencent.to_symbol(code), {})
        f = fwd.get(str(code).upper(), {}) if str(code).isalpha() else {}
        return {"操作": action, "标的": r.get("name") or code, "代码": code,
                "现价": r.get("price"), "今日%": r.get("chg_pct"),
                "明年EPS增速%": f.get("明年EPS增速%"), "净修正": f.get("净修正"),
                "理由": reason}

    st.markdown("#### 📌 持仓 — 加 / 留 / 减 / 砍 / 平")
    rows = [build(c, *MY_CALLS.get(str(c).upper(), ("⚪ —", "未覆盖")))
            for c in hold]
    # 操作排序:加/留在前,砍/平在后看着顺
    rank = {"🟢": 0, "⚪": 1, "🟡": 2, "🔴": 3}
    rows.sort(key=lambda x: rank.get(x["操作"][:1], 5))
    _action_table(rows)

    st.markdown("#### 🟢 买入候选(不在你持仓,我建议建仓)")
    brows = [build(c, *MY_BUYS[c]) for c in buys]
    _action_table(brows)

    st.info("**最该立刻做的两件:① 建 MU 仓(存储,全链最佳风险收益) ② 平掉 BE 空单(在逆势流血)。** "
            "其次:CRDO减一部分换CIEN、QCOM大减腾钱。")
    st.caption("⚠️ 这是我的判断,不是保证。存储是周期股,赌AI拉长周期到2027不见顶——逻辑有数据支撑,"
               "但超大厂capex急刹车则回撤快,故『加仓』非all-in。前瞻数据(增速/上修)仅美股有。")


def _action_table(rows):
    df = pd.DataFrame(rows)[["操作", "标的", "代码", "现价", "今日%",
                             "明年EPS增速%", "净修正", "理由"]]
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={
                     "今日%": st.column_config.NumberColumn(format="%.1f%%"),
                     "明年EPS增速%": st.column_config.NumberColumn(format="%d%%"),
                     "净修正": st.column_config.NumberColumn(help="分析师近4周净上调EPS家数,正=在上修"),
                     "理由": st.column_config.TextColumn(width="large"),
                 })


def page_research():
    st.subheader("📰 研报情报")
    st.caption("从你 持仓 文件夹里的卖方研报(GS/UBS/MS/Citi)提取的目标价+核心逻辑+前瞻变化。"
               "这是免费API给不了的——卖方的『为什么』和最新预期调整。")
    path = os.path.join(BASE_DIR, "research_intel.json")
    if not os.path.exists(path):
        st.info("还没有研报情报。把研报PDF放进 持仓 文件夹,让我重新提取。")
        return
    import json
    items = json.load(open(path, encoding="utf-8"))

    def age_days(d):
        try:
            return (dt.date.today() - dt.date.fromisoformat(d)).days
        except Exception:
            return 9999

    fresh_only = st.checkbox("只看近3个月(过滤过时研报)", value=True)
    groups = {"持仓": "📌 与你持仓相关", "AI核心": "🤖 AI核心", "主题": "🌐 主题/行业"}
    for key, title in groups.items():
        sub = [x for x in items if x.get("relevance") == key]
        sub.sort(key=lambda x: x.get("date", ""), reverse=True)  # 新的在前
        if fresh_only:
            sub = [x for x in sub if age_days(x.get("date", "")) <= 95]
        if not sub:
            continue
        st.markdown(f"#### {title}")
        rows = []
        for x in sub:
            a = age_days(x.get("date", ""))
            rows.append({
                "时效": "✅" if a <= 95 else "⏳过时", "标的": " ".join(x.get("tickers", [])) or "—",
                "券商": x.get("source", ""), "日期": x.get("date", ""),
                "评级": x.get("rating", ""), "目标价": x.get("target", ""),
                "核心逻辑": " · ".join(x.get("thesis", [])),
                "前瞻/预期变化": x.get("forward", ""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={
                         "核心逻辑": st.column_config.TextColumn(width="large"),
                         "前瞻/预期变化": st.column_config.TextColumn(width="medium"),
                     })
    st.caption("⚠️ 中文研报(GPU/ASIC、国产算力、存储动态、长飞光纤等约24份)是扫描图片版,"
               "需OCR才能提取——还没做。要的话告诉我,我加OCR。")


def page_forward():
    st.subheader("🔮 前瞻信号")
    st.caption("驱动股价的是『接下来会怎样』。这里看四类前瞻(仅美股):"
               "**明年EPS增速** · **分析师近期上调/下调**(领先信号) · **过去4季超预期** · 下一财季。"
               "数据:纳斯达克分析师预测。")
    # 默认:你持仓里的美股 + 几个核心AI票
    hold_us = []
    if os.path.exists(HOLDINGS_CSV):
        h = pd.read_csv(HOLDINGS_CSV, dtype={"ticker": str})
        hold_us = [t for t in h["ticker"].tolist() if str(t).isalpha()]
    default = ", ".join(dict.fromkeys(hold_us + ["NVDA", "AVGO", "MU", "CRDO", "QCOM", "PLTR"]))
    raw = st.text_area("美股代码(默认=你的持仓+核心AI)", default, height=68)
    tickers = [x.strip().upper() for x in raw.replace("\n", ",").split(",") if x.strip()]

    if st.button("拉取前瞻", type="primary") or tickers:
        with st.spinner("拉取分析师预测…"):
            data = forward_many(tuple(tickers))
        rows = []
        for t in tickers:
            r = data.get(t) or {}
            if not r or r.get("明年EPS增速%") is None:
                continue
            rows.append({
                "代码": t, "前瞻信号": forward.signal(r),
                "明年EPS增速%": r.get("明年EPS增速%"),
                "近4周上调": r.get("上调"), "近4周下调": r.get("下调"),
                "净修正": r.get("净修正"),
                "近4季超预期": r.get("近4季超预期"), "平均超预期%": r.get("平均超预期%"),
                "下一财季": r.get("下一财季"),
            })
        if not rows:
            st.warning("没拉到(可能是非美股/小票,纳斯达克无覆盖)。")
            return
        df = pd.DataFrame(rows)
        # 按信号强度+增速排序
        order = {"🔥 强前瞻": 0, "👍 偏正": 1, "⚪ 一般": 2, "⚠️ 转弱": 3}
        df["_o"] = df["前瞻信号"].map(order).fillna(2)
        df = df.sort_values(["_o", "明年EPS增速%"], ascending=[True, False]).drop(columns="_o")
        st.dataframe(df, use_container_width=True, hide_index=True, height=460,
                     column_config={
                         "明年EPS增速%": st.column_config.NumberColumn(format="%d%%",
                             help="明年共识EPS相对今年的增速"),
                         "净修正": st.column_config.NumberColumn(
                             help="近4周上调家数-下调家数,正=分析师在上修(领先信号)"),
                         "平均超预期%": st.column_config.NumberColumn(format="%.1f%%"),
                     })
        st.caption("🔥强前瞻=高增速+被上修+常超预期(三者占多);⚠️转弱=零/负增速或被下修。"
                   "**净修正为正**是最值得盯的领先信号——分析师在悄悄上调,股价往往跟。")


def page_sectors():
    st.subheader("🧭 按赛道选股")
    st.caption("把AI产业链拆成12个细分赛道。选赛道(或全部),再勾选条件,可同时按多个标准筛。")
    names = ["🌍 全部赛道"] + list(sectors.SECTORS.keys())
    labels = {n: (n if n.startswith("🌍") else f"{sectors.SECTORS[n]['verdict'][:2]} {n}")
              for n in names}
    pick = st.selectbox("选赛道", names, format_func=lambda n: labels[n])

    # 多条件勾选(同时满足 = AND)。研报学到的赢家规律:卡位+预期上修+不拥挤
    st.markdown("**同时满足这些条件(可多选):**")
    c1, c2, c3, c4, c5 = st.columns(5)
    f_cheap = c1.checkbox("💰 便宜", help="前瞻PE(无则PE)在0~30之间,即盈利且不贵")
    f_uncrowded = c2.checkbox("🧊 不拥挤", help="股价未超卖方目标(隐含涨幅≥0)且52周位置≤85%")
    f_cat = c3.checkbox("🚀 有催化", help="近14天新闻判为🟢")
    f_rev = c4.checkbox("📈 预期上修", help="分析师近4周净上调EPS预期(赢家共同信号,仅美股有数据)")
    f_fac = c5.selectbox("派系", ["全部", "🧓老登", "🐤小登", "—中间"],
                         help="🧓老登=便宜成熟盈利;🐤小登=贵/亏损/高成长")

    is_all = pick.startswith("🌍")
    if is_all:
        with st.spinner("拉取全部赛道(首次约60-90秒,之后缓存)…"):
            rows = all_sector_data()
    else:
        verdict = sectors.SECTORS[pick]["verdict"]
        (st.success if verdict.startswith("🟢") else st.error if verdict.startswith("🔴")
         else st.warning)(f"**赛道判定:** {verdict}")
        with st.spinner(f"拉取「{pick}」…"):
            _, rows = sector_data(pick)

    # 派系标签
    for r in rows:
        r["派系"] = _faction(r)
    # 先按非催化条件过滤(便宜/不拥挤/派系)
    sub = [r for r in rows if _passes(r, f_cheap, f_uncrowded, False, f_fac)]
    # 催化:全部赛道模式下默认没拉新闻,勾了才对子集按需算(省时)
    if f_cat:
        if is_all and any(r.get("近期催化", "—") == "—" for r in sub):
            with st.spinner(f"对 {len(sub)} 只候选扫近期新闻催化…"):
                sectors.add_catalyst(sub)
        sub = [r for r in sub if str(r.get("近期催化", "")).startswith("🟢")]
    # 预期上修(分析师近4周净上调EPS):赢家共同信号,仅美股有数据,按需拉取
    if f_rev:
        us = [r["代码"] for r in sub if str(r["代码"]).isalpha()]
        fwd = forward_many(tuple(us)) if us else {}
        kept = []
        for r in sub:
            net = (fwd.get(r["代码"]) or {}).get("净修正")
            if net is not None and net >= 1:
                r["净修正"] = net
                kept.append(r)
        sub = kept
    filt = sub

    active = [n for n, on in [("便宜", f_cheap), ("不拥挤", f_uncrowded),
                              ("有催化", f_cat), ("预期上修", f_rev)] if on]
    if f_fac != "全部":
        active.append(f_fac)
    any_filter = bool(active)
    if any_filter:
        st.success(f"✅ 同时满足【{' + '.join(active)}】的有 {len(filt)} 只(共 {len(rows)} 只)")
    else:
        st.caption(f"共 {len(rows)} 只。勾上面的条件可组合筛选。")

    show_data = filt if any_filter else rows
    base_cols = (["赛道"] if is_all else []) + ["名称", "代码", "派系", "现价", "PE", "前瞻PE",
                 "PS", "隐含涨幅%", "52周位置%"]
    if f_rev and any("净修正" in r for r in show_data):
        base_cols.append("净修正")
    base_cols += ["近期催化", "催化头条"]
    if not is_all:
        base_cols.append("判定理由")
    base_cols = [c for c in base_cols if any(c in r for r in show_data)] if show_data else base_cols
    df = pd.DataFrame(show_data)[[c for c in base_cols if c in pd.DataFrame(show_data).columns]] \
        if show_data else pd.DataFrame()
    st.dataframe(df, use_container_width=True, hide_index=True, height=520,
                 column_config={
                     "隐含涨幅%": st.column_config.NumberColumn("目标隐含涨幅%", format="%d%%",
                         help="卖方目标价vs现价,负数=已涨过目标"),
                     "52周位置%": st.column_config.NumberColumn(format="%d%%", help="52周区间位置"),
                     "净修正": st.column_config.NumberColumn(help="分析师近4周净上调EPS家数,越大越强"),
                     "催化头条": st.column_config.TextColumn(width="medium"),
                     "判定理由": st.column_config.TextColumn("赛道内备注", width="medium"),
                 })
    st.caption("🎯 研报学到的赢家规律=**价值链卡位 + 预期上修 + 不拥挤**(再加便宜/催化更稳)。"
               "⚠️拥挤度/预期上修只有美(及部分台日韩欧)股有,A股缺——勾这两项会过滤掉A股。"
               "「🌍全部赛道」默认不带催化/预期上修,勾了才对候选实时拉取。")


# 太空经济主题(你持仓 NASA/DXYZ 所在赛道)。研报底子:MS《Space 60》,FY27国防预算$1.5万亿、太空军+77%
SPACE_THEMES = {
    "🛰️ 卫星/太空互联网": {
        "ASTS": "AST SpaceMobile·手机直连卫星,弹性最大", "IRDM": "铱星·成熟卫星通信现金流",
        "GSAT": "Globalstar·绑苹果卫星", "VSAT": "Viasat·卫星宽带"},
    "🚀 火箭发射/新太空": {
        "RKLB": "Rocket Lab·小火箭+Neutron,发射龙头", "LUNR": "Intuitive Machines·登月/月球经济",
        "RDW": "Redwire·太空基础设施", "PL": "Planet Labs·对地观测数据", "BKSY": "BlackSky·实时地理情报"},
    "🛡️ 国防航天主承包": {
        "LMT": "洛克希德·导弹/航天主承包", "NOC": "诺斯罗普·B21/太空", "RTX": "雷神·导弹防御",
        "BA": "波音·航天/防务", "LHX": "L3Harris·太空载荷", "GD": "通用动力"},
    "⛏️ 关键材料/上游": {
        "MP": "MP Materials·稀土(国防/太空磁材),美国独苗"},
    "📦 太空ETF/代理(含你持仓)": {
        "NASA": "★你的持仓·Tema太空创新ETF", "DXYZ": "★你的持仓·Destiny,持SpaceX代理",
        "ARKX": "ARK太空探索ETF", "UFO": "Procure太空ETF"},
}


@st.cache_data(ttl=600, show_spinner=False)
def space_data():
    out = {}
    for grp, mp in SPACE_THEMES.items():
        out[grp] = aimap.build_many(list(mp.items()))
    return out


def page_space():
    st.subheader("🚀 太空经济")
    st.caption("你持仓 NASA(Tema太空ETF)、DXYZ(SpaceX代理)所在的主题。按子赛道铺全球标的+实时估值。"
               "底子:MS《Space 60》——FY27国防预算$1.5万亿、太空军预算+77%至$71B,主题热度十年最高。")
    with st.spinner("拉取太空板块行情+估值…"):
        data = space_data()
    for grp, rows in data.items():
        st.markdown(f"#### {grp}")
        df = pd.DataFrame(rows)[["名称", "代码", "现价", "PE", "前瞻PE", "PS",
                                 "隐含涨幅%", "52周位置%", "判定理由"]]
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "隐含涨幅%": st.column_config.NumberColumn("目标隐含涨幅%", format="%d%%",
                             help="卖方目标价vs现价"),
                         "52周位置%": st.column_config.NumberColumn(format="%d%%"),
                         "判定理由": st.column_config.TextColumn("看点", width="large"),
                     })
    st.caption("💡 我的判断:太空多数是题材/亏损(ASTS/LUNR/RKLB弹性大但贵),国防主承包(LMT/NOC/RTX)"
               "是有现金流的稳健底仓;MP(稀土)是国防自主的卡位。你的NASA/DXYZ是一篮子题材,波动大,小仓配置即可。")


def page_aimap():
    st.subheader("💡 AI估值+拥挤地图")
    st.caption("结合实时估值(PE/前瞻PE/PS)与拥挤度(卖方目标隐含涨幅、52周位置),"
               "加我的决断标签。背景:芯片是BofA史上最拥挤交易(80%),核心打法=从拥挤往洼地换仓。")
    with st.spinner("拉取估值+拥挤数据(首次约30秒,之后缓存)…"):
        data = ai_map()
    # 近期催化:扫所有标的近14天新闻
    allrows = tuple((r["代码"], r["名称"], str(r["代码"]).isdigit())
                    for rows in data.values() for r in rows)
    with st.spinner("扫近期新闻催化…"):
        cat = catalysts(allrows)

    for tier, rows in data.items():
        st.markdown(f"#### {tier}")
        for r in rows:
            c = cat.get(r["代码"], {})
            r["近期催化"] = c.get("催化", "—")
            r["催化头条"] = c.get("头条", "")
        df = pd.DataFrame(rows)[["名称", "代码", "现价", "PE", "前瞻PE", "PS",
                                 "隐含涨幅%", "52周位置%", "近期催化", "催化头条", "判定理由"]]
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "隐含涨幅%": st.column_config.NumberColumn(
                             "目标隐含涨幅%", format="%d%%",
                             help="卖方平均目标价vs现价。负数=已涨过分析师目标,定价完美"),
                         "52周位置%": st.column_config.NumberColumn(
                             format="%d%%", help="现价在52周区间的位置,90%+=贴着高点"),
                         "催化头条": st.column_config.TextColumn(width="medium",
                             help="近14天最具代表性的新闻标题"),
                     })
    st.caption("⚠️ 提醒:玻璃基板(三星电机009150.KS等)2027才放量,是埋伏非本季催化,且韩股无实时源;"
               "软件(CRM/MSFT)是逆向注,研究里'抄底软件'被证伪,别梭哈;存储买MU别追龙头SK海力士。"
               "数据:stockanalysis/纳斯达克/腾讯 + 深度研究(高盛Prime·BofA·Yicai·TrendForce)。")


def _fmt(df, with_market=False):
    cols = ["name", "code"]
    if with_market:
        cols.append("market")
    cols += [c for c in ["price", "chg_pct", "pe", "pb", "mktcap_yi", "turnover"] if c in df.columns]
    return df[cols].rename(columns={"name": "名称", "code": "代码", "market": "市场",
        "price": "现价", "chg_pct": "今日%", "pe": "PE", "pb": "PB",
        "mktcap_yi": "总市值(亿)", "turnover": "换手%"})


# ============================================================================
st.title("📈 选股工作台")
tabs = st.tabs(["📊 我的持仓", "🎯 操作建议", "📰 研报情报", "🔮 前瞻信号", "🧭 按赛道选股",
                "💡 AI估值+拥挤", "🔬 AI芯片材料", "🚀 太空经济", "🌐 全市场选股", "🔍 查股票"])
with tabs[0]:
    page_portfolio()
with tabs[1]:
    page_actions()
with tabs[2]:
    page_research()
with tabs[3]:
    page_forward()
with tabs[4]:
    page_sectors()
with tabs[5]:
    page_aimap()
with tabs[6]:
    page_themes()
with tabs[7]:
    page_space()
with tabs[8]:
    page_pick()
with tabs[9]:
    page_lookup()
st.caption("数据来自公开行情接口，仅供研究，非投资建议。")
