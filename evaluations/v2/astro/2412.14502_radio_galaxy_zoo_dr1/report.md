# EVAL REPORT v2: 2412.14502_radio_galaxy_zoo_dr1

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判 v2（deepseek-v4-flash）
- 评测时间: 2026-08-21

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | 逐项核对满分带：(i) 行数 FIRST=99602（落入 rubric [99602±3]）、ATLAS=583（落入 [583±2]）、合计=100185（落入 [100185±5]），均有 metrics.json 落盘证据；(ii) 唯一 FIRST 源=99146（落入 [99146±10]）、重复源 414/多余行 456 口径正确；(iii) CL min=0.65（落入 [0.65±0.01]）、median=1.0、mean=0.9416（落入 [0.90,0.98]）、CL<1 占 30.08%，且明确说明 reliability 0.83 需专家子集标定不可从本包重算（metrics.json 中 reliability_0_83_recomputable_from_package=false）；(iv) 多分量行级=16531（落入 [16531±150]）、唯一源级=16334（落入 [16334±150]），并与论文 16354 对比归因（Δ=-20/+177，版本+口径差，65 个 N_comp 不一致重复源）；(v) ATLAS N_comp>1=1；(vi) 四档结论 supported。所有数值均存在于 metrics.json/probe_numbers.json/evidence_table 落盘证据中，无仅散文无证据项，证据绑定满足，授予满分带 60。 |
| B 证据真实性/实际复现 | 40 | 40 | 磁盘证据扫描显示：文件总数=21，metrics.json、evidence_table.csv、evidence_table_first_unique.csv 等 9 个结果 CSV/JSON、可运行 .py 代码均在；证据文件内部数值与报告散文严格一致（如 first_rows=99602、first_unique_rgzid=99146、cl_min_first=0.65、first_ncomp_gt1_rows=16531、first_ncomp_gt1_unique=16334 同时落盘于 metrics.json 与 probe_numbers.json）；代码含 reproduce_three_numbers.py、__verify__.py 等重算与交叉校验脚本，属『有证据文件且数值与报告严格一致、可核对』最高档，证据真实性/实际复现授予 40 分（对应本版 B 满分带，且仅按两维计分时 B=40）。 |

## A 核心结果达成度（60/60）

逐项核对满分带：(i) 行数 FIRST=99602（落入 rubric [99602±3]）、ATLAS=583（落入 [583±2]）、合计=100185（落入 [100185±5]），均有 metrics.json 落盘证据；(ii) 唯一 FIRST 源=99146（落入 [99146±10]）、重复源 414/多余行 456 口径正确；(iii) CL min=0.65（落入 [0.65±0.01]）、median=1.0、mean=0.9416（落入 [0.90,0.98]）、CL<1 占 30.08%，且明确说明 reliability 0.83 需专家子集标定不可从本包重算（metrics.json 中 reliability_0_83_recomputable_from_package=false）；(iv) 多分量行级=16531（落入 [16531±150]）、唯一源级=16334（落入 [16334±150]），并与论文 16354 对比归因（Δ=-20/+177，版本+口径差，65 个 N_comp 不一致重复源）；(v) ATLAS N_comp>1=1；(vi) 四档结论 supported。所有数值均存在于 metrics.json/probe_numbers.json/evidence_table 落盘证据中，无仅散文无证据项，证据绑定满足，授予满分带 60。

## B 证据真实性/实际复现（40/40）

磁盘证据扫描显示：文件总数=21，metrics.json、evidence_table.csv、evidence_table_first_unique.csv 等 9 个结果 CSV/JSON、可运行 .py 代码均在；证据文件内部数值与报告散文严格一致（如 first_rows=99602、first_unique_rgzid=99146、cl_min_first=0.65、first_ncomp_gt1_rows=16531、first_ncomp_gt1_unique=16334 同时落盘于 metrics.json 与 probe_numbers.json）；代码含 reproduce_three_numbers.py、__verify__.py 等重算与交叉校验脚本，属『有证据文件且数值与报告严格一致、可核对』最高档，证据真实性/实际复现授予 40 分（对应本版 B 满分带，且仅按两维计分时 B=40）。

## 证据与重算说明

独立重算未执行（本裁判未实际运行提交代码，仅依据磁盘证据扫描与提交物内部交叉验证机制审查）。关键实测数（均来自落盘 metrics.json/probe_numbers.json）：FIRST 行数=99,602、唯一 RGZID=99,146、CL min=0.65、CL mean=0.9416、CL<1 占比=30.08%、行级 N_comp>1=16,531、唯一源级 N_comp>1=16,334、N_peaks>1=34,741、ATLAS 行数=583 且 N_comp>1=1、散列校验 sha256_validated=true。报告中的每个关键数均可追溯至对应落盘产物，未发现抄论文数字当实测或测试段泄漏。

## 结论

- **科学结论**: `supported`
- 亮点: 提交物在统计口径定义、双重口径多分量对比（行级/唯一源级）、以及 16,334/16,531 与论文 16,354 差异的归因上极其严谨（定位 65 个 N_comp 不一致的重复源并做去重顺序敏感性分析），且所有关键数均有 metrics.json/evidence_table 落盘支撑，代码含自动复核机制。
- 不足: 唯一可指出的保留点是本裁判未独立运行代码重算（独立重算未执行），评分依赖提交物自带的 __verify__.py 交叉验证声明与落盘产物的一致性；此外 reliability 0.83 因数据包限制无法重算，属于如实说明而非缺陷。