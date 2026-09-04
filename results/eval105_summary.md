# SciSolveBench eval105 评测汇总（A=A1+A2+A3 重构 + 分档 B，空壳≤20，contradicted≤50）

- 评测卡数: **17**
- 平均总分: **59.1** / 100
- 平均 A（核心结果达成度）: 37.5 / 60  = A1交付14.2/20 + A2保真13.7/25 + A3严谨9.6/15
- 平均 B（证据真实性/实际复现）: 26.4 / 40

## 总分分布

- <40 (空壳/未复现): 4 (24%) #########
- 40-59: 7 (41%) ################
- 60-69: 0 (0%) 
- 70-79: 1 (6%) ##
- 80-89: 0 (0%) 
- >=90: 5 (29%) ###########

## B 维度区分度

- B<=10 (空壳): 4 (24%)
- B 11-29 (部分): 4 (24%)
- B 30-40 (齐全): 9 (53%)

## A 子项分布（重构后）

- A1 交付实质 均值: 14.2 / 20 （占比 71%）
- A2 科学结论保真 均值: 13.7 / 25 （占比 55%）
- A3 方法严谨与可复现 均值: 9.6 / 15 （占比 64%）

## 结论分布

- supported: 6
- partially_supported: 4
- contradicted: 4
- inconclusive: 3

## 按领域均分

| 领域 | 卡数 | 均总分 | 均A | 均A1 | 均A2 | 均A3 | 均B |
|---|---:|---:|---:|---:|---:|---:|---:|
| astro | 1 | 100.0 | 60.0 | 20.0 | 25.0 | 15.0 | 40.0 |
| biomed | 2 | 50.0 | 30.0 | 10.0 | 12.5 | 7.5 | 20.0 |
| cs | 3 | 51.7 | 35.3 | 16.0 | 8.0 | 11.3 | 26.7 |
| earth | 6 | 45.3 | 26.8 | 11.0 | 10.2 | 5.7 | 18.5 |
| materials | 5 | 75.6 | 50.2 | 17.6 | 19.6 | 13.0 | 35.4 |

## 总分 ≤20 的卡（空壳/未真实复现 — 硬规则命中）

| 领域 | 卡片 | tier | A1 | A2 | A3 | A | B | 总分 | 结论 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| biomed | 1801.10193_deepdta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | inconclusive |
| earth | 1712.07835_rsicd | 1 | 8 | 0 | 0 | 8 | 5 | 13 | inconclusive |
| earth | 2010.00243_mlrsnet | 0 | 4 | 4 | 2 | 10 | 10 | 20 | inconclusive |

## 总分 Top 12

| 排名 | 领域 | 卡片 | A1 | A2 | A3 | A | B | 总分 | 结论 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | astro | 1905.02738_evryscope_variable_stars | 20 | 25 | 15 | 60 | 40 | 100 | supported |
| 2 | biomed | 2110.14795_medmnist_v2 | 20 | 25 | 15 | 60 | 40 | 100 | supported |
| 3 | materials | 2501.02144_gen_discovery_baselines | 20 | 25 | 15 | 60 | 40 | 100 | supported |
| 4 | earth | 1912.12171_so2sat | 20 | 25 | 15 | 60 | 38 | 98 | supported |
| 5 | materials | 1811.08425_small_xrd_classification | 20 | 20 | 15 | 55 | 40 | 95 | supported |
| 6 | materials | 2604.13897_molcryst_mlips | 14 | 12 | 15 | 41 | 35 | 76 | partially_supported |
| 7 | materials | 2207.04009_mg_mtp_defect_training | 14 | 16 | 5 | 35 | 22 | 57 | partially_supported |
| 8 | cs | 2311.04765_voraus_ad | 14 | 12 | 9 | 35 | 20 | 55 | partially_supported |
| 9 | earth | 1703.00121_resisc45 | 10 | 18 | 7 | 35 | 20 | 55 | supported |
| 10 | cs | 2509.16616_risky_investors_ranking | 14 | 6 | 10 | 30 | 20 | 50 | contradicted |
| 11 | cs | 2604.08131_gnn_misinfo | 20 | 6 | 15 | 41 | 40 | 50 | contradicted |
| 12 | earth | 2104.02846_multiscene | 14 | 6 | 0 | 20 | 30 | 50 | contradicted |

## 逐卡明细

| 领域 | 卡片 | tier | A1 | A2 | A3 | A | B | 总分 | 结论 |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| astro | 1905.02738_evryscope_variable_stars | 2 | 20 | 25 | 15 | 60 | 40 | 100 | supported |
| biomed | 1801.10193_deepdta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | inconclusive |
| biomed | 2110.14795_medmnist_v2 | 2 | 20 | 25 | 15 | 60 | 40 | 100 | supported |
| cs | 2311.04765_voraus_ad | 1 | 14 | 12 | 9 | 35 | 20 | 55 | partially_supported |
| cs | 2509.16616_risky_investors_ranking | 2 | 14 | 6 | 10 | 30 | 20 | 50 | contradicted |
| cs | 2604.08131_gnn_misinfo | 2 | 20 | 6 | 15 | 41 | 40 | 50 | contradicted |
| earth | 1703.00121_resisc45 | 1 | 10 | 18 | 7 | 35 | 20 | 55 | supported |
| earth | 1712.07835_rsicd | 1 | 8 | 0 | 0 | 8 | 5 | 13 | inconclusive |
| earth | 1912.12171_so2sat | 2 | 20 | 25 | 15 | 60 | 38 | 98 | supported |
| earth | 2010.00243_mlrsnet | 0 | 4 | 4 | 2 | 10 | 10 | 20 | inconclusive |
| earth | 2104.02846_multiscene | 2 | 14 | 6 | 0 | 20 | 30 | 50 | contradicted |
| earth | 2110.08733_loveda | 1 | 10 | 8 | 10 | 28 | 8 | 36 | partially_supported |
| materials | 1811.08425_small_xrd_classification | 2 | 20 | 20 | 15 | 55 | 40 | 95 | supported |
| materials | 2207.04009_mg_mtp_defect_training | 1 | 14 | 16 | 5 | 35 | 22 | 57 | partially_supported |
| materials | 2501.02144_gen_discovery_baselines | 2 | 20 | 25 | 15 | 60 | 40 | 100 | supported |
| materials | 2604.13897_molcryst_mlips | 2 | 14 | 12 | 15 | 41 | 35 | 76 | partially_supported |
| materials | 2606.23725_comp_refs_not_experiments | 2 | 20 | 25 | 15 | 60 | 40 | 50 | contradicted |
