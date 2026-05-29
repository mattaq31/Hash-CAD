#!/usr/bin/env python3

"""
Plot the two analytical selection-helper curves used in the Streamlit app.

- fraction bound vs. association Gibbs free energy
- fraction unpaired vs. secondary-structure Gibbs free energy
"""

from pathlib import Path
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


R_KCAL = 1.98720425864083e-3
RHO_H2O = 55.14

matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["svg.fonttype"] = "none"

MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.5 * 1.05
FIGURE_HEIGHT_MM = 58.0 * 1.05
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 8
AXIS_LABEL_FONT_SIZE = 8
TICK_LABEL_FONT_SIZE = 6

AXIS_LINEWIDTH = 0.5
CURVE_LINEWIDTH = 1.3
REFERENCE_LINEWIDTH = 1.1
CURVE_ZORDER = 2
REFERENCE_ZORDER = 3

BINDING_COLOR = "black"
SECONDARY_COLOR = "black"
RANGE_COLOR = "#2A9D8F"
LIMIT_COLOR = "#4F4F4F"

ONOFF_X_MIN = -24.0
ONOFF_X_MAX = 0.0
SECONDARY_X_MIN = -3.85
SECONDARY_X_MAX = 0.0


def solve_ab_equilibrium(a0, b0, kc):
    a = kc
    b = -(kc * (a0 + b0) + 1.0)
    c = kc * a0 * b0
    disc = max(b * b - 4.0 * a * c, 0.0)
    return (-b - math.sqrt(disc)) / (2.0 * a)


def fraction_bound_from_dg(dg_assoc, conc_m, temp_c):
    if conc_m <= 0.0:
        return 0.0
    rt = R_KCAL * (273.15 + temp_c)
    kx = math.exp(-dg_assoc / rt)
    kc = kx / RHO_H2O
    ab = solve_ab_equilibrium(conc_m, conc_m, kc)
    return max(min(ab / conc_m, 1.0), 0.0)


if __name__ == "__main__":
    temp_c = 37.0
    conc_nm = 1000.0
    conc_m = conc_nm * 1e-9

    min_ontarget = -16.6520552839256
    max_ontarget = -14.917680807592106
    offtarget_limit = -8.160422784450315
    self_energy_limit = -0.9919471230992267

    out_dir = Path(__file__).resolve().parent / "data" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    dg_assoc = np.linspace(ONOFF_X_MIN, 0.0, 400)
    frac_bound = np.array([fraction_bound_from_dg(dg, conc_m, temp_c) for dg in dg_assoc])

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    ax.plot(
        dg_assoc,
        frac_bound,
        color=BINDING_COLOR,
        linewidth=CURVE_LINEWIDTH,
        label="Fraction bound",
        zorder=CURVE_ZORDER,
    )
    ax.axvline(
        min_ontarget,
        color=RANGE_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="On-target range",
        zorder=REFERENCE_ZORDER,
    )
    ax.axvline(
        max_ontarget,
        color=RANGE_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="_nolegend_",
        zorder=REFERENCE_ZORDER,
    )
    ax.axvline(
        offtarget_limit,
        color=LIMIT_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="Off-target limit",
        zorder=REFERENCE_ZORDER,
    )
    ax.set_xlabel(r"Gibbs free energy, $\Delta G_{\mathrm{assoc}}$ (kcal/mol)", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Fraction bound", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_title("Strand binding", fontsize=TITLE_FONT_SIZE, pad=4)
    ax.set_xlim(ONOFF_X_MIN, ONOFF_X_MAX)
    ax.set_ylim(0.0, 1.05)
    ax.tick_params(axis="both", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=2)
    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)
    ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=TICK_LABEL_FONT_SIZE,
        loc="upper right",
        handlelength=1.4,
    )
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.22, top=0.90)
    fig.savefig(out_dir / "selection_helper_binding.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    rt = R_KCAL * (273.15 + temp_c)
    dg_sec = np.linspace(SECONDARY_X_MIN, 0.0, 400)
    frac_unpaired = np.exp(dg_sec / rt)
    frac_unpaired = np.clip(frac_unpaired, 0.0, 1.0)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)
    ax.plot(
        dg_sec,
        frac_unpaired,
        color=SECONDARY_COLOR,
        linewidth=CURVE_LINEWIDTH,
        label="Fraction unpaired",
        zorder=CURVE_ZORDER,
    )
    ax.axvline(
        self_energy_limit,
        color=LIMIT_COLOR,
        linestyle="--",
        linewidth=REFERENCE_LINEWIDTH,
        label="Secondary structure limit",
        zorder=REFERENCE_ZORDER,
    )
    ax.set_xlabel(r"Gibbs free energy, $\Delta G_{\mathrm{sec}}$ (kcal/mol)", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Fraction unpaired", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_title("Secondary structure formation", fontsize=TITLE_FONT_SIZE, pad=4)
    ax.set_xlim(SECONDARY_X_MIN, SECONDARY_X_MAX)
    ax.set_ylim(0.0, 1.05)
    ax.tick_params(axis="both", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=2)
    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)
    ax.legend(
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=TICK_LABEL_FONT_SIZE,
        loc="upper left",
        handlelength=1.4,
    )
    fig.subplots_adjust(left=0.17, right=0.98, bottom=0.22, top=0.90)
    fig.savefig(out_dir / "selection_helper_secondary.svg", format="svg", bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {out_dir / 'selection_helper_binding.svg'}")
    print(f"Wrote {out_dir / 'selection_helper_secondary.svg'}")
