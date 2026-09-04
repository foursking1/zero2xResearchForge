# solution.md — 方法与结果说明

任务：验证 Foschini et al. (2022, Universe 8, 587; arXiv:2211.03400) 关于 Fermi 4FGL
伽马射线源喷流 AGN 人口组成的核心论断（BLL 40% / FSRQ 23% / ~30% 无明确分类，最终样本 2,980）。
本方案在**冻结 4FGL-DR1 目录层**（CDS VizieR `J/ApJS/247/33`）重建最接近可复现口径并给出四档判定。

## 1. 数据与解析（权威来源 ReadMe "Byte-by-byte Description of file: 4fgl.dat"）

- 文件：`4fgl.dat.gz`（6,883,415 B）+ `ReadMe`（70,259 B），SHA-256 与 frozen manifest 一致。
- gzip 解压 `latin-1` 读取，逐行验证长度 = 4,104 字节（ReadMe `Lrecl=4104`，`Records=5065`），跳过末尾空行。
- 关键字节区间（1-based → Python slice，完全按 ReadMe）：
  - `Source_Name` 1–28（合并 `[4FGL]` + IAU 名；IAU 名本体为字节 1–18）
  - `GLON` 38–47、`GLAT` 49–58
  - `CLASS1` 3978–3982（表 7 分类码，**区分大小写**：小写=likely 关联，大写=identified）
  - `CLASS2` 3984–3986、`ASSOC1` 3988–4015
- 文件格式细节：VizieR .dat 在字节间隔处用 `|` 作分隔符渲染（等价于 ReadMe 的空字节），
  各字段内容严格占据 ReadMe 声明的字节范围——解析正确性由**全 33 类 CLASS1 计数与 ReadMe 表 7 的
  occurrence 数逐一吻合**以及 GLAT/GLON 数值物理合理（银盘集中、银河系中心方向密度高）双重验证。
- 无模拟/合成数据；不使用分隔符切列；`--seed 0` 固定（本任务无随机性，脚本纯确定性）。

## 2. 三个口径

1. **全空天**：5,065 行，唯一 `Source_Name` = 5,065。
2. **|b|>10°**（`|GLAT| > 10.0`）：3,646 源。
3. **论文口径样本**：`|GLAT|>10` 且 `CLASS1` 非空 且 剔除银河系/恒星形成类
   `{PSR,psr,spp,SNR,snr,PWN,pwn,glc,gal,sbg,SFR,sfr,hmb,HMB,lmb,LMB}` → **2,866 源**。

## 3. 关键结果

| 指标 | 实测（冻结 DR1 目录层） | 对照 |
|---|---|---|
| 总行 / 唯一源 | 5,065 / 5,065 | ReadMe Records=5065 ✓ |
| CLASS1 空（无对应体）全空天 | **1,336** | 4FGL 论文摘要 1,336 ✓ |
| \|b\|>10° 无对应体 | **657（18.0%）** | 论文未直接给出 |
| \|b\|>10° bcu（小写）/ BCU（大写）/ 合计 | 1,073 / 1 / 1,074（29.5%） | 抽查基准 1,074 ✓ |
| \|b\|>10° 无对应体+bcu | 1,731（47.5%） | 定义敏感度上界 |
| 论文口径重建样本 | **2,866** | 论文 2,980（Δ≈−3.8%，版本+重分类归因） |
| 样本内 BLL（bll+BLL） | **1,067（37.2%）** | 论文 BLL 40% |
| 样本内 FSRQ（fsrq+FSRQ） | **658（23.0%）** | 论文 FSRQ 23% |
| 样本内 bcu（bcu） | **1,073（37.4%）** | 论文"~30% 无明确分类"之目录代理 |
| 样本内 misaligned（rdg+RDG） | 38（1.3%） | 论文 2.8% |
| 样本内 NLS1+Sy+LINER | nlsy1+NLSY1 9（0.31%） | 论文 1.9% |
| changing-look AGN | CLASS 码不可表示 | 论文 1.1% |

**"~30% 无明确分类"敏感度**（分母/定义不同结果不同，需明确口径）：
- 仅无对应体（\|b\|>10° 分母）：18.0%；
- 样本内 bcu（最贴近论文口径）：37.4%；
- 无对应体 + bcu（\|b\|>10° 分母，含被论文排除的源）：47.5%。
论文的 ~30% 落在其中，等于其文献光谱重分类从 37% 左右的 bcu 中化解出部分明确分类。

## 4. 结论

**`partially_supported`**。数据规模与无对应体锚完全复现（5,065 / 1,336）；人口组成方向、量级一致
（FSRQ 23.0%≈23%，BLL 37.2%≈40%，无明确分类 37.4%≈30%），偏差由 DR1 vs DR2、论文文献重分类、
CLASS 码覆盖有限三点归因，非矛盾信号。

## 5. 复现运行

```bash
python3 code/analyze_4fgl.py  --data-dir <冻结数据目录> --outdir .
python3 code/verify_checks.py --data-dir <冻结数据目录> --outdir .   # 抽查 3 数 + 断言
python3 code/make_figures.py  --data-dir <冻结数据目录> --outdir evidence/figures
```

- `--data-dir` 也可通过环境变量 `FROZEN_DATA_DIR` 或默认候选路径（`data/`、F: 盘冻结目录及其
  WSL 挂载 `/mnt/f/dataset/astro/2211.03400_fermi_4fgl_jetted_agn`）解析。
- 产物：`results/evidence_table.csv`（全空天 / \|b\|>10° / 样本三层计数）、`results/metrics.json`
  （含对照与判定）、`results/sample_composition.csv`、`results/sample_source_membership.csv`
  （逐源可追溯）、`results/verify_checks.json`。
- 两套独立实现（手写字节切片 vs `pandas.read_fwf` colspecs）对抽查 3 数与全部关键计数给出**一致结果**。