"""Configuration for the FloodNet VQA reproduction task.

Paths default to the frozen dataset location and can be overridden with the
FLOODNET_DATA_DIR environment variable. All intermediate artifacts are written
under AGENT_DIR (= this repo's agent_solution/).
"""
import json
import os

AGENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR = os.environ.get(
    "FLOODNET_DATA_DIR",
    "/mnt/f/dataset/earth/2012.02951_floodnet/data",
)

VQA_TRAIN_JSON = os.path.join(DATA_DIR, "vqa_questions", "Training_Question.json")
VQA_VALID_JSON = os.path.join(DATA_DIR, "vqa_questions", "Valid_Question.json")
IMG_DIR = os.path.join(DATA_DIR, "takara_track2", "train_image", "img")

# ---- split / randomness -------------------------------------------------
SEED = 42
EVAL_FRAC = 0.15           # image-level evaluation fraction (85/15 split)
DEV_FRAC_OF_TRAIN = 0.12   # dev set drawn from the train images for model selection

# ---- output locations ---------------------------------------------------
RESULTS_DIR = os.path.join(AGENT_DIR, "results")
WORKSPACE = os.path.join(AGENT_DIR, "workspace")
FIGURES_DIR = os.path.join(AGENT_DIR, "figures")
EVIDENCE_DIR = os.path.join(AGENT_DIR, "evidence")
for _d in (RESULTS_DIR, WORKSPACE, FIGURES_DIR, EVIDENCE_DIR):
    os.makedirs(_d, exist_ok=True)

# ---- feature extraction settings ----------------------------------------
IMAGE_SIZE_R18 = 448     # ResNet-18 input resolution
IMAGE_SIZE_VIT = 224     # ViT-B/16 input resolution
BATCH_SIZE_FEAT = 4


def answer_vocab_map():
    with open(VQA_TRAIN_JSON) as f:
        qa = json.load(f)
    voc = sorted({str(v["Ground_Truth"]) for v in qa.values()})
    return {a: i for i, a in enumerate(voc)}, voc