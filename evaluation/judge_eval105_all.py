#!/usr/bin/env python3
"""SciSolveBench eval105 — redesigned A (3 sub-components) + tiered B, evidence-gated.

A redesign (vs eval104's single anchor-deviation score):
  A (0-60) is now THREE sub-components, so scoring is task-agnostic (not just
  numeric-anchor comparison) and transparent:
    A1 交付实质 (0-12): did the agent produce the core deliverable at all?
    A2 科学结论保真 (0-33): does the result support the paper's core claim?
         - quantitative tasks: graded by fidelity to the reported effect (not strict %)
         - qualitative tasks (curve/trend/relationship/figure): by pattern match
    A3 方法严谨与可复现 (0-15): sound method (splits/baseline/no leakage), reproducible
  B (0-40) unchanged: tiered by evidence scan (empty<20, partial, strong 30/35/40).
  Evidence gating (tier0 A<=10,B<=10 => total<=20; tier1 A<=35,B<=29; tier2 A<=60,B<=40)
  and conclusion ceilings (partially<=70, inconclusive<=57, contradicted<=45) are kept.

Outputs eval105_scores.csv + EVAL_REPORT_v5.md (does NOT overwrite earlier versions).
"""
from __future__ import annotations
import argparse, csv, json, os, re, ssl, sys, time, threading, traceback, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from card_material import material_path

# ---------------------------------------------------------------- config
API_URL = "https://api.agtcloud.cn/v1/chat/completions"
API_KEY = os.environ.get("JUDGE_API_KEY", "")
BASE = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS = os.path.join(BASE, "tasks")
DEFAULT_MODEL = "qwen3.7-max"
WORKERS = 5
RETRY = 6
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

TEXT_EXT = {".md", ".txt", ".csv", ".json", ".py", ".ipynb", ".log", ".yaml",
            ".yml", ".rst", ".toml", ".cfg", ".out", ".tsv"}
BINARY_EXT = {".pt", ".pth", ".h5", ".hdf5", ".npy", ".npz", ".png", ".jpg",
              ".jpeg", ".gif", ".pdf", ".ckpt", ".bin", ".onnx", ".safetensors",
              ".zip", ".gz", ".tar", ".parquet", ".wav", ".mp4", ".ptc"}
PER_FILE_CAP = 45000
TOTAL_CAP = 70000
LOG_PATH = os.path.join(BASE, "results", "judge_eval105.log")
CSV_PATH = os.path.join(BASE, "results", "eval105_all_scores.csv")
REPORT_LEAF = "EVAL_REPORT_v5.md"
BASELINES = os.path.join(BASE, "baselines")
EVALUATIONS = os.path.join(BASE, "evaluations")
csv_lock = threading.Lock()
log_lock = threading.Lock()


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with log_lock:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    print(line, flush=True)


# ---------------------------------------------------------------- collection
def read_text(path: str, cap: int = PER_FILE_CAP) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            s = f.read(cap + 200)
        return s[:cap]
    except Exception as e:
        return f"(read error: {e})"


def collect_spec(card_dir: str) -> str:
    parts = []
    for name in ["TASK.md", "SCORE_RUBRIC.md", "PAPER_ANCHOR.md", "CALIBRATION.md"]:
        p = material_path(card_dir, name)
        if os.path.exists(p):
            parts.append(f"===== {name} =====\n" + read_text(p, 9000))
    return "\n\n".join(parts)


def collect_artifacts(asol: str) -> str:
    def score(p: str) -> int:
        low = p.lower()
        if low.endswith("report.md"):
            return 0
        if "evidence" in low and low.endswith(".csv"):
            return 1
        if low.endswith("evidence_table.csv"):
            return 1
        if low.endswith("metrics.json"):
            return 2
        if low.endswith(".md"):
            return 3
        if low.endswith(".csv"):
            return 4
        if low.endswith(".json"):
            return 5
        if low.endswith(".py"):
            return 6
        if low.endswith(".log"):
            return 7
        if low.endswith(".txt"):
            return 8
        return 9

    files = []
    for root, dirs, names in os.walk(asol):
        for n in names:
            ext = os.path.splitext(n)[1].lower()
            if ext in BINARY_EXT or ext not in TEXT_EXT:
                continue
            fp = os.path.join(root, n)
            try:
                if os.path.getsize(fp) > 600000:
                    continue
            except OSError:
                continue
            files.append(fp)
    files.sort(key=score)
    out, used = [], 0
    for fp in files:
        rel = os.path.relpath(fp, asol)
        txt = read_text(fp)
        if not txt.strip():
            continue
        block = f"\n----- submission/{rel} -----\n{txt}\n"
        if used + len(block) > TOTAL_CAP:
            if score(fp) <= 4 and len(block) < 8000:
                out.append(block); used += len(block)
            continue
        out.append(block); used += len(block)
    return "\n".join(out)


# ---------------------------------------------------------------- evidence scan (drives B + A ceiling)
def scan_evidence(asol: str) -> dict:
    d = {"n_files": 0, "has_metrics": False, "has_evidence_csv": False,
         "result_files": 0, "has_code": False, "evidence_samples": []}
    if not os.path.isdir(asol):
        return d
    for root, dirs, names in os.walk(asol):
        depth = root[len(asol):].count(os.sep)
        for n in names:
            p = os.path.join(root, n)
            try:
                sz = os.path.getsize(p)
            except OSError:
                sz = 0
            d["n_files"] += 1
            low = n.lower()
            if low == "metrics.json" or low.endswith("metrics.json"):
                if sz > 0:
                    d["has_metrics"] = True
            if "evidence" in low and low.endswith(".csv") and sz > 0:
                d["has_evidence_csv"] = True
                d["evidence_samples"].append(os.path.relpath(p, asol))
            if low.endswith(".csv") or low.endswith(".json") or low.endswith(".tsv"):
                if sz > 0 and depth <= 2:
                    d["result_files"] += 1
            if low.endswith(".py") and sz > 0:
                d["has_code"] = True
    return d


def evidence_tier(d: dict) -> int:
    """0=empty(no materialized result evidence), 1=partial, 2=strong."""
    if not d.get("n_files"):
        return 0
    if d.get("has_metrics") or d.get("has_evidence_csv"):
        return 2
    if d.get("result_files", 0) > 0:
        return 1
    return 0


def evidence_line(d: dict) -> str:
    tier = evidence_tier(d)
    if not d.get("n_files"):
        return "【磁盘证据扫描】submission 为空或不存在 —— 无任何提交物。证据等级=0(空壳)。"
    parts = []
    parts.append(f"文件总数={d['n_files']}")
    parts.append(f"metrics.json={'有' if d['has_metrics'] else '缺失'}")
    parts.append(f"evidence_table/evidence*.csv={'有' if d['has_evidence_csv'] else '缺失'}")
    parts.append(f"结果CSV/JSON文件数(≤2层)={d['result_files']}")
    parts.append(f"可运行代码(.py)={'有' if d['has_code'] else '无'}")
    parts.append(f">>> 证据等级={tier} "
                 f"({'空壳/无真产物→A≤10,B≤10,总分≤20' if tier==0 else '部分证据→A≤35,B≤29' if tier==1 else '证据齐全自洽→A,B可放开'})")
    if not d["has_metrics"] and not d["has_evidence_csv"]:
        parts.append(">>> 实测证据文件缺失：仅代码+报告散文，属'产生文件但未真实复现'→空壳硬规则")
    if d["evidence_samples"]:
        parts.append("证据样本: " + ", ".join(d["evidence_samples"][:4]))
    return "【磁盘证据扫描】" + "；".join(parts)


# ---------------------------------------------------------------- judge call
SYSTEM = (
    "你是一位严谨的科研任务评测裁判（SciSolveBench scientific scoring judge, eval105 版）。"
    "本版仅两维评分（A 核心结果达成度 + B 证据真实性），分数由【磁盘证据扫描】的证据等级硬性约束。必须遵守：\n"
    "1. 只依据提交物中的真实证据（代码、evidence 表、报告中的实测数值）打分；"
    "严禁把论文/锚值当作 agent 已复现的证据。\n"
    "2. A 维度（核心结果达成度，0-60）由三个子项相加，分别评判，提高清晰度与任务通用性：\n"
    "   【A1 交付实质 0-12】agent 是否产出了 TASK.md 要求的『核心交付物』（训好的模型 / 建好的数据集 / "
    "算出的结果表 / 复现的图等），不看数值大小。\n"
    "     · 12：核心产物完整产出（符合任务明确要求）\n"
    "     · 8：实质性产出但有明显缺口（覆盖不全 / 缺一个必需输出）\n"
    "     · 4：尝试了但核心产物缺失或非功能\n"
    "     · 0：无实质产物（仅代码 / 散文）\n"
    "   【A2 科学结论保真 0-33】结果是否支持论文的核心 claim（本维度权重最高，是拉开区分度的核心）。"
    "数值比较只是其中一种情形：\n"
    "     · 量化任务（有锚值）：按『与论文报道效应的匹配度』分级——复现了声称的效应 / 落在合理容差内→33；"
    "正确区间但数量级偏离(约10-20%)→26；方向对 / 定性匹配但弱→18；部分不支持 / 弱相关→10；不支持 / 矛盾→5；无关→0。"
    "关键：把『数值精度』与『科学正确性』解耦——即便确切数字因环境/随机性有差，只要复现了声称的效应/趋势仍可高分；"
    "但『结论未成立』（partially_supported / inconclusive / contradicted）时本维度必须给低档。\n"
    "     · 定性任务（复现曲线 / 趋势 / 关系 / 图）：按复现出的模式是否匹配论文描述的结论判分。\n"
    "   【A3 方法严谨与可复现 0-15】证据是否 sound：\n"
    "     · 15：方法 sound（正确划分 / 基线 / 无泄漏），结果可由提交物+冻结数据复算\n"
    "     · 10：轻微方法论顾虑\n"
    "     · 5：明显顾虑（可能泄漏 / 评估不当）\n"
    "     · 0：不 sound / 不可复现\n"
    "   【证据绑定】A1/A2/A3 中涉及『实测数』的部分，仅当该数有落盘 metrics.json/evidence_table 支撑时方可授予高分；"
    "若仅出现在报告散文而无对应 evidence 文件，对应子项最高授予该档下限。\n"
    "3. B 维度（证据真实性/实际复现，0-40）：必须依据下方【磁盘证据扫描】判定，不得仅凭报告散文。\n"
    "   - 空壳（metrics/evidence 均缺失，仅代码+报告声称）→ B ∈ [0,10]（<20 硬规则）。\n"
    "   - 部分证据（有结果文件但关键证据缺失/内部不一致/仅为脚本无输出）→ B ∈ [11,29]。\n"
    "   - 证据齐全自洽（tier=2）：进一步分档——\n"
    "       · 有 metrics.json 且内部自洽、并有校验/可复算证据（checksum 脚本或 evidence 表齐全）→ B=40\n"
    "       · 有 evidence 但部分缺失或自洽性一般 → B=35\n"
    "       · 有结果文件但较松散 / 仅单点 → B=30\n"
    "   - 抄论文数字当实测 / 明显测试段泄漏 → B ≤ 8，且 A 该数不可信。\n"
    "4. 本版取消 C 维度（方法与报告不再计分）。\n"
    "5. 【结论级硬上限（代码强制）】conclusion 决定 A2 与 B 的天花板：\n"
    "   - supported：A2 ≤ 33，B ≤ 40（满分档）；\n"
    "   - partially_supported：A2 ≤ 15，B ≤ 28，总分 ≤ 70；\n"
    "   - inconclusive：A2 ≤ 8，B ≤ 22，总分 ≤ 57；\n"
    "   - contradicted：A2 ≤ 5，B ≤ 20，总分 ≤ 45。\n"
    "   『过程完整但结论未成立』不得借 A1/A3 的过程分拿高分。\n"
    "6. 输出严格 JSON（不要 markdown 代码块包裹），字段见要求。\n"
    "7. 评分保守、有据，不赠送分数；每个维度给中文理由。"
)

USER_TMPL = """# 任务卡规范与评分标准
{spec}

# Agent 提交物（submission 文本证据）
{artifacts}

# 磁盘证据扫描（脚本实测，裁判须据此判 A/B 并受硬上限约束）
{evidence}

# 数值带匹配示范（务必严格遵循）
错误判例：rubric 注明「某指标 >0.70 判 0 分」，agent 报告该指标 = 0.5674，裁判却写「大于 0.70 判 0」并给 0 分。
正确判例：0.5674 不大于 0.70，绝不可套用 >0.70 的规则；应定位 0.5674 实际落入的区间（例如 (0.42,0.70] 半满带 → 对应分）。
铁则：先列出 agent 报告的关键实测数值（逐字引用），再逐一带入 rubric 的每个 band 条件做布尔判断，只对命中的 band 给分。

# 评分要求（仅两维，受证据等级硬约束）
请作为裁判打分并输出严格 JSON：
- A（0-60）= A1(0-12) + A2(0-33) + A3(0-15)，分别评判：
   · A1 交付实质：是否产出 TASK.md 要求的『核心交付物』（完整→12；有缺口→8；缺失/非功能→4；无→0）。
   · A2 科学结论保真（权重最高）：结果是否支持论文核心 claim。量化任务按『效应匹配度』（复现效应/容差内→33；偏离10-20%→26；方向对/弱→18；部分不支持→10；不支持/矛盾→5；无关→0）；定性任务按『复现模式是否与论文结论一致』判分。严禁死磕百分比，效应复现即可高分；但『结论未成立』（partial/inconclusive/contradicted）必须给低档。
   · A3 方法严谨与可复现：sound 且可复算→15；轻微顾虑→10；明显顾虑→5；不 sound/不可复现→0。
   受证据约束（见上方【磁盘证据扫描】）：证据等级=0（空壳）时 A 实际不得超过 10；等级=1 时 A 不超过 35；等级=2 时 A 不超过 60（脚本强制钳制，纯散文无 evidence 文件不得高分）。
- B（0-40）：严格依【磁盘证据扫描】判定：空壳→[0,10]；部分→[11,29]；齐全自洽(tier2)按强度分档→[30/35/40]。
- 【结论级硬上限（脚本强制）】：partially_supported 总分≤70；inconclusive 总分≤57；contradicted 总分≤45；supported 不设上限。给分时『结论未成立』卡的 A2/B 须明显保守。

JSON 字段（务必输出，数值用整数或一位小数）：
{{
  "A1": <0-12>, "A2": <0-33>, "A3": <0-15>,
  "B": <0-40>,
  "total": <A1+A2+A3+B>,
  "conclusion": "<supported|partially_supported|contradicted|inconclusive>",
  "A_notes": "<中文，分别说明 A1/A2/A3 的给分理由>",
  "B_notes": "<中文>",
  "evidence_notes": "<中文，含『独立重算未执行』标注与关键实测数>",
  "strengths": "<中文，1-2句>",
  "weaknesses": "<中文，1-2句>"
}}
只输出该 JSON。"""


def call_judge(card_dir: str, asol: str, model: str) -> dict:
    spec = collect_spec(card_dir)
    artifacts = collect_artifacts(asol)
    if not artifacts.strip():
        artifacts = "(submission 中未发现可读文本证据文件——可能仅有二进制模型权重/无报告)"
    ev = scan_evidence(asol)
    user = USER_TMPL.format(spec=spec, artifacts=artifacts, evidence=evidence_line(ev))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 2800,
    }
    last_err = None
    for attempt in range(1, RETRY + 1):
        try:
            req = urllib.request.Request(
                API_URL, data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {API_KEY}",
                          "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180, context=SSL_CTX) as r:
                raw = r.read().decode("utf-8", "replace")
            out = json.loads(raw)          # may raise -> retry
            content = out["choices"][0]["message"]["content"]
            return parse_json(content, ev)
        except Exception as e:
            last_err = e
            log(f"  API err (attempt {attempt}): {e!r}")
            time.sleep(min(2 ** attempt * 3, 30))
    raise RuntimeError(f"judge failed after {RETRY} attempts: {last_err}")


def parse_json(content: str, ev: dict) -> dict:
    s = content.strip()
    if s.startswith("```"):
        s = s.split("```", 2)[1]
        if s.lower().startswith("json"):
            s = s[4:]
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b != -1 and b > a:
        s = s[a:b + 1]
    d = json.loads(s)                       # raises on truncated -> caller retries
    # clamp + round A sub-components, then sum (v6: A1=12 / A2=33 / A3=15)
    a1 = min(12.0, max(0.0, round(float(d.get("A1", 0)), 1)))
    a2 = min(33.0, max(0.0, round(float(d.get("A2", 0)), 1)))
    a3 = min(15.0, max(0.0, round(float(d.get("A3", 0)), 1)))
    d["A1"], d["A2"], d["A3"] = a1, a2, a3
    d["A"] = round(a1 + a2 + a3, 1)
    d["B"] = round(float(d.get("B", 0)), 1)
    d["B"] = min(40, max(0, d["B"]))
    # ---- v6 conclusion ceilings (enforced in code): conclusion -> (A2cap, Bcap) ----
    concl = d.get("conclusion", "")
    a2cap, bcap = {
        "supported": (33, 40),
        "partially_supported": (15, 28),
        "inconclusive": (8, 22),
        "contradicted": (5, 20),
    }.get(concl, (33, 40))
    d["A2"] = min(d["A2"], a2cap)
    d["A"] = round(d["A1"] + d["A2"] + d["A3"], 1)
    d["B"] = min(d["B"], bcap)
    # ---- HARD evidence-gated ceilings (enforced in code) ----
    tier = evidence_tier(ev)
    amax, bmax = {0: (10, 10), 1: (35, 29), 2: (60, 40)}[tier]
    d["A"] = min(d["A"], amax)
    d["B"] = min(d["B"], bmax)
    d["total"] = round(d["A"] + d["B"], 1)
    if concl == "contradicted":
        d["total"] = min(d["total"], 45.0)
    for k in ("conclusion", "A_notes", "B_notes", "evidence_notes",
              "strengths", "weaknesses"):
        d.setdefault(k, "")
    return d


def write_report(card_dir: str, asol: str, d: dict, model: str, exec_agent: str):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# EVAL REPORT v5: {os.path.basename(card_dir)}")
    lines.append("")
    lines.append(f"- 执行 agent: {exec_agent}")
    lines.append(f"- 评测裁判: SciSolveBench LLM 裁判 v5（{model}）")
    lines.append(f"- 评测时间: {today}")
    lines.append("")
    lines.append(f"## 总分: {d['total']} / 100")
    lines.append("")
    lines.append("| 评分项 | 得分 | 满分 | 说明 |")
    lines.append("|---|---:|---:|---|")
    lines.append(f"| A1 交付实质 | {d.get('A1',0)} | 12 | |")
    lines.append(f"| A2 科学结论保真 | {d.get('A2',0)} | 33 | |")
    lines.append(f"| A3 方法严谨与可复现 | {d.get('A3',0)} | 15 | |")
    lines.append(f"| **A 合计** | **{d['A']}** | 60 | {d.get('A_notes','')} |")
    lines.append(f"| B 证据真实性/实际复现 | {d['B']} | 40 | {d.get('B_notes','')} |")
    lines.append("")
    lines.append("## A 核心结果达成度（%s/60 = A1 %s + A2 %s + A3 %s）" % (
        d["A"], d.get("A1", 0), d.get("A2", 0), d.get("A3", 0)))
    lines.append("")
    lines.append(d.get("A_notes", ""))
    lines.append("")
    lines.append("## B 证据真实性/实际复现（%s/40）" % d["B"])
    lines.append("")
    lines.append(d.get("B_notes", ""))
    lines.append("")
    lines.append("## 证据与重算说明")
    lines.append("")
    lines.append(d.get("evidence_notes", ""))
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append(f"- **科学结论**: `{d['conclusion']}`")
    lines.append(f"- 亮点: {d.get('strengths','')}")
    lines.append(f"- 不足: {d.get('weaknesses','')}")
    txt = "\n".join(lines)
    path = report_path(card_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(txt)


def detect_exec_agent(card_dir: str) -> str:
    for version in ("v5", "v2", "v1"):
        p = os.path.join(EVALUATIONS, version, os.path.relpath(card_dir, TASKS), "report.md")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="replace"):
                if "执行 agent" in line:
                    return line.split(":", 1)[-1].strip()
    return "opencode (deepseek-v4-flash via agtcloud)"


def append_csv(domain: str, card: str, source: str, level: str, d: dict, model: str):
    with csv_lock:
        new = not os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["source", "domain", "card", "judge_model", "tier",
                            "A1", "A2", "A3", "A", "B", "total", "conclusion",
                            "level", "timestamp"])
            w.writerow([source, domain, card, model,
                        evidence_tier_last.get((domain, card), ""),
                        d.get("A1", 0), d.get("A2", 0), d.get("A3", 0),
                        d["A"], d["B"], d["total"], d["conclusion"], level,
                        datetime.now().isoformat(timespec="seconds")])


# remember tier per card for csv (set during judge_one)
evidence_tier_last = {}


# ---------------------------------------------------------------- unified roots
# Task cards hold definitions; historical submissions live in baselines/.
# 3 层 taxonomy (zero2xResearchForge):
#   L1 论文复现        -> reproduce a specific paper claim(s) with scaffolding
#   L2 多步骤          -> multi-step / multi-component reproduction (pipeline)
#   L3 端到端科研      -> open end-to-end research re-discovery
# 标注为 L2 的卡映射为 L3；Main L1 按多步骤信号切分。


def _load_l1l2():
    d = {}
    p = os.path.join(BASE, "l1l2_labels.csv")  # 根目录统一清单
    if os.path.exists(p):
        import csv as _csv
        with open(p, encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                d[(row["domain"], row["card"])] = row["level"]
    return d


L1L2 = _load_l1l2()


def report_path(card_dir: str) -> str:
    return os.path.join(EVALUATIONS, "v5", os.path.relpath(card_dir, TASKS), "report.md")


def _multistep_signal(txt: str) -> bool:
    # >=2 top-level falsifiable sub-questions
    if len(re.findall(r"问题\s*\d+\s*[（(]", txt)) >= 2:
        return True
    if len(re.findall(r"\n\s*问题\s*\d+\b", txt)) >= 2:
        return True
    kw = ["多数据集", "融合", "pipeline", "多阶段", "多模型", "多任务",
          "多个数据集", "多组件", "交叉验证", "训练与评估", "训练.*评估.*对比"]
    return any(re.search(k, txt) for k in kw)


def level_for(source: str, domain: str, card: str, cp: str) -> str:
    lab = L1L2.get((domain, card))
    if lab == "L2":
        return "L3"
    t = ""
    for leaf in ("TASK.md", "CALIBRATION.md"):
        pp = material_path(cp, leaf)
        if os.path.exists(pp):
            t += open(pp, encoding="utf-8", errors="replace").read() + "\n"
    if _multistep_signal(t):
        return "L2"
    return "L1"


def completed_cards() -> list:
    res = []
    # Baselines are stored separately from task definitions.
    for d in sorted(os.listdir(TASKS)):
        dd = os.path.join(TASKS, d)
        if not os.path.isdir(dd):
            continue
        for card in sorted(os.listdir(dd)):
            cp = os.path.join(dd, card)
            if not os.path.isdir(cp):
                continue
            asol = os.path.join(BASELINES, d, card)
            if os.path.isdir(asol) and any(os.scandir(asol)):
                res.append((d, card, cp, "main"))
    return res


def parse_report_scores(cp: str) -> dict:
    """Parse an existing EVAL_REPORT_v5.md back into score fields."""
    txt = open(report_path(cp), encoding="utf-8",
               errors="replace").read()
    def g(pat):
        m = re.search(pat, txt)
        return float(m.group(1)) if m else 0.0
    A1 = g(r"\| A1 交付实质 \| ([\d.]+)")
    A2 = g(r"\| A2 科学结论保真 \| ([\d.]+)")
    A3 = g(r"\| A3 方法严谨与可复现 \| ([\d.]+)")
    A = g(r"\*\*A 合计\*\* \| \*\*([\d.]+)\*\*")
    B = g(r"\| B 证据真实性/实际复现 \| ([\d.]+)")
    total = g(r"## 总分: ([\d.]+) / 100")
    m = re.search(r"- \*\*科学结论\*\*: `([^`]+)`", txt)
    conclusion = m.group(1) if m else "?"
    return {"A1": A1, "A2": A2, "A3": A3, "A": A, "B": B,
            "total": total, "conclusion": conclusion}


def judge_one(item, model, force, skip_existing):
    domain, card, cp, source = item
    asol = os.path.join(BASELINES, domain, card)
    rep = report_path(cp)
    if (not force) and skip_existing and os.path.exists(rep):
        try:
            d = parse_report_scores(cp)
            ev = scan_evidence(asol)
            evidence_tier_last[(domain, card)] = evidence_tier(ev)
            lvl = level_for(source, domain, card, cp)
            append_csv(domain, card, source, lvl, d, model)
            log(f"REUSE {source}/{domain}/{card}: total={d['total']} "
                f"tier={evidence_tier(ev)} L={lvl}")
            return ("skip", domain, card, d)
        except Exception:
            pass  # fall through to re-judge
    try:
        ev = scan_evidence(asol)
        evidence_tier_last[(domain, card)] = evidence_tier(ev)
        d = call_judge(cp, asol, model)
        lvl = level_for(source, domain, card, cp)
        write_report(cp, asol, d, model, detect_exec_agent(cp))
        append_csv(domain, card, source, lvl, d, model)
        log(f"DONE {source}/{domain}/{card}: tier={evidence_tier(ev)} "
            f"L={lvl} A={d['A']} B={d['B']} total={d['total']} ({d['conclusion']})")
        return ("ok", domain, card, d)
    except Exception as e:
        log(f"FAIL {domain}/{card}: {e!r}\n{traceback.format_exc()}")
        return ("fail", domain, card, None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--source", default="", choices=["", "main"],
                    help="restrict to main (tasks/<domain>/) — legacy 已合并")
    ap.add_argument("--only", nargs="*", default=[],
                    help="domain/card substrings to restrict to")
    args = ap.parse_args()

    cards = completed_cards()
    if args.source:
        cards = [c for c in cards if c[3] == args.source]
    if args.only:
        pats = args.only
        cards = [c for c in cards if any(p in f"{c[1]}" for p in pats)]
    if args.limit:
        cards = cards[:args.limit]
    log(f"=== judge105-all start: model={args.model} cards={len(cards)} "
        f"workers={args.workers} force={args.force} skip_existing={args.skip_existing} ===")
    results = {"ok": 0, "skip": 0, "fail": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(judge_one, c, args.model, args.force, args.skip_existing)
                for c in cards]
        for fut in as_completed(futs):
            st, dom, card, _ = fut.result()
            results[st] += 1
    log(f"=== judge105 done: ok={results['ok']} skip={results['skip']} "
        f"fail={results['fail']} ===")


if __name__ == "__main__":
    main()
