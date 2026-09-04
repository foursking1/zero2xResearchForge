"""Parse the frozen diffRL VNN-LIB query files into box + argmax constraints."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

IN_PAT = re.compile(r"\(assert \((>=|<=) X_(\d+) ([^\)]+)\)\)")
OUT_PAT = re.compile(r"\(assert \(<= Y_(\d+) Y_(\d+)\)\)")


@dataclass
class Query:
    name: str
    lower: np.ndarray  # (n,) inclusive lower bounds
    upper: np.ndarray  # (n,) inclusive upper bounds
    pairs: list[tuple[int, int]]  # output constraints: Y_lhs <= Y_rhs

    @property
    def n(self) -> int:
        return self.lower.size

    @property
    def varying(self) -> np.ndarray:
        return np.where(self.upper - self.lower > 1e-12)[0]

    def max_margin(self, outputs: np.ndarray) -> float:
        """max_j (Y_lhs - Y_rhs).  <= 0 means every constraint holds (violation)."""
        m = 0.0
        for lhs, rhs in self.pairs:
            m = max(m, float(outputs[lhs] - outputs[rhs]))
        return m

    def satisfied(self, outputs: np.ndarray, tol: float = 1e-9) -> bool:
        return all(float(outputs[lhs]) <= float(outputs[rhs]) + tol for lhs, rhs in self.pairs)


def parse_vnnlib(path: Path) -> Query:
    text = Path(path).read_text()
    idxs = [int(m.group(2)) for m in IN_PAT.finditer(text)]
    n = max(idxs) + 1 if idxs else 0
    lower = np.zeros(n)
    upper = np.zeros(n)
    for m in IN_PAT.finditer(text):
        op, i, v = m.group(1), int(m.group(2)), float(m.group(3))
        if op == ">=":
            lower[i] = v
        else:
            upper[i] = v
    pairs = [(int(a), int(b)) for a, b in OUT_PAT.findall(text)]
    return Query(name=Path(path).name, lower=lower, upper=upper, pairs=pairs)


def load_query_sets(data_root: Path) -> dict[str, list[Query]]:
    """Load the three Pensieve query sets from the frozen data tree."""
    app = data_root / "applications" / "pensieve"
    csvs = {
        "capacity_utilization": app / "capacity_utilization_input100.csv",
        "rebuffering_avoidance": app / "rebuffering_avoidance_input100.csv",
        "robustness": app / "robustness_input100.csv",
    }
    sets: dict[str, list[Query]] = {}
    for prop, csv_path in csvs.items():
        rels = [ln.strip() for ln in csv_path.read_text().splitlines() if ln.strip()]
        sets[prop] = [parse_vnnlib(app / rel) for rel in rels]
    return sets


def margins_for(net, query: Query, u: np.ndarray) -> list[float]:
    out = net.forward(u)
    return [float(out[l] - out[r]) for l, r in query.pairs]
