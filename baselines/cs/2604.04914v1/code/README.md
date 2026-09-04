# pensieve_verify — 可运行代码

Pensieve 符号性质验证复现的完整代码。只依赖 numpy / scipy / onnx / onnxruntime / matplotlib。

## 结构

```
code/
  run_analysis.py                 # 主分析：3 模型 × 24 查询 × 3 后端，增量写 ../results/analysis_results.jsonl
  make_figures.py                 # 从 jsonl 生成 results/figures/*.png
  make_evidence.py                # 生成 results/evidence_table.csv 与 results/metrics.json
  pensieve_verify/
    model.py                      # ONNX -> 序贯 ReLU 网络（精确提取 + 校验）
    verify.py                     # 比较网络构建、reduce、IBP、CROWN 线性松弛
    queries.py                    # VNN-LIB 解析
    heuristic.py                  # 随机 + 差分进化 + CMA-ES 反例搜索
    mip_verify.py                 # MILP 编码（HiGHS / scipy.milp），稀疏约束矩阵
    crown_bab.py                  # IBP+CROWN 分支定界（预检查含反例搜索）
```

## 运行

```bash
# 1) 全量分析（约 1 小时；可 `--models small --max-queries 2` 缩小验证）
python run_analysis.py

# 2) 图
python make_figures.py

# 3) 证据表与指标
python make_evidence.py
```

## 复算说明

- 所有数字只来自冻结数据 `F:\dataset\2604.04914v1\data\official\...`（原位读取）。
- `run_analysis.py` 每次运行先跳过已完成的 (model, prop, query, backend) 记录（断点续跑）。
- MIP/CROWN 时间预算：`--mip-timeout 20 --crown-timeout 20`（可调）。
- 反例的"certified"语义：`heuristic`/`crown_bab` 的 unsafe 均基于精确前向求值（witness 在
  onnxruntime 数值精度内还原网络输出）；`mip` 的 unsafe witness 额外用精确前向验证 max-margin ≤ 0。
