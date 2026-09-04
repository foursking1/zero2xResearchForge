"""
SATIN (2304.11619) - SAT-4 data preparation.
Loads the frozen parquet, verifies schema, decodes images, performs a fixed
stratified 80/20 train/test split, computes normalization stats from the
training split only (leakage prevention), and saves preprocessed arrays.

Outputs (in ../results):
  satin_arrays.npz : X_train, y_train, X_test, y_test, mean, std, class_names
  satin_data_summary.json : schema + class distribution + split sizes
"""
import os, io, json
import numpy as np
import pandas as pd
import PIL.Image
from sklearn.model_selection import train_test_split

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("TORCH_NUM_THREADS", "2")

DATA_PATH = r"F:/dataset/earth/2304.11619_satin/data/data/SAT_4.parquet"
RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
os.makedirs(RESULTS, exist_ok=True)

RNG_SEED = 20260817
TEST_SIZE = 0.2

CLASS_NAMES = ["barren land", "trees", "grassland", "buildings"]

def main():
    df = pd.read_parquet(DATA_PATH)
    assert df.shape == (100000, 2), df.shape
    assert list(df.columns) == ["image", "label"], list(df.columns)

    # decode images
    images = []
    for d in df["image"]:
        assert set(d.keys()) == {"bytes", "path"}, d.keys()
        img = PIL.Image.open(io.BytesIO(d["bytes"]))
        assert img.size == (28, 28), img.size
        images.append(np.array(img))
    X = np.stack(images).astype(np.uint8)
    y = df["label"].to_numpy(dtype=np.int64)

    # sanity: PNG-decode checks done above; assert label range
    assert set(np.unique(y)) <= {0, 1, 2, 3}

    # class distribution (full dataset)
    class_counts = {int(c): int((y == c).sum()) for c in np.unique(y)}

    # fixed stratified split (test_size=20%)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RNG_SEED, stratify=y
    )

    # normalization stats from training split only
    mean = X_tr.reshape(X_tr.shape[0], -1).mean(axis=0).reshape(3, 28, 28)
    std = X_tr.reshape(X_tr.shape[0], -1).std(axis=0).reshape(3, 28, 28)
    std[std == 0] = 1.0

    np.savez_compressed(
        os.path.join(RESULTS, "satin_arrays.npz"),
        X_train=X_tr, y_train=y_tr, X_test=X_te, y_test=y_te,
        mean=mean, std=std,
    )

    summary = {
        "data_path": DATA_PATH,
        "n_rows": len(df),
        "image_size": [28, 28, 3],
        "label_names": CLASS_NAMES,
        "class_counts_full": class_counts,
        "split_seed": RNG_SEED,
        "test_size": TEST_SIZE,
        "n_train": int(len(X_tr)),
        "n_test": int(len(X_te)),
        "train_class_counts": {int(c): int((y_tr == c).sum()) for c in np.unique(y_tr)},
        "test_class_counts": {int(c): int((y_te == c).sum()) for c in np.unique(y_te)},
        "normalization": {"from": "train_split_only", "mean_shape": list(mean.shape), "std_shape": list(std.shape)},
    }
    with open(os.path.join(RESULTS, "satin_data_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
