"""Driver: run the full CPU experiment matrix with resume support.

Run in background:  python run_all.py
Each run saves results/cpu/<data>_<prune_type>_<ratio>_<seed>_<model>.json
"""
import os, subprocess, sys, time

OUT = "results/cpu"
os.makedirs(OUT, exist_ok=True)
EPOCHS = 10
N_TRAIN = 2000
N_TEST = 2000
BATCH = 64

def configs():
    # Run A: CIFAR10 ResNet18, 3 seeds, 5 configs (core C02 comparison)
    for seed in [0, 1, 2]:
        for pt in ["full", "InfoBatch", "BLS_InfoBatch", "SeTa", "BLS_SeTa"]:
            yield dict(data="cifar10", prune_type=pt, ratio=0.3, seed=seed, model="resnet18")
    # Run B: CIFAR100 ResNet18, 2 seeds, 5 configs
    for seed in [0, 1]:
        for pt in ["full", "InfoBatch", "BLS_InfoBatch", "SeTa", "BLS_SeTa"]:
            yield dict(data="cifar100", prune_type=pt, ratio=0.3, seed=seed, model="resnet18")
    # Run C: ratio 0.5 probe on CIFAR10, 2 seeds
    for seed in [0, 1]:
        for pt in ["InfoBatch", "BLS_InfoBatch"]:
            yield dict(data="cifar10", prune_type=pt, ratio=0.5, seed=seed, model="resnet18")
    # Run D: ResNet50 cross-arch on CIFAR100, 1 seed (smaller scale)
    for pt in ["full", "BLS_InfoBatch", "BLS_SeTa"]:
        yield dict(data="cifar100", prune_type=pt, ratio=0.3, seed=0, model="resnet50")

def main():
    total = 0
    for c in configs():
        total += 1
    done = 0
    for c in configs():
        fn = f"{c['data']}_{c['prune_type']}_{c['ratio']}_{c['seed']}_{c['model']}.json"
        path = os.path.join(OUT, fn)
        if os.path.exists(path):
            print(f"SKIP {fn} (exists)", flush=True)
            done += 1
            continue
        cmd = [sys.executable, "run_exp.py", "--data", c["data"], "--prune_type", c["prune_type"],
               "--ratio", str(c["ratio"]), "--seed", str(c["seed"]), "--model", c["model"],
               "--epochs", str(EPOCHS), "--n_train", str(N_TRAIN), "--n_test", str(N_TEST),
               "--batch_size", str(BATCH), "--out", OUT]
        t0 = time.time()
        print(f"[{done+1}/{total}] RUN {fn}", flush=True)
        r = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - t0
        tail = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        print(f"  done in {elapsed:.0f}s | {tail} | rc={r.returncode}", flush=True)
        if r.returncode != 0:
            print(f"  STDERR: {r.stderr[-500:]}", flush=True)
        done += 1
    print("ALL DONE", flush=True)

if __name__ == "__main__":
    main()
