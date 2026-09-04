import os

ROOT = os.path.dirname(os.path.abspath(__file__))                    # code/
TASK_ROOT = os.path.realpath(os.path.join(ROOT, "..", ".."))         # task dir (contains data/)
DATA_DIR = os.environ.get("PAPER_DATA_DIR", os.path.join(TASK_ROOT, "data"))
WORK_DIR = os.environ.get("PAPER_WORK_DIR", os.path.realpath(os.path.join(ROOT, "..")))
if not os.path.isdir(DATA_DIR):
    DATA_DIR = os.path.join(os.getcwd(), "data")

RESULT_DIR = os.path.join(WORK_DIR, "results")
EVIDENCE_DIR = os.path.join(WORK_DIR, "evidence")
CACHE_DIR = os.path.join(WORK_DIR, "cache")

for d in (RESULT_DIR, EVIDENCE_DIR, CACHE_DIR):
    os.makedirs(d, exist_ok=True)

SEEDS = [0, 1, 2, 3, 4]
N_BOOTSTRAP = 10000
BOOTSTRAP_SEED = 0

SASCORE_EASY_BELOW = 4.0
SASCORE_HARD_ABOVE = 5.0

ELEMENTS = ["C", "N", "O", "S", "F", "Cl", "Br", "I", "P", "B", "Se", "Si",
            "Na", "K", "Mg", "Ca", "Fe", "Zn", "Cu", "Sn"]
UNK_ELEM_IDX = len(ELEMENTS)
ATOM_D = UNK_ELEM_IDX + 7
BOND_D = 5

TORCH_THREADS = max(4, min(16, (os.cpu_count() or 8) - 2))

MODEL = dict(
    hidden=64,
    layers=3,
    dropout=0.0,
    bn=True,
    eps=True,
    edge_dim=BOND_D,
    atom_dim=ATOM_D,
)

TRAIN = dict(
    batch_size=256,
    lr=1e-3,
    weight_decay=5e-4,
    max_epochs=26,
    patience=8,
    val_frac=0.1,
    val_seed=0,
    pos_weight=True,
    aux_weight=0.1,
)