"""Prepare and plot the published Polycube and OrthoSeq libraries using standard repository functions."""

from unittest.mock import patch

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.text import Text
import numpy as np
import pandas as pd

from orthoseq_generator.energy_plots import plot_on_off_target_histograms, plot_self_energy_histogram
from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata, load_offtarget_matrices
from orthoseq_generator.search_reporting import (
    verify_selected_pairs, write_hybrid_search_result_xlsx,
)


def load_published_sequences(report_path):
    """Read published pairs and their handle provenance from the extraction workbook."""
    selected = load_found_pairs(report_path).to_dict("records")
    handles = pd.read_excel(report_path, sheet_name="source_handles", keep_default_na=False).to_dict("records")
    return selected, handles


def read_energy_report(report_path):
    """Read on-target, monomer, and off-target energies from a standard Excel report."""
    pairs = load_found_pairs(report_path)
    metadata = load_metadata(report_path)
    bounds = (metadata.get("search.min_ontarget"), metadata.get("search.max_ontarget"))
    return {
        "pair_count": len(pairs),
        "on": pairs["on_target_energy_verified"].to_numpy(dtype=float),
        "self": pairs[["self_energy_seq_verified", "self_energy_rc_seq_verified"]].to_numpy().ravel(),
        "off": {name: frame.to_numpy(dtype=float) for name, frame in load_offtarget_matrices(report_path).items()},
        "allowed_on_target_range": bounds if all(value is not None for value in bounds) else None,
        "offtarget_limit": metadata.get("search.offtarget_limit"),
        "self_energy_limit": metadata.get("search.self_energy_limit"),
    }


def minimum_specificity_gap(on_target, off_target):
    """Return the smallest per-strand gap, including homodimers and excluding intended partners."""
    hh = off_target["handle_handle_energies"]
    ha = off_target["antihandle_handle_energies"].copy()
    aa = off_target["antihandle_antihandle_energies"]
    # HH and AA contain only the lower triangle; HA contains both cross-pair orientations.
    hh = np.tril(hh) + np.tril(hh, -1).T
    aa = np.tril(aa) + np.tril(aa, -1).T
    np.fill_diagonal(ha, np.inf)
    competitors = np.block([[hh, ha], [ha.T, aa]])
    strongest_offtarget = np.min(competitors, axis=1)
    return float(np.min(strongest_offtarget - np.tile(on_target, 2)))


def verify_and_write_report(selected, output_path, nupack_params, input_params, source_path, source_handles=None):
    """Compute one energy convention directly and write the standard Excel report."""
    from nupack import __version__ as nupack_version

    print(f"Verifying {len(selected)} pairs: {nupack_params}", flush=True)
    # Verification sets the model and energy type in the backend and each worker before calculation.
    verified = verify_selected_pairs(selected, nupack_params=nupack_params)
    write_hybrid_search_result_xlsx(
        output_path, algorithm_name="complete_library_comparison", selected_sequence_data=selected,
        verified=verified, search_params={}, input_params=input_params, nupack_params=nupack_params,
        artifact_info={"dataset_dir": str(source_path.parent)}, generation_data=[], validation_data=[],
        extra_metadata={"source.input_path": str(source_path.resolve()),
                        "nupack.version": nupack_version, "nupack.ensemble": "stacking"},
        extra_sheets={"source_handles": source_handles} if source_handles is not None else None,
    )
    print(f"Saved {output_path}", flush=True)


def load_comparison_data(reports):
    """Load association distributions and calculate the complex-energy gap for each library."""
    libraries = {}
    for name, paths in reports.items():
        association = read_energy_report(paths["total"])
        complex_energy = read_energy_report(paths["totalu"])
        count = association["pair_count"]
        lower = np.tril_indices(count)
        cross = ~np.eye(count, dtype=bool)
        off = association["off"]
        # Count each unintended complex once, including the HH and AA diagonal homodimers.
        unintended = np.concatenate([off["handle_handle_energies"][lower],
                                     off["antihandle_handle_energies"][cross],
                                     off["antihandle_antihandle_energies"][lower]])
        libraries[name] = {**association, "off": unintended,
                           "gap": minimum_specificity_gap(complex_energy["on"], complex_energy["off"])}
    return libraries


def plot_comparison(libraries, output_path, display_names, bins, visible_max_energy,
                    figure_width_mm, figure_height_mm, table_height_mm, style_scale):
    """Draw the final publication layout using the existing repository histogram functions."""
    # The published Menger library optimized a different objective. Our allowed interval applies only to OrthoSeq.
    on_min, on_max = libraries["OrthoSeq"]["allowed_on_target_range"]
    table_rows = [
        ["Achieved on-target range"] + [f"[{np.min(data['on']):.3f}, {np.max(data['on']):.3f}]"
                                       for data in libraries.values()],
        ["Mean on-target energy"] + [f"{np.mean(data['on']):.3f}" for data in libraries.values()],
        ["Minimum off-target energy"] + [f"{np.min(data['off']):.3f}" for data in libraries.values()],
        ["Minimum self-folding energy"] + [f"{np.min(data['self']):.3f}" for data in libraries.values()],
        ["Polycube criterion (kcal/mol)", "", ""],
        ["Minimum gap (complex free energy)"] + [f"{data['gap']:.3f}" for data in libraries.values()],
    ]
    x_min = np.floor(min(np.min(data["on"]) for data in libraries.values()) - 0.5)
    full_x_max = np.ceil(max(np.max(data["off"]) for data in libraries.values()) + 0.2)
    xlim = (float(x_min), visible_max_energy)
    self_x_min = np.floor(min(np.min(data["self"]) for data in libraries.values()) * 10) / 10
    self_bins = np.linspace(self_x_min, 0, 31)
    plt.switch_backend("Agg")
    plt.rcParams.update({"font.family": "Arial", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(figure_width_mm / 25.4, figure_height_mm / 25.4))
    # Give the table a smaller gap than the two plot rows.
    layout = fig.add_gridspec(2, 1, height_ratios=[2.7, table_height_mm / 45], hspace=0.25)
    grid = layout[0].subgridspec(2, 2, width_ratios=[1.15, 1], hspace=0.70, wspace=0.32)
    energy_axes = [fig.add_subplot(grid[row, 0]) for row in range(2)]
    self_axes = [fig.add_subplot(grid[row, 1]) for row in range(2)]
    for ax, self_ax, (name, data) in zip(energy_axes, self_axes, libraries.items()):
        # Bin over the complete datasets, then crop only the displayed range so density stays normalized.
        # The unchanged helper creates its own axes. Supply this panel only during this local call.
        with patch.object(plt, "subplots", return_value=(fig, ax)), patch.object(plt, "tight_layout"):
            plot_on_off_target_histograms(
                data["on"], data["off"], bins=bins, xlim=(x_min, full_x_max), show_plot=False,
                title="On and off-target energies",
            )
        ax.set_xlim(xlim)
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
    # Match the two libraries' scales within each energy type; monomer and association densities differ.
    for group in (energy_axes, self_axes):
        y_max = max(ax.get_ylim()[1] for ax in group)
        for ax in group:
            ax.set_ylim(0, y_max)
    for ax in energy_axes + self_axes:
        # Scale the helper's existing typography and strokes together to fit a paper-sized panel.
        for artist in ax.findobj():
            if isinstance(artist, Text):
                artist.set_fontsize(artist.get_fontsize() * style_scale)
            elif isinstance(artist, (Line2D, Patch)):
                artist.set_linewidth(artist.get_linewidth() * style_scale)
                if isinstance(artist, Line2D):
                    artist.set_markersize(artist.get_markersize() * style_scale)
                    artist.set_markeredgewidth(artist.get_markeredgewidth() * style_scale)
        # Automatic tick spacing reads the axis font setting, not the individually scaled text artists.
        ax.tick_params(axis="both", which="major", labelsize=16 * style_scale)
        ax.xaxis.labelpad *= style_scale
        ax.yaxis.labelpad *= style_scale
        ax.set_title(ax.get_title(), fontsize=19 * style_scale, pad=10 * style_scale)
        ax.legend(fontsize=16 * style_scale, frameon=False,
                  loc="upper right" if ax in energy_axes else "upper left")
        if ax in energy_axes:
            ax.set_xticks(np.arange(x_min, visible_max_energy + 0.5, 2))
        else:
            ax.set_xticks(np.arange(self_x_min, 0.01, 0.2))

    table_ax = fig.add_subplot(layout[1])
    table_ax.axis("off")
    table = table_ax.table(
        cellText=table_rows,
        colLabels=["Achieved values (kcal/mol)", f"Polycubes ({libraries['Menger']['pair_count']} pairs)",
                   f"OrthoSeq ({libraries['OrthoSeq']['pair_count']} pairs)"],
        colWidths=[0.44, 0.28, 0.28], cellLoc="left", colLoc="left", bbox=[0, 0, 1, 1],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    for (row, col), cell in table.get_celld().items():
        cell.visible_edges = ""
        cell.set_edgecolor("black")
        cell.set_linewidth(0.5)
        cell.set_facecolor("white")
        cell.PAD = 0.045
        cell.set_height(1 / (len(table_rows) + 1))
        if row == 0:
            cell.visible_edges = "BT"
            cell.get_text().set_fontweight("bold")
        elif row == len(table_rows) - 1:
            cell.visible_edges = "BT"
            cell.get_text().set_fontweight("bold")
        elif row == len(table_rows):
            cell.visible_edges = "B"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(left=0.08, right=0.985, top=0.90, bottom=0.045)
    # Use the space below the panels for both tables without changing any histogram's size or position.
    figure_height_pt = fig.get_figheight() * 72
    table_height = 7.6 * (len(table_rows) + 1) / figure_height_pt
    table_ax.set_position([0.08, 0.015, 0.905, table_height])
    limits_ax = fig.add_axes([0.08, 0.015 + table_height + 4 / figure_height_pt,
                              0.905, 16 / figure_height_pt])
    limits_ax.axis("off")
    # Enclose the title and all three limits together, keeping the existing text and panel positions.
    limits_ax.add_patch(Rectangle((0, -1 / 16), 1, 27 / 16, transform=limits_ax.transAxes,
                                  fill=False, edgecolor="black", linewidth=0.5, clip_on=False))
    limits_ax.text(0.02, 1 + 2 / 16, "OrthoSeq design limits (kcal/mol)",
                   ha="left", va="bottom", fontsize=7, fontweight="bold")
    # Read only OrthoSeq's saved design settings; the published library used a different objective.
    limits = limits_ax.table(
        cellText=[[f"[{on_min:.3f}, {on_max:.3f}]", f"{libraries['OrthoSeq']['offtarget_limit']:.3f}",
                   f"{libraries['OrthoSeq']['self_energy_limit']:.3f}"]],
        colLabels=["Allowed on-target range", "Off-target limit", "Self-folding limit"],
        colWidths=[0.44, 0.28, 0.28], cellLoc="left", colLoc="left", bbox=[0, 0, 1, 1],
    )
    limits.auto_set_font_size(False)
    limits.set_fontsize(7)
    for cell in limits.get_celld().values():
        cell.visible_edges = ""
        cell.PAD = 0.045
    for ax, name in zip(energy_axes, libraries):
        # Give each library its own row heading above the two distribution titles.
        fig.text((fig.subplotpars.left + fig.subplotpars.right) / 2, ax.get_position().y1 + 0.048,
                 display_names[name], ha="center", va="bottom", fontsize=9, fontweight="bold")
    fig.savefig(output_path)
    plt.close(fig)
    print(f"Saved {output_path}")
