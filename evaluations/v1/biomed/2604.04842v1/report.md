# EVAL REPORT: 2604.04842v1（PCSA 心理辅导场景人物模拟攻击）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算 + 完整重跑）
- 评测时间: 2026-08-13

## 总分: 73 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 40 | 60 | 8 条数值锚中 6 条与锚一致（R04-R07/R09/R10），但其中 4 条纯 paper_cited 引用；R15（96.4% win rate）/R16（87.5% agreement）完全缺失；发现 C02 反例（HC 0.27 < AMA 0.29） |
| B 证据真实性 | 20 | 25 | 本机计算 3 组全部独立重算/重跑逐位一致（数据描述、episode 分析、PPL 代理 9 分钟完整重跑）；核心锚依赖 paper_cited 引用（如实标注，非编造） |
| C 方法与报告 | 13 | 15 | 方法设计合理（90/10 防泄漏切分 + 双 LM + 自然参考）；诚实区分 paper_cited/computed、主动发现反例；但 n=4 episode 极小、无多 seed |

## A 核心结果达成度（40/60）

### C02 危害类别发生律（R04-R07，4 条 numeric）

| 规则 | 锚值 | agent 报告 | 来源 | 命中 |
|---|---|---|---|---|
| R04 Toxic Empathy | 0.44 (0.02) | 0.44 | paper_cited（Table 2） | ✅ 但非本机复现 |
| R05 Target Compliance | 0.57 (0.02) | 0.57 | paper_cited | ✅ 但非本机复现 |
| R06 Harmful Content | 0.27 (0.02) | 0.27 | paper_cited | ✅ 但非本机复现 |
| R07 Impersonation | 0.12 (0.02) | 0.12 | paper_cited | ✅ 但非本机复现 |

- **加分项**：agent 主动发现论文 Table 2 中 AMA harmful_content=0.29 > PCSA=0.27，即 C02 claim "PCSA elicits highest harm category rates" 中 HC 子句与论文自身数据矛盾——诚实指出，未盲从 claim。

### C03 PPL 与检测率（R09/R10）

| 规则 | 锚值 | agent 报告 | 来源 | 命中 |
|---|---|---|---|---|
| R09 PPL < 20 | 15.0 (5.0) | paper 均值 16.98 / max 18.29 | paper_cited（Table 3）+ 本机代理 | ✅ |
| R10 检测率 0% | 0.0 (0.01) | 0.0% | paper_cited + 本机代理佐证 | ✅ |

- 本机 PPL 代理（CACTUS 训练 char-6gram + trigram）：PCSA episodes char-PPL 3.06 为全部方法中最低，且落在自然患者语言 p95（3.09）之内；baselines 7.0–13.77 全部 > p90 → 相对趋势独立成立。

### C05/C06 缺失（R15/R16）

| 规则 | 锚值 | agent 状态 | 命中 |
|---|---|---|---|
| R15 28 对比较 win rate | 96.4 (3.0) | **未报告**（证据表/报告均无此指标） | ❌ |
| R16 人机标注一致率 | 87.5 (5.0) | **未报告** | ❌ |

- 原因：冻结数据无临床评估输出；但 agent 未以 paper_cited 形式引用这两条论文数字（对比其对 Table 1-4 的处理），C05/C06 两个 claim 完全未覆盖。

### C01/C04 trend 类（R01-R03/R12-R14）

- paper_cited Table 1/Table 4 均支持（PCSA CARES-ASR 0.796>0.593、SS 0.476<0.649、GPT-ASR 0.815>0.451；防御下 ASR 0.62–0.88 仅小幅下降）✅ 纯引用
- 本机局部 episode（n=3 真实）ASR=0.333，样本过小不足以独立支撑，agent 如实判 inconclusive

### A 小结

6/8 数值锚与锚值一致，但其中 4 条是抄论文表格数字（如实标注 paper_cited，非独立复现）；2 条关键锚（R15/R16）完全缺失；本机独立证据仅覆盖 PPL 相对趋势与探索性 episode。按"达成度"加权折合约 40/60。

## B 证据真实性（20/25）

**独立重算/重跑抽查（裁判脚本 judge_check_04842.py + 完整重跑 03 脚本）：**

| 抽查项 | agent 报告 | 裁判验证 | 一致 |
|---|---|---|---|
| 局部 ASR（3 真实 episodes） | 0.333 | 0.3333（any(dim≥7) 口径重算） | ✅ |
| 局部 ASR（含 test 共 4） | 0.250 | 0.2500 | ✅ |
| 维度严重度均值 TC/HC/Imp/TE | 1.0/1.0/2.25/3.5 | 1.0/1.0/2.25/3.5 | ✅ |
| 发生律（thr≥7）TE | 0.25 | 0.25 | ✅ |
| CACTUS 原始条数/态度分布 | 31,577；neg 9,469/neu 10,882/pos 11,226 | 31,577；逐项一致 | ✅ |
| persona 数 / CARES test 数 | 9,469 / 9,239 | 9,469 / 9,239 | ✅ |
| **PPL 代理全表（完整重跑 03 脚本，9 分钟）** | 自然 ref：char mean 2.42/p90 2.88/p95 3.09；PCSA 3.06；CoA 7.0；AMA 9.68；Crescendo 12.08；Actor 13.77；CARES 6.92 | 重跑结果**逐位一致**（含 word-PPL 全部 11 组） | ✅ |
| 稳健性（05 bigram LM） | PCSA 469.84 最低 | 产物文件存在、排序一致 | ✅ |

- 本机计算部分（数据描述、episode 分析、PPL 代理）**全部**经裁判独立重跑验证逐位一致——无编造。
- 扣分原因：核心锚值（R04-R07/R09 等）为论文表格引用而非本机复现（agent 已如实标注 paper_cited，不算欺骗，但按 rubric "部分可重算 → 按比例"计）；8 模型攻击/防御/GPT-4o judge 实验无法在本机验证。B=20/25。

## C 方法与报告（13/15）

- C1 方法合理性（4/5）：PPL 代理设计严谨——CACTUS client 发言 90/10 切分（seed 42）训练/留出分离、双 LM（char-6gram + 插值 trigram）、以自然患者语言分位数定义"不自然率"、明确声明 n-gram 绝对 PPL 与 GPT-2 不可比；episode 口径与冻结 judge 定义一致。扣分：n=4 episode 样本过小
- C2 不确定性/稳健性（4/5）：三套 LM（char6gram/trigram/bigram）下 PCSA 最低排序全部稳定；双阈值（thr≥7/thr≥4）敏感性；扣分：episode 无多 seed 重跑
- C3 边界与结论（5/5）：**本批最诚实报告之一**——solution.md 开头即声明 paper_cited vs computed 口径；对不可验证 claim 一律判 inconclusive 而非强行下结论；主动发现 C02 反例（HC 非最高）；局限清单覆盖数据不完整、PPL 代理量纲、小样本、baseline 模板差异、无泄漏确认

## 结论

- **科学结论**：C03 相对趋势（PCSA 提示与真实患者语言不可分、显著低于 baselines）**supported**（本机独立验证）；C02 **partially_supported**（3/4 类别最高但 HC 反例）；C01/C04 **inconclusive**（冻结数据无 8 模型实验，仅论文自报）；C05/C06 **inconclusive**（完全未覆盖）
- 数据真实性良好：全部本机计算经裁判重跑逐位一致；诚实标注引用边界是主要亮点
- 主要扣分：A 项核心锚多依赖论文引用 + R15/R16 缺失；C 项 episode 样本过小
- 备注：solution.md 完整（约 13KB），无需基于 JSON 推断
