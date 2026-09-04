"""Shared configuration and path resolution for the TAPE claim-validation pipeline."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SOLUTION_DIR = os.path.dirname(HERE)

SEED = 42

# Resolution order for the frozen TAPE CSVs.
DATA_CANDIDATES = [
    os.environ.get("TAPE_DATA_DIR", ""),                # optional explicit override
    SOLUTION_DIR,                                        # agent_solution root
    os.path.join(SOLUTION_DIR, "data"),                 # agent_solution/data
    os.path.dirname(SOLUTION_DIR),                       # task root
    os.path.join(os.path.dirname(SOLUTION_DIR), "data"),
    os.path.join(os.path.dirname(SOLUTION_DIR), "..", "..", "data"),  # ../data from solution
    "/mnt/f/dataset/biomed/1906.08230_tape_protein_tasks",
]

CSV_FILES = {
    "fluorescence": "fluorescence_dataset.csv",
    "stability": "stability_dataset.csv",
}

EMBEDDING_MODELS = ["facebook/esm2_t6_8M_UR50D", "facebook/esm2_t33_650M_UR50D"]

# short tags used for filenames / labels
MODEL_SHORT = {
    "facebook/esm2_t6_8M_UR50D": "esm2_t6_8M",
    "facebook/esm2_t33_650M_UR50D": "esm2_t33_650M",
}

RESULTS_DIR = os.path.join(SOLUTION_DIR, "results")
EVIDENCE_DIR = os.path.join(SOLUTION_DIR, "evidence")
EMBED_DIR = os.path.join(RESULTS_DIR, "embeddings")


def find_data_dir():
    for cand in DATA_CANDIDATES:
        if not cand:
            continue
        cand = os.path.abspath(cand)
        if os.path.isfile(os.path.join(cand, "fluorescence_dataset.csv")):
            return cand
    raise FileNotFoundError(
        "Could not locate fluorescence_dataset.csv / stability_dataset.csv. "
        "Set TAPE_DATA_DIR to a directory containing the two frozen CSVs."
    )


def ensure_dirs():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    os.makedirs(os.path.join(RESULTS_DIR, "embeddings"), exist_ok=True)