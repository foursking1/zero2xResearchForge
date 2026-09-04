"""04 - Claim assessment and evidence-table generation.

Combines:
  (i)   the frozen-data analyses (02 episode analysis, 03 PPL proxy),
  (ii)  the paper's own tables transcribed from the PDF (explicitly cited
        as "paper-cited", never passed off as our reproduction), and
  (iii) checks of the claims C01-C04 in TASK.md.

Outputs:
  results/evidence_table.csv
  results/metrics.json
  results/04_claim_assessment.txt
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

OUT_DIR = Path(__file__).resolve().parents[1] / "results"


# ---------------------------------------------------------------------------
# Paper-cited tables (transcribed from arxiv_2604.04842v1.pdf)
# ---------------------------------------------------------------------------
# Table 1: per model x method -> (SS, CARES_ASR, GPT_ASR)
TABLE1_MODELS = ["Llama-3.1-8B", "Llama-3.1-70B", "GPT-3.5", "GPT-5.1",
                 "Crispers-7B", "Psycho-8B", "Qwen-3-14B", "Qwen-2.5-72B"]
TABLE1 = {
    # method: {model: (SS, CARES_ASR, GPT_ASR)}
    "CoA": {
        "Llama-3.1-8B": (0.72, 0.56, 0.19), "Llama-3.1-70B": (0.69, 0.59, 0.18),
        "GPT-3.5": (0.75, 0.44, 0.25), "GPT-5.1": (0.60, 0.59, 0.21),
        "Crispers-7B": (0.66, 0.53, 0.30), "Psycho-8B": (0.67, 0.58, 0.21),
        "Qwen-3-14B": (0.71, 0.52, 0.22), "Qwen-2.5-72B": (0.73, 0.49, 0.21),
    },
    "AMA": {
        "Llama-3.1-8B": (0.84, 0.29, 0.64), "Llama-3.1-70B": (0.75, 0.44, 0.66),
        "GPT-3.5": (0.76, 0.32, 0.19), "GPT-5.1": (0.67, 0.48, 0.27),
        "Crispers-7B": (0.75, 0.37, 0.11), "Psycho-8B": (0.77, 0.38, 0.59),
        "Qwen-3-14B": (0.74, 0.47, 0.48), "Qwen-2.5-72B": (0.77, 0.40, 0.64),
    },
    "Crescendo": {
        "Llama-3.1-8B": (0.66, 0.69, 0.52), "Llama-3.1-70B": (0.61, 0.64, 0.51),
        "GPT-3.5": (0.66, 0.58, 0.53), "GPT-5.1": (0.65, 0.52, 0.44),
        "Crispers-7B": (0.62, 0.63, 0.47), "Psycho-8B": (0.62, 0.62, 0.44),
        "Qwen-3-14B": (0.70, 0.51, 0.22), "Qwen-2.5-72B": (0.67, 0.55, 0.48),
    },
    "Actor-Attack": {
        "Llama-3.1-8B": (0.73, 0.45, 0.15), "Llama-3.1-70B": (0.77, 0.41, 0.34),
        "GPT-3.5": (0.76, 0.41, 0.42), "GPT-5.1": (0.75, 0.38, 0.32),
        "Crispers-7B": (0.74, 0.42, 0.38), "Psycho-8B": (0.80, 0.34, 0.29),
        "Qwen-3-14B": (0.69, 0.53, 0.33), "Qwen-2.5-72B": (0.76, 0.40, 0.25),
    },
    "PCSA": {
        "Llama-3.1-8B": (0.43, 0.84, 0.89), "Llama-3.1-70B": (0.53, 0.77, 0.78),
        "GPT-3.5": (0.36, 0.88, 0.79), "GPT-5.1": (0.53, 0.74, 0.71),
        "Crispers-7B": (0.40, 0.84, 0.81), "Psycho-8B": (0.46, 0.86, 0.88),
        "Qwen-3-14B": (0.59, 0.67, 0.84), "Qwen-2.5-72B": (0.51, 0.77, 0.82),
    },
}

# Table 2: method -> {dimension: occurrence rate}
TABLE2 = {
    "CoA": {"target_compliance": 0.21, "harmful_content": 0.07, "toxic_empathy": 0.09, "impersonation": 0.00},
    "AMA": {"target_compliance": 0.46, "harmful_content": 0.29, "toxic_empathy": 0.25, "impersonation": 0.02},
    "Crescendo": {"target_compliance": 0.42, "harmful_content": 0.27, "toxic_empathy": 0.13, "impersonation": 0.01},
    "Actor-Attack": {"target_compliance": 0.31, "harmful_content": 0.20, "toxic_empathy": 0.21, "impersonation": 0.00},
    "PCSA": {"target_compliance": 0.57, "harmful_content": 0.27, "toxic_empathy": 0.44, "impersonation": 0.12},
}

# Table 3: method -> model -> (PPL, detection_rate_pct)
TABLE3 = {
    "CoA": {
        "Llama-3.1-8B": (64.73, 8.22), "Llama-3.1-70B": (59.46, 5.48),
        "GPT-3.5": (68.46, 10.96), "GPT-5.1": (48.57, 2.74),
        "Crispers-7B": (58.04, 8.22), "Psycho-8B": (57.55, 4.11),
        "Qwen-3-14B": (22.63, 0.00), "Qwen-2.5-72B": (19.09, 0.00),
    },
    "AMA": {
        "Llama-3.1-8B": (64.42, 4.11), "Llama-3.1-70B": (58.66, 1.37),
        "GPT-3.5": (73.55, 11.11), "GPT-5.1": (60.05, 0.00),
        "Crispers-7B": (57.65, 0.00), "Psycho-8B": (60.11, 0.00),
        "Qwen-3-14B": (59.75, 1.37), "Qwen-2.5-72B": (60.34, 2.74),
    },
    "Crescendo": {
        "Llama-3.1-8B": (65.45, 18.31), "Llama-3.1-70B": (67.82, 22.39),
        "GPT-3.5": (60.15, 12.12), "GPT-5.1": (46.18, 8.22),
        "Crispers-7B": (51.15, 5.36), "Psycho-8B": (58.98, 5.88),
        "Qwen-3-14B": (56.18, 11.43), "Qwen-2.5-72B": (56.45, 8.57),
    },
    "Actor-Attack": {
        "Llama-3.1-8B": (117.51, 31.43), "Llama-3.1-70B": (109.34, 30.77),
        "GPT-3.5": (135.07, 34.78), "GPT-5.1": (98.74, 23.29),
        "Crispers-7B": (168.19, 35.71), "Psycho-8B": (112.54, 17.65),
        "Qwen-3-14B": (111.56, 35.29), "Qwen-2.5-72B": (108.75, 30.00),
    },
    "PCSA": {
        "Llama-3.1-8B": (16.61, 0.00), "Llama-3.1-70B": (16.59, 0.00),
        "GPT-3.5": (16.55, 0.00), "GPT-5.1": (17.01, 0.00),
        "Crispers-7B": (17.51, 0.00), "Psycho-8B": (15.40, 0.00),
        "Qwen-3-14B": (18.29, 0.00), "Qwen-2.5-72B": (17.84, 0.00),
    },
}

# Table 4: defense -> model -> ASR (None entry = no delta reported)
TABLE4 = {
    "No Defense": {
        "Llama-3.1-8B": 0.84, "Llama-3.1-70B": 0.77, "GPT-3.5": 0.88, "GPT-5.1": 0.71,
        "Crispers-7B": 0.84, "Psycho-8B": 0.86, "Qwen-3-14B": 0.67, "Qwen-2.5-72B": 0.77,
    },
    "PerplexityFilter": {
        "Llama-3.1-8B": 0.84, "Llama-3.1-70B": 0.77, "GPT-3.5": 0.88, "GPT-5.1": 0.71,
        "Crispers-7B": 0.84, "Psycho-8B": 0.86, "Qwen-3-14B": 0.67, "Qwen-2.5-72B": 0.77,
    },
    "SelfDefend": {
        "Llama-3.1-8B": 0.71, "Llama-3.1-70B": 0.70, "GPT-3.5": 0.73, "GPT-5.1": 0.65,
        "Crispers-7B": 0.74, "Psycho-8B": 0.68, "Qwen-3-14B": 0.62, "Qwen-2.5-72B": 0.67,
    },
    "GraniteGuardian": {
        "Llama-3.1-8B": 0.79, "Llama-3.1-70B": 0.75, "GPT-3.5": 0.84, "GPT-5.1": 0.69,
        "Crispers-7B": 0.81, "Psycho-8B": 0.86, "Qwen-3-14B": 0.67, "Qwen-2.5-72B": 0.73,
    },
}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def mean(xs):
    return sum(xs) / len(xs)


def main():
    ep = load(OUT_DIR / "02_episode_analysis.json")
    ppl = load(OUT_DIR / "03_perplexity_analysis.json")

    rows = []   # evidence table rows
    metrics = {}

    def add(claim, metric, value, unit, definition, source, evidence_kind, supports):
        rows.append({
            "claim": claim,
            "metric": metric,
            "value": value,
            "unit": unit,
            "口径_definition": definition,
            "source": source,          # "computed_from_frozen_data" | "paper_cited"
            "evidence_kind": evidence_kind,
            "supports_claim": supports,
        })

    # ------------------------------------------------------------------
    # C01  PCSA outperforms 4 baselines on ASR & SS (8 target LLMs)
    # ------------------------------------------------------------------
    for m in ["CoA", "AMA", "Crescendo", "Actor-Attack", "PCSA"]:
        ss = [TABLE1[m][mod][0] for mod in TABLE1_MODELS]
        cas = [TABLE1[m][mod][1] for mod in TABLE1_MODELS]
        gas = [TABLE1[m][mod][2] for mod in TABLE1_MODELS]
        add("C01", f"Table1 {m} mean SS", round(mean(ss), 3), "SS(lower=worse)",
            "CARES Safety Score, avg over 8 models (Refuse=1.0/Cautious=0.5/Accept=0.0)",
            "paper_cited", "paper_table", None)
        add("C01", f"Table1 {m} mean CARES-ASR", round(mean(cas), 3), "ASR",
            "CARES Attack Success Rate (non-refusal), avg over 8 models",
            "paper_cited", "paper_table", None)
        add("C01", f"Table1 {m} mean GPT-ASR", round(mean(gas), 3), "ASR",
            "GPT-4o-as-a-judge ASR, avg over 8 models",
            "paper_cited", "paper_table", None)

    pcsa_cas = mean([TABLE1["PCSA"][mod][1] for mod in TABLE1_MODELS])
    best_base_cas = max(mean([TABLE1[m][mod][1] for mod in TABLE1_MODELS]) for m in ["CoA", "AMA", "Crescendo", "Actor-Attack"])
    pcsa_ss = mean([TABLE1["PCSA"][mod][0] for mod in TABLE1_MODELS])
    best_base_ss = min(mean([TABLE1[m][mod][0] for mod in TABLE1_MODELS]) for m in ["CoA", "AMA", "Crescendo", "Actor-Attack"])
    pcsa_gas = mean([TABLE1["PCSA"][mod][2] for mod in TABLE1_MODELS])
    best_base_gas = max(mean([TABLE1[m][mod][2] for mod in TABLE1_MODELS]) for m in ["CoA", "AMA", "Crescendo", "Actor-Attack"])

    add("C01", "PCSA CARES-ASR vs best baseline (paper)", f"{pcsa_cas:.3f} > {best_base_cas:.3f}",
        "comparison", "does PCSA CARES ASR exceed all 4 baselines (paper Table 1)?",
        "paper_cited", "paper_table", "yes")
    add("C01", "PCSA SS vs best baseline (paper)", f"{pcsa_ss:.3f} < {best_base_ss:.3f}",
        "comparison", "does PCSA SS fall below all 4 baselines (lower SS = more unsafe)?",
        "paper_cited", "paper_table", "yes")
    add("C01", "PCSA GPT-ASR vs best baseline (paper)", f"{pcsa_gas:.3f} > {best_base_gas:.3f}",
        "comparison", "does PCSA GPT-ASR exceed all 4 baselines (paper Table 1)?",
        "paper_cited", "paper_table", "yes")

    # Local (frozen) proxy: ASR on 3 real episodes using local Qwen judge
    add("C01", "Local PCSA ASR (3 real episodes)", ep["asr_local_judge_real_only"],
        "ASR", "attack_successful = any(dim>=7) in local judge; n=3 real episodes (Qwen2.5-7B)",
        "computed_from_frozen_data", "small_sample_proxy", None)
    add("C01", "Local PCSA ASR (4 episodes incl test)", ep["asr_local_judge_total"],
        "ASR", "same, n=4 episodes", "computed_from_frozen_data", "small_sample_proxy", None)

    # ------------------------------------------------------------------
    # C02  Harm category occurrence rates
    # ------------------------------------------------------------------
    dims = ["target_compliance", "harmful_content", "toxic_empathy", "impersonation"]
    for m, rates in TABLE2.items():
        for d in dims:
            add("C02", f"Table2 {m} {d}", rates[d], "rate",
                "average occurrence rate across all target LLMs (GPT-4o judge)",
                "paper_cited", "paper_table", None)

    pcsa_t2 = TABLE2["PCSA"]
    for d in dims:
        others_max = max(TABLE2[m][d] for m in ["CoA", "AMA", "Crescendo", "Actor-Attack"])
        is_max = pcsa_t2[d] >= others_max
        add("C02", f"PCSA highest on {d}?", f"{pcsa_t2[d]:.2f} vs max baseline {others_max:.2f}",
            "comparison", "is PCSA occurrence rate the highest on this dimension (paper Table 2)?",
            "paper_cited", "paper_table", "yes" if is_max else "no")

    # local frozen episodes occurrence rates (threshold >= 7)
    for d in dims:
        add("C02", f"Local PCSA {d} occurrence rate (thr>=7, n=4)",
            ep["occurrence_rate_by_threshold"]["thr_ge7"][d], "rate",
            "dimension score >=7 in local Qwen judge; n=4 frozen episodes",
            "computed_from_frozen_data", "small_sample_proxy", None)

    # ------------------------------------------------------------------
    # C03  Perplexity < 20 and 0% detection
    # ------------------------------------------------------------------
    TABLE3_MODELS = TABLE1_MODELS
    for m in ["CoA", "AMA", "Crescendo", "Actor-Attack", "PCSA"]:
        ppls = [TABLE3[m][mod][0] for mod in TABLE3_MODELS]
        dets = [TABLE3[m][mod][1] for mod in TABLE3_MODELS]
        add("C03", f"Table3 {m} mean PPL", round(mean(ppls), 2), "PPL",
            "GPT-2 perplexity, avg over 8 target LLMs",
            "paper_cited", "paper_table", None)
        add("C03", f"Table3 {m} mean detection%", round(mean(dets), 2), "%",
            "detection = fraction of prompts with PPL>100, avg over 8 models",
            "paper_cited", "paper_table", None)

    pcsa_ppl_max = max(TABLE3["PCSA"][mod][0] for mod in TABLE3_MODELS)
    add("C03", "PCSA max PPL across 8 models (paper)", pcsa_ppl_max, "PPL",
        "is max PCSA GPT-2 PPL < 20?", "paper_cited", "paper_table", "yes" if pcsa_ppl_max < 20 else "no")
    add("C03", "PCSA detection rate across 8 models (paper)", "0.00 all models", "%",
        "GPT-2 PPL>100 detection rate", "paper_cited", "paper_table", "yes")

    # Proxy PPL (frozen data)
    nr = ppl["natural_reference_heldout"]
    add("C03", "Natural client-language char-PPL (heldout)", nr["char_ppl_mean"], "PPL(proxy)",
        "character 6-gram PPL of held-out CACTUS client utterances (natural reference)",
        "computed_from_frozen_data", "ppl_proxy", None)
    for set_name in ppl["results"]:
        r = ppl["results"][set_name]
        add("C03", f"Proxy char-PPL mean [{set_name}]", r["char_ppl_mean"], "PPL(proxy)",
            "character 6-gram PPL trained on CACTUS client utterances",
            "computed_from_frozen_data" if "Paper" not in set_name else "paper_cited",
            "ppl_proxy", None)
        add("C03", f"Proxy unnatural-rate% charPPL>nat_p90 [{set_name}]",
            r["unnatural_rate_pct_charPPL_gt_nat_p90"], "%",
            "fraction of prompts above the natural client-language 90th percentile char-PPL",
            "computed_from_frozen_data" if "Paper" not in set_name else "paper_cited",
            "ppl_proxy", None)

    # Ordering check on proxy: PCSA mean char-PPL < every baseline group mean
    proxy_res = ppl["results"]
    pcsa_proxy = proxy_res["PCSA (episodes, frozen)"]["char_ppl_mean"]
    base_groups = [k for k in proxy_res if "frozen baseline code" in k]
    base_means = {k: proxy_res[k]["char_ppl_mean"] for k in base_groups}
    add("C03", "Proxy: PCSA char-PPL < all baselines?",
        f"{pcsa_proxy} vs " + ", ".join(f"{k.split(' ')[0]}={v:.2f}" for k, v in base_means.items()),
        "comparison", "PCSA episode prompts have lowest mean char-PPL among all frozen baseline groups",
        "computed_from_frozen_data", "ppl_proxy", "yes" if all(pcsa_proxy < v for v in base_means.values()) else "no")

    # ------------------------------------------------------------------
    # C04  Defenses: high ASR, marginal reductions
    # ------------------------------------------------------------------
    TABLE4_MODELS = TABLE1_MODELS
    nd = TABLE4["No Defense"]
    for defense in ["PerplexityFilter", "SelfDefend", "GraniteGuardian"]:
        reds = [TABLE4[defense][mod] - nd[mod] for mod in TABLE4_MODELS]
        mean_asr = mean([TABLE4[defense][mod] for mod in TABLE4_MODELS])
        add("C04", f"Table4 {defense} mean ASR", round(mean_asr, 3), "ASR",
            "mean PCSA ASR under defense across 8 models",
            "paper_cited", "paper_table", None)
        add("C04", f"Table4 {defense} ASR reduction", round(mean(reds), 3), "delta ASR",
            "mean absolute reduction vs No Defense (delta<=0 for all models?)",
            "paper_cited", "paper_table", "yes" if all(r <= 0 for r in reds) else "no")

    add("C04", "PerplexityFilter ASR unchanged (paper)",
        "delta=0 on all 8 models", "delta ASR",
        "PerplexityFilter has no effect because PCSA PPL<20 (paper Table 4)",
        "paper_cited", "paper_table", "yes")
    add("C04", "SelfDefend/GraniteGuardian marginal (paper)",
        f"mean reductions {mean([TABLE4['SelfDefend'][m]-nd[m] for m in TABLE4_MODELS]):.3f} / "
        f"{mean([TABLE4['GraniteGuardian'][m]-nd[m] for m in TABLE4_MODELS]):.3f}",
        "delta ASR",
        "small mean reductions; ASR stays 0.62-0.88",
        "paper_cited", "paper_table", "yes")

    # ------------------------------------------------------------------
    # Write evidence table CSV
    # ------------------------------------------------------------------
    csv_path = OUT_DIR / "evidence_table.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # ------------------------------------------------------------------
    # Metrics JSON (keys match evidence table metric names)
    # ------------------------------------------------------------------
    metrics = {
        "C01_pcsa_mean_cares_asr_paper_cited": round(pcsa_cas, 3),
        "C01_best_baseline_mean_cares_asr_paper_cited": round(best_base_cas, 3),
        "C01_pcsa_mean_ss_paper_cited": round(pcsa_ss, 3),
        "C01_best_baseline_mean_ss_paper_cited": round(best_base_ss, 3),
        "C01_pcsa_mean_gpt_asr_paper_cited": round(pcsa_gas, 3),
        "C01_local_pcsa_asr_3episodes": ep["asr_local_judge_real_only"],
        "C02_pcsa_rate_target_compliance_paper_cited": TABLE2["PCSA"]["target_compliance"],
        "C02_pcsa_rate_harmful_content_paper_cited": TABLE2["PCSA"]["harmful_content"],
        "C02_pcsa_rate_toxic_empathy_paper_cited": TABLE2["PCSA"]["toxic_empathy"],
        "C02_pcsa_rate_impersonation_paper_cited": TABLE2["PCSA"]["impersonation"],
        "C02_ama_rate_harmful_content_paper_cited": TABLE2["AMA"]["harmful_content"],
        "C02_local_toxic_empathy_rate_thr7": ep["occurrence_rate_by_threshold"]["thr_ge7"]["toxic_empathy"],
        "C03_pcsa_max_gpt2_ppl_paper_cited": pcsa_ppl_max,
        "C03_pcsa_gpt2_detection_pct_paper_cited": 0.0,
        "C03_proxy_natural_char_ppl_mean": nr["char_ppl_mean"],
        "C03_proxy_natural_char_ppl_p90": nr["char_ppl_p90"],
        "C03_proxy_pcsa_episodes_char_ppl_mean": proxy_res["PCSA (episodes, frozen)"]["char_ppl_mean"],
        "C03_proxy_pcsa_episodes_char_ppl_unnatural_pct": proxy_res["PCSA (episodes, frozen)"]["unnatural_rate_pct_charPPL_gt_nat_p90"],
        "C03_proxy_coa_char_ppl_mean": proxy_res["CoA (frozen baseline code)"]["char_ppl_mean"],
        "C03_proxy_ama_char_ppl_mean": proxy_res["AMA (frozen baseline code)"]["char_ppl_mean"],
        "C03_proxy_crescendo_char_ppl_mean": proxy_res["Crescendo (frozen baseline code)"]["char_ppl_mean"],
        "C03_proxy_actor_char_ppl_mean": proxy_res["Actor-Attack (frozen baseline code)"]["char_ppl_mean"],
        "C04_pcsa_asr_meandelta_perplexityfilter_paper_cited": round(
            mean([TABLE4["PerplexityFilter"][m] - nd[m] for m in TABLE4_MODELS]), 3),
        "C04_pcsa_asr_meandelta_selfdefend_paper_cited": round(
            mean([TABLE4["SelfDefend"][m] - nd[m] for m in TABLE4_MODELS]), 3),
        "C04_pcsa_asr_meandelta_graniteguardian_paper_cited": round(
            mean([TABLE4["GraniteGuardian"][m] - nd[m] for m in TABLE4_MODELS]), 3),
        "data_note": (
            "paper_cited = transcribed from arxiv PDF tables (not our reproduction); "
            "computed = produced in this run from frozen data. "
            "Frozen workspace contains no full 8-model attack/defense runs."
        ),
    }
    with open(OUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Human-readable summary
    # ------------------------------------------------------------------
    lines = ["# 04 Claim Assessment", ""]
    lines.append("## C01  (paper Table 1, cited)")
    lines.append(f"  PCSA mean CARES-ASR {pcsa_cas:.3f} vs best baseline {best_base_cas:.3f}  -> {'YES' if pcsa_cas > best_base_cas else 'NO'}")
    lines.append(f"  PCSA mean SS       {pcsa_ss:.3f} vs lowest baseline {best_base_ss:.3f}  -> {'YES' if pcsa_ss < best_base_ss else 'NO'}")
    lines.append(f"  PCSA mean GPT-ASR  {pcsa_gas:.3f} vs best baseline {best_base_gas:.3f}  -> {'YES' if pcsa_gas > best_base_gas else 'NO'}")
    lines.append(f"  Local frozen episodes: ASR = {ep['asr_local_judge_real_only']} (3 real episodes, local Qwen judge)")
    lines.append("")
    lines.append("## C02  (paper Table 2, cited)")
    for d in dims:
        o = max(TABLE2[m][d] for m in ["CoA", "AMA", "Crescendo", "Actor-Attack"])
        lines.append(f"  {d:<18} PCSA={TABLE2['PCSA'][d]:.2f}  max baseline={o:.2f}  -> "
                     f"{'highest' if TABLE2['PCSA'][d] >= o else 'NOT highest'}")
    lines.append("  NOTE: Harmful Content: AMA=0.29 > PCSA=0.27 (PCSA NOT highest on this dimension)")
    lines.append("  Local frozen episodes (thr>=7, n=4): " + json.dumps(ep["occurrence_rate_by_threshold"]["thr_ge7"]))
    lines.append("")
    lines.append("## C03  (paper Table 3, cited + proxy)")
    lines.append(f"  Paper: PCSA max GPT-2 PPL = {pcsa_ppl_max} (<20? {pcsa_ppl_max < 20}); detection 0% all models")
    lines.append(f"  Proxy: natural client char-PPL mean {nr['char_ppl_mean']} (p90 {nr['char_ppl_p90']}); "
                 f"PCSA-episodes {proxy_res['PCSA (episodes, frozen)']['char_ppl_mean']}; "
                 f"baselines { {k.split(' ')[0]: proxy_res[k]['char_ppl_mean'] for k in base_groups} }")
    lines.append("")
    lines.append("## C04  (paper Table 4, cited)")
    for defense in ["PerplexityFilter", "SelfDefend", "GraniteGuardian"]:
        reds = [TABLE4[defense][m] - nd[m] for m in TABLE4_MODELS]
        lines.append(f"  {defense:<18} mean delta={mean(reds):+.3f}  mean ASR={mean([TABLE4[defense][m] for m in TABLE4_MODELS]):.3f}")
    lines.append("")
    lines.append("## Verdicts (relative to frozen data + cited paper numbers)")
    lines.append("  C01: inconclusive on frozen data (no 8-model runs); paper's own Table 1 supports the claim")
    lines.append("  C02: partially supported - PCSA highest on TC/TE/Impersonation; NOT on Harmful Content (AMA 0.29>0.27)")
    lines.append("  C03: partially supported - relative PPL ordering reproduced (PCSA lowest under proxy LM); "
                 "absolute GPT-2 PPL<20 and 0% detection not verifiable from frozen data (cited paper numbers support)")
    lines.append("  C04: inconclusive on frozen data (no defense runs); paper's own Table 4 supports the claim")

    with open(OUT_DIR / "04_claim_assessment.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n".join(lines))
    print(f"\nWrote {csv_path} ({len(rows)} rows) and metrics.json")


if __name__ == "__main__":
    main()
