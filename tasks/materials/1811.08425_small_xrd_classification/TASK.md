# Task: 1811.08425_small_xrd_classification（L1 critical claim）

> Internal data root: `$PAPER_BENCH_DATA_DIR`. Run this card through `paperbench.py run`; verify the downloaded mirror with `$PAPER_BENCH_DATA_ROOT/checksums.sha256`.

## 元信息
- task_id: `1811.08425_small_xrd_classification`
- 层级: L1（critical claim，可证伪）
- 论文: Oviedo, F., Ren, Z., Sun, S., et al. *Fast and interpretable classification of small X-ray diffraction datasets using data augmentation and deep neural networks.* npj Computational Materials 5, 60 (2019). arXiv:1811.08425. DOI: 10.1038/s41524-019-0196-x
- 领域: materials（薄膜 XRD 物相分类）

## 问题（可证伪）
论文声称：在小样本**真实薄膜 XRD 数据集**上，采用「物理信息数据增强 + 全卷积网络（a-CNN）」路线，可在 5 折交叉验证下达到**空间群分类精度 ≈89%**（Case 3 口径：全部模拟谱 + 80% 实验谱训练、20% 实验谱测试），且**数据增强相对无增强带来显著精度提升**（论文称无增强 <60% → 增强后 89%）。

请使用本任务冻结数据（88 条真实实验薄膜 XRD 谱 + 7 个空间群标签；164 条作者发布的模拟训练谱）独立实现并验证该声明，回答：

1. **空间群分类的 5 折交叉验证平均精度（Case 3 口径）能否达到论文报告的 ≈89%？**
2. **物理信息数据增强（峰缩放 / 峰消除 / 图案平移）相对无增强是否带来论文声称的精度提升？**
3. （加分）**2θ 步长粗化到 0.16° 时，分类精度是否仍 ≥85%？**（论文基线步长 0.04°）

## 方向提示
- **数据构成**：`exp.csv` 为 88 条实验谱（2θ/强度交错两列一组，共 176 列）；`label_exp.csv` 为类别标签（0-6，映射见 `encoding.csv` 的 7 个空间群）；`theor.csv` 为 164 条模拟谱训练集（2θ/强度两列一组）。
- **预处理**：论文对原始谱做背景扣除 + Savitzky-Golay 平滑 + 归一化；可自行实现等价处理（`Experimental/*.xy` 为原始谱）。
- **数据增强**：论文 Eqs.1-3 —— ①随机峰缩放（周期性子集按因子 c 缩放）②随机峰消除（周期性子集置 0）③沿 2θ 轴随机小量平移；论文从模拟集与实验集各增强 2000 条。
- **网络**：论文 a-CNN = 3 层 1D 卷积（各 32 filters，kernel/stride 8/5/3）+ ReLU + 全局平均池化 + softmax；BCE loss；Adam；batch 128；早停（Keras/TF，可换等价框架）。
- **评估**：5 折交叉验证（固定随机种子），子集精度（subset accuracy）+ F1 micro/macro；注意**类别不平衡**（7 类实验样本数 4/17/1/13/4/2/47）。
- **关键检查**：数据增强只能基于训练折（防泄漏）；报告均值与标准差、随机种子。

## 数据说明
- 目录：`data/`（冻结，94 文件，约 17.5 MB）
- **来源**：论文作者官方 GitHub 仓库 PV-Lab/AUTO-XRD（https://github.com/PV-Lab/AUTO-XRD ，分支 master，2026-08-13 抓取）；即论文 Data availability 声明中的实验数据地址。
- **许可**：Apache-2.0（官方仓库 LICENSE，SPDX: Apache-2.0；文件 `data/LICENSE_APACHE2.txt`）。按 npj Computational Materials 数据政策与作者归属要求使用（使用需引用论文）。`theor.csv` 为作者随仓库以 Apache-2.0 发布的模拟粉末谱（源自受许可的 ICSD 晶体结构），**仅作为论文训练协议的组成部分**；评测对象仅为真实实验谱。
- **Checksum**：全部 94 文件 SHA-256 见 `data/CHECKSUMS_SHA256.tsv`；核心文件：
  - `exp.csv` 41a213b16a7119dab1727cb238a55012f507d575af7bcdc9eba9edba6fda9219
  - `label_exp.csv` 037e37246243376369f235b6266548d2bee8a2ac905571d997cc683658951bff
  - `encoding.csv` 4a72c443bdfed9b1d837d8439b607d849eddd041b3fae9b711a029500fcd6487
  - `theor.csv` dc78efb90cc7079002980fe6c68607e5a235db3eac0129f1a3ab935cf84bc09e
  - `label_theo.csv` 8c5f6601d8df956b30820daa0bebec206acec5c02bb4a0133ff158e59107803c
- **Schema**（详见 `data/SOURCE.md`）：
  - `exp.csv`：1499 行（2θ 10.04°–69.96°，步长 0.04°）× 176 列（88 谱 × [2θ, 强度] 两列一组），float64
  - `label_exp.csv`：88 行，列 0 = 空间群类别索引（0-6）
  - `encoding.csv`：0=Fm-3m, 1=I41mcm, 2=P21a, 3=P3m1, 4=P61mmc, 5=Pc, 6=Pm-3m
  - `theor.csv`：2126 行 × 328 列（164 谱 × [2θ, 强度] 两列一组），列名为空间群名
  - `label_theo.csv`：328 行（索引, 空间群名），与 theor.csv 列一一对应（作者格式）
  - `Experimental/<空间群>/*.xy`：88 条原始实验谱（2 列文本：2θ, 强度）

## 输出要求
1. **结论**：对 3 个问题给出明确回答（复现 / 部分复现 / 未复现），并与论文数值（89%、<60%→89%、0.16°≥85%）逐项对比。
2. **证据表**（`results/evidence_table`）：5 折逐折精度、均值±标准差、F1 micro/macro、增强消融（有/无增强）、（可选）步长粗化精度曲线。
3. **代码**：可运行脚本，能从冻结数据 `data/` 直接重算出证据表中的关键数值。
4. **报告**：方法、超参数、随机种子、与论文 Case 3 口径的差异、局限性。

## 数据铁律提醒
- 只用本任务冻结的真实数据；**禁止自行生成/合成其他模拟数据或伪造标签**。
- `theor.csv` 为论文训练协议组成部分（作者发布的模拟谱），仅允许用于训练；**测试与评测必须基于真实实验谱**（`exp.csv` / `Experimental/*.xy` + `label_exp.csv`）。
- 禁止把文件顺序、列索引、行号等非物理信息当作特征（不得用当前窗口标签当特征）。
- 数据 checksum 已固定（SHA-256）；报告中注明数据来源与许可。
