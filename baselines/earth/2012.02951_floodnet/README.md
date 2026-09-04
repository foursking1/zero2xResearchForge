# FloodNet VQA Reproduction (2012.02951) — agent_solution

复现论文 Rahnemoonfar et al., *"FloodNet: A High Resolution Aerial Imagery Dataset
for Post Flood Scene Understanding"* (IEEE TPAMI 2021; arXiv:2012.02951) 的核心
claim：MFB with Co-Attention 在 FloodNet VQA 上 ~0.72 整体准确率（计数类除外）。

## 结果速览
| 指标 | 值 | 论文锚 |
|---|---|---|
| Overall Accuracy (eval, 662 问) | **0.8127** | 0.72 (validation) |
| Yes/No | 0.9851 | 0.98 |
| Condition Recognition | 0.9915 | 0.96 |
| Simple Counting | 0.3571 | 0.31 |
| Complex Counting | 0.3011 | 0.28 |
| 随机换图消融（语言偏差） | 0.2628 | — |
| 纯语言（图置零）基线 | 0.6647 | — |
| 模板多数先验 | 0.6722 | — |

**Verdict: supported。**

## 目录
- `report.md` — 完整报告（结论/方法/划分/防泄漏/按类型分析/消融/局限/复现）
- `solution.md` — 摘要版
- `submission/` — 任务要求的提交目录（report + results/evidence_table.csv 等）
- `code/` — 全部源代码 + `run_all.sh`（一键复现）
- `results/` — 全部指标与证据表
- `figures/` — 分析图（按类型柱状图、计数散点图、语言偏差对比图）
- `evidence/` — 关键证据导出副本
- `workspace/` — 预计算图像特征、模型权重、训练/评估日志

## 复现
```bash
cd code
bash run_all.sh
# 手动分步：data_prep.py -> extract_features.py -> train.py -> evaluate.py -> analysis.py
```
- 数据路径默认 `/mnt/f/dataset/earth/2012.02951_floodnet/data`，
  可用环境变量 `FLOODNET_DATA_DIR` 覆盖。
- 依赖：Python≥3.10, torch, torchvision, numpy, PIL, matplotlib。
  图像特征使用 ImageNet 预训练权重（torchvision 缓存 resnet18 / vit_b_16）。
- 全程 CPU 可跑；特征预计算约 5–10 分钟，5 个配置训练数分钟完成。

## 关键技术决策
1. **图级 85/15 划分（seed=42）**，train/dev/eval 图像互不重叠，防同图泄漏；
   eval 答案仅用于最终统计。模型选择只用 dev。
2. **冻结预训练图像特征**（ResNet-18 + ViT-B/16）× **Bi-LSTM 问句编码** ×
   **MFB 双线性融合 + Co-Attention**（问句条件空间注意力 + 图像条件问句注意力），
   每类型合法答案掩码分类。
3. **语言偏差三重检查**：随机换图 OA 0.813→0.263（模型强烈依赖图像）；
   纯语言 0.665 ≈ 模板先验 0.672（报告了 FloodNet 模板先验强的现实）。

## 主要局限（如实报告）
- 官方 Valid/Test 答案未发布 → 0.72/0.73 为不同子集上的量级参照。
- 图像编码器用 ResNet-18/ViT-B-16（离线仅有这两种缓存），非论文 VGG16。
- 计数类仍是系统难点（0.30 量级，与论文一致）。