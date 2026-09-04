import hashlib, os, random

base = r"F:/dataset/materials/2608.06662_mlip_cross_geometry/ZrO2"
sums = {}
with open(r"D:/project/paper-bench/tasks/materials/2608.06662_mlip_cross_geometry/data/checksums.sha256") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1]] = parts[0]

files = []
for g in ["bulk", "slab", "particle", "neck", "wire"]:
    for fn in os.listdir(os.path.join(base, g)):
        files.append(os.path.join(g, fn))
print("total xyz:", len(files))

random.seed(42)
sample = random.sample(files, 8)
allok = True
for rel in sample:
    key = "ZrO2/" + rel.replace("/", "\\")
    h = hashlib.sha256(open(os.path.join(base, rel), "rb").read()).hexdigest()
    ok = sums.get(key) == h
    if not ok:
        allok = False
    print(("OK  " if ok else "FAIL"), rel)
print("ALL OK:", allok)
