# 持仓日报 —— 怎么跑、现在缺什么

建于 2026-08-15。你要的是「每天一份我持仓股的日报」,08:00 北京时间,发邮箱 + 存仓库。
代码已经写完并验证;**定时那一环现在是残的,残在哪、怎么补,下面写清楚。**

---

## 现状:每天准时会到,但拿不到当天的价

已建 Routine `trig_018NvTmCVvvgrbQCR3Bx4Xwg`(每日 UTC 00:00 = 北京 08:00,首次 8/17),
每次开一个全新云端会话跑日报,完成后把正文邮件发到 xiaoyi.d.lei@gmail.com,并把
`reports/YYYY-MM-DD_持仓日报.md` 提交进仓库。

**但那个云端会话有两条硬限制:**

1. **没有 IBKR 连接。** 建 Routine 时系统明确回了一句:该触发器**不携带任何 MCP connector**,
   因为定时会话继承不到交互授权。→ 拿不到实盘净值 / 杠杆 / 缓冲 / 持仓 / 成交明细。
2. **连不上任何行情源。** 该环境的网络策略实测挡住了 `qt.gtimg.cn`(腾讯)、`api.nasdaq.com`、
   `query1.finance.yahoo.com`、`stooq.com` —— 四个全部 HTTP 000。→ 连公开报价都取不到。

**所以每天到你邮箱的那份,第①②节(账户、逐仓)会是仓库快照里的数,不是当天的数。**

### 这不会被藏起来

`daily_brief.py` 对陈旧做了分级,故意让它难看:

| 快照距今 | 表现 |
|---|---|
| 0-2 天 | 顶部 ⚠️ 横幅 + 写明快照日期,「今日涨跌」列显示 `—`(不是 0) |
| **≥3 天** | **标题变成「⚠️ 无新数据」,正文第一句是 🛑 大标题,直说第①②节不是今天的数** |

理由写在代码注释里:一份每天准时到、数字却一个月没变的日报,和旧版 `wechat_push.py`
写死「建 MU 仓」是同一类错误的两种长相 —— **都是"看起来在更新"**。

### 仍然每天真变的部分

第③④⑤节不依赖行情,天天都是新的:

- **③ 在案未执行的 call + 各挂了几天**(≥5 天打 ⚠️,按 `EXECUTION_RATE_RULE` 必须重新论证或撤回)
- **④ 未来三周有确认日期的催化倒计时**(8/17 DeepSeek 涨价 → 8/20 SPCX 解禁 → 9/2 AVGO 财报 → 9/15 FOMC)
- **⑤ 记分牌**(我的 call 命中率与美元合计)

---

## 三条补法,按推荐顺序

### ① 从 claude.ai 的 Routines 界面重建(最省事,推荐)
你自己在网页上建的 Routine 可以挂 connector。把本文件末尾的 prompt 原样贴进去,
时间设 UTC 00:00,勾上 IBKR。**这样第①②节就有实盘数了**,行情仍取不到但 IB 自带持仓与价格,够用。
建好后把我建的那个删掉,避免一天两封。

### ② 放行一个行情域名
如果这个云端环境的网络策略能加白名单,加 `api.nasdaq.com`(`nav.py` 已经在用它取美股历史)
或 `qt.gtimg.cn`(`tencent.py` 用它,A股/港股/美股都覆盖)。加完 `daily_brief.py` 不用改,
它会自己走实时分支、横幅自动消失。

### ③ 本机 Windows 计划任务(数据最全,但笔记本得开着)
只有你本机同时拿得到 IB Flex 令牌(`ib_config.json`)和私有文件(`holdings.csv` / `account_risk.json`)。

```bat
cd /d C:\path\to\stockapp
py -3.12 daily_brief.py --save --push
```

`--save` 写 `reports/`,`--push` 走 Server酱发微信(需要 `server_chan.json` 或 `SERVERCHAN_KEY`)。
想要邮件而不是微信,就用 ①。

---

## 手动跑

```bash
py -3.12 daily_brief.py              # 打印,尝试取实时价
py -3.12 daily_brief.py --offline    # 强制走快照(调试用)
py -3.12 daily_brief.py --save       # 另存 reports/YYYY-MM-DD_持仓日报.md
py -3.12 daily_brief.py --push       # 发微信
```

## 日报里的数从哪来

| 节 | 来源 |
|---|---|
| ① 账户 | `heavy.load_account()` → `account_risk.json`(实盘)否则 `heavy.SNAPSHOT` |
| ② 逐仓 | `heavy.positions()` + `calls.MY_CALLS` 的评级 |
| ③ 在案未执行 | `heavy.execution_gap()` / `heavy.OPEN_CALLS` |
| ④ 催化 | `daily_brief.CATALYSTS`(**只登记已确认日期,猜的不许进**,过期自动消失) |
| ⑤ 记分牌 | `scorecard.score()` |
| ⑥ 风险雷达 | `risk_radar.all_risks()` |

**日报里没有一句写死的判断。** 出厂带闸门 `_gate()`:`BUY_SIDE_LOCKED` 为真时正文出现
建仓/加仓措辞就抛 `AssertionError`,宁可当天不发,也不发一份违反你自己 7/30 条款的日报。

## 每天要维护的只有一件事

**把 `heavy.py` 的 `SNAPSHOT` / `POSITIONS` / `PREV` 更新成当天的 IB 读数**(我每次开工都会做)。
其余全是算出来的。如果哪天日报标题出现「⚠️ 无新数据」,就是这一步没做。
