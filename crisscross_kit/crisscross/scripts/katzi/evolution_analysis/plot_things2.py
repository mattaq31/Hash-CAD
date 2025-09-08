import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from pathlib import Path
from scipy.optimize import curve_fit

# ---------- IO ----------
def load_results_pkl(path):
    with open(path, "rb") as f:
        return pickle.load(f)

# ---------- Normalize ONCE ----------
def results_to_df(results):
    rows = []
    for r in results:
        gen = int(r["generation"])
        for m, c in zip(r["match_type"], r["counts"]):
            rows.append((gen, int(m), int(c)))
    return pd.DataFrame(rows, columns=["generation", "match_type", "count"])

# ---------- Views ----------
def as_multiindex_series(df):
    return df.set_index(["match_type", "generation"])["count"]

def as_wide_matrix(df, fill=0):
    return df.pivot_table(index="generation",
                          columns="match_type",
                          values="count",
                          aggfunc="sum",
                          fill_value=fill)

# ---------- Minimal plotting ----------
LINEWIDTH = 3.0
FIGSIZE = (8, 5)

def plot_match_counts_df(df, savepath=None):
    fig, ax = plt.subplots(figsize=FIGSIZE)
    for m, sub in df.groupby("match_type"):
        sub = sub.sort_values("generation")
        ax.plot(sub["generation"], sub["count"],
                "-", linewidth=LINEWIDTH, label=f"{m} Binding Sites")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Generation"); ax.set_ylabel("Occurrences")
    ax.set_title("Elimination of Pairwise Interaction Modes")
    ax.legend(loc="best")
    fig.tight_layout()
    if savepath:
        fig.savefig(savepath, bbox_inches="tight")
    else:
        plt.show()

# ---------- Analytics ----------
def last_nonzero_gen_per_m(df):
    out = {}
    for m, sub in df.groupby("match_type"):
        out[int(m)] = int(sub["generation"].max())
    return out

def alt_score_per_gen_df(df, fudge_dG):
    gens, scores = [], []
    for g, sub in df.groupby("generation"):
        counts = sub["count"].to_numpy(dtype=float)
        mtypes = sub["match_type"].to_numpy(dtype=float)
        avg = np.sum(counts * np.exp(-fudge_dG * mtypes)) / np.sum(counts)
        scores.append(-np.log(avg) / fudge_dG)
        gens.append(g)
    order = np.argsort(gens)
    return np.asarray(gens, float)[order], np.asarray(scores, float)[order]


def decline_of(m, df):
    """
    Return two 1D arrays (generations, counts) for match_type == m,
    starting at the generation where match_type (m+1) disappears.
    """
    last_gens = last_nonzero_gen_per_m(df)   # {m: last gen with count>0}
    decline_start = last_gens[m + 1]

    sub = df[(df["match_type"] == m) & (df["generation"] >= decline_start)]
    sub = sub.sort_values("generation")

    gens = sub["generation"].to_numpy()
    counts = sub["count"].to_numpy()
    return gens, counts


# ---- model (no x0) ----
def stretched_exp(x, A, tau, beta):
    return A * np.exp(-np.power(x / tau, beta))

def fit_decline(m, df, savepath=None):
    """
    Fit decline_of(m, df) with stretched exponential:
        y = A * exp(-(x/tau)^beta)
    space ∈ {"linear","log"}:
    Returns (params, aux, (x, y), model_fn).
    """
    gens, counts = decline_of(m, df)
    x = gens
    y = counts.astype(float)


    p0     = (y[0], max((x.max()+1.0)/5, 1.0), 0.8)
    bounds = ((0.0, 1e-12, 0.01), (np.inf, np.inf, 2.0))
    popt, pcov = curve_fit(stretched_exp, x, y, p0=p0,
                               bounds=bounds, maxfev=200000)
    aux = pcov



    # ---- plotting ----
    fig, ax = plt.subplots(figsize=(8,5))
    ax.scatter(x, y, s=30, color="dodgerblue", label="data")

    x_model = np.linspace(x.min(), x.max(), 100000)
    ax.plot(x_model, stretched_exp(x_model, *popt),
            "-", color="crimson", linewidth=2.5,
            label=f"A={popt[0]:.3g}, τ={popt[1]:.3g}, β={popt[2]:.3g}")

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Generation (shifted)")
    ax.set_ylabel("Count")
    ax.set_title(f"Stretched exponential fit m={m}")
    ax.legend(); plt.tight_layout()

    if savepath:
        plt.savefig(savepath, bbox_inches="tight")
    else:
        plt.show()

    return popt, aux, (x, y), stretched_exp

# ---------- Example main ----------
if __name__ == "__main__":
    p1 = Path(r"D:\Wyss_experiments\Evolution_analysis\evo_run_hexagon_2\evolution_results2.pkl")
    p2 = Path(r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\evolution_runs\katzi_long_term_hexa_evo_renamed1\evolution_results24000_onwards.pkl")
    results = load_results_pkl(p1) + load_results_pkl(p2)

    df = results_to_df(results)

    plot_match_counts_df(df, savepath=r"D:\Wyss_experiments\Evolution_analysis\match_counts_hexagon.pdf")

    last_gen = last_nonzero_gen_per_m(df)
    print("Last nonzero gen per m:", last_gen)

    gens, scores = alt_score_per_gen_df(df, fudge_dG=-15)
    plt.figure(figsize=FIGSIZE)
    plt.plot(gens, scores, "-", linewidth=LINEWIDTH)
    plt.xlabel("Generation"); plt.ylabel("Score")
    plt.title("Mean Pairwise Interaction vs Generation")
    plt.tight_layout()
    plt.savefig(r"D:\Wyss_experiments\Evolution_analysis\score_hexagon_alt_score-15.pdf", bbox_inches="tight")

    last_gen = last_nonzero_gen_per_m(df)
    m = 3
    decline_m = decline_of(m, df)
    print(decline_m)

    # fit in linear space
    params_lin, cov_lin, (x_lin, y_lin), f_lin = fit_decline(3, df)




