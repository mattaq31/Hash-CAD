"""Plot all canonical benchmark GC profiles as separate supplementary PDFs, one per condition.

Each figure contains a 3-by-3 grid of core lengths. Overlay hybrid runs with initial
sizes 250, 450, 900, and 2500 plus the naive result. The saved init900 random pool
is the baseline. Average both strands after removing fixed extensions, using the
existing report readers without computing energies. The canonical 12-mer script
is independent of this overview. Save compact vector figures at 165.1 mm width
for inclusion within the supplement's text area using LaTeX graphicx.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import PercentFormatter
import numpy as np

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata, load_seed_pairs


def load_gc_profile(report_path, length, seed_pool=False):
    """Read a saved sequence set and average its positional GC fractions across both core strands."""
    metadata = load_metadata(report_path)
    if int(metadata["input.length"]) != length:
        raise ValueError(f"{report_path}: report length does not match the requested core length.")
    pairs_df = load_seed_pairs(report_path) if seed_pool else load_found_pairs(report_path)
    if pairs_df is None or pairs_df.empty:
        raise ValueError(f"{report_path}: no saved sequences for the requested set.")
    offset = len(metadata.get("input.fivep_ext") or "")
    # Use the same core extraction and orientation averaging as the canonical GC plot.
    cores = [seq[offset:offset + length] for strand in ["seq", "rc_seq"] for seq in pairs_df[strand]]
    if any(len(core) != length or set(core) - set("ACGT") for core in cores):
        raise ValueError(f"{report_path}: invalid DNA core or core length.")
    profile = np.array([[base in "GC" for base in core] for core in cores]).mean(axis=0)
    return profile, len(pairs_df), metadata


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    lengths = [8, 9, 10, 12, 14, 16, 18, 20, 25]
    init_counts = [250, 450, 900, 2500]
    baseline_init = 900
    random_seed = 41
    # The PDF is a figure, not a document page: its width matches the supplement's usable text area.
    # SI_v3(review).log reports textwidth=469.75539 TeX points, equivalent to 165.1 mm.
    figure_width_mm = 165.1
    left_space_mm = 10.0
    right_space_mm = 1.5
    column_gap_mm = 10.0
    row_gap_mm = 11.0
    bottom_space_mm = 8.0
    heading_space_mm = 20.0
    panel_size_mm = (figure_width_mm - left_space_mm - right_space_mm - 2 * column_gap_mm) / 3
    figure_height_mm = bottom_space_mm + 3 * panel_size_mm + 2 * row_gap_mm + heading_space_mm
    variant_labels = {250: "Hybrid 250", 450: "Hybrid 450", 900: "Hybrid 900", 2500: "Graph-aware"}
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "5′ TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]
    styles = {
        "Initial random pool": ("0.5", "--"),
        "Hybrid 250": ("#0072B2", "-"),
        "Hybrid 450": ("#009E73", "-"),
        "Hybrid 900": ("#D55E00", "-"),
        "Graph-aware": ("#CC79A7", "-"),
        "Naive": ("#222222", "-."),
    }
    comparison_keys = (
        "input.length", "input.fivep_ext", "input.threep_ext", "input.unwanted_substrings",
        "input.apply_unwanted_to", "search.min_ontarget", "search.max_ontarget", "search.self_energy_limit",
        "search.offtarget_limit", "nupack.energy_type", "nupack.material", "nupack.celsius",
        "nupack.sodium", "nupack.magnesium",
    )
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["pdf.fonttype"] = 42

    pages = []
    for batch_name, condition, title in targets:
        panels = []
        for length in lengths:
            data_dir = module_dir / "data" / batch_name / f"len{length}" / condition
            report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
            baseline_report = data_dir / f"hybrid_{report_stem}_init{baseline_init}_seed{random_seed}.xlsx"
            baseline, baseline_count, reference = load_gc_profile(baseline_report, length, seed_pool=True)
            expected_extension = "TTTT" if condition == "5p_TTTT" else ""
            if (reference.get("input.fivep_ext") or "") != expected_extension or reference.get("input.threep_ext"):
                raise ValueError(f"{baseline_report}: extensions do not match the requested condition.")
            curves = {"Initial random pool": baseline}
            counts = {}
            for init_count in init_counts:
                report_path = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
                profile, count, metadata = load_gc_profile(report_path, length)
                if any(metadata.get(key) != reference.get(key) for key in comparison_keys):
                    raise ValueError(f"{report_path}: comparison conditions differ from the baseline report.")
                label = variant_labels[init_count]
                curves[label] = profile
                counts[label] = count
            naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
            profile, count, metadata = load_gc_profile(naive_report, length)
            if any(metadata.get(key) != reference.get(key) for key in comparison_keys):
                raise ValueError(f"{naive_report}: comparison conditions differ from the baseline report.")
            curves["Naive"] = profile
            counts["Naive"] = count
            panels.append((length, curves))
            print(f"{title}, {length}-mers: initial pool={baseline_count}; final pairs={counts}", flush=True)
        pages.append((condition, title, panels))

    # Share the scale across both pages and widen it if any curve would otherwise be clipped.
    all_profiles = [profile for _, _, panels in pages for _, curves in panels for profile in curves.values()]
    ymin = max(0.0, min(0.20, np.floor(min(profile.min() for profile in all_profiles) * 10) / 10))
    ymax = min(1.0, max(0.90, np.ceil(max(profile.max() for profile in all_profiles) * 10) / 10))
    print(f"Shared GC range: {ymin:.0%} to {ymax:.0%}", flush=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    for condition, title, panels in pages:
        condition_label = "TTTT" if condition == "5p_TTTT" else "no_extension"
        output_path = output_dir / f"gc_bias_overview_{condition_label}_seed{random_seed}.pdf"
        with PdfPages(output_path) as pdf:
            fig, axes = plt.subplots(3, 3, figsize=(figure_width_mm / 25.4, figure_height_mm / 25.4), sharey=True)
            for panel, (length, curves) in enumerate(panels):
                ax = axes.flat[panel]
                positions = np.arange(1, length + 1)
                for label, profile in curves.items():
                    color, linestyle = styles[label]
                    ax.plot(positions, profile, color=color, ls=linestyle, lw=0.8, marker="o", ms=1.5,
                            label=label, zorder=3 if label.startswith("Initial") else 2)
                ax.axhline(0.5, color="0.85", lw=0.6, ls=":", zorder=0)
                ax.set_title(f"{length}-mers", fontsize=8, pad=3)
                ax.set_box_aspect(1)
                tick_step = max(1, int(np.ceil(length / 10)))
                ticks = sorted(set(range(1, length + 1, tick_step)) | {length})
                ax.set_xticks(ticks)
                ax.set_xlim(0.7, length + 0.3)
                ax.set_ylim(ymin, ymax)
                ax.set_yticks(np.arange(ymin, ymax + 0.01, 0.10))
                ax.yaxis.set_major_formatter(PercentFormatter(xmax=1))
                ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, labelleft=True, labelbottom=True)
                for spine in ax.spines.values():
                    spine.set_linewidth(0.5)
                ax.set_ylabel("GC fraction", fontsize=6, labelpad=2)
                ax.set_xlabel("Core base position", fontsize=6, labelpad=2)
            fig.suptitle(title, fontsize=10, y=1 - 1.5 / figure_height_mm, va="top")
            handles, labels = axes.flat[0].get_legend_handles_labels()
            fig.legend(handles, labels, loc="upper center",
                       bbox_to_anchor=(0.5, 1 - 6 / figure_height_mm), ncol=3,
                       fontsize=6, frameon=False, handlelength=2.0, columnspacing=1.5)
            # Physical panel sizes keep the axes square and gaps only large enough for labels and titles.
            fig.subplots_adjust(left=left_space_mm / figure_width_mm,
                                right=1 - right_space_mm / figure_width_mm,
                                bottom=bottom_space_mm / figure_height_mm,
                                top=1 - heading_space_mm / figure_height_mm,
                                wspace=column_gap_mm / panel_size_mm, hspace=row_gap_mm / panel_size_mm)
            pdf.savefig(fig)
            plt.close(fig)
        print(f"Saved: {output_path}")
