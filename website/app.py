#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zero2x ResearchForge · Benchmark Arena —— 可部署评测网站（Flask）。

本地运行:
    pip install -r requirements.txt
    python build_data.py          # 从仓库聚合数据（需要 PAPER_BENCH_ROOT 指向仓库根）
    python app.py                 # http://127.0.0.1:5000

环境变量:
    PAPER_BENCH_ROOT  仓库根目录（默认: 本文件的上一级）
    JUDGE_MODE        demo | llm   （默认 demo；llm 需 JUDGE_API_KEY）
    JUDGE_API_KEY     裁判 API key（llm 模式）
    JUDGE_API_URL     OpenAI-compatible /chat/completions endpoint（可选）
    JUDGE_MODEL       裁判模型名（可选）
    PORT              监听端口（默认 5000）
"""
import json
import os
import re
import threading
import time
import uuid
import zipfile
from pathlib import Path

from flask import Flask, jsonify, request, render_template, abort

import judge_service

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("PAPER_BENCH_ROOT", HERE.parent))
SUB_DIR = HERE / "submissions"
SUB_DIR.mkdir(exist_ok=True)
DATA_FILE = HERE / "data" / "eval_data.json"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB zip 上限

if not DATA_FILE.exists():
    raise SystemExit("data/eval_data.json 不存在 —— 请先运行: python build_data.py")

_DATA = json.loads(DATA_FILE.read_text(encoding="utf-8"))
_CARDS = {c["id"]: c for c in _DATA["cards"]}
_SN_FIELDS = ("card_id", "agent_name", "agent_version", "description", "mode")


def _sub_status(sub_id):
    p = SUB_DIR / sub_id / "status.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# ---------- 页面 ----------
@app.get("/")
def index():
    html = (HERE / "templates" / "index.html").read_text(encoding="utf-8")
    payload = json.dumps(_DATA, ensure_ascii=False).replace("</", "<\\/")
    return (html.replace("__DATA_JSON__", payload)
                .replace("__JUDGE_MODE__", judge_service.JUDGE_MODE))


# ---------- 只读 API ----------
@app.get("/api/health")
def health():
    return jsonify(ok=True, cards=len(_CARDS), judge_mode=judge_service.JUDGE_MODE,
                  repo=str(REPO))


@app.get("/api/data")
def data_api():
    return jsonify(_DATA)


@app.get("/api/cards/<card_id>")
def card_detail(card_id):
    c = _CARDS.get(card_id)
    if not c:
        abort(404)
    dom, cid = c["domain"], c["id"]
    task_md = ""
    p = REPO / "tasks" / dom / cid / "TASK.md"
    if p.exists():
        task_md = p.read_text(encoding="utf-8", errors="ignore")
    return jsonify(card=c, task_md=task_md)


@app.get("/api/submissions")
def list_submissions():
    rows = []
    if SUB_DIR.exists():
        for d in sorted(SUB_DIR.iterdir(), key=lambda x: x.name, reverse=True)[:50]:
            st = _sub_status(d.name)
            if st:
                rows.append({k: st.get(k) for k in
                             ("id", "status", "stage", "card_id", "agent_name",
                              "agent_version", "mode", "updated_at")})
    return jsonify(rows)


@app.get("/api/submissions/<sub_id>")
def get_submission(sub_id):
    if not re.fullmatch(r"[0-9a-f-]{36}", sub_id or ""):
        abort(400)
    st = _sub_status(sub_id)
    if not st:
        abort(404)
    return jsonify(st)


# ---------- 提交 ----------
@app.post("/api/submit")
def submit():
    card_id = request.form.get("card_id", "").strip()
    if card_id not in _CARDS:
        return jsonify(error=f"未知任务卡: {card_id}"), 400
    bundle = request.files.get("bundle")
    report_text = request.form.get("report_text", "").strip()
    if bundle is None and not report_text:
        return jsonify(error="请上传 solution ZIP 或粘贴报告文本"), 400

    sub_id = str(uuid.uuid4())
    sdir = SUB_DIR / sub_id
    sol = sdir / "solution"
    sol.mkdir(parents=True, exist_ok=True)

    if bundle and bundle.filename:
        fn = bundle.filename or ""
        if not fn.lower().endswith(".zip"):
            return jsonify(error="仅支持 .zip"), 400
        zp = sdir / "bundle.zip"
        bundle.save(zp)
        try:
            with zipfile.ZipFile(zp) as z:
                for m in z.namelist():  # 防 zip slip
                    if m.startswith("/") or ".." in Path(m).parts:
                        continue
                    z.extract(m, sdir / "_unzip")
            src = sdir / "_unzip"
            # 若 zip 里只有一层目录则下钻
            entries = [e for e in src.iterdir() if e.name != "__MACOSX"]
            if len(entries) == 1 and entries[0].is_dir():
                src = entries[0]
            for p in src.iterdir():
                os.rename(p, sol / p.name)
        except zipfile.BadZipFile:
            return jsonify(error="ZIP 文件损坏"), 400
        # 粘贴文本作为 report.md 一并保留
        if report_text:
            (sol / "report.md").write_text(report_text, encoding="utf-8")
    else:
        (sol / "report.md").write_text(report_text, encoding="utf-8")
        (sol / "README.txt").write_text(
            "本提交仅包含粘贴的 report 文本，无代码/指标产物。", encoding="utf-8")

    meta = {"card_id": card_id, "agent_name": request.form.get("agent_name", "").strip() or "anonymous",
            "agent_version": request.form.get("agent_version", "").strip(),
            "description": request.form.get("description", "").strip()[:2000],
            "mode": judge_service.JUDGE_MODE,
            "has_bundle": bool(bundle and bundle.filename)}
    card = _CARDS[card_id]
    card_dir = REPO / "tasks" / card["domain"] / card["id"]
    threading.Thread(target=judge_service.run_submission,
                     args=(sub_id, card, card_dir, sol, meta), daemon=True).start()
    return jsonify(submission_id=sub_id, status_url=f"/api/submissions/{sub_id}"), 202


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    print(f"* PAPER_BENCH_ROOT = {REPO}")
    print(f"* JUDGE_MODE       = {judge_service.JUDGE_MODE}"
          + ("" if judge_service.JUDGE_MODE != "llm" else (" (key set)" if judge_service.j105_ok() else "  ⚠ 缺 JUDGE_API_KEY")))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
