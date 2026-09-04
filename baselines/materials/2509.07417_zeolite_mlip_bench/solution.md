# Solution: 2509.07417_zeolite_mlip_bench

## 结论摘要（判定：复现）

论文三个核心 claim（C1 纯硅排序、C2 含客体 RMSE 与 "Cu/CHA 更难"、C3 eSEN "最一致"）全部由冻结官方 Zenodo 数据独立复算得到复现：

- **C1（Table 3，纯硅）**：复现。排序 eSEN(0.44) < ORB-v3(1.01) < PFP-v7(1.34) < MatterSim(1.49) < CHGNet(3.60) ≪ GFN-FF(24.49) < Dreiding(40.95) < UFF(44.65)；通用解析势 RMSE 比最优 MLIP（eSEN）大一个数量级（24.5–44.6 vs 0.44）。
- **C2（Table 4，含客体）**：复现。Cu/CHA 中 eSEN 最小（0.142）；K-OSDA/ERI 中 eSEN 最小（0.020）；每个模型 Cu/CHA RMSE 均大于 ERI RMSE（"含过渡金属更难"）。
- **C3（最一致）**：复现。在论文报告模型集合（CHGNet/ORB-v3/MatterSim/eSEN/PFP-v7/EqV2-OC22）内，eSEN 在纯硅/Cu-CHA/K-OSDA-ERI 三个体系全部取得最小 RMSE。

## 方法

1. **数据**：冻结 `F:/dataset/materials/2509.07417_zeolite_mlip_bench/ZeoBenchmark.zip`（48,048,651 字节），使用前校验 SHA-256 = `f8214b63e39c6d3e3f84bfe6bcf7cf5c44140074de5d12de4085921131a7f3d1`（与 `data/checksums.sha256` 一致）。
2. **解压**：脚本内用 `zipfile` 解压到临时目录（不修改冻结文件），读取 `Zenodo/Puresilica.json`（229 拓扑）、`Zenodo/Cu_CHA.json`（347 结构）、`Zenodo/KSDA_ERI.json`（1,190 结构）。
3. **原子数**：从每个结构 `dft` 条目的 pymatgen `structure` 字典直接统计 sites（纯硅数 Si，客体数总原子=各 site 各 species occu 之和）。每个势场条目 `energy` 为总能量（eV）。
4. **相对能量定义**（论文口径）：
   - 纯硅：`rel(s) = [E_model(s)/nSi(s) − E_model(quartz)/nSi(quartz)] × 96.48533212`（kJ/molSi）。每个势场用各自的 α-quartz 能量作参考。RMSE vs 同口径 DFT 相对能量，对全部 228 个非 quartz 拓扑计算。
   - 客体：`rel(s) = [E_model(s)/N(s) − E_model(ref)/N(ref)] × 96.48533212`（kJ/molatom）。`ref` = 该数据集内 DFT 每原子能量最低的结构（Cu/CHA：`CHA_0_6_11_13_16_30_35_Cu8`；KSDA_ERI：`613868a29871063a280b4606`）。RMSE vs DFT。
5. **单位换算**：1 eV = 96.48533212 kJ/mol。

## 结果

### Table 3 复算（纯硅，kJ/molSi，vs DFT）—— C1

| 模型 | 论文报告值 | 本工作复算值 | 偏差 |
|---|---|---|---|
| eSEN-30M-OAM | 0.44 | **0.4386** | +0.00 |
| ORB-v3 | 1.01 | **1.0074** | +0.00 |
| PFP-v7 | 1.33 | **1.3359** | +0.01 |
| MatterSim | 1.49 | **1.4923** | +0.00 |
| CHGNet | 3.60 | **3.6039** | +0.00 |
| SLC | 7.40 | **7.4176** | +0.02 |
| BSFF | 7.60 | **7.6184** | +0.02 |
| ClayFF | 8.98 | **8.9964** | +0.02 |
| GFN-FF | 24.44 | **24.4902** | +0.05 |
| Dreiding | 40.86 | **40.9502** | +0.09 |
| UFF | 44.55 | **44.6467** | +0.10 |

- 排序完全一致：eSEN < ORB-v3 < PFP-v7 < MatterSim < CHGNet ≪ GFN-FF < Dreiding < UFF；定制势 SLC/BSFF/ClayFF 落在 CHGNet 与 GFN-FF 之间（7.4–9.0）。
- `pfp` 与 `pfp_shifted` 在相对能量下等价（两者 RMSE 均为 1.3359），与论文说明一致；下表以 `pfp`（论文采用修正版，相对能量下无差别）报告。
- 通用解析势（GFN-FF 24.49 / Dreiding 40.95 / UFF 44.65）RMSE 为最优 MLIP（eSEN 0.44）的 56–102 倍，验证"至少大一个数量级"。
- 额外发现：`orb`（ORB 旧版）RMSE=0.4071，略优于 eSEN，但该模型不在论文 Table 3 报告列表内（论文报告的是 ORB-v3），不影响对论文 claim 的判定。

### Table 4 复算（含客体，kJ/molatom，vs DFT）—— C2

Cu/CHA（347 结构）：

| 模型 | 论文报告值 | 本工作复算值 |
|---|---|---|
| eSEN-30M-OAM | 0.14 | **0.1421** |
| ORB-v3 | 0.24 | **0.2399** |
| PFP-v7 | 0.24 | **0.2449** |
| EqV2(OC22) | 0.26 | **0.2571** |
| MatterSim | 0.52 | **0.5203** |
| CHGNet | 0.76 | **0.7643** |

K-OSDA/ERI（1,190 结构）：

| 模型 | 论文报告值 | 本工作复算值 |
|---|---|---|
| eSEN-30M-OAM | 0.02 | **0.0198** |
| CHGNet | 0.04 | **0.0411** |
| ORB-v3 | 0.07 | **0.0745** |
| EqV2(OC22) | 0.09 | **0.0876** |
| MatterSim | 0.09 | **0.0922** |
| PFP-v7 | 0.11 | **0.1102** |

- 两体系中 eSEN 均最小。
- 全部 11 个共有模型（含 GFN-FF、ORB、eqV2 变体）的 Cu/CHA RMSE 都大于其 ERI RMSE（`cu_cha_harder_than_eri_all_models` 全部为 true），确认"含过渡金属的 Cu/CHA 更难预测"。

### C3 —— eSEN "最一致" claim

- 在论文报告模型集合（CHGNet / ORB-v3 / MatterSim / eSEN / PFP-v7 / EqV2-OC22）内，eSEN 在三体系（纯硅/Cu-CHA/K-OSDA-ERI）全部排第 1（RMSE 最小）。
- 若把 `orb`（旧版 ORB，不在论文报告集内）也计入纯硅排序，eSEN 在纯硅排第 2；不影响论文 claim。

## 与论文口径的差异与局限

- 相对能量、参考结构（quartz / DFT 每原子能量最低结构）、每 Si / 每原子归一化、单位换算均严格按论文口径，复算值与论文 Table 3/4 在舍入误差内一致（本工作复算 eSEN 纯硅 0.4386，论文 0.44）。
- Table 2（纯硅 vs 实验热力学数据）需要论文 SI 中的实验 ΔH_f 值，未随冻结数据发布，本任务不要求复算；未复算。
- `pfp` vs `pfp_shifted` 在相对能量口径下等价，本报告用两者中任一均得到同一 RMSE。
- 设备：CPU（20 核）单进程；未使用 GPU。脚本限制内存按需加载。

## 数据来源与许可

- 论文：S. Ito, K. Muraoka, A. Nakayama, "Benchmarking Universal Interatomic Potentials on Zeolite Structures", arXiv:2509.07417 (2025)。
- 官方数据：Zenodo record 17075635，DOI 10.5281/zenodo.17075635，version 1.0 (2025-09-08)。
- 许可：CC BY-NC-ND 4.0（非商业、禁止演绎）。
- 校验：zip SHA-256 `f8214b63e39c6d3e3f84bfe6bcf7cf5c44140074de5d12de4085921131a7f3d1` 已核对一致。
- 代码：`agent_solution/code/analyze_zeo.py`（含校验、解压、解析、全部 RMSE 计算与证据表输出）。
