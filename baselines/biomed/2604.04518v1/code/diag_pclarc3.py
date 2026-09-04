import os, numpy as np, torch
from config import SEED, WORKSPACE
from models import make_resnet18
from corrections import load_split, split_root, predict, compute_group_metrics, extract_features, compute_cav, ProjectionLayer, CorrectedModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

dataset, poison = "squares", "symmetric"
root = split_root(dataset, poison)
train, val, test = load_split(root)
m = make_resnet18(2, SEED)
m.load_state_dict(torch.load(os.path.join(WORKSPACE, "models", "students", f"{dataset}_{poison}", "best.pt"), weights_only=False))
m.eval()
t = test["targets"].numpy(); g = test["groups"].numpy(); q = g % 2
act = extract_features(m, test["images"], 6).numpy()  # [N, 8192]

def probe(X, labels):
    Xtr, Xte, ytr, yte = train_test_split(X, labels, test_size=0.5, stratify=labels, random_state=0)
    clf = LogisticRegression(max_iter=2000); clf.fit(Xtr, ytr)
    return clf.score(Xte, yte)

# true confounder direction from probe on train
tr_act = extract_features(m, train["images"], 6).numpy()
tr_q = (train["groups"].numpy() % 2)
clf = LogisticRegression(max_iter=2000); clf.fit(tr_act, tr_q)
wdir = clf.coef_[0]; wdir /= (np.linalg.norm(wdir)+1e-12)
wdir = torch.from_numpy(wdir).float()

# project out wdir exactly
def proj_out(X, d):
    Xt = torch.from_numpy(X).float()
    P = d.reshape(1,-1) * ((Xt @ d).unsqueeze(1))
    return (Xt - P).numpy()

actp = proj_out(act, wdir)
print(f"remove TRUE conf dir: causal={probe(actp,t):.3f} conf={probe(actp,q):.3f}")

# CAV over both classes (split by confounder q only)
def cav_both_classes(seed_mode):
    aq0 = tr_act[tr_q==0]; aq1 = tr_act[tr_q==1]
    if seed_mode == "pca":
        xc = aq1 - aq1.mean(0, keepdim=True)
        U, S, _ = torch.linalg.svd(torch.from_numpy(xc).float().T, full_matrices=False)
        vc = U[:,0].numpy()
    else:
        from sklearn.svm import LinearSVC
        X = np.concatenate([aq0, aq1]); yv = np.array([0]*len(aq0)+[1]*len(aq1))
        s = LinearSVC(C=1.0, max_iter=5000); s.fit(X, yv)
        vc = s.coef_[0]
    vc = vc/(np.linalg.norm(vc)+1e-12)
    align = abs(float(np.dot(vc, wdir.numpy())))
    ap = proj_out(act, torch.from_numpy(vc).float())
    return align, probe(ap,t), probe(ap,q)

for mode in ("pca","svm"):
    align, c, cf = cav_both_classes(mode)
    print(f"CAV over BOTH classes mode={mode}: align={align:.3f} causal={c:.3f} conf={cf:.3f}")
print("DONE")
