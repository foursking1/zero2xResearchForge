# PAPER_ANCHOR: 2511.22885_mech_props_mlip（私有）

目标论文（隐藏）：arXiv:2511.22885v1。锚全部摘自论文原文（摘要/正文章节），禁臆造。冻结数据重算参考值附于每条（编译期完整性核对，非自测实验）。

## 锚 1（方向性：系统性偏差 / PES 软化）
- 指标：每模型体模量偏差中位数符号（KT）、每模型热膨胀偏差中位数符号（αV）
- 论文数值：**六个模型全部低估体模量、全部高估热膨胀**；正文中位数偏差（对模型平均）为 **KT −6.92 GPa、αV +11.38 MK⁻¹、Tdecomp +18.50 K**；KT 范围 −11.21~243.02 GPa、αV −64.10~152.09 MK⁻¹
- 出处：Abstract（"systematic underestimation of bulk modulus and overestimation of thermal expansion across all models, consistent with potential energy surface softening"）；Sec 3（"The median deviations from reference values, averaged across all models, are −6.92 GPa for bulk modulus, 11.38 MK−1 for CTE and 18.50 K for decomposition temperature"；"KT from −11.21 to 243.02 GPa … αV −64.10 to 152.09 MK−1"）
- 口径：Deltas 表每模型 Delta 中位数；论文"对模型平均"= 每模型先取中位数再对 6 模型平均
- 冻结数据重算：每模型 KT 中位数均 < 0（−4.87~−10.97 GPa）、每模型 αV 中位数均 > 0（+11.2~+21.5 MK⁻¹）→ 方向性完全复现；对模型平均中位数 = −6.62 / +14.96 / +18.50 K
- 容差：方向性无容差（必须全负/全正）；KT 中位数 ±2.5 GPa；αV 中位数 ±5 MK⁻¹；Tdecomp 中位数 ±8 K

## 锚 2（模型排序与总体平均误差）
- 指标：三指标（Bulk/CTE/Stability）平均 MAE(%) 的模型排名与前 3 数值
- 论文数值：**MACE-1 = 41%，fairchem_OMAT = 44%，Orb-v3 = 47%**（摘要 "average error across metrics and materials of 41 %, 44 %, and 47 %"）；总结论重申 "averaging at MAE of 44 % for our top performers"
- 出处：Abstract；Sec 4（"top-performing models, MACE-1, fairchem_OMAT, and Orb-v3 … averaging at MAE of 44 %"）；Figure 3
- 口径：每模型对三指标、全部材料的 MAE% 均值
- 冻结数据重算：mace-mp-0=40.0%、fairchem_omat=40.7%、orbital=43.7%（Deltas 表全材料）；前三排序一致，数值差 ≤3.3 pp
- 容差：前三集合与顺序必须一致；数值 ±5 pp（论文值 41/44/47）

## 锚 3（指标级 MAE 与任务特异精度）
- 指标：NVT 体模量 MAE（对方法平均）、CTE MAE（对方法平均）、fairchem_ODAC 分解温度 MAE 与总体 MAE
- 论文数值：**KT (NVT) MAE = 43.8% ± 6.9%**；**αV MAE = 76.2% ± 25.2%**；**fairchem_ODAC 总体 MAE = 66%、分解温度 MAE = 23%**；CaMn7O12 例子 **NPT 平均 9.3 GPa vs NVT 平均 197.8 GPa vs 实验 190 GPa**
- 出处：Sec 3（"the bulk modulus from NV T simulations … achieving an MAE of 43.8 %±6.9 %"；"CTE … MAE of 76.2 % ± 25.2 %"；"the example of CaMn7O12, where the NPT simulations yield an average value of 9.3 GPa, while the NV T simulations give 197.8 GPa, which is much closer to the experimentally-determined value of 190 GPa"）；Sec 4（"fairchem_ODAC … low overall accuracy (MAE, 66 %) … predicting the decomposition temperature with a MAE of 23 %"）
- 口径：MAE% 对方法平均（6 模型）± 方法间标准差；CaMn7O12 NPT/NVT 对可用模型平均（NVT 197.8 为剔除 fairchem_ODAC 异常值后平均）
- 冻结数据重算：KT 42.5%±7.7、αV 76.6%±25.0、fairchem_ODAC 总体 63.9% / Stability 22.6%；CaMn7O12 NPT 平均 9.34 GPa、NVT（剔除 fairchem_odac）平均 197.79 GPa
- 容差：KT MAE ±4 pp（且 std ±3 pp）；αV MAE ±4 pp；fairchem_ODAC 总体 ±6 pp、Stability ±6 pp；CaMn7O12 NPT/NVT ±3 GPa

## 参考值锚（Table 3，供 B 证据核查对照）
- 出处：Table 3（13 材料 KT/αV/Tdecomp，各带文献引用）
- 关键值：MOF-5 KT=17.0 GPa、αV=−48 MK⁻¹、Tdecomp=673–783 K；CaMn7O12 KT=190 GPa、αV=19.5 MK⁻¹、Tdecomp=550 K；SiO2(β-cristobalite) KT=37 GPa、αV=32.7 MK⁻¹、Tdecomp=1986 K；Zr(WO4)2 KT=61.3 GPa、αV=−26.7 MK⁻¹、Tdecomp=1050 K
- 注：官方 Deltas 管线对分解温度参考封顶 1000 K（SiO2/CaMn7O12→1000），CaMn7O12 用 550 K、Zr(WO4)2 用 1050 K、UiO-67 用 670 K；聚合以 Deltas 表 Reference 列为准
- 容差：参考值数值本身无容差（表列值）；用于重算口径一致性核对