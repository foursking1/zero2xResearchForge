#!/usr/bin/env python3
"""SciSolveBench eval105 — v7 judge: B redefined as truth-agreement (verifiability).

v7 CHANGE vs v5 (NO deliverable change — agents are NOT re-run):
  The existing judge already fed PAPER_ANCHOR.md (paper ground truth) into context,
  but B was scored on "internal self-consistency" (tier 2 => B=40) without ever
  checking the agent's numbers against the paper's stated values. v7 fixes this:

  - B (0-40) is now "与论文真值的一致性 / 可验证性". The judge MUST read
    PAPER_ANCHOR.md (already in context) and the agent's machine-readable numbers
    (metrics.json / claim.md / evidence_table.csv), then perform an EXPLICIT
    numeric cross-check for each key claim and cite the anchor values.
      * matched   : agent numbers demonstrably match paper truth within tolerance
                    (judge cites specific anchor values)            -> B 35-40
      * diverged  : numbers present but deviate from paper truth (even if direction
                    correct / magnitude off)                        -> B 10-25
      * unverified: no machine-readable numbers / only narrative / numbers cannot be
                    tied to any paper-stated value (unverifiable)   -> B 0-15
      * empty     : tier 0 (no materialized result evidence)        -> B 0-10
  - A1 (0-12) now requires machine-readable result evidence. Prose-only submissions
    are capped at A1 <= 6 (deliverable exists but is not verifiable).
  - New output field `truth_check` (matched|diverged|unverified|empty) is code-enforced
    to cap B: empty<=10, unverified<=15, diverged<=25, matched<=40 (and tier-gated).
  - A2 high (33) only when the supported conclusion is backed by numbers matching
    paper truth; if conclusion=supported but numbers diverge, A2 must be low.

Outputs EVAL_REPORT_v7.md + eval105_all_scores_v7.csv (does NOT touch v5 files).
"""
from __future__ import annotations
import argparse, csv, json, os, re, ssl, sys, time, threading, traceback, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from card_material import material_path

# ---------------------------------------------------------------- config
API_URL = os.environ.get("JUDGE_API_URL", "https://api.agtcloud.cn/v1/chat/completions")
API_KEY = os.environ.get("JUDGE_API_KEY", "")
BASE = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TASKS = os.path.join(BASE, "tasks")
DEFAULT_MODEL = os.environ.get("JUDGE_MODEL", "qwen3.7-max")
WORKERS = int(os.environ.get("JUDGE_WORKERS", "5"))
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
LOG_PATH = os.path.join(BASE, "results", "judge_eval105_v7.log")
CSV_PATH = os.path.join(BASE, "results", "eval105_all_scores_v7.csv")
REPORT_LEAF = "EVAL_REPORT_v7.md"
csv_lock = threading.Lock()
log_lock = threading.Lock()


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with log_lock:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        print(line, flush=True)
    except OSError:
        # Windows 后台进程退出阶段 stdout 句柄可能失效，忽略即可（日志已落盘）
        pass


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
def scan_evidence(asol: str, card_dir: str = "") -> dict:
    d = {"n_files": 0, "has_metrics": False, "has_evidence_csv": False,
         "has_claim": False, "has_anchor": False, "result_files": 0,
         "has_code": False, "evidence_samples": []}
    if not os.path.isdir(asol):
        return d
    if card_dir and material_path(card_dir, "PAPER_ANCHOR.md").exists():
        d["has_anchor"] = True
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
            if low == "claim.md":
                if sz > 0:
                    d["has_claim"] = True
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
        return ("【磁盘证据扫描】submission 为空或不存在 —— 无任何提交物。"
                "证据等级=0(空壳)；无机器可读结果→不可验证→B≤10。")
    parts = []
    parts.append(f"文件总数={d['n_files']}")
    parts.append(f"metrics.json={'有' if d['has_metrics'] else '缺失'}")
    parts.append(f"claim.md(实测vs真值对照)={'有' if d['has_claim'] else '缺失'}")
    parts.append(f"evidence_table/evidence*.csv={'有' if d['has_evidence_csv'] else '缺失'}")
    parts.append(f"PAPER_ANCHOR.md(论文真值,已在上下文)={'有' if d['has_anchor'] else '缺失'}")
    parts.append(f"结果CSV/JSON文件数(≤2层)={d['result_files']}")
    parts.append(f"可运行代码(.py)={'有' if d['has_code'] else '无'}")
    if d["has_claim"]:
        parts.append(">>> 有 claim.md：agent 已自比对真值，judge 必须复核其比对并引用锚点值")
    elif d["has_metrics"] or d["has_evidence_csv"]:
        parts.append(">>> 有机器可读数字但【无 claim.md 真值对照】：agent 报数但未对照论文真值"
                     "→必须靠 PAPER_ANCHOR 自行核对，无法核对者判 unverified")
    else:
        parts.append(">>> 仅有代码+散文、无机器可读结果文件→空壳/不可验证")
    parts.append(f">>> 证据等级={tier}")
    if d["evidence_samples"]:
        parts.append("证据样本: " + ", ".join(d["evidence_samples"][:4]))
    return "【磁盘证据扫描】" + "；".join(parts)


# ---------------------------------------------------------------- judge call
SYSTEM = (
    "你是一位严谨的科研任务评测裁判（SciSolveBench scientific scoring judge, eval105 v7 版）。"
    "本版核心改动：B 维度从『证据内部自洽』改为『与论文真值的一致性 / 可验证性』。"
    "你必须拿 agent 报出的数字去和【PAPER_ANCHOR.md 中的论文真值】逐项比对，"
    "绝不能仅因『提交物内部自洽』就给高分。\n\n"
    "【可用证据】上下文已包含：TASK.md(任务)、SCORE_RUBRIC.md(评分细则)、"
    "PAPER_ANCHOR.md(论文报道的真值/锚点，含容差带)、CALIBRATION.md，"
    "以及 submission 的全部文本证据(metrics.json / claim.md / evidence_table.csv / report.md 等)。\n\n"
    "1. 只依据提交物中的真实证据打分；严禁把论文/锚值本身当作 agent 已复现的证据。\n\n"
    "2. A 维度（核心结果达成度，0-60）三个子项：\n"
    "   【A1 交付实质 0-12】是否产出 TASK.md 要求的『核心交付物』，且为【机器可读】的结果。\n"
    "     · 12：核心交付物完整产出，且有机器可读结果文件(metrics.json/claim.md/evidence CSV)\n"
    "     · 8：交付物完整但仅有散文报告、无机器可读结果文件\n"
    "     · 6：有机器可读结果但明显缺口(覆盖不全/缺必需输出)\n"
    "     · 4：尝试了但核心产物缺失或非功能；0：无实质产物(仅代码/散文且无结果)\n"
    "   【A2 科学结论保真 0-33】结果是否支持论文核心 claim。\n"
    "     · 量化任务：按『与 PAPER_ANCHOR 真值的匹配度』分级——在锚点容差带内逐项吻合→33；"
    "落在合理容差但个别指标偏离10-20%→26；方向对/定性匹配但弱→18；部分不支持→10；不支持/矛盾→5；无关→0。\n"
    "     · 关键：结论=supported 时，A2 必须≥30 且你能引用具体锚点值证明吻合；"
    "若结论=supported 但 agent 数字与锚点偏离，A2 必须≤10（不得借方向对就给满）。\n"
    "     · 定性任务按复现模式是否与论文结论一致判分。\n"
    "   【A3 方法严谨与可复现 0-15】证据 sound 且可复算→15；轻微顾虑→10；明显顾虑(泄漏/评估不当)→5；不 sound→0。\n"
    "   【证据绑定】A1/A2 中涉及实测数的部分，仅当该数有落盘 metrics.json/claim.md/evidence 支撑、"
    "且与 PAPER_ANCHOR 真值一致时方可授高分；纯散文无 evidence 文件支撑者对应子项封顶下限。\n\n"
    "3. B 维度（与论文真值一致性 / 可验证性，0-40）——本版重点，必须做真值比对：\n"
    "   步骤：①从 agent 的 metrics.json/claim.md/evidence 抽取关键实测数值(逐字引用)；"
    "②从 PAPER_ANCHOR.md 抽取对应论文真值(逐字引用)；③判断每个关键指标是否在容差内吻合。\n"
    "   按【truth_check】给分：\n"
    "     · matched(已核对且吻合)：B=35~40（须引用≥2个具体锚点值证明吻合）\n"
    "     · diverged(有数字但与真值偏离，方向对也算)：B=10~25（按偏离程度，量级错误/超容差重扣）\n"
    "     · unverified(无机器可读数字 / 仅散文 / 数字无法对应任何论文真值)：B=0~15（不可验证=不可信）\n"
    "     · empty(空壳 tier0 无真产物)：B=0~10\n"
    "   严禁因『提交物内部自洽』『有校验脚本』就默认给 40；自洽≠真值正确。\n"
    "   抄论文数字当实测 / 测试段泄漏 → B≤8。\n\n"
    "4. 本版取消 C 维度。\n\n"
    "5. 【结论级硬上限（代码强制）】conclusion 决定 A2/B 天花板：\n"
    "   supported：A2≤33,B≤40；partially_supported：A2≤15,B≤28,总分≤70；"
    "inconclusive：A2≤8,B≤22,总分≤57；contradicted：A2≤5,B≤20,总分≤45。\n"
    "   supported 但 truth_check≠matched 时，B 实际≤25（详见代码钳制）。\n\n"
    "6. 输出严格 JSON（不要 markdown 包裹）。必填字段见要求。\n"
    "7. 评分保守、有据；每个维度给中文理由，B_notes 必须包含『agent数 X vs 锚点 Y → 吻合/偏离』的逐条比对。"
)

USER_TMPL = """# 任务卡规范与评分标准（含 PAPER_ANCHOR 论文真值）
{spec}

# Agent 提交物（submission 文本证据）
{artifacts}

# 磁盘证据扫描（脚本实测，裁判须据此 + PAPER_ANCHOR 做真值比对）
{evidence}

# 真值比对铁则（v7 核心）
你必须执行：①列出 agent 报出的关键实测数值（逐字引用，注明来自哪个文件）；
②列出 PAPER_ANCHOR.md 中对应的论文真值（逐字引用）；
③对每个关键指标判断：在容差带内吻合(matched) / 偏离(diverged) / 无法核对(unverified)。
禁止：仅因"提交物内部自洽""有 SHA/校验脚本"就给 B=40。自洽不代表真值正确。

# 评分要求（仅两维，受证据等级 + truth_check 硬约束）
- A（0-60）= A1(0-12)+A2(0-33)+A3(0-15)：
   · A1：核心交付物+机器可读结果→12；完整但仅散文→8；有结果但缺口→6；缺失→≤4。
   · A2：与 PAPER_ANCHOR 真值匹配度。supported 必须 A2≥30 且能引锚点证明；supported 但数字偏离→A2≤10。
   · A3：sound 可复算→15；轻微→10；明显顾虑→5；不 sound→0。
- B（0-40）= 与论文真值一致性/可验证性，按 truth_check：
   matched(引用≥2锚点证明吻合)→35~40；diverged(有数但偏真值)→10~25；
   unverified(无机器可读数/仅散文/无法对应真值)→0~15；empty(空壳)→0~10。
- 结论级硬上限（代码强制）：partially≤70；inconclusive≤57；contradicted≤45；supported 不设总上限但 B 受 truth_check 钳制。

JSON 字段（务必输出，数值整数或一位小数）：
{{
  "A1": <0-12>, "A2": <0-33>, "A3": <0-15>,
  "B": <0-40>,
  "total": <A1+A2+A3+B>,
  "conclusion": "<supported|partially_supported|contradicted|inconclusive>",
  "truth_check": "<matched|diverged|unverified|empty>",
  "A_notes": "<中文，分别说明 A1/A2/A3 给分理由>",
  "B_notes": "<中文，必含『agent数 X vs 锚点 Y → 吻合/偏离』逐条比对>",
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
    ev = scan_evidence(asol, card_dir)
    user = USER_TMPL.format(spec=spec, artifacts=artifacts, evidence=evidence_line(ev))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 3000,
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
            out = json.loads(raw)
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
    d = json.loads(s)
    a1 = min(12.0, max(0.0, round(float(d.get("A1", 0)), 1)))
    a2 = min(33.0, max(0.0, round(float(d.get("A2", 0)), 1)))
    a3 = min(15.0, max(0.0, round(float(d.get("A3", 0)), 1)))
    d["A1"], d["A2"], d["A3"] = a1, a2, a3
    d["A"] = round(a1 + a2 + a3, 1)
    d["B"] = round(float(d.get("B", 0)), 1)
    d["B"] = min(40, max(0, d["B"]))

    # ---- conclusion ceilings ----
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

    # ---- v7 truth_check enforcement (verifiability gate) ----
    tier = evidence_tier(ev)
    tc = (d.get("truth_check") or "").lower()
    if tc == "empty" or tier == 0:
        d["B"] = min(d["B"], 10.0)
        d["truth_check"] = "empty"
    elif tc == "unverified":
        d["B"] = min(d["B"], 15.0)
    elif tc == "diverged":
        d["B"] = min(d["B"], 25.0)
    elif tc == "matched":
        d["B"] = min(d["B"], 40.0)
    else:
        # judge didn't report truth_check -> infer from evidence
        if tier == 0:
            d["B"] = min(d["B"], 10.0); d["truth_check"] = "empty"
        elif not (ev.get("has_claim") or ev.get("has_metrics") or ev.get("has_evidence_csv")):
            d["B"] = min(d["B"], 15.0); d["truth_check"] = "unverified"
        else:
            # has numbers but judge silent -> treat as unverified-by-default (conservative)
            d["B"] = min(d["B"], 25.0); d["truth_check"] = "diverged"
    # supported but not matched -> extra B cap (consistency with A2 rule)
    if concl == "supported" and d["truth_check"] != "matched":
        d["B"] = min(d["B"], 25.0)

    # ---- HARD evidence-gated ceilings (B also capped by evidence tier) ----
    amax, bmax = {0: (10, 10), 1: (35, 29), 2: (60, 40)}[tier]
    d["A"] = min(d["A"], amax)
    d["B"] = min(d["B"], bmax)
    d["total"] = round(d["A"] + d["B"], 1)
    if concl == "contradicted":
        d["total"] = min(d["total"], 45.0)
    for k in ("conclusion", "truth_check", "A_notes", "B_notes", "evidence_notes",
              "strengths", "weaknesses"):
        d.setdefault(k, "")
    return d


def write_report(card_dir: str, asol: str, d: dict, model: str, exec_agent: str):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = []
    lines.append(f"# EVAL REPORT v7: {os.path.basename(card_dir)}")
    lines.append("")
    lines.append(f"- 执行 agent: {exec_agent}")
    lines.append(f"- 评测裁判: SciSolveBench LLM 裁判 v7（{model}）")
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
    lines.append(f"| B 真值一致性/可验证性 | {d['B']} | 40 | truth_check={d.get('truth_check','')} | {d.get('B_notes','')} |")
    lines.append("")
    lines.append("## A 核心结果达成度（%s/60 = A1 %s + A2 %s + A3 %s）" % (
        d["A"], d.get("A1", 0), d.get("A2", 0), d.get("A3", 0)))
    lines.append("")
    lines.append(d.get("A_notes", ""))
    lines.append("")
    lines.append("## B 真值一致性/可验证性（%s/40）[truth_check=%s]" % (d["B"], d.get("truth_check", "")))
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
    lines.append(f"- **可验证性**: `{d.get('truth_check','')}`")
    lines.append(f"- 亮点: {d.get('strengths','')}")
    lines.append(f"- 不足: {d.get('weaknesses','')}")
    txt = "\n".join(lines)
    path = report_path(card_dir, "v7")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(txt)


def detect_exec_agent(card_dir: str) -> str:
    for version in ("v7", "v5", "v2", "v1"):
        p = report_path(card_dir, version)
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="replace"):
                if "执行 agent" in line:
                    return line.split(":", 1)[-1].strip()
    return "opencode (deepseek-v4-flash via agtcloud)"


def append_csv(domain: str, card: str, source: str, level: str, d: dict, model: str, tier: int):
    with csv_lock:
        new = not os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["source", "domain", "card", "judge_model", "tier",
                            "A1", "A2", "A3", "A", "B", "total", "conclusion",
                            "truth_check", "level", "timestamp"])
            w.writerow([source, domain, card, model, tier,
                        d.get("A1", 0), d.get("A2", 0), d.get("A3", 0),
                        d["A"], d["B"], d["total"], d["conclusion"],
                        d.get("truth_check", ""), level,
                        datetime.now().isoformat(timespec="seconds")])


# ---------------------------------------------------------------- unified roots
# Task cards hold definitions; historical submissions live in baselines/.
TASKS = os.path.join(BASE, "tasks")
BASELINES = os.path.join(BASE, "baselines")
EVALUATIONS = os.path.join(BASE, "evaluations")


def report_path(card_dir: str, version: str) -> str:
    """Return the centralized report location for one task card."""
    relative = os.path.relpath(card_dir, TASKS)
    return os.path.join(EVALUATIONS, version, relative, "report.md")


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


def _multistep_signal(txt: str) -> bool:
    if len(re.findall(r"问题\s*\d+\s*[（(]", txt)) >= 2:
        return True
    if len(re.findall(r"\n\s*问题\s*\d+\b", txt)) >= 2:
        return True
    kw = ["多数据集", "融合", "pipeline", "多阶段", "多模型", "多任务",
          "多个数据集", "多组件", "交叉验证", "训练与评估", "训练.*评估.*对比"]
    return any(re.search(k, txt) for k in kw)


def level_for(source: str, domain: str, card: str, cp: str) -> str:
    # 仅区分 L1（论文复现）/L2（多步骤+原端到端）；legacy 已合并，source 恒为 main
    lab = L1L2.get((domain, card))
    if lab == "L1":
        return "L1"
    return "L2"


def completed_cards() -> list:
    res = []
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


def judge_one(item, model, force):
    domain, card, cp, source = item
    asol = os.path.join(BASELINES, domain, card)
    try:
        ev = scan_evidence(asol, cp)
        tier = evidence_tier(ev)
        d = call_judge(cp, asol, model)
        lvl = level_for(source, domain, card, cp)
        write_report(cp, asol, d, model, detect_exec_agent(cp))
        append_csv(domain, card, source, lvl, d, model, tier)
        log(f"DONE {source}/{domain}/{card}: tier={tier} truth={d.get('truth_check')} "
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
    ap.add_argument("--source", default="", choices=["", "main", "legacy"])
    ap.add_argument("--only", nargs="*", default=[],
                    help="domain/card substrings to restrict to")
    args = ap.parse_args()

    if not API_KEY:
        raise SystemExit("JUDGE_API_KEY is required for LLM judging.")

    cards = completed_cards()

    # ---- skip-existing / force handling ----
    if args.force and os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)
        log("force: removed existing CSV for clean rewrite")
    existing = set()
    if os.path.exists(CSV_PATH) and not args.force:
        try:
            with open(CSV_PATH, encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    existing.add((r["source"], r["card"]))
        except Exception:
            pass
    if not args.force:
        before = len(cards)
        cards = [c for c in cards if (c[3], c[1]) not in existing]
        log(f"skip-existing: {before} -> {len(cards)} (skipped {before - len(cards)})")

    if args.source:
        cards = [c for c in cards if c[3] == args.source]
    if args.only:
        pats = args.only
        cards = [c for c in cards if any(p in f"{c[1]}" for p in pats)]
    if args.limit:
        cards = cards[:args.limit]
    log(f"=== judge105-v7 start: model={args.model} cards={len(cards)} "
        f"workers={args.workers} force={args.force} ===")
    results = {"ok": 0, "fail": 0}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(judge_one, c, args.model, args.force) for c in cards]
        for fut in as_completed(futs):
            st, dom, card, _ = fut.result()
            results[st] += 1
    log(f"=== judge105-v7 done: ok={results['ok']} fail={results['fail']} ===")


if __name__ == "__main__":
    main()
