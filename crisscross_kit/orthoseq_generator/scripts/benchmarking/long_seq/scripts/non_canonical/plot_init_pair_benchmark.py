#!/usr/bin/env python3
"""
Plot the long-sequence initial-pair benchmark as clustered bars.

This plotter is intentionally self-contained. It reads the generated batch
summary TOML to recover the expected layout, scans whichever XLSX workbooks
are already present, and plots one clustered bar chart per 5' extension
condition. Each cluster corresponds to one off-target limit within one
sequence length and contains:

    - one Naive bar
    - one Hybrid bar for each configured initial_fresh_pair_count

Missing runs are shown as hatched placeholder bars so incomplete result sets
still produce a useful figure.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["svg.fonttype"] = "none"

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


DATA_ROOT = MODULE_DIR / "data" / "non_canonical" / "test_init_pairs_sigma1p0_seed41"
SUMMARY_PATH = (
    MODULE_DIR
    / "configs"
    / "generated"
    / "test_init_pairs_sigma1p0_seed41"
    / "batch_summary.toml"
)

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

SERIES_ORDER_PREFIX = ["naive"]
SERIES_COLORS = {
    "naive": "#808080",
    "hybrid": "#2A9D8F",
}
OUTPUT_STEM = "long_seq_init_pair_benchmark"

MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.75
FIGURE_HEIGHT_MM = 78.0
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 6
AXIS_LABEL_FONT_SIZE = 5
TICK_LABEL_FONT_SIZE = 5
LEGEND_FONT_SIZE = 5
ANNOTATION_FONT_SIZE = 5

AXIS_LINEWIDTH = 0.5
GRID_LINEWIDTH = 0.5
BAR_EDGE_LINEWIDTH = 0.5


@dataclass(frozen=True)
class ExpectedSlot:
    length: int
    fivep_label: str
    limit_label: str
    limit_value: float
    target_fraction_bound: float
    algorithm: str
    init_count: int | None


def format_limit_label(value: float) -> str:
    """Encode one off-target limit in the workbook filename format."""
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


def parse_float_token(value: str) -> float:
    """Decode a token such as `m8p16` into a float."""
    return float(value.replace("m", "-").replace("p", "."))


def normalize_algorithm_name(value: str | None) -> str | None:
    """Map workbook metadata algorithm names onto the plot labels."""
    if value == "naive_search":
        return "naive"
    if value == "hybrid_search":
        return "hybrid"
    if value is None:
        return None
    return str(value)


def normalize_fivep_label(value: str) -> str:
    """Normalize an extension string into the folder label used by the runs."""
    text = str(value or "")
    return text if text else "none"


def parse_number(text: str | None) -> int | float | None:
    """Convert a numeric metadata string into `int` or `float` when possible."""
    if text is None:
        return None
    stripped = text.strip()
    if stripped == "":
        return None
    try:
        numeric = float(stripped)
    except ValueError:
        return None
    if numeric.is_integer():
        return int(numeric)
    return numeric


def parse_workbook_filename(report_path: Path) -> dict | None:
    """Parse the run identity from one workbook filename."""
    match = re.match(
        (
            r"(?P<algorithm>naive|hybrid)_len(?P<length>\d+)"
            r"_5p_(?P<fivep_label>[^_]+)"
            r"_limit(?P<limit_label>[a-z0-9]+)"
            r"(?:_budget(?P<budget>\d+))?"
            r"(?:_init(?P<init_count>\d+))?"
            r"_seed(?P<seed>\d+)\.xlsx$"
        ),
        report_path.name,
    )
    if not match:
        return None
    init_count = match.group("init_count")
    return {
        "algorithm": match.group("algorithm"),
        "length": int(match.group("length")),
        "fivep_label": match.group("fivep_label"),
        "limit_label": match.group("limit_label"),
        "init_count": None if init_count is None else int(init_count),
        "seed": int(match.group("seed")),
    }


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    """Read the workbook shared string table."""
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(raw)
    shared_strings = []
    for item in root.findall("main:si", NS):
        texts = [node.text or "" for node in item.findall(".//main:t", NS)]
        shared_strings.append("".join(texts))
    return shared_strings


def get_sheet_xml_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    """Resolve a worksheet name to its XML member path inside the workbook."""
    workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
    rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))

    rel_id_to_target = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels_root.findall("pkgrel:Relationship", NS)
    }
    for sheet in workbook_root.findall("main:sheets/main:sheet", NS):
        if sheet.attrib.get("name") != sheet_name:
            continue
        rel_id = sheet.attrib.get(f"{{{NS['rel']}}}id")
        if rel_id is None or rel_id not in rel_id_to_target:
            break
        return f"xl/{rel_id_to_target[rel_id]}"
    raise KeyError(f"Sheet '{sheet_name}' not found.")


def column_from_cell_ref(cell_ref: str) -> str:
    """Extract the Excel column letters from a cell reference such as `B12`."""
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        raise ValueError(f"Unexpected cell reference: {cell_ref}")
    return match.group(1)


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    """Decode one sheet cell into plain text."""
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", NS))

    value_node = cell.find("main:v", NS)
    if value_node is None:
        return ""
    raw_value = value_node.text or ""

    if cell_type == "s":
        return shared_strings[int(raw_value)]
    return raw_value


def read_run_metadata(xlsx_path: Path) -> dict[str, str]:
    """Read the `run_metadata` sheet from one workbook without pandas/openpyxl."""
    with zipfile.ZipFile(xlsx_path) as archive:
        shared_strings = read_shared_strings(archive)
        sheet_xml_path = get_sheet_xml_path(archive, "run_metadata")
        sheet_root = ET.fromstring(archive.read(sheet_xml_path))

    rows = []
    for row in sheet_root.findall("main:sheetData/main:row", NS):
        values_by_column = {}
        for cell in row.findall("main:c", NS):
            cell_ref = cell.attrib.get("r", "")
            values_by_column[column_from_cell_ref(cell_ref)] = read_cell_value(cell, shared_strings)
        if values_by_column:
            rows.append(values_by_column)

    metadata = {}
    for row in rows[1:]:
        key = row.get("A", "").strip()
        if not key:
            continue
        metadata[key] = row.get("B", "").strip()
    return metadata


def load_expected_slots(summary_path: Path) -> tuple[list[ExpectedSlot], list[int]]:
    """Load the expected plotting grid from the generated batch summary TOML."""
    with summary_path.open("rb") as fh:
        summary = tomllib.load(fh)

    expected_slots = []
    init_counts = sorted(
        {
            int(condition["initial_fresh_pair_count"])
            for condition in summary.get("conditions", [])
            if condition.get("algorithm") == "hybrid"
        }
    )
    for condition in summary.get("conditions", []):
        fivep_label = normalize_fivep_label(condition.get("fivep_ext", ""))
        algorithm = str(condition["algorithm"])
        init_count = condition.get("initial_fresh_pair_count")
        if algorithm == "naive":
            init_count = None
        else:
            init_count = int(init_count)
        limit_value = float(condition["derived_offtarget_limit"])
        expected_slots.append(
            ExpectedSlot(
                length=int(condition["length"]),
                fivep_label=fivep_label,
                limit_label=format_limit_label(limit_value),
                limit_value=limit_value,
                target_fraction_bound=float(condition["target_fraction_bound"]),
                algorithm=algorithm,
                init_count=init_count,
            )
        )
    return expected_slots, init_counts


def collect_runs(data_root: Path) -> list[dict]:
    """Collect all currently available benchmark workbooks under one data root."""
    rows = []
    for report_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_workbook_filename(report_path)
        if parsed is None:
            continue

        metadata = read_run_metadata(report_path)
        metadata_algorithm = normalize_algorithm_name(metadata.get("algorithm_name"))
        metadata_length = parse_number(metadata.get("input.length"))
        metadata_limit = parse_number(metadata.get("search.offtarget_limit"))
        metadata_init = parse_number(metadata.get("search.initial_fresh_pair_count"))
        found_pair_count = parse_number(metadata.get("found_pair_count"))

        algorithm = metadata_algorithm or parsed["algorithm"]
        if metadata_algorithm is not None and metadata_algorithm != parsed["algorithm"]:
            raise ValueError(
                f"Algorithm mismatch in {report_path}: filename says {parsed['algorithm']}, "
                f"metadata says {metadata_algorithm}."
            )

        fivep_value = metadata.get("input.fivep_ext", "")
        fivep_label = normalize_fivep_label(fivep_value if fivep_value is not None else parsed["fivep_label"])
        init_count = parsed["init_count"]
        if metadata_init is not None:
            init_count = int(metadata_init)
        if algorithm == "naive":
            init_count = None

        rows.append(
            {
                "report_path": report_path,
                "algorithm": algorithm,
                "length": int(metadata_length) if metadata_length is not None else parsed["length"],
                "fivep_label": fivep_label,
                "limit_label": parsed["limit_label"],
                "offtarget_limit": (
                    float(metadata_limit) if metadata_limit is not None else parse_float_token(parsed["limit_label"])
                ),
                "init_count": init_count,
                "seed": parsed["seed"],
                "found_pair_count": None if found_pair_count is None else int(found_pair_count),
            }
        )
    return rows


def build_series_order(init_counts: list[int]) -> list[tuple[str, int | None]]:
    """Build the left-to-right order of bars inside each subgroup."""
    return [("naive", None)] + [("hybrid", init_count) for init_count in init_counts]


def series_label(algorithm: str, init_count: int | None) -> str:
    """Return the legend label for one series."""
    if algorithm == "naive":
        return "Naive"
    return f"H{init_count}"


def build_expected_lookup(expected_slots: list[ExpectedSlot]) -> dict[tuple, ExpectedSlot]:
    """Index expected slots by their plotting key."""
    return {
        (slot.length, slot.fivep_label, slot.limit_label, slot.algorithm, slot.init_count): slot
        for slot in expected_slots
    }


def build_run_lookup(runs: list[dict]) -> dict[tuple, dict]:
    """Index observed runs by the same plotting key."""
    return {
        (row["length"], row["fivep_label"], row["limit_label"], row["algorithm"], row["init_count"]): row
        for row in runs
    }


def compute_subgroups(expected_slots: list[ExpectedSlot], fivep_label: str) -> list[tuple[int, str, float, float]]:
    """Return the ordered `(length, limit_label, limit_value, target_fraction)` subgroups."""
    unique = {}
    for slot in expected_slots:
        if slot.fivep_label != fivep_label:
            continue
        key = (slot.length, slot.limit_label)
        unique.setdefault(key, (slot.length, slot.limit_label, slot.limit_value, slot.target_fraction_bound))
    return [
        unique[key]
        for key in sorted(unique, key=lambda item: (item[0], unique[item][2], unique[item][1]))
    ]


def compute_y_max(runs: list[dict]) -> float:
    """Compute a shared y-axis maximum across the observed bars."""
    values = [row["found_pair_count"] for row in runs if row["found_pair_count"] is not None]
    if not values:
        return 1.0
    return max(1.0, max(values) * 1.08 + 2.0)


def plot_fivep_group(
    *,
    fivep_label: str,
    expected_slots: list[ExpectedSlot],
    runs: list[dict],
    init_counts: list[int],
    output_dir: Path,
) -> Path | None:
    """Plot one 5' extension condition and return the output path."""
    subgroups = compute_subgroups(expected_slots, fivep_label)
    if not subgroups:
        return None

    series_order = build_series_order(init_counts)
    run_lookup = build_run_lookup(runs)
    shared_y_max = compute_y_max(runs)
    missing_stub_height = max(0.8, shared_y_max * 0.035)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)

    bar_width = 0.30
    subgroup_gap = 0.20
    length_gap = 0.95

    xticks = []
    xticklabels = []
    length_annotations = []

    lengths = sorted({length for length, _, _, _ in subgroups})
    subgroups_by_length = defaultdict(list)
    for subgroup in subgroups:
        subgroups_by_length[subgroup[0]].append(subgroup)

    current_x = 0.0
    for length in lengths:
        length_start = current_x
        length_peak = 0.0
        group = subgroups_by_length[length]

        for subgroup_index, (_, limit_label, limit_value, target_fraction) in enumerate(group):
            subgroup_start = current_x
            subgroup_peak = 0.0

            for series_index, (algorithm, init_count) in enumerate(series_order):
                x = subgroup_start + series_index * bar_width
                key = (length, fivep_label, limit_label, algorithm, init_count)
                row = run_lookup.get(key)

                is_missing = row is None or row.get("found_pair_count") is None
                if is_missing:
                    ax.bar(
                        x,
                        missing_stub_height,
                        width=bar_width,
                        facecolor="white",
                        edgecolor="#9A9A9A",
                        linewidth=BAR_EDGE_LINEWIDTH,
                        hatch="///",
                        zorder=3,
                    )
                else:
                    value = float(row["found_pair_count"])
                    subgroup_peak = max(subgroup_peak, value)
                    length_peak = max(length_peak, value)
                    color = SERIES_COLORS["naive"] if algorithm == "naive" else SERIES_COLORS["hybrid"]
                    ax.bar(
                        x,
                        value,
                        width=bar_width,
                        facecolor=color,
                        edgecolor="black",
                        linewidth=BAR_EDGE_LINEWIDTH,
                        alpha=1.0,
                        zorder=3,
                    )

            subgroup_center = subgroup_start + 0.5 * (len(series_order) - 1) * bar_width
            xticks.append(subgroup_center)
            xticklabels.append(f"{limit_value:.2f}\nfb={target_fraction:.2f}")
            current_x += len(series_order) * bar_width
            if subgroup_index != len(group) - 1:
                current_x += subgroup_gap

        length_end = current_x - bar_width
        length_center = 0.5 * (length_start + length_end)
        length_annotations.append((length_center, length, length_peak))
        current_x += length_gap

    title_suffix = f"5' extension: {fivep_label}" if fivep_label != "none" else "No 5' extension"
    ax.set_title(title_suffix, fontsize=TITLE_FONT_SIZE, pad=7)
    ax.set_xlabel("Off-target limit (kcal/mol)", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Number of pairs found", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_ylim(0, shared_y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=0)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=2)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    ax.grid(axis="y", color="#B5B5B5", linewidth=GRID_LINEWIDTH, alpha=0.8)
    ax.set_axisbelow(True)

    handles = [
        Patch(facecolor=SERIES_COLORS["naive"], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label="Naive"),
        Patch(facecolor=SERIES_COLORS["hybrid"], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label="Hybrid"),
        Patch(facecolor="white", edgecolor="#9A9A9A", linewidth=BAR_EDGE_LINEWIDTH, hatch="///", label="Missing"),
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        handlelength=1.2,
        borderaxespad=0.2,
    )

    if xticks:
        for subgroup_center in xticks:
            for series_index, (algorithm, init_count) in enumerate(series_order):
                x = subgroup_center - 0.5 * (len(series_order) - 1) * bar_width + series_index * bar_width
                ax.text(
                    x,
                    -shared_y_max * 0.055,
                    series_label(algorithm, init_count),
                    rotation=90,
                    ha="center",
                    va="top",
                    fontsize=TICK_LABEL_FONT_SIZE,
                    clip_on=False,
                )

    for x_pos, length, peak in length_annotations:
        label_y = min(shared_y_max * 0.97, peak + shared_y_max * 0.09 if peak > 0 else shared_y_max * 0.92)
        ax.text(
            x_pos,
            label_y,
            f"Length = {length}",
            ha="center",
            va="top",
            fontsize=ANNOTATION_FONT_SIZE,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    fig.subplots_adjust(left=0.12, right=0.99, bottom=0.30, top=0.88)
    output_path = output_dir / f"{OUTPUT_STEM}_5p_{fivep_label}.svg"
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    return output_path


def summarize_missing_slots(expected_slots: list[ExpectedSlot], runs: list[dict]) -> list[ExpectedSlot]:
    """Return expected slots that do not yet have a workbook."""
    expected_lookup = build_expected_lookup(expected_slots)
    run_lookup = build_run_lookup(runs)
    missing = []
    for key, slot in expected_lookup.items():
        if key not in run_lookup:
            missing.append(slot)
    return sorted(
        missing,
        key=lambda slot: (slot.fivep_label, slot.length, slot.limit_value, slot.algorithm, slot.init_count or -1),
    )


def main() -> None:
    """Parse arguments, load runs, and write the benchmark figure(s)."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DATA_ROOT,
        help="Directory containing len*/5p_* benchmark workbooks.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=SUMMARY_PATH,
        help="Generated batch_summary.toml for the benchmark batch.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for the output SVGs. Defaults to --data-root.",
    )
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    summary_path = args.summary.resolve()
    output_dir = data_root if args.output_dir is None else args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    expected_slots, init_counts = load_expected_slots(summary_path)
    runs = collect_runs(data_root)
    missing_slots = summarize_missing_slots(expected_slots, runs)

    print(f"data root: {data_root}")
    print(f"batch summary: {summary_path}")
    print(f"loaded workbooks: {len(runs)}")
    print(f"expected slots: {len(expected_slots)}")
    print(f"missing slots: {len(missing_slots)}")

    if missing_slots:
        print("missing:")
        for slot in missing_slots:
            init_label = "naive" if slot.algorithm == "naive" else f"init{slot.init_count}"
            print(
                f"  5p_{slot.fivep_label} len{slot.length} limit{slot.limit_label} "
                f"{slot.algorithm} {init_label}"
            )

    fivep_labels = sorted({slot.fivep_label for slot in expected_slots})
    for fivep_label in fivep_labels:
        output_path = plot_fivep_group(
            fivep_label=fivep_label,
            expected_slots=expected_slots,
            runs=[row for row in runs if row["fivep_label"] == fivep_label],
            init_counts=init_counts,
            output_dir=output_dir,
        )
        if output_path is not None:
            print(f"wrote plot: {output_path}")


if __name__ == "__main__":
    main()
