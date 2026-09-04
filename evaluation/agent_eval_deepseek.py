#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek agent 评测 PoC（prompt 式 tool-use 循环）
- 后端：pear-api 网关 DeepSeek-V4-Flash-0731（OpenAI 兼容 /v1/chat/completions）
- 不依赖网关原生 tool_calls（已知挂起），改用 prompt 式 action JSON
- agent 在沙箱内真读文件、真跑提交代码、与 PAPER_ANCHOR 真值做容差比对，最终吐结构化评分
"""
import json, subprocess, os, sys, re, textwrap, time, tempfile
from card_material import material_path, private_card_dir

# 仓库根：默认从本脚本位置推导（evaluation/ 的上一级），可用环境变量覆盖
ROOT = os.environ.get(
    "PAPER_BENCH_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASHRC = os.path.expanduser("~/.bashrc")

def load_env():
    env = dict(os.environ)
    if os.path.exists(BASHRC):
        for line in open(BASHRC, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line.startswith("export ANTHROPIC_"):
                line = line[len("export "):]
                if "=" in line:
                    k, _, v = line.partition("=")
                    v = v.strip().strip('"').strip("'")
                    env[k] = v
    return env

ENV = load_env()
TOKEN = ENV.get("ANTHROPIC_AUTH_TOKEN") or ENV.get("ANTHROPIC_API_KEY")
BASE = ENV.get("ANTHROPIC_BASE_URL", "https://api.pear-api.top")
MODEL = "DeepSeek-V4-Flash-0731"
CHAT = f"{BASE}/v1/chat/completions"

# ---- 探测 chat/completions 接受的 auth header ----
def detect_header():
    body = json.dumps({"model": MODEL, "max_tokens": 50,
                       "messages": [{"role": "user", "content": "hi reply one word"}]})
    for hdr in (("Authorization", f"Bearer {TOKEN}"), ("x-api-key", TOKEN)):
        p = subprocess.run(["curl", "-sS", "-m", "40", "-X", "POST", CHAT,
                            "-H", "content-type: application/json",
                            "-H", f"{hdr[0]}: {hdr[1]}", "-d", body],
                           capture_output=True, text=True)
        try:
            d = json.loads(p.stdout)
            if "choices" in d:
                print(f"[auth] {hdr[0]} -> OK ({d['choices'][0]['message']['content'][:20]!r})", file=sys.stderr)
                return hdr[0], hdr[1]
        except Exception:
            pass
        print(f"[auth] {hdr[0]} -> fail {p.stdout[:120]}", file=sys.stderr)
    return None, None

HDR_NAME, HDR_VAL = detect_header()
if not HDR_NAME:
    print("FATAL: chat/completions 两种 header 都不通", file=sys.stderr); sys.exit(1)

def call_llm(messages, temperature=0, max_tokens=4000):
    payload = {"model": MODEL, "temperature": temperature, "max_tokens": max_tokens,
               "messages": messages}
    for attempt in range(3):
        fd, ppath = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))
        p = subprocess.run(["curl", "-sS", "-m", "150", "-X", "POST", CHAT,
                            "-H", "content-type: application/json",
                            "-H", f"{HDR_NAME}: {HDR_VAL}", "-d", f"@{ppath}"],
                           capture_output=True, text=True)
        os.unlink(ppath)
        try:
            return json.loads(p.stdout)["choices"][0]["message"]["content"]
        except Exception as e:
            err = f"LLM_ERR {e} raw={p.stdout[:200]}"
            if attempt < 2:
                print(f"[retry {attempt+1}] {err}", file=sys.stderr)
                time.sleep(3)
                continue
            return err
    return "LLM_ERR exhausted retries"

# ---- 工具执行（沙箱限定在卡目录内）----
def list_dir(path):
    try:
        out = subprocess.run(["ls", "-la", path], capture_output=True, text=True, timeout=20)
        return out.stdout[:3000] + out.stderr[:500]
    except Exception as e:
        return f"ERR {e}"

def read_file(path, limit=9000):
    path = os.path.normpath(path)
    # 防越界：只允许 ROOT 下
    if not (path.startswith(ROOT) or path.startswith("/mnt/d/project/paper-bench")):
        return "REFUSED: path outside project"
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except Exception as e:
        return f"ERR {e}"

def run_shell(cmd, cwd, timeout=90):
    cwd = os.path.normpath(cwd)
    if not (cwd.startswith(ROOT) or cwd.startswith("/mnt/d/project/paper-bench")):
        return "REFUSED: cwd outside project"
    try:
        p = subprocess.run(["bash", "-c", cmd], cwd=cwd, capture_output=True,
                           text=True, timeout=timeout)
        out = (p.stdout or "") + (p.stderr or "")
        return f"[exit {p.returncode}]\n{out[:4000]}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT after %ds" % timeout
    except Exception as e:
        return f"ERR {e}"

def do_action(act, card_dir):
    a = (act or {}).get("action", "")
    if a == "list_dir":
        return list_dir(act.get("path", card_dir))
    if a == "read_file":
        return read_file(act.get("path", ""))
    if a == "run_shell":
        return run_shell(act.get("cmd", ""), act.get("cwd", card_dir))
    if a == "final_score":
        return "FINAL:" + json.dumps(act, ensure_ascii=False)
    return f"UNKNOWN action: {a}"

# ---- 主循环 ----
SYSTEM = """你是一个严格的科研复现评测 agent。给定一张论文复现任务的提交物，你要：
1) 阅读任务目录中的 TASK.md 了解任务要求与评分维度；
2) 阅读私有评测资料目录中的 PAPER_ANCHOR.md 了解论文真值（关键数值、阈值、方法）；
3) 阅读 baselines/<domain>/<card> 下的历史提交物（metrics.json/report/evidence 等）；
4) 在沙箱中真实执行提交代码，复现关键指标；
5) 将复现结果与真值做容差比对（注意单位、分母口径、阈值）；
6) 给出结构化评分。

总分100，四维度：
- A1 交付完整度 0-12（是否包含可运行代码、结果文件、说明）
- A2 科学保真 0-33（复现结果是否接近真值）
- A3 方法严谨 0-15（方法是否与论文一致、有无取巧）
- B 证据真实性 0-40（提交证据是否真实可验证、与真值一致）
conclusion 取值：supported / partially_supported / contradicted / unverified。

每轮你只能输出一个 JSON 动作（不要多余文字）：
{"action":"list_dir","path":"<绝对路径>"}
{"action":"read_file","path":"<绝对路径>"}
{"action":"run_shell","cmd":"<shell命令>","cwd":"<卡目录绝对路径>"}
{"action":"final_score","A1":0,"A2":0,"A3":0,"B":0,"conclusion":"..","reason":".."}

评估路径示例：先 list_dir 看结构，read_file 分别读任务目录的 TASK.md、私有资料目录的 PAPER_ANCHOR.md，以及 baselines 下的 report 或 metrics，run_shell 跑 python 复现脚本（若有），最后 final_score。"""

def _local_read(p, limit=15000):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except Exception as e:
        return f"(read fail: {e})"

def run_card(card_id, domain, max_turns=45, base="tasks"):
    # legacy 已合并进 tasks/<domain>/<card_id>，所有卡统一走此路径
    card_dir = os.path.join(ROOT, base, domain, card_id)
    baseline_dir = os.path.join(ROOT, "baselines", domain, card_id)
    private_dir = private_card_dir(card_dir)
    if not os.path.isdir(card_dir):
        return {"card": card_id, "error": "no card dir"}
    # 预置 TASK + PAPER_ANCHOR 全文（省去 agent 逐个读的轮次）
    task_md = _local_read(os.path.join(card_dir, "TASK.md"))
    anchor_md = _local_read(material_path(card_dir, "PAPER_ANCHOR.md"))
    # 初始 user 消息：给出路径 + 关键规格/真值全文 + 文件清单
    files = []
    for dp, _, fns in os.walk(card_dir):
        for fn in fns:
            files.append(os.path.join(dp, fn))
    if os.path.isdir(private_dir):
        for dp, _, fns in os.walk(private_dir):
            for fn in fns:
                files.append(os.path.join(dp, fn))
    if os.path.isdir(baseline_dir):
        for dp, _, fns in os.walk(baseline_dir):
            for fn in fns:
                files.append(os.path.join(dp, fn))
    files = [f for f in files if os.path.getsize(f) < 5_000_000][:80]
    init = (f"请评测以下论文复现任务卡：\n任务目录(绝对路径): {card_dir}\n"
            f"私有评测资料目录(绝对路径): {private_dir}\n"
            f"历史基线目录(绝对路径): {baseline_dir}\n\n"
            f"=== TASK.md (任务要求) ===\n{task_md}\n\n"
            f"=== PAPER_ANCHOR.md (论文真值，含关键数值/阈值/方法) ===\n{anchor_md}\n\n"
            f"=== 目录文件清单（共 {len(files)} 个，可用 read_file/list_dir/run_shell 查看与执行）===\n"
            + "\n".join(files)
            + "\n\n请重点阅读历史基线目录下的提交物（report/metrics/claim/code 等）。"
              "评测报告位于 evaluations/，不是提交物证据，不要将其作为评分依据。"
              "在沙箱内真实执行复现代码（WSL 可用 python3，或用 Windows 侧 "
              "C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe），"
              "将复现结果与上方真值做容差比对，最后输出 final_score。\n\n"
              "【收敛约束】探查动作(list_dir 以及仅用于 ls/find/cat 的 run_shell)总计不得超过 4 次，超过后必须 final_score。"
              "若 baseline/code/ 下存在复现脚本(如 dash_run.py/run.py)，优先用 run_shell 真实执行它来复现指标，"
              "再与上方真值做容差比对；若代码无法运行(数据缺失/依赖报错)，不要反复尝试，直接读取已有 metrics.json/report 与真值比对并 final_score。"
              "严禁重复读取同一批文件。")
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": init}]
    print(f"\n===== [{card_id}] 开始 agent 评测 (max {max_turns} turns) =====", file=sys.stderr)
    for turn in range(max_turns):
        raw = call_llm(messages)
        # 抽取第一个 JSON 对象（剥离 ```json 包裹）
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        print(f"[t{turn}] raw_head={raw[:300]!r}", file=sys.stderr)
        if not m:
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": "你的输出不是合法 JSON 动作，请只输出一个 JSON 动作。"})
            continue
        try:
            act = json.loads(m.group(0))
        except Exception as e:
            print(f"[t{turn}] JSON FAIL: {e}", file=sys.stderr)
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": "JSON 解析失败，请只输出一个合法 JSON 动作。"})
            continue
        print(f"[t{turn}] act={act}", file=sys.stderr)
        if act.get("action") == "final_score":
            print(f"  final_score={act}", file=sys.stderr)
            return {"card": card_id, "domain": domain,
                    "A1": act.get("A1"), "A2": act.get("A2"), "A3": act.get("A3"),
                    "B": act.get("B"), "conclusion": act.get("conclusion"),
                    "reason": act.get("reason"), "model": MODEL}
        obs = do_action(act, card_dir)
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": f"执行结果：\n{obs}\n\n请继续（输出下一个 JSON 动作或 final_score）。"})
    return {"card": card_id, "domain": domain, "error": "max_turns exceeded", "model": MODEL}

if __name__ == "__main__":
    # PoC：单卡。参数: card_id domain [max_turns]
    card_id = sys.argv[1] if len(sys.argv) > 1 else "1903.02557_dash_supernova_class"
    domain = sys.argv[2] if len(sys.argv) > 2 else "astro"
    max_turns = int(sys.argv[3]) if len(sys.argv) > 3 else 45
    res = run_card(card_id, domain, max_turns=max_turns)
    print(json.dumps(res, ensure_ascii=False, indent=2))
