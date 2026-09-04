"""Explore frozen M3 monthly data: counts, lengths, degenerate segments."""
import os
import pandas as pd
import numpy as np

DATA_ROOT = os.environ.get(
    "M3_DATA",
    "/mnt/f/dataset/cs/2103.12057_tsf_experimental_review/tsf",
)
CSV_PATH = os.path.join(DATA_ROOT, "m3_monthly_series.csv")

HORIZON = 18


def main():
    df = pd.read_csv(CSV_PATH)
    print(f"csv rows: {len(df):,}")
    n_series = df["series_id"].nunique()
    print(f"n_series: {n_series}")

    lens = df.groupby("series_id").size()
    print("full length: min", lens.min(), "max", lens.max(), "median", lens.median())

    train_lens = lens - HORIZON
    print("train length: min", train_lens.min(), "max", train_lens.max())

    # degenerate test segments
    test_degen_allzero = []
    test_degen_const = []
    zero_train_any = 0
    for sid, g in df.groupby("series_id"):
        v = g["value"].to_numpy(float)
        t = v[-HORIZON:]
        if np.all(t == 0):
            test_degen_allzero.append(sid)
        elif np.std(t) < 1e-12:
            test_degen_const.append(sid)
        tr = v[:-HORIZON]
        if np.min(tr) == np.max(tr):
            zero_train_any += 1
    print(f"series with test all-zero: {len(test_degen_allzero)}")
    print(f"series with test constant (nonzero): {len(test_degen_const)}")
    print(f"series with constant train segment (min==max): {zero_train_any}")

    # support for past_history windows
    for ph in (22, 36, 54):
        need_train = ph + HORIZON
        ok = train_lens.ge(ph).sum()
        ok_full = train_lens.ge(need_train).sum()
        print(f"ph={ph}: series with len_train>=ph: {ok}; len_train>=ph+horizon {need_train}: {ok_full}")

    # distribution of train lengths
    hist = train_lens.value_counts().sort_index()
    print(pd.DataFrame({"train_len": hist.index, "count": hist.values}).to_string(index=False))


if __name__ == "__main__":
    main()