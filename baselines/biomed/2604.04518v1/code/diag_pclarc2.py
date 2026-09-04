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

def probe(act, labels):
    Xtr, Xte, ytr, yte = train_test_split(act.numpy(), labels, test_size=0.5, stratify=labels, random_state=0)
    clf = LogisticRegression(max_iter=2000)
    clf.fit(Xtr, ytr)
    return clf.score(Xte, yte)

for mode in ("pca", "svm"):
    act = extract_features(m, test["images"], 6)
    vc, zsup = compute_cav(m, train, 6, target_class=1, mode=mode)
    # alignment of vc with the logistic confounder direction
    Xtr, _, ytr, _ = train_test_split(act.numpy(), q, test_size=0.5, stratify=q, random_state=0)
    clf = LogisticRegression(max_iter=2000); clf.fit(Xtr, ytr)
    wdir = clf.coef_[0]; wdir = wdir/(np.linalg.norm(wdir)+1e-12)
    align = abs(float(np.dot(vc.numpy(), wdir)))
    proj = ProjectionLayer(vc, zsup)
    actp = proj(act)
    print(f"mode={mode}: |vc·w_dir|={align:.3f}  after proj: causal={probe(actp,t):.3f} conf={probe(actp,q):.3f}")
    cm = CorrectedModel(m, 6, proj)
    emp, aga, wga, gacc = compute_group_metrics(predict(cm, test["images"]).numpy(), t, g)
    print(f"  projected-no-finetune: emp={emp:.3f} aga={aga:.3f} wga={wga:.3f}")
print("DONE")
