# PAPER_ANCHOR：论文核心结果锚（私有，禁止外泄到 TASK.md 之外的公开面）

论文：Pant, Baniya, Lee & Aryal, Hyperspectral Anomaly Detection Methods: A Survey and Comparative Study（arXiv:2507.05730，2025）。以下数值摘自论文 Table 5 / Table 4 / §5.3，禁止臆造。

## 锚 A1 — RX 列像素级 AUC（Table 5，本包 14 行）
冻结文件 ↔ 论文行号 ↔ 论文 RX AUC（2026-08-14 全局 RX 自检复算值）：

| 冻结文件 | 论文行 | 论文 RX AUC | 自检 RX AUC | Δ | 备注 |
| --- | --- | --- | --- | --- | --- |
| sandiego.mat+plane_gt.mat（左上 100×100） | 1 San Diego | 0.9403 | 0.9219 | −0.0184 | 论文用 100×100×186 裁剪，本包为全图 400×400×224 → 版本差异 |
| hydice_urban.mat | 2 HYDICE | 0.9857 | 0.9857 | 0.0000 | 精确一致 |
| aviris_1.mat | 6 AVIRIS-1 | 0.8866 | 0.8866 | 0.0000 | 精确一致 |
| aviris_2.mat | 7 AVIRIS-2 | 0.9181 | 0.9181 | 0.0000 | 精确一致 |
| abu/abu-airport-1.mat | 8.1 LA-1 | 0.8221 | 0.8221 | 0.0000 | 精确一致 |
| abu/abu-airport-2.mat | 8.3 LA-2（映射互换） | 0.8404 | 0.8404 | 0.0000 | 精确一致（镜像命名与论文表互换） |
| abu/abu-airport-3.mat | 8.2 Gulfport | 0.9526 | 0.9288 | −0.0238 | 版本差异（镜像 205 波段 vs 论文 191） |
| abu/abu-urban-1.mat | 9.1 Texas-1 | 0.9907 | 0.9907 | 0.0000 | 精确一致 |
| abu/abu-urban-2.mat | 9.2 Texas-2 | 0.9946 | 0.9946 | 0.0000 | 精确一致 |
| abu/abu-urban-3.mat | 9.3 Gainesville | 0.9513 | 0.9513 | 0.0000 | 精确一致 |
| abu/abu-urban-4.mat | 9.4 LA-3 | 0.9887 | 0.9887 | 0.0000 | 精确一致 |
| abu/abu-urban-5.mat | 9.5 LA-4 | 0.9692 | 0.9692 | 0.0000 | 精确一致 |
| abu/abu-beach-1.mat | 10.1 Cat Island | 0.9807 | 0.9807 | 0.0000 | 精确一致 |
| abu/abu-beach-2.mat | 10.2 Bay Champagne | 0.9999 | 0.9106 | −0.0893 | 版本差异（镜像 193 波段 vs 论文 188） |

- 精确一致（|Δ|≤0.01）：**11/14**（行 2、6、7、8.1、8.3、9.1–9.5、10.1）；版本差异行 3 个（1、8.2、10.2）。
- RX 定义口径：全局统计 μ/Σ（全图像素）、Σ 伪逆、马氏距离分数、AUC=roc_auc_score(gt>0, score)。

## 锚 A2 — RX 竞争力下限与速度（Table 5）
- RX 列全部 17 行 AUC 范围 [0.8221, 0.9999]，最低 0.8221（LA-1）→ 冻结 14 行全部 ≥0.80。
- 平均 AUC：RX 0.9390 / LRX 0.9013 / CRD 0.9567 / PTA 0.9141 / KIFD 0.9529 / Auto-AD 0.9273 / RGAE 0.8846 / TDD 0.6468 / LREN 0.8297 / **GT-HAD 0.9733（最高）**。
- 平均时间（s）：RX **0.40（最快）** / LRX 17.21 / CRD 31.96 / PTA 30.40 / KIFD 57.51 / Auto-AD 8.05 / RGAE 176.80 / TDD 2.24 / LREN 142.17 / GT-HAD 30.51。
- 自检：单图 100×100×200 全局 RX 运行 <1.5s（本机）。

## 锚 A3 — 方法族结论（§5.3）
- 统计（RX/LRX）：速度最快，精度有竞争力（部分数据集近完美：Cri RX 0.9989）。
- 表示类（PTA/CRD）：CRD 为非深度方法中最高平均 AUC（0.9567），但计算密集。
- 深度类（Auto-AD/RGAE/TDD/LREN/GT-HAD）：GT-HAD 平均最高（0.9733）；TDD/LREN 高度不稳定（多个数据集 AUC<0.3）。
- 用途：A2/A3 用于校验 agent 对 (c) 的解读——若 agent 声称「RX 平均精度最高」或「深度方法平均更差」，与锚冲突。

## 判分一致性提醒
- 判分以 A1（|Δ|≤0.01 的匹配数，满分档 ≥10/14）与 A2（min_auc≥0.80、运行时间）为主；版本差异 3 行须被正确识别为版本问题（|Δ|∈(0.01, 0.12] 给部分分，错误声称复现失败 → 扣分）。
- 未冻结的 3 行（Cri/Salinas/Pavia）不在判分范围，agent 若引用须说明未冻结。
