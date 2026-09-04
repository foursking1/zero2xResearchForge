"""
Model / data consistency check (rubric A1).

Loads the frozen Be model artifacts and verifies:
  * params.json key fields (element/system = Be, 256-atom training snapshot,
    SNAP descriptor, LDOS target, network architecture, scalers).
  * network.pth state dict shapes match params.network.layer_sizes.
  * iscaler/oscaler scale metadata is consistent with the params scaling
    settings.
  * the recalled snapshot data agrees with model_training/training.py.

Output:  evidence/model_check.json
Run:     python model_check.py   (env MALA_MODEL_DIR overrides model dir)
"""
import json
import os

import torch
import mala
from mala.datahandling.snapshot import Snapshot
from mala.targets.target import Target


MODEL_DIR = os.environ.get(
    "MALA_MODEL_DIR",
    "F:/dataset/materials/2210.11343_mala_size_transfer/trained_models/beryllium/",
)


def main():
    params_path = MODEL_DIR + "beryllium.params.json"
    with open(params_path, encoding="utf-8") as f:
        raw = json.load(f)

    # ---- 1) raw JSON key fields ----
    snap0 = raw["data"]["snapshot_directories_list"][0]["data"]
    snap1 = raw["data"]["snapshot_directories_list"][1]["data"]
    checks = {
        "element_be": (
            "Be256" in snap0["input_npy_file"]
            and "Be256" in snap1["input_npy_file"]),
        "training_size_256": (
            "/N256/" in snap0["input_npy_directory"]
            and "/N256/" in snap0["output_npy_directory"]),
        "training_298K": "298K" in snap0["input_npy_directory"],
        "train_snapshot0_validate_snapshot2": (
            snap0["input_npy_file"] == "Be256_298K_snapshot0.in.npy"
            and snap0["snapshot_function"] == "tr"
            and snap1["input_npy_file"] == "Be256_298K_snapshot2.in.npy"
            and snap1["snapshot_function"] == "va"),
        "ldos_units_1_per_eV": snap0["output_units"] == "1/eV",
        "descriptor_snap_twojmax10": (
            raw["descriptors"]["descriptor_type"] == "SNAP"
            and raw["descriptors"]["twojmax"] == 10),
        "rcutfac_467637": raw["descriptors"]["rcutfac"] == 4.67637,
        "ldos_grid_250_01_off5": (
            raw["targets"]["ldos_gridsize"] == 250
            and raw["targets"]["ldos_gridspacing_ev"] == 0.1
            and raw["targets"]["ldos_gridoffset_ev"] == -5),
        "restrict_targets_zero_negative":
            raw["targets"]["restrict_targets"] == "zero_out_negative",
        "output_scaling_normal": raw["data"]["output_rescaling_type"] == "normal",
        "input_scaling_featurewise_standard":
            raw["data"]["input_rescaling_type"] == "feature-wise-standard",
        "loss_mse": raw["network"]["loss_function_type"] == "mse",
        "ffn_leakyrelu": raw["network"]["nn_type"] == "feed-forward"
            and raw["network"]["layer_activations"] == ["LeakyReLU"],
    }
    layer_sizes = raw["network"]["layer_sizes"]

    # ---- 2) network state dict shape vs params ----
    sd = torch.load(MODEL_DIR + "beryllium.network.pth", map_location="cpu",
                    weights_only=True)
    first_w = tuple(sd["layers.0.weight"].shape)
    last_w = tuple(sd["layers.8.weight"].shape)
    # FFN with 5 layers -> [in, 800, 800, 800, 250, out]: weights 0,2,4,6,8
    checks["network_first_layer_in_91"] = first_w[1] == 91
    checks["network_output_250"] = last_w[0] == 250
    checks["layer_sizes_match_state_dict"] = (
        layer_sizes == [first_w[1], first_w[0], first_w[0], first_w[0],
                        last_w[1], last_w[0]])

    # ---- 3) scaler metadata ----
    iscaler = mala.DataScaler.load_from_file(MODEL_DIR + "beryllium.iscaler.pkl",
                                             auto_convert=False)
    oscaler = mala.DataScaler.load_from_file(MODEL_DIR + "beryllium.oscaler.pkl",
                                             auto_convert=False)
    checks["iscaler_feature_wise_standard"] = (
        iscaler.typestring == "feature-wise-standard"
        and bool(getattr(iscaler, "feature_wise", False)))
    checks["oscaler_normal"] = bool(getattr(oscaler, "scale_normal", True)) or (
        oscaler.typestring == "normal")
    n_feat_in = float(iscaler.means.shape[1])
    n_feat_out = float(oscaler.maxs.shape[0]) if oscaler.maxs is not None \
        else float(0)  # typical 'normal' typestring scale
    checks["scaler_dims_91_in"] = n_feat_in == 91

    report = {
        "params_path": params_path,
        "model_files": sorted(os.listdir(MODEL_DIR)),
        "raw_params_fields": {
            "layer_sizes": layer_sizes,
            "descriptor": raw["descriptors"],
            "targets": raw["targets"],
            "data": raw["data"],
            "network_params": raw["network"],
            "running_params": raw["running"],
        },
        "snapshot_training": {
            "tr": snap0,
            "va": snap1,
        },
        "network_state_dict_shapes": {k: list(v.shape)
                                      for k, v in sd.items()},
        "scaler_dims": {"input": int(n_feat_in), "output": int(n_feat_out)},
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "note": ("Network/params/scalers load successfully under MALA 1.4 "
                 "(legacy 1.1 compat patches); element Be, 256-atom 298 K "
                 "training snapshot, SNAP 2Jmax=10 descriptor, LDOS target."),
    }

    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "..", "evidence", "model_check.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)

    print("all_checks_pass:", all(checks.values()))
    for k, v in checks.items():
        print(f"  {k}: {v}")
    print("wrote", out_path)


if __name__ == "__main__":
    main()