"""05 - Sensitivity of the PPL-proxy ordering to LM choice.

Checks whether "PCSA has the lowest perplexity among methods" is stable
when the proxy language model is changed (word bigram vs word trigram vs
character 6-gram) and when a different (subsampled) training set is used.

This is a cheap sanity check; the primary proxy numbers live in 03.

Outputs:
  results/05_sensitivity.json
  results/05_sensitivity.txt
"""
import json
import math
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CACTUS_RAW, RAW_OUTPUTS, BASELINES_PY, clean_text

OUT_DIR = Path(__file__).resolve().parents[1] / "results"


class WordBigramLM:
    """Word bigram LM with interpolation + Laplace smoothing."""

    def __init__(self, l1=0.25, l2=0.75):
        self.l1, self.l2 = l1, l2
        self.uni = Counter()
        self.bi = Counter()
        self.ctx = Counter()

    def train(self, token_lists):
        for toks in token_lists:
            toks = ["<s>"] + toks + ["</s>"]
            for i, w in enumerate(toks):
                self.uni[w] += 1
                if i >= 1:
                    self.bi[(toks[i - 1], w)] += 1
                    self.ctx[toks[i - 1]] += 1
        self.vocab = len(self.uni)

    def perplexity(self, toks):
        toks = ["<s>"] + toks + ["</s>"]
        logp = 0.0
        for i in range(1, len(toks)):
            w = toks[i]
            pu = self.uni.get(w, 0) / max(1, sum(self.uni.values()))
            pb = (self.bi.get((toks[i - 1], w), 0) + 1) / (self.ctx.get(toks[i - 1], 0) + self.vocab)
            p = self.l1 * pu + self.l2 * pb
            logp += math.log(max(p, 1e-12))
        return math.exp(-logp / (len(toks) - 1))


def get_prompt_sets():
    """Same prompt sets as 03 (re-encoded compactly)."""
    sets = {}
    # PCSA episodes
    pcsa = []
    for p in sorted(Path(RAW_OUTPUTS).glob("episode_*.json")):
        d = json.load(open(p, encoding="utf-8"))
        for m in d.get("conversation", []):
            if m.get("role") == "client":
                pcsa.append(clean_text(m.get("content", "")))
    tp = RAW_OUTPUTS / "test_episode.json"
    if tp.exists():
        d = json.load(open(tp, encoding="utf-8"))
        for m in d.get("conversation", []):
            if m.get("role") == "client":
                pcsa.append(clean_text(m.get("content", "")))
    sets["PCSA (episodes)"] = [p for p in pcsa if p]

    sys.path.insert(0, str(BASELINES_PY.parent.parent))
    from baselines import CoABaseline, AMABaseline, CrescendoBaseline, ActorAttackBaseline

    class DummyTarget:
        def respond(self, msgs):
            return ""

    for cls in [CoABaseline, AMABaseline, CrescendoBaseline, ActorAttackBaseline]:
        b = cls()
        turns = b.run_episode("", DummyTarget(), max_turns=10)
        sets[cls.NAME] = [clean_text(t["client"]) for t in turns]
    return sets


def main():
    print("Collecting CACTUS client utterances...")
    client_texts = []
    with open(CACTUS_RAW, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            for m in re.finditer(r"\bClient:\s*(.+?)(?=\b(?:Counselor|Client):|\Z)",
                                 d.get("dialogue", ""), flags=re.S):
                t = clean_text(m.group(1))
                if t:
                    client_texts.append(t)

    # subsample for speed (150k utterances)
    rng = random.Random(0)
    rng.shuffle(client_texts)
    sub = client_texts[:150000]
    print(f"  training bigram LM on {len(sub)} utterances")

    blm = WordBigramLM()
    blm.train([t.lower().split(" ") for t in sub])

    sets = get_prompt_sets()
    results = {}
    for name, prompts in sets.items():
        pps = [blm.perplexity(p.lower().split(" ")) for p in prompts]
        results[name] = {
            "n": len(prompts),
            "bigram_ppl_mean": round(statistics.mean(pps), 2),
            "bigram_ppl_median": round(statistics.median(pps), 2),
        }

    report = {
        "model": "word bigram LM (interpolation l=(0.25,0.75)), trained on 150k CACTUS client utterances (seed 0)",
        "note": "sensitivity check: does the PCSA-lowest ordering from 03 (char6gram + trigram) persist?",
        "results": results,
        "pcsa_lowest": all(results["PCSA (episodes)"]["bigram_ppl_mean"] < results[b]["bigram_ppl_mean"]
                           for b in results if b != "PCSA (episodes)"),
    }
    with open(OUT_DIR / "05_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    lines = ["# 05 Sensitivity (word bigram LM)", ""]
    lines.append(json.dumps(report, indent=2))
    with open(OUT_DIR / "05_sensitivity.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
