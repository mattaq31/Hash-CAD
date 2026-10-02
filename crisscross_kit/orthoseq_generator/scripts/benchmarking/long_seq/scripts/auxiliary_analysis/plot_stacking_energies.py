"""Plot mean nearest-neighbor stacking energies along selected and random DNA cores."""

from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import nupack as nu

from orthoseq_generator.search_report_reader import (
    load_found_pairs,
    load_metadata,
    load_seed_pairs,
)


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    length = 16
    init_count = 900
    random_seed = 41
    shown_steps = length - 1
    plt.rcParams["font.family"] = "Arial"
    plt.rcParams["svg.fonttype"] = "none"
    complement = str.maketrans("ACGT", "TGCA")
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(177.8 / 25.4, 120 / 25.4), sharex=True, sharey=True)
    for row, (batch_name, condition, title) in enumerate(targets):
        data_dir = module_dir / "data" / batch_name / f"len{length}" / condition
        report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
        naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
        metadata = load_metadata(hybrid_report)
        offset = len(metadata.get("input.fivep_ext") or "")
        seed_df = load_seed_pairs(hybrid_report)
        hybrid_df = load_found_pairs(hybrid_report)
        naive_df = load_found_pairs(naive_report)

        model = nu.Model(
            material=str(metadata["nupack.material"]), celsius=float(metadata["nupack.celsius"]),
            sodium=float(metadata["nupack.sodium"]), magnesium=float(metadata["nupack.magnesium"]),
        )
        stack_energies = {}
        for bases in product("ACGT", repeat=2):
            step = "".join(bases)
            # Two closed-loop snippets specify an internal stack, excluding duplex end/initiation terms.
            stack_energies[step] = model.loop_energy([step, step.translate(complement)[::-1]])

        profiles = {}
        groups = {"Initial random pool": seed_df, "Hybrid": hybrid_df, "Naive": naive_df}
        for group_name, pairs_df in groups.items():
            # Both strands give a reverse-complement-symmetric mean profile; count only core steps.
            cores = [seq[offset:offset + length] for strand in ["seq", "rc_seq"] for seq in pairs_df[strand]]
            energies = np.array([
                [stack_energies[core[i:i + 2]] for i in range(length - 1)] for core in cores
            ])
            profiles[group_name] = energies.mean(axis=0)[:shown_steps]

        positions = np.arange(1, shown_steps + 1)
        for column, (group_name, color) in enumerate([
            ("Hybrid", "#3B6FB6"), ("Naive", "#009E73"),
        ]):
            ax = axes[row, column]
            ax.plot(positions, profiles[group_name], "o-", color=color, label=group_name, lw=1.3, ms=2.5)
            ax.plot(positions, profiles["Initial random pool"], "o--", color="0.5",
                    label="Initial random pool", lw=1.1, ms=2.5)
            ax.set_title(f"{title}\n{group_name} (n={len(groups[group_name])})", fontsize=8, pad=4)
            ax.set_xticks(positions, [f"{i}–{i + 1}" for i in positions], rotation=45, ha="right")
            ax.tick_params(axis="both", labelsize=6, width=0.5, length=2, labelbottom=True, labelleft=True)
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
            ax.legend(fontsize=6, frameon=True, facecolor="white", edgecolor="none", framealpha=1,
                      handlelength=1.4)
            ax.set_ylabel("Mean stacking ΔG (kcal/mol)", fontsize=8)
            ax.set_xlabel("Base pair position", fontsize=8)

    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.15, top=0.93, wspace=0.22, hspace=0.60)
    output_path = output_dir / f"stacking_energies_len{length}_init{init_count}_seed{random_seed}.svg"
    fig.savefig(output_path, format="svg")
    print(f"Saved: {output_path}")
    plt.close(fig)
