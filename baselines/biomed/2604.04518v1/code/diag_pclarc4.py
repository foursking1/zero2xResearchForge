import os, numpy as np, torch
from config import SEED, WORKSPACE
from models import make_resnet18
from corrections import load_split, split_root, extract_features
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

dataset, poison = "squares", "symmetric"
root = split_root(dataset, poison)
train, val, test = load_split(root)
m = make_resnet18(2, SEED)
m.load_state_dict(torch.load(os.path.join(WORKSPACE, "models", "students", f"{dataset}_{poison}", "best.pt"), weights_only=False))
m.eval()
t = test["targets"].numpy(); q = (test["groups"].numpy() % 2)

def probe(X, labels):
    Xtr, Xte, ytr, yte = train_test_split(X, labels, test_size=0.5, stratify=labels, random_state=0)
    clf = LogisticRegression(max_iter=2000); clf.fit(Xtr, ytr)
    return clf.score(Xte, yte)

def proj_out(X, d):
    Xt = torch.from_numpy(X).float()
    d = torch.from_numpy(d).float(); P = d.reshape(1,-1) * ((Xt @ d).unsqueeze(1))
    return (Xt - P).numpy()

for layer in (6, 12):
    tr_act = extract_features(m, train["images"], layer).numpy()
    tr_q = (train["groups"].numpy() % 2)
    clf = LogisticRegression(max_iter=2000); clf.fit(tr_act, tr_q)
    wdir = clf.coef_[0]; wdir /= (np.linalg.norm(wdir)+1e-12)
    act = extract_features(m, test["images"], layer).numpy()
    actp = proj_out(act, wdir)
    # remove top-k probe directions iteratively (rank-k suppression ceiling)
    X = tr_act; y = tr_q
    dirs = []
    for k in range(1, 6):
        clf = LogisticRegression(max_iter=2000); clf.fit(X, y)
        d = clf.coef_[0]; d /= (np.linalg.norm(d)+1e-12)
        dirs.append(d)
        X = proj_out(X, d)
    actp_k = act
    for d in dirs:
        actp_k = proj_out(actp_k, d)
    print(f"layer {layer}: orig causal={probe(act,t):.3f} conf={probe(act,q):.3f}")
    print(f"  remove 1 dir: causal={probe(actp,t):.3f} conf={probe(actp,q):.3f}")
    print(f"  remove 5 dirs: causal={probe(actp_k,t):.3f} conf={probe(actp_k,q):.3f}")
print("DONE")
