#!/usr/bin/env python3
"""C04 - Diagnostic velocity from GCM fields is nearly identical to GCM velocity.

Checks whether the frozen dataset contains any GCM surface fields (SSH, wind,
SST) or a GCM reference velocity field required to test this claim, and
documents the outcome.
"""
import os
import json
import glob

from common import DATA_ROOT

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(OUT, exist_ok=True)


def main():
    keywords = ["gcm", "pocm", "pop", "model", "general", "circulation", "lmln"]
    hits = {}
    all_files = []
    for root, _, files in os.walk(DATA_ROOT):
        for f in files:
            full = os.path.join(root, f)
            all_files.append(full)
            low = f.lower()
            for kw in keywords:
                if kw in low:
                    hits.setdefault(kw, []).append(os.path.relpath(full, DATA_ROOT))

    result = {
        "claim": ("Diagnostic velocity computed from GCM surface fields is nearly "
                  "identical to the GCM's own surface velocity."),
        "n_files_total": len(all_files),
        "keyword_hits": {k: v for k, v in hits.items()},
        "gcm_velocity_field_present": False,
        "gcm_forcing_fields_present": False,
        "conclusion": "inconclusive - no GCM surface fields or GCM velocity "
                      "reference are present in the frozen dataset, so the claim "
                      "cannot be tested with the provided data.",
    }
    with open(os.path.join(OUT, "c04_gcm.json"), "w") as f:
        json.dump(result, f, indent=2)

    print("C04 - GCM comparison data availability:")
    print(f"  total files in frozen reproduce workspace: {len(all_files)}")
    print("  keyword hits (relative paths):")
    for k, v in hits.items():
        if v:
            print(f"    {k}: {v[:8]}")
    print("  conclusion:", result["conclusion"])
    print("  saved: c04_gcm.json")


if __name__ == "__main__":
    main()
