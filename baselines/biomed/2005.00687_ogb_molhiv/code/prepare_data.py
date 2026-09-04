#!/usr/bin/env python3
"""Read the frozen OGBG-MOLHIV jsonl files and build PyTorch Geometric Data objects.

Frozen data location: /mnt/f/dataset/biomed/2005.00687_ogb_molhiv/
  train.jsonl (32,901 graphs), valid.jsonl (4,113), test.jsonl (4,113)

Each line is one molecule graph with keys:
  num_nodes, node_feat (9-dim atom features), edge_index (2 x num_edges),
  edge_attr (3-dim bond features), y ([[0]] or [[1]]).

This script also computes the dataset statistics required by the task (A1) and
writes them to results/data_statistics.json.
"""

import json
import os
import sys

import numpy as np
import torch
from torch_geometric.data import Data

DATA_DIR = "/mnt/f/dataset/biomed/2005.00687_ogb_molhiv"
BENCH_DIR = os.environ.get("BENCH_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(BENCH_DIR, "results")

OUT_DIRS = {
    "train": os.getenv("MOLHIV_TRAIN_PT", "/tmp/molhiv/train.pt"),
    "valid": os.getenv("MOLHIV_VALID_PT", "/tmp/molhiv/valid.pt"),
    "test": os.getenv("MOLHIV_TEST_PT", "/tmp/molhiv/test.pt"),
}


def load_jsonl_graphs(split: str):
    path = os.path.join(DATA_DIR, f"{split}.jsonl")
    graphs = []
    pos = 0
    with open(path, "r") as f:
        for i, line in enumerate(f):
            raw = json.loads(line)
            edges = raw["edge_index"]
            x = torch.tensor(raw["node_feat"], dtype=torch.float32)
            ei = torch.tensor(edges, dtype=torch.long)
            ea = torch.tensor(raw["edge_attr"], dtype=torch.float32)
            y = torch.tensor(raw["y"], dtype=torch.long)
            assert x.shape[0] == raw["num_nodes"]
            g = Data(x=x, edge_index=ei, edge_attr=ea, y=y)
            g.num_nodes = raw["num_nodes"]
            graphs.append(g)
            if raw["y"][0] == 1:
                pos += 1
    return graphs, pos


def compute_statistics(graphs, split):
    n_nodes = np.array([g.num_nodes for g in graphs])
    n_edges = np.array([g.edge_index.shape[1] // 2 for g in graphs])
    n_graphs = len(graphs)
    return {
        "split": split,
        "n_graphs": n_graphs,
        "mean_num_nodes": round(float(n_nodes.mean()), 3),
        "median_num_nodes": int(np.median(n_nodes)),
        "min_num_nodes": int(n_nodes.min()),
        "max_num_nodes": int(n_nodes.max()),
        "mean_num_edges": round(float(n_edges.mean()), 3),
        "median_num_edges": int(np.median(n_edges)),
        "pos_rate": None,
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs("/tmp/molhiv", exist_ok=True)

    stats = {}
    all_pos = 0
    all_n = 0
    for split in ["train", "valid", "test"]:
        graphs, pos = load_jsonl_graphs(split)
        s = compute_statistics(graphs, split)
        s["pos_rate"] = round(pos / len(graphs), 5)
        stats[split] = s
        all_pos += pos
        all_n += len(graphs)
        torch.save(graphs, OUT_DIRS[split])
        print(f"{split}: {len(graphs)} graphs, positive rate {s['pos_rate']}, "
              f"nodes mean/median/max {s['mean_num_nodes']}/{s['median_num_nodes']}/{s['max_num_nodes']}")

    # Consistency checks vs. the paper (Table 2/3): 80/10/10 scaffold split.
    assert stats["train"]["n_graphs"] == 32901
    assert stats["valid"]["n_graphs"] == 4113
    assert stats["test"]["n_graphs"] == 4113
    assert 41127 == sum(x["n_graphs"] for x in stats.values())

    summary = {
        "total_graphs": all_n,
        "overall_pos_rate": round(all_pos / all_n, 5),
        "node_feat_dim": 9,
        "edge_attr_dim": 3,
        "split": stats,
    }
    out_path = os.path.join(RESULTS_DIR, "data_statistics.json")
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("wrote", out_path)


if __name__ == "__main__":
    main()