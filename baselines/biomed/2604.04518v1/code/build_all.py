"""Detached rebuild of all real-dataset tensors at IMG_SIZE=128."""
import os
import subprocess
import sys

specs = [
    ("smiling", "symmetric"),
    ("smiling", "asymmetric"),
    ("blond", "symmetric"),
    ("blond", "asymmetric"),
    ("camelyon", "symmetric"),
    ("camelyon", "asymmetric"),
]
code = os.path.dirname(os.path.abspath(__file__))
for kind, poison in specs:
    print(f"=== building {kind} {poison} ===", flush=True)
    env = dict(os.environ)
    env["IMG_SIZE"] = "128"
    env["BUILD_WORKERS"] = "6"
    env["OMP_THREADS"] = "1"
    r = subprocess.call([sys.executable, "build_tensors.py", kind, poison],
                        cwd=code, env=env)
    if r != 0:
        print(f"FAILED {kind} {poison}", flush=True)
        sys.exit(r)
print("ALL_DONE", flush=True)
