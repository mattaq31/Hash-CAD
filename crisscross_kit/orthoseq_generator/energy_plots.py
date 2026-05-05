import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator


def plot_on_off_target_histograms(
    on_energies,
    off_energies,
    bins=80,
    output_path=None,
    show_plot=True,
    vlines=None,
    title=None,
    xlim=None,
):
    if isinstance(off_energies, dict):
        off_energies = np.concatenate(
            [
                off_energies["handle_handle_energies"].flatten(),
                off_energies["antihandle_handle_energies"].flatten(),
                off_energies["antihandle_antihandle_energies"].flatten(),
            ]
        )
        off_energies = off_energies[off_energies != 0]

    linewidth_axis = 2.5
    tick_width = 2.5
    tick_length = 6
    fontsize_ticks = 16
    fontsize_labels = 19
    fontsize_title = 19
    fontsize_legend = 16
    figsize = (5.5 * 16 / 9, 5.5)
    color_on = "#1f77b4"
    color_off = "#d62728"

    combined_min = min(np.min(on_energies), np.min(off_energies))
    combined_max = max(np.max(on_energies), np.max(off_energies))

    if vlines:
        for val in vlines.values():
            combined_min = min(combined_min, val)
            combined_max = max(combined_max, val)

    if xlim is not None:
        combined_min, combined_max = map(float, xlim)

    bin_edges = np.linspace(combined_min, combined_max, bins + 1)

    min_on = np.min(on_energies)
    mean_on = np.mean(on_energies)
    std_on = np.std(on_energies)
    max_on = np.max(on_energies)
    mean_off = np.mean(off_energies)
    std_off = np.std(off_energies)
    min_off = np.min(off_energies)

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(
        on_energies,
        bins=bin_edges,
        alpha=0.8,
        label="On-target",
        color=color_on,
        edgecolor="black",
        linewidth=2,
        density=True,
        zorder=1,
    )
    ax.hist(
        off_energies,
        bins=bin_edges,
        alpha=0.8,
        label="Off-target",
        color=color_off,
        edgecolor="black",
        linewidth=2,
        density=True,
        zorder=2,
    )

    if vlines and "min_ontarget" in vlines:
        ax.axvline(
            vlines["min_ontarget"],
            color="blue",
            linestyle="--",
            linewidth=3,
            label=f"Min on-target = {vlines['min_ontarget']:.3f}",
        )
    ax.axvline(
        max_on,
        color="blue",
        linestyle="--",
        linewidth=3,
        label=f"Max on-target = {max_on:.2f}",
    )
    ax.axvline(
        min_off,
        color="gray",
        linestyle="--",
        linewidth=3,
        label=f"Off-target cutoff = {min_off:.2f}",
    )

    ax.set_xlabel("Gibbs free energy (kcal/mol)", fontsize=fontsize_labels)
    ax.set_ylabel("Normalized frequency", fontsize=fontsize_labels)
    if title is None:
        title = "On-target vs Off-target Energy Distribution"
    ax.set_title(title, fontsize=fontsize_title, pad=10)
    ax.set_xlim(combined_min, combined_max)

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(axis="x", which="minor", length=4, width=1.2)
    ax.tick_params(
        axis="both",
        which="major",
        labelsize=fontsize_ticks,
        width=tick_width,
        length=tick_length,
    )

    for spine in ax.spines.values():
        spine.set_linewidth(linewidth_axis)

    ax.legend(fontsize=fontsize_legend, frameon=False)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path)
    if show_plot:
        plt.show()

    print("\nSummary statistics:")
    print(f"Min On-Target Energy:   {min_on:.3f} kcal/mol")
    print(f"Mean On-Target Energy:  {mean_on:.3f} kcal/mol")
    print(f"Std Dev On-Target:      {std_on:.3f} kcal/mol")
    print(f"Max On-Target Energy:   {max_on:.3f} kcal/mol")
    print(f"Mean Off-Target Energy: {mean_off:.3f} kcal/mol")
    print(f"Std Dev Off-Target:     {std_off:.3f} kcal/mol")
    print(f"Min Off-Target Energy:  {min_off:.3f} kcal/mol")

    return {
        "min_on": min_on,
        "mean_on": mean_on,
        "std_on": std_on,
        "max_on": max_on,
        "mean_off": mean_off,
        "std_off": std_off,
        "min_off": min_off,
    }


def plot_self_energy_histogram(self_energies, bins=30, output_path=None, show_plot=True):
    if isinstance(self_energies, dict):
        values = [np.ravel(v) for v in self_energies.values()]
        combined = np.concatenate(values) if values else np.array([])
    elif isinstance(self_energies, (list, tuple)) and len(self_energies) > 1:
        combined = np.concatenate([np.ravel(v) for v in self_energies])
    else:
        combined = np.ravel(self_energies)

    linewidth_axis = 2.5
    tick_width = 2.5
    tick_length = 6
    fontsize_ticks = 16
    fontsize_labels = 19
    fontsize_title = 19
    fontsize_legend = 16
    figsize = (12, 5.5)
    color_self = "#1f77b4"

    mean_self = np.mean(combined)
    std_self = np.std(combined)
    min_self = np.min(combined)
    max_self = np.max(combined)

    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(
        combined,
        bins=bins,
        alpha=0.8,
        label="Self-energies",
        color=color_self,
        edgecolor="black",
        linewidth=2,
        density=True,
    )

    ax.set_xlabel("Gibbs free energy (kcal/mol)", fontsize=fontsize_labels)
    ax.set_ylabel("Normalized frequency", fontsize=fontsize_labels)
    ax.set_title("Self-Energy Distribution", fontsize=fontsize_title, pad=10)

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.tick_params(axis="x", which="minor", length=4, width=1.2)
    ax.tick_params(
        axis="both",
        which="major",
        labelsize=fontsize_ticks,
        width=tick_width,
        length=tick_length,
    )

    for spine in ax.spines.values():
        spine.set_linewidth(linewidth_axis)

    ax.legend(fontsize=fontsize_legend)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path)
    if show_plot:
        plt.show()

    print("\nSummary statistics:")
    print(f"Mean Self Energy:  {mean_self:.3f} kcal/mol")
    print(f"Std Dev Self:      {std_self:.3f} kcal/mol")
    print(f"Min Self Energy:   {min_self:.3f} kcal/mol")
    print(f"Max Self Energy:   {max_self:.3f} kcal/mol")

    return {
        "mean_self": mean_self,
        "std_self": std_self,
        "min_self": min_self,
        "max_self": max_self,
    }
