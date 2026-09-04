# code/ 运行说明

对冻结 LUDB v1.0.1（200 条 × 12 导联 × 500 Hz × 10 s）复现
「多导联联合分割 vs 单导联基线」的完整评估。

## 依赖
Python 3.10+；`pip install -r requirements.txt`
（numpy, scipy, wfdb, matplotlib）。

## 数据路径
默认：`/mnt/f/dataset/biomed/1809.03393_ludb_ecg_delineation/ludb_1.0.1/data`
可用环境变量覆盖：
```bash
export LUDB_DATA_DIR=/path/to/ludb_1.0.1/data
```

## 运行
```bash
python3 run_all.py        # 全流程（计数→双方法分割→评估→evidence/metrics→表格）
python3 spot_check.py     # 裁判复核：record1 lead ii 符号统计 + evidence QRS Se/PPV
python3 make_figures.py   # 生成 evidence/*.png
```

`run_all.py` 固定评估协议：容差 ±150 ms（±75 样本 @500Hz）；
评估窗口 = 每条导联每类波 [首标注, 末标注]；跨记录聚合 TP/FP/FN → Se/PPV/m±σ。

## 模块
- `common.py`    配置、WFDB 读写、标注解析（波计算、滤波）
- `qrs.py`       Pan-Tompkins 类 QRS 检测 + onset/offset
- `waves.py`     P/T 波检测与边界
- `delineate.py` 逐导联分割 + 多导联一致性校正 + 单导联管线
- `evaluate.py`  评估（matcher、Se/PPV/m±σ、聚合）
- `run_all.py`   主流程
- `spot_check.py`、`make_figures.py`、`requirements.txt`

固定随机种子：无随机过程（确定性信号处理），结果可逐位复现。