"""Training / evaluation helpers.

Data is pre-tensorized; two visual maps (`img_map7`, `img_map14`) are cached per
unique image and looked up per row. All runs are deterministic with fixed seeds.
"""
import numpy as np
import torch
import torch.nn.functional as F

from .model import count_to_int

QTYPE_ID = {"presence": 0, "comparison": 1, "rural_urban": 2, "count": 3}


def tokenize_row(question, w2i, max_len=24):
    ids = [w2i.get(w, w2i["<unk>"]) for w in question.split()]
    ids = ids[:max_len]
    return np.array([0] * (max_len - len(ids)) + ids, dtype=np.int64)


def answer_to_int(answer):
    a = str(answer).strip().lower()
    if a in ("no",):
        return 0
    if a in ("yes",):
        return 1
    if a in ("rural",):
        return 0
    if a in ("urban",):
        return 1
    return int(a)


def int_to_answer(t, qtype):
    if qtype == "count":
        return str(int(t))
    if qtype == "rural_urban":
        return "rural" if t == 0 else "urban"
    return "no" if t == 0 else "yes"


class Dataset:
    def __init__(self, qids, targets, qtypes, img_idx, img_map7, img_map14=None,
                 device="cpu", answers=None):
        self.qids = torch.from_numpy(qids).long().to(device)
        self.targets = torch.from_numpy(targets).long().to(device)
        self.qtypes = torch.from_numpy(qtypes).long().to(device)
        self.img_idx = torch.from_numpy(img_idx).long().to(device)
        self.img_map7 = torch.from_numpy(img_map7).float().to(device)
        self.img_map14 = torch.from_numpy(img_map14).float().to(device) if img_map14 is not None else None
        self.n = qids.shape[0]
        self._answers = list(answers) if answers is not None else [None] * self.n

    @property
    def answers(self):
        return self._answers

    def visual_for(self, idx):
        i = self.img_idx[idx]
        m14 = self.img_map14[i] if self.img_map14 is not None else None
        return self.img_map7[i], m14


def build_dataset(df, img_map7, imgid_to_idx, w2i, device="cpu", img_map14=None):
    n = len(df)
    qids = np.zeros((n, 24), dtype=np.int64)
    targets = np.zeros(n, dtype=np.int64)
    qtypes = np.zeros(n, dtype=np.int64)
    img_idx = np.zeros(n, dtype=np.int64)
    for i, (_, r) in enumerate(df.iterrows()):
        qids[i] = tokenize_row(r["question_norm"], w2i)
        targets[i] = answer_to_int(r["answer"])
        qtypes[i] = QTYPE_ID[r["qtype"]]
        img_idx[i] = imgid_to_idx[r["imgid"]]
    return Dataset(qids, targets, qtypes, img_idx, img_map7, img_map14,
                   device, df["answer"].astype(str).tolist())


def predict(model, data, idx, shuffle_row=False, seed=0):
    preds, _ = predict_scores(model, data, idx, shuffle_row=shuffle_row, seed=seed)
    return preds, np.arange(len(idx)) if not shuffle_row else np.arange(len(idx))


def predict_scores(model, data, idx, shuffle_row=False, seed=0):
    """Return (predicted_int, meta) where meta carries per-row raw scores for
    ensembling: {'yn': (2,), 'cnt': (1,) regr log1p or (n_bins) bin logits}.

    When shuffle_row=True, the image features are shuffled across rows (each row
    gets a random *other* row's image) but each row keeps its own question/answer,
    so scores are returned in the original row order.
    """
    device = next(model.parameters()).device
    model.eval()
    idx = np.asarray(idx)
    if shuffle_row:
        rng = np.random.RandomState(seed)
        use = idx[rng.permutation(len(idx))]
    else:
        use = idx
    preds = np.zeros(len(idx), dtype=np.int64)
    scores = [None] * len(idx)
    with torch.no_grad():
        for s in range(0, len(idx), 128):
            b = use[s:s + 128]
            m7, m14 = data.visual_for(b)
            out = model(data.qids[b].to(device), m7.to(device),
                        m14.to(device) if m14 is not None else None)
            yn_l = out["yn"].cpu().numpy()
            qt = data.qtypes[b].cpu().numpy()
            if "count_bin" in out:
                bin_logits = out["count_bin"].cpu().numpy()
                cnt_reg = count_to_int(out["count"]).cpu().numpy()
                top = model.n_bins - 1
                pred_bin = bin_logits.argmax(1)
                cnt = np.where(pred_bin < top, pred_bin, cnt_reg)
                cnt_score = bin_logits
            else:
                cnt_reg_v = out["count"].cpu().numpy()
                cnt = count_to_int(out["count"]).cpu().numpy()
                cnt_score = cnt_reg_v[:, None]
            yn_pred = yn_l.argmax(1)
            pred = np.where(qt == 3, cnt, yn_pred)
            for k in range(len(b)):
                preds[s + k] = pred[k]
                scores[s + k] = {"yn": yn_l[k], "cnt": cnt_score[k]}
    return preds, scores


def accuracy(preds, data, idx):
    idx = np.asarray(idx)
    return float(np.mean(preds == data.targets[idx].cpu().numpy()))


def accuracy_by_type(preds, data, idx, qtypes=None):
    idx = np.asarray(idx)
    tgt = data.targets[idx].cpu().numpy()
    qt = data.qtypes[idx].cpu().numpy()
    out = {}
    for tid, name in [(0, "presence"), (1, "comparison"), (2, "rural_urban"), (3, "count")]:
        m = qt == tid
        out[name] = float(np.mean(preds[m] == tgt[m])) if m.any() else None
    return out


def train_epoch(model, data, idx, opt, bs=128, device="cpu", seed=0, count_weight=1.0,
                only_count=False):
    model.train()
    rng = np.random.RandomState(seed)
    perm = rng.permutation(len(idx))
    loss_sum, cnt = 0.0, 0
    for s in range(0, len(perm), bs):
        b = idx[perm[s:s + bs]]
        qids = data.qids[b].to(device)
        m7, m14 = data.visual_for(b)
        out = model(qids, m7.to(device), m14.to(device) if m14 is not None else None)
        qt = data.qtypes[b]
        tgt = data.targets[b].to(device)
        loss = model_loss(out, qt, tgt, count_weight, only_count)
        opt.zero_grad()
        loss.backward()
        opt.step()
        loss_sum += float(loss.item())
        cnt += 1
    return loss_sum / cnt


def model_loss(out, qt, tgt, count_weight=1.0, only_count=False):
    qtype_ids = qt
    loss = torch.zeros((), device=tgt.device)
    if not only_count:
        mask_yn = qtype_ids != 3
        if mask_yn.any():
            loss = loss + F.cross_entropy(out["yn"][mask_yn], tgt[mask_yn])
    mask_cnt = qtype_ids == 3
    if mask_cnt.any():
        if "count_bin" in out:
            top = out["count_bin"].shape[1] - 1
            labels = tgt[mask_cnt].clamp(max=top)
            loss = loss + count_weight * F.cross_entropy(out["count_bin"][mask_cnt], labels)
            tail = tgt[mask_cnt] >= top
            if tail.any():
                t = tgt[mask_cnt][tail].float().clamp(min=1)
                loss = loss + 0.5 * F.smooth_l1_loss(out["count"][mask_cnt][tail], torch.log1p(t))
        else:
            t = tgt[mask_cnt].float().clamp(min=0)
            loss = loss + count_weight * F.smooth_l1_loss(out["count"][mask_cnt], torch.log1p(t))
    return loss


def train_model(model, tr, dev, opt, epochs=60, bs=128, device="cpu", seed=0,
                patience=10, verbose=True, count_weight=1.0, only_count=False):
    best_dev = -1.0
    best_state = None
    best_epoch = -1
    acc_best = 0.0
    for ep in range(1, epochs + 1):
        loss = train_epoch(model, tr, np.arange(tr.n), opt, bs, device, seed,
                           count_weight=count_weight, only_count=only_count)
        dev_preds, _ = predict(model, dev, np.arange(dev.n))
        dev_acc = accuracy(dev_preds, dev, np.arange(dev.n))
        if verbose and ep % 5 == 0:
            print(f"  ep {ep:03d} loss {loss:.3f} dev {dev_acc:.4f}")
        if dev_acc > best_dev:
            best_dev = dev_acc
            acc_best = dev_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            best_epoch = ep
        if ep - best_epoch >= patience:
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    return best_dev, best_epoch