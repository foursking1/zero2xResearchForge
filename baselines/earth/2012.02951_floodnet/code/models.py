"""VQA models for the FloodNet reproduction.

Two fusion architectures follow the paper's recipe (CNN image features + LSTM
question features + bilinear fusion):

  * ConcatMLP :: concat(global-image feats, question-embedding) -> MLP
  * MFBCoAtt  :: factorized-bilinear (MFB-style) fusion, where the visual
                 feature is produced by question-conditioned spatial attention
                 and the question is re-attended given the attended region
                 ("co-attention").

The final classifier is shared across question types and masked per question
type to that type's allowed answer set (Condition -> {flooded, non flooded,
flooded,non flooded}; Yes/No -> {Yes,No}; counting -> integer answers).
"""
import re
import unicodedata

import torch
import torch.nn as nn
import torch.nn.functional as F


# --------------------------------------------------------------------------
# text utilities
# --------------------------------------------------------------------------
def tokenize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return [t for t in re.split(r"[^a-z0-9]+", text) if t]


def build_vocab(questions):
    words = set()
    for q in questions:
        words.update(tokenize(q))
    vocab = ["<PAD>", "<UNK>"] + sorted(words)
    return {w: i for i, w in enumerate(vocab)}


def encode(text, vocab):
    return [vocab[t] if t in vocab else vocab["<UNK>"] for t in tokenize(text)]


def pad_sequences(batch, pad=0):
    T = max(len(s) for s in batch)
    out = torch.full((len(batch), T), pad, dtype=torch.long)
    for i, s in enumerate(batch):
        out[i, : len(s)] = torch.tensor(s, dtype=torch.long)
    return out


# --------------------------------------------------------------------------
# modules
# --------------------------------------------------------------------------
class TextEncoder(nn.Module):
    """Token embedding + Bi-LSTM -> concatenated last hidden states (2*hidden)."""

    def __init__(self, vocab_size, emb_dim=128, hidden=128):
        super().__init__()
        self.emb = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(emb_dim, hidden, batch_first=True, bidirectional=True)

    def forward(self, toks, return_all=False):
        x = self.emb(toks)
        out, _ = self.lstm(x)            # B,T,2H
        last = out[:, -1]                # B,2H
        if return_all:
            return last, out
        return last


class SpatialAttention(nn.Module):
    """Question-conditioned attention over a spatial feature map (V-attention)."""

    def __init__(self, img_dim, q_dim, hid=256):
        super().__init__()
        self.Ws = nn.Linear(img_dim, hid)
        self.Wq = nn.Linear(q_dim, hid)
        self.Wa = nn.Linear(hid, 1)

    def forward(self, s, q):
        B, C, H, W = s.shape
        sp = s.view(B, C, H * W).permute(0, 2, 1)                # B,N,C
        e = torch.tanh(self.Ws(sp) + self.Wq(q).unsqueeze(1))   # B,N,hid
        a = torch.softmax(self.Wa(e).squeeze(-1), dim=1)        # B,N
        v = torch.bmm(a.unsqueeze(1), sp).squeeze(1)            # B,C
        return v, a


class TextConditionedAttention(nn.Module):
    """Image-conditioned attention over question tokens (co-attention)."""

    def __init__(self, hid, img_dim, q_dim):
        super().__init__()
        self.Wv = nn.Linear(img_dim, hid)
        self.Wh = nn.Linear(q_dim, hid)
        self.Wa = nn.Linear(hid, 1)

    def forward(self, h, v, mask):
        e = torch.tanh(self.Wv(v).unsqueeze(1) + self.Wh(h))    # B,T,hid
        e = self.Wa(e).squeeze(-1) + (1 - mask) * -1e9
        a = torch.softmax(e, dim=1)
        return torch.bmm(a.unsqueeze(1), h).squeeze(1), a


class MFBFusion(nn.Module):
    """Factorized bilinear pooling: element-wise interaction + chunk sum-pool."""

    def __init__(self, v_dim, q_dim, out_dim=512, k=2):
        super().__init__()
        self.Pv = nn.Linear(v_dim, out_dim * k, bias=False)
        self.Pq = nn.Linear(q_dim, out_dim * k, bias=False)
        self.k = k
        self.out_dim = out_dim

    def forward(self, v, q):
        z = self.Pv(v) * self.Pq(q)
        z = z.view(z.size(0), self.out_dim, self.k).sum(dim=2)
        return F.normalize(z, p=2, dim=1)


class AnswerHead(nn.Module):
    def __init__(self, in_dim, n_answers):
        super().__init__()
        global_branch = [
            nn.Linear(in_dim, in_dim), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(in_dim, n_answers),
        ]
        self.net = nn.Sequential(*global_branch)

    def forward(self, x):
        return self.net(x)


class ConcatMLP(nn.Module):
    """Baseline fusion: concat(global image feats, question embedding) -> MLP."""

    def __init__(self, img_dim, q_dim, n_answers):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(img_dim + q_dim, 512), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(512, 256), nn.ReLU(), nn.Dropout(0.2),
        )
        self.head = AnswerHead(256, n_answers)

    def forward(self, img, sp, q):
        x = torch.cat([img, q], dim=1)
        return self.head(self.net(x))


class MFBCoAtt(nn.Module):
    """MFB fusion with question-conditioned spatial co-attention."""

    def __init__(self, img_dim, q_dim, n_answers, fusion_out=512, spatial_dim=512):
        super().__init__()
        self.att = SpatialAttention(spatial_dim, q_dim, hid=256)
        self.to_text = TextConditionedAttention(hid=256, img_dim=spatial_dim, q_dim=q_dim)
        self.mfb = MFBFusion(spatial_dim, q_dim, out_dim=fusion_out, k=2)
        self.g_v = nn.Linear(img_dim, 128)
        self.g_q = nn.Linear(q_dim, 128)
        self.drop = nn.Dropout(0.1)
        self.head = AnswerHead(fusion_out + 256, n_answers)

    def forward(self, img, sp, h_all, q_last, mask):
        v, _ = self.att(sp, q_last)                 # B,img_dim   (attended visual)
        v_t, _ = self.to_text(h_all, v, mask)       # B,q_dim     (co-attended text)
        z = self.mfb(v, v_t)                        # B,fusion_out
        shortcut = torch.cat([self.g_v(img), self.g_q(q_last)], dim=1)  # B,256
        z = torch.cat([z, shortcut], dim=1)
        return self.head(self.drop(z))


class JointNet(nn.Module):
    """Text encoder + fusion network + shared masked classifier."""

    def __init__(self, vocab, n_answers, img_dim, arch="concat",
                 answer_masks=None):
        super().__init__()
        self.vocab = vocab
        self.text = TextEncoder(len(vocab), emb_dim=128, hidden=128)  # q_dim=256
        q_dim = 256
        self.arch = arch
        self.img_dim = img_dim
        if arch == "concat":
            self.fusion = ConcatMLP(img_dim, q_dim, n_answers)
        elif arch == "mfb":
            self.fusion = MFBCoAtt(img_dim, q_dim, n_answers)
        else:
            raise ValueError(arch)
        # answer masks: dict type -> torch LongTensor of allowed answer indices
        self.register_buffer("mask_cache", None)
        self.answer_masks = answer_masks  # built at train time from vocab layout

    def set_answer_masks(self, masks):
        self.answer_masks = masks

    def _masked_logits(self, logits, qtypes):
        out = logits.clone()
        for i, qt in enumerate(qtypes):
            allowed = self.answer_masks.get(qt)
            if allowed is not None:
                keep = torch.full_like(logits[i], -1e9)
                keep[allowed] = logits[i][allowed]
                out[i] = keep
        return out

    def forward(self, img, sp, q_toks, qtypes):
        if self.arch == "concat":
            q = self.text(q_toks)
            logits = self.fusion(img, sp, q)
        else:
            q_last, h_all = self.text(q_toks, return_all=True)
            mask = (q_toks != 0).float()
            logits = self.fusion(img, sp, h_all, q_last, mask)
        if self.answer_masks:
            logits = self._masked_logits(logits, qtypes)
        return logits