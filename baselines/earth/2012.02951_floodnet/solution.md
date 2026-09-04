# solution.md — FloodNet VQA 复现（2012.02951）

## 结论
- **Verdict: supported**
- **整体准确率（eval，图级 85/15 划分，seed=42）OA = 0.8127**
  - 论文锚 0.72（validation）；相对差 d = 12.9%
  - 与论文 Table 5 按类型量级一致：Yes/No 0.985、条件识别 0.992、
    简单计数 0.357、复杂计数 0.301（论文 0.98/0.96/0.31/0.28）
- 语言偏差消融：随机换图 OA→**0.263**（严重依赖图像）；纯语言（图置零）
  0.665 ≈ 模板多数先验 0.672 → 模型确实在看图，claim 未被先验污染。

## 方法要点
- 冻结真实数据：官方 4,511 问-答对 + 1,448 张航拍影像（4000×3000）
- 图级划分（防同图泄漏）：train 1,083 图/3,387 对，dev 148 图/462 对，
  eval 217 图/662 对；模型选择只用 dev，eval 答案仅用于最终统计
- 图像：冻结 ImageNet 预训练 ResNet-18（448px，全局 512-d + 空间 14×14×512）
  与 ViT-B/16（224px，CLS 768-d）
- 文本：嵌入 + Bi-LSTM（256-d）
- 融合：MFB（factorized bilinear，k=2 分组求和 + L2 归一）+ 问句条件空间
  Co-Attention（含图像→问句反向注意力）
- 分类：41 类共享头 + 按问题类型的合法答案掩码
- 实现于 CPU，特征预计算后 5 配置训练（Adam, lr=3e-4，dev 早停），
  最优 r18vit-mfb（dev 0.838）整体可复现

## 关键产物（agent_solution/）
- `report.md`：完整报告（方法/划分/防泄漏/按类型/消融/局限/复现）
- `results/metrics.json`：主指标（overall_accuracy、accuracy_by_type、
  random_image_ablation_accuracy 等）
- `results/evidence_table.csv`：4,511 行逐条 prediction + correct
- `results/by_type_summary.csv`、`results/per_template_eval.csv`
- `figures/*.png`：三张分析图
- `code/run_all.sh`：一键复现；`code/{data_prep,extract_features,train,evaluate,analysis}.py`

## 复现
```bash
cd code && bash run_all.sh
```
数据路径经 `FLOODNET_DATA_DIR` 可覆盖；离线需本地 ImageNet 权重缓存
（resnet18 / vit_b_16）。

## 主要局限
官方 Valid/Test 答案未发布 → OA 为非官方子集口径，0.72/0.73 仅作量级参照；
计数类仍为系统难点（0.30 左右与论文一致）；FloodNet 模板少、多数先验强
（纯语言 0.66），使整体数字偏高，已用量化消融说明。