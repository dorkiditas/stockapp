# -*- coding: utf-8 -*-
"""
desk.py —— Alpha Desk 的机器闸门(/alphadesk skill 的执行层)。
建于 2026-09-19。起因:她要把 AI 对冲基金做成一个 skill。规矩靠记忆会漏(SIEGY/7-16 部署/CRDO 两张皮
都是"记得规矩但没执行"),所以规矩必须做成闸门,每班开工先过它,出任何 call 先问它。

用法(在 stockapp 目录,用 .venv 的 python):
  python desk.py                      桌面状态:账户 / 闸门 / 未执行建议拖延成本 / 台账 / 自查
  python desk.py gate <代码> <buy|add|sell|trim|short|cover>
                                      某个方向的 call 现在允不允许、必须附带什么
  python desk.py wrap                 收班检查:今天该落的档案落了没(calls_log / account_risk / roadmap)

退出码:0 = 通过 / 1 = 有阻断。
只读:本文件永远不下单、不动钱。
"""
import sys, os, io, csv, json, re, datetime, subprocess

sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
RISK = os.path.join(BASE, 'account_risk.json')
HOLD = os.path.join(BASE, 'holdings.csv')
LOG = os.path.join(BASE, 'calls_log.csv')
LEDGER = os.path.join(BASE, 'feed', 'txt', 'reading_ledger.csv')
IDENT = os.path.join(BASE, 'position_identity.json')
ROADMAP = r'C:\Users\xiaoy\OneDrive\Desktop\基金路线图.html'
PY = os.path.join(BASE, '.venv', 'Scripts', 'python.exe')

# ---- 军规常量(与 calls.py 自缴械条款 / selfcheck R7 同源,改这里要同时改那边) ----
LEV_SURVIVAL = 2.50        # 杠杆 >= 此值:生存 gate,只准减
BUF_SURVIVAL = 15000       # 缓冲 < 此值:生存 gate
LEV_UNLOCK = 1.50          # 买方解锁:杠杆 < 此值 且缓冲 >= BUF_SURVIVAL 连续 5 日
LEV_HARD = 3.00            # 🔴 硬红线
BUF_HARD = 3000            # 🔴 硬红线
DROP_HARD = 12.0           # 单票单日跌幅 🔴
STALE_DAYS = 2             # 账户读数超过 N 天 = 盲区,禁买方判断
DOSAGE_WORDS = ('重手', '顶格', '头号', '砸', '满仓', '梭哈', 'all in')
BUY_WORDS = ('建仓', '部署', '首笔', '逢跌加', '加仓', '分批建')

BLOCK, WARN, INFO = [], [], []


def block(m): BLOCK.append(m)
def warn(m): WARN.append(m)
def info(m): INFO.append(m)


# ---------------------------------------------------------------- 数据
def load_risk():
    try:
        return json.load(io.open(RISK, encoding='utf-8'))
    except Exception as e:
        block(f'读不到 account_risk.json({type(e).__name__})——没有账户读数,只准风控和减法')
        return {}


def load_holdings():
    out = {}
    if not os.path.exists(HOLD):
        return out
    for r in csv.DictReader(io.open(HOLD, encoding='utf-8-sig')):
        try:
            out[r['ticker'].strip()] = (float(r['shares']), float(r['cost']))
        except (KeyError, ValueError):
            pass
    return out


def risk_age(risk):
    try:
        d = datetime.date.fromisoformat(risk.get('date', ''))
        return (datetime.date.today() - d).days
    except ValueError:
        return 999


def gate_state(risk):
    """返回 dict:survival(bool) / hard(bool) / stale(bool) / dosage_ban(bool) / 描述"""
    lev = float(risk.get('leverage') or 0)
    buf = float(risk.get('excess_liquidity') or 0)
    age = risk_age(risk)
    st = {
        'lev': lev, 'buf': buf, 'age': age,
        'stale': age > STALE_DAYS,
        'hard': bool(risk) and (buf < BUF_HARD or lev >= LEV_HARD),
        'survival': bool(risk) and (lev >= LEV_SURVIVAL or buf < BUF_SURVIVAL),
        'dosage_ban': lev > LEV_UNLOCK,
    }
    try:
        import calls
        st['locked_flag'] = bool(getattr(calls, 'BUY_SIDE_LOCKED', True))
    except Exception:
        st['locked_flag'] = True
    st['buy_locked'] = st['survival'] or st['stale'] or st['locked_flag']
    return st


def live_prices(tickers):
    try:
        import tencent
        df = tencent.quote(list(tickers))
        m = {}
        for _, r in df.iterrows():
            code = r['code']
            key = code[2:] if code.startswith('us') else (code[2:] if code.startswith(('sh', 'sz')) else code)
            m[key] = (r['price'], r['chg_pct'], r['name'])
        return m
    except Exception as e:
        warn(f'腾讯行情不可用({type(e).__name__}),拖延成本用上次记录')
        return {}


# ---------------------------------------------------------------- status
def cmd_status():
    risk = load_risk()
    st = gate_state(risk)
    hold = load_holdings()
    today = datetime.date.today()

    print('=' * 70)
    print(f'Alpha Desk 桌面状态  {today}  (Max·副CIO)')
    print('=' * 70)
    if risk:
        print(f"账户({risk.get('date')},{st['age']}天前): IB净值 ${float(risk.get('net_liq',0)):,.0f} | "
              f"真实总资产 ${float(risk.get('true_nav',0)):,.0f} | 缓冲 ${st['buf']:,.0f} | 杠杆 {st['lev']:.2f}")
    # 闸门
    print()
    print('闸门:')
    if st['stale']:
        block(f"账户读数 {st['age']} 天旧(>{STALE_DAYS}) = 盲区:禁任何加仓类判断,先拉 IB get_account_summary")
    if st['hard']:
        warn(f"🔴 硬红线命中(缓冲<{BUF_HARD} 或 杠杆>={LEV_HARD}):必须重拉一次 IB 二次确认,两次一致才推微信")
    if st['survival']:
        why = []
        if st['lev'] >= LEV_SURVIVAL: why.append(f"杠杆 {st['lev']:.2f} >= {LEV_SURVIVAL}")
        if st['buf'] < BUF_SURVIVAL: why.append(f"缓冲 ${st['buf']:,.0f} < ${BUF_SURVIVAL:,}")
        print(f"  🔒 生存gate 触发({' 且 '.join(why)}) → 只准:减/清/换仓/观察;禁字眼 {BUY_WORDS}")
    else:
        print(f"  🔓 生存gate 未触发(杠杆 {st['lev']:.2f} / 缓冲 ${st['buf']:,.0f})")
    print(f"  买方权限:{'锁死' if st['buy_locked'] else '开放'}"
          f"(calls.BUY_SIDE_LOCKED={st['locked_flag']};解锁条件=杠杆<{LEV_UNLOCK} 且缓冲>={BUF_SURVIVAL:,} 连续5日)")
    if st['dosage_ban']:
        print(f"  🚫 剂量词禁令生效(杠杆>{LEV_UNLOCK}):{DOSAGE_WORDS} 不得出现在任何输出")

    # 未执行建议 × 拖延成本
    print()
    print('未执行建议 × 拖延成本(早报第一段):')
    try:
        import daily
        acts = daily.open_actions(LOG)
    except Exception as e:
        acts = []
        warn(f'daily.open_actions 失败:{e}')
    # 只保留真实标的(持仓里有的,或干净的单一代码);ACCT/RISK/PORTFOLIO 这类是日志标签不是仓位
    clean = re.compile(r'^([A-Z]{1,5}|\d{6}|\d{4,5}\.HK)$')
    acts = [a for a in acts if (a['ticker'] in hold or clean.match(a['ticker'])) and a['price0']]
    px = live_prices([a['ticker'] for a in acts]) if acts else {}
    if not acts:
        print('  (无)')
    for a in acts:
        cur = px.get(a['ticker'], (None, None, ''))[0]
        pct = daily.delay_pnl_pct(a['side'], a['price0'], cur) if cur else None
        sh = abs(hold.get(a['ticker'], (0, 0))[0])
        usd = ''
        if pct is not None and a['price0'] and sh:
            usd = f" ≈ {'+' if pct>=0 else '-'}${abs(pct)/100*a['price0']*sh:,.0f}(按持仓{sh:.0f}股)"
        pstr = f"{pct:+.1f}%" if pct is not None else '?'
        print(f"  {a['side_label']} {a['ticker']:<7} {a['date']} @{a['price0']} → 现 {cur}  拖延 {pstr}{usd}")
        print(f"      {a['call'][:70]}")
    if acts:
        print('  注:正数=她不听反而占便宜(用价格说话,不洗地);逻辑没变就仍该执行。')

    # 台账
    print()
    if os.path.exists(LEDGER):
        rows = [r for r in csv.reader(io.open(LEDGER, encoding='utf-8-sig')) if len(r) > 1][1:]
        unread = sum(1 for r in rows if r[1].strip().startswith('未读'))
        print(f'研报台账:{len(rows)} 份,未读 {unread}(每班清 ≥5,优先能证伪在案 call 的)')
    # 今日落档
    todays = [r for r in csv.reader(io.open(LOG, encoding='utf-8')) if r and r[0] == today.isoformat()]
    print(f'今日 calls_log 已落 {len(todays)} 条')

    # selfcheck
    print()
    print('selfcheck.py(R1-R10):')
    try:
        p = subprocess.run([PY if os.path.exists(PY) else sys.executable, os.path.join(BASE, 'selfcheck.py')],
                           capture_output=True, text=True, encoding='utf-8', timeout=120)
        lines = p.stdout.splitlines()
        # R7(生存gate)本脚本已单独裁定(它只锁买方,不锁减法),不再重复算阻断;其余 R 规则的阻断照算
        blocks = [l.strip() for l in lines if l.strip().startswith('[R') and '[R7-' not in l
                  and any(l.strip().startswith(f'[R{n}-') for n in (0, 1, 2, 3, 4, 5, 6, 8, 9, 10))]
        hard = []
        in_block = False
        for l in lines:
            if l.startswith('🔴'): in_block = True; continue
            if l.startswith('🟠'): in_block = False
            if in_block and l.strip().startswith('[R') and '[R7-' not in l:
                hard.append(l.strip())
        for l in hard:
            print('  🔴 ' + l)
        nwarn = sum(1 for l in lines if l.startswith('🟠'))
        print(f'  (警告见 python selfcheck.py 全文)' if nwarn else '  ✅ selfcheck 无警告')
        for l in hard:
            block('selfcheck ' + l[:90])
    except Exception as e:
        warn(f'selfcheck 未能运行:{e}')

    _report()


# ---------------------------------------------------------------- gate <ticker> <side>
PEAKS = os.path.join(BASE, 'price_peaks.json')
PEAK_STALE_DAYS = 10


def drawdown_from_peak(tk, px):
    """返回 (60日高点, 当前回撤%, 数据日期) 或 None。
    数据由 Max 每班用 IB get_price_history 更新进 price_peaks.json。
    宁可返回 None 让闸门喊'数据不可用',也不拿旧数据放行。"""
    if not px:
        return None
    try:
        raw = json.load(io.open(PEAKS, encoding='utf-8'))
    except Exception:
        return None
    rec = raw.get('peaks', {}).get(tk)
    if not rec:
        return None
    asof = rec.get('asof', '')
    try:
        age = (datetime.date.today() - datetime.date.fromisoformat(asof)).days
    except Exception:
        return None
    if age > PEAK_STALE_DAYS:
        return None
    peak = float(rec['high_60d'])
    if peak <= 0:
        return None
    return peak, (float(px) / peak - 1) * 100, asof


def cmd_gate(ticker, side):
    side = side.lower()
    if side not in ('buy', 'add', 'sell', 'trim', 'short', 'cover'):
        print('side 必须是 buy|add|sell|trim|short|cover'); sys.exit(2)
    risk = load_risk()
    st = gate_state(risk)
    hold = load_holdings()
    tk = ticker.upper() if not ticker.isdigit() else ticker
    print('=' * 70)
    print(f'闸门裁定:{tk} · {side}   (杠杆 {st["lev"]:.2f} / 缓冲 ${st["buf"]:,.0f} / 读数 {st["age"]} 天前)')
    print('=' * 70)
    must = []

    # 0 身份闸门
    try:
        reg = json.load(io.open(IDENT, encoding='utf-8'))['positions']
        if tk not in reg:
            block(f'{tk} 不在 position_identity.json:先用 IB search_contracts/交易所/公司IR 核【法实体·ADR比例·主上市地】再写')
        else:
            info(f"身份:{reg[tk].get('legal_entity','?')}(核于 {reg[tk].get('verified_by','?')})")
    except Exception:
        warn('position_identity.json 不可读,身份闸门跳过')

    # 1 前提闸门:档案里已有什么
    try:
        import calls
        if tk in calls.MY_CALLS:
            v = calls.MY_CALLS[tk]
            head = (v[0] if isinstance(v, (list, tuple)) else str(v)).replace('\n', ' ')[:220]
            info(f'档案在案:{head}…')
            must.append('先从头读完 calls.py 里该标的的现有条目,写明"我这条与档案哪一条冲突或重复"')
        else:
            info('档案无此标的 → 属于新 idea,走三问')
            must.append('反共识三问:共识是什么/已定价多少;我看到了什么没被定价;为什么现在没被定价——答不出=只报事实不给方向')
    except Exception as e:
        warn(f'calls.py 载入失败:{e}')

    # 2 方向闸门
    if side in ('buy', 'add', 'short'):
        if st['stale']:
            block(f'账户读数 {st["age"]} 天旧 = 盲区:禁买方判断')
        if st['survival']:
            block(f'生存gate:杠杆 {st["lev"]:.2f}/缓冲 ${st["buf"]:,.0f} → 只准减/清/换仓/观察,本 call 不得输出')
        if st['locked_flag'] and not st['survival']:
            block('calls.BUY_SIDE_LOCKED=True(自缴械条款):需杠杆<1.5 且缓冲>=$15k 连续5日才解锁')
        if side == 'short':
            must.append('空头=无上限风险:必须写死回补线,-30% 必平;与多头主线打架的空单一律不建')
        if not BLOCK:
            must.append('联锁条款:同一句话里写"杠杆<X且缓冲>Y才执行,否则本建议自动作废"')
            must.append('显式数字:"如果我又错了她会损失多少美元"')
            must.append('钱从哪来:必须是减仓腾出的,不加毛杠杆;首笔≤净值5%')
            must.append('论文≠处方:先过账户状态审查,再写交易表达')
    elif side in ('sell', 'trim'):
        pos = hold.get(tk)
        px = live_prices([tk]).get(tk, (None, None, ''))[0]
        if pos and px:
            sh, cost = pos
            pnl = (px - cost) / cost * 100 if cost else 0
            if sh > 0 and pnl > 0:
                info(f'这是一只【赢家】:成本 {cost:.2f} → 现 {px}({pnl:+.1f}%)')
                must.append('砍赢家战绩 0/2:必须写明"这是风控不是看空"+ "如果我又错了她少赚多少美元"')
                must.append('先从已经坏掉的仓里找减仓额度;非动它不可要说清为什么')
                must.append('不许拿远期风险(2028 产能崖之类)交易当期仓位')
            elif sh > 0:
                info(f'这是一只【亏损仓】:成本 {cost:.2f} → 现 {px}({pnl:+.1f}%);砍坏仓战绩 3/3')
        must.append('给线不给令:止盈线 + 止损线并列,拖延成本按班重算')

        # ------------------------------------------------------------------
        # 追跌闸门(2026-09-19 晚班建)。起因:她说"你的 call 真的很不准",
        # 我把自己 61 条带价格的方向性 call 全部拉出来用现价打分,结果是单调的:
        #   发 call 时该股距【当时已知阶段高点】的回撤   条数   胜率
        #        < 10%  (还在高位)                     10    100.0%
        #        10-20%                                 5     40.0%
        #        > 20%  (已深跌)                       19      5.3%
        # 即:我的基本面判断不差(AVGO 在高位喊的 10 条全对),
        # 坏的是时机——价格先跌、我后怕,怕了才喊减,等于卖在地板上。
        # QCOM 我从 -23% 一路喊到 -37%(8/3 当天正是区间绝对底部 142.89),现价 178;
        # SPCX 我在 -17%~-24% 区间喊了 10 次,现价 152.64。
        # 靠"我记得别追跌"没用,我已经证明过我不记得。所以做成闸门。
        # 例外:生存红线(st['hard'])触发时不受限——那是保命,不是择时。
        # ------------------------------------------------------------------
        dd = drawdown_from_peak(tk, px)
        if dd is None:
            warn(f'{tk} 没有可用的阶段高点数据(price_peaks.json 缺失或过期)'
                 f' → 追跌闸门无法执行,先用 IB get_price_history 更新再出减仓 call')
        else:
            peak, ddpct, asof = dd
            info(f'距阶段高点:现价 {px} vs 60日高 {peak:.2f} = {ddpct:+.1f}%(高点数据 {asof})')
            if ddpct <= -20 and not st['hard']:
                block(f'【追跌闸门】{tk} 已自阶段高点回撤 {ddpct:.1f}%(≥20%),'
                      f'而我在这个区间的减仓胜率是 19 条里只对 1 条(5.3%)。'
                      f'生存红线未触发(缓冲 ${st["buf"]:,.0f}/杠杆 {st["lev"]:.2f}),'
                      f'所以这不是保命是择时 → 只许出【风险记录】,不许出减仓指令')
            elif ddpct <= -10:
                warn(f'{tk} 回撤 {ddpct:.1f}% 落在 10-20% 桶(我的历史胜率 40%)'
                     f' → 可以出,但必须在 call 里写明这条胜率,让她知道我在这个位置的记录很一般')
            else:
                info(f'回撤 {ddpct:.1f}% < 10%,属于我历史胜率 100%(10/10)的区间 —— 这是我该喊的位置')
    elif side == 'cover':
        must.append('平空=降 gross,永远允许;写明回补后杠杆/缓冲变成多少')

    # 3 通用
    if st['dosage_ban']:
        must.append(f'剂量词禁令:{DOSAGE_WORDS} 一个都不许出现')
    must.append('证伪条件 + 验证时点(哪份数据、哪个日期出来说明我错了)')
    must.append('先在 reading_ledger 检索能打脸本 call 的未读件,有就先读')
    must.append('数字带时间窗口(今天/本周/YTD 写死在同一句)')
    must.append('落档:calls.py + calls_log.csv(7 字段、正确加引号)→ 跑 check_calls.py')

    for m in INFO:
        print('  ℹ ' + m)
    print()
    if BLOCK:
        print('🔴 不许出这个 call:')
        for m in BLOCK:
            print('   · ' + m)
    else:
        print('🟢 允许,但必须附带:')
    for m in must:
        print('   □ ' + m)
    if WARN:
        print()
        for m in WARN:
            print('  🟠 ' + m)
    sys.exit(1 if BLOCK else 0)


# ---------------------------------------------------------------- wrap
def cmd_wrap():
    today = datetime.date.today().isoformat()
    risk = load_risk()
    if risk.get('date') != today:
        warn(f"account_risk.json 日期 {risk.get('date')} ≠ 今天(周末/休市可接受,盘中班不可)")
    todays = [r for r in csv.reader(io.open(LOG, encoding='utf-8')) if r and r[0] == today]
    if not todays:
        block('今天 calls_log.csv 一条没落——判断没进单一事实源等于没发生')
    if not any('DELAY_COST' in r[1] for r in todays):
        warn('今天没有 DELAY_COST 重算行')
    try:
        mt = datetime.date.fromtimestamp(os.path.getmtime(ROADMAP))
        if (datetime.date.today() - mt).days > 1:
            warn(f'桌面基金路线图.html 上次更新 {mt},跑 update_roadmap.py 回填(close-the-loop)')
    except OSError:
        warn('找不到桌面基金路线图.html')
    brief = os.path.join(BASE, 'shift_brief.md')
    try:
        mt = datetime.date.fromtimestamp(os.path.getmtime(brief))
        if mt != datetime.date.today():
            warn('shift_brief.md 今天没更新——写文件≠汇报,但没文件更不算')
    except OSError:
        warn('shift_brief.md 不存在')
    print('收班检查:')
    _report()


def _report():
    print()
    for m in WARN:
        print('🟠 ' + m)
    for m in BLOCK:
        print('🔴 ' + m)
    if not BLOCK and not WARN:
        print('✅ 通过')
    print('结论:' + ('阻断——先修再出判断' if BLOCK else '通过'))
    sys.exit(1 if BLOCK else 0)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'status':
        cmd_status()
    elif a[0] == 'gate' and len(a) >= 3:
        cmd_gate(a[1], a[2])
    elif a[0] == 'wrap':
        cmd_wrap()
    else:
        print(__doc__); sys.exit(2)
