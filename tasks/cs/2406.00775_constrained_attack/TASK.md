# 科研任务：表格数据的约束自适应对抗攻击（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

- task_id: `2406.00775_constrained_attack`
- 层级：L1（critical claim，论文锚 + LLM 裁判）
- 论文：Constrained Adaptive Attack: Effective Adversarial Attack Against Deep Neural Networks for Tabular Data（arXiv:2406.00775）
- 领域：CS / 表格机器学习 / 对抗鲁棒性

## 问题（可证伪）

论文提出约束自适应梯度攻击 CAPGD（在 CPGD 基础上加入自适应步长、repair 算子、随机初始化和动量），并报告核心结论：**在表格数据上，CAPGD 显著优于既有梯度攻击（CPGD / LowProFool）——以 URL（钓鱼 URL 检测）数据集为例，深层模型的鲁棒准确率从 CPGD 的 ~88–93% 降至 CAPGD 的 ~11–73%（5 个架构中 3 个 ≤ 20%）；CAA（CAPGD+MOEVA 组合）进一步把鲁棒准确率压到 ~9–58%（Table 3）。**

可证伪表述：基于冻结的 URL 数据，(a)「CAPGD 的鲁棒准确率比 CPGD 至少低 40 个百分点」在至少一个深层表格模型上是否成立；(b)「CAPGD < CPGD 的方向在多个（≥2）模型上一致」是否成立。

## 方向提示（非方法步骤）

- 指标：鲁棒准确率（%），越低越好（攻击越有效）；论文定义：攻击后仍被正确分类（或攻击生成无效样本——视为被正确分类）的干净样本比例。报告 clean accuracy 作为对照。
- 数据：本包冻结 URL 数据集（`data/url.csv`，11,430 行 × 64 列 = 63 特征 + `is_phishing` 标签）。关键类（critical class）= phishing（`is_phishing=1`，约 50%）；**只攻击关键类中已被模型正确分类的干净样本**（与论文一致）。
- 攻击设置（论文 §5）：L2 范数距离，ε = 0.5；特征/域约束见 `data/url_features.csv`（每特征 min/max 边界）与 `data/url_constraints.md`（14 条关系/线性约束）+ `data/url_constraints_reference.py`（参考实现）。
- 模型：训练 ≥2 个深层表格分类器（可从论文的 TabTransformer / TabNet / RLN / STG / VIME 中选，或等价深层 MLP/Transformer；须在报告说明架构与训练细节）。训练/验证划分由你定（固定种子），但测试划分必须与攻击评估一致并全程冻结。
- 攻击实现：实现 (1) 一个约束感知的梯度攻击基线（CPGD，论文 §4 描述其缺陷：固定步长、无 repair、单初始点）；(2) CAPGD（论文 Algorithm 1：自适应步长 η0=2ε、检查点 halving（ρ=0.75）、repair 算子 R_Ω、双初始点（原始 + 随机）、动量 α=0.75）。两者共享同一约束集与投影。
- 防泄漏：模型只用于分类；攻击只使用测试集（干净）样本与其预测；约束/特征边界来自冻结数据包，不得重新从外部下载。

## 数据说明

- 数据包：`data/`（冻结真实数据；来源/许可/checksum 见 `data/SOURCE.md` 与 `data/source_manifest.json`）
  - `url.csv`：URL 数据集（ISCX-URL2016），63 特征 + `is_phishing`（0/1）
  - `url_features.csv`：63 特征元数据（type / mutable / min / max）——边界约束
  - `url_constraints.md` + `url_constraints_reference.py`：14 条关系/线性约束（g1–g16）
- 来源：与 CAA 论文同团队的公开数据/约束（TabularBench HF 镜像 + constrained-attacks GitHub，均 MIT）；特征顺序与论文一致（63 特征，Table 5 的 11,430 / 63 / 50-50 完全吻合）。
- 许可：MIT（TabularBench/constrained-attacks 仓库）/ ISCX-URL2016 派生，学术研究用途。
- checksum（sha256）：见 `data/source_manifest.json`。

## 输出要求（提交物）

1. **结论**：对 claim (a) 与 (b) 分别给出 `supported / partially_supported / contradicted / inconclusive`，并说明数据支持的强度。
2. **证据表**：`results/evidence_table.csv`，至少含列：`model`、`clean_acc`、`robust_acc_cpgd`、`robust_acc_capgd`、`n_attacked`（攻击的干净关键类样本数）、`constraint_satisfaction_rate`（CAPGD 生成样本满足约束的比例）。
3. **代码**：完整可复现的模型训练 + 两种攻击 + 评估脚本（固定随机种子），从 `data/` 读取冻结数据与约束。
4. **报告**：`report.md`：模型架构与训练细节、攻击实现（与 Algorithm 1 的对应关系）、约束处理（边界 + 关系约束如何投影/repair）、ε/范数口径、防泄漏说明、局限性。

## 数据铁律提醒

- 只使用本包冻结数据；禁止合成/模拟数据替代；禁止从网络下载其他 URL 版本或约束集。
- 测试集（攻击评估）只用于最终评估；模型训练不得使用攻击评估同一切分的样本（采用独立划分或仅在训练/验证集上训练，测试集全程冻结）。
- 鲁棒准确率必须按论文口径计算（无效样本视为被正确分类）；约束满足率必须报告。
- 禁止把论文数值当作"本实验实测"；所有指标必须由你的代码从本包数据算出。