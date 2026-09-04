#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校准脚本：用 opencode 免费模型 (hy3-free via zen 网关) 评测一批卡，
与 v7 LLM 裁判分数并排对比，判断免费模型是否系统性更宽松。

- 不经过故障的 opencode 客户端，直接 POST zen OpenAI 兼容 API (curl 子进程，免 key)。
- 不执行提交代码（与 v7 一致：仅基于文件做真值一致性判断），保证对比公平。
- 输出 calibrate_results.csv，并打印均值差/相关性/宽松率。
"""
import csv, json, os, sys, time, subprocess, re
from card_material import material_path

ROOT = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS = os.path.join(ROOT, "results")
CSV_V7 = os.path.join(RESULTS, "v7_full_scores.csv")
ZEN = "https://opencode.ai/zen/v1/chat/completions"
MODEL = "hy3-free"
MAX_TOKENS = 8000
TRUNC = 12000          # 单文件截断字符数
MAX_FILES = 8          # 最多纳入的提交物文件数
SLEEP_BETWEEN = 3.0    # 卡片间退避，避免 IP 限额
MAX_RETRY = 4

def v7_scores():
    d = {}
    for r in csv.DictReader(open(CSV_V7, encoding="utf-8-sig")):
        d[r["card"]] = float(r["total"]) if r["submission_class"] != "not_submitted" else None
    return d

def read(path, trunc=TRUNC):
    try:
        s = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""
    return s[:trunc]

def build_context(card):
    base = f"{ROOT}/tasks"
    # 定位卡目录（legacy 已合并进 tasks/<domain>/<card>，统一按 2 层结构）
    d = None
    for cand in [f"{base}/{card[:card.index('_')] if '_' in card else card}",
                 f"{base}/astro/{card}", f"{base}/biomed/{card}", f"{base}/cs/{card}",
                 f"{base}/earth/{card}", f"{base}/materials/{card}"]:
        if os.path.isdir(cand):
            d = cand; break
    if d is None:
        return None, None
    parts = []
    for fn in ["TASK.md", "PAPER_ANCHOR.md", "CALIBRATION.md", "SCORE_RUBRIC.md"]:
        p = material_path(d, fn)
        if os.path.isfile(p):
            parts.append(f"# FILE: {fn}\n{read(p)}")
    domain = os.path.basename(os.path.dirname(d))
    sol = os.path.join(ROOT, "baselines", domain, os.path.basename(d))
    if os.path.isdir(sol):
        files = []
        for root, _, fs in os.walk(sol):
            for f in fs:
                if f.lower().endswith((".md", ".txt", ".json", ".csv", ".py")):
                    files.append(os.path.join(root, f))
        files.sort(key=lambda x: -os.path.getsize(x))
        inc = 0
        for f in files:
            if inc >= MAX_FILES:
                parts.append(f"[... 其余提交物文件未纳入，共 {len(files)} 个 ...]")
                break
            parts.append(f"# FILE: baseline/{os.path.relpath(f, sol)}\n{read(f)}")
            inc += 1
    return d, "\n\n".join(parts)

PROMPT = """你是严格的科研复现评测裁判。下面给出一张 benchmark 卡的任务规格(TASK)、论文真值锚表(PAPER_ANCHOR)、评分标准(SCORE_RUBRIC)以及 agent 的提交物。

评分维度与满分：
- A1 交付完整(0-12)：是否提供机器可读的提交物(report/metrics/代码/证据表)，缺关键交付则低分。
- A2 科学保真(0-33)：方法是否贴合任务规定，有无擅自替换方法/数据集。
- A3 方法严谨(0-15)：实验设计/消融/误差处理是否严谨。
- B 证据真实性(0-40)：agent 报告的数字与 PAPER_ANCHOR 真值是否一致(带合理容差)。明显偏离真值则大幅扣分；结论与真值矛盾则 B 应很低。

必须基于锚表真值逐项核对 agent 报告的具体数字，而不是只看叙述是否自信。控制推理篇幅，聚焦可验证数字。

严格输出一个 JSON（不要多余文字）：
{"A1":<int 0-12>,"A2":<int 0-33>,"A3":<int 0-15>,"B":<int 0-40>,"total":<A1+A2+A3+B>,"conclusion":"supported|partially_supported|contradicted|unverified","reason":"<中文简短说明，指出具体数字核对结果>"}
"""

def call_zen(context):
    payload = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": context},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(MAX_RETRY):
        try:
            out = subprocess.run(
                ["curl", "-sS", "-m", "180", "-X", "POST", ZEN,
                 "-H", "Content-Type: application/json",
                 "--data-binary", "@-"],
                input=data, capture_output=True, timeout=200)
            txt = out.stdout.decode("utf-8", "ignore")
            if not txt.strip():
                time.sleep(5 * (attempt + 1)); continue
            js = json.loads(txt)
            content = js.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content.strip():
                # 推理模型可能在 length 截断，重试
                if js.get("choices", [{}])[0].get("finish_reason") == "length":
                    time.sleep(2); continue
                time.sleep(3); continue
            return content
        except Exception as e:
            sys.stderr.write(f"[retry {attempt}] {e}\n")
            time.sleep(5 * (attempt + 1))
    return ""

def parse_score(content):
    m = re.search(r"\{[^{}]*\"total\"[^{}]*\}", content, re.S)
    if not m:
        m = re.search(r"\{.*\}", content, re.S)
    if not m: return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def main():
    v7 = v7_scores()
    # 分层抽样卡（与之前分析一致）
    sample = [
        "2303.08092_solar_energetic_particle_ensemble","2111.10009_exominer_tess_vetting",
        "2607.16250_multiomics_breast_cancer_er","2502.20784_arseg_next_scale_seg",
        "2606.12651_physics_aware_gnn_ood","2103.12057_tsf_experimental_review",
        "2604.08131_gnn_misinfo","2502.05832_compression_ood",
        "2110.08733_loveda","1703.00121_resisc45","1709.00029_eurosat",
        "2604.04858v1","2604.04895v1","2604.04673v1",
        "2401.11052_llm_materials_mining","2001.10591_stability_ml_predictions",
    ]
    out_rows = []
    for card in sample:
        d, ctx = build_context(card)
        if ctx is None:
            sys.stderr.write(f"[skip] {card} 目录未找到\n"); continue
        free = call_zen(ctx)
        sc = parse_score(free) if free else None
        v7s = v7.get(card)
        free_total = sc.get("total") if sc else None
        concl = sc.get("conclusion") if sc else None
        out_rows.append({
            "card": card, "v7_total": v7s,
            "free_total": free_total, "free_conclusion": concl,
            "free_A1": sc.get("A1") if sc else "", "free_A2": sc.get("A2") if sc else "",
            "free_A3": sc.get("A3") if sc else "", "free_B": sc.get("B") if sc else "",
            "free_reason": (sc.get("reason","")[:300] if sc else free[:200]),
        })
        sys.stderr.write(f"[done] {card}: v7={v7s}  free={free_total} ({concl})\n")
        time.sleep(SLEEP_BETWEEN)
    # 写 CSV
    with open(os.path.join(RESULTS, "calibrate_results.csv"), "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    # 统计
    pairs = [(r["v7_total"], r["free_total"]) for r in out_rows if r["free_total"] is not None]
    if pairs:
        import statistics as st
        v = [p[0] for p in pairs]; f = [p[1] for p in pairs]
        diffs = [p[1]-p[0] for p in pairs]
        print(f"\n=== 校准对照 (n={len(pairs)}) ===")
        print(f"v7 均分:    {st.mean(v):.1f}")
        print(f"free 均分:  {st.mean(f):.1f}")
        print(f"平均偏差(free-v7): {st.mean(diffs):+.1f}  (中位 {st.median(diffs):+.1f})")
        looser = sum(1 for d in diffs if d > 5); stricter = sum(1 for d in diffs if d < -5)
        print(f"free 更宽松(>+5): {looser} 张 | 更严格(<-5): {stricter} 张 | 基本一致: {len(diffs)-looser-stricter} 张")
        # 相关系数
        if len(set(v))>1 and len(set(f))>1:
            mv=st.mean(v); mf=st.mean(f)
            num=sum((a-mv)*(b-mf) for a,b in pairs)
            den=(sum((a-mv)**2 for a in v)*sum((b-mf)**2 for b in f))**0.5
            print(f"Pearson r:  {num/den:.2f}" if den else "Pearson r: n/a")
    print("\n明细:")
    for r in out_rows:
        print(f"  {r['card'][:42]:42s} v7={r['v7_total']}  free={r['free_total']}  {r['free_conclusion']}")

if __name__ == "__main__":
    main()
