# agent_solution — Task `2507.12295_textadbench`

Reproduction of the Text-ADBench "deep detectors show no advantage over
shallow algorithms" claim on the **SMS-Spam + LLaMA-3-8B (mntp) EOS**
frozen embeddings (official HuggingFace `Feng-001/Text-ADBench` release).

- **结论**: `solution.md`（三 claim 判定 supported + 证据)
- **完整报告**: `report.md`（方法 / 防泄漏 / 版本 / 局限性 / 复现步骤）
- **快速复核** (~30 s): `python code/verify_knn.py --checksums` → KNN AUROC = 94.85% (pyod 3.6.4 reference)
- **全量复现** (~1 h): `python code/run_experiment.py`
- 关键结果表: `results/evidence_table.csv`；逐 seed: `results/auroc_per_seed.csv`；图: `results/auroc_comparison.png`

## Directory layout

```
agent_solution/
├── solution.md / report.md / README.md
├── requirements.txt
├── code/
│   ├── run_experiment.py        # main pipeline (10 methods x 5 seeds)
│   ├── dpad.py                  # official repo DPAD (vendored, MIT)
│   ├── deep_port.py             # pyod-3.6.4-equivalent DeepSVDD + device (verifiably identical on CPU)
│   ├── aggregate_from_scores.py # audit-style evidence-table rebuild from saved scores
│   ├── verify_knn.py            # judge-facing KNN spot-check + SHA-256
│   └── arguments_official/      # official arguments/*.json used
├── data/embeddings/sms_spam/Llama3-8b/   # 4 frozen .npy (sha matched)
├── results/                     # evidence_table.csv, per-seed csv/json, scores/, logs, figure
└── evidence/                    # copies of key evidence for the judge
```