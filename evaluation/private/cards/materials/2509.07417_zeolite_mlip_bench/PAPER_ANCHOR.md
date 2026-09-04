# PAPER_ANCHOR: 2509.07417_zeolite_mlip_bench（私有）

论文：Ito, Muraoka & Nakayama, "Benchmarking Universal Interatomic Potentials on Zeolite Structures", arXiv:2509.07417 (2025)。锚全部摘自论文正文/表格/图，并用冻结数据重算验证（编译期核对，2026-08-13）。

## 锚 1（主锚，A 维度，可复算）
- 指标名：纯硅沸石相对能量 RMSE vs DFT（Table 3，kJ/molSi）
- 论文数值：**SLC 7.40 / ClayFF 8.98 / BSFF 7.60 / UFF 44.55 / Dreiding 40.86 / GFN-FF 24.44 / CHGNet 3.60 / ORB-v3 1.01 / MatterSim 1.49 / eSEN(OMat) 0.44 / PFP-v7 1.33**
- 出处：Table 3（Sec "Reproducibility of experimental results for pure silica zeolites" 之后的扩展评估节）；正文："For the calculation of pure silica zeolites, eSEN shows the best performance among all tested universal IPs and MLIPs."
- 定义口径：相对能量 = 各势场总能量按每 Si 归一化、以各自 α-quartz 为参考；RMSE vs 同口径 DFT（PBE+D3）相对能量；单位 kJ/molSi（1 eV = 96.485 kJ/mol）；覆盖 229 个 IZA 拓扑（冻结数据全集）。
- 编译期重算（冻结数据）：eSEN=0.44 / ORB-v3=1.01 / MatterSim=1.49 / PFP=1.34 / CHGNet=3.60 / GFN-FF=24.49 / SLC=7.42 / ClayFF=9.00 / BSFF=7.62 / UFF=44.65 / Dreiding=40.95 —— 与论文一致（±0.1，舍入差异）。
- 容差（判定满分档）：每个关键值 ±0.05（Table 3 主值）/ ±0.5（解析势大值）；排序要求完全一致。

## 锚 2（主锚，A 维度，可复算）
- 指标名：含客体沸石相对能量 RMSE vs DFT（Table 4，kJ/molatom）
- 论文数值：
  - Cu/CHA：**CHGNet 0.76 / ORB-v3 0.24 / MatterSim 0.52 / eSEN(OMat) 0.14 / PFP-v7 0.24 / EqV2(OC22) 0.26**
  - K-OSDA/ERI：**CHGNet 0.04 / ORB-v3 0.07 / MatterSim 0.09 / eSEN(OMat) 0.02 / PFP-v7 0.11 / EqV2(OC22) 0.09**
- 出处：Table 4（Sec "Reproducibility of DFT results for guests containing zeolites"）；正文："the eSEN model again excels all the other MLIPs in both Cu/CHA and K-OSDA/ERI structures... it appears to be more difficult to accurately predict the DFT results of Cu/CHA zeolites."
- 定义口径：相对能量 = 各 MLIP 总能量按每原子归一化、参考相 = DFT 每原子能量最低的结构；RMSE vs DFT 相对能量；单位 kJ/molatom。Cu/CHA 347 个结构、K-OSDA/ERI 1,190 个结构。
- 编译期重算（冻结数据）：Cu/CHA eSEN=0.142/CHGNet=0.764/ORB-v3=0.240/MatterSim=0.520/PFP=0.245/EqV2=0.257；ERI eSEN=0.020/CHGNet=0.041/ORB-v3=0.074/MatterSim=0.092/PFP=0.110/EqV2=0.088 —— 与论文一致（±0.005）。
- 容差：±0.01（值 ≤0.30 的）/ ±0.03（值 >0.30）；排序要求一致。

## 锚 3（佐证/背景，不可从冻结数据复算）
- 指标名：纯硅相对能量 RMSE vs 实验热力学数据（Table 2，kJ/molSi，8 个有实验数据拓扑）
- 论文数值：**PBE(D3) 1.43 / SLC 4.41 / ClayFF 4.68 / BSFF 1.75 / UFF 15.99 / Dreiding 15.36 / GFN-FF 4.53 / CHGNet 2.84 / ORB-v3 1.88 / MatterSim 2.44 / eSEN 1.55 / PFP-v7 2.38**
- 出处：Table 2；正文 "DFT using the PBE functional with D3 correction shows the highest accuracy in reproducing experimental relative energies. One of the universal MLIPs, eSEN, exhibits the second-smallest RMSE value."
- 定义口径：相对能量（以 α-quartz 为参考）vs 实验热力学数据（引用文献 44 的 ΔH_f，论文 SI 有表）；忽略振动贡献。**实验值未随 Zenodo 发布，本任务不要求复算此表**；仅作辅助上下文。

## 辅助事实（裁判核查用）
- 摘要结论：GFN-FF 是通用解析势中最佳但无法满足精度；"All MLIPs can well reproduce experimental or DFT-level geometries and energetics. Among the universal MLIPs, the eSEN-30M-OAM model shows the most consistent performance across all zeolite structures studied."
- Fig. 3/正文：CHGNet 相对稳定拓扑存在系统误差；GFN-FF 在 SOS/RWY 型（陡 Si–O–Si 角/三员环）结构失真。
- 计算设置（Methods）：VASP 6.2.1，PBE+D3，PAW，520 eV 截断，0.02 eV/Å 最大残余力收敛；MLIP 用各自官方权重+D3。
- 数据源：Zenodo 10.5281/zenodo.17075635（CC BY-NC-ND 4.0）；论文 Data availability 声明明确指向该记录。
- 数据规模：Puresilica 229 拓扑（17 势场键齐全）；Cu_CHA 347（12 键）；KSDA_ERI 1,190（12 键）；`dft` 均含 pymatgen 弛豫结构。