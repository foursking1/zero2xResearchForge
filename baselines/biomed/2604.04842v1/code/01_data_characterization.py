"""01 - Characterization of the frozen data.

Produces descriptive statistics for the three input corpora that the paper
uses (Sections 4.1-4.2):
  1. CACTUS CBT counseling corpus (raw + negative-filtered)
  2. CARES medical-safety benchmark (train/test)
  3. persona_profiles.jsonl (PCSA constructed client personas)

Outputs:
  results/01_data_characterization.json
  results/01_data_characterization.txt
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    CACTUS_RAW, CACTUS_NEG, CARES_TRAIN, CARES_TEST, PERSONA_PROFILES,
    load_jsonl,
)

OUT_DIR = Path(__file__).resolve().parents[1] / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def summarize_jsonl_counts(path, key_names, sample_line=None):
    """Count distribution of a set of keys in a JSONL file."""
    counts = {k: collections.Counter() for k in key_names}
    total = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            total += 1
            for k in key_names:
                counts[k][str(d.get(k, "?"))] += 1
    return total, counts


def main():
    report = {}

    # ------------------------------------------------------------------
    # 1. CACTUS corpus
    # ------------------------------------------------------------------
    n_raw, raw_counts = summarize_jsonl_counts(
        CACTUS_RAW, ["attitude", "cbt_technique"])
    n_neg, neg_counts = summarize_jsonl_counts(CACTUS_NEG, ["attitude"])

    # utterance statistics: extract speaker lines from the dialogue field
    utt = collections.Counter()
    n_dialogues = 0
    client_len = []
    counselor_len = []
    with open(CACTUS_RAW, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            n_dialogues += 1
            dialogue = d.get("dialogue", "")
            for m in re.finditer(r"\b(Counselor|Client):\s*(.+?)(?=\b(?:Counselor|Client):|\Z)",
                                 dialogue, flags=re.S):
                role = m.group(1)
                text = m.group(2).strip()
                utt[role] += 1
                if role == "Client":
                    client_len.append(len(text.split()))
                else:
                    counselor_len.append(len(text.split()))
            if n_dialogues >= 100000:
                break

    cactus = {
        "n_dialogues_raw": n_raw,
        "attitude_distribution": dict(raw_counts["attitude"]),
        "n_negative_filtered": n_neg,
        "cbt_technique_distribution": {
            k: v for k, v in sorted(
                raw_counts["cbt_technique"].items(), key=lambda kv: -kv[1])
        },
        "sampled_dialogues_analyzed": n_dialogues,
        "speaker_utterance_counts_sampled": dict(utt),
        "client_mean_tokens_per_utterance": round(
            sum(client_len) / max(1, len(client_len)), 2),
        "counselor_mean_tokens_per_utterance": round(
            sum(counselor_len) / max(1, len(counselor_len)), 2),
    }
    report["cactus"] = cactus

    # ------------------------------------------------------------------
    # 2. CARES benchmark
    # ------------------------------------------------------------------
    cares = {}
    for split, path in [("train", CARES_TRAIN), ("test", CARES_TEST)]:
        n, cnts = summarize_jsonl_counts(
            path, ["harmful_level", "method", "principle_index"])
        cares[split] = {
            "n": n,
            "harmful_level": dict(cnts["harmful_level"]),
            "method": dict(cnts["method"]),
            "principle_index": dict(cnts["principle_index"]),
        }
    report["cares"] = cares

    # ------------------------------------------------------------------
    # 3. Persona profiles
    # ------------------------------------------------------------------
    profiles = load_jsonl(PERSONA_PROFILES)
    pattern_counter = collections.Counter()
    tech_counter = collections.Counter()
    attitude_counter = collections.Counter()
    unique_thoughts = set()
    for p in profiles:
        attitude_counter[p.get("attitude", "?")] += 1
        tech_counter[p.get("cbt_technique", "?")] += 1
        pat = p.get("patterns", [])
        if isinstance(pat, str):
            pat = pat.strip("[]").replace("'", "").split(",")
        pat = [x.strip() for x in pat if x.strip()]
        if pat:
            pattern_counter[pat[0]] += 1  # primary cognitive distortion
        unique_thoughts.add(p.get("thought", ""))
    report["persona_profiles"] = {
        "n_profiles": len(profiles),
        "n_unique_thoughts": len(unique_thoughts),
        "attitude": dict(attitude_counter),
        "cbt_technique": dict(tech_counter),
        "primary_cognitive_distortion": {
            k: v for k, v in sorted(pattern_counter.items(), key=lambda kv: -kv[1])
        },
    }

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    with open(OUT_DIR / "01_data_characterization.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    lines = ["# 01 Data Characterization", ""]
    lines.append("## CACTUS corpus")
    lines.append(json.dumps(cactus, indent=2))
    lines.append("")
    lines.append("## CARES benchmark")
    lines.append(json.dumps(cares, indent=2))
    lines.append("")
    lines.append("## Persona profiles")
    lines.append(json.dumps(report["persona_profiles"], indent=2))
    with open(OUT_DIR / "01_data_characterization.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("Wrote results/01_data_characterization.json")
    print("  CACTUS dialogues:", n_raw, "| negative:", n_neg)
    print("  CARES train:", cares["train"]["n"], "| test:", cares["test"]["n"])
    print("  Persona profiles:", len(profiles))


if __name__ == "__main__":
    import re
    main()
