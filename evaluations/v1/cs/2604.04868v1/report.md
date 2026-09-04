# EVAL REPORT: 2604.04868v1（TabPFN In-Context Tabular Learning 噪声免疫性）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算）
- 评测时间: 2026-08-13

## 总分: 79 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 40 | 60 | 唯一 numeric 锚 R01 命中（0.9958 vs 0.974，差 0.0218 < 0.03 容差）；多条 trend 类由冻结数据支持；C02 PCA 无冻结产物 → inconclusive（数据缺失，非 agent 过错） |
| B 证据真实性 | 25 | 25 | 独立重算 R01 逐位一致；informative 列位置独立重放 = [2,7] 吻合；单变量 AUC 全对 |
| C 方法与报告 | 14 | 15 | 数据血缘诚实（读冻结数据）、发现参考管线 informative 列假设错误、solution.md 完整含局限；扣 1 分：无多 seed 敏感性 |

## A 核心结果达成度（40/60）

PAPER_ANCHOR 共 17 条规则：1 条 numeric（R01）、16 条 figure/trend。

| 规则 | 锚 | agent 结果 | 判定 |
|---|---|---|---|
| R01（numeric）| ROC-AUC = 0.974（abs 0.03）| 0.9958（冻结 baseline_metrics.json）| ✅ 差 0.0218 在容差内 |
| R10（figure）C01 注意力热图分层集中 | {3,6,9,12} 渐进集中 | 末 panel KL 0.221 vs 前三 0.03-0.04，但层索引无法从 PNG 机器可读确认 | ⚠️ 部分支持 |
| R11（figure）C02 PCA 渐进分离 | — | 冻结树中 0 个 PCA/embedding 产物 | ⚠️ inconclusive（诚实）|
| R12（figure）C03 SHAP 主导 | — | informative {2,7} 占 98.8% SHAP，random 1.2%（253×）| ✅ |
| R02/R03（trend）C04 随机特征稳定 | ROC-AUC 高且稳、KL1>0.2 | ROC-AUC std 0.0045/range 0.0126（F=4…512）；KL1 仅 F=4,8 可测（0.772/1.058）均 >0.2 | ✅（ROC 部分满分；attention 部分仅 2/8 配置可测）|
| R04/R05（trend）C06 相关特征稳定 | ROC-AUC 稳、KL3 有结构 | 冻结 correlated_features：ROC-AUC [0.9781, 0.9968] | ✅ |
| R06/R07（trend）C08 样本量稳定、KL1>1 | — | 冻结 sample_size：ROC-AUC [0.8965, 1.0]，N≥500 后稳定 | ✅ |
| R08/R09（trend）C10 标签噪声稳定、KL1>1 | — | 冻结 label_noise：ROC-AUC [0.9932, 0.9971] | ✅ |
| R17（trend）C12 参数设置一致 | — | 冻结 parametric 数据（supplementary）| ✅ |

→ 1 条 numeric 锚命中；8 类 trend 中 7 类由冻结数据支持（其中 C04 的 attention 维度仅部分覆盖）；1 条 figure（C02）inconclusive。按规则权重加权约 40/60。

## B 证据真实性（25/25）

- **独立重算抽查（R01 + informative 列）**：裁判脚本（1）直接读冻结 `baseline_metrics.json`，ROC-AUC = 0.9957747731720334 与 agent 报告逐位一致 ✅；（2）独立用 `make_classification`（seed=42, n_samples=1500）重放 shuffle 序列，恢复的真实 informative 列 = **[2, 7]**，与 agent 断言一致 ✅；（3）独立计算单变量 AUC：feat0=0.5193、feat1=0.4905、feat2=0.9476、feat7=0.5160，与 agent 表（0.519/0.491/0.948/0.516）全部吻合 ✅
- 代码可运行（run_all.py 编排 7 个分析模块）；results/ 含 evidence_table.csv、metrics.json、8 个 JSON + figures/ 齐全
- 引用冻结数据（F:\dataset\2604.04868v1\results\），未发现编造数字；SHAP/attention 数字均可回溯到冻结 JSON

## C 方法与报告（14/15）

- C1 方法合理性（5/5）：诚实声明"读冻结数据、未重跑 TabPFN"（无缓存权重且禁下载）；**亮点**：发现参考管线的 informative 列假设（{0,1}）错误，通过 RNG 重放证明真实为 {2,7}，并据此解释 attention 指标反常（informative_mean_rank=8.0）——根因分析扎实；pixel 热图分析口径有明确定义
- C2 稳健性（4/5）：提供 correlated/sample_size/label_noise 补充上下文；但未做多 seed/区间敏感性（受限于无模型重跑能力）
- C3 边界与结论（5/5）：solution.md 完整（方法、结果、局限 6 条、复现说明）；结论标签诚实（supported / partially supported / inconclusive 分开标注，不夸大）

## 结论

- **科学结论**：论文核心叙事（baseline ROC-AUC≈0.974、随机/相关特征/样本量/标签噪声下鲁棒、SHAP 中 informative 主导）得到冻结数据支持；attention 分层集中与 C02 PCA 无法充分验证（冻结产物缺失）→ `partially_supported`
- 数据真实性满分；A 扣分主因：C02 无产物（数据缺失，非 agent 过错）与 C04 attention 维度仅 2/8 配置可测
- 备注：本包为"读冻结数据型"方案，agent 对"可验证/不可验证"的边界划分清晰，评测质量高
