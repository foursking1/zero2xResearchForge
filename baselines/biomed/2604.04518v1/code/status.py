"""Print a compact status of all reproduction artifacts and running jobs."""
import json
import os
import subprocess
import sys

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workspace")
WS = os.path.normpath(WS)

def jload(p):
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None

print("=== STUDENTS (C01 baseline) ===")
sa = jload(os.path.join(WS, "results", "students_all.json")) or []
for r in sa:
    print(f"  {r['dataset']:<9} {r['poison']:<10} aga={r['test_aga']:.4f} wga={r['test_wga']:.4f}")

print("\n=== CORRECTIONS (GT labels, C02) ===")
corr = os.path.join(WS, "results", "corrections")
if os.path.isdir(corr):
    for d in sorted(os.listdir(corr)):
        for f in sorted(os.listdir(os.path.join(corr, d))):
            if f.endswith(".json"):
                r = jload(os.path.join(corr, d, f))
                if r:
                    print(f"  {d:<22} {f[:-5]:<8} aga={r.get('test_aga'):.4f} wga={r.get('test_wga'):.4f}")

print("\n=== CFKD (C03) ===")
cfkd = os.path.join(WS, "results", "cfkd")
if os.path.isdir(cfkd):
    for f in sorted(os.listdir(cfkd)):
        if f.endswith(".json"):
            r = jload(os.path.join(cfkd, f))
            if r:
                print(f"  {f[:-5]:<25} aga={r.get('test_aga'):.4f} wga={r.get('test_wga'):.4f}")

print("\n=== SPRAY LABELS (C05) ===")
sl = os.path.join(WS, "spray_labels")
if os.path.isdir(sl):
    for d in sorted(os.listdir(sl)):
        for f in sorted(os.listdir(os.path.join(sl, d))):
            if f.startswith("metrics"):
                r = jload(os.path.join(sl, d, f))
                if r:
                    print(f"  {d:<20} {f[:-5]:<12} mean_acc={r.get('mean_acc'):.4f}")

print("\n=== SPRAY CORRECTIONS (C04) ===")
sp = os.path.join(WS, "results", "corrections_spray")
if os.path.isdir(sp):
    for d in sorted(os.listdir(sp)):
        for f in sorted(os.listdir(os.path.join(sp, d))):
            if f.endswith(".json"):
                r = jload(os.path.join(sp, d, f))
                if r:
                    print(f"  {d:<22} {f[:-5]:<8} aga={r.get('test_aga'):.4f} wga={r.get('test_wga'):.4f}")

print("\n=== TRAINING LOGS (last lines) ===")
lg = os.path.join(WS, "logs")
for f in sorted(os.listdir(lg)):
    if f.endswith(".log") and ("train" in f or f in ("squares_sym.log",)):
        path = os.path.join(lg, f)
        try:
            with open(path) as fh:
                lines = fh.read().strip().splitlines()
            last = lines[-1] if lines else ""
            print(f"  {f:<35} | {last[:100]}")
        except Exception:
            pass

print("\n=== RUNNING PYTHON JOBS (mine) ===")
try:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
         "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
        capture_output=True, text=True, timeout=30).stdout
    procs = json.loads(out) if out.strip() else []
    if isinstance(procs, dict):
        procs = [procs]
    mine = [p for p in procs
            if any(k in p.get("CommandLine", "")
                   for k in ("train_student", "run_corrections", "eval_one",
                             "cfkd", "spray", "status"))]
    for p in mine:
        cmd = p.get("CommandLine", "")
        print(f"  {p['ProcessId']:<7} | {cmd[:90]}")
except Exception as e:
    print(f"  (proc scan failed: {e})")

print("\n=== DISK ===")
try:
    for drive in ("D:", "C:"):
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              f"Get-PSDrive {drive[0]} | Select-Object Used,Free | ConvertTo-Json -Compress"],
                             capture_output=True, text=True, timeout=30).stdout
        d = json.loads(out)
        if isinstance(d, dict):
            print(f"  {drive} free={d.get('Free',0)/1e9:.2f} GB")
except Exception as e:
    print(f"  (disk scan failed: {e})")
