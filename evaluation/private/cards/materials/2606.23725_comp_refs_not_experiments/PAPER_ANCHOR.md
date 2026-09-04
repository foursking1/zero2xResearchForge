# PAPER_ANCHOR（私有，勿随任务分发）

任务：`2606.23725_comp_refs_not_experiments`（L2）｜目标论文：*Computational references are not experiments: pre-registered validation of machine-learned sodium-cathode voltages*（arXiv:2606.23725，Krishna Teja Vepa，2026-06-30）

## 论文核心声称（一句话）

ML 电池材料筛选以**计算参考电压**（Materials Project PBE+U）训练与评估，而计算参考携带自身系统误差；在本论文的 Na-ion 阴极验证集上，筛选器相对实验文献电压的误差大到不可用于筛选，残差强烈依赖电压（加性校准无效），且误差主要由参考尺度（而非模型）贡献。

## 数值锚（全部来自论文正文/表格/图 + 官方仓库冻结数据交叉验证）

| 锚 | 指标 | 论文数值 | 出处 | 定义口径 | 容差 |
|---|---|---|---|---|---|
| A1 | 原始 held-out MAE（实验基准） | **0.668 V**（摘要 0.67 V） | 摘要；Table II 行"held-out, A/B only"（n=6, raw MAE 0.668）；官方 `s3b_litexp_summary.json` `raw_MAE_V=0.6682` | canonical n=6（tier A/B，maricite 因相鉴定不符被操作者审计剔除）；误差 = v_pred − v_lit | 全分 0.60–0.73 V；半分 0.47–0.87 V；其余 0 |
| A2 | 残差-实验电压 Pearson 相关 | **r = −0.939**（摘要 −0.94） | Sec. IV B（"Pearson r(err, V_lit) = −0.939"）；Fig. 2（r=−0.939）；官方 summary `voltage_dependence_pearson_r_signedErr_vs_Vlit=-0.939` | 7 个已预测行的 signed error vs v_lit | 全分 \|r−(−0.939)\|≤0.05；半分 ≤0.15；其余 0 |
| A3 | 预注册保守指标：留一法偏差校正后 MAE 的 95% bootstrap CI **上界** | **1.092 V**（摘要 1.09 V） | Table II 行"held-out, A/B only"（corr. MAE 0.802, corr. CI95 1.092）；Sec. III（主指标定义）；Methods VIII C；官方 summary `loocv_corrected_MAE_boot95` 上界 1.0919；官方脚本 `scripts/s3b_litexp.py`（LOO 校正一次 + 对校正误差 10,000 次重采样 + 97.5 分位） | 对 n=6（canonical）：行 i 的加性偏差 = 其余 5 行平均符号误差（留一、样本外），得校正误差向量；对校正误差做 10,000 次有放回重采样（np.random.default_rng(seed 20260609)），95% CI 上界 = 97.5 分位；本环境重算 1.0905–1.0919（RNG 版本差 <0.002 V）；判定阈值 0.50 V（>0.50 = not screening-grade，Sec. III 梯子） | 全分 0.94–1.24 V 且方法=样本外偏差校正+重采样 CI；半分 0.79–1.39 V（方法近似，如原始 MAE 的 bootstrap 上界≈0.98）；其余 0 |
| A4 | MP PBE+U 计算参考 vs 实验的系统偏差（两行均值） | **−0.538 V ≈ 0.54 V**（摘要"about 0.54 V below"） | Sec. V A（"0.539 V below … 0.538 V below"）；Fig. 3（V_MP−V_lit = −0.539/−0.538）；官方 summary `three_way_decomposition`（mp_minus_lit −0.539 / −0.5375） | 仅 NaCoPO4 两多形体（n=2）可三方比较：mean(v_mp − v_lit)；论文明确标注 n=2、方向性证据 | 全分 −0.44…−0.64 V；半分 −0.34…−0.74 V；其余 0 |
| A5 | 本地 PBE+U 基准偏移审计 sd(δ)（Li 4 对） | **0.31 V**（δ = +0.31/+0.48/+0.43/−0.20；sd=0.31） | Sec. VI；Table IV；官方 `d1_corrected_offsets.json`（offsets 0.314/0.4839/0.4338/−0.198；sd=0.3125，样本标准差 ddof=1） | δ = V_QME − V_exp，4 个 Li-ion 基准对；预注册门槛 sd≥0.30 V → 撤销绝对电压声称（FAIL）；n=3 核心对共用 +0.41 V（sd 0.087） | 全分 0.26–0.36 V；半分 0.20–0.42 V；其余 0 |

## 结论标签参考（供判分）

- 预期：对"计算参考≈实验、筛选器可用"的声称 → `contradicted`（在验证边界内）；因 n<20（F3 触发 provisional）也可论证为 `partially_supported`。
- 错误结论：`supported`（声称成立，屏幕可用/加性校准有效）→ A 相关锚按"数值未达"处理，C 结论校准扣分。
- 论文额外语境（不评分，供裁判理解）：74 化合物 MP 参考集 raw MAE 0.5892 V、家族偏差跨度 0.4419 V（F1 触发，Sec. IV A / Table I / Table III）；先验已发表基率 55/78=70.5%（Table III）；Na3V2(PO4)3 本地计算 2.8957 V vs 实验 ~3.4 V（方向一致）；预注册梯子：<0.30 screening-grade、0.30–0.50 ranking-only、>0.50 not screening-grade；F1 家族偏差跨度 >0.15 V 时无干净判决；F3 n<20 判决标 provisional。

## 锚真实性核对

- A1: 由冻结 `na_cathodes_validation.csv` 中 6 行（excluded_canonical=no）直接重算可得 0.6682（校验见 CALIBRATION）。
- A2: 由 7 行 signed_error vs v_lit 直接重算可得 −0.939。
- A3: 由 6 行 LOO 校正 + bootstrap（seed 20260609, 10,000 次）重算可得 1.0919。
- A4: 两行 (v_mp − v_lit) = −0.539 / −0.5375。
- A5: 四行 δ 的样本标准差 = 0.3125。
（全部数值可由冻结数据独立重算，无臆造。）