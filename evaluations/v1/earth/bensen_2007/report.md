# EVAL REPORT: bensen_2007（Seismic ambient noise → surface wave dispersion, GJI 169:1239-1260）

- 执行 agent: Claude Code（deepseek-chat，经 DeepSeek Anthropic 兼容网关）
- 评测裁判: WorkBuddy（LLM 裁判，独立脚本重算）
- 评测时间: 2026-08-13

## 总分: 71 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---|---|---|
| A 核心结果达成度 | 32 | 60 | 任务范围 C01-C04 共 9 条锚（全为 compare/trend，无机器可读数值目标）：C01 物理结果复现成功但站对不匹配（HRV-PFO vs 论文 ANMO-HRV）；C02 机制验证通过但交叉相关 SNR 无法复现；C03/C04 冻结数据缺失 → inconclusive |
| B 证据真实性 | 25 | 25 | 独立重算 C01 六通带到达时间/群速度/SNR 全部逐位一致（1327s→1038s、Vg 3.02→3.87 km/s） |
| C 方法与报告 | 14 | 15 | 数据清单详尽、SNR 双口径、交叉相关布局判定严谨、局限诚实；扣 1 分：无敏感性分析 |

## A 核心结果达成度（32/60）

PAPER_ANCHOR 任务范围内（C01-C04）共 9 条规则（R01-R09），全部为 compare/trend 型（无目标数值）。

| 规则 | 类型 | agent 结果 | 判定 |
|---|---|---|---|
| R01（compare）C01 六通带瑞利波 | figure 对比 | 冻结包唯一宽带乘积为 HRV-PFO（非论文 ANMO-HRV），六通带全部出现清晰到达：SNR_tail 38.7–121.2、SNR_near 16.8–51.3，到达时间随周期增长单调提前（1327→1038s），群速度 3.02→3.87 km/s，标准大陆瑞利波频散 | ⚠️ 部分支持（物理复现成功，站对不匹配）|
| R02/R03（compare/trend）C02 五种归一化方法 | figure/趋势 | 无法复现交叉相关 SNR（原始双台日记录缺失）；在真实 Bhuj 地震波形上验证机制：one-bit 压缩 2.13/2.31×、running-mean 1.65/1.79×、water-level 1.53/1.65×、raw 1.0×、clipping 1.36×——方向与论文一致 | ⚠️ inconclusive（机制支持）|
| R04（compare）C03 CRLZ-HIZ 震波带调权 | figure | CRLZ/HIZ/NZ 台站在全部冻结数据中不存在 | ⚠️ inconclusive（数据缺失）|
| R05-R09（compare/trend）C04 谱白化 | figure | 白化实现在真实原始记录（BK.CMB）上验证有效（flatness −33%、峰 prominence −23%）；但 HRV 原始记录缺失，仅有的 HRV 迹是带限处理产物（1.4% 能量 > 0.14Hz），白化后无显著变平（flatness 0.65→0.69）→ 论文所述微震峰/26s 线无法验证 | ⚠️ inconclusive（数据缺失）|

→ C01 是唯一可直接测试的 claim 且物理结果复现成功（站对不匹配扣分）；C02-C04 因冻结数据缺失判 inconclusive（非 agent 过错，按规则不归零、给部分分）。加权约 32/60。

## B 证据真实性（25/25）

- **独立重算抽查（C01 六通带）**：裁判脚本用 obspy 1.5.0 从冻结 `12mo_2004_sym.mseed`（IU.HRV..LHZ, 86400 点, 1 Hz）独立做 4 阶零相位带通 + Hilbert 包络 + 300-4000s 窗口峰值检测 + 60000-86000s 尾部 RMS：

| 通带 | agent 到达(s) | 裁判到达(s) | agent Vg | 裁判 Vg | agent SNR_tail | 裁判 SNR_tail |
|---|---|---|---|---|---|---|
| 7-150s | 1327 | 1327 | 3.024 | 3.024 | 105.1 | 105.1 |
| 7-25s | 1327 | 1327 | 3.024 | 3.024 | 121.2 | 121.1 |
| 20-50s | 1206 | 1206 | 3.327 | 3.327 | 44.5 | 44.5 |
| 33-67s | 1090 | 1090 | 3.681 | 3.681 | 50.5 | 50.5 |
| 50-100s | 1045 | 1045 | 3.840 | 3.840 | 44.4 | 44.4 |
| 70-150s | 1038 | 1038 | 3.866 | 3.866 | 38.7 | 38.7 |

全部逐位一致 ✅；data_inventory.json 与 evidence_table.csv/metrics.json 交叉一致
- 代码可运行（explore/analyze_c01-c04/make_evidence 流水线，obspy 依赖）；未发现抄论文数字

## C 方法与报告（14/15）

- C1 方法合理性（5/5）：标准噪声处理流程（带通→包络→峰值/SNR）；SNR 给两种噪声窗定义（tail 60000-86000s 与 near 5000-20000s）消除口径歧义；**亮点**：对 `*_sym` 文件做了正负 lag 镜像检查（corr≈0.003）判定其为单边因果布局（zero lag @ sample 0），避免误读
- C2 稳健性（3/5）：SNR 双口径对照好；但无窗宽敏感性/多参数扫描（c02 压缩比仅 1 条记录 × 2 分量）
- C3 边界与结论（5/5）：结论标签正确且克制（partially_supported / inconclusive 分明），站对不匹配、原始数据缺失等 5 条局限全部如实列出，不夸大机制验证为 claim 验证

## 结论

- **科学结论**：论文核心方法论（六通带瑞利波提取、one-bit/running-mean 归一化抑制地震能量、谱白化）在冻结数据上得到机制层面支持，C01 的频散物理完全复现（但站对为 HRV-PFO 而非 ANMO-HRV）→ `partially_supported`
- 数据真实性满分（C01 全可重算且逐位一致）；A 扣分主因：C02-C04 冻结数据缺失（原始双台日记录、CRLZ/HIZ、原始 HRV 记录均不在包内）
- 备注：本包冻结数据为"真实数据子集"型，agent 对数据可用性边界（inventory 审计）做得非常扎实
