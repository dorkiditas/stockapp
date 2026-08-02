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

thin = [k for k, (r, b) in calls.MY_CALLS.items() if len(b) < 40]
if thin:
    print(f'[INFO] 正文<40字(可能覆盖不足): {", ".join(thin)}')
print('[FAIL] 存在问题,别提交' if bad else '[PASS] 可以提交')
sys.exit(1 if bad else 0)
