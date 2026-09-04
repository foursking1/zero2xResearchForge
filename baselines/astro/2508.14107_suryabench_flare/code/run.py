"""
SuryaBench DS4 太阳耀斑 24h 二分类预测 —— 端到端再发现分析 (leak-free)
========================================================================
任务: 基于 GOES 派生标签序列(仅标量, 无 SDO 影像), 预测未来 24h 窗口内
是否发生 >=M1.0 耀斑 (label_max), 并评估该技能在未见时段
(2020-2024, 太阳活动周25上升期) 是否保持(跨周期泛化).

数据铁律:
  - 只用 data/ 内冻结真实数据, 所有数字由本脚本从冻结数据重算.
  - 预测窗口 t 的特征只能用严格早于 t 的历史信息.
  - 关键口径: 行 ts 的 label_max 描述窗口 [ts, ts+24h). 在预测时刻 t,
    窗口 [t', t'+24h) 只有在 t'+24h <= t (即 t' <= t-24) 时才已完全结束、
    其标签才可知. 因此主特征全部基于 shift(24) 及更早(已完全结束的窗口);
    shift(1) 系窗口与目标窗口重叠 23h, 属未来泄漏, 仅作"泄漏参照"量化.

输出 (写入 agent_solution/results/):
  - evidence_table.csv  逐期证据表 (period,n,base_rate,threshold,tp,fp,tn,fn,tss,hss)
  - metrics.json        总体指标
  - figure.svg / figure.png  关键图 (分年 TSS vs base rate + 阈值敏感性)

运行: python code/run.py   (工作目录任意, 自动定位 data/)
依赖: python>=3.9, numpy, pandas, scikit-learn, matplotlib
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------------
# 0. 路径与常量
# ----------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
SOLUTION_DIR = os.path.dirname(HERE)                 # agent_solution/
TASK_DIR = os.path.dirname(SOLUTION_DIR)             # 任务根目录 (含 data/)
DATA_DIR = os.path.join(TASK_DIR, "data")
RESULT_DIR = os.path.join(SOLUTION_DIR, "results")
os.makedirs(RESULT_DIR, exist_ok=True)

RANDOM_STATE = 42
M1_LEVEL = 1e-5                                      # M1.0 峰值通量 W/m^2
SPLIT_NAMES = ["train", "validation", "test", "leaky_validation"]


# ----------------------------------------------------------------------------
# 1. 数据加载与自洽性校验
# ----------------------------------------------------------------------------

def goes_to_flux(s):
    """GOES 级别字符串 -> 峰值通量数值 (W/m^2). FQ(无>=C级) 记 0."""
    s = str(s).strip().upper()
    if s in ("FQ", "NAN", "NONE", ""):
        return 0.0
    letter = s[0]
    num = float(s[1:])
    scale = {"A": 1e-8, "B": 1e-7, "C": 1e-6, "M": 1e-5, "X": 1e-4}.get(letter)
    if scale is None:
        raise ValueError(f"未知 GOES 级别: {s!r}")
    return scale * num


def load_all():
    """加载四分裂 + 全量, 校验标签自洽与拼接一致性."""
    splits = {name: pd.read_csv(os.path.join(DATA_DIR, f"{name}.csv"),
                                parse_dates=["timestamp"])
              for name in SPLIT_NAMES}
    full = pd.read_csv(os.path.join(DATA_DIR, "data.csv"),
                       parse_dates=["timestamp"])

    checks = {"total_rows_full": int(len(full)),
              "splits_sum": int(sum(len(v) for v in splits.values()))}
    for name, df in splits.items():
        flux = df["max_goes_class"].map(goes_to_flux)
        rec_max = (flux >= M1_LEVEL).astype(int)
        rec_cum = (df["cumulative_index"] >= 10.0).astype(int)
        ok_max = bool((rec_max == df["label_max"]).all())
        ok_cum = bool((rec_cum == df["label_cum"]).all())
        checks[f"label_max_consistent_{name}"] = ok_max
        checks[f"label_cum_consistent_{name}"] = ok_cum
        assert ok_max and ok_cum, f"{name}: 标签自洽校验失败"

    concat = pd.concat(splits.values(), ignore_index=True)
    concat = concat.sort_values("timestamp").reset_index(drop=True)
    full_s = full.sort_values("timestamp").reset_index(drop=True)
    checks["concat_equals_data"] = bool(
        len(concat) == len(full_s)
        and (concat["timestamp"].values == full_s["timestamp"].values).all()
        and (concat["label_max"].values == full_s["label_max"].values).all())
    assert checks["concat_equals_data"]
    return splits, full, checks


# ----------------------------------------------------------------------------
# 2. 特征工程 (严格滞后, 无未来泄漏)
# ----------------------------------------------------------------------------

def build_features(master):
    """在完整时间轴上构造特征. master 按时间升序每小时一行.

    行 ts 的 label_max 描述窗口 [ts, ts+24h). 预测时刻 t 时, 只有起点
    <= t-24 的窗口(已完全结束)的标签才可用. 因此所有 'prev' 特征以
    shift(24) 为基准, 绝不触碰 shift(1)..shift(23) 的未结束窗口信息.
    """
    df = master.sort_values("timestamp").reset_index(drop=True).copy()
    lm = df["label_max"].astype(float)
    cum = df["cumulative_index"].astype(float)
    fl = df["max_goes_class"].map(goes_to_flux).astype(float)
    df["flux"] = fl

    # ---- A. 主特征: 已完全结束的过去窗口 (start <= t-24) ----
    # 每个滚动特征要求完整窗口历史 (min_periods=窗口长度), 保证 warm-up 干净可报告.
    df["lag24_lm"] = lm.shift(24)                      # 窗口 [t-24,t) 是否有 M+
    df["lag24_cum"] = cum.shift(24)                    # 该窗口累积指数
    df["lag24_flux"] = fl.shift(24)                    # 该窗口峰值通量
    df["nM_prev_1d"] = lm.shift(24).rolling(24, min_periods=24).sum()    # [t-48,t)
    df["nM_prev_3d"] = lm.shift(24).rolling(72, min_periods=72).sum()    # [t-96,t)
    df["nM_prev_7d"] = lm.shift(24).rolling(168, min_periods=168).sum()  # [t-192,t)
    df["nM_prev_14d"] = lm.shift(24).rolling(336, min_periods=336).sum()  # [t-360,t)
    df["nM_prev_30d"] = lm.shift(24).rolling(720, min_periods=720).sum()  # [t-744,t)
    df["cum_prev_3d"] = cum.shift(24).rolling(72, min_periods=72).sum()
    df["cum_prev_7d"] = cum.shift(24).rolling(168, min_periods=168).sum()
    df["cum_prev_30d"] = cum.shift(24).rolling(720, min_periods=720).sum()
    df["fluxmax_prev_3d"] = fl.shift(24).rolling(72, min_periods=72).max()
    df["fluxmax_prev_7d"] = fl.shift(24).rolling(168, min_periods=168).max()
    df["nFQ_prev_7d"] = (fl.shift(24) <= 0).rolling(168, min_periods=168).sum()
    # 活动度梯度: 近3天 M+ 数 - 再往前4天 M+ 数
    df["nM_trend"] = (lm.shift(24).rolling(72, min_periods=72).sum()
                      - lm.shift(24).rolling(96, min_periods=96).sum())

    # ---- B. 日历特征 (预测时刻已知; 供漂移分解) ----
    ts = df["timestamp"]
    hour = ts.dt.hour + ts.dt.minute / 60.0
    doy = ts.dt.dayofyear
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    df["year_c"] = (ts.dt.year - 2010).astype(float)

    # ---- C. 泄漏参照特征 (shift(1): 窗口与目标重叠 23h, 仅用于量化泄漏) ----
    df["lag1_lm"] = lm.shift(1)
    df["lag1_cum"] = cum.shift(1)
    df["lag1_flux"] = fl.shift(1)
    df["nM_leaky_3d"] = lm.shift(1).rolling(72, min_periods=1).sum()
    df["nM_leaky_7d"] = lm.shift(1).rolling(168, min_periods=1).sum()
    df["cum_leaky_7d"] = cum.shift(1).rolling(168, min_periods=1).sum()
    df["fluxmax_leaky_3d"] = fl.shift(1).rolling(72, min_periods=1).max()

    return df


# 特征组定义
FEATS_HIST = ["lag24_lm", "lag24_cum", "lag24_flux",
              "nM_prev_1d", "nM_prev_3d", "nM_prev_7d", "nM_prev_14d",
              "nM_prev_30d", "cum_prev_3d", "cum_prev_7d", "cum_prev_30d",
              "fluxmax_prev_3d", "fluxmax_prev_7d", "nFQ_prev_7d", "nM_trend",
              "hour_sin", "hour_cos", "doy_sin", "doy_cos", "year_c"]
FEATS_HIST_NOYEAR = [f for f in FEATS_HIST if f != "year_c"]
FEATS_SNAPSHOT = ["lag24_lm", "lag24_cum", "lag24_flux",
                  "hour_sin", "hour_cos", "doy_sin", "doy_cos", "year_c"]
FEATS_CAL = ["hour_sin", "hour_cos", "doy_sin", "doy_cos", "year_c"]
FEATS_LEAKY = ["lag1_lm", "lag1_cum", "lag1_flux",
               "nM_leaky_3d", "nM_leaky_7d", "cum_leaky_7d", "fluxmax_leaky_3d",
               "hour_sin", "hour_cos", "doy_sin", "doy_cos", "year_c"]


# ----------------------------------------------------------------------------
# 3. 指标
# ----------------------------------------------------------------------------

def tss_from_counts(tp, fp, tn, fn):
    tpr = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    fpr = fp / (fp + tn) if (fp + tn) > 0 else np.nan
    return tpr - fpr


def hss_from_counts(tp, fp, tn, fn):
    """Heidke Skill Score (2x2)."""
    denom = (tp + fn) * (fn + tn) + (tp + fp) * (fp + tn)
    if denom == 0:
        return np.nan
    return 2.0 * (tp * tn - fp * fn) / denom


def confusion_at_threshold(y_true, proba, thr):
    pred = (proba >= thr).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    tn = int(((pred == 0) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    return tp, fp, tn, fn


def metrics_at_threshold(y_true, proba, thr):
    tp, fp, tn, fn = confusion_at_threshold(y_true, proba, thr)
    return {
        "threshold": float(thr),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "tss": tss_from_counts(tp, fp, tn, fn),
        "hss": hss_from_counts(tp, fp, tn, fn),
        "f1": (2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else np.nan,
        # CSI / 临界成功指数 (论文锚中的 CSS 语义)
        "css": (tp / (tp + fp + fn)) if (tp + fp + fn) else np.nan,
    }


def best_threshold_on_validation(y_val, p_val, grid=None):
    if grid is None:
        grid = np.round(np.arange(0.01, 1.0, 0.01), 3)
    best_t, best_tss = None, -np.inf
    for thr in grid:
        m = metrics_at_threshold(y_val, p_val, thr)
        if m["tss"] > best_tss:
            best_tss, best_t = m["tss"], float(thr)
    return best_t, best_tss


def bootstrap_tss_ci(y, p, thr, n_boot=1000, seed=RANDOM_STATE):
    """对 test 行做 Bootstrap 重采样, 返回 TSS 95% 置信区间."""
    rng = np.random.default_rng(seed)
    n = len(y)
    idx = np.arange(n)
    vals = np.empty(n_boot)
    for i in range(n_boot):
        b = rng.choice(idx, size=n, replace=True)
        tp = int(((p[b] >= thr) & (y[b] == 1)).sum())
        fp = int(((p[b] >= thr) & (y[b] == 0)).sum())
        tn = int(((p[b] < thr) & (y[b] == 0)).sum())
        fn = int(((p[b] < thr) & (y[b] == 1)).sum())
        vals[i] = tss_from_counts(tp, fp, tn, fn)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


# ----------------------------------------------------------------------------
# 4. 主流程
# ----------------------------------------------------------------------------

def main():
    print("== 1/8 加载冻结数据与自洽性校验 ==")
    splits, full, checks = load_all()
    for k, v in checks.items():
        print(f"   {k}: {v}")

    master = full.copy()
    mem = pd.concat([v[["timestamp"]].assign(split=n)
                     for n, v in splits.items()], ignore_index=True)
    master = master.merge(mem, on="timestamp", how="left", validate="1:1")
    assert master["split"].notna().all(), "存在不属于任一 split 的行"

    # 基础口径统计
    stats = {}
    for s in SPLIT_NAMES:
        sub = master[master.split == s]
        stats[s] = {"n": int(len(sub)), "pos": int(sub.label_max.sum()),
                    "base_rate": float(sub.label_max.mean())}
    stats["full"] = {"n": int(len(master)), "pos": int(master.label_max.sum()),
                     "base_rate": float(master.label_max.mean())}
    drift = stats["test"]["base_rate"] - stats["train"]["base_rate"]
    print(f"train base_rate={stats['train']['base_rate']:.4f}  "
          f"test base_rate={stats['test']['base_rate']:.4f}  drift={drift:+.4f}")

    t = master[master.split == "test"].copy()
    t["year"] = t.timestamp.dt.year
    yearly_br = t.groupby("year")["label_max"].agg(["size", "mean"]).reset_index()
    yearly_br.columns = ["year", "n", "base_rate"]
    print("分年 test base rate:")
    print(yearly_br.to_string(index=False))

    print("== 2/8 特征工程 ==")
    mf = build_features(master)

    # warm-up: 需要 30 天完整"已完成窗口"历史 (shift(24) + rolling 720),
    # 故最早的 743 行 (30 天 + 23h) 无完整特征, 全部落在 train 期.
    warmup_mask = mf[FEATS_HIST].isna().any(axis=1)
    n_dropped = int(warmup_mask.sum())
    dropped_split = master.loc[warmup_mask, "split"].value_counts().to_dict()
    print(f"warm-up: 丢弃 {n_dropped} 行 (缺完整30天已完成窗口历史); 分布 {dropped_split}")

    data = {s: mf[(mf.split == s) & (~warmup_mask)].copy()
            for s in SPLIT_NAMES}
    for s in SPLIT_NAMES:
        data[s]["year"] = data[s].timestamp.dt.year
        print(f"   {s}: n={len(data[s])}  base_rate="
              f"{data[s].label_max.mean():.4f}")

    print("== 3/8 训练模型 ==")
    train_df = data["train"]
    models = {}

    def fit_lr(feats, name):
        X = train_df[feats].values
        y = train_df["label_max"].values
        sc = StandardScaler().fit(X)
        lr = LogisticRegression(class_weight="balanced", C=1.0, max_iter=3000,
                                random_state=RANDOM_STATE)
        lr.fit(sc.transform(X), y)
        auc = roc_auc_score(y, lr.predict_proba(sc.transform(X))[:, 1])
        models[name] = (lr, sc, feats, "logreg")
        print(f"   {name}: 特征数={len(feats)} train AUC={auc:.4f}")

    fit_lr(FEATS_HIST, "lr_hist")
    fit_lr(FEATS_HIST_NOYEAR, "lr_hist_noyear")
    fit_lr(FEATS_SNAPSHOT, "lr_snapshot")
    fit_lr(FEATS_CAL, "lr_cal")
    fit_lr(FEATS_LEAKY, "lr_leaky")

    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5,
                                class_weight="balanced", n_jobs=-1,
                                random_state=RANDOM_STATE)
    rf.fit(train_df[FEATS_HIST].values, train_df["label_max"].values)
    models["rf_hist"] = (rf, None, FEATS_HIST, "randomforest")
    print(f"   rf_hist: train AUC="
          f"{roc_auc_score(train_df['label_max'], rf.predict_proba(train_df[FEATS_HIST].values)[:,1]):.4f}")

    print("== 4/8 阈值选择 (validation 上最大化 TSS) ==")
    grid = np.round(np.arange(0.01, 1.0, 0.01), 3)
    model_results = {}
    for name, (model, sc, feats, _) in models.items():
        preds = {}
        for s in SPLIT_NAMES:
            sub = data[s]
            Xs = sc.transform(sub[feats].values) if sc is not None else sub[feats].values
            preds[s] = model.predict_proba(Xs)[:, 1]
        best_t, best_val_tss = best_threshold_on_validation(
            data["validation"]["label_max"].values, preds["validation"], grid)
        model_results[name] = {"preds": preds, "best_thr": best_t,
                               "val_tss": best_val_tss}
        print(f"   {name}: 最优阈值(validation)={best_t:.3f} val TSS={best_val_tss:.4f}")

    print("== 5/8 证据表 ==")
    mr = model_results["lr_hist"]
    thr = mr["best_thr"]

    rows = []
    for s in SPLIT_NAMES:
        y = data[s]["label_max"].values
        p = mr["preds"][s]
        m = metrics_at_threshold(y, p, thr)
        rows.append({"period": s, "n": int(len(y)),
                     "base_rate": float(y.mean()), "threshold": thr,
                     "tp": m["tp"], "fp": m["fp"], "tn": m["tn"], "fn": m["fn"],
                     "tss": m["tss"], "hss": m["hss"]})

    # 分年 test (数据按时间升序, preds 同序 -> 位置对齐)
    test_df = data["test"]
    test_ts = test_df["timestamp"].values
    test_y = test_df["label_max"].values
    test_p = mr["preds"]["test"]
    yearly_test_rows = []
    for yr, sub in test_df.groupby("year"):
        pos = np.searchsorted(test_ts, sub["timestamp"].values)
        m = metrics_at_threshold(test_y[pos], test_p[pos], thr)
        rows.append({"period": f"test_{int(yr)}", "n": int(len(sub)),
                     "base_rate": float(sub["label_max"].mean()), "threshold": thr,
                     "tp": m["tp"], "fp": m["fp"], "tn": m["tn"], "fn": m["fn"],
                     "tss": m["tss"], "hss": m["hss"]})
        yearly_test_rows.append({"year": int(yr), "n": int(len(sub)),
                                 "base_rate": float(sub["label_max"].mean()),
                                 "tss_at_fixed_thr": m["tss"],
                                 "hss_at_fixed_thr": m["hss"],
                                 "roc_auc": float(roc_auc_score(
                                     test_y[pos], test_p[pos]))})
    yearly_test_df = pd.DataFrame(yearly_test_rows)

    ev = pd.DataFrame(rows)[["period", "n", "base_rate", "threshold",
                             "tp", "fp", "tn", "fn", "tss", "hss"]]
    ev.to_csv(os.path.join(RESULT_DIR, "evidence_table.csv"), index=False)
    print(ev.round(4).to_string(index=False))

    print("== 6/8 阈值敏感性 + Bootstrap 不确定区间 (test) ==")
    sens = []
    for thr2 in np.round(np.arange(0.01, 1.0, 0.01), 3):
        m = metrics_at_threshold(test_y, test_p, thr2)
        sens.append({"threshold": thr2, "tss": m["tss"], "hss": m["hss"]})
    sens_df = pd.DataFrame(sens)
    tss_env = (float(sens_df.tss.min()), float(sens_df.tss.max()))
    tss_at_br = float(sens_df.iloc[np.argmin(
        np.abs(sens_df.threshold - stats["test"]["base_rate"]))]["tss"])

    test_m = metrics_at_threshold(test_y, test_p, thr)
    ci = bootstrap_tss_ci(test_y, test_p, thr)
    print(f"test TSS={test_m['tss']:.4f} (95% CI [{ci[0]:.4f}, {ci[1]:.4f}])  "
          f"HSS={test_m['hss']:.4f}  AUC={roc_auc_score(test_y, test_p):.4f}")
    print(f"阈值扫描 TSS 范围 [{tss_env[0]:.4f}, {tss_env[1]:.4f}];  "
          f"base-rate 阈值处 TSS={tss_at_br:.4f}")

    print("== 7/8 漂移分解 ==")
    year_rows = ev[ev.period.str.startswith("test_")]
    agg_tss = test_m["tss"]
    mean_year_tss = float(year_rows.tss.mean())
    # 分年 TSS 按正样本数加权 (等价于在各年内部预测的聚合)
    w_year_tss = float((year_rows.tss * year_rows.n).sum() / year_rows.n.sum())
    mean_year_auc = float(yearly_test_df["roc_auc"].mean())
    # 无 year 特征模型: 剔除漂移捕获通道后的技能
    noyear_test = metrics_at_threshold(
        test_y, model_results["lr_hist_noyear"]["preds"]["test"],
        model_results["lr_hist_noyear"]["best_thr"])
    cal_test = metrics_at_threshold(
        test_y, model_results["lr_cal"]["preds"]["test"],
        model_results["lr_cal"]["best_thr"])
    print(f"聚合 test TSS={agg_tss:.4f}  分年TSS均值={mean_year_tss:.4f}  "
          f"加权分年均值={w_year_tss:.4f}  分年AUC均值={mean_year_auc:.4f}")
    print(f"无year模型 test TSS={noyear_test['tss']:.4f}  "
          f"仅日历模型 test TSS={cal_test['tss']:.4f}")
    print(yearly_test_df.round(4).to_string(index=False))

    print("== 8/8 汇总 JSON + 图 ==")
    metrics = {
        "task": "24h M1.0+ solar flare binary forecast (SuryaBench DS4 label_max)",
        "target": "label_max (window max >= M1.0)",
        "data_checks": checks,
        "base_rates": {s: {"n": stats[s]["n"], "pos": stats[s]["pos"],
                           "base_rate": stats[s]["base_rate"]}
                       for s in SPLIT_NAMES + ["full"]},
        "drift_test_minus_train": drift,
        "yearly_test_base_rate": yearly_br.set_index("year")["base_rate"].to_dict(),
        "primary_model": ("LogisticRegression(class_weight=balanced) on strictly "
                          "past completed windows (shift>=24) + calendar"),
        "threshold_selection": f"maximize TSS on official validation split; thr={thr:.3f}",
        "warmup": {
            "dropped_rows": n_dropped,
            "dropped_by_split": {k: int(v) for k, v in dropped_split.items()},
            "reason": "first ~30 days lack full completed-window history for "
                      "30-day lag features; all dropped rows are in the train period",
        },
        "main": {
            "period": "test",
            "n": stats["test"]["n"],
            "base_rate": stats["test"]["base_rate"],
            "threshold": thr,
            "tp": test_m["tp"], "fp": test_m["fp"],
            "tn": test_m["tn"], "fn": test_m["fn"],
            "tss": test_m["tss"], "hss": test_m["hss"],
            "f1": test_m["f1"], "css": test_m["css"],
            "tss_95ci_bootstrap": ci,
            "roc_auc": float(roc_auc_score(test_y, test_p)),
        },
        "threshold_sensitivity": {
            "scan_grid": "0.01..0.99 step 0.01",
            "tss_min": tss_env[0], "tss_max": tss_env[1],
            "tss_at_base_rate_threshold": tss_at_br,
        },
        "drift_decomposition": {
            "aggregate_test_tss": agg_tss,
            "mean_within_year_tss": mean_year_tss,
            "n_weighted_within_year_tss": w_year_tss,
            "mean_within_year_roc_auc": mean_year_auc,
            "skill_attributable_to_between_year_drift": agg_tss - mean_year_tss,
            "hist_no_year_model_test_tss": noyear_test["tss"],
            "calendar_only_model_test_tss": cal_test["tss"],
            "comment": ("aggregate TSS - mean within-year TSS = the component of "
                        "skill that comes from discriminating activity levels "
                        "between years (base-rate drift); within-year TSS/ROC-AUC "
                        "measure the skill inside a fixed activity regime (AUC is "
                        "threshold-free and reveals ranking skill that fixed-"
                        "threshold TSS under-reports in drifted regimes)"),
        },
        "yearly_test": yearly_test_df.to_dict(orient="records"),
        "robustness": {},
    }

    for mname in ["lr_snapshot", "lr_hist_noyear", "lr_cal", "lr_leaky", "rf_hist"]:
        mr2 = model_results[mname]
        m2 = metrics_at_threshold(test_y, mr2["preds"]["test"], mr2["best_thr"])
        metrics["robustness"][mname] = {
            "test_tss": m2["tss"], "test_hss": m2["hss"],
            "threshold": mr2["best_thr"],
            "roc_auc": float(roc_auc_score(test_y, mr2["preds"]["test"])),
            "note": ("leaky reference uses shift(1) windows overlapping the target "
                     "window (23h future info); reported only to quantify leakage"
                     if mname == "lr_leaky" else ""),
        }

    with open(os.path.join(RESULT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2, default=str)
    print("metrics.json 已写入")

    # ---- 图: 双面板 (matplotlib 缺失时跳过, 不影响核心结果) ----
    try:
        fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))

        # 面板1: 分年 test TSS / AUC 与 base rate
        ax = axes[0]
        yy = year_rows.copy()
        yy["year"] = yy.period.str.split("_").str[-1].astype(int)
        yy = yy.sort_values("year")
        ytd = yearly_test_df.set_index("year").sort_index()
        ax.bar(yy["year"] - 0.2, yy["tss"], width=0.4, color="#1f77b4",
               label="TSS (fixed threshold, within-year)")
        ax.plot(ytd.index, ytd["roc_auc"], "o-", color="#2ca02c",
                label="ROC-AUC (within-year)")
        ax2 = ax.twinx()
        ax2.plot(yearly_br["year"], yearly_br["base_rate"], "s--", color="#d62728",
                 label="test base rate")
        ax2.set_ylabel("base rate", color="#d62728")
        ax2.tick_params(axis="y", labelcolor="#d62728")
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_xlabel("Year (test period 2020-2024)")
        ax.set_ylabel("TSS / ROC-AUC")
        ax.set_title("Per-year test skill and base rate, official split\n"
                     "(leak-free LR at validation-tuned threshold)")
        lines = ax.get_lines() + ax2.get_lines()
        ax.legend(lines, [l.get_label() for l in lines], loc="lower left", fontsize=8)
        ax.set_ylim(-0.05, 1.05)
        ax2.set_ylim(-0.05, 1.05)

        # 面板2: 阈值敏感性 (test TSS)
        ax = axes[1]
        ax.plot(sens_df.threshold, sens_df.tss, "-", color="#2ca02c")
        ax.axvline(thr, color="black", ls="--", lw=1,
                   label=f"validation-tuned thr={thr:.2f}")
        ax.axvline(stats["test"]["base_rate"], color="#d62728", ls=":",
                   label=f"test base rate={stats['test']['base_rate']:.2f}")
        ax.axhline(0, color="grey", lw=0.8)
        ax.set_xlabel("Decision threshold")
        ax.set_ylabel("Test TSS")
        ax.set_title("Threshold sensitivity of test TSS\n"
                     f"(TSS envelope [{tss_env[0]:.2f}, {tss_env[1]:.2f}])")
        ax.legend(fontsize=8)

        fig.tight_layout()
        fig.savefig(os.path.join(RESULT_DIR, "figure.svg"))
        fig.savefig(os.path.join(RESULT_DIR, "figure.png"), dpi=150)
        plt.close(fig)
    except Exception as _e:  # matplotlib 不可用时跳过绘图
        print(f"[warning] figure skipped: {_e}")
    print("完成。结果已写入", RESULT_DIR)


if __name__ == "__main__":
    main()
