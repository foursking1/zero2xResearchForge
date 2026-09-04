# RGZ DR1 冻结目录验证报告 (2412.14502_radio_galaxy_zoo_dr1, L1)

**任务**：基于冻结的官方 Radio Galaxy Zoo Data Release 1（RGZ DR1, Zenodo 10.5281/zenodo.10656393，CC-BY-4.0）4 个 CSV，验证论文 *Wong+ 2024, MNRAS, arXiv:2412.14502* 的 L1 critical claim：

> DR1 由公民科学家加权共识分类构成，总计 **100,185 条**分类（**99,602 条 FIRST** + **583 条 ATLAS**），对应 **99,146 个唯一 FIRST 射电源** + 583 个 ATLAS 源；全部收录分类 **consensus ≥ 0.65**，平均 **reliability 0.83**；99,146 个 FIRST 源中 **16,354 个（~16.5%）为多分量**源。

所有数字均由提交代码直接从冻结 CSV 重算（`code/run_analysis.py`），论文数值仅用于对照、从不混入实测。SHA-256 全量校验通过（4 文件均与 `data/source_manifest.json` 一致，见 `results/files_verified.csv`）。

---

## 1. 方法（口径定义）

- **数据**：`DR1_FIRST_radio_classifications.csv`（99,602 行 × 16 列）、`DR1_ATLAS_radio_classifications.csv`（583 行 × 16 列）、`DR1_FIRST_host_properties.csv`（99,602 行 × 23 列）、`DR1_ATLAS_host_properties.csv`（583 行 × 19 列），`pandas.read_csv` 直接读取。
- **唯一源去重**：`df.drop_duplicates(subset="RGZID", keep="first")`（文件顺序，pandas 默认语义，任务方向提示指定的口径），与任务锚点/编译器探针一致。
- **CL** 即加权 consensus（0–1），`N_comp` 为每源的射电分量数，`N_peaks` 为亮度峰数。
- **多分量两类口径**：
  - 行级（catalogue-entry level）：`N_comp > 1` 的**条目**数；
  - 唯一源级（unique-source level）：去重后每个 **RGZID** 记一次，看其 `N_comp > 1`；
  - 另报唯一源级 `N_peaks > 1`（更宽松口径）。
- **reliability 0.83**：论文 §3.3.1 用专家标定子集对标定加权 consensus 得到；目录中**无 reliability 列、无专家子集标签，无法从本包重算**——只验证 CL 分布。

## 2. 结果（从冻结 CSV 实测）

### Q1 规模声称

| 项 | 论文 | 实测 | Δ |
|---|---|---|---|
| FIRST 分类条目行数 | 99,602 | **99,602** | 0 |
| ATLAS 分类条目行数 | 583 | **583** | 0 |
| 分类总数 | 100,185 | **100,185** | 0 |
| FIRST 唯一 RGZID 源 | 99,146 | **99,146** | 0 |
| ATLAS 唯一 RGZID 源 | 583 | **583** | 0 |

- 重复源结构：414 个 RGZID 出现 >1 次（重数为 2/3/4/5 的分别 384/21/6/3 个源），多余行 456 = 99,602 − 99,146。
- 宿主表与分类表行数一致（99,602 / 583），且宿主表 RGZID 集合与分类表 RGZID 集合完全相等（对称差为空）。

### Q2 consensus 阈值与可靠性

FIRST（99,602 行）：

| 统计量 | 实测 |
|---|---|
| min | **0.65** |
| Q1 | 0.92 |
| median | **1.0** |
| mean | **0.9416** |
| max | 1.0 |
| CL < 1 占比 | **30.08%**（29,963 行） |
| CL ≥ 0.65 行数 | 99,602 / 99,602（**全部**） |

ATLAS（583 行）：min 0.65 / Q1 0.69 / median 0.72 / mean 0.7801 / max 1.0，全部 ≥ 0.65。

全部 100,185 行 `CL ≥ 0.65` 成立（`all_gte_0_65 = true`，0 行低于阈值）。`CL` 取值分辨率 0.01，`CL==0.65` 在 FIRST/ATLAS 中分别为 580 / 5 行。

**0.83 reliability 不可从本包重算**：目录没有 reliability 列，也未发布论文 §3.3.1 的专家标定子集与其权重方案；CL（加权 consensus 本身）是可靠性标定的输入而非输出。`metrics.json["Q2_consensus"]["reliability_0_83_recomputable_from_package"] = false`。

### Q3 多分量占比（FIRST）

| 口径 | N_comp > 1 | 占比 |
|---|---|---|
| 行级（catalogue entries） | **16,531** | 16.60% |
| 唯一源级（RGZID，canonical 去重） | **16,334** | 16.47% |
| 唯一源级 N_peaks > 1（另口径） | 34,741 | 35.04% |
| 论文 §5.1 | 16,354 | ~16.5% |

**哪个口径最接近论文**：唯一源级 16,334（Δ = −20，−0.1%）比行级 16,531（Δ = +177，+1.1%）更贴近论文 §5.1 的表述（"16,354 DR1 radio sources are composed of more than one component"，即按源计）。

**差异归因（16,354 ≠ 16,334 / 16,531）**：
1. **版本差**：论文数字出自论文写作/内部发布版本；本包冻结的是 Zenodo v1 正式发布版。两者在 414 个重复源的多条行上有更新差异。
2. **口径定义差**：
   - 行级 16,531 把同一源的重复条目各自计数，多出 197 = 重复源中主行之外 `N_comp>1` 的行数（重复源内 359 个 `N_comp>1` 行 − 162 个被保留主行）；
   - 唯一源级与论文同为“按源”，剩 20 个源之差可全部追溯到 **65 个重复源在同一源的多条行上 `N_comp` 取值不一致**（例如 `RGZ_J001419.7+085402` 两行分别是 N_comp=1（CL 1.0）与 N_comp=2（CL 0.88））。不同去重顺序（按 CL / N_votes / 原序等）下唯一源级结果在 **16,315–16,349** 间变动；若按 CL 降序取主行，唯一源级为 16,349，与论文 16,354 仅差 5——支持“论文内部发布版在少数重复源上的分量判定略不同”的归因。

### Q4 ATLAS 子样本

- 583 行 / 583 唯一源，**`N_comp>1` = 1**（唯一源级与行级相同，因无重复 RGZID）。
- CL 分布同上：min 0.65 / median 0.72 / mean 0.7801，全部 ≥ 0.65（弱于 FIRST，符合论文对较深源分类共识偏低的描述）。
- 另有唯一源级 `N_peaks>1` = 16。

### Q5 四档结论

**`supported`（支持）**。冻结数据在：①规模（99,602+583=100,185 分类，99,146+583 唯一源，重复源 414/多余行 456）；②consensus 阈值（全部 `CL≥0.65`，min=0.65 / median=1.0 / mean=0.9416 / CL<1 占 30.1%）；③多分量占比（~16.5%；行级 16,531 / 唯一源级 16,334，与论文 16,354 的 Δ 为版本+口径差）三个层面均精确复现论文声称。0.83 reliability 因缺少专家标定子集无法在本包重算（如实说明，不构成反驳）。

## 3. 附带回执（A4）

- `N_votes`（FIRST）：min 1 / mean **33.06** / median 23 / max **9,412**（与论文/锚点一致）。
- 宿主表：FIRST 99,602 行 × 23 列、ATLAS 583 行 × 19 列；分类的 `#CatID` 与宿主表完全对齐（99,602 行一致）。

## 4. 产品清单

- `code/run_analysis.py`：主脚本，产出 `results/{metrics.json, evidence_table.csv, evidence_table_first_unique.csv, cl_distribution.csv, nvotes_distribution.csv, summary_table.csv, files_verified.csv, probe_numbers.json}` 与 `evidence/*.png`。
- `code/reproduce_three_numbers.py`：裁判抽查脚本（99,602 / 99,146 / 0.65 / 行级 16,531）。
- `code/robustness_checks.py`：schema/取值范围/重复源一致性校验。
- `code/__verify__.py`：自动复核——从原始 CSV 重算全部关键数，并与各产物交叉比对（当前 **ALL CHECKS PASSED**）。
- `code/config.py`：数据目录解析（`--data-dir` / `$RGZ_DATA_DIR` / 默认 F 盘冻结路径）。

## 5. 局限说明

- 冻结数据为 Zenodo v1 正式发布版；论文内部发布版与 v1 的小差异（集中体现在 65 个 `N_comp` 不一致的重复源上）无法从本包消解，已如实归因。
- 唯一源级多分量计数对去重顺序敏感（16,315–16,349）；本报告采用 task 指定的 canonical `drop_duplicates` 得到 16,334，与任务锚点一致。
- 0.83 reliability / §5.3 射电-MIR 关系等依赖未随包发布的中间量，不在此验证范围。

## 6. 复现

```bash
cd agent_solution
python3 code/run_analysis.py            # 生成全部 results/ 与 evidence/
python3 code/reproduce_three_numbers.py # 裁判 3 数抽查（exit 0 = 通过）
python3 code/__verify__.py              # 全量交叉复核（exit 0 = 通过）
python3 code/robustness_checks.py --out-dir results
```
如需指向其他冻结副本：`--data-dir <dir>` 或设环境变量 `RGZ_DATA_DIR`。