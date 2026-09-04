# 科研任务：Leak Proof PDBBind「时间分裂防泄漏」关键论断验证（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2308.09639_leakproof_pdbbind`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Leak Proof PDBBind: A Reorganized Dataset of Protein-Ligand Complexes to Facilitate Fair and Robust Benchmarking（arXiv:2308.09639）
- 领域：biomed / 药物发现 / 蛋白质-配体结合亲和力预测

## 问题（可证伪）

Leak Proof PDBBind（LP-PDBBind）论文的核心论断是：**传统 PDBBind 基准（refined set）按随机划分切分训练/测试，导致同一配体或同一靶点同时出现在训练与测试集中（时间泄漏），使结构基方法与序列方法在测试集上的表现被系统性高估**。论文按配体-靶点复合物的沉积时间（PDB deposit date）重新组织数据集，得到时间分裂（time-based split）的 LP-PDBBind 后，所有基线方法在测试集上的结合亲和力预测误差（RMSE，kcal/mol）普遍上升，而经过"时间重训练"的模型误差下降。

请基于冻结数据回答（三问）：

1. **泄漏程度**：在冻结的 LP-PDBBind 时间分裂数据中，训练/验证/测试三集之间是否存在"同一配体（Ligand ID）或同一靶点（UniProt ID）跨集重复"的泄漏？统计并报告重复数量与比例。
2. **时间分裂 vs 随机分裂的差异**：用同样的亲和力预测模型（如随机森林或深度模型）分别在「时间分裂」与「随机重分裂」两种划分下训练并评测，测试 RMSE 是否如论文所示出现方向性差异（时间分裂更严格 → 误差更高）？给出两套划分下的 RMSE 对比。
3. **核心锚复现**：在 LP test 集（CL2 非共价子集）上，复现至少一个基线方法（如 DeepDTA 或随机森林）的 RMSE，与论文报告值对照；并回答"时间泄漏是否显著高估了方法性能"这一论断在你复现范围内成立与否。

- 结论标签（四档之一）：`supported` / `partially_supported` / `contradicted` / `inconclusive`（可对三问分别给标签）。

## 数据说明

- 数据包：`data/`（冻结，来源/许可/checksum 见下与 `data/README.md`）
  - `LP_PDBBind.csv`：LP-PDBBind 全量亲和力数据（19,443 行）。关键列：`Ligand ID`、`UniProt ID`、`PDB ID`、`Time-based split`（train/val/test）、`PKI`（实验结合亲和力 pKd/pKi）、`CL2 complex type` 等（与官方仓库 `dataset/LP_PDBBind.csv` 一致）
  - `BDB2020+.csv`：论文 Table 2 使用的 Benchmark DataBase 2020+（BDB2020+）115 个复合物清单（含 `ligand`、`uniprot`、`pIC50`、`CL2 complex type`、`Time-based split` 等列）
  - `BDB2020+.tgz`：BDB2020+ 115 个复合物的 PDB 结构包（约 35 MB），用于复现结构基方法（可选）
- 来源：官方 GitHub 仓库 THGLab/LP-PDBBind（`dataset/LP_PDBBind.csv`、`dataset/BDB2020+.csv`、`dataset/BDB2020+.tgz`）
- 许可：UC Berkeley Regents 许可（教育/研究/非营利用途免费；`LICENSE.txt`）；底层 PDBBind 数据为学术公开数据
- SHA-256（固定不可变）：
  - `LP_PDBBind.csv` = `7BB4E54E66C0C58AB74263EDB8C2A2D677C2474CFC4AE4DEC1EB31A231B10F8A`
  - `BDB2020+.csv` = `9C1AA1E8E32852A267BF2BFA1955BD88347AAE3474E2DA54E9011BAC73E8FE7A`
  - `BDB2020+.tgz` = `8CC529F456CA33BCD5BE8AAB5D6578865FCC2844695D51D4E1E252105420EE6E`
- 划分规模（论文 §3.3 / Table 1）：train 11,513 / val 2,422 / test 4,860；test 中 CL2 非共价子集 2,171 条。

## 方向提示（协议建议，按此口径才能与论文锚对齐）

1. **划分**：以 CSV 中的 `Time-based split` 列为准（train/val/test），不要自行重切；随机分裂对照组请固定随机种子（如 0）并写入代码。
2. **泄漏检查**：分别按 `Ligand ID`、`UniProt ID` 统计跨 train/test（及 val）重复；论文的关键观察是传统随机划分下同配体/同靶点泄漏普遍，时间分裂下显著减少。
3. **亲和力模型**：至少实现一种可运行模型（推荐随机森林回归：以分子指纹/RDKit 描述符为特征，预测 `PKI`）；如需更接近论文 DeepDTA 基线，可用一维 CNN 编码 SMILES（小规模可跑即可）。评估指标用 RMSE（kcal/mol），并给出 Pearson R（可选）。
4. **报告口径**：CL2 非共价测试子集（2,171 条）为论文主要对照口径（Table 1）；BDB2020+（115 条）为结构基方法口径（Table 2）。

## 输出要求（提交物）

1. **`claim.md`**：三问的判定（四档标签）、失败条件、数据支持强度、关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从 `data/` 读取并重算全部指标（含泄漏统计、时间/随机划分对比、RMSE）。
3. **`results/evidence_table.csv`**：至少含列 `split_type,model,rmse_test_cl2_noncov,pearson_r`（每模型×每划分方式一行）；另附 `leakage_stats.csv`（按 ligand/uniprot 的跨集重复统计）。
4. **`results/metrics.json`**：测试样本数；时间分裂与随机分裂的 RMSE；论文锚对照（RMSE 与相对差 %）；结论标签。
5. **`report.md`**：方法（特征/模型/划分/泄漏检查）、结果、结论、局限（与论文口径差异：模型族、特征、是否用 BDB2020+ 结构等）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止用合成/模拟数据替代。
- 禁止手工抄写论文数字作为"实测结果"；所有指标必须运行代码得到。论文数值（Table 1/2/3）只能用于对照讨论。
- 模型训练与超参选择只允许使用 train（+val）划分；test 不得参与任何拟合或调参。
- 时间分裂是论文核心口径，不得用随机划分结果顶替主结论。