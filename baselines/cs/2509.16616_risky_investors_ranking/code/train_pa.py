"""Train PA-RiskRanker and Rankformer baseline.

PA-RiskRanker (modes):
  seq : transformer encoder over each ranking-group's traders (self-cross-trader
        attention); profit-aware BCE (+ listnet mix) -- the paper's construction.
  ft  : FT-Transformer-style feature-token self-attention per trader (tabular
        adaptation of the cross-trader transformer); profit-aware BCE + profit-
        proxy aux regression. Ranking by the BCE logit head.

Rankformer baseline: seq mode WITHOUT cross-trader attention, ListNet loss only.

Usage:
  python3 train_pa.py --model pabce --dataset creditcard --fold 1 --mode ft --epochs 60
  python3 train_pa.py --model pabce --dataset jobprofit --fold 2 --mode seq --mix 0.5
  python3 train_pa.py --model rankformer --dataset creditcard --fold 1
"""
from __future__ import annotations
import os, sys, json, time, argparse, numpy as np, torch
from sklearn.metrics import roc_auc_score
from torch.optim.lr_scheduler import CosineAnnealingLR
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare_fold, topk_metrics, pick_threshold, ROOT
from model import PARiskRanker, pabce_loss, listnet_loss, aux_huber_loss

RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)


def tgt_full(d):
    imp = d["i_train"]
    t = np.arcsinh(imp).astype(np.float32)
    return (t - t.mean()) / (t.std() + 1e-9)


def load_fold(dataset, fold, device):
    d = prepare_fold(dataset, fold)
    dev = torch.device(device)
    groups = d["groups"].astype(np.int64)
    idx_map = np.full(int(d["idx_train"].max()) + 1, -1)
    idx_map[d["idx_train"]] = np.arange(len(d["idx_train"]))
    groups = idx_map[groups]
    Xg_t = torch.tensor(d["X_train"][groups], dtype=torch.float32, device=dev)
    yg_t = torch.tensor(d["y_train"][groups].astype(np.float32), dtype=torch.float32, device=dev)
    pos_imp = d["i_train"][groups][d["y_train"][groups] > 0.5]
    mean_pos = float(pos_imp.mean()) + 1e-9
    impact_d = torch.tensor(d["i_train"][groups] / mean_pos, dtype=torch.float32, device=dev)
    tgt_d = torch.tensor(tgt_full(d)[groups], dtype=torch.float32, device=dev)
    Xp = torch.tensor(d["X_train"], dtype=torch.float32, device=dev)
    yp = torch.tensor(d["y_train"].astype(np.float32), dtype=torch.float32, device=dev)
    imp_mean_p = float(d["i_train"][d["y_train"] > 0.5].mean()) + 1e-9
    wimp = torch.tensor(d["i_train"] / imp_mean_p, dtype=torch.float32, device=dev)
    tgtp = torch.tensor(tgt_full(d), dtype=torch.float32, device=dev)
    return d, dev, Xg_t, yg_t, impact_d, tgt_d, Xp, yp, wimp, tgtp


def val_scores(model, Xv, rank_by_aux=False):
    model.eval()
    with torch.no_grad():
        s = []
        for i in range(0, len(Xv), 4096):
            b = Xv[i:i + 4096]
            out = model(b.unsqueeze(1))
            if isinstance(out, tuple):
                _, auxo = out
                sc = auxo if rank_by_aux else out[0]
            else:
                sc = out
            s.append(sc.reshape(len(b), -1)[:, -1].numpy())
        return np.concatenate(s)


def context_scores(model, X, rng_seed=0, group=100, n_draws=3):
    model.eval()
    n = len(X)
    rng = np.random.RandomState(rng_seed)
    Xt = torch.tensor(X, dtype=torch.float32)
    with torch.no_grad():
        Em = torch.cat([model.tokens(Xt[i:i + 4096].unsqueeze(1)) for i in range(0, n, 4096)], 0)
    scores = np.zeros(n, dtype=np.float64)
    with torch.no_grad():
        for _ in range(n_draws):
            peers = np.stack([np.concatenate([[i], rng.choice(np.delete(np.arange(n), i),
                          size=group - 1, replace=False)]) for i in range(n)])
            rel = np.zeros(n)
            for b in range(0, n, 256):
                toks = Em[peers[b:b + 256]]
                h = model.encoder(toks)
                if model.mode == "ft":
                    logits = model.head(h[:, 0]).squeeze(-1)
                else:
                    logits = model.head(h).squeeze(-1)
                if model.head_aux is not None:
                    logits = model.head_aux(h[:, 0] if model.mode == "ft" else h).squeeze(-1)
                rel[b:b + 256] = (logits[:, 0] - logits.mean(-1)).numpy()
            scores += rel
    return scores / n_draws


def run(model_name, dataset, fold, epochs=40, batch=32, pos_lambda=20.0,
        aux=1.0, device="cpu", seed=0, threads=4, lr=1e-3, wd=0.01,
        dropout=0.05, w_cap=3.0, tag="", rank_by_aux=False, context=False,
        mix=0.0, mode="seq", d_embed=128, n_layer=2, clip=5.0, pretrain_aux=0):
    torch.set_num_threads(threads)
    torch.manual_seed(seed); np.random.seed(seed)
    d, dev, Xg_t, yg_t, impact_d, tgt_d, Xp, yp, wimp, tgtp = load_fold(dataset, fold, device)
    nG = Xg_t.shape[0]
    model = PARiskRanker(Xg_t.shape[-1], d_embed=d_embed, n_layer=n_layer,
                         cross=(model_name == "pabce"), dropout=dropout,
                         aux=(model_name == "pabce" and aux > 0), mode=mode).to(dev)

    def loss_pbce(logits, y, impw, tgt, mix_):
        out = logits
        L = pabce_loss(out, y, impw, pos_lambda=pos_lambda, w_cap=w_cap)
        if mix_ > 0:
            L = L + mix_ * listnet_loss(out, y)
        return L

    def make_iter(flat):
        if flat:
            def it(b):
                perm = torch.randperm(len(Xp))
                n = len(Xp)
                for i in range(0, n, b):
                    ids = perm[i:i + b]
                    if len(ids) < 2:
                        break
                    yield Xp[ids], yp[ids], wimp[ids], tgtp[ids]
        else:
            def it(b):
                perm = torch.randperm(nG)
                for i in range(0, nG, b):
                    ids = perm[i:i + b]
                    if len(ids) < 2:
                        break
                    yield Xg_t[ids], yg_t[ids], impact_d[ids], tgt_d[ids]
        return it

    flat = (mode == "ft")
    n_steps = len(Xp) if flat else nG
    batch_iter = make_iter(flat)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    sched = CosineAnnealingLR(opt, T_max=epochs)
    Xv = torch.tensor(d["X_val"], dtype=torch.float32, device=dev)
    if pretrain_aux > 0 and flat is False and model.head_aux is not None:
        optp = torch.optim.AdamW(model.parameters(), lr=lr * 0.5, weight_decay=wd)
        sp = CosineAnnealingLR(optp, T_max=pretrain_aux)
        print(f"  .. pretrain-aux {pretrain_aux} epochs", flush=True)
        model.train()
        for ep in range(1, pretrain_aux + 1):
            perm = torch.randperm(nG)
            for i in range(0, nG, batch):
                ids = perm[i:i + batch]
                if len(ids) < 2:
                    break
                lg, auxo = model(Xg_t[ids])
                L = aux * aux_huber_loss(auxo, tgt_d[ids])
                optp.zero_grad(); L.backward(); optp.step()
            sp.step()
            if ep % 10 == 0:
                sv = val_scores(model, Xv, False)
                print(f"  .. pre{ep} valAUC={roc_auc_score(d['y_val'], sv):.4f}", flush=True)
    best_score, best_state, pat, best_ep = -1e9, None, 0, 0
    best_auc = best_f1 = 0.0
    t0 = time.time()
    for ep in range(1, epochs + 1):
        model.train()
        tot = 0.0
        for xb, yb, impb, tgtb in batch_iter(batch):
            out = model(xb)
            if isinstance(out, tuple):
                logits, auxo = out
            else:
                logits, auxo = out, None
            L = loss_pbce(logits, yb, impb, tgtb, mix if not flat else 0.0)
            if auxo is not None:
                L = L + aux * aux_huber_loss(auxo, tgtb)
            opt.zero_grad(); L.backward()
            if clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
            opt.step()
            tot += float(L.item())
        sched.step()
        sv = val_scores(model, Xv, rank_by_aux)
        auc_v = float(roc_auc_score(d["y_val"], sv))
        f1_v = topk_metrics(d["y_val"], sv, d["i_val"])["f1"]
        score = f1_v * 1000 + auc_v
        if score > best_score:
            best_score, best_ep, pat = score, ep, 0
            best_auc, best_f1 = auc_v, f1_v
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            pat += 1
        if ep % 5 == 0 or ep == 1:
            print(f"  [{dataset}/{model_name}:{mode} fold{fold} s{seed}] ep{ep} "
                  f"loss={tot / max(1, n_steps // batch):.4f} valAUC={auc_v:.4f} "
                  f"valF1={f1_v:.4f} ({time.time() - t0:.0f}s)", flush=True)
        if pat >= 12 and ep >= 20:
            break
    model.load_state_dict(best_state)
    model.eval()
    Xt = torch.tensor(d["X_test"], dtype=torch.float32, device=dev)
    if context:
        try:
            st_ctx = context_scores(model, d["X_test"], rng_seed=seed + 100 * fold)
            wp_ctx = topk_metrics(d["y_test"], st_ctx, d["i_test"])
            print(f"  : contextual F1={wp_ctx['f1']:.4f} loss={wp_ctx['financial_loss']:.2f} "
                  f"auc={roc_auc_score(d['y_test'], st_ctx):.4f}", flush=True)
        except Exception as e:
            print("  : context failed:", e, flush=True)
    st = val_scores(model, Xt, rank_by_aux)
    wp = topk_metrics(d["y_test"], st, d["i_test"])
    sv = val_scores(model, Xv, rank_by_aux)
    thr = pick_threshold(d["y_val"], sv)
    auc = float(roc_auc_score(d["y_test"], st))
    scoredir = os.path.join(RESULTS, "scores"); os.makedirs(scoredir, exist_ok=True)
    np.save(os.path.join(scoredir, f"{model_name.replace(':','_')}_{dataset}_fold{fold}_s{seed}.npy"),
            st.astype(np.float32))
    print(f"== {dataset}/{model_name}:{mode} fold{fold} s{seed} best_ep={best_ep} "
          f"(valAUC={best_auc:.4f} valF1={best_f1:.4f}) with_prior F1={wp['f1']:.4f} "
          f"loss={wp['financial_loss']:.2f} P={wp['precision']:.4f} S={wp['sensitivity']:.4f} "
          f"Sp={wp['specificity']:.4f} auc={auc:.4f} thr={thr:.3f}", flush=True)
    return {"model": f"{model_name}:{mode}", "dataset": dataset, "fold": fold, "seed": seed,
            **{k: wp[k] for k in ("f1", "financial_loss", "precision", "sensitivity", "specificity")},
            "auc": auc, "threshold": thr, "best_epoch": best_ep, "val_auc": float(best_auc),
            "val_f1": float(best_f1), "seconds": round(time.time() - t0, 1)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=["pabce", "rankformer"], required=True)
    ap.add_argument("--dataset", choices=["creditcard", "jobprofit"], required=True)
    ap.add_argument("--fold", type=int, choices=[1, 2, 3], required=True)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--pos-lambda", type=float, default=20.0)
    ap.add_argument("--aux", type=float, default=1.0)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=0.01)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--w-cap", type=float, default=3.0)
    ap.add_argument("--tag", default="")
    ap.add_argument("--rank-by-aux", action="store_true")
    ap.add_argument("--context", action="store_true")
    ap.add_argument("--mix", type=float, default=0.0)
    ap.add_argument("--mode", choices=["seq", "ft"], default="seq")
    ap.add_argument("--d-embed", type=int, default=128)
    ap.add_argument("--n-layer", type=int, default=2)
    ap.add_argument("--clip", type=float, default=5.0)
    ap.add_argument("--pretrain-aux", type=int, default=0)
    a = ap.parse_args()
    r = run(a.model, a.dataset, a.fold, a.epochs, a.batch, a.pos_lambda, a.aux, a.device,
            a.seed, a.threads, a.lr, a.wd, a.dropout, a.w_cap, a.tag, a.rank_by_aux,
            a.context, a.mix, a.mode, a.d_embed, a.n_layer, a.clip, a.pretrain_aux)
    out = os.path.join(RESULTS, f"{a.model}_{a.dataset}_fold{a.fold}{a.tag}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(r, open(out, "w"), indent=2)
    print("saved", out)