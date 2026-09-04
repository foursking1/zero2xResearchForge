# Scratch results log (working notes)

## Baseline with-prior 3-fold means (confirmed 2026-08-14 ~19:00)

### creditcard
- lambdamart: F1 mean 0.9712  (0.9722, 0.9760, 0.9654) | loss mean 67,870.79
- lgbm:       F1 mean 0.9718  (0.9731, 0.9734, 0.9690) | loss mean 63,995.33
- xgb:        F1 mean 0.9662  (0.9678, 0.9663, 0.9645) | loss mean 78,296.67
- rf:         F1 mean 0.9659  (0.9678, 0.9672, 0.9627) | loss mean 78,136.66

### jobprofit
- lambdamart: F1 mean 0.8788  (0.8918, 0.8918, 0.8529) | loss mean 36,615.97
- lgbm:       F1 mean 0.9058  (0.9278, 0.8737, 0.9159) | loss mean 28,224.56
- xgb:        F1 mean 0.9109  (0.9459, 0.8918, 0.8949) | loss mean 25,357.83
- rf:         F1 mean 0.8858  (0.9098, 0.8737, 0.8739) | loss mean 34,330.80

## Paper anchors (with-prior 3-fold mean)
- creditcard: PA-RiskRanker F1=0.9870 loss=31,368.39 | RankFormer F1=0.9820
- jobprofit:  PA-RiskRanker F1=0.9491 loss=19,363.32 | RankFormer F1=0.8539

## Fold stats (group_size=100)
- creditcard test: 56,900 rows, 559/569/556 pos per fold1/2/3; with-prior predicts 569
- jobprofit test:  2,800 rows, 28/28/20 pos per fold1/2/3; with-prior predicts 28
  - fold3 jobprofit ceiling: max sens 20/28, macro-F1 ceiling ~0.916

## Transformer runs (status)
- graph test (PID 14600): jobprofit fold1 graph pre100 freeze maxE40 pat12 — running, ~1145s CPU (pretrain near done)
- creditcard tr (PID 20220): creditcard fold1-3 pabce+rankformer pre5 frac0.25 maxE4 pat2 — running, ~1239s CPU
- jobprofit tr (PID 15260): jobprofit fold1-3 pabce(maxE200 pat40)+rankformer(maxE100 pat20) — just relaunched after kill of maxE60 run
- jobprofit pabce fold1 OLD loss pre100 freeze maxE40: F1=0.8557 loss=42,267.91 auc=0.9958 sens=0.7143

## Decisions
- pabce (PA-BCE γ=2, per-list mean) = primary PA-RiskRanker loss; graph = experimental (reference default, underperformed with undertrained embedder)
- freeze embedder (fine-tune degraded fold1 F1 0.820 vs 0.856)
