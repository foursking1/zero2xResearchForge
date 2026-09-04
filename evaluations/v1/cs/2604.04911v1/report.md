# EVAL REPORT: 2604.04911v1（SpatialEdit: Benchmarking Fine-Grained Image Spatial Editing）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算 `_prep/judge_check_04911.py`）
- 评测时间: 2026-08-13

## 总分: 52 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 12 | 60 | 12 条 numeric 锚全为论文 Table 值（转录一致 + 算术自洽 + Table 内最优成立），但冻结数据独立复现仅 FE 部分达成（0.690 vs 0.527）、VE 复现失败（2295 vs 0.243）；C02/C03/C04 数据缺失 |
| B 证据真实性 | 25 | 25 | 裁判独立重算 FE 聚合（0.6896 vs 0.6902，聚合顺序差异 <0.1%）与命令分解，实质一致 |
| C 方法与报告 | 15 | 15 | 数据真实性验证充分（387 三元组/yaw-pitch 离散化/prompt↔JSON 一致率）、zoom 口径 4 变体敏感性、VE 失败诚实归因 |

## A 核心结果达成度（12/60）

### 关键前提

论文 12 条 numeric 锚：R01-R06（SpatialEdit-Bench 相机级）、R07-R09（GEdit-Bench-EN）、R13-R15（Spearman 可靠性）。冻结数据包含：meta（1216 任务）、387 个完整 camera 三元组（src/gt/pred/json/prompt）、逐样本 FE/VE CSV（yolo11n 替代检测器、VGGT-1B 公开权重）；**不含** move/rotate 预测三元组（object 级 MS/RS 不可复现）、GEdit-Bench 评测、训练消融、受控 Spearman 验证数据。

### claim 判定复核

| Claim | agent 判定 | 裁判复核 | 依据 |
|---|---|---|---|
| C01 SpatialEdit-Bench 整体最优（0.673/0.632/0.243/0.527/0.653/0.385） | **partially_supported** | ✅ 合理 | ① 6 数字与 Table 2 转录一致、"各列最优"成立、Overall=(MS+RS)/2 与 (VE+FE)/2 算术自洽（论文引用+校验）；② 基准数据真实（1216 meta / 387 三元组 / yaw 45° pitch 15° 离散化 / prompt↔JSON 100% 一致）；③ FE 复现 0.690 vs 0.527（检测器替代 + zoom 口径可解释，Eq.9 口径下 0.327）；④ VE 复现 2295 vs 0.243（公开 VGGT 栈位姿/尺度不匹配，差 4 个数量级）→ 论文精确数值未获独立确认 |
| C02 GEdit-Bench-EN（8.09/7.80/7.52） | **inconclusive** | ✅ 合理 | 数字与 Table 5 一致、开源模型 Overall 排 3/8 称"competitive"成立；冻结数据无 GEdit 评测，无法独立复现 |
| C03 多任务混合训练最优 | **inconclusive** | ✅ 合理 | Table 3 各列最优成立；无训练/消融数据 |
| C04 VE 相关性最高（0.932/0.659/0.445） | **inconclusive** | ✅ 合理 | Table 4 排序成立；无受控验证数据 |

### A 小结

12 条 numeric 锚 0 条以论文口径独立达成（FE/VE 复现均偏离论文值，虽差距有口径/栈因素可解释）；但 C01 的"数据存在性 + Table 内部一致性 + FE 复现与敏感性"核验有价值 → A=12/60。

## B 证据真实性（25/25）

**独立重算抽查（裁判脚本 judge_check_04911.py，从冻结逐样本 CSV 独立重算）：**

| 抽查项 | agent 报告 | 裁判重算 | 一致 |
|---|---|---|---|
| FE angle_error_deg（387 样本，det_fail→20°） | 11.227353 | 11.227353 | ✅ 逐位 |
| FE zoom_error（缺失→1.0） | 0.819121 | 0.819121 | ✅ 逐位 |
| FE 总值（mean 后 clamp 口径，同 agent 公式） | 0.690245 | 0.690245（per-sample clamp 口径 0.6896，差 0.09%） | ✅ 实质 |
| Variant A（非 zoom 命令 zoom=0） | 0.3272 | 0.3266 | ✅ 实质 |
| 命令分解 D（zoom, n=106） | 0.4289 | 0.4289 | ✅ 逐位 |
| 387 三元组计数 | 387 | 387 | ✅ |

- 注：裁判按 per-sample clamp 重算得 FE=0.6896，与 agent（mean 后 clamp）0.6902 差 0.09%，属聚合顺序差异，两种口径均成立且结论不变；agent solution.md 中公式自洽
- 数据真实性核验充分：图像 1161/1161 可读且尺寸一致、prompt↔JSON 一致率 1.0、yaw/pitch 离散化 1.0
- VE 复现（8 样本 smoke）如实报告为失败（2295 vs 0.243），无粉饰

## C 方法与报告（15/15）

- C1 方法合理性（5/5）：FE/VE 公式逐项定义明确；数据真实性验证（三元组完整性/离散化/一致率）严谨；只读冻结数据无泄漏
- C2 稳健性（5/5）：zoom 口径 4 变体敏感性（0.690→0.327 的跨度拆解）、按命令类型（D/P/Y/Y+P）分解、图像健全性检查——口径敏感性分析是本题最大亮点
- C3 边界与结论（5/5）：VE 复现失败诚实归因（公开栈与论文评测设置不匹配，位姿约定/尺度/预处理），未把 2295 硬说成接近论文；C02/C03/C04 数据缺失判 inconclusive 不硬套锚值；结论有数据支撑、不夸大

## 结论

- **科学结论**：C01 `partially_supported`（数据与 Table 自洽 + 部分口径复现，但精确数值未独立确认）；C02/C03/C04 `inconclusive`（数据缺失）→ 整体 `partially_supported`（数据受限）
- 证据真实性满分：FE 聚合数字（含两套 zoom 口径）独立重算实质一致，无编造
- 主要扣分在 A 达成度：论文关键数值（VE 0.243 等）无法用公开栈+冻结数据复现，且 object 级/GEdit/Spearman 数据缺失；agent 执行诚实、敏感性分析出色，但可达成锚极少
