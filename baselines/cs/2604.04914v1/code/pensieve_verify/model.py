"""Extract a sequential ReLU network from the frozen diffRL Pensieve ONNX models.

The public ``*_simple.onnx`` checkpoints are ReLU classifiers whose graph
(input 1x6x8 -> per-feature embeddings -> concat -> FC(H) -> ReLU -> FC(6)) is
rewritten here as an exact sequence of affine layers::

    h0 = relu(W0 x + b0)     # concatenated feature embeddings (with per-row mask)
    h1 = relu(W1 h0 + b1)    # shared hidden layer
    y  =      W2 h1 + b2     # 6 logits

The pre-activation of the first hidden block (the concat tensor) is purely
linear in x, so we recover (W0, b0) by evaluating a ReLU->Identity copy of the
graph at x=0 and at the 48 basis vectors.  (W1, W2) are read directly from the
final Gemm initializers.  The extraction is validated against onnxruntime.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnx
from onnx import helper, TensorProto
import onnxruntime as ort


@dataclass
class ReLUNet:
    """Sequential ReLU network.

    h0 = (mask? relu : id)(W0 x + b0);  h1 = relu(W1 h0 + b1);  y = W2 h1 + b2
    """

    W0: np.ndarray
    b0: np.ndarray
    mask0: np.ndarray  # bool array: which rows of W0 x + b0 go through ReLU
    W1: np.ndarray
    b1: np.ndarray
    W2: np.ndarray
    b2: np.ndarray
    name: str = ""

    @property
    def n_in(self) -> int:
        return self.W0.shape[1]

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Exact forward pass (numpy, float64).  x shape (..., n_in)."""
        x = np.asarray(x, dtype=np.float64)
        z0 = x @ self.W0.T + self.b0
        h0 = np.where(self.mask0, np.maximum(0.0, z0), z0)
        h1 = np.maximum(0.0, h0 @ self.W1.T + self.b1)
        return h1 @ self.W2.T + self.b2

    def n_params(self) -> int:
        return (
            self.W0.size + self.b0.size
            + self.W1.size + self.b1.size
            + self.W2.size + self.b2.size
        )

    def layers(self):
        """(W, b, is_relu, mask) in forward order for the generic verifiers."""
        return [
            (self.W0, self.b0, True, self.mask0),
            (self.W1, self.b1, True, None),
            (self.W2, self.b2, False, None),
        ]


def _relu_to_identity(model: onnx.ModelProto) -> onnx.ModelProto:
    """Return a copy with every Relu node replaced by Identity."""
    m = onnx.ModelProto()
    m.CopyFrom(model)
    new_nodes = []
    for node in m.graph.node:
        if node.op_type == "Relu":
            ident = helper.make_node("Identity", inputs=[node.input[0]], outputs=node.output)
            new_nodes.append(ident)
        else:
            new_nodes.append(node)
    del m.graph.node[:]
    m.graph.node.extend(new_nodes)
    return m


def _with_extra_outputs(model: onnx.ModelProto, names: list[str]) -> onnx.ModelProto:
    """Return a copy of ``model`` that additionally outputs tensors ``names``."""
    m = onnx.ModelProto()
    m.CopyFrom(model)
    existing = {o.name for o in m.graph.output}
    for nm in names:
        if nm in existing:
            continue
        m.graph.output.append(helper.make_tensor_value_info(nm, TensorProto.FLOAT, None))
    return m


def _concat_input_map(graph) -> dict[str, bool]:
    """Map concat output tensor -> bool mask over its rows (True = row passes through ReLU).

    For the diffRL simple models the first ReLU block is consumed by the unique
    Concat node.  Return the mask for the concat output rows.
    """
    for node in graph.node:
        if node.op_type == "Concat":
            relu_out = {n.output[0] for n in graph.node if n.op_type == "Relu"}
            mask = np.array([inp in relu_out for inp in node.input], dtype=bool)
            # rows per input are contiguous; concat repeats mask per row later
            return {node.output[0]: mask}
    raise RuntimeError("no Concat node found")


def _basis_maps(model_lin: onnx.ModelProto, in_name: str, target: str, n_in: int, n_out: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute the exact affine map x -> target tensor for a purely linear graph.

    A x + b recovered by evaluating at x=0 and at each basis vector.
    """
    probe = _with_extra_outputs(model_lin, [target])
    sess = ort.InferenceSession(probe.SerializeToString(), providers=["CPUExecutionProvider"])
    b = sess.run([target], {in_name: np.zeros((1, 6, 8), dtype=np.float32)})[0].reshape(-1)[:n_out]
    A = np.zeros((n_out, n_in), dtype=np.float64)
    for j in range(n_in):
        x = np.zeros((1, 6, 8), dtype=np.float32)
        x.reshape(-1)[j] = 1.0
        val = sess.run([target], {in_name: x})[0].reshape(-1)[:n_out]
        A[:, j] = val - b
    return A, b


def extract_relu_net(onnx_path: Path | str, name: str = "") -> ReLUNet:
    """Extract (W0,b0,mask0,W1,b1,W2,b2) from a diffRL ``*_simple.onnx`` checkpoint."""
    model = onnx.load(str(onnx_path))
    graph = model.graph
    n_in = 48  # flattened 1x6x8

    model_lin = _relu_to_identity(model)
    in_name = graph.input[0].name

    # ---- find the concat node and the two final Gemm layers ----
    concat_node = next(n for n in graph.node if n.op_type == "Concat")
    gemms = [n for n in graph.node if n.op_type == "Gemm"]
    final_gemm = gemms[-1]          # output layer
    shared_gemm = gemms[-2]         # layer feeding the shared ReLU (W1)

    # concat output is the pre-activation of the first hidden block
    concat_out = concat_node.output[0]
    W1 = _weight(graph, shared_gemm.input[1])
    W2 = _weight(graph, final_gemm.input[1])
    b1 = _weight(graph, shared_gemm.input[2]) if len(shared_gemm.input) > 2 else np.zeros(W1.shape[0])
    b2 = _weight(graph, final_gemm.input[2]) if len(final_gemm.input) > 2 else np.zeros(W2.shape[0])
    n_out0 = W1.shape[1]  # concat length == second-dim of shared Gemm weight

    A0, b0 = _basis_maps(model_lin, in_name, concat_out, n_in, n_out0)

    # per-row ReLU mask for the first hidden block
    mask0 = np.zeros(n_out0, dtype=bool)
    rows_per_in = []
    for i, inp in enumerate(concat_node.input):
        # number of elements per concat input
        if inp in graph.value_info:
            dims = [d.dim_value for d in graph.value_info[inp].type.tensor_type.shape.dim]
            n_el = int(np.prod(dims)) if all(d > 0 for d in dims) else None
        else:
            n_el = None
        # fall back: infer from the weight slices is complex; use relu output set
        n_el = rows_per_in[i] if False else None
    # Robust mask derivation: concat inputs are relu outputs or linear outputs.
    # A tensor "passes through ReLU" if it is a Relu output or is produced by a
    # shape-only op (Reshape/Identity) whose input passes through ReLU.
    relu_passthrough = set()
    changed = True
    while changed:
        changed = False
        for n in graph.node:
            if n.op_type == "Relu" and n.output[0] not in relu_passthrough:
                relu_passthrough.add(n.output[0])
                changed = True
            elif n.op_type in ("Reshape", "Identity") and n.input[0] in relu_passthrough:
                if n.output[0] not in relu_passthrough:
                    relu_passthrough.add(n.output[0])
                    changed = True
    probe = _with_extra_outputs(model_lin, list(concat_node.input))
    sess_probe = ort.InferenceSession(probe.SerializeToString(), providers=["CPUExecutionProvider"])
    outs = sess_probe.run(list(concat_node.input), {in_name: np.zeros((1, 6, 8), dtype=np.float32)})
    idx = 0
    for inp, arr in zip(concat_node.input, outs):
        n_el = arr.size
        mask0[idx: idx + n_el] = (inp in relu_passthrough)
        idx += n_el
    assert idx == n_out0, f"concat size mismatch {idx} vs {n_out0}"

    net = ReLUNet(
        W0=np.ascontiguousarray(A0, dtype=np.float64),
        b0=np.ascontiguousarray(b0, dtype=np.float64),
        mask0=mask0,
        W1=np.ascontiguousarray(W1, dtype=np.float64),
        b1=np.ascontiguousarray(b1, dtype=np.float64),
        W2=np.ascontiguousarray(W2, dtype=np.float64),
        b2=np.ascontiguousarray(b2, dtype=np.float64),
        name=name,
    )
    return net


def _weight(graph, name: str) -> np.ndarray:
    for init in graph.initializer:
        if init.name == name:
            return onnx.numpy_helper.to_array(init).astype(np.float64)
    raise KeyError(name)


def validate_net(net: ReLUNet, onnx_path: Path | str, ranges=(-1.0, 1.0), n_samples: int = 64, seed: int = 0) -> dict:
    """Compare the extracted ReLUNet against onnxruntime on random inputs."""
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(seed)
    lo, hi = ranges
    xs = rng.uniform(lo, hi, size=(n_samples, 6, 8)).astype(np.float32)
    max_diff = 0.0
    mean_diff = 0.0
    for x in xs:
        y_onnx = sess.run(None, {"input": np.expand_dims(x, 0)})[0][0]
        y_np = net.forward(x.reshape(1, -1))[0]
        max_diff = max(max_diff, float(np.max(np.abs(y_onnx - y_np))))
        mean_diff += float(np.mean(np.abs(y_onnx - y_np)))
    return {"samples": n_samples, "max_abs_diff": max_diff, "mean_abs_diff": mean_diff / n_samples}
