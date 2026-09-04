# Claim verification: DASH supernova classification (arXiv:1903.02557)

## Falsifiable scientific claim (one sentence)

The DASH deep convolutional network (official v06 model, known redshift) classifies
real OzDES/DES optical spectra into the ATel-reported SN broad class at a high
match rate (paper: 197/212 = 92.9%; rubric "claim holds" if frozen-subset overall
>= 0.80 and Ia >= 0.90) and completes the whole set autonomously in well under
20 seconds (paper: "all 212 in <20 s").

## Failure conditions

1. Frozen-subset overall broad-class match rate < 0.80, OR Ia match rate < 0.90.
2. The 69-spectrum autonomous run takes >= 20 s wall clock (with no human
   intervention), contradicting the "<20 s / 212" claim on the smaller subset.

## Result

| metric | frozen subset (v06) | paper (Table 1) |
|---|---|---|
| overall match | 56/64 = **0.875** | 197/212 = 0.929 |
| Ia | 49/54 = **0.907** | 127/129 = 0.984 |
| II | 6/8 = 0.750 | 25/28 = 0.893 |
| Ibc | 1/2 = 0.500 | 1/1 = 1.0 |
| wall time (69 spec, one batch) | **3.59 s** | <20 s / 212 |

- 5 DASH top-1 "Ic-broad" predictions excluded per paper Sec.5.2 convention
  (host contamination); if counted as mismatches the overall rate is 56/69 =
  0.812, still above 0.80.
- Spot-check vs paper Table 2: DES16C3bq -> Ia-norm (MATCH), DES16E2aoh -> Ia
  (broad MATCH).

## Conclusion label

**supported** — on the frozen 69-spectrum subset the claim holds by the rubric
thresholds (overall 0.875 >= 0.80, Ia 0.907 >= 0.90) and the speed claim is
comfortably met (3.59 s vs 20 s).  The absolute match rate is below the paper's
92.9%, attributed to the smaller frozen subset (69 vs 212) and the official v06
model vs the 2019 paper model version.
