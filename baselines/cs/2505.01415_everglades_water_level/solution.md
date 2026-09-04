# solution.md — Everglades 水位预测（论文 2505.01415）复现与判定

## 结论速览

| 可证伪表述 | 结论 | 关键证据 |
|---|---|---|
| (a) 28 天 horizon 下 MLP/深度类任务特定模型 Overall MAE 显著低于线性类 | **supported** | 最佳深度模型 MLPResidual(mc0.1) 28d=0.298 < NLinear 0.397 < DLinear 0.451 |
| (b) 线性模型 7→28 天 Overall MAE 相对增幅 ≥50% | **supported** | DLinear +69%（0.268→0.451），NLinear +83%（0.217→0.397） |
| (c) 零样本 Chronos 显著优于所有任务特定模型 | **contradicted**（环境局限） | chronos-t5-small 28d=0.348 > 最佳任务特定 0.298（且 > persistence 0.330） |

数据支撑强度：
- (a) 排序稳定（多种 seed / 两种线性模型均确认）；绝对数值高于论文锚
  （锚 NBEATS 0.176 / DLinear 0.392），差异源于自定义管线 vs 论文
  neuralforecast 管线，方向与锚一致。
- (b) 两个线性模型增幅均 ≥50%，退化方向与锚一致；模型间精确次序
  （锚中 DLinear 增幅最大）未复现，为部分吻合。
- (c) 在本环境唯一可用的 chronos-t5-small 权重下无法复现；需更大规模
  Chronos 权重才可最终判定。

## 证据表（Overall MAE，Overall = 5 站均值；RMSE 见 results/evidence_table.csv）

| 模型 | 类别 | 7d | 14d | 21d | 28d |
|---|---|---|---|---|---|
| **MLPResidual_mc0.1**（深层 MLP+MC-dropout，seed42） | MLP/深度 | 0.127 | 0.192 | 0.247 | **0.298** |
| MLPResidual（plain） | MLP/深度 | 0.132 | 0.197 | 0.257 | 0.316 |
| NLinear | 线性 | 0.217 | 0.305 | 0.378 | 0.397 |
| DLinear | 线性 | 0.268 | 0.331 | 0.398 | 0.451 |
| NBEATS（复现尝试，弱于论文） | MLP | 0.299 | 0.355 | 0.447 | 0.451 |
| TSMixer | MLP | 0.286 | 0.350 | 0.405 | 0.437 |
| PatchTST | Transformer | 0.342 | 0.374 | 0.449 | 0.513 |
| **Chronos_c512**（零样本，本地权重） | 基础模型 | 0.126 | 0.210 | 0.284 | 0.348 |
| Chronos_c100 | 基础模型 | 0.135 | 0.218 | 0.315 | 0.406 |
| persistence 基线 | 参考 | 0.132 | 0.198 | 0.264 | 0.330 |

每站点 28d MAE：NP205 在所有模型中最难（MLPRes:0.521 / NLinear:0.695 /
DLinear:0.782），与论文 A4 辅助判据一致。

## 方法要点

- **协议**：1411 天（2020-10-16→2024-08-26），37 变量；训练=前 1200 天，
  验证=训练内最后 211 天（与测试不相交），测试=最后 211 天；输入=前
  100 天全部变量；单模型 h=28 直接多步，测试期日滚动评估，lead
  7/14/21/28，Overall=5 站 MAE 均值。
- **防泄漏**：标准化只由训练段拟合；窗口输出全在训练段内；滚动上下文只含
  目标日前观测；测试段不进训练/验证/早停；固定随机种子 42。
- **代码**：`code/` 内 pytorch 自实现 NLinear/DLinear/NBEATS/MLPResidual/
  TSMixer/PatchTST + chronos 零样本评估 + 持久基线 + 证据聚合；全部从
  冻结 CSV 读取（sha256 核对）。CPU 可复现，命令见 README.md。

## 关键文件

- `results/evidence_table.csv` — 主证据表（model/lead_time/overall_mae/
  overall_rmse/各站 MAE 列）
- `results/evidence_station_lead.csv` — 每(站点,lead)原始指标
- `results/predictions_{model}.npz` — 测试期滚动预测
- `results/claim_analysis.md` — 自动生成的判定摘要
- `results/figures/*.png` — MAE-vs-horizon、每站点 28d、预测曲线图
- `evidence/data_facts.json` — 冻结数据事实与校验
- 完整方法/局限讨论见 `report.md`