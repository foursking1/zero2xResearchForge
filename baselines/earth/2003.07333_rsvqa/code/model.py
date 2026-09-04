"""VQA model: LSTM question encoder + CNN visual features + attention fusion +
per-task heads, with two count-head variants:
  - "regress": direct regression on log1p(global attended features)
  - "density": 14x14 question-conditional density sum (counting by summing
    per-position object-density), trained with smooth L1 on log1p.

All trainable parts are trained on the frozen training split; the CNN/ViT backbone
stays frozen and features are precomputed once (offline), matching the RSVQA design
of CNN features + LSTM question encoding.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class QuestionEncoder(nn.Module):
    def __init__(self, vocab_size, embed_dim=256, hidden=256, num_layers=1, dropout=0.1):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden, num_layers=num_layers,
                            batch_first=True, dropout=dropout if num_layers > 1 else 0.0)
        self.out = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, hidden))

    def forward(self, x):
        _, (h, _) = self.lstm(self.embed(x))
        return self.out(h[-1])


class RSVQAModel(nn.Module):
    def __init__(self, vocab_size, feat_dim=512, q_dim=256, hidden=512,
                 attn_heads=2, dropout=0.2, count_head="regress",
                 density_dim=256, count_weight=1.0, n_bins=41):
        super().__init__()
        self.count_head = count_head
        self.count_weight = count_weight
        self.n_bins = n_bins
        self.q_enc = QuestionEncoder(vocab_size, q_dim, q_dim)
        self.q_to_att = nn.Linear(q_dim, feat_dim, bias=False)
        self.attn = nn.MultiheadAttention(feat_dim, attn_heads, dropout=dropout, batch_first=True)
        self.vis_proj = nn.Sequential(nn.Linear(feat_dim, hidden), nn.ReLU(), nn.Dropout(dropout))
        self.att_proj = nn.Sequential(nn.Linear(feat_dim, hidden), nn.ReLU(), nn.Dropout(dropout))
        self.fusion = nn.Sequential(nn.Linear(hidden + hidden + q_dim, hidden), nn.ReLU(),
                                    nn.Dropout(dropout))
        self.head_yn = nn.Linear(hidden, 2)
        if count_head == "density":
            self.gate = nn.Sequential(nn.Linear(q_dim, density_dim), nn.Sigmoid())
            self.dens = nn.Conv2d(density_dim, 1, 1)
        elif count_head == "hybrid":
            self.head_count = nn.Sequential(nn.Linear(hidden, 256), nn.ReLU(),
                                            nn.Dropout(dropout), nn.Linear(256, 1))
            self.head_count_bin = nn.Linear(hidden, n_bins)  # bins 0..n_bins-2, last=">=n_bins-1"
        else:
            self.head_count = nn.Sequential(nn.Linear(hidden, 256), nn.ReLU(),
                                            nn.Dropout(dropout), nn.Linear(256, 1))

    def forward(self, qids, img_map7, img_map14=None):
        q = self.q_enc(qids)                              # (B, q_dim)
        B, C, H, W = img_map7.shape
        v = img_map7.flatten(2).transpose(1, 2)           # (B, K, C)
        query = self.q_to_att(q).unsqueeze(1)             # (B,1,C)
        att, _ = self.attn(query, v, v)
        att = att.squeeze(1)                              # (B, C)
        vg = F.adaptive_avg_pool2d(img_map7, 1).flatten(1)
        fused = torch.cat([self.vis_proj(vg), self.att_proj(att), q], dim=1)
        h = self.fusion(fused)
        yn = self.head_yn(h)

        if self.count_head == "density":
            m = img_map14 if img_map14 is not None else F.interpolate(
                img_map7, scale_factor=2.0, mode="bilinear", align_corners=False)
            g = self.gate(q).view(B, -1, 1, 1)           # (B,C,1,1)
            d = self.dens(m * g).relu()                  # (B,1,H,W)
            cnt = torch.log1p(d.flatten(1).sum(1))       # log1p(sum density)
        elif self.count_head == "hybrid":
            cnt = self.head_count(h).squeeze(-1)
            cnt_bin = self.head_count_bin(h)
        else:
            cnt = self.head_count(h).squeeze(-1)
        out = {"yn": yn, "count": cnt}
        if self.count_head == "hybrid":
            out["count_bin"] = cnt_bin
        return out


def count_to_int(pred_log1p):
    return torch.clamp((torch.expm1(pred_log1p) + 0.5).long(), min=0)


def binary_loss(out, qtypes, targets):
    mask = qtypes != 3
    if mask.any():
        return F.cross_entropy(out["yn"][mask], targets[mask])
    return torch.zeros((), device=targets.device)


def count_loss(out, qtypes, targets):
    mask = qtypes == 3
    if mask.any():
        t = targets[mask].float().clamp(min=0)
        return F.smooth_l1_loss(out["count"][mask], torch.log1p(t))
    return torch.zeros((), device=targets.device)