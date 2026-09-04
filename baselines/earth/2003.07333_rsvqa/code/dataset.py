"""Dataset loading, image-level splitting and question/answer processing for RSVQA LR.

Fixed pipeline:
- Reads the frozen parquet (path configurable; default points to the F: mirror).
- Splits at the IMAGE level (83? -> 80 train / 20 eval) with a fixed seed so that no
  image seen in training appears in evaluation (avoids image-level leakage).
- Normalizes questions (white-space collapse) and answers; labels question types.
"""
import io
import hashlib
import re

import numpy as np
import pandas as pd
from PIL import Image

DATA_PATH = "/mnt/f/dataset/earth/2003.07333_rsvqa/data/data/validation-00000-of-00001.parquet"


def image_hash(img):
    if isinstance(img, dict):
        return hashlib.md5(img["bytes"]).hexdigest()
    return hashlib.md5(np.asarray(img).tobytes()).hexdigest()


def decode_image(img):
    if isinstance(img, dict):
        raw = img.get("bytes")
        if raw is not None:
            return Image.open(io.BytesIO(raw)).convert("RGB")
        path = img.get("path")
        if path:
            return Image.open(path).convert("RGB")
    return img


def normalize_text(s):
    return re.sub(r"\s+", " ", str(s).strip())


def qtype_of(question):
    qs = normalize_text(question).lower()
    if "rural or an urban" in qs:
        return "rural_urban"
    if ("more " in qs or "less " in qs or " than " in qs or "equal to the number" in qs):
        return "comparison"
    if ("how many" in qs or "what is the number" in qs or "what is the amount" in qs):
        return "count"
    if ("is there" in qs or " there a " in qs or " there an " in qs or "present" in qs):
        return "presence"
    return "unknown"


def load_data(path=DATA_PATH):
    df = pd.read_parquet(path)
    df["imgid"] = df["image"].map(image_hash)
    df["question_norm"] = df["question"].map(normalize_text)
    df["answer_norm"] = df["answer"].map(normalize_text)
    df["qtype"] = df["question_norm"].map(qtype_of)
    assert (df["qtype"] != "unknown").all(), "unrecognized question type present"
    return df


def make_split(df, n_train_images=80, seed=42):
    """Image-level split. Returns (train_df, eval_df, valid_df_lookup)."""
    rng = np.random.RandomState(seed)
    ids = sorted(df["imgid"].unique())
    rng.shuffle(ids)
    train_ids = set(ids[:n_train_images])
    eval_ids = set(ids[n_train_images:])
    tr = df[df["imgid"].isin(train_ids)].copy()
    ev = df[df["imgid"].isin(eval_ids)].copy()
    return tr, ev, {"train": train_ids, "eval": eval_ids}


def answer_to_target(answer, qtype):
    a = normalize_text(answer).lower()
    if qtype == "count":
        return int(a)
    if qtype == "rural_urban":
        return 0 if a == "rural" else 1
    if qtype in ("presence", "comparison"):
        return 0 if a == "no" else (1 if a == "yes" else -1)
    return -1


def target_to_answer(t, qtype):
    if qtype == "count":
        return str(int(round(t)))
    if qtype == "rural_urban":
        return "rural" if t == 0 else "urban"
    return "no" if t == 0 else "yes"


def build_vocab(questions, min_freq=1):
    from collections import Counter

    c = Counter()
    for q in questions:
        c.update(normalize_text(q).split())
    words = ["<pad>", "<unk>"] + sorted(w for w, n in c.items() if n >= min_freq)
    w2i = {w: i for i, w in enumerate(words)}
    return w2i


def tokenize(question, w2i, max_len=24):
    ids = [w2i.get(w, w2i["<unk>"]) for w in normalize_text(question).split()]
    ids = ids[:max_len]
    ids = [w2i["<pad>"]] * (max_len - len(ids)) + ids
    return np.array(ids, dtype=np.int64)


def qtype_tpl(question):
    """Template signature used for language-prior baselines."""
    q = normalize_text(question)
    return re.sub(r"\d+", "#", q)