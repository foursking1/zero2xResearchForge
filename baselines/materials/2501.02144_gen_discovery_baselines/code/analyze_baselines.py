"""
Task 2: 2501.02144_gen_discovery_baselines
Recompute per-method statistics (median dEd, stability rate, distribution
quantiles) from the frozen CSV structure lists, and compare with paper Table 1.

Usage:
    python analyze_baselines.py [root_dir] [out_dir]

root_dir defaults to F:/dataset/materials/2501.02144_gen_discovery_baselines/structures
out_dir  defaults to <script_dir>/../results
"""
import hashlib
import json
import os
import sys

METHODS = ["Random", "Ion-Exchange", "CrystaLLM", "CDVAE", "FTCP", "MatterGen"]

# SHA-256 from data/CHECKSUMS_SHA256.tsv (paths relative to data/)
CHECKSUMS = {
    "CDVAE.csv": "c67ce24444a21a6054c5687d51592a2d311cd61c972db9cb36c9e3d2021d9961",
    "CrystaLLM.csv": "cfad3e3e757dc795f388ab7338840206b071afc0b66df07ba4a13d6988f7e7ca",
    "FTCP.csv": None,  # filled below if present in tsv
    "Ion-Exchange.csv": None,
    "MatterGen.csv": None,
    "Random.csv": None,
}


def load_checksums():
    here = os.path.dirname(os.path.abspath(__file__))
    # try task data dir then parent
    candidates = [
        os.path.join(here, "..", "data", "CHECKSUMS_SHA256.tsv"),
        os.path.join(here, "..", "..", "data", "CHECKSUMS_SHA256.tsv"),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, encoding="utf-8-sig") as f:
                return f.read().splitlines()
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else (
        r"F:/dataset/materials/2501.02144_gen_discovery_baselines/structures")
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "results")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # checksums
    checksum_lines = load_checksums()
    cs_map = {}
    if checksum_lines:
        for line in checksum_lines:
            line = line.strip()
            if not line or "\t" not in line:
                continue
            rel, h = line.split("\t")
            cs_map[os.path.basename(rel)] = h
    print("checksum map entries:", len(cs_map))

    import csv
    rows_out = []
    metrics = {
        "task_id": "2501.02144_gen_discovery_baselines",
        "n_per_method": {},
        "median_Ed_meV_atom": {},
        "stability_rate_pct": {},
        "quantiles_meV_atom": {},
        "mean_Ed_meV_atom": {},
        "checksums_ok": {},
    }

    for m in METHODS:
        path = os.path.join(root, m + ".csv")
        if not os.path.exists(path):
            print("MISSING", path)
            continue
        csum = sha256(path)
        exp = cs_map.get(m + ".csv")
        ok = (exp is None) or (exp.lower() == csum.lower())
        metrics["checksums_ok"][m] = {"computed": csum, "expected": exp, "ok": ok}
        if exp is None:
            print(f"[warn] no expected checksum for {m}.csv")

        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader]
        n = len(rows)
        # Ed column
        ed = [float(r["Ed (eV/atom)"]) for r in rows]
        ed_meV = [v * 1000.0 for v in ed]
        n_ok = sum(1 for v in ed if v <= 0)
        import statistics
        med = statistics.median(ed_meV)
        mean = statistics.mean(ed_meV)
        stab = n_ok / n * 100.0
        qs = [20, 50, 80, 90]
        import numpy as np
        quantiles = {q: float(np.percentile(ed_meV, q)) for q in qs}

        metrics["n_per_method"][m] = n
        metrics["median_Ed_meV_atom"][m] = round(med, 3)
        metrics["mean_Ed_meV_atom"][m] = round(mean, 3)
        metrics["stability_rate_pct"][m] = round(stab, 3)
        metrics["quantiles_meV_atom"][m] = {str(q): round(v, 3) for q, v in quantiles.items()}

        rows_out.append({
            "method": m, "n": n, "median_Ed_meV_atom": round(med, 3),
            "stability_rate_pct": round(stab, 3), "mean_Ed_meV_atom": round(mean, 3),
            **{f"q{q}": round(v, 3) for q, v in quantiles.items()},
        })
        print(f"{m:<14s} n={n} median={med:.3f} meV/atom stab={stab:.3f}% q80={quantiles[80]:.3f}")

    # paper Table 1 reference
    paper_ref = {
        "Random": {"med": 409, "stab": 1.4},
        "Ion-Exchange": {"med": 85, "stab": 9.2},
        "CrystaLLM": {"med": 442, "stab": 2.4},
        "CDVAE": {"med": 207, "stab": 1.8},
        "FTCP": {"med": 205, "stab": 2.0},
        "MatterGen": {"med": 188, "stab": 3.0},
    }
    metrics["paper_table1_ref"] = paper_ref

    # ranking
    ranked = sorted(METHODS, key=lambda m: metrics["median_Ed_meV_atom"][m])
    metrics["median_ranking"] = ranked
    ranked_stab = sorted(METHODS, key=lambda m: -metrics["stability_rate_pct"][m])
    metrics["stability_ranking"] = ranked_stab
    print("\nMedian ranking:", ranked)
    print("Stability ranking:", ranked_stab)

    with open(os.path.join(out_dir, "evidence_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        w.writeheader()
        w.writerows(rows_out)
    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("\nWrote", os.path.join(out_dir, "evidence_table.csv"))
    print("Wrote", os.path.join(out_dir, "metrics.json"))


if __name__ == "__main__":
    main()
