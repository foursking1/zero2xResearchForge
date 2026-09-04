"""Decode LoveDA parquet shards into PNG images/masks on disk + build manifest.

Frozen input  : /mnt/f/dataset/earth/2110.08733_loveda/data/data/train-*.parquet
Derived output: {here}/../data_decoded/{images,masks}/*.png  (1024x1024)
                {here}/../data_decoded/manifest.csv
"""
import io
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # agent_solution/
DATA_DIR = os.path.dirname(os.path.dirname(BASE)) + "/data"
SHARD_DIR = "/mnt/f/dataset/earth/2110.08733_loveda/data/data"
OUT = os.path.join(BASE, "data_decoded")


def decode(df):
    images, masks = [], []
    for i in range(len(df)):
        img = Image.open(io.BytesIO(list(df["image"][i].values())[0])).convert("RGB")
        msk = np.array(Image.open(io.BytesIO(list(df["label"][i].values())[0])))
        images.append(np.array(img))
        masks.append(msk)
    return np.stack(images), np.stack(masks)


def main():
    os.makedirs(os.path.join(OUT, "images"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "masks"), exist_ok=True)
    rows = []
    for shard in ["train-00000-of-00009.parquet", "train-00001-of-00009.parquet"]:
        df = pd.read_parquet(os.path.join(SHARD_DIR, shard))
        images, masks = decode(df)
        for i in range(len(df)):
            idx = len(rows)
            Image.fromarray(images[i]).save(os.path.join(OUT, "images", f"{idx:04d}.png"))
            Image.fromarray(masks[i].astype(np.uint8), mode="L").save(
                os.path.join(OUT, "masks", f"{idx:04d}.png"))
            rows.append({"shard": shard, "image": f"images/{idx:04d}.png",
                         "label": f"masks/{idx:04d}.png"})
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "manifest.csv"), index=False)
    print(f"decoded {len(rows)} samples -> {OUT}")


if __name__ == "__main__":
    main()