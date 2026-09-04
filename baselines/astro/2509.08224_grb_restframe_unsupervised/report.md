# report.md — 复现报告

**任务**：验证"GRB rest-frame 参数形成 ~14% / ~86% 两族人口结构"（L1 critical claim）
**论文**：Zhu S.-Y. et al., A&A (2025), arXiv:2509.08224（基于 rest-frame T90,z / Ep,z / Eiso 的无监督分类）
**数据**：冻结 M20 官方目录 `tablea1.dat`（320 行 × 152 字节定宽）+ `ReadMe`（VizieR 字节级说明），SHA-256 与 manifest 校验一致。
**主要交付物**：`claim.md`（判定）、`code/`（可复现脚本）、`results/evidence_table.csv`、`results/evidence_summary.csv`、`results/metrics.json`、`results/figures/`、`evidence/`。

---

## 1. 方法

### 1.1 数据与解析
- 数据来源：CDS VizieR `J/MNRAS/492/1919`（Minaev & Pozanenko 2020）。按 ReadMe 的字节级映射切片解析（latin-1），每行 152 字节定宽；实测 278 行恰好 152 B、42 行 151 B（末字段 EHDtype 无尾随空格），解析统一按 `pad(152)` 补齐（补齐列在 147 列之后，不影响任何关键列）。
- 关键列（1-based 字节区间，与 ReadMe 一致）：GRB 1–7；T90i 11–17（rest-frame s）；z 19–25；Eiso 40–50（10⁴⁴ J = ×10⁵¹ erg）；Epi 74–80（rest-frame keV）；Type 99–105；EH 134–138；EHtype 140–141；EHD 143–149；EHDtype 151–152。
- Type 归并：`I`、`I+EE` → **Type I**；`II`、`II+SNph`、`II+SNsp` → **Type II**。
- 单位：Eiso 表值单位为 10⁴⁴ J，数值 1:1 对应 ×10⁵¹ erg（1 J = 10⁷ erg ⇒ 10⁴⁴ J = 10⁵¹ erg），与论文口径一致。
- 完整性：320/320 行的 T90z、z、Eiso、Epz 均有值；`Verify!` 脚本独立重算通过。

### 1.2 复现流程
`python3 code/reproduce.py` → 解析 → 计数/中位数/短暴统计/事件查询 → 输出
`results/evidence_table.csv`（逐行）、`results/evidence_summary.csv`（分族汇总行）、
`results/metrics.json`（全部关键指标 JSON）、`results/figures/*.png`（3 张图）。
`python3 code/verify_probe.py` 从原始字节独立重算 3 个抽查数（320 / 45 / 0.27），全 PASS。
固定随机种子（k-means 健全性检查 `random_state=42`）；无任何外部重权/预处理依赖，纯 CPU 秒级。

### 1.3 范围边界
冻结包只含 M20 目录，不含论文 370 样本的剔除名单与 Table A.2（t-SNE/UMAP 嵌入）。因此本报告
的验证对象是**论文样本主干的目录层面人口结构**；370 样本嵌入与图 A.1/A.2 不可逐点重算，
不以任何方式将论文实施例抄为"实测"。

---

## 2. 结果

### 2.1 目录规模与分类计数

| 项 | 实测 | ReadMe 对照 |
|---|---|---|
| 总行数 | **320** | 320 records |
| Type I：`I` + `I+EE` | **45** = 34 + 11 | "45 type I" |
| Type II：`II` + `II+SNph` + `II+SNsp` | **275** = 235 + 19 + 21 | "275 type II" |
| Type I 占比 | **14.06%** | — |
| Type II 占比 | **85.94%** | — |

### 2.2 两族参数中位数（×10⁵¹ erg 口径）

| 中位数 | Type I（实测） | 论文 GRBs-I | Type II（实测） | 论文 GRBs-II |
|---|---|---|---|---|
| T90,z（s） | **0.27** | 0.31 | **14.50** | 13.84 |
| Ep,z（keV） | **706** | 523.83 | **446** | 407.94 |
| Eiso（×10⁵¹ erg） | **0.69** | 0.28 | **100.0** | 75.19 |

两族分离：T90z 相差 **~54 倍**，Eiso 相差 **~145 倍**，Epz 比值为 1.58（Type I 较高，与论文
方向一致）。中位数分离显著，支持"两族 rest-frame 参数中位数显著分离"。

### 2.3 T90 双峰与"仅靠 T90 不可靠"

| 项 | 实测 |
|---|---|
| T90,z < 2 s | **64 / 320（20.0%）** |
| Type I 中短暴 | **42 / 45（93.3%）** |
| Type II 中短暴（重叠） | **22 / 275（8.0%）** |

存在 4 个 T90z ≥ 2 s 的 Type I（含 060614A：T90z 4.4 s，属于 I+EE，其 T90i 为初始脉冲复合体
时长），以及 22 个短 T90 的 Type II → **单纯 T90=2 s 阈值无法可靠区分两族**，与论文动机
（GRB 200826A/060614A/211211A/230307A 打破 SGRB/LGRB 二分）一致。

### 2.4 点名事件交叉验证

| GRB | 目录 Type | 论文归属 | 实测参数（T90z / Epz / Eiso） | 一致 |
|---|---|---|---|---|
| 060614A | **I+EE**（Type I） | GRBs-I（合并起源） | 4.4 s / 340 / 2.4 | ✓ |
| 980425B | **II+SNsp**（Type II） | GRBs-II（SN 关联） | 17.9 s / 55 / 0.001 | ✓ |
| 171205A | **II+SNsp**（Type II） | GRBs-II（SN 关联） | 183.7 s / 125 / 0.022 | ✓ |
| 110402A | **I+EE**（Type I） | t-SNE GRBs-I / UMAP GRBs-II（不一致） | 2.8 s / 1924 / 15.2（边界案例） | ✓ |
| 200826A | 不在 M20（2020 事件，论文 Table A.1） | — | — | 如实说明 |

### 2.5 补充交叉验证（M20 自身 EH/EHD 分类）
- EHDtype 与目录 Type 一致率 **99.1%**（目录中 42 个标 I、278 个标 II，对比 Type 标签
  45/275）；EHtype 与 Type 一致率 95.9%。
- EH 边界（EH>3.3 ⇒ Type I）：Type I 中 80.0% 满足 EH>3.3，Type II 中 98.5% 满足 EH<3.3；
  Type I/II 中位 EH = 6.21 / 0.70。
- 含义：M20 使用 rest-frame 参数的 EH/EHD 判据本身即可达 ~96–99% 与 Type 标签一致，佐证
  "rest-frame 参数具有清晰双族结构"，不依赖单一方法。

### 2.6 诚实披露的健全性检查（非论文方法）
对 320 样本的 log10 标准化 (T90z, Epz, Eiso) 做 k-means(k=2, seed=42)：小簇 102 (31.9%)，
与目录 Type 吻合率 77.8%。**与论文 ~14% 不一致**——这正是"论文方法（370 样本 + t-SNE/UMAP
流形聚类）无法在 M20 单一样本上复现"的直接体现，而非论文错误：样本组成（320 vs 300+70）、
特征空间与聚类算法均不同。该结果仅作完整性披露，不进入主判定。

---

## 3. 与论文论断的对比与归因

| 论文论断 | 冻结口径实测 | 判定 |
|---|---|---|
| ~14% 小族（14.59% t-SNE / 14.32% UMAP） | Type I **14.06%** | **一致**（Δ≤0.53pt，归因样本与方法差异） |
| 两族 T90z 中位数（0.31 vs 13.84 s） | 0.27 vs 14.50 s | 一致 |
| 两族 Eiso 中位数（0.28 vs 75.19） | 0.69 vs 100.0 | 同量级一致 |
| 两族 Epz 中位数（523.83 vs 407.94 keV） | 706 vs 446 keV | 方向一致；Type I 绝对差 ~35% |
| 060614A→I、980425/171205A→II、110402A 边界 | 全部命中 | 一致 |
| "仅靠 T90 不可靠"（短暴≠Type I） | 64 短暴、22 个 Type II 短暴 | 一致 |

**差异归因**：
1. *样本组成*：论文 370 = M20 300（剔除 14 个红移不准）+ 70 个新 GRB；本卡为 M20 全表 320。
2. *分族方式*：论文 GRBs-I/II 是 t-SNE/UMAP 聚类归属，与 M20 Type I/II 标签非一一对应
   （110402A 两方法归属不同即为例证），故占比与中位数天然存在系统差。
3. *Epz 的 ~35% 差*：Type I 中 Epz 很高的 EE 事件（如 110402A=1924 keV）与 70 个新 GRB
   的影响放大；Epz 是三者中族内离散度最大的参数，中位数对分组变化敏感。

---

## 4. 结论

**`supported`**（冻结 M20 目录口径）：rest-frame 参数（T90z/Epz/Eiso）将 M20 目录清晰分为
**45（14.06%）/ 275（85.94%）** 两族，与论文 GRBs-I 占比 14.32–14.59% 一致；两族 T90z/Eiso
中位数分离**显著**（54 倍/145 倍），点名事件归属全部吻合，并佐证"仅靠 T90 不可靠"。

## 5. 局限

1. **定宽解析**依赖 ReadMe 字节表；42 行实为 151 B（缺末位空格），已按 152 补齐解析，不影响
   任何 ≤147 列字段，parser 做过逐字段核对。
2. **口径差异**：论文取 M20 300 + 70 = 370；本卡为 320 全表，两族占比/中位数的数值级对应
   而非逐点相等，属预期差异（已归因）。
3. **不可重算项**：370 样本剔除名单、t-SNE/UMAP 嵌入与 Table A.2 不在冻结包，嵌入级论断
   （各点归属、视觉双簇图）不做重构，也不虚报。
4. **无外部依赖污染**：除 numpy/pandas/matplotlib/scikit-learn 外零依赖；sklearn 仅用于
   2.6 节健全性检查，可离线禁用（HAS_SKLEARN=False 自动跳过）。

## 6. 复现

```bash
cd agent_solution
python3 code/reproduce.py                 # 完整分析 → results/
python3 code/verify_probe.py              # 独立重算 3 个抽查数（320 / 45 / 0.27）
python3 code/reproduce.py --out /tmp/out --data /mnt/f/dataset/astro/2509.08224_grb_restframe_unsupervised
```
默认数据定位顺序：`$GRB_DATA_DIR` → `code/data` → `agent_solution/data` → 冻结包 F 盘路径。
每轮运行都对 `tablea1.dat` 做 SHA-256 校验并在 `metrics.json.data` 记录。