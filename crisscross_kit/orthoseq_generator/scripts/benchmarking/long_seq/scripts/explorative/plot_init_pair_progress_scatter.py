#!/usr/bin/env python3
"""
Plot seed/collection progress points for the init-pair benchmark batch.

For each fixed `(length, fivep extension, off-target limit)` condition, this
script creates one scatter plot containing all available init sizes. Each
hybrid workbook contributes up to two points from `search_progress`:

    - `pass == "seed"`
    - `pass == "collection"`

with:

    x = pairs_collected
    y = pairs_after_vc

Color encodes init size and marker shape encodes pass.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

matplotlib.rcParams["font.family"] = "Arial"

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


DATA_ROOT = MODULE_DIR / "data" / "test_init_pairs_sigma1p0_seed41"
OUTPUT_STEM = "long_seq_init_pair_progress"

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

INIT_COLORS = {
    225: "#2A9D8F",
    450: "#577590",
    900: "#8E6C8A",
}
PASS_MARKERS = {
    "seed": "o",
    "collection": "s",
}


@dataclass(frozen=True)
class ProgressPoint:
    length: int
    fivep_label: str
    limit_label: str
    limit_value: float
    init_count: int
    pass_name: str
    pairs_collected: int
    pairs_after_vc: int


@dataclass(frozen=True)
class NaiveTrajectoryPoint:
    length: int
    fivep_label: str
    limit_label: str
    limit_value: float
    nupack_calls_executed: float
    pairs_found: float


def er_basis(value: float) -> float | None:
    """Return the basis `ln(n)` for `n > 1`."""
    if value <= 1.0:
        return None
    return math.log(value)


def fit_er_log_estimator(points: list[ProgressPoint]) -> tuple[float, float] | None:
    """Fit `y = a * ln(n) + b` by least squares."""
    basis_values = []
    y_values = []
    for point in points:
        basis = er_basis(float(point.pairs_collected))
        if basis is None:
            continue
        basis_values.append(basis)
        y_values.append(float(point.pairs_after_vc))

    if len(basis_values) < 2:
        return None

    basis_array = np.asarray(basis_values, dtype=float)
    y_array = np.asarray(y_values, dtype=float)
    design = np.column_stack([basis_array, np.ones_like(basis_array)])
    coefficients, _, rank, _ = np.linalg.lstsq(design, y_array, rcond=None)
    if rank < 2:
        return None
    return float(coefficients[0]), float(coefficients[1])


def fit_naive_log1p_model(points: list[NaiveTrajectoryPoint]) -> tuple[float, float] | None:
    """
    Fit the transformed-variable model with ordinary least squares.

    Let `u = ln(x)` with `x = nupack_calls_executed`, then fit

        y = a * ln(1 + exp(u) / b)

    by ordinary least squares. The plot is still rendered on the raw `x` axis.
    """
    if len(points) < 3:
        return None

    x_values = np.asarray([point.nupack_calls_executed for point in points], dtype=float)
    y_values = np.asarray([point.pairs_found for point in points], dtype=float)
    if np.any(x_values <= 0.0) or np.any(y_values < 0.0):
        return None

    x_max = float(np.max(x_values))
    if x_max <= 0.0:
        return None
    u_values = np.log(x_values)

    log_b_low = math.log(max(x_max * 1e-6, 1e-12))
    log_b_high = math.log(max(x_max * 1e2, 1e-6))

    best_a = float("nan")
    best_b = float("nan")
    best_sse = float("inf")

    for _ in range(8):
        b_grid = np.exp(np.linspace(log_b_low, log_b_high, 160))
        sse_values = np.empty(len(b_grid), dtype=float)
        a_values = np.empty(len(b_grid), dtype=float)
        for idx, b_value in enumerate(b_grid):
            basis = np.log1p(np.exp(u_values) / b_value)
            denominator = float(np.dot(basis, basis))
            if denominator <= 0.0:
                a_value = 0.0
            else:
                a_value = float(np.dot(basis, y_values) / denominator)
            if a_value <= 0.0:
                a_value = 1e-12
            residual = y_values - a_value * basis
            sse_values[idx] = float(np.dot(residual, residual))
            a_values[idx] = a_value

        best_idx = int(np.argmin(sse_values))
        best_b = float(b_grid[best_idx])
        best_a = float(a_values[best_idx])
        best_sse = float(sse_values[best_idx])

        log_step = (log_b_high - log_b_low) / max(len(b_grid) - 1, 1)
        best_log_b = math.log(best_b)
        log_b_low = best_log_b - 3.0 * log_step
        log_b_high = best_log_b + 3.0 * log_step

    if not math.isfinite(best_a) or not math.isfinite(best_b):
        return None
    return best_a, best_b


def evaluate_naive_log1p_model(a_value: float, b_value: float, x_values: np.ndarray) -> np.ndarray:
    """Evaluate `a * ln(1 + x / b)`."""
    return a_value * np.log1p(x_values / b_value)


def parse_float_token(value: str) -> float:
    """Decode a token such as `m8p16` into a float."""
    return float(value.replace("m", "-").replace("p", "."))


def normalize_fivep_label(value: str) -> str:
    """Normalize a 5' extension string into the folder label used on disk."""
    text = str(value or "")
    return text if text else "none"


def parse_numeric(text: str | None) -> int | float | None:
    """Convert numeric-like workbook cell text into `int` or `float`."""
    if text is None:
        return None
    stripped = text.strip()
    if stripped in {"", "N.A."}:
        return None
    try:
        number = float(stripped)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


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
    if match is None:
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
    """Load the workbook shared string table."""
    try:
        raw = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(raw)
    return [
        "".join(node.text or "" for node in item.findall(".//main:t", NS))
        for item in root.findall("main:si", NS)
    ]


def get_sheet_xml_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    """Resolve a sheet name to its XML member path inside the workbook."""
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
        if rel_id is not None:
            return f"xl/{rel_id_to_target[rel_id]}"
    raise KeyError(f"Sheet '{sheet_name}' not found.")


def column_from_cell_ref(cell_ref: str) -> str:
    """Extract the Excel column letters from a cell reference."""
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        raise ValueError(f"Unexpected cell reference: {cell_ref}")
    return match.group(1)


def read_cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    """Decode one XML cell into plain text."""
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


def read_sheet_rows(xlsx_path: Path, sheet_name: str) -> list[dict[str, str]]:
    """Read one worksheet into row dictionaries keyed by column letter."""
    with zipfile.ZipFile(xlsx_path) as archive:
        shared_strings = read_shared_strings(archive)
        sheet_xml_path = get_sheet_xml_path(archive, sheet_name)
        sheet_root = ET.fromstring(archive.read(sheet_xml_path))

    rows = []
    for row in sheet_root.findall("main:sheetData/main:row", NS):
        values_by_column = {}
        for cell in row.findall("main:c", NS):
            cell_ref = cell.attrib.get("r", "")
            values_by_column[column_from_cell_ref(cell_ref)] = read_cell_value(cell, shared_strings)
        rows.append(values_by_column)
    return rows


def read_table_rows(xlsx_path: Path, sheet_name: str) -> list[dict[str, str]]:
    """Read a tabular worksheet using the first row as the header."""
    rows = read_sheet_rows(xlsx_path, sheet_name)
    if not rows:
        return []
    header_row = rows[0]
    header_map = {column: value for column, value in header_row.items() if value}
    records = []
    for row in rows[1:]:
        record = {}
        for column, header in header_map.items():
            record[str(header)] = row.get(column, "")
        if any(value != "" for value in record.values()):
            records.append(record)
    return records


def collect_progress_points(data_root: Path) -> list[ProgressPoint]:
    """Collect seed/collection `(pairs_collected, pairs_after_vc)` points from hybrid workbooks."""
    points = []
    for report_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_workbook_filename(report_path)
        if parsed is None or parsed["algorithm"] != "hybrid":
            continue

        search_progress_rows = read_table_rows(report_path, "search_progress")
        for row in search_progress_rows:
            pass_name = row.get("pass", "")
            if pass_name not in PASS_MARKERS:
                continue
            pairs_collected = parse_numeric(row.get("pairs_collected"))
            pairs_after_vc = parse_numeric(row.get("pairs_after_vc"))
            if pairs_collected is None or pairs_after_vc is None:
                continue
            points.append(
                ProgressPoint(
                    length=int(parsed["length"]),
                    fivep_label=normalize_fivep_label(parsed["fivep_label"]),
                    limit_label=parsed["limit_label"],
                    limit_value=parse_float_token(parsed["limit_label"]),
                    init_count=int(parsed["init_count"]),
                    pass_name=pass_name,
                    pairs_collected=int(pairs_collected),
                    pairs_after_vc=int(pairs_after_vc),
                )
            )
    return points


def collect_naive_trajectory_points(data_root: Path) -> list[NaiveTrajectoryPoint]:
    """Collect naive `(nupack_calls_executed, pairs_found)` trajectory points."""
    points = []
    for report_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_workbook_filename(report_path)
        if parsed is None or parsed["algorithm"] != "naive":
            continue

        search_progress_rows = read_table_rows(report_path, "search_progress")
        for row in search_progress_rows:
            if row.get("step") != "accepted_pair":
                continue
            nupack_calls_executed = parse_numeric(row.get("nupack_calls_executed"))
            pairs_found = parse_numeric(row.get("pairs_found"))
            if nupack_calls_executed is None or pairs_found is None:
                continue
            points.append(
                NaiveTrajectoryPoint(
                    length=int(parsed["length"]),
                    fivep_label=normalize_fivep_label(parsed["fivep_label"]),
                    limit_label=parsed["limit_label"],
                    limit_value=parse_float_token(parsed["limit_label"]),
                    nupack_calls_executed=float(nupack_calls_executed),
                    pairs_found=float(pairs_found),
                )
            )
    return points


def plot_condition(points: list[ProgressPoint], output_dir: Path) -> Path:
    """Plot one condition's seed/collection progress points and return the saved path."""
    first = points[0]
    condition_title = f"len{first.length}, 5p_{first.fivep_label}, limit {first.limit_value:.2f}"

    fig, ax = plt.subplots(figsize=(5.8, 4.8))

    x_values = [point.pairs_collected for point in points]
    y_values = [point.pairs_after_vc for point in points]
    x_max = max(x_values) if x_values else 1
    y_max = max(y_values) if y_values else 1
    er_log_fit = fit_er_log_estimator(points)

    for point in sorted(points, key=lambda item: (item.init_count, item.pass_name)):
        color = INIT_COLORS.get(point.init_count, "#6C757D")
        marker = PASS_MARKERS[point.pass_name]
        ax.scatter(
            point.pairs_collected,
            point.pairs_after_vc,
            s=58,
            color=color,
            marker=marker,
            edgecolors="black",
            linewidths=0.5,
            zorder=3,
        )
        ax.annotate(
            f"I{point.init_count}",
            (point.pairs_collected, point.pairs_after_vc),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
            color=color,
        )

    if er_log_fit is not None:
        er_log_a, er_log_b = er_log_fit
        x_curve = np.linspace(max(1.0, min(x_values)), x_max * 1.03, 400)
        basis_values = np.array([er_basis(float(value)) for value in x_curve], dtype=float)
        y_curve = er_log_a * basis_values + er_log_b
        ax.plot(
            x_curve,
            y_curve,
            color="#E76F51",
            linewidth=1.6,
            label="Erdos-Renyi estimator",
            zorder=2,
        )

    ax.set_title(condition_title, fontsize=10)
    ax.set_xlabel("pairs_collected")
    ax.set_ylabel("pairs_after_vc")
    ax.set_xlim(-0.03 * x_max, x_max * 1.08)
    ax.set_ylim(-0.03 * y_max, y_max * 1.10)
    ax.grid(True, color="#D0D0D0", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)

    init_legend_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markerfacecolor=INIT_COLORS.get(init_count, "#6C757D"),
            markeredgecolor="black",
            markeredgewidth=0.5,
            markersize=7,
            label=f"init{init_count}",
        )
        for init_count in sorted({point.init_count for point in points})
    ]
    pass_legend_handles = [
        Line2D(
            [0],
            [0],
            marker=PASS_MARKERS[pass_name],
            linestyle="None",
            markerfacecolor="white",
            markeredgecolor="black",
            markeredgewidth=0.8,
            markersize=7,
            label=pass_name,
        )
        for pass_name in ("seed", "collection")
        if any(point.pass_name == pass_name for point in points)
    ]
    estimator_handles = []
    if er_log_fit is not None:
        estimator_handles.append(
            Line2D(
                [0],
                [0],
                color="#E76F51",
                linewidth=1.6,
                label="Erdos-Renyi estimator",
            )
        )
    legend_handles = init_legend_handles + pass_legend_handles + estimator_handles
    ax.legend(
        handles=legend_handles,
        loc="upper left",
        frameon=True,
        facecolor="white",
        edgecolor="none",
        fontsize=8,
        ncol=1,
    )
    if er_log_fit is not None:
        ax.text(
            0.99,
            0.01,
            f"y = {er_log_a:.3f} ln(n) + {er_log_b:.3f}",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3},
        )

    fig.tight_layout()
    output_path = output_dir / (
        f"{OUTPUT_STEM}_len{first.length}_5p_{first.fivep_label}_limit{first.limit_label}.png"
    )
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_naive_condition(points: list[NaiveTrajectoryPoint], output_dir: Path) -> Path | None:
    """Plot one naive trajectory fit per condition and return the saved path."""
    if not points:
        return None

    fit = fit_naive_log1p_model(points)
    if fit is None:
        return None
    a_value, b_value = fit

    tail_points = [
        point
        for point in points
        if 2_000_000.0 <= point.nupack_calls_executed <= 5_000_000.0
    ]
    tail_fit = fit_naive_log1p_model(tail_points) if len(tail_points) >= 3 else None

    first = points[0]
    condition_title = f"Naive fit: len{first.length}, 5p_{first.fivep_label}, limit {first.limit_value:.2f}"
    x_values = np.asarray([point.nupack_calls_executed for point in points], dtype=float)
    y_values = np.asarray([point.pairs_found for point in points], dtype=float)

    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    ax.scatter(
        x_values,
        y_values,
        s=22,
        color="#264653",
        alpha=0.85,
        edgecolors="black",
        linewidths=0.3,
        label="Naive trajectory",
        zorder=3,
    )

    x_grid = np.linspace(0.0, float(np.max(x_values)) * 1.02, 500)
    y_grid = evaluate_naive_log1p_model(a_value, b_value, x_grid)
    ax.plot(
        x_grid,
        y_grid,
        color="#E76F51",
        linewidth=1.7,
        label="Full log-x OLS fit",
        zorder=2,
    )

    tail_summary_lines = []
    if tail_fit is not None:
        tail_a_value, tail_b_value = tail_fit
        tail_x_grid = np.linspace(0.0, float(np.max(x_values)) * 1.02, 500)
        tail_y_grid = evaluate_naive_log1p_model(tail_a_value, tail_b_value, tail_x_grid)
        ax.plot(
            tail_x_grid,
            tail_y_grid,
            color="#2A9D8F",
            linewidth=1.7,
            linestyle="--",
            label="Tail fit (2e6-5e6)",
            zorder=2,
        )
        tail_summary_lines.extend(
            [
                f"tail: y = {tail_a_value:.3f} ln(1 + x / {tail_b_value:.3f})",
                f"tail window points = {len(tail_points)}",
            ]
        )

    ax.set_title(condition_title, fontsize=10)
    ax.set_xlabel("nupack_calls_executed")
    ax.set_ylabel("pairs_found")
    ax.grid(True, color="#D0D0D0", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=False, fontsize=8)
    ax.text(
        0.99,
        0.01,
        "\n".join(
            [
                f"full: y = {a_value:.3f} ln(1 + x / {b_value:.3f})",
                "fit in u = ln(x) with OLS",
                *tail_summary_lines,
            ]
        ),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3},
    )

    fig.tight_layout()
    output_path = output_dir / (
        f"{OUTPUT_STEM}_naive_fit_len{first.length}_5p_{first.fivep_label}_limit{first.limit_label}.png"
    )
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    """Collect hybrid progress points and write one plot per condition."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DATA_ROOT,
        help="Directory containing the batch workbooks.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for output plots. Defaults to --data-root.",
    )
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    output_dir = data_root if args.output_dir is None else args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    points = collect_progress_points(data_root)
    naive_points = collect_naive_trajectory_points(data_root)
    grouped = defaultdict(list)
    for point in points:
        grouped[(point.length, point.fivep_label, point.limit_label)].append(point)
    naive_grouped = defaultdict(list)
    for point in naive_points:
        naive_grouped[(point.length, point.fivep_label, point.limit_label)].append(point)

    print(f"data root: {data_root}")
    print(f"conditions: {len(grouped)}")
    print(f"points: {len(points)}")
    print(f"naive trajectory points: {len(naive_points)}")

    for key in sorted(grouped, key=lambda item: (item[0], item[1], parse_float_token(item[2]), item[2])):
        output_path = plot_condition(grouped[key], output_dir)
        print(f"wrote plot: {output_path}")
        naive_output_path = plot_naive_condition(naive_grouped.get(key, []), output_dir)
        if naive_output_path is not None:
            print(f"wrote naive fit: {naive_output_path}")


if __name__ == "__main__":
    main()
