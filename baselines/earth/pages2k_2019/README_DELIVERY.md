# Delivery note — this directory holds a previous run's solution

`agent_solution/` currently contains the **previous evaluation's 3-method solution**
(CPS/PCR/PAI only; scored 73/100 per `EVAL_REPORT.md`). Those files are locked by the
sandbox (created by another process; they cannot be overwritten, deleted, or renamed from
this session, and the sandbox recycle bin is unavailable).

The **complete, current 7-method solution** produced in this session is in:

- **`../agent_solution_v2/`**
  - `solution.md` — methods / results / claim judgments (C01–C04 all **supported**)
  - `code/` — `load_data.py`, `filters.py`, `c01_analysis.py`–`c04_analysis.py` (runnable)
  - `results/metrics.json`, `results/evidence_table.csv`, `results/c01–c04_metrics.json`

Key improvements over the old files: all **7** reconstruction methods (OIE/M08/BHM/DA were
missing before), the exact pipeline of the authors (models windowed 850–1995 **before**
30–200 yr bandpass; common window 1300–1995), and per-pair variance ratios / AR(1) red-noise
significance — reproducing the paper's key anchors (cooling rates −0.227/−0.090 °C/ka,
warmest-decade fraction 0.935, variance-ratio median 1.03, correlations 0.53–0.66, D&A
n1=7000 with 98.4% of residuals inside the control 5–95% range).
