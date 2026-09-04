# SCORE_RUBRIC（私有，仅裁判/编译者可见）— 2308.05572_gaia_wd_xp_class（L1）

> 用途：LLM judge 判分基准。禁止向作答 agent 暴露本文件与 PAPER_ANCHOR.md。
> 判定模型：Claude / GLM 等 LLM 均可；需运行提交代码做抽查重算。
> 数据：`F:\dataset\astro\2308.05572_gaia_wd_xp_class\`（2 文件，SHA-256 已固定）。

## A. 核心结果达成度（60 分）

判定基准（PAPER_ANCHOR A1/A2/A3）：论文声称 100,886 个白矮星候选、89,188 个 high-confidence（11,698 uncertain）、逐类计数 DA 77,330 / DB 5,688 / DC 4,082 / DO 215 / DQ 601 / DZ 1,272（Table 2）。编译器在冻结数据上用「SpType 无冒号」口径**逐类精确复现** Table 2 与 89,188/11,698。因此满分带可直接对齐论文数值。

| 分段 | 得分 | 判定条件（agent 报告的冻结数据口径数值） |
|---|---|---|
| 满分带 | **60** | （i）总行数 = **100,886** 且唯一 GaiaDR3 源数 = 100,886；（ii）六类 high-confidence 计数**全部**落入 Table 2 ±50（即 DA∈[77,280,77,380] 等；相对差 ≤0.07%），总数 = 89,188 ±10，uncertain = 11,698 ±10；（iii）报告 DA 占比 ∈ [76.0%, 77.3%]（论文 76.65%），high-confidence 占比 ∈ [87.9%, 88.9%]（论文 88.40%）；（iv）同时报告 SpType 与 argmax 两种口径并解释差异（舍入）；（v）Teff=-999 与 DA Teff>300,000K 计数如实报告并与论文 §4.2（1,080 / 34）做漂移讨论 |
| 半分带 | **30** | 六类计数相对差 ≤5% 且总数 |Δ| ≤1%；或漏掉 (iv)/(v) 任一要求但数字正确；或 DA 占比 ∈ [74%, 79%] |
| 零分带 | **0** | 总数 ≠ 100,886（±1）或 DA 计数偏离 >10%；或直接抄论文数字而无代码支撑；或把 argmax 口径误当 high-confidence（会得到 DA 83,963 ≠ Table 2）且未做任何交叉验证 |

> 注：论文正文 "Feeding the 101,783 objects" 为笔误（与「100,886」及目录行数矛盾），以目录行数 100,886 与 ReadMe Records 为准；agent 若指出该不一致可加分讨论但不强制。

## B. 证据真实性（25 分）

- 提交必须含**代码** + **证据表**（`results/evidence_table.csv`：至少 `class, n_high_conf, n_uncertain, n_argmax, frac_high_conf`）+ `results/metrics.json`。
- 裁判**抽查重算 3 个关键数**（运行提交代码，从冻结数据重算）：
  1. 总行数 = **100,886**
  2. DA high-confidence 计数 = **77,330**（SpType 无冒号）
  3. `Teff = -999` 行数 = **1,396**（冻结目录值；论文 §4.2 为 1,080，属版本漂移，重算以冻结数据为准）
- 计分：
  - 3 个抽查数均可从冻结数据 + 代码重算且与报告一致 → **25**（满分）。
  - 每个抽查数不可重算或与报告不一致 → 各扣 8–12 分。
  - 无代码或代码不可运行 → 扣 8 分；证据表缺列/不完整 → 扣 5–10 分。
  - 证据表数字无法从 pred/actual 类原始记录重算（抄数嫌疑）→ 该项 0–5 分。

## C. 方法与报告（15 分）

| 子项 | 分值 | 判定要点 |
|---|---|---|
| C1 方法合理性 | 5 | 定宽解析正确（按 ReadMe 字节区间）；规则透明（SpType 冒号 vs max(P)≥0.65 均说明）；无模拟/合成数据 |
| C2 泛化与严谨性 | 6 | 两种口径交叉验证；与论文 Table 2 逐类对比并归因差异（舍入/版本）；对 1,396 vs 1,080、68 vs 34 做漂移讨论 |
| C3 报告与边界 | 4 | 结论用四档标签（supported/partially_supported/contradicted/inconclusive）；明确口径与局限；report ≤2 页可读 |

## 判定流程（judge 步骤）

1. 读 `TASK.md` → 确认提交物齐全（claim/code/evidence_table/metrics/report）。
2. 按 A 数值带对 agent 报告计数打分（60/30/0）。
3. 运行提交代码（Python 3.11+，gzip/pandas 即可），从冻结数据重算抽查 3 数 → 打 B。
4. 依 C1–C3 打 C。
5. 总分 = A+B+C；将得分与理由写入评测报告（或 CALIBRATION.md 复测记录）。
