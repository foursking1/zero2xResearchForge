"""Shared constants and utilities for the AID multi-label / single-label pipelines."""
import json
import os

# 17-class label order of the AID_MultiLabel mirror (SATIN).
CLASS_NAMES_17 = [
    "airplane", "bare soil", "buildings", "cars", "chaparral", "court",
    "dock", "field", "grass", "mobile home", "pavement", "sand",
    "sea", "ship", "tanks", "trees", "water",
]
N_CLASSES_17 = 17

# Original AID 30-class single-label order (from folder listing order).
CLASS_NAMES_30 = [
    "Airport", "BareLand", "BaseballField", "Beach", "Bridge", "Center",
    "Church", "Commercial", "DenseResidential", "Desert", "Farmland",
    "Forest", "Industrial", "Meadow", "MediumResidential", "Mountain",
    "Park", "Parking", "Playground", "Pond", "Port", "RailwayStation",
    "Resort", "River", "School", "SparseResidential", "Square", "Stadium",
    "StorageTanks", "Viaduct",
]
N_CLASSES_30 = 30

# Frozen data physical location.
FROZEN_PARQUET = (
    "/mnt/f/dataset/earth/1608.05167_aid/data_multilabel_quarantine/"
    "train-00000-of-00001-ee58cb5d786e111e.parquet"
)
AID_30_ROOT = "/mnt/f/dataset/earth/1608.05167_aid/data/data"
AID_30_SPLIT_CSV = "/mnt/f/dataset/earth/1608.05167_aid/aid_split_50.csv"

SEED = 20260813


def save_metrics(metrics, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print("wrote", path)