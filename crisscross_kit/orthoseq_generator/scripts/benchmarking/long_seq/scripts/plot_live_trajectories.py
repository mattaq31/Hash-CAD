#!/usr/bin/env python3
"""
Plot diagnostic long-sequence search trajectories from saved XLSX workbooks.

This script reads the `search_progress` sheet from each saved long-seq workbook
and writes four diagnostic plots:

- `5p_none`, `fb=0.01`
- `5p_none`, `fb=0.05`
- `5p_TTTT`, `fb=0.01`
- `5p_TTTT`, `fb=0.05`

The x-axis is cumulative NUPACK calls and the y-axis is `pairs_found`.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import tomllib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.rcParams["font.family"] = "Arial"

MODULE_DIR = Path(__file__).resolve().parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


DATA_ROOT = MODULE_DIR / "data"
GENERATED_CONFIG_ROOT = MODULE_DIR / "configs" / "generated"
ALGORITHM_LABELS = {
    "naive": "Naive",
    "hybrid": "Hybrid",
}
ALGORITHM_LINESTYLES = {
    "naive": "--",
    "hybrid": "-",
}
LENGTH_COLORS = {
    8: "#1f77b4",
    10: "#ff7f0e",
    12: "#2ca02c",
    14: "#d62728",
    16: "#9467bd",
    18: "#8c564b",
    20: "#e377c2",
}
GROUP_TITLES = {
    False: "Long-Seq Trajectories: No extension",
    True: "Long-Seq Trajectories: 5' TTTT extension",
}
OUTPUT_FILENAME_STEM = "long_seq_live_trajectories"


def format_limit_label(value: float) -> str:
    """Format one numeric off-target limit into the workbook filename token."""
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


def parse_limit_label(limit_label: str) -> float:
    """Decode a filename token such as `m8p16` back into a float."""
    return float(limit_label.replace("m", "-").replace("p", "."))


def read_metadata_value(metadata_df: pd.DataFrame, key: str):
    """Return one value from the workbook metadata sheet by key."""
    rows = metadata_df.loc[metadata_df["key"] == key, "value"]
    if rows.empty:
        return None
    return rows.iloc[0]


def normalize_algorithm_name(value: str | None) -> str | None:
    """Map workbook metadata algorithm names onto the plotting labels."""
    if value == "naive_search":
        return "naive"
    if value == "hybrid_search":
        return "hybrid"
    return None if value is None else str(value)


def parse_run_filename(report_path: Path) -> dict | None:
    """Parse one long-sequence workbook filename into plot-relevant fields."""
    match = re.match(
        r"(?P<algorithm>naive|hybrid)_len(?P<length>\d+)_5p_(?P<fivep_label>[^_]+)_limit(?P<cutoff>[a-z0-9]+)_seed(?P<seed>\d+)\.xlsx$",
        report_path.name,
    )
    if not match:
        return None
    return {
        "algorithm": match.group("algorithm"),
        "length": int(match.group("length")),
        "fivep_label": match.group("fivep_label"),
        "selected_offtarget_limit_label": match.group("cutoff"),
        "seed": int(match.group("seed")),
    }


def load_limit_label_to_fraction(config_root: Path) -> dict[str, float]:
    """Load the mapping from energy-limit labels to target bound fractions."""
    mapping = {}
    for summary_path in sorted(config_root.glob("*/batch_summary.toml")):
        data = tomllib.loads(summary_path.read_text(encoding="utf-8"))
        for condition in data.get("conditions", []):
            target_fraction = float(condition["target_fraction_bound"])
            derived_offtarget_limit = float(condition["derived_offtarget_limit"])
            mapping.setdefault(format_limit_label(derived_offtarget_limit), target_fraction)
    return mapping


def build_trajectory_df(progress_df: pd.DataFrame) -> pd.DataFrame:
    """Normalize one workbook's search-progress sheet into x/y trajectory rows."""
    required_columns = {"pairs_found", "nupack_calls_executed"}
    if not required_columns.issubset(progress_df.columns):
        raise ValueError(f"search_progress is missing required columns: {required_columns}")

    trajectory_df = progress_df.loc[:, ["pairs_found", "nupack_calls_executed"]].copy()
    trajectory_df["pairs_found"] = pd.to_numeric(trajectory_df["pairs_found"], errors="coerce")
    trajectory_df["nupack_calls_executed"] = pd.to_numeric(
        trajectory_df["nupack_calls_executed"], errors="coerce"
    )
    trajectory_df = trajectory_df.dropna(subset=["pairs_found", "nupack_calls_executed"])
    trajectory_df = trajectory_df.sort_values("nupack_calls_executed").reset_index(drop=True)

    if trajectory_df.empty:
        return trajectory_df

    first_x = float(trajectory_df.iloc[0]["nupack_calls_executed"])
    first_y = float(trajectory_df.iloc[0]["pairs_found"])
    if first_x > 0.0 or first_y > 0.0:
        trajectory_df = pd.concat(
            [
                pd.DataFrame({"pairs_found": [0.0], "nupack_calls_executed": [0.0]}),
                trajectory_df,
            ],
            ignore_index=True,
        )

    return trajectory_df


def collect_trajectories(data_root: Path, limit_label_to_fraction: dict[str, float]) -> list[dict]:
    """Collect trajectory records from all currently available long-seq workbooks."""
    records = []
    for report_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_run_filename(report_path)
        if parsed is None:
            continue

        metadata_df = pd.read_excel(report_path, sheet_name="run_metadata")
        progress_df = pd.read_excel(report_path, sheet_name="search_progress")

        metadata_algorithm = normalize_algorithm_name(read_metadata_value(metadata_df, "algorithm_name"))
        if metadata_algorithm is not None and metadata_algorithm != parsed["algorithm"]:
            raise ValueError(
                f"Algorithm mismatch in {report_path}: filename says {parsed['algorithm']}, "
                f"run_metadata says {metadata_algorithm}."
            )

        length = read_metadata_value(metadata_df, "input.length")
        fivep_ext = read_metadata_value(metadata_df, "input.fivep_ext")
        limit_label = parsed["selected_offtarget_limit_label"]
        target_fraction = limit_label_to_fraction.get(limit_label)
        offtarget_limit = read_metadata_value(metadata_df, "search.offtarget_limit")
        limit_value = float(offtarget_limit) if offtarget_limit is not None else parse_limit_label(limit_label)
        condition_label = f"fb={target_fraction:.2f}" if target_fraction is not None else f"limit={limit_value:.2f}"

        trajectory_df = build_trajectory_df(progress_df)
        if trajectory_df.empty:
            continue

        records.append(
            {
                "report_path": str(report_path),
                "algorithm": metadata_algorithm or parsed["algorithm"],
                "length": int(length) if length is not None else parsed["length"],
                "has_tttt5p": str(fivep_ext or parsed["fivep_label"]).upper() == "TTTT",
                "condition_label": condition_label,
                "target_fraction": target_fraction,
                "trajectory_df": trajectory_df,
            }
        )
    return records


def condition_sort_key(record: dict) -> tuple:
    """Stable ordering for legend entries and plotting order."""
    fraction = record.get("target_fraction")
    fraction_sort = float(fraction) if fraction is not None else float("inf")
    return (
        int(record["length"]),
        fraction_sort,
        record["condition_label"],
        0 if record["algorithm"] == "naive" else 1,
        Path(record["report_path"]).name,
    )


def format_fraction_suffix(target_fraction: float | None) -> str:
    """Build a filesystem-friendly suffix for one target fraction."""
    if target_fraction is None:
        return "unknown_fraction"
    return f"fb_{target_fraction:.2f}".replace(".", "p")


def save_plot(
    fig: plt.Figure,
    output_dir: Path,
    *,
    has_tttt5p: bool,
    target_fraction: float | None,
) -> Path:
    """Write one diagnostic trajectory plot and return its path."""
    suffix = "5p_tttt" if has_tttt5p else "5p_none"
    fraction_suffix = format_fraction_suffix(target_fraction)
    output_path = output_dir / f"{OUTPUT_FILENAME_STEM}_{suffix}_{fraction_suffix}.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    return output_path


def plot_group(
    records: list[dict],
    *,
    has_tttt5p: bool,
    target_fraction: float | None,
) -> tuple[plt.Figure, Path] | None:
    """Plot all trajectories for one extension/fraction group."""
    group_records = sorted(
        [
            record
            for record in records
            if record["has_tttt5p"] == has_tttt5p and record["target_fraction"] == target_fraction
        ],
        key=condition_sort_key,
    )
    if not group_records:
        return None

    fig, ax = plt.subplots(figsize=(11, 7))

    for record in group_records:
        trajectory_df = record["trajectory_df"]
        label = f"L{record['length']} {record['condition_label']} {ALGORITHM_LABELS[record['algorithm']]}"
        ax.plot(
            trajectory_df["nupack_calls_executed"],
            trajectory_df["pairs_found"],
            color=LENGTH_COLORS.get(record["length"], "#333333"),
            linestyle=ALGORITHM_LINESTYLES.get(record["algorithm"], "-."),
            linewidth=1.5,
            alpha=0.9,
            label=label,
        )

    fraction_label = f"fb={target_fraction:.2f}" if target_fraction is not None else "unknown fraction"
    ax.set_title(f"{GROUP_TITLES[has_tttt5p]} | {fraction_label}")
    ax.set_xlabel("NUPACK calls executed")
    ax.set_ylabel("Pairs found")
    ax.grid(True, alpha=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8, frameon=False)
    fig.subplots_adjust(right=0.72)

    output_path = save_plot(
        fig,
        DATA_ROOT,
        has_tttt5p=has_tttt5p,
        target_fraction=target_fraction,
    )
    return fig, output_path


if __name__ == "__main__":
    limit_label_to_fraction = load_limit_label_to_fraction(GENERATED_CONFIG_ROOT)
    records = collect_trajectories(DATA_ROOT, limit_label_to_fraction)
    target_fractions = sorted({record["target_fraction"] for record in records if record["target_fraction"] is not None})

    print(f"data root: {DATA_ROOT}")
    print(f"loaded trajectory files: {len(records)}")

    for has_tttt5p in (False, True):
        for target_fraction in target_fractions:
            plot_result = plot_group(
                records,
                has_tttt5p=has_tttt5p,
                target_fraction=target_fraction,
            )
            if plot_result is None:
                continue
            fig, output_path = plot_result
            print(f"wrote plot: {output_path}")
            plt.close(fig)
