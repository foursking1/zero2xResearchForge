# SCORE_RUBRIC（私有，仅裁判/编译者可见）— 2305.05782_lotss_deep_source_class（L1）

> 用途：LLM judge 判分基准。禁止向作答 agent 暴露本文件与 PAPER_ANCHOR.md。
> 判定模型：Claude / GLM 等 LLM 均可；需运行提交代码做抽查重算。
> 数据：`F:\dataset\astro\2305.05782_lotss_deep_source_class\`（9 文件，SHA-256 已固定）。

## A. 核心结果达成度（60 分）

判定基准（PAPER_ANCHOR A1/A2/A3）：论文 Table 2 声称 81,951 源分五类，SFG 67.9%、RQAGN 9.1%、LERG 15.6%、HERG 2.1%、Unc 5.3%。编译器在冻结数据上用 `Overall_class` 逐类精确复现 Table 2，满分带可直接对齐论文数值。

| 分段 | 得分 | 判定条件（agent 报告的冻结数据口径数值） |
|---|---|---|
| 满分带 | **60** | （i）三场行数 31,610 / 31,162 / 19,179、总计 **81,951**（±3）；（ii）五类 × 三场计数与 Table 2 **全部精确一致**（±5）；（iii）百分比 SFG 67.9%±0.5pt / RQAGN 9.1%±0.5pt / Unc 5.3%±0.5pt；（iv）可靠分类率 ∈ [93%, 96%]；（v）ELAIS-N1 流量分箱单调下降 + 50% 交叉 ∈ [0.5, 2.5] mJy + 对论文「>90% 极限流量」与实测 84% 的差异归因；（vi）给出四档结论 |
| 半分带 | **30** | （i）（ii）正确但漏 (iii) 或 (v) 任一；或单场单类偏差 ≤1% 但未全部精确；或 (v) 方向正确但开关点/差异归因缺失 |
| 零分带 | **0** | 总计 ≠ 81,951（±10）或任一字段行数错位；或把论文 67.9% 直接抄作实测而无代码支撑；或列解析错误（如把 AGN_final 当 Overall_class） |

> 注：论文 Abstract「>90% 极限流量」与目录实测 84% 的差异（完整性修正/极限流量定义）是讨论点而非错误；agent 若正确归因，判分时视为满足 (v)。

## B. 证据真实性（25 分）

- 提交必须含**代码** + **证据表**（`results/evidence_table.csv`：至少逐类计数表 `field, class, n` + 流量分箱表 `field, flux_bin_uJy, n, n_sfg, frac_sfg`）+ `results/metrics.json`。
- 裁判**抽查重算 3 个关键数**（运行提交代码，从冻结数据重算）：
  1. 三场总计行数 = **81,951**
  2. ELAIS-N1 的 SFG 计数 = **22,720**
  3. 总计 RQAGN 计数 = **7,442**
- 计分：
  - 3 个抽查数均可从冻结数据 + 代码重算且与报告一致 → **25**（满分）。
  - 每个抽查数不可重算或与报告不一致 → 各扣 8–12 分。
  - 无代码或代码不可运行 → 扣 8 分；证据表缺列/不完整 → 扣 5–10 分。
  - 证据表数字无法从原始 FITS 行重算（抄数嫌疑）→ 该项 0–5 分。

## C. 方法与报告（15 分）

| 子项 | 分值 | 判定要点 |
|---|---|---|
| C1 方法合理性 | 5 | FITS 解析正确；`Overall_class` 口径正确（或由 AGN_final/RadioAGN_final 推导验证）；无模拟/合成数据 |
| C2 泛化与严谨性 | 6 | 三场逐类对照 Table 2；百分比与「94.7% 可靠分类」「SFG 2/3」一致性；流量分箱与开关点讨论；对「>90% 极限流量 vs 84%」的口径差异归因 |
| C3 报告与边界 | 4 | 结论用四档标签（supported/partially_supported/contradicted/inconclusive）；明确口径与局限；report ≤2 页可读 |

## 判定流程（judge 步骤）

1. 读 `TASK.md` → 确认提交物齐全（claim/code/evidence_table/metrics/report）。
2. 按 A 数值带对 agent 报告计数打分（60/30/0）。
3. 运行提交代码（Python 3.11+，fitsio/pandas 即可），从冻结数据重算抽查 3 数 → 打 B。
4. 依 C1–C3 打 C。
5. 总分 = A+B+C；将得分与理由写入评测报告（或 CALIBRATION.md 复测记录）。
