"""
SATIN (2304.11619) - SAT-4 zero-shot classification with OpenCLIP.

Frozen data only for evaluation (test split from satin_arrays.npz). The CLIP
model weights are downloaded from HuggingFace at first run (model parameters,
NOT evaluation data). Model size is reported; the paper's anchor 0.54 uses
OpenCLIP ViT-G/14 (LAION-2B), a much larger model.

Prompts follow the SATIN paper's zero-shot protocol (template ensemble over
class names). Reports overall accuracy + per-class accuracy + 95% Wilson CI.

Outputs: ../results/satin_clip_zeroshot_metrics.json
"""
import os, json
import numpy as np
import torch
import open_clip

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("TORCH_NUM_THREADS", "2")
torch.set_num_threads(2)

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

CLASS_NAMES = ["barren land", "trees", "grassland", "buildings"]

# Templates (ensemble). "a photo of {}" is the OpenAI CLIP default;
# satellite-specific templates reflect the remote-sensing domain.
TEMPLATES = [
    "a photo of {}.",
    "a satellite photo of {}.",
    "an aerial view of {}.",
    "satellite imagery of {}.",
    "a top-down view of {}.",
]

MODEL_NAME = "ViT-B-32"
PRETRAINED = "laion2b_s34b_b79k"
# If a subset_size is set, evaluate on a fixed random subset of the test split
# (reproducible via seed) and report a 95% CI. 0 = use full test split.
SUBSET_SIZE = 0  # full 20k test split
RNG_SEED = 20260817
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def wilson_ci(p, n, z=1.96):
    if n == 0:
        return 0.0, 1.0
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return centre - half, centre + half


def main():
    d = np.load(os.path.join(RESULTS, "satin_arrays.npz"), allow_pickle=False)
    X_te = d["X_test"]  # N,28,28,3 uint8
    y_te = d["y_test"]

    rng = np.random.RandomState(RNG_SEED)
    if SUBSET_SIZE and SUBSET_SIZE < len(y_te):
        sel = rng.choice(len(y_te), size=SUBSET_SIZE, replace=False)
        X_eval, y_eval = X_te[sel], y_te[sel]
        subset = True
    else:
        X_eval, y_eval = X_te, y_te
        subset = False

    model, _, preprocess = open_clip.create_model_and_transforms(
        MODEL_NAME, pretrained=PRETRAINED
    )
    model = model.to(DEVICE)
    model.eval()
    tokenizer = open_clip.get_tokenizer(MODEL_NAME)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"model={MODEL_NAME} pretrained={PRETRAINED} params={n_params/1e6:.1f}M device={DEVICE}")

    # text features per class (average over templates)
    text_features = []
    for c in CLASS_NAMES:
        texts = [t.format(c) for t in TEMPLATES]
        tok = tokenizer(texts).to(DEVICE)
        with torch.no_grad():
            feats = model.encode_text(tok)
        feats = feats.mean(dim=0)
        feats /= feats.norm(dim=-1, keepdim=True)
        text_features.append(feats)
    text_features = torch.stack(text_features)  # C,D

    # image features
    import PIL.Image
    import io
    all_logits = []
    B = 64 if DEVICE == "cuda" else 32
    with torch.no_grad():
        for i in range(0, len(X_eval), B):
            batch = X_eval[i:i + B]
            imgs = []
            for arr in batch:
                img = PIL.Image.fromarray(arr, "RGB")
                imgs.append(preprocess(img))
            x = torch.stack(imgs).to(DEVICE)
            f = model.encode_image(x)
            f /= f.norm(dim=-1, keepdim=True)
            logits = (f @ text_features.T)  # B,C
            all_logits.append(logits.cpu().numpy())
    logits = np.concatenate(all_logits)
    preds = logits.argmax(axis=1)
    acc = float((preds == y_eval).mean())
    per_class = []
    for c in range(4):
        mask = y_eval == c
        per_class.append(float((preds[mask] == c).mean()) if mask.sum() else float("nan"))
    lo, hi = wilson_ci(acc, len(y_eval))

    out = {
        "model": MODEL_NAME,
        "pretrained": PRETRAINED,
        "n_params": int(n_params),
        "device": DEVICE,
        "threads": torch.get_num_threads(),
        "templates": TEMPLATES,
        "subset": subset,
        "subset_size": int(len(X_eval)),
        "seed": RNG_SEED,
        "overall_acc": acc,
        "wilson95_ci": [float(lo), float(hi)],
        "per_class_acc": {CLASS_NAMES[i]: per_class[i] for i in range(4)},
        "n_test_total": int(len(y_te)),
    }
    with open(os.path.join(RESULTS, "satin_clip_zeroshot_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
