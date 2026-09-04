# 科研任务：检验「特征工程提升压电模量预测」与「GNN vs 传统 ML」关键论断（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id：`2111.05557_piezoelectric_ml`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Hu & Song, "Piezoelectric modulus prediction using machine learning and graph neural networks", Chemical Physics Letters 791 (2022) 139359（arXiv:2111.05557）
- 领域：materials / 材料信息学 / 压电材料性质预测

## 问题（可证伪）

论文核心论断：
1. **特征工程显著提升传统 ML**：随机森林（RF）仅用 Magpie 特征时 MAE=1.17 C/m²、R²=−0.509；逐级加入氧化态/结构/能量-磁性/弹性模量特征后 MAE 降 18.5% 至 0.953、R² 升 32.6% 至 −0.343。SVM 的 R² 从 0.043（Magpie）随特征增加持续上升（加氧化态+结构特征后 +117%），且 SVM 的 R² 在各特征集下始终为正，**SVM 明显优于 RF**。
2. **GNN 介于两者之间**：五折交叉验证中 CGCNN MAE=0.97439 C/m²（GNN 中最好）、SchNet MAE=1.34294 C/m²（最差）；所有 GNN 都劣于 SVM，但除 GATGNN 外略优于 RF。
3. 用训练好的模型对 Materials Project 中 12,680 个材料预测压电系数，报告 top 20 候选。

请基于冻结数据回答：

1. **数据统计**：解析 `Piezoelectric_renewed.csv`（1,705 个含压电模量材料，列：`Materials,Piezoelectric_Modulus,Crystal_Symmetry,mp_id`），报告压电模量分布（C/m²）与晶系分布。
2. **传统 ML**：用特征向量/组合式特征（Magpie 或元素统计特征，可复用 `feature_vectors.csv` 或自行构造）训练 RF 与 SVM（或等价核方法），报告 MAE/R²。至少对比「仅 Magpie/基础特征」与「加入更多特征」两个设置，验证 MAE 下降、R² 上升的方向性。
3. **GNN 对照（可选但加分）**：用 CGCNN 或轻量消息传递网络训练结构模型（可用 pymatgen 解析结构或直接对 mp_id 分组），报告 5 折 CV MAE。若无结构解析能力，可跳过并说明。
4. **验证论文论断**：结合自身结果给出四档结论，重点对照「SVM 优于 RF」「特征增加降低 MAE」「GNN 略优于 RF 但劣于 SVM」三个方向性论断。

- 结论标签：`supported` / `partially_supported` / `contradicted` / `inconclusive`。

## 数据说明

- 数据包：`data/`（冻结）→ 物理位置 `$PAPER_BENCH_DATA_DIR`（来源/许可/逐文件 SHA-256 见 `data/SOURCE.md` 与 `$PAPER_BENCH_DATA_ROOT/checksums.sha256`）。
- 文件：`Piezoelectric_renewed.csv`（1,705 材料标签）；`feature_vectors.csv`（论文特征向量，10 行×104,652 列，行为样本组）；`MP_allcompounds_synthesis_totalenergy.csv`（MP 全化合物 138,613 行，用于 12,680 材料扩展预测；含 `material_id,pretty_formula,final_energy,e_above_hull,band_gap,density` 等）；`README.md`（仓库说明）。
- 来源：论文官方 GitHub 仓库 `jeffreyhusc/PiezoelectricML`（公开）。
- 规模：~52MB；CPU 即可完成（RF/SVM 分钟级；CGCNN 训练约 1–3 小时视配置）。

## 方向提示（协议建议）

1. **标签**：目标 = `Piezoelectric_Modulus`（C/m²）。
2. **特征**：论文用 Magpie + 氧化态/结构/能量-磁性/弹性特征逐步堆叠；可简化用元素分数 + 元素统计属性（matminer 或手算），至少做「基础 vs 增强」两档。
3. **模型**：RF（sklearn）与 SVM/SVR（RBF 核，标准缩放）；固定随机种子，5 折 CV 或固定 80/20 划分并声明。
4. **指标**：MAE（C/m²）与 R²；报告五折均值±std。
5. **对照**：论文 Table 1/2 与 Figure 5 数值仅用于对照讨论，禁止抄作实测。

## 输出要求（提交物）

1. **`claim.md`**：问题判定（四档标签）与关键数字。
2. **`code/`**：完整可复现脚本（固定种子），从冻结数据读取并完成训练与评估。
3. **`results/evidence_table.csv`**：至少含列 `model,feature_set,split,metric,value`。
4. **`results/metrics.json`**：样本统计、各方法指标、论文锚对照、结论标签。
5. **`report.md`**：方法、结果、局限（特征差异/划分差异 vs 论文）。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据。
- 禁止手工抄写论文数字作为「实测结果」；所有指标必须运行代码得到。
- 论文数值只能用于对照讨论；不同方法必须在同一划分、同一评估协议下比较。
