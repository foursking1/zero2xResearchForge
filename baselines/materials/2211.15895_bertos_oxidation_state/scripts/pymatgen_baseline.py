#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pymatgen_baseline.py - Reproduce the paper's comparison of BERTOS against
Pymatgen's heuristic oxidation-state guessing on the frozen test sets.

Paper claim (Sec 3): "when we use the Pymatgen's oxid state guess function,
only 4.49% of the test samples can be assigned definite oxidation states."

A "definite assignment" here means Composition(name).oxi_state_guesses()
returns exactly one consistent oxidation-state assignment covering all elements
of the compound. We report that fraction per frozen test set.

Usage: python3 pymatgen_baseline.py --data <data_root> [--split test]
"""
import argparse
import os
import signal

from pymatgen.core.composition import Composition


def load_blocks(ds_name, split, data_root):
    import zipfile
    with zipfile.ZipFile(os.path.join(data_root, "datasets", f"{ds_name}.zip")) as z:
        text = z.read(f"{ds_name}/{split}.txt").decode("utf-8")
    blocks = []
    for chunk in text.split("\n\n"):
        lines = [ln for ln in chunk.splitlines() if ln.strip()]
        if lines:
            elements = {}
            for ln in lines:
                ele = ln.split()[0]
                elements[ele] = elements.get(ele, 0) + 1
            formula = "".join(f"{e}{c}" if c > 1 else e for e, c in elements.items())
            blocks.append((formula, elements))
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--split", default="test")
    ap.add_argument("--datasets", default="ICSD,ICSD_CN,ICSD_oxide,ICSD_CN_oxide")
    ap.add_argument("--cap_ms", type=int, default=1000,
                    help="Abort oxi_state_guesses for a sample after this many ms "
                         "and treat it as non-definite (guards against combinatorial blowup).")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    data_root = args.data or os.path.normpath(os.path.join(here, "..", "..", "data"))

    import warnings
    warnings.filterwarnings("ignore")
    import time

    def _timeout(signum, frame):
        raise TimeoutError("oxi_state_guesses took too long")

    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(0)

    for ds in args.datasets.split(","):
        blocks = load_blocks(ds, args.split, data_root)
        definite = 0
        total = 0
        capped = 0
        for formula, elements in blocks:
            total += 1
            if total % 500 == 0:
                print(f"  {ds}: {total} done, definite={definite}, "
                      f"running={definite/total*100:.2f}%", flush=True)
            try:
                comp = Composition(formula)
                t0 = time.time()
                signal.alarm(max(1, args.cap_ms // 1000))
                try:
                    guesses = comp.oxi_state_guesses()
                finally:
                    signal.alarm(0)
                if (time.time() - t0) * 1000 > args.cap_ms:
                    capped += 1
            except TimeoutError:
                capped += 1
                guesses = []
            except Exception:
                guesses = []
            if isinstance(guesses, list) and len(guesses) == 1:
                definite += 1
        print(f"{ds:15s} [{args.split}] samples={total} definite={definite} "
              f"definite_ratio={definite/total*100:.4f}% (timeout_capped={capped})", flush=True)


if __name__ == "__main__":
    main()