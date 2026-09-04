import numpy as np, os, torch
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from config import SEED, WORKSPACE
from corrections import load_split, split_root
from models import make_resnet18
from spray import attributions

root = split_root("squares", "symmetric")
train, val, test = load_split(root)
model = make_resnet18(2, SEED)
model.load_state_dict(torch.load(os.path.join(WORKSPACE,"models","students","squares_symmetric","best.pt"), weights_only=False))
x = torch.cat([train["images"], val["images"]])
targets = torch.cat([train["targets"], val["targets"]])
groups = torch.cat([train["groups"], val["groups"]])
t = targets.numpy(); g = groups.numpy(); q_true = g % 2
for layer in (6, 12):
    attr, preds = attributions(model, x, layer)
    print(f"layer {layer} attr {attr.shape}", flush=True)
    for cl in np.unique(t):
        idx = np.where(t == cl)[0]
        a = attr[idx]; qc = q_true[idx]
        if qc.sum()==0 or qc.sum()==len(qc):
            print(f"  class {cl}: no q mixture", flush=True); continue
        a_z = StandardScaler().fit_transform(a)
        lab = KMeans(n_clusters=2, random_state=SEED, n_init=10).fit_predict(a_z)
        qh = np.zeros_like(qc)
        for c in np.unique(lab):
            sub = lab==c; qh[sub] = 1 if qc[sub].mean()>=0.5 else 0
        print(f"  class {cl} kmeans: qacc={accuracy_score(qc,qh):.3f} sizes={[int((lab==c).sum()) for c in np.unique(lab)]}", flush=True)
        sc = SpectralClustering(n_clusters=2, random_state=SEED, affinity="nearest_neighbors", assign_labels="kmeans")
        lab2 = sc.fit_predict(a_z)
        qh2 = np.zeros_like(qc)
        for c in np.unique(lab2):
            sub = lab2==c; qh2[sub] = 1 if qc[sub].mean()>=0.5 else 0
        print(f"  class {cl} spectral: qacc={accuracy_score(qc,qh2):.3f} sizes={[int((lab2==c).sum()) for c in np.unique(lab2)]}", flush=True)
