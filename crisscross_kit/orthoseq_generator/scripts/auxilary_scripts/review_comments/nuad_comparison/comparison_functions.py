"""Read standard repository XLSX reports and draw nuad / OrthoSeq comparison figures."""

from ast import literal_eval
from pathlib import Path
from unittest.mock import patch

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text
import numpy as np

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata, load_offtarget_matrices
from orthoseq_generator.scripts.auxilary_scripts.review_comments.comparison_tables import add_comparison_boxes
from orthoseq_generator.energy_plots import plot_on_off_target_histograms, plot_self_energy_histogram


def load_energy_report(report_path):
    """Load verified energies and count each unintended complex once, including diagonal homodimers."""
    metadata = load_metadata(report_path)
    pairs = load_found_pairs(report_path)
    count = len(pairs)
    matrices = {name: frame.to_numpy(dtype=float) for name, frame in load_offtarget_matrices(report_path).items()}
    if count != metadata["found_pair_count"] or any(matrix.shape != (count, count) for matrix in matrices.values()):
        raise ValueError(f"Inconsistent report dimensions: {report_path}")
    lower = np.tril_indices(count)
    cross = ~np.eye(count, dtype=bool)
    data = {"pair_count": count, "on": pairs["on_target_energy_verified"].to_numpy(dtype=float),
            "self": pairs[["self_energy_seq_verified", "self_energy_rc_seq_verified"]].to_numpy(dtype=float).ravel(),
            "off": np.concatenate([matrices["handle_handle_energies"][lower],
                                   matrices["antihandle_handle_energies"][cross],
                                   matrices["antihandle_antihandle_energies"][lower]])}
    assert len(data["off"]) == 2 * count ** 2
    if any(np.any(np.isnan(data[key])) or np.any(np.isneginf(data[key])) for key in ("on", "off", "self")):
        raise ValueError(f"Invalid verified energies: {report_path}")
    data["off_finite"] = data["off"][np.isfinite(data["off"])]
    data["off_infinite_count"] = int(np.count_nonzero(np.isposinf(data["off"])))
    data["violations"] = (
        int(np.count_nonzero(data["self"] < metadata["search.self_energy_limit"])),
        int(np.count_nonzero((data["on"] < metadata["search.min_ontarget"])
                            | (data["on"] > metadata["search.max_ontarget"]))),
        int(np.count_nonzero(data["off"] < metadata["search.offtarget_limit"])),
    )
    return data, metadata


def plot_comparison(nuad_report, orthoseq_report, output_path):
    """Plot nuad above its matching OrthoSeq library with the existing histogram helpers and achieved-value table."""
    nuad, metadata = load_energy_report(nuad_report)
    orthoseq, reference = load_energy_report(orthoseq_report)
    for key in ("input.length", "search.min_ontarget", "search.max_ontarget", "search.offtarget_limit",
                "search.self_energy_limit", "nupack.celsius", "nupack.sodium", "nupack.magnesium"):
        if not np.isclose(metadata[key], reference[key], rtol=0, atol=1e-12):
            raise ValueError(f"Different {key} in the comparison reports.")
    for key in ("input.fivep_ext", "input.threep_ext", "nupack.energy_type"):
        if metadata[key] != reference[key]:
            raise ValueError(f"Different {key} in the comparison reports.")
    if any(info["nupack.material"] not in ("dna", "dna04.2") for info in (metadata, reference)):
        raise ValueError("Both reports must use the DNA model.")
    if literal_eval(metadata["input.unwanted_substrings"]) != literal_eval(reference["input.unwanted_substrings"]):
        raise ValueError("Different forbidden motifs in the comparison reports.")
    assert nuad["pair_count"] == orthoseq["pair_count"]
    assert sum(nuad["violations"]) == metadata["validation.individual_violation_count"]
    libraries = {"nuad": nuad, "OrthoSeq": orthoseq}
    for name, data in libraries.items():
        print(f"{name}: {data['pair_count']} pairs; individual self/on/off violations: {data['violations']}")
    bins = 100
    visible_max_energy = -4.0 if metadata["input.length"] >= 12 else 0.0
    style_scale = 8 / 19
    x_min = float(np.floor(min(np.min(data["on"]) for data in libraries.values()) - 0.5))
    full_x_max = float(np.ceil(max(np.max(data["off_finite"]) for data in libraries.values()) + 0.2))
    # Very short strands can all have zero folding energy; still give their histogram a nonzero bin range.
    self_x_min = min(-0.1, np.floor(min(np.min(data["self"]) for data in libraries.values()) * 10) / 10)
    self_bins = np.linspace(self_x_min, 0, 31)
    plt.switch_backend("Agg")
    plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(165.1 / 25.4, 142 / 25.4))
    layout = fig.add_gridspec(2, 1, height_ratios=[2.7, 30 / 45], hspace=0.25)
    grid = layout[0].subgridspec(2, 2, width_ratios=[1.15, 1], hspace=0.70, wspace=0.32)
    energy_axes = [fig.add_subplot(grid[row, 0]) for row in range(2)]
    self_axes = [fig.add_subplot(grid[row, 1]) for row in range(2)]
    for ax, self_ax, (name, data) in zip(energy_axes, self_axes, libraries.items()):
        # Reuse the same histogram helpers and panel placement as the Polycube figure.
        # Normalize over all energies before cropping the visible off-target tail.
        print(f"Plotting {name}")
        with patch.object(plt, "subplots", return_value=(fig, ax)), patch.object(plt, "tight_layout"):
            plot_on_off_target_histograms(data["on"], data["off_finite"], bins=bins, xlim=(x_min, full_x_max),
                                          show_plot=False, title="On and off-target energies")
        # The helper normalizes finite values. Retain the mass of +infinity entries outside the displayed axis.
        finite_fraction = len(data["off_finite"]) / len(data["off"])
        for bar in ax.patches[bins:]:
            bar.set_height(bar.get_height() * finite_fraction)
        ax.set_xlim(x_min, visible_max_energy)
        ax.xaxis.label.set_text(r"Gibbs free energy, $\Delta G_{\mathrm{assoc}}$ (kcal/mol)")
        ax.yaxis.label.set_text("Density")
        # These lines mark measured extrema. Keep their values and distinguish them from imposed limits.
        for line in ax.lines:
            label = line.get_label()
            if label.startswith("Max on-target ="):
                line.set_label(label.replace("Max on-target", "Maximum on-target energy", 1))
            elif label.startswith("Off-target cutoff ="):
                line.set_label(label.replace("Off-target cutoff", "Minimum off-target energy", 1))
        with patch.object(plt, "subplots", return_value=(fig, self_ax)), patch.object(plt, "tight_layout"):
            plot_self_energy_histogram(data["self"], bins=self_bins, show_plot=False)
        self_ax.set_title("Self-folding energies")
        self_ax.xaxis.label.set_text(r"Gibbs free energy, $\Delta G_{\mathrm{self}}$ (kcal/mol)")
        self_ax.yaxis.label.set_text("Density")
        for bar in self_ax.patches:
            if bar.get_label() == "Self-energies":
                bar.set_label("Self-folding")
        self_ax.set_xlim(self_x_min, 0.02)
        self_ax.axvline(np.min(data["self"]), color="gray", linestyle="--", linewidth=3,
                        label=f"Minimum self-folding energy = {np.min(data['self']):.3f}")
        self_ax.get_legend().remove()
    for group in (energy_axes, self_axes):
        y_max = max(ax.get_ylim()[1] for ax in group)
        for ax in group:
            ax.set_ylim(0, y_max)
    for ax in energy_axes + self_axes:
        for artist in ax.findobj():
            if isinstance(artist, Text):
                artist.set_fontsize(artist.get_fontsize() * style_scale)
            elif isinstance(artist, (Line2D, Patch)):
                artist.set_linewidth(artist.get_linewidth() * style_scale)
                if isinstance(artist, Line2D):
                    artist.set_markersize(artist.get_markersize() * style_scale)
                    artist.set_markeredgewidth(artist.get_markeredgewidth() * style_scale)
        # Scale tick geometry and padding with the text when embedding the large histogram helpers.
        ax.tick_params(axis="both", which="major", labelsize=16 * style_scale,
                       length=6 * style_scale, width=2.5 * style_scale, pad=3.5 * style_scale)
        ax.tick_params(axis="both", which="minor", length=4 * style_scale, width=1.2 * style_scale)
        ax.xaxis.labelpad *= style_scale
        ax.yaxis.labelpad *= style_scale
        ax.set_title(ax.get_title(), fontsize=19 * style_scale, pad=10 * style_scale)
        ax.legend(fontsize=16 * style_scale, frameon=False,
                  loc="upper right" if ax in energy_axes else "upper left")
        energy_tick_step = 4 if visible_max_energy - x_min > 18 else 2
        self_tick_step = 0.05 if self_x_min >= -0.5 else 0.2 if self_x_min >= -1.5 else 0.5
        self_tick_start = np.ceil(self_x_min / self_tick_step) * self_tick_step
        ax.set_xticks(np.arange(x_min, visible_max_energy + 0.5, energy_tick_step) if ax in energy_axes
                      else np.arange(self_tick_start, 0.01, self_tick_step))

    allowed_range = f"[{metadata['search.min_ontarget']:.3f}, {metadata['search.max_ontarget']:.3f}]"
    table_rows = [
        ["Achieved on-target range"] + [f"[{np.min(data['on']):.3f}, {np.max(data['on']):.3f}]"
                                       for data in libraries.values()],
        ["Mean on-target energy"] + [f"{np.mean(data['on']):.3f}" for data in libraries.values()],
        ["Minimum off-target energy"] + [f"{np.min(data['off']):.3f}" for data in libraries.values()],
        ["Minimum self-folding energy"] + [f"{np.min(data['self']):.3f}" for data in libraries.values()],
        ["Violations: self / on / off (counts)"] + [" / ".join(map(str, data["violations"]))
                                                  for data in libraries.values()],
    ]
    if any(data["off_infinite_count"] for data in libraries.values()):
        table_rows.insert(-1, ["Saved +infinity entries (counts)"]
                          + [str(data["off_infinite_count"]) for data in libraries.values()])
    fig.subplots_adjust(left=0.08, right=0.985, top=0.90, bottom=0.045)
    for ax, name in zip(energy_axes, libraries):
        fig.text((fig.subplotpars.left + fig.subplotpars.right) / 2, ax.get_position().y1 + 0.048,
                 name, ha="center", va="bottom", fontsize=9, fontweight="bold")
    method_columns = ["Criterion"] + [f"{name} ({data['pair_count']} pairs)" for name, data in libraries.items()]
    limits = [
        ["Allowed on-target energy range", allowed_range],
        ["Off-target energy limit", f"{metadata['search.offtarget_limit']:.3f}"],
        ["Self-folding energy limit", f"{metadata['search.self_energy_limit']:.3f}"],
    ]
    add_comparison_boxes(fig, energy_axes + self_axes, [
        ("Design limits (kcal/mol)", None, limits, [0.48, 0.52]),
        ("Achieved values (kcal/mol)", method_columns, table_rows, [0.48, 0.26, 0.26]),
    ])
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix(".pdf"))
    plt.close(fig)
    print(f"Saved {output.with_suffix('.pdf')}")
