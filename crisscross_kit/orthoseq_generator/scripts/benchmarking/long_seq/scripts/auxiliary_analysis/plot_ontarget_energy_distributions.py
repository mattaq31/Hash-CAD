"""Compare initial-pool and final on-target energy distributions in the Figure 1 style."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata, load_seed_pairs


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    length = 16
    init_count = 900
    random_seed = 41
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["svg.fonttype"] = "none"
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(150 / 25.4, 190 / 25.4), sharex="col", sharey=True)
    for column, (batch_name, condition, title) in enumerate(targets):
        data_dir = module_dir / "data" / batch_name / f"len{length}" / condition
        report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
        naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
        metadata = load_metadata(hybrid_report)
        min_ontarget = float(metadata["search.min_ontarget"])
        max_ontarget = float(metadata["search.max_ontarget"])
        groups = {
            "Initial random pool": load_seed_pairs(hybrid_report),
            "Hybrid": load_found_pairs(hybrid_report),
            "Naive": load_found_pairs(naive_report),
        }
        # The same bins within each condition make selection shifts directly comparable.
        bin_edges = np.linspace(min_ontarget, max_ontarget, 21)
        margin = (max_ontarget - min_ontarget) * 0.08
        for row, (group_name, pairs_df) in enumerate(groups.items()):
            energies = pairs_df["on_target_energy_verified"].to_numpy(dtype=float)
            ax = axes[row, column]
            ax.hist(energies, bins=bin_edges, density=True, color="#3B6FB6", edgecolor="black", linewidth=0.35)
            ax.axvline(min_ontarget, color="#2A9D8F", ls="--", lw=1.1, label="On-target range", zorder=4)
            ax.axvline(max_ontarget, color="#2A9D8F", ls="--", lw=1.1, zorder=4)
            ax.axvline(energies.mean(), color="#4F4F4F", lw=1.1,
                       label=f"Mean: {energies.mean():.2f} kcal/mol", zorder=4)
            ax.set_title(f"{title}\n{group_name} (n={len(energies)})", fontsize=8, pad=4)
            ax.set_xlim(min_ontarget - margin, max_ontarget + margin)
            ax.set_box_aspect(3 / 4)
            ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, labelbottom=True, labelleft=True)
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
            ax.legend(fontsize=6, frameon=True, facecolor="white", edgecolor="none", framealpha=1,
                      loc="upper left", handlelength=1.4)
            ax.set_ylabel("Density", fontsize=8)
            ax.set_xlabel(r"$\Delta G_{\mathrm{assoc}}$ (kcal/mol)", fontsize=8)

    # Leave space above the histograms for the mean and range labels.
    axes[0, 0].set_ylim(0, axes[0, 0].get_ylim()[1] * 1.25)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.07, top=0.95, wspace=0.24, hspace=0.38)
    output_path = output_dir / f"ontarget_energy_distributions_len{length}_init{init_count}_seed{random_seed}.svg"
    fig.savefig(output_path, format="svg")
    print(f"Saved: {output_path}")
    plt.close(fig)
