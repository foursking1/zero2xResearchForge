#!/usr/bin/env python3
"""Judge one organization-member submission without changing benchmark baselines."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import ssl
import sys
import urllib.request


ROOT = Path(os.environ.get("PAPER_BENCH_ROOT", Path(__file__).resolve().parents[1])).resolve()
EVALUATION = ROOT / "evaluation"
if str(EVALUATION) not in sys.path:
    sys.path.insert(0, str(EVALUATION))

import judge_eval105_v7 as judge  # noqa: E402
import judge_v7_full as full_judge  # noqa: E402
from card_material import required_paths  # noqa: E402


def resolve_card(reference: str) -> tuple[dict[str, str], Path]:
    if "/" not in reference:
        raise ValueError("card must use domain/card_id")
    domain, card_id = reference.strip("/").split("/", 1)
    with (ROOT / "cards.csv").open(encoding="utf-8-sig", newline="") as handle:
        cards = list(csv.DictReader(handle))
    matches = [card for card in cards if card["domain"] == domain and card["card_id"] == card_id]
    if len(matches) != 1:
        raise ValueError(f"unknown card: {reference}")
    card_dir = ROOT / "tasks" / domain / card_id
    missing = [name for name, path in required_paths(card_dir).items() if not path.is_file()]
    if missing:
        raise ValueError(f"card is missing private evaluation files: {', '.join(missing)}")
    return matches[0], card_dir


def render_report(card_ref: str, submission: Path, model: str, result: dict) -> str:
    def text(key: str) -> str:
        value = result.get(key, "")
        if isinstance(value, list):
            return "; ".join(str(item) for item in value)
        return str(value)

    return "\n".join([
        f"# Evaluation: {card_ref}",
        "",
        f"- Submission: `{submission}`",
        f"- Judge model: `{model}`",
        f"- Scored at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        f"## Score: {result.get('total', 0)} / 100",
        "",
        "| Component | Score | Maximum |",
        "|---|---:|---:|",
        f"| A1 delivery | {result.get('A1', 0)} | 12 |",
        f"| A2 scientific fidelity | {result.get('A2', 0)} | 33 |",
        f"| A3 rigor | {result.get('A3', 0)} | 15 |",
        f"| A total | {result.get('A', 0)} | 60 |",
        f"| B truth agreement | {result.get('B', 0)} | 40 |",
        "",
        "## Decision",
        "",
        f"- Conclusion: `{text('conclusion')}`",
        f"- Truth check: `{text('truth_check')}`",
        f"- Enforcement: {text('enforce_note')}",
        "",
        "## Notes",
        "",
        text("A_notes"),
        "",
        text("B_notes"),
        "",
        "## Weaknesses",
        "",
        text("weaknesses"),
        "",
    ])


def call_llm(card_dir: Path, submission: Path, model: str) -> tuple[dict, dict]:
    if not judge.API_KEY:
        raise RuntimeError("JUDGE_API_KEY is required; put it in the environment or ignored .env")
    prompt_file = EVALUATION / "JUDGE_PROMPT_v7.md"
    if not prompt_file.is_file():
        raise RuntimeError(f"missing judge prompt: {prompt_file}")
    evidence = judge.scan_evidence(str(submission), str(card_dir))
    user = judge.USER_TMPL.format(
        spec=judge.collect_spec(str(card_dir)),
        artifacts=judge.collect_artifacts(str(submission)),
        evidence=judge.evidence_line(evidence),
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_file.read_text(encoding="utf-8")},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 6000,
    }
    request = urllib.request.Request(
        judge.API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {judge.API_KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300, context=ssl.create_default_context()) as response:
        raw = json.loads(response.read().decode("utf-8", "replace"))
    content = raw["choices"][0]["message"]["content"]
    return full_judge.enforce(judge.parse_json(content, evidence)), evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", help="domain/card_id")
    parser.add_argument("--submission", required=True, help="directory containing the member submission")
    parser.add_argument("--output", required=True, help="directory for result.json and report.md")
    parser.add_argument("--model", default=os.environ.get("JUDGE_MODEL", judge.DEFAULT_MODEL))
    parser.add_argument("--dry-run", action="store_true", help="inspect inputs without calling the LLM")
    args = parser.parse_args()

    card, card_dir = resolve_card(args.card)
    submission = Path(args.submission).expanduser().resolve()
    if not submission.is_dir():
        raise SystemExit(f"submission directory does not exist: {submission}")
    evidence = judge.scan_evidence(str(submission), str(card_dir))
    if args.dry_run:
        print(f"dry run passed: {card['domain']}/{card['card_id']}")
        print(f"submission: {submission}")
        print(judge.evidence_line(evidence))
        return 0

    try:
        result, evidence = call_llm(card_dir, submission, args.model)
    except (KeyError, OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"evaluation failed: {error}") from error

    output = Path(args.output).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    card_ref = f"{card['domain']}/{card['card_id']}"
    record = {
        "schema_version": 1,
        "card": card_ref,
        "submission": str(submission),
        "judge_model": args.model,
        "scored_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence": evidence,
        "result": result,
    }
    (output / "result.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "report.md").write_text(render_report(card_ref, submission, args.model, result), encoding="utf-8")
    print(f"evaluation complete: {output / 'result.json'}")
    print(f"score: {result.get('total', 0)} / 100 ({result.get('conclusion', 'unknown')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
