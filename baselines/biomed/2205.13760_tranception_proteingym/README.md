# README — ProteinGym 零样本突变效应预测复现

任务 `2205.13760_tranception_proteingym` 的 agent 解决方案：验证 Tranception/ProteinGym
(LM 零样本突变效应预测优于简单基线) 的主论断。

## 目录
```
agent_solution/
├── claim.md           结论标签 (supported) 与关键数字
├── solution.md        方法/结果速览
├── report.md          完整报告（方法、结果、局限）
├── code/
│   ├── common.py               共享工具（CSV 解析、target_seq、BLOSUM62）
│   ├── 00_explore_data.py      数据核验 -> results/exploration_summary.json
│   ├── 01_score_lm.py          ESM-2 掩码边际评分（tables / joint 两模式）
│   ├── 02_score_baselines.py   BLOSUM62 等非 LM 基线
│   ├── 03_evaluate.py          Spearman ρ + metrics.json + evidence_table.csv
│   └── 04_make_figures.py      出图
└── results/
    ├── evidence_table.csv      列: assay,uniprot_id,method,spearman_rho,n_variants
    ├── metrics.json            per-assay rows, method agg, 结论标签, 论文锚对照
    ├── exploration_summary.json
    ├── lm_scores/{tables,joint}/{model}/{assay}.csv    逐变异 LM 分数
    ├── baseline_scores/*.csv                           逐变异基线分数
    └── figures/*.png
```

## 复现命令
```bash
# 依赖（Python 3.12；torch 2.x, pandas, numpy, scipy, transformers>=4.45, huggingface_hub）
pip install torch pandas numpy scipy transformers==4.45.0  "huggingface_hub<0.36"

# 1) 数据核验
python code/00_explore_data.py

# 2) 基线打分（秒级）与 LM 打分（650M 需要 GPU ~10-20 分钟；8M 更快）
python code/02_score_baselines.py
python code/01_score_lm.py --mode tables --models esm2_t33_650M,esm2_t6_8M --device cuda
#    GFP 多点变异的联合掩码保真校验（可选；约 15 分钟）
python code/01_score_lm.py --mode joint --models esm2_t33_650M --device cuda \
       --assays GFP_AEQVI_Sarkisyan_2016

# 3) 评估：Spearman ρ、evidence_table.csv、metrics.json
python code/03_evaluate.py

# 4) 图表
python code/04_make_figures.py
```

无 GPU 时 `--device cpu`（8M 模型完全可行；650M 会明显变慢）。模型权重首次运行时从
HuggingFace Hub 下载（允许；仅权重，非评测数据）。所有随机源固定种子（null 基线 seed=1234）。

## 关键结果
- ESM-2 650M（主 LM）平均 Spearman ρ = **0.463**，胜出 BLOSUM62 基线 **5/6** assay；
- 平均 Δρ = +0.219；小模型 8M ρ=0.227（容量缩放与论文一致）；
- 唯一反例 GFP（多点变异为主 + 极浅 MSA），详见 report.md §3.3；
- 结论标签：**supported**（详见 claim.md 的判定矩阵与披露）。

## 数据 & 权限
- 冻结数据位于 `../data/`（assay CSV + 参考文件；ProteinGym 数据 CC BY 4.0）；
- 评估只用冻结 DMS 分数；无泄漏（零样本、无训练）。