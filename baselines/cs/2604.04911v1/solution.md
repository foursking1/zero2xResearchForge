# Solution: SpatialEdit (arXiv:2604.04911v1) — Claim Verification

## 0. 概述

本方案使用**冻结数据**（`F:\dataset\2604.04911v1`，原位读取，未复制/未下载任何数据）对 TASK.md 中
4 条 claim 进行验证。验证同时使用两类证据：

1. **冻结数据实际计算**：SpatialEdit-Bench 元数据、387 个真实 camera 三元组（src/gt/pred/json/prompt）、
   以及此前复现流水线在真实数据上运行得到的逐样本 FE/VE 结果 CSV（`results/fe_yolo11n_full/camera_framing_error_per_sample.csv`、
   `results/camera_viewpoint_error_per_sample.csv`）。
2. **论文表格引用**（明确标注 "论文引用"）：论文 Table 2/3/4/5 中的数值由论文 PDF 提取核对。

**环境说明**：本机为 CPU-only、无 `ultralytics/cv2/vggt`，无法重新运行 YOLO/VGGT 推理；
模型类指标的复现仅基于冻结的逐样本 CSV 重新聚合（聚合公式与原复现流水线一致），
并做口径敏感性分析。

**复现入口**：`python code/run_all.py`（依次运行 inventory / paper 校验 / FE 分解 / evidence 生成）。

---

## 1. 方法

### 1.1 数据清单与基准结构核验（`code/analyze_frozen_data.py`）
- 读取 `SpatialEdit_Bench_Meta_File.json`：统计任务类型分布（camera / rotate / move）、唯一 scene 数。
- 扫描 `SpatialEdit_Results/spatialedit/fullset/camera/en/`：统计含完整五件套
  （`<edit>.json`、`<edit>.png`、`<edit>_gt.png`、`<edit>_src.png`、`<edit>_prompt.txt`）的三元组数量。
- 逐任务解析 JSON 中 `metadata.edit_ypd`（yaw/pitch/distance），并解析 prompt 文本，
  校验 **prompt↔JSON 一致率**；检查 yaw 是否为 45° 倍数、pitch 是否为 15° 倍数（论文第 3.2 节声称的离散化粒度）。
- 图像健全性：全部 src/gt/pred 图像可读且尺寸一致。

### 1.2 相机级指标聚合（FE / VE）
- **Framing Error (FE)**：对逐样本 CSV 重新聚合（与原复现流水线 `summarize_framing_results` 同公式）：
  - `angle_error = mean(gt_ray_diff_deg 缺失→20°)`；`zoom_error = mean(zoom_dir_err 缺失→1.0)`；
  - `FE = ( clamp(angle_error/20,0,1) + clamp(zoom_error,0,1) ) / 2`。
- **Viewpoint Error (VE)**：`VE = mean(overall_VE_error)`，其中
  `overall_VE_error = (gt_xyz_err + gt_ypr_err)/2`，`gt_xyz_err` 为 VGGT 相机中心的
  baseline 归一化平移误差，`gt_ypr_err` 为旋转测地误差/90°。
- 另做 **FE 的 zoom 口径敏感性分析**（`code/fe_by_command.py`）：
  原聚合对非 zoom 命令（ddist=0）的 zoom 误差以 1.0 填充；论文 Eq.(9) 的指示函数在 Δd=0 时为 0。
  因此补充"非 zoom 命令 zoom 误差按 0 计"（Variant A）与"仅 zoom 命令"两种口径。

### 1.3 论文数值校验（`code/verify_paper_tables.py`）
- 转录论文 Table 2（SpatialEdit-Bench 对比）、Table 3（多任务消融）、Table 4（Spearman 可靠性）、
  Table 5（GEdit-Bench-EN），全部标注为**论文引用**。
- 校验：claim 中的数字是否与论文表一致；Table 2 各列 SpatialEdit 是否最优；
  `Object Overall = (MS+RS)/2`、`Camera Overall = (VE+FE)/2` 的算术一致性；
  Table 3 全任务是否各列最优；Table 4 排序是否 VE > FE > GPT4.1；Table 5 中 "competitive" 的定位。

### 1.4 判定标准
- **supported**：冻结数据可独立重现且与 claim 一致。
- **partially_supported**：部分可独立重现/部分仅论文引用，或复现口径与论文不一致。
- **contradicted**：冻结数据与 claim 相矛盾。
- **inconclusive**：冻结数据缺失，无法独立验证（仅论文引用可核对）。

---

## 2. 结果

### 2.1 基准结构与数据（冻结数据实测）

| 指标 | 实测值 | 口径 |
|---|---|---|
| meta 任务总数 | 1216 | 冻结数据 |
| 任务类型分布 | camera 452 / rotate 488 / move 276 | 冻结数据 |
| 唯一 scene (image_id) 数 | 131 | 冻结数据 |
| 磁盘上完整 camera 三元组 | 387（28 个场景目录） | 冻结数据 |
| 三元组与 meta 匹配 | 387/387 | 冻结数据 |
| 图像可读率 | 100% (1161/1161)，尺寸均 1152×896 | 冻结数据 |
| yaw 为 45° 倍数比例 | 1.0 | 冻结数据 |
| pitch 为 15° 倍数比例 | 1.0 | 冻结数据 |
| prompt↔JSON edit_ypd 一致率 | 1.0 | 冻结数据 |
| camera 命令覆盖 | yaw∈[−135°,180°], pitch∈[−75°,75°], dist∈[−516,923]；zoom-in 47 / zoom-out 59 / 无 zoom 281 | 冻结数据 |

> 结论：SpatialEdit-Bench **camera 子集数据真实存在且结构自洽**，与论文第 3.2 节描述的
> "yaw 45°、pitch 15° 离散化"一致。meta 中 rotate/move 任务条目存在，但**冻结数据中不含
> 相应的 src/gt/pred 预测三元组**，无法进行 object-level 指标复现。

### 2.2 C01 — SpatialEdit-Bench 相机级指标：论文值 vs 冻结数据复现

| 指标 | 论文值（引用 Table 2） | 冻结数据复现 | 差异 |
|---|---|---|---|
| Framing Error (FE) | 0.527 | **0.6902**（387 样本, yolo11n 替代检测器） | +0.163 |
| Viewpoint Error (VE) | 0.243 | **2295.46**（8 样本 smoke, VGGT-1B 公开权重） | +2295 |
| Camera Overall | 0.385 | 1148.08（受 VE 不稳定主导） | — |

- **FE 复现**：angle_error=11.23°（angle 分量有效 226/387，缺失按 20° 填充），zoom_error=0.819
  （zoom_dir_err 仅在 zoom 命令且匹配成功时有效，其余 281 个非 zoom 命令按 1.0 填充）。
  与论文 0.527 不符，原因包括：(a) 检测器为 yolo11n 替代（论文用 yolo26x）；
  (b) **zoom 聚合口径**——原复现把非 zoom 命令的 zoom 误差按 1.0 填充（见表 2.3 敏感性）。
- **VE 复现**：`gt_xyz_err` 均值 4590（样本范围 175–18167），`gt_ypr_err` 均值 0.793，
  即公开 VGGT-1B 栈的平移归一化严重不稳定，与论文 0.243 差 4 个数量级；旋转项本身也偏高，
  说明公开栈与论文评测设置（位姿约定/尺度/预处理）存在系统性不匹配。

### 2.3 FE 按命令类型分解与 zoom 口径敏感性（冻结数据）

| 命令类型 | n | angle_error(°) | zoom_error | FE |
|---|---|---|---|---|
| D (zoom) | 106 | 10.36 | 0.340 | 0.429 |
| P (pitch) | 101 | 9.25 | 1.000 | 0.731 |
| Y (yaw) | 82 | 10.13 | 1.000 | 0.753 |
| Y+P | 98 | 15.12 | 1.000 | 0.878 |

| zoom 口径 | FE |
|---|---|
| 原复现（非 zoom 命令 zoom 误差=1.0 填充） | 0.6902 |
| Variant A（非 zoom 命令 zoom 误差=0，对应论文 Eq.9） | **0.3272** |
| 仅 zoom 命令（n=106） | 0.4289 |
| 仅非 zoom 命令（n=281） | 0.7888 |

> 关键发现：复现 FE=0.690 中约一半来自"非 zoom 命令被计为全额 zoom 失败"这一聚合选择；
> 若按论文 Eq.(9)（Δd=0 时指示函数为 0）则 FE≈0.327。因此**复现 FE 与论文 0.527 的差距
> 主要源于口径与检测器差异，而非单纯模型能力**。

### 2.4 论文表格内部一致性（论文引用 + 算术校验）

| 校验 | 结果 |
|---|---|
| C01 六个数字 = Table 2 SpatialEdit 行 | 全部一致 |
| Table 2 各列最优者 = SpatialEdit（MS/RS/Obj/VE/FE/Cam 共 6 列） | 全部 True |
| Object Overall = (MS+RS)/2 | SpatialEdit: (0.673+0.632)/2=0.6525→0.653 ✓（全部 7 个具名方法均 ✓） |
| Camera Overall = (VE+FE)/2 | SpatialEdit: (0.243+0.527)/2=0.385 ✓（全部 9 行均 ✓） |
| Table 3 全任务(Mov+Rot+Cam)各列最优 | Mov 0.673=max、Rot 0.632=max、Cam 0.385=min，均 True |
| Table 4 排序 | VE 0.932 > FE 0.659 > GPT4.1 0.445 ✓ |
| Table 5 SpatialEdit (SC 8.09, PQ 7.80, O 7.52) | 与 claim 完全一致；开源模型 Overall 排第 3/8（"competitive"成立） |

---

## 3. Claim 判定

| Claim | 判定 | 依据 |
|---|---|---|
| **C01**：SpatialEdit 在 SpatialEdit-Bench 上整体最优（0.673/0.632/0.243/0.527/0.653/0.385） | **partially_supported** | ① 六个数字与论文 Table 2 完全一致，"各列最优"在 Table 2 内成立，Overall 算术自洽（论文引用+校验）；② 基准数据真实存在（1216 meta 任务、387 camera 三元组）；③ **object-level MS/RS 无法从冻结数据复现**（无 move/rotate 预测三元组）；④ **camera 级 FE/VE 用公开栈复现明显偏离论文**（FE 0.690 vs 0.527；VE 2295 vs 0.243），差距可由检测器替代 + zoom 聚合口径 + VGGT 设置不匹配解释，但意味着论文的精确数值未能被独立确认。 |
| **C02**：GEdit-Bench-EN 竞争性表现（SC 8.09, PQ 7.80, O 7.52） | **inconclusive**（冻结数据缺失；论文数字核对一致） | 数字与 Table 5 完全一致；开源模型 Overall 排名 3/8，高于多数开源模型，称"competitive"合理（论文引用）。冻结数据中**无 GEdit-Bench 评测数据**，无法独立复现。 |
| **C03**：多任务混合训练 (Mov+Rot+Cam) 最优 | **inconclusive**（冻结数据缺失；论文 Table 3 内部一致） | Table 3 全任务行各列均为最优（0.673/0.632/0.385），消融趋势自洽（论文引用）。冻结数据中**无训练/消融数据**，无法独立复现。 |
| **C04**：VE 相关性最高，其次 FE，均远超 GPT4.1（0.932/0.659/0.445） | **inconclusive**（冻结数据缺失；论文 Table 4 一致） | Table 4 排序成立（论文引用）。冻结数据中**无受控验证的细粒度视角渲染与排序数据**，无法独立复现。 |

### 结论要点
1. **C01 的前半句（"paper 声称的数字与自身 Table 2 一致且在各列最优、Overall 算术自洽"）成立**；
   但"用冻结数据重现论文关键结果"只做到了**部分**：基准数据存在性、FE 复现（口径修正后与论文量级可解释）、
   VE 复现失败（公开栈不稳定）。
2. C02/C03/C04 依赖的数据（GEdit-Bench、训练消融、Spearman 受控验证）**不在冻结数据集中**，
   只能核对论文数字一致性，无法独立复现 → 判定为 inconclusive（不满足"数据支撑"的严格标准）。

---

## 4. 文件清单

- `solution.md` — 本文档。
- `code/run_all.py` — 一键复现入口；`code/analyze_frozen_data.py`、`code/verify_paper_tables.py`、
  `code/fe_by_command.py`、`code/build_evidence.py`、`code/requirements.txt`。
- `results/evidence_table.csv` — 证据表（指标名、数值、口径、说明），78 行。
- `results/metrics.json` — 机器可读指标（键名与 evidence_table 一致）。
- `results/frozen_data_analysis.json` — 冻结数据实测原始输出。
- `results/paper_table_verification.json` — 论文表格校验原始输出。
- `results/fe_by_command.json` — FE 命令类型分解与 zoom 敏感性输出。

> 附：`results/sample_{src,gt}.png`、`results/sample.png` 为一个真实三元组（zoom-in 任务）样例，
> 供人工核对数据真实性。
