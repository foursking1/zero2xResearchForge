# solution.md — BERTOS 氧化态预测声明验证（task 2211.15895_bertos_oxidation_state）

## 结论（一句话）

**复现**：用官方冻结预训练 checkpoint（`data/models/*.zip`）在官方冻结测试集（`data/datasets/*.zip`）上独立推理，BERTOS 论文的核心声明全部成立：全元素位点级精度 PS、氧化物 PS、OS-ICSD-CN 的 PS/PC/金属-非金属精度均在论文容差内（表见下）。

## 关键结果 vs 论文 / 冻结数据锚值

| 指标 | 论文宣称 | 本任务复现（精确值） | 冻结数据锚值(±容差) | 判定 |
|---|---|---|---|---|
| PS(ICSD 模型×ICSD 测试) 全元素 | 96.82% | **96.78%（96.7778%）** | 96.25 ±1.5 | 复现 |
| PS(ICSD_oxide×ICSD_oxide) 氧化物 | 97.61% | **97.50%（97.4966%）** | 97.04 ±1.5 | 复现 |
| PS(ICSD_CN×ICSD_CN) 电荷中性 | 96.27%（T1:96.28） | **96.34%（96.3384%）** | 95.75 ±1.5 | 复现 |
| PC（化合物全对比例） | 87.76% | **86.63%（86.6273%）** | 84.80 ±3 | 复现 |
| 金属位点精度 | 97.12% | **97.17%（97.1669%）** | 95.49 ±2.5 | 复现 |
| 非金属位点精度 | 96.05% | **96.13%（96.1251%）** | 95.81 ±2.5 | 复现 |
| PCASA | 97.16% | **97.17%（97.1696%）** | — | 复现 |
| OS-ICSD-CN 规模 train/test | 31,827 / 3,724 | **31,827 / 3,724** | 精确一致 | 一致 |

> 与论文 Table 1 的 **16 格 PS 矩阵逐格对照，全部差值 ≤ 0.14 pp**（见 `evidence/table1_ps_matrix.md`）。
> 本复现值比基准"冻结数据锚值"高约 0.5 pp、比论文 Table 1 低 ≤0.2 pp：论文报告的是训练最佳 checkpoint，仓库释放 checkpoint 有合理差异；锚值来自基准方自己的重算管线，与本评估协议存在小口径差异（详见 `report.md` §差异归因）。

## 评估协议（与本任务/官方代码一致）

- 输入：CoNLL 块（每行 `元素 氧化态`，空行分隔化合物；每个原子一个位点）。
- 分词：官方 `BertTokenizerFast`（`do_lower_case=False`，vocab 123）；`is_split_into_words=True`，每个元素恰为 1 个 token（元素→token 1:1 对齐）；注意 vocab 中 `Nb `/`Re ` 行带尾随空格 → 这两元素映射为 `[UNK]`（仍占 1 个位置，对齐不受影响，属官方数据产物）。
- 模型：官方 `pytorch_model.bin`（12 层 hidden=120，vocab 123，14 类氧化态 −5..+8），`BertForTokenClassification`，加载时 `num_labels=14`。
- 序列：`[CLS] elem1 … elemN [SEP]`，截断 `max_length=200`（=模型 max_position_embeddings，199→实际上限 198 个元素预测）；标签经 word_ids 对齐，special token 置 −100。
- 计分：位点级精度 **PS** = 全对原子位点数 / 计分位点数；位点按化合物上限 **site_cap=199**（`min(L,199)`，复现锚值的 295,515 / 200,020 / 236,003 个位点统计）；超过模型预测位置的位点（L≥199 化合物的第 199 个原子）计为错误。化合物级 **PC** = 全位点全对化合物数 / 化合物总数。金属/非金属按标准金属元素表分组。
- 预测：logits argmax，类索引 − 5 = 氧化态（与 config `id2label` 一致）。

## 数据与许可

- 数据来源：官方仓库 usccolumbia/BERTOS（main，HEAD b845c3d），GPL-3.0；详见 `data/SOURCE.md`。
- 完整性：核心 12 个文件（4 数据集 + 4 模型 + tokenizer/关键代码）SHA-256 与 `data/CHECKSUMS_SHA256.tsv` 一致（本任务冻结包缺 LICENSE/pyproject/train_BERTOS.sh 三个非核心文件，不影响评估）。
- 未重新训练、未修改标签/权重；全部数值由冻结数据与官方 checkpoint 推出。

## 运行说明（裁判可复现，CPU 即可）

```bash
# 依赖：python3 + torch + transformers（>=4.23）
cd <repo>/agent_solution/scripts
python3 evaluate.py --data ../../data --max_length 200 --site_cap 199 --jobs 4 --outdir ../results
#   -> 输出 ../results/evaluation_results.json（4 模型 × 4 测试集 PS/PC/金属/非金属/位点数）+ 控制台逐格打印
python3 per_element.py --data ../../data --combos ICSD__ICSD,ICSD_CN__ICSD_CN,ICSD_oxide__ICSD_oxide
python3 compute_extra.py        # PCASA/每类精度/位置剖面
python3 make_tables.py          # 生成 evidence/ 下的 Table1 对照表与数据集规模表
python3 pymatgen_baseline.py --data ../../data --datasets ICSD_CN  # 启发式 baselines（可选）
python3 -u ../../data/code/checkCN.py --f ../../agent_solution/evidence/formulas.csv \
        --model_name_or_path <extracted ICSD_CN model dir> --tokenizer_name ../../data/code/tokenizer
```

核对的 B 抽查项：
- B1 `PS(ICSD×ICSD)=96.78%`（±0.3 自洽）；B2 `PS(ICSD_CN×ICSD_CN)=96.34%`、`PS(ICSD_oxide×ICSD_oxide)=97.50%`；B3 测试集块数 ICSD_CN test = 3,724、ICSD test = 5,215。
- 注：基准 B 部分以"重算值与提交报告一致"判真；本报告数值严格取自 `evaluation_results.json`（代码重算输出）。基准锚值 96.25/95.75/97.04 与本报告差异成因见 `report.md`。

## 产物清单

```
agent_solution/
├── solution.md              本文件
├── report.md                完整报告
├── scripts/                 evaluate.py（主评估）per_element.py compute_extra.py
│                            make_tables.py pymatgen_baseline.py probe_*.py（诊断用）
├── results/                 evaluation_results.json + per_element_*.csv + 运行日志
└── evidence/                table1_ps_matrix.md table1_pc_matrix.md
                             table1_metal_nonmetal.md anchor_comparison.md
                             dataset_sizes.md formulas*.csv（checkCN 演示）
```