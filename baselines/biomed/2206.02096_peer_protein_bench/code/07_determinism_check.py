"""Determinism self-check (run-to-run): train CNN seed 2024 twice back-to-back
with identical code + frozen data and require bit-exact identical test accuracy,
and additionally require it to equal the value recorded in
results/encoder_model_results.json. Confirms both reproducibility across
launches and consistency of the delivered evidence."""
import os
import sys
import json
import importlib.util

from common import load_split, set_seed, get_device

HERE = os.path.dirname(__file__)
spec = importlib.util.spec_from_file_location("enc", os.path.join(HERE, "03_encoder_models.py"))
enc = importlib.util.module_from_spec(spec)
sys.modules["enc"] = enc
spec.loader.exec_module(enc)

set_seed(2024)
device, workers = get_device()
train, valid, test = load_split("train"), load_split("valid"), load_split("test")

accs = []
for i in range(2):
    res = enc.run_model("CNN", enc.CNNModel, train, valid, test, device, workers)
    v = [r["test_acc_pct"] for r in res["runs"] if r["seed"] == 2024][0]
    accs.append(v)
    print(f"[run {i+1}] CNN seed 2024 test acc = {v:.6f}")

assert accs[0] == accs[1], f"run-to-run mismatch: {accs}"
with open(os.path.join(HERE, "..", "results", "encoder_model_results.json")) as f:
    saved = json.load(f)
sv = [r["test_acc_pct"] for r in saved["CNN"]["runs"] if r["seed"] == 2024][0]
assert abs(accs[0] - sv) < 1e-9, f"mismatch vs delivered evidence: {accs[0]} != {sv}"
print(f"matches delivered evidence ({sv:.6f}); DETERMINISM OK (bit-exact)")