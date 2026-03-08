from pathlib import Path

import pandas as pd


name = "short_seq_7mer_sigma1_subset_compare_results.pkl"

path = Path(name)
if path.suffix == ".pkl":
    df = pd.read_pickle(path)
elif path.suffix == ".csv":
    df = pd.read_csv(path)
else:
    raise ValueError(f"Unsupported file extension: {path.suffix}")

print(df.head())
