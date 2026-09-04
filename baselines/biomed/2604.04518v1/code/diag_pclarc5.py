import os, numpy as np, torch
from config import SEED, WORKSPACE
from models import make_resnet18
from corrections import load_split, split_root, extract_features, compute_group_metrics, predict, ProjectionLayer, CorrectedModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

dataset, poison = "squares", "symmetric"
root = split_root(dataset, poison)
train, val, test = load_split(root)
m = make_resnet18(2, SEED)
m.load_state_dict(torch.load(os.path.join(WORKSPACE, "models", "students", f"{dataset}_{poison}", "best.pt"), weights_only=False))
m.eval()
t = test["targets"].numpy(); g = test["groups"].numpy(); q = g % 2

def probe(X, labels):
    Xtr, Xte, ytr, yte = train_test_split(X, labels, test_size=0.5, stratify=labels, random_state=0)
    clf = LogisticRegression(max_iter=2000); clf.fit(Xtr, ytr)
    return clf.score(Xte, yte)

def project_act(X, d):
    Xt = torch.from_numpy(X).float()
    P = d.reshape(1,-1) * ((Xt @ d).unsqueeze(1))
    return (Xt - P)

for layer in (6, 12):
    tr_act = extract_features(m, train["images"], layer).numpy()
    tr_t = train["targets"].numpy(); tr_q = (train["groups"].numpy() % 2)
    act = extract_features(m, test["images"], layer).numpy()
    # --- CAV on class-1 only (current impl) ---
    m1 = tr_t == 1
    aq0 = tr_act[m1 & (tr_q==0)]; aq1 = tr_act[m1 & (tr_q==1)]
    xc = aq1 - aq1.mean(0, keepdims=True)
    U,S,_ = torch.linalg.svd(torch.from_numpy(xc).float().T, full_matrices=False)
    vc1 = U[:,0].numpy(); vc1/= (np.linalg.norm(vc1)+1e-12)
    ap1 = project_act(act, torch.from_numpy(vc1).float())
    # --- CAV on both classes ---
    aq0b = tr_act[tr_q==0]; aq1b = tr_act[tr_q==1]
    xcb = aq1b - aq1b.mean(0, keepdims=True)
    U,S,_ = torch.linalg.svd(torch.from_numpy(xcb).float().T, full_matrices=False)
    vcb = U[:,0].numpy(); vcb/= (np.linalg.norm(vcb)+1e-12)
    apb = project_act(act, torch.from_numpy(vcb).float())
    # --- SVM CAV on both classes ---
    Xs = np.concatenate([aq0b, aq1b]); ys = np.array([0]*len(aq0b)+[1]*len(aq1b))
    s = LinearSVC(C=1.0, max_iter=5000); s.fit(Xs, ys)
    vs = s.coef_[0]; vs/= (np.linalg.norm(vs)+1e-12)
    aps = project_act(act, torch.from_numpy(vs).float())
    print(f"layer {layer} (conf-present samples: class1={len(aq1)}, both={len(aq1b)})")
    print(f"  class1 PCAV : conf={probe(ap1.numpy(),q):.3f} causal={probe(ap1.numpy(),t):.3f}")
    print(f"  both  PCAV : conf={probe(apb.numpy(),q):.3f} causal={probe(apb.numpy(),t):.3f}")
    print(f"  both  SVM  : conf={probe(aps.numpy(),q):.3f} causal={probe(aps.numpy(),t):.3f}")
    # end-to-end with projected model (no fine-tune) using both PCAV
    zsup = torch.from_numpy(aq0b.mean(0, keepdims=True)).float()
    cm = CorrectedModel(m, layer, ProjectionLayer(torch.from_numpy(vcb).float(), zsup))
    emp, aga, wga, gacc = compute_group_metrics(predict(cm, test["images"]).numpy(), t, g)
    print(f"  both-PCAV projected-no-finetune: emp={emp:.3f} aga={aga:.3f} wga={wga:.3f}")
print("DONE")
