# paper-bench 仓库整理与 GitHub 提交计划

> 状态：执行中（2026-08-28 启动）
> 目标：把当前 28GB 的脏仓库整理成可提交的干净基准仓库，并把 legacy 任务**完全合并去 legacy 化**进 main。

---

## 一、已确认的总决策

1. **仓库策略**：全新干净仓库——备份旧 `.git` 到 `../paper-bench.git.backup`，重新 `git init`，只纳入精选树（pack 从 28GB 降到几十 MB）。
2. **legacy 范围**：保留 23 张小卡定义（2604.04518v1 仅排除其 23GB `agent_solution/workspace`）。
3. **work/ 整理**：精选脚本迁 `evaluation/`、结果迁 `results/`，`work/` 整体 gitignore（不删除磁盘文件）。
4. **去 legacy 化（新增）**：24 张 legacy 卡合并进 `tasks/<domain>/`，与 main 完全等同，**不保留 origin 标记**；顶层不再有 `tasks_legacy/`。

---

## 二、24 张 legacy 卡 → 域归属映射

| 域 | 卡 ID（共 24） |
|---|---|
| **earth** (+6) | 08_tapley_2004, bensen_2007, bonjean_2002, gehlen_2019, pages2k_2019, wong_2020 |
| **biomed** (+6) | 2604.04477v1, 2604.04518v1(23GB), 2604.04842v1, 2604.04858v1, 2604.04878v1, 2604.04915v1 |
| **cs** (+12) | 2604.04673v1, 2604.04681v1, 2604.04832v1, 2604.04868v1, 2604.04871v1, 2604.04891v1, 2604.04895v1, 2604.04898v1, 2604.04911v1, 2604.04914v1, 2604.04923v1, 2604.04930v1 |
| astro (+0) | — |
| materials (+0) | — |

⚠️ 待复核判域：2604.04842v1 / 04915v1（临床 vs cs）、2604.04832v1（cs vs materials）。
合并后 5 域共 **125 张**（main 101 + legacy 24；earth26 / astro20 / cs32 / biomed27 / materials20——2026-08-31 核实更正，原"108+24=132"为过时估计），无 legacy 概念。

---

## 三、执行阶段

### 阶段 0 — 结构重组（去 legacy 化核心）
- `tasks_legacy/<id>/` → `tasks/<domain>/<id>/`（24 张，同卷 rename 瞬时完成）。
- `tasks/biomed/2604.04518v1/agent_solution/workspace/`（23GB）后续在 `.gitignore` 精确排除，定义文件正常跟踪。
- 清空后删除 `tasks_legacy/`。

### 阶段 1 — 统一卡片清单
- 合并 `valid_cards.csv` + `valid_legacy_cards.csv` → **一份 `cards.csv`**，列：`card_id, domain, level`。
- `l1l2_labels.csv`：24 张的 `domain=legacy` → 真实域；删除 legacy 标识。

### 阶段 2 — 评测脚本适配
- `agent_eval_full.py`：去掉 `BASE` 的 legacy 分支，`run_card` 永远 `tasks/<domain>/<id>`。
- `analyze_cards.py`：从统一 `cards.csv` 生成（扫描 `tasks/*/<id>` 并 join level）。
- `gen_legacy_cards.py`：**弃用，不迁入 evaluation/**（legacy 概念已移除）。
- `legacy_data_inventory.py`：重写为扫 `tasks/` 的**通用数据设计审计工具**（覆盖原 legacy 卡，无 legacy 假设），迁入 `evaluation/`。
- `summarize_agent_eval.py`：域汇总自然纳入，无需 origin 维度。
- 其余探索性脚本（poc_zen_eval / build_legacy_tasks / verify_legacy_copy / parse_legacy_truth / update_legacy_paths / compare_v5_v7 / verify_proto / patch_v7_fix / recalib_v51 / agg_scores / audit_discrimination / difficulty_correlate / prep_data / selftest / finalize_v6）留在 `work/`（gitignore），不迁入。

### 阶段 3 — `.gitignore`
- 删 `tasks_legacy/` 整目录忽略；改加 `tasks/biomed/2604.04518v1/agent_solution/workspace/`。
- 保留 `tasks/*/*/data/` 与全局 `*.npy/*.pt/*.ckpt/*.pth/*.safetensors/*.onnx/*.h5/*.hdf5`。
- 补 `work/`、根目录 `power_upload.zip`、`speedtest.bin`、`solubility.tar.gz`、`*.bin`、`t4_run*.log`、`L3_problem.md.txt`、`dl.ps1`、`*.whl`、`_venv*/`、`_tmp_deps/`、`data_cache/`、`*.tmp`。

### 阶段 4 — 文档 + 工作树精选
- 新建 `README.md`（项目/基准结构/如何跑评测）、`LICENSE`、`requirements.txt`、`DATA.md`（外部数据取回：tasks/*/data、23GB legacy workspace、scisolvebench-assets、candidate-papers；说明部分卡源数据在 F:/dataset、E:/scisolvebench-data 沙箱不可跑——不单独标 legacy）。
- 精选脚本迁 `evaluation/`、结果迁 `results/`（同前清单）。`work/` 整体 gitignore，不删磁盘文件。

### 阶段 5 — 干净重建 + 推送 ✅ **已完成（2026-08-28）**
- 采用孤儿分支重建（保留工作树与旧对象，不删数据）：清空分支引用 → 标准索引 `git add -A` → 提交 → `reflog expire` + `gc` 回收旧对象。
- **实际结果**：分支 `main`，单提交 `d6c6368`；树内 **4391 文件 / 125 张卡**；**0 个 >50MB**；**size-pack 40.05 MiB**（原 28.21 GiB）；密钥泄露 0 处；工作树 125 张 TASK.md 完好。
- 校验通过：域分布 earth26 / astro20 / cs32 / biomed27 / materials20；cards.csv、l1l2_labels.csv、README.md、.gitignore、.gitattributes 全部入库。
- ⚠️ 关键坑（详见 `.workbuddy/memory/2026-08-28.md`）：IDE 的 `git status` 监控卡死并长期霸占 `.git/index.lock`（杀后重生）→ 必须 `taskkill /F /IM git.exe` 后**立刻**清锁并 `git add -A` 抢锁；`GIT_INDEX_FILE` 指向 `.git/` 外会失败并产生**空树提交**，务必用标准索引路径。
- `git remote add origin <URL>` → `git push -u origin main`（**URL 待用户提供**）。

---

## 四、验证清单（2026-08-31 全部核实通过）
- [x] `tasks_legacy/` 已不存在；24 张卡均在 `tasks/<domain>/`。
- [x] `cards.csv` 含 125 卡（card_id, domain, level），无 domain=legacy。
- [x] `l1l2_labels.csv` 无 legacy 标识。
- [x] 评测脚本无 `tasks_legacy` 引用（2026-08-31 改写注释措辞后通过）。
- [x] `git ls-files` 无 >50MB 文件；pack 40.05 MiB。
- [x] README/DATA.md 不再提 legacy 独立目录。

## 五、待确认事项
1. 三张卡域归属（见 ⚠️）。
2. GitHub 仓库 URL（用于 push）。

---

## 六、收尾清理（2026-08-31）
- `tasks/earth/` 下 7 个杂散监控脚本（`_finalize.py`、`_monitor.py/.sh`、`_monitor_status.txt`、3 个 `watchdog_*.sh`）迁入 `work/`（gitignore，不删磁盘文件）。
- `evaluation/` 3 个脚本的注释去掉 `tasks_legacy` 字样（代码路径本已统一）。
- `README.md` 卡数修正为 125（101 main + 24 legacy）；legacy 目录提法改为统一路径说明。
- 附带发现：`.git` 中仍有 22.24 GiB 松散旧对象（orphan 重建前遗留），不影响仓库内容，可用 `git gc --prune=now` 回收磁盘。
