# -*- coding: utf-8 -*-
"""落库自检:字典重复键会被 Python 静默吞掉,导致 calls.py 档案与 App 显示两张皮
(2026-08-02 实际踩过:GEV 被重复键覆盖,我当晚写的更新成了死代码)。
每次改完 calls.py 必须跑一次: py -3.12 check_calls.py"""
import io, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')

src = io.open('calls.py', encoding='utf-8').read()
bad = False

def block(name):
    i = src.index(name + ' = {')
    depth, j = 0, src.index('{', i)
    for k in range(j, len(src)):
        if src[k] == '{': depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0: return src[j:k]
    return src[j:]

for dname in re.findall(r'^([A-Z_][A-Z0-9_]*)\s*=\s*\{', src, re.M):
    b = block(dname)
    keys = collections.Counter(m.group(1) for m in
                               re.finditer(r'^\s*"([^"]+)":\s*[\(\[\{"]', b, re.M))
    dups = {k: n for k, n in keys.items() if n > 1}
    if dups:
        bad = True
        print(f'[FAIL] {dname} 重复键(后者静默覆盖前者): ' +
              ', '.join(f'{k} x{n}' for k, n in dups.items()))
    else:
        print(f'[OK] {dname}: {len(keys)} 键,无重复')

import calls
n_src = len(collections.Counter(
    m.group(1) for m in re.finditer(r'^\s*"([^"]+)":\s*\(', block('MY_CALLS'), re.M)))
if n_src != len(calls.MY_CALLS):
    bad = True
    print(f'[FAIL] MY_CALLS 源码 {n_src} 键 != 载入后 {len(calls.MY_CALLS)} 键')
else:
    print(f'[OK] MY_CALLS 源码==载入 {n_src} 键')

# 2026-09-19 晚班修:MY_CALLS 的值 27 个里有 23 个是裸字符串、不是 (评级, 正文) 二元组,
# 原写法 `for k,(r,b) in ...` 在这里 ValueError 崩溃 —— 而崩溃点在身份闸门之前,
# 意味着下面那道为 SIEGY 认错专门建的身份闸门,从建成起就一次都没真正执行过。
# 闸门坏着 == 没有闸门,所以这里改成两种结构都吃。
def _body(v):
    if isinstance(v, (list, tuple)):
        return v[1] if len(v) > 1 else (v[0] if v else '')
    return v or ''

thin = [k for k, v in calls.MY_CALLS.items() if len(_body(v)) < 40]
if thin:
    print(f'[INFO] 正文<40字(可能覆盖不足): {", ".join(thin)}')

# ---------------------------------------------------------------------------
# 身份闸门(2026-08-07 加):MY_CALLS 里的每个代码必须先在 position_identity.json
# 里有一条经【一级源】核实的身份记录。
# 起因:我把 SIEGY 当成西门子能源跑了至少五班论据,而 IBKR 的 search_contracts
# 一次调用就返回 'SIEMENS AG-SPONS ADR'。信息一直拿得到,我从没去拿。
# 光写"新规矩"没用——靠我记得遵守的规矩,我已经证明过我不记得。所以做成闸门。
# ---------------------------------------------------------------------------
import json, os
IDP = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'position_identity.json')
try:
    reg = json.load(io.open(IDP, encoding='utf-8'))['positions']
except Exception as e:
    bad = True
    reg = {}
    print(f'[FAIL] 读不到 position_identity.json ({type(e).__name__}) —— 身份闸门无法执行')

if reg:
    # __XXX__ 是框架/复盘条目(__MACRO__、__CUT_CALL_POSTMORTEM__ 等),不是可交易标的,
    # 没有法人实体可核 —— 豁免身份闸门。真实代码一个都不豁免。(2026-09-19 晚班加)
    def _is_framework(k):
        return k.startswith('__') and k.endswith('__')

    missing = [k for k in calls.MY_CALLS if k not in reg and not _is_framework(k)]
    if missing:
        bad = True
        print('[FAIL] 以下代码没有经核实的身份记录,不许写判断: ' + ', '.join(missing))
        print('       修法:用 IBKR search_contracts / 交易所 / 公司IR 核实后,'
              '把 legal_entity + adr_ratio + verified_by 写进 position_identity.json')
    incomplete = [k for k, v in reg.items()
                  if not v.get('legal_entity') or not v.get('verified_by')]
    if incomplete:
        bad = True
        print('[FAIL] 身份记录缺 legal_entity 或 verified_by: ' + ', '.join(incomplete))
    if not missing and not incomplete:
        print(f'[OK] 身份闸门: MY_CALLS {len(calls.MY_CALLS)} 个代码全部有一级源核实记录')

print('[FAIL] 存在问题,别提交' if bad else '[PASS] 可以提交')
sys.exit(1 if bad else 0)
