"""Verify the frozen input data against the shipped SHA-256 manifest."""
import hashlib
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data")
MANIFEST = os.path.join(ROOT, "CHECKSUMS_SHA256.tsv")


def main():
    with open(MANIFEST) as f:
        next(f)
        manifest = {}
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 3:
                continue
            rel, sha, _ = parts
            manifest[rel] = sha
    bad = []
    ok = 0
    for rel, sha in manifest.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append((rel, "MISSING"))
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h == sha:
            ok += 1
        else:
            bad.append((rel, "HASH MISMATCH"))
    print(f"verified {ok}/{len(manifest)} frozen files")
    if bad:
        print("!! problems:")
        for rel, why in bad[:20]:
            print(f"   {rel}: {why}")
        raise SystemExit(1)
    print("all files match the benchmark manifest (Apache-2.0 repo snapshot)")


if __name__ == "__main__":
    main()