# -*- coding: utf-8 -*-
"""
selfcheck.py —— Max 的自查闸门。每班开工第一件事跑它,不通过不许出判断。
建于 2026-08-14,起因:8/13 一整天我犯了五类错,每一类都是她抓到的,不是我自己抓到的。
这个脚本把那五类错做成机械检查,让它们不依赖我的自觉。

用法:  py -3.12 selfcheck.py
退出码 0 = 通过;1 = 有阻断项(BLOCK),不许出任何持仓判断。
"""
import sys, os, csv, re, json, datetime

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(BASE, 'feed', 'txt', 'reading_ledger.csv')
LOG = os.path.join(BASE, 'calls_log.csv')
RISK = os.path.join(BASE, 'account_risk.json')
HOLD = os.path.join(BASE, 'holdings.csv')

BLOCK, WARN = [], []


def block(rule, msg):
    BLOCK.append((rule, msg))


def warn(rule, msg):
    WARN.append((rule, msg))


# ---------- 载入 ----------
def load_calls():
    sys.path.insert(0, BASE)
    import importlib
    import calls as _c
    importlib.reload(_c)
    return _c.MY_CALLS, _c.MY_BUYS


try:
    MY_CALLS, MY_BUYS = load_calls()
except Exception as e:
    block('C0-编译', f'calls.py 无法载入:{e}')
    MY_CALLS, MY_BUYS = {}, {}

ledger = []
if os.path.exists(LEDGER):
    ledger = [r for r in csv.reader(open(LEDGER, encoding='utf-8-sig')) if len(r) > 1][1:]

log = []
if os.path.exists(LOG):
    log = [r for r in csv.reader(open(LOG, encoding='utf-8')) if len(r) >= 7]

risk = {}
if os.path.exists(RISK):
    try:
        risk = json.load(open(RISK, encoding='utf-8'))
    except Exception:
        pass

# ---------- 规则 1:台账不许无凭据地声称全文已读 ----------
# 8/13 我把 78 份只读第1页/只读开头的标成"全文已读"。凭据 = 明确写出读了多少页。
PAGE_RE = re.compile(r'全文已读\s*(\d+)\s*页|全文已读\(|读\s*p?\d+\s*[-–]\s*p?\d+|逐页|逐表|逐行')
n_claim = n_ok = 0
for r in ledger:
    st = r[1]
    if '全文已读' not in st and '已读全' not in st:
        continue
    if '谎报' in st:          # 已被标注改正的,不再计入声称
        continue
    n_claim += 1
    if PAGE_RE.search(st):
        n_ok += 1
    else:
        warn('R1-阅读凭据', f'台账声称全文已读但未写明页数凭据:{r[-1][:60]}')
if n_claim:
    ratio = n_ok / n_claim
    if ratio < 0.90:
        block('R1-阅读凭据', f'声称全文已读 {n_claim} 份,其中只有 {n_ok} 份({ratio:.0%})写明了页数凭据。低于 90% 视为不可信。')

# ---------- 规则 2:承重仓位的研报必须真读完 ----------
# 承重 = 占 IB 净值 >15%。这些标的的任何新判断,来源必须是全文已读件。
netliq = float(risk.get('net_liq') or 0)
heavy = []
if netliq and os.path.exists(HOLD):
    # 用 account_risk 里的备注无法逐票取值,这里用 calls.py 里已写明的占比文字兜底
    for tk, v in MY_CALLS.items():
        txt = (v[0] if isinstance(v, (list, tuple)) else str(v))
        m = re.search(r'净值\s*(?:的)?\s*(\d{1,2}(?:\.\d)?)%', txt)
        if m and float(m.group(1)) >= 15:
            heavy.append((tk, float(m.group(1))))
UNDERREAD = re.compile(r'谎报|只读|仅读|未读完|只渲染')
REMEDY = re.compile(r'已修复|已补读|已逐页|真读了|已全文补读')
for tk, pct in heavy:
    txt = MY_CALLS[tk][0]
    unresolved = []
    for m in UNDERREAD.finditer(txt):
        window = txt[m.start():m.start() + 160]
        if not REMEDY.search(window):
            unresolved.append(txt[max(0, m.start()-20):m.start()+60].replace(chr(10), ' '))
    if unresolved:
        block('R2-承重件', f'{tk}(净值 {pct}%)存在未修复的欠读标注 {len(unresolved)} 处,例:…{unresolved[0]}…')

# ---------- 规则 3:引用研报必须同时写明评级与目标价 ----------
# 8/13 我从一份买入评级+75.5%上行的报告里只摘空头数字。
HOUSE = re.compile(r'高盛|花旗|大摩|摩根士丹利|瑞银|美银|摩根大通|广发|中金|野村|Bernstein|巴克莱')
RATING = re.compile(r'买入|增持|中性|卖出|减持|持有|Buy|Neutral|Sell|Overweight|Underweight|信念名单|Conviction')
TP = re.compile(r'目标价|TP\s*\$|目标市值|price target', re.I)
bad_cite = 0
for r in log:
    if r[0] != datetime.date.today().isoformat():
        continue
    body, tag = r[4], r[1]
    NONSTOCK = re.compile(r'宏观|产业判断|策略|量化|组合风险|自省|流程|对账')
    if NONSTOCK.search(tag):
        continue          # 策略/宏观/量化/行业类研究无单票评级,豁免
    if HOUSE.search(body) and len(body) > 300:
        if not (RATING.search(body) and TP.search(body)):
            bad_cite += 1
            warn('R3-引用完整性', f'{tag}:引用了卖方但未同时写明评级与目标价')
if bad_cite >= 3:
    block('R3-引用完整性', f'今日有 {bad_cite} 条引用卖方却未写明评级+目标价。这是"选择性摘录"的机械信号。')

# ---------- 规则 4:任何同比/环比/占比必须写明分子分母口径 ----------
# 8/13 我三次拿计划值当历史值、拿汇总当分部、拿标题当环比。
RATIO = re.compile(r'同比|环比|占比|[+\-]\d+(?:\.\d+)?%')
BASIS = re.compile(r'口径|基数|分母|分子|vs\s|对照|按.{0,6}计|同一口径')
for r in log:
    if r[0] != datetime.date.today().isoformat():
        continue
    body = r[4]
    if len(RATIO.findall(body)) >= 5 and not BASIS.search(body):
        warn('R4-口径', f'{r[1]}:含多处比率但未写口径说明')

# ---------- 规则 5:每个方向性判断必须有证伪条件 + 日期 ----------
FALSIFY = re.compile(r'证伪|可证伪|我错了|作废|推翻|失效|降级触发')
DATED = re.compile(r'\d{1,2}\s*月|Q[1-4]|[1-4]Q\d{2}|\d{4}\s*年|财报')
for tk, v in MY_CALLS.items():
    short = v[0] if isinstance(v, (list, tuple)) else str(v)
    if re.search(r'已清仓|已了结|归档|观察', short):
        continue
    full = short + (v[1] if isinstance(v, (list, tuple)) and len(v) > 1 else '')
    if not FALSIFY.search(full):
        block('R5-证伪条件', f'{tk} 有在册判断但档案里找不到证伪条件')
    elif not DATED.search(full):
        warn('R5-证伪条件', f'{tk} 有证伪条件但没写验证时点')

# ---------- 规则 6:未执行建议的拖延成本必须当班重算 ----------
today = datetime.date.today()
pend = [r for r in log if '未执行' in r[6]]
recalc = [r for r in log if r[0] == today.isoformat() and 'DELAY_COST' in r[1]]
if pend and not recalc:
    warn('R6-拖延成本', f'有 {len(pend)} 条未执行建议,但今日 log 里没有 DELAY_COST 重算记录')
elif pend:
    print(f'ℹ️  R6:{len(pend)} 条未执行建议,今日已重算拖延成本 ✓')

# ---------- 规则 7:生存 gate ----------
lev = float(risk.get('leverage') or 0)
buf = float(risk.get('excess_liquidity') or 0)
if lev >= 2.5 or (buf and buf < 15000):
    block('R7-生存gate', f'杠杆 {lev} / 缓冲 ${buf:,.0f} —— 只准喊减,禁"建仓/部署"字眼')

# ---------- 规则 8:宏观必须含长端,不只是政策利率 ----------
# 8/13 我用CPI与FedWatch宣布"宏观在改善",而10年期在19个月高点。
macro_today = [r for r in log if r[0] == today.isoformat() and '宏观' in r[1]]
if macro_today:
    joined = ' '.join(r[4] for r in macro_today)
    if not re.search(r'10\s*年期|长端|期限溢价|30\s*年期|收益率曲线', joined):
        block('R8-宏观长端', '今日有宏观判断但未包含长端/期限溢价读数。政策利率是二阶,长端是一阶。')

# ---------- 规则 9:点名公司必须带可核验代码 ----------
# 8/7 我把 SIEGY 认成西门子能源(实为西门子集团);8/14 我把江苏永鼎认成亨通光电。
# 两次都是"中文名/英文名相近"导致的,而两次都能被一个代码检查挡住。
CN_CO = re.compile(r'[\u4e00-\u9fff]{2,6}(?:光电|科技|股份|电气|能源|重工|集团|电子|通信|材料)')
CODE = re.compile(r'\d{6}\.(?:SH|SZ|SS)|\d{4}\.(?:HK|TW|T)|[A-Z]{1,5}\.(?:O|N|OQ)|\b[A-Z]{2,5}\s*(?:US|美股)|代码')
for r in log:
    if r[0] != datetime.date.today().isoformat():
        continue
    body = r[4]
    names = set(CN_CO.findall(body))
    if len(names) >= 2 and not CODE.search(body):
        warn('R9-公司标识', f'{r[1]}:点名了 {len(names)} 家中文公司却未给任何可核验代码')

# ---------- 输出 ----------
print('=' * 68)
print(f'Max 自查闸门  {today}  ——  calls {len(MY_CALLS)} / 台账 {len(ledger)} / log {len(log)}')
print('=' * 68)
if risk:
    print(f"账户:净值 ${netliq:,.0f} | 缓冲 ${buf:,.0f} | 杠杆 {lev}")
print()
if BLOCK:
    print(f'🔴 阻断 {len(BLOCK)} 项 —— 不许出任何持仓判断:')
    for k, m in BLOCK:
        print(f'   [{k}] {m}')
    print()
if WARN:
    print(f'🟠 警告 {len(WARN)} 项:')
    for k, m in WARN[:25]:
        print(f'   [{k}] {m}')
    if len(WARN) > 25:
        print(f'   ...另有 {len(WARN)-25} 条')
    print()
if not BLOCK and not WARN:
    print('✅ 全部通过')
print(f'结论:{"不通过 — 先修 BLOCK 项" if BLOCK else "通过"}')
sys.exit(1 if BLOCK else 0)
