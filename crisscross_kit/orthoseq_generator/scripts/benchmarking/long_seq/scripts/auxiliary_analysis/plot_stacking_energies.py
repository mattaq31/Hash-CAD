"""Plot mean nearest-neighbor stacking energies along selected and random DNA cores."""

from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import nupack as nu

from prepare_init900_outside_crossref import reconstruct_seed_independent_df
from orthoseq_generator.search_report_reader import (
    load_found_pairs,
    load_metadata,
    load_search_progress,
    load_seed_pairs,
)


if __name__ == "__main__":
    module_dir = Path(__file__).resolve().parents[2]
    output_dir = module_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    length = 14
    init_count = 900
    random_seed = 41
    shown_steps = length // 2
    complement = str.maketrans("ACGT", "TGCA")
    targets = [
        ("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT", "TTTT extension"),
        ("batch_x______sigma1p0_seed41", "5p_none", "No extension"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True, sharey=True, constrained_layout=True)
    for row, (batch_name, condition, title) in enumerate(targets):
        data_dir = module_dir / "data" / batch_name / f"len{length}" / condition
        report_stem = f"len{length}_{condition}_limitm8p16_budget10000000"
        hybrid_report = data_dir / f"hybrid_{report_stem}_init{init_count}_seed{random_seed}.xlsx"
        naive_report = data_dir / f"naive_{report_stem}_seed{random_seed}.xlsx"
        metadata = load_metadata(hybrid_report)
        offset = len(metadata.get("input.fivep_ext") or "")
        seed_df = load_seed_pairs(hybrid_report)
        gmax_df = reconstruct_seed_independent_df(
            seed_df, load_found_pairs(hybrid_report), load_search_progress(hybrid_report),
        )
        naive_df = load_found_pairs(naive_report).head(len(gmax_df))
        if len(naive_df) != len(gmax_df):
            raise ValueError("The naive report has fewer pairs than the initial GMAX set.")

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
        groups = {"Initial random pool": seed_df, "GMAX selected": gmax_df, "Naive selected": naive_df}
        for group_name, pairs_df in groups.items():
            # Both strands give a reverse-complement-symmetric mean profile; count only core steps.
            cores = [seq[offset:offset + length] for strand in ["seq", "rc_seq"] for seq in pairs_df[strand]]
            energies = np.array([
                [stack_energies[core[i:i + 2]] for i in range(length - 1)] for core in cores
            ])
            profiles[group_name] = energies.mean(axis=0)[:shown_steps]

        positions = np.arange(1, shown_steps + 1)
        for column, (group_name, color) in enumerate([
            ("GMAX selected", "#0072B2"), ("Naive selected", "#009E73"),
        ]):
            ax = axes[row, column]
            ax.plot(positions, profiles[group_name], "o-", color=color, label=group_name)
            ax.plot(positions, profiles["Initial random pool"], "o--", color="0.5", label="Initial random pool")
            ax.set_title(f"{group_name} ({len(groups[group_name])} pairs)")
            ax.set_xticks(positions, [f"{i}–{i + 1}" for i in positions])
            ax.grid(axis="y", alpha=0.2)
            ax.legend(fontsize=8)
            if column == 0:
                ax.set_ylabel(f"{title}\nMean stacking ΔG (kcal/mol)")
            if row == 1:
                ax.set_xlabel("Core base-pair step (5′ → 3′)")

    fig.suptitle(
        f"{length}-mer nearest-neighbor stacking energies — more negative is more favorable\n"
        "Both strands averaged; mirrored steps and fixed extensions omitted"
    )
    output_path = output_dir / f"stacking_energies_len{length}_init{init_count}_seed{random_seed}.pdf"
    fig.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close(fig)
