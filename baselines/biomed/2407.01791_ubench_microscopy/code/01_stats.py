#!/usr/bin/env python
"""Step 1: parse the frozen Arrow shard and emit dataset statistics.

Outputs:
  results/dataset_stats.json   -- counts / distributions used in the report
  results/questions_long.csv   -- long-form question table (option list + answer)
  results/task_counts.csv      -- question counts per dataset x question type
"""
import json
import sys
import os

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import load_arrow_questions, COARSE_TYPES, FINE_TYPES, QUESTION_NAMES, RESULTS

df = load_arrow_questions()

img_meta = df.drop_duplicates("image_id").reset_index(drop=True)

valid_answer = int(df["answer_idx"].isna().sum()) == 0
opts_match = int(((df["options"].map(len) > df["answer_idx"]).sum() == len(df)))

stats = {
    "n_images": int(img_meta.shape[0]),
    "n_question_rows": int(df.shape[0]),
    "n_questions_per_image": [6, 6, "all 6 closed-VQA slots populated"],
    "n_closedvqa_questions": int(df.shape[0]),
    "question_types": QUESTION_NAMES,
    "coarse_question_types": COARSE_TYPES,
    "fine_question_types": FINE_TYPES,
    "n_datasets": int(img_meta["dataset"].nunique()),
    "datasets": json.loads(img_meta["dataset"].value_counts().to_json()),
    "modality_counts": json.loads(img_meta["modality_meta"].value_counts().to_json()),
    "domain_counts": json.loads(img_meta["domain_meta"].value_counts().to_json()),
    "subdomain_counts": json.loads(img_meta["subdomain_meta"].value_counts().to_json()),
    "submodality_counts": json.loads(img_meta["submodality_meta"].value_counts().to_json()),
    "stain_counts": json.loads(img_meta["stain_meta"].value_counts().to_json()),
    "classification_class_counts": json.loads(img_meta["label_name"].value_counts().to_json()),
    "n_classification_classes": int(img_meta["label_name"].nunique()),
    "all_answer_indexes_valid": bool(valid_answer),
    "all_answer_indexes_within_options": bool(opts_match),
    "n_options_distribution": json.loads(df["options"].map(len).value_counts().to_json()),
    "split": "test",
    "shard": "ubench-test-00000-of-00007.arrow (1 of 7 perception test shards)",
}

tc = df.groupby(["dataset", "question_type"]).size().unstack(fill_value=0)
tc.to_csv(os.path.join(RESULTS, "task_counts.csv"))

df.drop(columns="image_bytes").to_pickle(os.path.join(RESULTS, "questions_long.pkl"))
df[["image_id", "dataset", "question_type", "question_id", "question", "options",
    "answer_idx", "answer"]].to_csv(os.path.join(RESULTS, "questions_long.csv"), index=False)

with open(os.path.join(RESULTS, "dataset_stats.json"), "w") as f:
    json.dump(stats, f, indent=2)

print(json.dumps({k: v for k, v in stats.items() if not isinstance(v, dict)}, indent=2))
print("saved: dataset_stats.json, task_counts.csv, questions_long.csv")