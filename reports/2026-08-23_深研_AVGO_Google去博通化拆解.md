# AVGO 深研:「Google 去博通化」到底是替代还是增量?(2026-08-23 · 一天一题挖穿)

> 为什么做这一题:AVGO 240 股 = 净值 65.9% 头号仓,周一在案动作 = NVDA 前减 100 回 140,
> 而这条裁定的承重叙事——"Google 去博通化三线并进,份额天花板被第三方合同画出"——**两个席位都没有查过 Marvell 到底拿的是哪个 socket**。
> 兄弟会话 8/22 深研引用的是 8-K 的 headline,我 8/23 补课时照抄共署。今天把 socket 拆开看,结论要修正。

## 一、Socket 地图(逐源核对后)

| Socket | 现任 | 挑战者 | 状态 |
|---|---|---|---|
| **TPU 主计算 die(训练旗舰)+ 先进封装设计** | **AVGO**(4 月已披露长约:未来数代 TPU,最晚至 **2031**) | — | **不在这次分流范围内** |
| HBM 集成 + 高速 SerDes | AVGO | MediaTek(336G→400G/2nm) | AVGO 在位;MediaTek 在 v9/v10 上逼近 |
| 网络交换 + PHY(Tomahawk/Jericho 系) | AVGO | — | 稳 |
| **TPU v9"Triggerfish"部分计算 die + CPU tile**(偏推理/成本优化变体) | — | **MediaTek**(量产约 2028 年初,EMIB 封装) | **这才是唯一真正的 die 级替代线** |
| 推理加速器 / 存储控制器 / NIC / 内存接口 / 近存计算(**生态外围**) | 无在位者(多为新增 socket) | **Marvell**(7/29 签约,8/19 披露) | **增量为主,不是从 AVGO 手里抢** |
| TPU v10 某变体(传闻) | — | AMD(在谈,未确认) | ⚠️ 单源传闻,标观察 |

**8-K 原文的措辞是关键**:Marvell 的范围是 "custom silicon programs that **attach to the TPU ecosystem**"——挂在 TPU 生态上的外围件。多家独立源一致:**"Marvell 拿外围,博通保留核心计算芯片;核心计算芯片不在这次分流之内。"** BOM 里价值最高的四块(核心 ASIC+封装、HBM 集成、SerDes、网络交换/PHY)全部仍在 AVGO 手里。Digitimes 的读法甚至相反:**这笔长约"挡住的是博通被整体替代、限制的是联发科的扩张"**——Marvell 把外围拿走,联发科向外围扩张的路也被堵了一段。

## 二、那 $120B 是谁的天花板?——我 8/23 上午写错的一句,当场改

warrant 结构:5,897 万股 @ $206.58,Google 每采购 **$5 亿 Marvell 定制产品** vest 一档、共 240 档 = 累计 **$1,200 亿、至 FY2033**(另有 136 万股按时间 vest)。

**→ 这 $120B 是 Marvell 自己的收入 vesting 上限,不是从 AVGO 盘子里划走的份额。**我上午在档案里写"博通在 Google 未来支出里的份额天花板被第三方合同画了出来"——**措辞过重,撤回换成准确版**:被画出天花板的是 **AVGO 的增量空间**(外围 socket 本可以是它的 content 扩张方向,现在归了 Marvell),不是它的存量核心。

## 三、修正后的风险表述(替换"三线并进")

1. **真正的 die 级威胁只有一条线:MediaTek**,兑现窗口约 2028(v9 推理变体量产),v10 在争。不是三条。
2. **Marvell 线的实质 = Google 的多源采购战略**:按 socket 分包、让供应商逐段竞争、再用 warrant 把供应商利益绑上船。**它的杀伤机制不是份额悬崖,是续约谈判时的毛利率挤压**——Google 手里从此有了"每一段都有备选"的谈判筹码。盯守项从"份额"改为:**AVGO 对 Google 业务的毛利率趋势(10-Q/财报口径)**。
3. AMD 线 = 单源传闻,只登记不承重。
4. 35-40% 单一客户集中度这条**原样保留**——多源化不改变它,只改变它恶化的方式(慢刀,不是断崖)。

## 四、对周一裁定的影响:动作不变,理由修正

**减 100 回 140 维持不变**——因为这条裁定的承重从来不该是"去博通化",而是:
① 65.9% 单仓 + 2.81x 杠杆 + 缓冲 7.7%,SPCX/QCOM/CBRS 同向,8/26 NVDA 一份 print 可以同时打穿四仓;
② $394 加仓价已破 $370 自设止损线;
③ S&P 对 XPV 的 credit negative 半触发仍在。
**但修正后的叙事改变"之后怎么办"**:若 NVDA print 过关、9/2 财报重申 FY27 >$1,000 亿、10-Q 把 XPV 披露清楚——**140 股核心仓的论文在 Marvell 新闻下比我们档案原先写的更完整**,8/19 的 -4.6% 里有一部分是市场(和我们)把"外围分包"读成了"核心分流"。

## 五、这一课的元教训(记我名下)

兄弟会话把 8-K headline 当"第三条替代线",我复核共署时**没有打开 8-K 看 scope 那一行**。两个席位、同一个错、互相引用对方当确认——**这就是"转录不是研究"的标本**:转录了三家券商、两份班报,不如自己读一段 8-K 原文。铁律 2(价格与日期当场实拉)之外补一条个人规矩:**凡是承重叙事,落笔前先问"我看过原始文件的哪一行"。**

### 来源
- [Marvell 8-K(8/19,SEC 原文)](https://www.sec.gov/Archives/edgar/data/0001835632/000119312526356217/d412696d8k.htm) · [CNBC:Marvell +10%,Google 获 $12.2B warrant](https://www.cnbc.com/2026/08/19/marvell-google-ai-chips.html)
- [Digitimes:Marvell 长约挡住博通被替代、限制联发科影响](https://www.digitimes.com/news/a20260821PD211/marvell-google-mediatek-broadcom-chips.html) · [The Register:Google 让 Marvell 与博通竞争](https://www.theregister.com/off-prem/2026/08/19/google-pits-marvell-against-broadcom-as-it-chases-ai-crown/5289902)
- [TrendForce:Marvell/AMD 搅动 TPU 竞局,博通与联发科承压](https://www.trendforce.com/news/2026/08/20/news-marvell-amd-reportedly-shake-up-google-tpu-race-putting-broadcom-mediatek-under-pressure/) · [TrendForce:MediaTek 400G SerDes/2nm 争 TPU v10](https://www.trendforce.com/news/2026/08/03/news-mediatek-advances-400g-serdes-on-2nm-targeting-google-tpu-v10-and-meta-ai-asic-orders/)
- [Jon Peddie:Ironwood 四方(Google/Broadcom/MediaTek/TSMC)](https://www.jonpeddie.com/news/ironwood-chetyorka-google-broadcom-mediatek-and-tsmc/) · [Futurum:Marvell attach 全栈与 $120B vesting](https://futurumgroup.com/insights/marvell-attaches-across-googles-tpu-stack-with-a-warrant-vesting-toward-120b/) · [TheNextWeb:与博通 TPU 项目并行的推理芯片](https://thenextweb.com/news/google-marvell-ai-chips-inference-tpu-broadcom)

*Max · Alpha Desk 副CIO · 2026-08-23 · 深研 AVGO 专篇(二)*
