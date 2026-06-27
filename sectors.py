# -*- coding: utf-8 -*-
"""
AI产业链细分赛道 —— 12个赛道,全球标的(美/中A股/港/台/韩/日/欧)。
按赛道选股:选赛道 → 实时拉 估值(aimap._one)+拥挤+催化(catalyst)。
代码后缀:纯数字=A股(腾讯);.HK=港股(腾讯);.TW台/.T日/.KS韩/.AS.DE.PA欧=Yahoo;字母=美股。
研究判定基于2026-06深度研究。备注尾括号标地区。
"""
import aimap
import catalyst
from concurrent.futures import ThreadPoolExecutor

SECTORS = {
    "算力/GPU": {
        "verdict": "🔴 最拥挤核心 —— BofA史上最拥挤交易(80%),别加码",
        "tickers": {
            "NVDA": "英伟达·龙头(美)", "AMD": "超威·前瞻PE62(美)", "CBRS": "Cerebras·你的持仓(美)",
            "688256": "寒武纪·算力龙头(A)", "688041": "海光信息·CPU/DCU(A)",
            "300474": "景嘉微·国产GPU(A)", "688521": "芯原股份·IP(A)"},
    },
    "定制ASIC/IP": {
        "verdict": "🟡 分化 —— AVGO质量在,ALAB/世芯已超目标价",
        "tickers": {
            "AVGO": "博通·前瞻26质量在(美)", "MRVL": "迈威尔·已超目标价(美)",
            "ALAB": "Astera·PS71躲(美)", "MTSI": "MACOM(美)",
            "3661.TW": "世芯-KY·AI ASIC设计(台)", "3035.TW": "智原·ASIC(台)",
            "4966.TWO": "譜瑞-KY·信号IC(台)", "688008": "澜起科技·内存接口龙头(A)"},
    },
    "光互连/光模块": {
        "verdict": "🟡 美股有相对值,A股最挤 —— CIEN/COHR没人挤,中际旭创全球最挤",
        "tickers": {
            "COHR": "Coherent·相对值PS11(美)", "LITE": "Lumentum·PS26(美)",
            "CIEN": "Ciena·隐含+40%没人挤(美)", "AAOI": "应用光电·弹性大(美)",
            "FN": "Fabrinet·代工龙头(美)", "300308": "中际旭创·全球最挤(A)",
            "300502": "新易盛·公募超配(A)", "300394": "天孚通信·PE169(A)",
            "688498": "源杰科技·PS585(A)", "002281": "光迅科技(A)",
            "300570": "太辰光·无源(A)", "688048": "长光华芯·激光芯片(A)"},
    },
    "网络/交换": {
        "verdict": "🟡 白盒交换是AI东风 —— ANET贵,智邦/CSCO相对稳",
        "tickers": {
            "ANET": "Arista·前瞻45(美)", "CSCO": "思科·便宜Strong Buy(美)",
            "JNPR": "Juniper(美)", "2345.TW": "智邦·白盒交换龙头(台)",
            "301165": "锐捷网络·国产交换机(A)", "000938": "紫光股份·新华三(A)"},
    },
    "存储/HBM": {
        "verdict": "🟢 机会 —— 卖到2028缺货;海力士/三星forward仅6倍",
        "tickers": {
            "000660.KS": "SK海力士·HBM龙头前瞻6.7(韩)", "005930.KS": "三星电子·前瞻6隐含+21%(韩)",
            "MU": "美光·前瞻11最硬(美)", "SNDK": "闪迪(美)", "STX": "希捷·HDD(美)",
            "2408.TW": "南亚科·DRAM(台)", "2344.TW": "华邦电·利基存储(台)",
            "603986": "兆易创新·国产存储(A)", "301308": "江波龙·模组(A)",
            "300475": "香农芯创·HBM分销(A)", "300223": "北京君正·车规存储(A)"},
    },
    "晶圆代工/硅片": {
        "verdict": "🟡 TSM估值合理但在高位;硅片信越/SUMCO隐形卡位",
        "tickers": {
            "2330.TW": "台积电·前瞻19合理(台)", "2303.TW": "联电·成熟制程(台)",
            "6770.TW": "力积电(台)", "GFS": "格芯·成熟制程(美)",
            "0981.HK": "中芯国际·国产龙头(港)", "688347": "华虹·特色工艺(A)",
            "688126": "沪硅产业·大硅片(A)", "605358": "立昂微·硅片(A)",
            "4063.T": "信越化学·硅片龙头PE29(日)", "3436.T": "SUMCO·硅片第二(日)"},
    },
    "半导体设备": {
        "verdict": "🔴 贵+挤+高位 —— 欧美日设备全在52周高位且超目标价,别加",
        "tickers": {
            "AMAT": "应用材料(美)", "LRCX": "泛林(美)", "KLAC": "科磊(美)",
            "ASML.AS": "阿斯麦·EUV垄断(欧)", "ASM.AS": "ASM国际·ALD(欧)",
            "BESI.AS": "BESI·混合键合(欧)", "AIXA.DE": "爱思强·MOCVD(欧)",
            "8035.T": "东京电子(日)", "6857.T": "爱德万·AI测试龙头97%高位(日)",
            "6920.T": "Lasertec·EUV检测(日)", "7735.T": "SCREEN·清洗(日)", "6146.T": "Disco·切割(日)",
            "002371": "北方华创·国产龙头(A)", "688012": "中微公司·刻蚀(A)",
            "688072": "拓荆科技·薄膜(A)", "688082": "盛美上海·清洗(A)",
            "300604": "长川科技·测试机(A)", "688361": "中科飞测·量检测(A)"},
    },
    "先进封装": {
        "verdict": "🟢 ABF载板(日)+玻璃基板(韩)上游卡位;A股封测估值最低(PS3.5)",
        "tickers": {
            "AMKR": "Amkor·OSAT(美)", "3711.TW": "日月光·封测全球龙头(台)",
            "4062.T": "Ibiden·ABF载板龙头(日)", "6976.T": "太阳诱电·MLCC(日)",
            "009150.KS": "三星电机·玻璃基板2027放量(韩)", "011070.KS": "LG Innotek·玻璃基板(韩)",
            "600584": "长电科技·盈利PS3.8(A)", "002156": "通富微电·绑AMD(A)",
            "002185": "华天科技(A)", "688362": "甬矽电子(A)", "688372": "伟测科技·测试(A)"},
    },
    "数据中心电力/散热": {
        "verdict": "🟡 共识看多,ETN/台达相对值;GEV你已持有",
        "tickers": {
            "GEV": "GE Vernova·你的仓前瞻60(美)", "VRT": "维谛·液冷前瞻49(美)",
            "ETN": "伊顿·相对值PS5.7(美)", "NVT": "nVent(美)", "POWL": "Powell·配电(美)",
            "SU.PA": "施耐德电气(欧)", "SIE.DE": "西门子(欧)",
            "2308.TW": "台达电·电源龙头(台)", "002837": "英维克·液冷龙头(A)",
            "002851": "麦格米特·电源(A)", "002335": "科华数据·DC+储能(A)", "301018": "申菱环境·温控(A)"},
    },
    "AI软件/应用": {
        "verdict": "🟡 被嫌弃但选择性有值 —— CRM/MSFT便宜,PLTR低价陷阱",
        "tickers": {
            "MSFT": "微软·PE23(美)", "CRM": "赛富时·PS2.9(美)", "NOW": "ServiceNow(美)",
            "PLTR": "Palantir·PS59陷阱(美)", "ORCL": "甲骨文·云+AI(美)", "SNOW": "Snowflake·数据(美)",
            "SAP.DE": "SAP·欧洲软件龙头(欧)", "688111": "金山办公(A)",
            "002230": "科大讯飞·大模型(A)", "600588": "用友网络(A)"},
    },
    "边缘AI/SoC": {
        "verdict": "🟡 QCOM便宜没人爱,ARM贵到离谱;端侧SoC国产活跃",
        "tickers": {
            "QCOM": "高通·PE25但Hold(美)", "ARM": "Arm·PS95躲(美)",
            "2454.TW": "联发科·手机AI SoC(台)", "6723.T": "瑞萨·车规MCU(日)",
            "603893": "瑞芯微·国产AISoC(A)", "688608": "恒玄科技·音频SoC(A)", "300458": "全志科技·端侧(A)"},
    },
    "AI新材料(GaN/SiC/InP/金刚石)": {
        "verdict": "🔴/⚪ 主题驱动多亏损 —— 题材弹性可博,别当配置",
        "tickers": {
            "NVTS": "Navitas·GaN(美)", "WOLF": "Wolfspeed·SiC评级Sell(美)",
            "ON": "安森美·SiC器件(美)", "AXTI": "AXT·InP衬底(美)",
            "IFX.DE": "英飞凌·功率龙头(欧)", "STMPA.PA": "意法半导体·SiC(欧)",
            "600703": "三安光电·平台(A)", "688234": "天岳先进·8寸SiC(A)",
            "300179": "四方达·金刚石(A)", "300316": "晶盛机电·SiC+设备(A)", "002409": "雅克科技·材料(A)"},
    },
}


def _enrich_catalyst(rows):
    """给行补催化(按代码去重拉新闻)。"""
    uniq = {}
    for r in rows:
        uniq[r["代码"]] = (r["代码"], r["名称"] or r["代码"], str(r["代码"]).isdigit())
    cat = catalyst.classify_many(list(uniq.values()))
    for r in rows:
        c = cat.get(r["代码"], {})
        r["近期催化"] = c.get("催化", "—")
        r["催化头条"] = c.get("头条", "")
    return rows


def build_one(sector, with_catalyst=True):
    """拉某赛道全部标的的估值+拥挤(+催化)。返回 (verdict, [行])。"""
    info = SECTORS[sector]
    items = list(info["tickers"].items())
    with ThreadPoolExecutor(max_workers=12) as ex:
        rows = list(ex.map(lambda kv: aimap._one(kv[0], "", kv[1]), items))
    if with_catalyst:
        _enrich_catalyst(rows)
    else:
        for r in rows:
            r["近期催化"], r["催化头条"] = "—", ""
    return info["verdict"], rows


def build_all(with_catalyst=False):
    """拉全部赛道(并发),每行带『赛道』列。默认不拉催化(几百只太慢),按需另算。"""
    jobs = [(sec, code, note) for sec, info in SECTORS.items()
            for code, note in info["tickers"].items()]
    with ThreadPoolExecutor(max_workers=16) as ex:
        vals = list(ex.map(lambda j: aimap._one(j[1], "", j[2]), jobs))
    out = []
    for (sec, code, note), r in zip(jobs, vals):
        r = dict(r)
        r["赛道"] = sec
        r["近期催化"], r["催化头条"] = "—", ""
        out.append(r)
    if with_catalyst:
        _enrich_catalyst(out)
    return out


def add_catalyst(rows):
    """对外:给一批行补催化(用于全部赛道筛后再算)。"""
    return _enrich_catalyst(rows)


if __name__ == "__main__":
    import sys, time
    sys.stdout.reconfigure(encoding="utf-8")
    t = time.time()
    rows = build_all()
    n = sum(1 for r in rows if r.get("现价") is not None)
    print(f"全池 {len(rows)} 只, 取到价 {n} 只, 用时 {time.time()-t:.0f}s")
    miss = [r["代码"] for r in rows if r.get("现价") is None]
    print("无价(代码可能错):", miss)
