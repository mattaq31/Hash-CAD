"""Compare core-position base probabilities from the long-sequence benchmark reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from prepare_init900_outside_crossref import reconstruct_seed_independent_df
from orthoseq_generator.search_report_reader import load_found_pairs, load_search_progress, load_seed_pairs


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    length = 10
    init_count = 900
    random_seed = 41
    shown_positions = (length + 1) // 2
    ymax = 0.5
    bar_width = 0.16
    colors = {"A": "#0072B2", "T": "#009E73", "C": "#F0E442", "G": "#E69F00"}
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", 4, "TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", 0, "No extension"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 7), sharex=True, sharey=True, constrained_layout=True)
    for row, (batch_name, condition, offset, title) in enumerate(targets):
        batch_dir = module_dir / "data" / batch_name
        data_dir = batch_dir / f"len{length}" / condition
        report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
        naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
        gmax_df = reconstruct_seed_independent_df(
            load_seed_pairs(hybrid_report), load_found_pairs(hybrid_report), load_search_progress(hybrid_report),
        )
        naive_df = load_found_pairs(naive_report).head(len(gmax_df))
        if len(naive_df) != len(gmax_df):
            raise ValueError("The naive report has fewer pairs than the initial GMAX set.")
        groups = {
            "GMAX selected": gmax_df,
            "Naive selected": naive_df,
        }
        for group_index, (group_name, pairs_df) in enumerate(groups.items()):
            ax = axes[row, group_index]
            # Pool both strands to avoid choosing an arbitrary orientation; strip the fixed extension.
            cores = np.array([
                list(seq[offset:offset + length]) for strand in ["seq", "rc_seq"] for seq in pairs_df[strand]
            ])
            for base_index, (base, color) in enumerate(colors.items()):
                positions = np.arange(1, shown_positions + 1) + (base_index - 1.5) * bar_width
                probabilities = (cores[:, :shown_positions] == base).mean(axis=0)
                ymax = max(ymax, probabilities.max() * 1.1)
                ax.bar(
                    positions, probabilities, width=bar_width * 0.9, color=color,
                    label=base, edgecolor="0.25", linewidth=0.3,
                )
            ax.set_title(f"{group_name} ({len(pairs_df)} pairs)")
            ax.axhline(0.25, color="0.6", linestyle=":", linewidth=1)
            ax.set_xticks(range(1, shown_positions + 1))
            ax.set_xlim(0.5, shown_positions + 0.5)
            ax.set_axisbelow(True)
            ax.grid(axis="y", alpha=0.2)
            if group_index == 0:
                ax.set_ylabel(f"{title}\nBase probability")
            if row == 1:
                ax.set_xlabel("Core position (5′ → 3′)")
    axes[0, 0].set_ylim(0, ymax)
    axes[0, 0].legend(ncol=4, fontsize=8, loc="upper center")
    fig.suptitle(
        f"{length}-mer base probabilities — both strands, fixed extensions excluded\n"
        f"Positions 1–{shown_positions} shown; remaining positions follow by reverse-complement symmetry"
    )
    output_path = output_dir / f"base_probabilities_len{length}_init{init_count}_seed{random_seed}.pdf"
    fig.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close(fig)
