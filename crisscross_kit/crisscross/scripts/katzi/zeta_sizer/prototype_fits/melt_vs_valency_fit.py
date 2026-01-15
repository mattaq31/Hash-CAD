import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, multirule_precise_hamming, oneshot_hamming_compute,extract_handle_dicts
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import read_handle_log as rhl
import numpy as np
from crisscross.scripts.katzi.evolution_analysis.analyse_evo import intuitive_score as in_sc
import matplotlib.pyplot as plt
from math import factorial
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext


# ============================================================
# USER SETTINGS
# ============================================================

T_MAX_FIT = 2000000.0  # µs

# design files (Zenodo)
DESIGN_FILES = {
    "H24": r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH24.xlsx",
    "H29": r"C:\Users\Flori\Dropbox\CrissCross\Papers\hash_cad\exp1_hamming_distance\design_and_echo\Exports\full_designH29.xlsx",
}

def get_counts_in_dict(file_location):
    slat_len = 32
    megastructure = Megastructure(import_design_file=file_location)
    slat_array = megastructure.generate_slat_occupancy_grid()
    handle_array = megastructure.generate_assembly_handle_grid()
    handle_dict, antihandle_dict = extract_handle_dicts(handle_array, slat_array)
    hamming_results = oneshot_hamming_compute(handle_dict, antihandle_dict, slat_len)

    matches = -(hamming_results - slat_len)
    flat_matches = matches.flatten()
    score = in_sc(flat_matches)

    match_type, counts = np.unique(flat_matches, return_counts=True)

    results = [{
        "generation": 1,
        "match_type": match_type,
        "counts": counts,
        "score": score,
    }]
    return results

# ============================================================
# LOAD P(n) FROM DESIGN FILE
# ============================================================

def load_Pn_from_design(path):
    r_table = get_counts_in_dict(path)
    r_1 = r_table[0]

    counts = r_1["counts"][1:]        # drop n=0
    match_types = r_1["match_type"][1:]
    counts[0]= counts[0]*0.3
    counts[1] = counts[1] * 0.5
    Pn = counts / np.sum(counts)
    return np.asarray(match_types, float), np.asarray(Pn, float)

Pn_data = {
    sample: load_Pn_from_design(path)
    for sample, path in DESIGN_FILES.items()
}

# ============================================================
# MIXTURE MODEL
# ============================================================

def make_g2_mixture_from_Pn(match_types, Pn):
    n_vals = np.asarray(match_types, dtype=float)
    Pn = np.asarray(Pn, dtype=float)
    Pn = Pn / np.sum(Pn)

    def g2_model(t, beta, tau0, a):
        t = np.asarray(t, dtype=float)

        # NOTE: sign convention chosen by you
        en = np.exp(a * n_vals)                     # exp(+a n)
        arg = -(t[:, None] / tau0) * en[None, :]    # -(t/tau0) * exp(+a n)

        g1 = np.sum(Pn[None, :] * np.exp(arg), axis=1)
        return beta * g1**2

    return g2_model


def make_g2_mixture_from_Pn2(match_types, Pn, tau_fast=120.0, f_fast=0.1):
    """
    Discrete network mixture + fixed fast exponential (free particles).

    Parameters (fixed, NOT fitted):
        tau_fast : fast relaxation time (µs)
        f_fast   : fraction of free particles in g1
    """
    n_vals = np.asarray(match_types, dtype=float)
    Pn = np.asarray(Pn, dtype=float)
    Pn = Pn / np.sum(Pn)

    def g2_model(t, beta, tau0, a):
        t = np.asarray(t, dtype=float)

        # --- fast (free) mode in g1 ---
        g1_fast = np.exp(-t / tau_fast)

        # --- network mixture in g1 ---
        en = np.exp(a * n_vals)
        arg = -(t[:, None] / tau0) * en[None, :]
        g1_net = np.sum(Pn[None, :] * np.exp(arg), axis=1)

        # --- combined g1 ---
        g1 = f_fast * g1_fast + (1.0 - f_fast) * g1_net

        return beta * g1**2

    return g2_model


def load_melt_file_malvern(path):
    rows = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue

            toks = [t.strip() for t in line.split("\t") if t.strip()]

            # skip header / short lines like "H24   H24"
            if len(toks) < 6:
                continue

            sample_id = toks[0]

            # temperature must parse
            try:
                T = float(toks[1])
            except ValueError:
                continue

            # Find where sample_id repeats (separator between delays and correlations)
            # In your file it repeats exactly, e.g. "H24 1" appears twice.
            try:
                sep = toks.index(sample_id, 2)
            except ValueError as e:
                raise RuntimeError(
                    f"Could not find repeated sample token '{sample_id}' in row starting: {toks[:5]}"
                ) from e

            delays = np.array(toks[2:sep], dtype=float)
            corrs  = np.array(toks[sep+1:], dtype=float)

            if len(delays) != len(corrs):
                raise RuntimeError(
                    f"Length mismatch for {sample_id} at {T}°C: "
                    f"{len(delays)} delays vs {len(corrs)} corrs"
                )

            sample_base = sample_id.split()[0]  # "H24" or "h29"
            # optional: normalize case so you don't get H29 vs h29 split
            sample_base = sample_base.upper()

            for d, c in zip(delays, corrs):
                rows.append({
                    "sample_base": sample_base,
                    "sample_id": sample_id,
                    "temperature_C": T,
                    "delay_us": d,
                    "correlation": c
                })

    return pd.DataFrame(rows)


# ============================================================
# FIT MIXTURE MODEL
# ============================================================

PATH = r"D:\Wyss_experiments\random_shihlab_stuff\in_wiki\Katzi020\data_and_plots\melt_h24_h29_better_exp.txt"

df = load_melt_file_malvern(PATH)

fit_rows = []
failed = []

for (sample_base, T), g in df.groupby(["sample_base", "temperature_C"]):

    if sample_base not in Pn_data:
        continue

    match_types, Pn = Pn_data[sample_base]
    g2_mixture = make_g2_mixture_from_Pn(match_types, Pn)

    t = g["delay_us"].values
    y = g["correlation"].values

    m = (y > 0) & (t <= T_MAX_FIT)
    t = t[m]
    y = y[m]

    try:
        p0 = [
            float(np.max(y)),      # beta
            float(np.median(t)),   # tau0
            0.5                    # a
        ]

        bounds = (
            [0.0, 1e-9, -20],
            [2.0, np.inf, np.inf]
        )

        popt, _ = curve_fit(
            g2_mixture,
            t, y,
            p0=p0,
            bounds=bounds,
            maxfev=200000
        )

        beta, tau0, a = popt

    except Exception as e:
        failed.append((sample_base, T, str(e)))
        continue

    fit_rows.append({
        "sample_base": sample_base,
        "temperature_C": T,
        "beta": beta,
        "tau0": tau0,
        "a": a
    })

if failed:
    raise RuntimeError(
        "Mixture fits failed:\n" +
        "\n".join(f"{s} @ {T}°C: {err}" for s, T, err in failed)
    )

fit_df_mix = (
    pd.DataFrame(fit_rows)
    .set_index(["sample_base", "temperature_C"])
    .sort_index()
)

# ============================================================
# PLOT 1: MIXTURE MODEL ONLY (DLS CURVES)
# ============================================================

for sample_base in ["H24", "H29"]:

    plt.figure()
    df_s = df[df["sample_base"] == sample_base]

    match_types, Pn = Pn_data[sample_base]
    g2_mixture = make_g2_mixture_from_Pn(match_types, Pn)

    for T, g in df_s.groupby("temperature_C"):

        t = g["delay_us"].values
        y = g["correlation"].values

        m = (y > 0) & (t <= T_MAX_FIT)
        t = t[m]
        y = y[m]

        beta, tau0, a = fit_df_mix.loc[
            (sample_base, T), ["beta", "tau0", "a"]
        ].values

        y_fit = g2_mixture(t, beta, tau0, a)

        line, = plt.semilogx(t, y, ".", alpha=0.25)
        plt.semilogx(t, y_fit, "-", color=line.get_color(), lw=2)

    plt.title(f"{sample_base}: mixture model")
    plt.xlabel("Delay time (µs)")
    plt.ylabel("g₂ − 1")
    plt.tight_layout()
    plt.show()

# ============================================================
# PLOT 2: τ0(T)
# ============================================================

plt.figure()
for sample_base in ["H24", "H29"]:
    g = fit_df_mix.loc[sample_base].reset_index()
    plt.semilogy(g["temperature_C"], g["tau0"], "o-", label=sample_base)

plt.xlabel("Temperature (°C)")
plt.ylabel("τ₀ (µs)")
plt.legend()
plt.tight_layout()
plt.show()

# ============================================================
# PLOT 3: a(T)
# ============================================================

plt.figure()
for sample_base in ["H24", "H29"]:
    g = fit_df_mix.loc[sample_base].reset_index()
    plt.plot(g["temperature_C"], g["a"], "o-", label=sample_base)

plt.xlabel("Temperature (°C)")
plt.ylabel("a  (exp sensitivity)")
plt.legend()
plt.tight_layout()
plt.show()
