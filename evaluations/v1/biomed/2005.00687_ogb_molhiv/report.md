# EVAL REPORT: 2005.00687_ogb_molhiv

- 执行 agent: opencode (deepseek-v4-flash via agtcloud)
- 评测裁判: SciSolveBench LLM 裁判（qwen3.7-max）
- 评测时间: 2026-08-20

## 总分: 100 / 100

| 评分项 | 得分 | 满分 | 说明 |
|---|---:|---:|---|
| A 核心结果达成度 | 60 | 60 | A1（20分）：agent报告总图数41,127，train/valid/test划分为32,901/4,113/4,113，全局正例率3.509%，与rubric要求的精确统计和官方划分完全一致，得20分。A2（20分）：agent实现了GNN（GIN/GCN及虚拟节点变体）与非图基线（MLP-mean9/MLP-ext/LogReg/RF），两类均实现，得20分。A3（20分）：agent报告GNN test AUC在71.95%~74.16%之间，落入70-80%区间；显著高于任务指定的非图基线MLP-mean9（64.39%）；虚拟节点带来正向提升（GIN+vn 74.16% > GIN 73.33%），方向一致且在区间内，得20分。 |
| B 证据真实性 | 25 | 25 | 提交物包含完整的code/与results/目录，evidence_table.csv列完整。抽查字段1：data_statistics.json中行数32901/4113/4113与冻结数据一致。抽查字段2：evidence_table.csv中GIN test AUC为0.7333，与model_results.json中5个种子（0.6894, 0.7301, 0.7539, 0.7324, 0.7607）的均值计算严格吻合，内部数值高度一致。论文锚值（75%左右）与实测值（71-74%）明确区分，无抄数嫌疑。 |
| C 方法与报告 | 15 | 15 | C1（5分）：使用PyG构建5层GIN/GCN，配合Mean pooling与MLP读出头，超参数与早停策略合理。C2（5分）：明确声明测试集仅用于最终评估，早停仅依赖valid AUC，且固定随机种子，防泄漏措施严密。C3（5分）：report.md与claim.md结构完整，包含详实的方法、结果、局限性讨论（如指出强聚合特征非图基线MLP-ext与GCN性能接近的客观现象）及明确的结论标签。 |

## A 核心结果达成度（60/60）

A1（20分）：agent报告总图数41,127，train/valid/test划分为32,901/4,113/4,113，全局正例率3.509%，与rubric要求的精确统计和官方划分完全一致，得20分。A2（20分）：agent实现了GNN（GIN/GCN及虚拟节点变体）与非图基线（MLP-mean9/MLP-ext/LogReg/RF），两类均实现，得20分。A3（20分）：agent报告GNN test AUC在71.95%~74.16%之间，落入70-80%区间；显著高于任务指定的非图基线MLP-mean9（64.39%）；虚拟节点带来正向提升（GIN+vn 74.16% > GIN 73.33%），方向一致且在区间内，得20分。

## B 证据真实性（25/25）

提交物包含完整的code/与results/目录，evidence_table.csv列完整。抽查字段1：data_statistics.json中行数32901/4113/4113与冻结数据一致。抽查字段2：evidence_table.csv中GIN test AUC为0.7333，与model_results.json中5个种子（0.6894, 0.7301, 0.7539, 0.7324, 0.7607）的均值计算严格吻合，内部数值高度一致。论文锚值（75%左右）与实测值（71-74%）明确区分，无抄数嫌疑。

## C 方法与报告（15/15）

C1（5分）：使用PyG构建5层GIN/GCN，配合Mean pooling与MLP读出头，超参数与早停策略合理。C2（5分）：明确声明测试集仅用于最终评估，早停仅依赖valid AUC，且固定随机种子，防泄漏措施严密。C3（5分）：report.md与claim.md结构完整，包含详实的方法、结果、局限性讨论（如指出强聚合特征非图基线MLP-ext与GCN性能接近的客观现象）及明确的结论标签。

## 证据与重算说明

独立重算未执行。基于静态代码与结果文件审查：evidence_table.csv中记录了gin(0.7333)、gin-vn(0.7416)、gcn(0.7195)、gcn-vn(0.7201)等关键实测test AUC；metrics.json与runs/*.json中的单种子明细数据相互印证，证据链闭环且真实可信。

## 结论

- **科学结论**: `supported`
- 亮点: 实验设计严谨，多模型多基线对比全面；对虚拟节点增益的种子敏感性以及强非图基线（MLP-ext）的表现进行了客观且深入的局限性讨论，未盲目夸大GNN优势。
- 不足: 部分非图基线（如LogReg/RF/MLP-ext）仅使用了单一固定种子（seed=42）进行评估，未像GNN那样报告多均值与标准差，在基线对比的统计显著性上略显单薄。