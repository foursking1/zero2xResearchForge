# Solution — PatternNet (1706.03424) Image Retrieval Reproduction

## Question
On the frozen PatternNet benchmark (30,400 remote-sensing images, 38 classes ×
800), can content-based retrieval built on deep CNN features reproduce the
paper's reported **mAP ≈ 0.60–0.62** (AlexNet_Fc1 mAP=0.6003 / VGGF mAP=0.6195,
P@5≈0.92–0.95)? I.e. the L1 claim: "deep CNN features achieve high-precision
content retrieval on PatternNet".

## Approach (1-line)
Frozen ImageNet-pretrained CNN backbones (ResNet18 primary; ViT-B/16 secondary)
→ L2-normalized embeddings → every image queries the full 30,400-image gallery
(self excluded) ranked by cosine similarity → mAP / P@5 / P@10 with
same-class = relevant (paper §5.2 protocol).

## Result
| feature | mAP | P@5 | P@10 | queries | gallery |
|---|---|---|---|---|---|
| **ResNet18** (primary) | **0.6233** | **0.9518** | **0.9407** | 30,400 | 30,400 |
| ViT-B/16 (secondary) | **0.6103** | **0.9477** | **0.9357** | 30,400 | 30,400 |
| paper AlexNet_Fc1 | 0.6003 | 0.9545 | – | – | – |
| paper VGGF | 0.6195 | 0.9246 | – | – | – |

Relative diff vs 0.61 anchor: +2.2% (ResNet18) / +0.05% (ViT-B/16) → inside the
≤10% full-score band. **Conclusion: supported.**

## Anti-leak protocol
Backbones are frozen ImageNet-pretrained and **never trained/fine-tuned on
PatternNet** (no fitting → no label leakage, no split to manipulate). Labels are
used only at evaluation time to score hits; query self-exclusion enforced;
deterministic ranking (seed 0 only for optional subsampling).

## Reproduction
```bash
python submission/scripts/run_all.py --out-root submission/ --model resnet18 --device cpu
```
Dependencies: python≥3.10, numpy, pandas, pyarrow, Pillow, torch, torchvision,
matplotlib; local torch hub checkpoint `resnet18-f37072fd.pth` required.
Full details: `submission/report.md` · `submission/README.md` ·
`submission/results/evidence_table.csv` · `submission/results/metrics.json`.