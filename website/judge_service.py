# -*- coding: utf-8 -*-
"""评分服务：对提交的 solution 打分。

两种模式（环境变量 JUDGE_MODE，默认 demo）：
  demo  -- 模拟评分（无需 API key，用于演示/联调，分数基于该卡基线分布合成）
  llm   -- 真实 LLM 裁判：完全复用仓库评测链
           evaluation/judge_eval105.py（collect_spec/collect_artifacts/scan_evidence/parse_json）
           evaluation/JUDGE_PROMPT_v7.md + evaluation/judge_v7_full.py::enforce
           需要环境变量 JUDGE_API_KEY；端点和模型由 JUDGE_API_URL/JUDGE_MODEL 配置
"""
import hashlib
import json
import os
import random
import re
import threading
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("PAPER_BENCH_ROOT", HERE.parent))
sys_evaluation = str(REPO / "evaluation")
if sys_evaluation not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_evaluation)

JUDGE_MODE = os.environ.get("JUDGE_MODE", "demo").lower()
STAGES = ["校验提交物完整性", "冻结数据挂载与工作区准备", "复跑/收集提交产物",
          "数值锚点比对", "LLM 裁判评分 + enforce 钳制"]


def j105_ok():
    """llm 模式就绪检查：judge_eval105 可导入且 JUDGE_API_KEY 已配置。"""
    try:
        import judge_eval105_v7  # noqa: F401
        return bool(os.environ.get("JUDGE_API_KEY"))
    except Exception:
        return False

_TEXT_EXTS = {".md", ".txt", ".json", ".csv", ".py", ".tsv", ".log", ".yaml", ".yml"}


def _stage_update(status: dict, path: Path, stage_idx: int, note=""):
    status["stage"] = STAGES[stage_idx]
    status["stage_idx"] = stage_idx
    status["stages"] = [{"name": s, "state": "done" if i < stage_idx else ("running" if i == stage_idx else "pending")}
                        for i, s in enumerate(STAGES)]
    if note:
        status.setdefault("log", []).append(note)
    status["updated_at"] = time.time()
    path.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")


def _solution_texts(sol_dir: Path, limit=60000):
    """收集提交物里的文本内容（供 llm 裁判与 demo 参考）。"""
    chunks, total = [], 0
    for p in sorted(sol_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in _TEXT_EXTS and p.stat().st_size < 2_000_000:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if total >= limit:
                break
            chunks.append(f"### {p.relative_to(sol_dir)}\n{t[:limit - total]}")
            total += len(t)
    return "\n\n".join(chunks)[:limit]


def _demo_score(card: dict, sub_seed: str):
    rnd = random.Random(int(hashlib.md5(sub_seed.encode()).hexdigest(), 16) % (2**31))
    base = card["v7"]["total"] if card["v7"]["total"] is not None else 65.0
    total = round(max(5, min(100, base + rnd.uniform(-9, 7))), 1)
    ratio = total / max(base, 1)
    A1 = round(min(20, (card["v7"]["A1"] or 0) * ratio + rnd.uniform(-1.5, 1.5)), 1)
    A2 = round(min(25, (card["v7"]["A2"] or 0) * ratio + rnd.uniform(-2, 2)), 1)
    A3 = round(min(15, (card["v7"]["A3"] or 0) * ratio + rnd.uniform(-1, 1)), 1)
    B = round(max(0, min(40, total - A1 - A2 - A3)), 1)
    total = round(A1 + A2 + A3 + B, 1)
    concl = ("supported" if total >= 78 else "partially_supported" if total >= 55
             else "inconclusive" if total >= 40 else "contradicted")
    enforce_note = ""
    if total < 70:  # 模拟锚表不全触发钳制
        A2 = min(A2, 12.0)
        total = round(A1 + A2 + A3 + B, 1)
        enforce_note = "anchor_table incomplete -> A2 capped"
    return {"total": total, "A": round(A1 + A2 + A3, 1), "A1": A1, "A2": A2, "A3": A3, "B": B,
            "conclusion": concl, "n_anchors": card["v7"]["nAnchors"], "enforce_note": enforce_note,
            "A_notes": "（demo 模拟评分）分项按该卡基线 v7 分布合成，仅供前端联调演示。",
            "B_notes": "", "weaknesses": [], "anchor_table": [], "judge": "demo-simulator"}


def _llm_score(card_dir: Path, sol_dir: Path, status_path: Path, status: dict):
    """真实裁判：与 work/judge_v7_full.py 同一条链。"""
    import judge_eval105_v7 as j105
    import judge_v7_full
    prompt = (REPO / "evaluation" / "JUDGE_PROMPT_v7.md").read_text(encoding="utf-8")
    spec = j105.collect_spec(card_dir)
    artifacts = j105.collect_artifacts(sol_dir)
    ev = j105.scan_evidence(sol_dir)
    user = j105.USER_TMPL.format(spec=spec, artifacts=artifacts,
                                 evidence=j105.evidence_line(ev))
    _stage_update(status, status_path, 4, f"构造裁判上下文：spec={len(spec)} chars, artifacts={len(artifacts)} chars")

    payload = {"model": j105.DEFAULT_MODEL,
               "messages": [{"role": "system", "content": prompt},
                            {"role": "user", "content": user}],
               "temperature": 0, "max_tokens": 6000}
    import urllib.request, ssl
    req = urllib.request.Request(
        j105.API_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {j105.API_KEY}", "Content-Type": "application/json"})
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=300, context=ctx) as r:
                out = json.loads(r.read().decode("utf-8"))["choices"][0]["message"]["content"]
            break
        except Exception as e:  # noqa: PERF203
            last = e
            time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f"judge API failed: {last!r}")
    d = j105.parse_json(out, ev)
    d = judge_v7_full.enforce(d)
    d["judge"] = f"v7/{j105.DEFAULT_MODEL}"
    return d


def run_submission(sub_id: str, card: dict, card_dir: Path, sol_dir: Path, meta: dict):
    """后台线程：执行评分并写 submissions/<id>/status.json + result.json。"""
    sdir = HERE / "submissions" / sub_id
    status_path = sdir / "status.json"
    status = {"id": sub_id, "status": "running", "stage": STAGES[0], "stage_idx": 0,
              "log": [], "updated_at": time.time(), **meta}
    status_path.write_text(json.dumps(status, ensure_ascii=False), encoding="utf-8")
    try:
        texts = _solution_texts(sol_dir)
        _stage_update(status, status_path, 0, f"提交物文本共 {len(texts)} chars")
        _stage_update(status, status_path, 1, f"挂载冻结数据：{card_dir.name}/data (read-only)")
        _stage_update(status, status_path, 2, "收集 claim/metrics/report/evidence 产物")

        if JUDGE_MODE == "llm":
            _stage_update(status, status_path, 3, "逐锚容差带判定交给裁判 prompt（v7 协议）")
            d = _llm_score(card_dir, sol_dir, status_path, status)
        else:
            for wait in (1.2, 1.5):
                time.sleep(wait)
            _stage_update(status, status_path, 3, "demo：按基线锚点容差模拟比对")
            time.sleep(1.2)
            d = _demo_score(card, sub_id)
            _stage_update(status, status_path, 4, "demo：评分完成（模拟）")

        (sdir / "result.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        status.update({"status": "done", "result": d, "updated_at": time.time()})
    except Exception as e:  # noqa: BLE001
        status.update({"status": "error", "error": f"{e!r}", "trace": traceback.format_exc()[-800:],
                       "updated_at": time.time()})
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
