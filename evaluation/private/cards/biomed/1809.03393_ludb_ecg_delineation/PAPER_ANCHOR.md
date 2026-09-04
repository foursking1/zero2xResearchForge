# 论文锚：1809.03393_ludb_ecg_delineation

> 用途：LLM judge 判分基准（私有，仅裁判/编译者可见）。数值全部来自 arXiv:1809.03393v4（IEEE Access 2020, doi:10.1109/ACCESS.2020.3029211），禁止臆造。

## 锚清单（全部来自论文）

| # | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| 1 | 数据库规模 | 200 条记录 / 200 名受试者；12 导联；500 Hz；10 秒 | §I | 每条记录每导联 5000 样本 | 精确（可核验） |
| 2 | 标注总量 | 58,429 个波（P 16,797 / QRS 21,966 / T 19,666），全部导联独立标注 | §I / Table 1 | 与 QTDB 10,359（P 3,194 / QRS 3,623 / T 3,542）对比 | ±1%（冻结数据核验） |
| 3 | 容差 | ±150 ms（ANSI/AAMI EC57:1998） | §III | TP=参考点 150 ms 内；误差为自动点与人工点时间差 | 精确 |
| 4 | 多导联校正规则 | 复合波 ≥8/12 导联检出视为存在；≤1/3 导联检出则撤销；5-8 导联不做校正；参考点跨导联平均 | §II | 算法设计锚（方向性） | 方向性 |
| 5 | 多导联算法（Kalyakulina et al.）LUDB Se/PPV | P onset/peak/offset：Se 98.46%、PPV 96.41%；QRS onset/offset：Se 99.61%、PPV 99.87%；T peak：Se 99.03%、PPV 98.84%；T offset：Se 98.03%、PPV 98.84% | Table 6 | 全 200 条 × 12 导联，150 ms 容差 | 参照锚（±2 pp 内判方向一致） |
| 6 | 时间误差（Kalyakulina et al. LUDB） | P onset −2.7±10.02 ms；P peak −0.3±6.2 ms；P offset −0.4±11.4 ms；QRS onset −8.1±7.7 ms；QRS offset 3.8±8.8 ms；T peak 4.0±7.4 ms；T offset 5.7±15.5 ms | Table 6 | m±σ | 参照锚 |
| 7 | 单导联基线（ecg-kit）LUDB Se/PPV | P onset Se 88.26% / PPV 82.43%；P peak 89.64% / 83.73%；P offset 91.08% / 85.07%；QRS onset 99.52% / 91.36%；QRS offset 99.51% / 91.35%；T peak 85.62% / 94.91%；T offset 85.00% / 94.22% | Table 6 | 单导联工具 | 参照锚 |
| 8 | 主论断 | 多导联算法在 LUDB 上 P/T 波 Se/PPV 显著高于单导联 ecg-kit；QTDB（2 导联）上两者相当（P onset Se 97.46 vs 98.64） | §III 结论段 | 方向性锚 | 方向 |

## 备注
- 主论断：多导联联合分析显著提升 P/T 波分割精度；QRS 检测两者均近完美。
- 数据同源：PhysioNet LUDB v1.0.1（ODC-By 许可）即论文数据库；冻结数据与论文同一数据源。
- 判分提示：agent 不必复现论文绝对数值（实现细节不同）；以「多导联 P/T Se/PPV ≥ 单导联」方向 + QRS 保持高精度（≥97%）为主判据；若 agent 报告相反方向且方法合理，可判 contradicted 高分。
