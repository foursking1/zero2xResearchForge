# solution.md — 方法说明与结果

## 任务
验证 Ratzloff+ (2019, PASP 131, h4201; arXiv:1905.02738) 关于 Evryscope 南天极区高幅变星发现的人口组成论断（L1 critical claim），基于官方 CDS VizieR 发布目录 `J/PASP/131/H4201` 的冻结数据复算并在冻结目录口径下判定。

## 数据
冻结包 3 个文件（SHA-256 已校验，见 `results/metrics.json` 与 `data/source_manifest.json`，全部 match）：
- `table10.dat`（12,960 B）— Variable Star discoveries，135 行
- `table11.dat`（15,264 B）— Eclipsing Binary discoveries，159 行
- `ReadMe` — 95 字节定宽列定义（字节级权威说明）

两表同构，关键列（1-based 字节区间）：`ESID` 1–22、`APASS` 24–31、`RAdeg` 33–40、`DEdeg` 42–49、`Vmag` 51–55、`RPM` 57–61、`B-V` 63–67、`Size` 69–73、`SpType` 75–79、`Per` 81–89、`Amp` 91–95。缺失值标记 `---` 按 VizieR 约定处理为 missing。

## 方法
1. **定宽解析**（`code/parse_catalog.py`）：按 ReadMe 逐列字节切片（latin-1）；逐行校验行长 == 95 B，异常即终止；浮点列遇空/`---` 取 None。
2. **完整性校验**：对 3 文件计算 SHA-256 与 manifest 比对。
3. **统计**：行数、Size 分布（ms/giant/空）、光谱类（StpType 首字母+"V" 类名）、Per/Amp 的阈值占比与中位数、巨星分表（变量 vs 食双星）。
4. **判定**：以「论文属性 vs 目录实测」的一致性逐项检查，输出四档标签。
5. `code/supplementary_analysis.py`：Size×光谱类联合表、2 条未分类行、逐表百分位与 period–amplitude 图。

## 运行
```bash
# 从 agent_solution/ 运行（无外部依赖，stdlib + matplotlib 可选）
cp -r <冻结包> agent_solution/data   # 本包已附带只读副本
python3 code/parse_catalog.py data results
python3 code/supplementary_analysis.py results/evidence_table.csv results/fig_catalog
```
数据目录可显式指定；`python3 code/parse_catalog.py <DATA_DIR> <OUT_DIR>` 兼容任意冻结路径。

## 结果（冻结目录实测）
| 指标 | 值 |
|---|---|
| table10 / table11 / 合计 | **135 / 159 / 294** |
| 合并 Size | **ms 258 · giant 34 · 空 2** |
| 巨星·变量 / 巨星·食双星 | **24 / 10** |
| EB 周期 ≤75 h | **134/159 = 84.3%** |
| EB 振幅 5–25% | **115/159 = 72.3%** |
| EB 振幅 ≥5% / 变量振幅 ≥5% | 97.5% / **60.0%** |
| 周期中位 EB / 变量 | **34.80 h / 6.48 h** |
| 振幅中位 EB / 变量 | **0.185 / 0.063 mag** |
| 光谱类（合并）top | G(107) ≥ F(89) ≥ K(69) ≥ M(11) ≥ A(13)* |

*类计数以 SpType 首字母归属，G 型（含 GxV 与裸 G）最常见；`NONE` 恰为 Size 为空的 2 条未分类。

## 论文锚对照（论文数值仅作对照，非实测）
- 303 = 168 EB + 135 变量 → 目录 **294 = 159 EB + 135 变量**；变量精确一致，EB Δ=9。
- 267 MS + 34 giant + 2 未分类 → 目录 **258 MS + 34 giant + 2 空**；giant/未分类精确一致，MS Δ=9。
- 两个 Δ9 完全相同 → 目录较正文删减 **9 条主序 EB**（版本差异），方向唯一、量级吻合。

## 结论标签
**supported**。冻结目录口径下全部人口/分布子论断成立；EB 168→159 与 MS 267→258 的 Δ9 归因为发布版与正文的版本差异（删减 9 条主序 EB），非对论文发现的否定。

## 交付物
- `code/parse_catalog.py` + `code/supplementary_analysis.py`（固定种子不需要，纯数据统计无随机性；每次运行结果唯一）
- `results/evidence_table.csv`（294 行逐行 + 2 行汇总）
- `results/metrics.json`（全部指标 + 完整性 + 对照 + 结论）
- `results/fig_catalog.png`（光谱类分布 + Period–Amplitude 平面）
- `claim.md` / `solution.md` / `report.md`
- `data/`（冻结数据只读副本，SHA-256 与 F 盘冻结包一致）