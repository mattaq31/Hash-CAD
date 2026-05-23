#!/usr/bin/env python3
"""
Plot hybrid empirical rates against naive proxy-fit rates for init-pair runs.

For each `(length, off-target limit, init)` hybrid run this script plots:

    - the empirical hybrid collection-pass acceptance rate
    - the naive proxy-fit local rate evaluated at that run's seed-set size

The naive proxy scaling factor `rho = passed_homodimer / attempts` is taken
from the `init900` hybrid run for the matching `(length, fivep, limit)` when
available. If that workbook is missing, the script falls back to the largest
available init count for that condition.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import math
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
from matplotlib.lines import Line2D
import numpy as np

matplotlib.rcParams["font.family"] = "Arial"
matplotlib.rcParams["svg.fonttype"] = "none"

MODULE_DIR = Path(__file__).resolve().parents[2]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))


DATA_ROOT = MODULE_DIR / "data" / "test_init_pairs_sigma1p0_seed41"
SUMMARY_PATH = (
    MODULE_DIR
    / "configs"
    / "generated"
    / "test_init_pairs_sigma1p0_seed41"
    / "batch_summary.toml"
)
OUTPUT_STEM = "long_seq_init_pair_rate_benchmark"
CONFLICT_OUTPUT_STEM = "long_seq_init_pair_conflict_benchmark"

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

MM_PER_INCH = 25.4
FIGURE_WIDTH_MM = 177.8 * 0.82
FIGURE_HEIGHT_MM = 82.0
FIGURE_SIZE_INCHES = (FIGURE_WIDTH_MM / MM_PER_INCH, FIGURE_HEIGHT_MM / MM_PER_INCH)

TITLE_FONT_SIZE = 6
AXIS_LABEL_FONT_SIZE = 5
TICK_LABEL_FONT_SIZE = 5
LEGEND_FONT_SIZE = 5
ANNOTATION_FONT_SIZE = 5

AXIS_LINEWIDTH = 0.5
GRID_LINEWIDTH = 0.5
BAR_EDGE_LINEWIDTH = 0.5

BAR_COLORS = {
    "hybrid_empirical": "#E76F51",
    "naive_proxy": "#2A9D8F",
}


@dataclass(frozen=True)
class ExpectedHybridSlot:
    length: int
    fivep_label: str
    limit_label: str
    limit_value: float
    target_fraction_bound: float
    init_count: int


@dataclass
class HybridRunSummary:
    report_path: Path
    length: int
    fivep_label: str
    limit_label: str
    offtarget_limit: float
    init_count: int
    seed_size: int | None
    empirical_rate: float | None
    pooled_rho: float | None


@dataclass
class NaiveRunSummary:
    report_path: Path
    length: int
    fivep_label: str
    limit_label: str
    offtarget_limit: float
    raw_attempts: np.ndarray
    pairs_found: np.ndarray


@dataclass(frozen=True)
class FitDiagnosticPoint:
    init_count: int
    seed_size: int
    empirical_rate: float | None
    naive_rate: float | None


def format_limit_label(value: float) -> str:
    """Encode one off-target limit in the workbook filename format."""
    return f"{value:.2f}".replace("-", "m").replace(".", "p")


def parse_float_token(value: str) -> float:
    """Decode a token such as `m8p16` into a float."""
    return float(value.replace("m", "-").replace("p", "."))


def normalize_fivep_label(value: str) -> str:
    """Normalize a 5' extension string into the folder label used on disk."""
    text = str(value or "")
    return text if text else "none"


def parse_numeric(text: str | None) -> int | float | None:
    """Convert a numeric-like cell text into `int` or `float`."""
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
    """Parse the benchmark identity from one workbook filename."""
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
    """Read one worksheet into a list of row dictionaries keyed by column letter."""
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


def read_run_metadata(xlsx_path: Path) -> dict[str, str]:
    """Read the `run_metadata` sheet into a key-value dictionary."""
    rows = read_sheet_rows(xlsx_path, "run_metadata")
    metadata = {}
    for row in rows[1:]:
        key = row.get("A", "").strip()
        if key:
            metadata[key] = row.get("B", "").strip()
    return metadata


def read_table_rows(xlsx_path: Path, sheet_name: str) -> list[dict[str, str]]:
    """Read a tabular worksheet using its first row as the header."""
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


def load_expected_hybrid_slots(summary_path: Path) -> tuple[list[ExpectedHybridSlot], list[int]]:
    """Load the expected hybrid plotting grid from the batch summary TOML."""
    with summary_path.open("rb") as fh:
        summary = tomllib.load(fh)

    slots = []
    init_counts = sorted(
        {
            int(condition["initial_fresh_pair_count"])
            for condition in summary.get("conditions", [])
            if condition.get("algorithm") == "hybrid"
        }
    )
    for condition in summary.get("conditions", []):
        if condition.get("algorithm") != "hybrid":
            continue
        limit_value = float(condition["derived_offtarget_limit"])
        slots.append(
            ExpectedHybridSlot(
                length=int(condition["length"]),
                fivep_label=normalize_fivep_label(condition.get("fivep_ext", "")),
                limit_label=format_limit_label(limit_value),
                limit_value=limit_value,
                target_fraction_bound=float(condition["target_fraction_bound"]),
                init_count=int(condition["initial_fresh_pair_count"]),
            )
        )
    return slots, init_counts


def extract_hybrid_summary(report_path: Path) -> HybridRunSummary:
    """Extract the rate-relevant statistics from one hybrid workbook."""
    parsed = parse_workbook_filename(report_path)
    if parsed is None or parsed["algorithm"] != "hybrid":
        raise ValueError(f"Unexpected hybrid workbook filename: {report_path}")

    metadata = read_run_metadata(report_path)
    search_progress_rows = read_table_rows(report_path, "search_progress")

    pooled_attempts = 0.0
    pooled_passed_homodimer = 0.0
    seed_size = None
    empirical_rate = None

    for row in search_progress_rows:
        pass_name = row.get("pass", "")
        attempts = parse_numeric(row.get("attempts"))
        passed_homodimer = parse_numeric(row.get("passed_homodimer"))
        accepted_into_pool = parse_numeric(row.get("accepted_into_pool"))

        if attempts is not None:
            pooled_attempts += float(attempts)
        if passed_homodimer is not None:
            pooled_passed_homodimer += float(passed_homodimer)

        if pass_name == "seed":
            total_retained = parse_numeric(row.get("total_retained"))
            pairs_after_vc = parse_numeric(row.get("pairs_after_vc"))
            if total_retained is not None:
                seed_size = int(total_retained)
            elif pairs_after_vc is not None:
                seed_size = int(pairs_after_vc)
            elif accepted_into_pool is not None:
                seed_size = int(accepted_into_pool)
            elif passed_homodimer is not None:
                seed_size = int(passed_homodimer)
        elif pass_name == "collection":
            if accepted_into_pool is not None and passed_homodimer is not None and float(passed_homodimer) > 0.0:
                empirical_rate = float(float(accepted_into_pool) / float(passed_homodimer))

    pooled_rho = None
    if pooled_attempts > 0.0:
        pooled_rho = float(pooled_passed_homodimer / pooled_attempts)

    length = parse_numeric(metadata.get("input.length"))
    offtarget_limit = parse_numeric(metadata.get("search.offtarget_limit"))
    fivep_label = normalize_fivep_label(metadata.get("input.fivep_ext", parsed["fivep_label"]))
    init_count = parse_numeric(metadata.get("search.initial_fresh_pair_count"))

    return HybridRunSummary(
        report_path=report_path,
        length=int(length) if length is not None else parsed["length"],
        fivep_label=fivep_label,
        limit_label=parsed["limit_label"],
        offtarget_limit=float(offtarget_limit) if offtarget_limit is not None else parse_float_token(parsed["limit_label"]),
        init_count=int(init_count) if init_count is not None else int(parsed["init_count"]),
        seed_size=seed_size,
        empirical_rate=empirical_rate,
        pooled_rho=pooled_rho,
    )


def extract_naive_trajectory_rows(search_progress_rows: list[dict[str, str]]) -> tuple[np.ndarray, np.ndarray]:
    """Normalize naive progress rows into raw-attempt and pairs-found arrays."""
    if not search_progress_rows:
        raise ValueError("Naive workbook has an empty search_progress sheet.")

    header_names = set(search_progress_rows[0].keys())
    if {"step", "attempt", "pairs_found"}.issubset(header_names):
        points = []
        for row in search_progress_rows:
            if row.get("step") != "accepted_pair":
                continue
            attempt = parse_numeric(row.get("attempt"))
            pairs_found = parse_numeric(row.get("pairs_found"))
            if attempt is None or pairs_found is None:
                continue
            points.append((float(attempt), float(pairs_found)))
    elif {"attempts", "accepted_into_pool", "pass"}.issubset(header_names):
        points = []
        for row in search_progress_rows:
            if row.get("pass") != "naive":
                continue
            attempts = parse_numeric(row.get("attempts"))
            accepted_into_pool = parse_numeric(row.get("accepted_into_pool"))
            if attempts is None or accepted_into_pool is None:
                continue
            points.append((float(attempts), float(accepted_into_pool)))
    else:
        raise ValueError("Naive search_progress has an unsupported format.")

    if not points:
        raise ValueError("Naive workbook does not contain an accepted-pair trajectory.")

    points.sort(key=lambda item: item[0])
    raw_attempts = np.array([0.0] + [point[0] for point in points], dtype=float)
    pairs_found = np.array([0.0] + [point[1] for point in points], dtype=float)
    return raw_attempts, pairs_found


def extract_naive_summary(report_path: Path) -> NaiveRunSummary:
    """Extract the naive accepted-pair trajectory from one workbook."""
    parsed = parse_workbook_filename(report_path)
    if parsed is None or parsed["algorithm"] != "naive":
        raise ValueError(f"Unexpected naive workbook filename: {report_path}")

    metadata = read_run_metadata(report_path)
    search_progress_rows = read_table_rows(report_path, "search_progress")
    raw_attempts, pairs_found = extract_naive_trajectory_rows(search_progress_rows)

    length = parse_numeric(metadata.get("input.length"))
    offtarget_limit = parse_numeric(metadata.get("search.offtarget_limit"))
    fivep_label = normalize_fivep_label(metadata.get("input.fivep_ext", parsed["fivep_label"]))

    return NaiveRunSummary(
        report_path=report_path,
        length=int(length) if length is not None else parsed["length"],
        fivep_label=fivep_label,
        limit_label=parsed["limit_label"],
        offtarget_limit=float(offtarget_limit) if offtarget_limit is not None else parse_float_token(parsed["limit_label"]),
        raw_attempts=raw_attempts,
        pairs_found=pairs_found,
    )


def fit_log_model(x_values: np.ndarray, y_values: np.ndarray) -> tuple[float, float, float]:
    """Fit `s(t) = a * ln(1 + b t)` by grid search with refinement."""
    if len(x_values) != len(y_values) or len(x_values) < 3:
        raise ValueError("Need at least three trajectory points to fit the log model.")
    if np.any(x_values < 0.0) or np.any(y_values < 0.0):
        raise ValueError("Trajectory values must be non-negative.")

    x_max = float(np.max(x_values))
    y_max = float(np.max(y_values))
    if x_max <= 0.0 or y_max <= 0.0:
        raise ValueError("Trajectory must extend beyond the origin to fit the log model.")

    log_b_low = math.log(max(x_max * 1e-8, 1e-14))
    log_b_high = math.log(max(x_max, 1e-9))

    best_a = float("nan")
    best_b = float("nan")
    best_sse = float("inf")

    for _ in range(8):
        b_grid = np.exp(np.linspace(log_b_low, log_b_high, 160))
        sse_values = np.empty(len(b_grid), dtype=float)
        a_values = np.empty(len(b_grid), dtype=float)
        for idx, b_value in enumerate(b_grid):
            basis = np.log1p(b_value * x_values)
            denom = float(np.dot(basis, basis))
            if denom <= 0.0:
                a_value = 0.0
            else:
                a_value = float(np.dot(basis, y_values) / denom)
            if a_value <= 0.0:
                a_value = 1e-12
            y_hat = a_value * basis
            residual = y_values - y_hat
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

    return best_a, best_b, best_sse


def slope_at_target_size(a_value: float, b_value: float, target_size: float) -> float:
    """Evaluate the fitted local rate at the requested target set size."""
    return float((a_value * b_value) / (1.0 + b_value * target_size))


def build_reference_rho_lookup(hybrid_runs: list[HybridRunSummary]) -> tuple[dict[tuple, float], dict[tuple, int]]:
    """Choose one reference `rho` per `(length, fivep, limit)` condition."""
    grouped = defaultdict(list)
    for run in hybrid_runs:
        grouped[(run.length, run.fivep_label, run.limit_label)].append(run)

    rho_lookup = {}
    init_source_lookup = {}
    for key, runs in grouped.items():
        runs_with_rho = [run for run in runs if run.pooled_rho is not None]
        if not runs_with_rho:
            continue
        preferred = [run for run in runs_with_rho if run.init_count == 900]
        chosen = preferred[0] if preferred else max(runs_with_rho, key=lambda run: run.init_count)
        rho_lookup[key] = float(chosen.pooled_rho)
        init_source_lookup[key] = int(chosen.init_count)
    return rho_lookup, init_source_lookup


def compute_naive_rate_lookup(
    naive_runs: list[NaiveRunSummary],
    hybrid_runs: list[HybridRunSummary],
) -> tuple[dict[tuple, float], dict[tuple, tuple[float, float]], dict[tuple, int]]:
    """Compute the naive proxy-fit rate for each hybrid run key."""
    naive_by_condition = {
        (run.length, run.fivep_label, run.limit_label): run
        for run in naive_runs
    }
    rho_lookup, init_source_lookup = build_reference_rho_lookup(hybrid_runs)

    rate_lookup = {}
    fit_param_lookup = {}
    for run in hybrid_runs:
        key = (run.length, run.fivep_label, run.limit_label)
        naive_run = naive_by_condition.get(key)
        rho = rho_lookup.get(key)
        if naive_run is None or rho is None or run.seed_size is None:
            continue
        proxy_x = rho * naive_run.raw_attempts
        a_value, b_value, _ = fit_log_model(proxy_x, naive_run.pairs_found)
        hybrid_key = (run.length, run.fivep_label, run.limit_label, run.init_count)
        rate_lookup[hybrid_key] = slope_at_target_size(a_value, b_value, float(run.seed_size))
        fit_param_lookup[hybrid_key] = (a_value, b_value)
    return rate_lookup, fit_param_lookup, init_source_lookup


def evaluate_log_model(a_value: float, b_value: float, x_values: np.ndarray) -> np.ndarray:
    """Evaluate the fitted two-parameter log model."""
    return a_value * np.log1p(b_value * x_values)


def x_at_target_size(a_value: float, b_value: float, target_size: float) -> float:
    """Invert the fitted model to obtain proxy x at a requested target size."""
    if a_value <= 0.0 or b_value <= 0.0:
        return float("nan")
    return float(math.expm1(target_size / a_value) / b_value)


def compute_y_max(hybrid_runs: list[HybridRunSummary], naive_rate_lookup: dict[tuple, float]) -> float:
    """Compute a shared y-axis limit across both plotted series."""
    values = []
    for run in hybrid_runs:
        if run.empirical_rate is not None:
            values.append(float(run.empirical_rate))
        key = (run.length, run.fivep_label, run.limit_label, run.init_count)
        naive_rate = naive_rate_lookup.get(key)
        if naive_rate is not None:
            values.append(float(naive_rate))
    if not values:
        return 1.0
    return max(1.0e-4, max(values) * 1.15)


def compute_y_min(hybrid_runs: list[HybridRunSummary], naive_rate_lookup: dict[tuple, float]) -> float:
    """Compute a positive lower y limit for log-scale plotting."""
    values = []
    for run in hybrid_runs:
        if run.empirical_rate is not None and run.empirical_rate > 0.0:
            values.append(float(run.empirical_rate))
        key = (run.length, run.fivep_label, run.limit_label, run.init_count)
        naive_rate = naive_rate_lookup.get(key)
        if naive_rate is not None and naive_rate > 0.0:
            values.append(float(naive_rate))
    if not values:
        return 1.0e-12
    min_positive = min(values)
    return 10.0 ** (math.floor(math.log10(min_positive)) - 0.5)


def apparent_conflict_probability_from_rate(rate: float, reference_size: int) -> float | None:
    """Convert a local acceptance rate at set size `m` into apparent conflict probability."""
    if reference_size <= 0:
        return None
    if rate <= 0.0:
        return 1.0
    if rate >= 1.0:
        return 0.0
    return float(1.0 - math.exp(math.log(rate) / reference_size))


def compute_conflict_y_limits(
    hybrid_runs: list[HybridRunSummary],
    naive_rate_lookup: dict[tuple, float],
) -> tuple[float, float]:
    """Compute linear-scale y limits for apparent-conflict-probability plotting."""
    values = []
    for run in hybrid_runs:
        if run.seed_size is None:
            continue
        if run.empirical_rate is not None:
            probability = apparent_conflict_probability_from_rate(run.empirical_rate, int(run.seed_size))
            if probability is not None:
                values.append(probability)
        key = (run.length, run.fivep_label, run.limit_label, run.init_count)
        naive_rate = naive_rate_lookup.get(key)
        if naive_rate is not None:
            probability = apparent_conflict_probability_from_rate(naive_rate, int(run.seed_size))
            if probability is not None:
                values.append(probability)
    if not values:
        return 0.0, 1.0
    y_max = min(1.0, max(values) * 1.15 + 0.01)
    return 0.0, max(0.05, y_max)


def plot_fivep_group(
    *,
    fivep_label: str,
    expected_slots: list[ExpectedHybridSlot],
    hybrid_runs: list[HybridRunSummary],
    init_counts: list[int],
    naive_rate_lookup: dict[tuple, float],
    init_source_lookup: dict[tuple, int],
    output_dir: Path,
) -> Path | None:
    """Plot one 5' extension condition and return the saved SVG path."""
    slots = [slot for slot in expected_slots if slot.fivep_label == fivep_label]
    if not slots:
        return None

    run_lookup = {
        (run.length, run.fivep_label, run.limit_label, run.init_count): run
        for run in hybrid_runs
        if run.fivep_label == fivep_label
    }

    subgroups = sorted(
        {
            (slot.length, slot.limit_label, slot.limit_value, slot.target_fraction_bound)
            for slot in slots
        },
        key=lambda item: (item[0], item[2], item[1]),
    )
    lengths = sorted({item[0] for item in subgroups})
    subgroups_by_length = defaultdict(list)
    for subgroup in subgroups:
        subgroups_by_length[subgroup[0]].append(subgroup)

    series_order = []
    for init_count in init_counts:
        series_order.append(("hybrid_empirical", init_count))
        series_order.append(("naive_proxy", init_count))

    relevant_runs = list(run_lookup.values())
    y_max = compute_y_max(relevant_runs, naive_rate_lookup)
    y_min = compute_y_min(relevant_runs, naive_rate_lookup)
    missing_value = min(y_max, y_min * 3.0)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)

    bar_width = 0.18
    init_gap = 0.08
    subgroup_gap = 0.28
    length_gap = 1.00

    xticks = []
    xticklabels = []
    length_annotations = []
    subgroup_annotations = []

    current_x = 0.0
    for length in lengths:
        length_start = current_x
        length_peak = 0.0
        group = subgroups_by_length[length]

        for subgroup_index, (_, limit_label, limit_value, target_fraction) in enumerate(group):
            subgroup_start = current_x
            for init_idx, init_count in enumerate(init_counts):
                pair_start = subgroup_start + init_idx * (2 * bar_width + init_gap)
                hybrid_key = (length, fivep_label, limit_label, init_count)
                run = run_lookup.get(hybrid_key)

                hybrid_value = None if run is None else run.empirical_rate
                naive_value = naive_rate_lookup.get(hybrid_key)

                for offset, (series_name, value) in enumerate(
                    [("hybrid_empirical", hybrid_value), ("naive_proxy", naive_value)]
                ):
                    x = pair_start + offset * bar_width
                    if value is None:
                        ax.bar(
                            x,
                            max(missing_value - y_min, y_min * 0.01),
                            width=bar_width,
                            bottom=y_min,
                            facecolor="white",
                            edgecolor="#9A9A9A",
                            linewidth=BAR_EDGE_LINEWIDTH,
                            hatch="///",
                            zorder=3,
                        )
                    else:
                        length_peak = max(length_peak, float(value))
                        ax.bar(
                            x,
                            max(float(value) - y_min, y_min * 0.01),
                            width=bar_width,
                            bottom=y_min,
                            facecolor=BAR_COLORS[series_name],
                            edgecolor="black",
                            linewidth=BAR_EDGE_LINEWIDTH,
                            zorder=3,
                        )

                pair_center = pair_start + 0.5 * bar_width
                xticks.append(pair_center)
                xticklabels.append(str(init_count))

            subgroup_width = len(init_counts) * (2 * bar_width + init_gap) - init_gap
            subgroup_center = subgroup_start + 0.5 * (subgroup_width - bar_width)
            subgroup_annotations.append((subgroup_center, limit_value, target_fraction))
            current_x += subgroup_width
            if subgroup_index != len(group) - 1:
                current_x += subgroup_gap

        length_end = current_x - bar_width
        length_center = 0.5 * (length_start + length_end)
        length_annotations.append((length_center, length, length_peak))
        current_x += length_gap

    title_suffix = f"5' extension: {fivep_label}" if fivep_label != "none" else "No 5' extension"
    ax.set_title(title_suffix, fontsize=TITLE_FONT_SIZE, pad=7)
    ax.set_xlabel("Initial independent set size", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Acceptance rate", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_yscale("log")
    ax.set_ylim(y_min, y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=0)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=1)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    ax.grid(axis="y", color="#B5B5B5", linewidth=GRID_LINEWIDTH, alpha=0.8, which="both")
    ax.set_axisbelow(True)

    handles = [
        Patch(facecolor=BAR_COLORS["hybrid_empirical"], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label="Hybrid empirical"),
        Patch(facecolor=BAR_COLORS["naive_proxy"], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label="Naive implied"),
        Patch(facecolor="white", edgecolor="#9A9A9A", linewidth=BAR_EDGE_LINEWIDTH, hatch="///", label="Missing"),
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        bbox_to_anchor=(0.995, 1.16),
        ncol=1,
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        handlelength=1.2,
        borderaxespad=0.2,
    )

    for x_pos, length, peak in length_annotations:
        if peak > 0:
            label_y = min(y_max / 1.30, peak * 1.8)
        else:
            label_y = y_max / 1.4
        ax.text(
            x_pos,
            label_y,
            f"Length = {length}",
            ha="center",
            va="top",
            fontsize=ANNOTATION_FONT_SIZE,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    for subgroup_center, limit_value, target_fraction in subgroup_annotations:
        ax.text(
            subgroup_center,
            y_min / (10 ** 0.18),
            f"{limit_value:.2f}\nfb={target_fraction:.2f}",
            ha="center",
            va="top",
            fontsize=TICK_LABEL_FONT_SIZE,
            clip_on=False,
        )

    reference_labels = []
    for length, limit_label, _, _ in subgroups:
        key = (length, fivep_label, limit_label)
        if key not in init_source_lookup:
            continue
        reference_labels.append(f"len{length}/{limit_label}: rho from init{init_source_lookup[key]}")
    if reference_labels:
        ax.text(
            0.995,
            0.02,
            "; ".join(reference_labels),
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=ANNOTATION_FONT_SIZE,
        )

    fig.subplots_adjust(left=0.11, right=0.99, bottom=0.38, top=0.82)
    output_path = output_dir / f"{OUTPUT_STEM}_5p_{fivep_label}.svg"
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_fit_diagnostics(
    *,
    fivep_label: str,
    naive_runs: list[NaiveRunSummary],
    hybrid_runs: list[HybridRunSummary],
    naive_rate_lookup: dict[tuple, float],
    fit_param_lookup: dict[tuple, tuple[float, float]],
    init_source_lookup: dict[tuple, int],
    output_dir: Path,
) -> list[Path]:
    """Write one naive proxy-fit diagnostic plot per `(length, limit)` condition."""
    hybrid_by_condition = defaultdict(list)
    for run in hybrid_runs:
        if run.fivep_label == fivep_label:
            hybrid_by_condition[(run.length, run.fivep_label, run.limit_label)].append(run)

    output_paths = []
    for naive_run in naive_runs:
        if naive_run.fivep_label != fivep_label:
            continue

        condition_key = (naive_run.length, naive_run.fivep_label, naive_run.limit_label)
        condition_hybrids = sorted(hybrid_by_condition.get(condition_key, []), key=lambda run: run.init_count)
        if not condition_hybrids:
            continue

        reference_init = init_source_lookup.get(condition_key)
        if reference_init is None:
            continue

        reference_hybrid = next(
            (run for run in condition_hybrids if run.init_count == reference_init),
            None,
        )
        if reference_hybrid is None or reference_hybrid.pooled_rho is None:
            continue

        reference_key = (
            reference_hybrid.length,
            reference_hybrid.fivep_label,
            reference_hybrid.limit_label,
            condition_hybrids[0].init_count,
        )
        fit_params = fit_param_lookup.get(reference_key)
        if fit_params is None:
            continue
        a_value, b_value = fit_params

        proxy_x = reference_hybrid.pooled_rho * naive_run.raw_attempts
        y_values = naive_run.pairs_found
        x_grid_max = max(
            float(np.max(proxy_x)),
            max(
                x_at_target_size(a_value, b_value, float(run.seed_size))
                for run in condition_hybrids
                if run.seed_size is not None
            ),
        ) * 1.05
        x_grid = np.linspace(0.0, x_grid_max, 800)
        y_grid = evaluate_log_model(a_value, b_value, x_grid)

        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        ax.scatter(
            proxy_x,
            y_values,
            s=18,
            color="#264653",
            alpha=0.85,
            label="Naive trajectory",
            zorder=3,
        )
        ax.plot(
            x_grid,
            y_grid,
            color="#E76F51",
            linewidth=1.8,
            label="Proxy fit",
            zorder=2,
        )

        diagnostic_points: list[FitDiagnosticPoint] = []
        for run in condition_hybrids:
            if run.seed_size is None:
                continue
            hybrid_key = (run.length, run.fivep_label, run.limit_label, run.init_count)
            naive_rate = naive_rate_lookup.get(hybrid_key)
            diagnostic_points.append(
                FitDiagnosticPoint(
                    init_count=run.init_count,
                    seed_size=int(run.seed_size),
                    empirical_rate=run.empirical_rate,
                    naive_rate=naive_rate,
                )
            )

        point_palette = ["#2A9D8F", "#577590", "#8E6C8A", "#6C757D"]
        for idx, point in enumerate(diagnostic_points):
            marker_color = point_palette[idx % len(point_palette)]
            x_target = x_at_target_size(a_value, b_value, float(point.seed_size))
            ax.axhline(point.seed_size, color=marker_color, linewidth=0.8, linestyle="--", alpha=0.65, zorder=1)
            ax.axvline(x_target, color=marker_color, linewidth=0.8, linestyle="--", alpha=0.65, zorder=1)
            ax.scatter([x_target], [point.seed_size], color=marker_color, s=28, zorder=4)
            label = f"init{point.init_count}: seed={point.seed_size}, naive={point.naive_rate:.2e}" if point.naive_rate is not None else f"init{point.init_count}: seed={point.seed_size}"
            ax.annotate(
                label,
                (x_target, point.seed_size),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
                color=marker_color,
            )

        title = (
            f"Naive proxy fit: len{naive_run.length}, 5p_{naive_run.fivep_label}, "
            f"limit {naive_run.offtarget_limit:.2f}"
        )
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Proxy passed_homodimer")
        ax.set_ylabel("Pairs found")
        ax.grid(True, color="#D0D0D0", linewidth=0.6, alpha=0.7)
        ax.legend(loc="upper left", frameon=False, fontsize=8)

        summary_lines = [
            f"rho source: init{reference_init}",
            f"rho = {reference_hybrid.pooled_rho:.6f}",
            f"a = {a_value:.4e}",
            f"b = {b_value:.4e}",
        ]
        ax.text(
            0.99,
            0.01,
            "\n".join(summary_lines),
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3},
        )

        fig.tight_layout()
        output_path = output_dir / (
            f"{OUTPUT_STEM}_fit_diag_len{naive_run.length}_5p_{naive_run.fivep_label}_limit{naive_run.limit_label}.png"
        )
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths


def plot_conflict_probability_group(
    *,
    fivep_label: str,
    expected_slots: list[ExpectedHybridSlot],
    hybrid_runs: list[HybridRunSummary],
    init_counts: list[int],
    naive_rate_lookup: dict[tuple, float],
    init_source_lookup: dict[tuple, int],
    output_dir: Path,
) -> Path | None:
    """Plot apparent conflict probabilities derived from the rate comparison bars."""
    slots = [slot for slot in expected_slots if slot.fivep_label == fivep_label]
    if not slots:
        return None

    run_lookup = {
        (run.length, run.fivep_label, run.limit_label, run.init_count): run
        for run in hybrid_runs
        if run.fivep_label == fivep_label
    }

    subgroups = sorted(
        {
            (slot.length, slot.limit_label, slot.limit_value, slot.target_fraction_bound)
            for slot in slots
        },
        key=lambda item: (item[0], item[2], item[1]),
    )
    lengths = sorted({item[0] for item in subgroups})
    subgroups_by_length = defaultdict(list)
    for subgroup in subgroups:
        subgroups_by_length[subgroup[0]].append(subgroup)

    relevant_runs = list(run_lookup.values())
    y_min, y_max = compute_conflict_y_limits(relevant_runs, naive_rate_lookup)
    missing_height = max(0.012, y_max * 0.05)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_INCHES)

    bar_width = 0.18
    init_gap = 0.08
    subgroup_gap = 0.28
    length_gap = 1.00

    xticks = []
    xticklabels = []
    length_annotations = []
    subgroup_annotations = []

    current_x = 0.0
    for length in lengths:
        length_start = current_x
        length_peak = 0.0
        group = subgroups_by_length[length]

        for subgroup_index, (_, limit_label, limit_value, target_fraction) in enumerate(group):
            subgroup_start = current_x
            for init_idx, init_count in enumerate(init_counts):
                pair_start = subgroup_start + init_idx * (2 * bar_width + init_gap)
                hybrid_key = (length, fivep_label, limit_label, init_count)
                run = run_lookup.get(hybrid_key)

                hybrid_value = None
                naive_value = None
                if run is not None and run.seed_size is not None:
                    if run.empirical_rate is not None:
                        hybrid_value = apparent_conflict_probability_from_rate(run.empirical_rate, int(run.seed_size))
                    naive_rate = naive_rate_lookup.get(hybrid_key)
                    if naive_rate is not None:
                        naive_value = apparent_conflict_probability_from_rate(naive_rate, int(run.seed_size))

                for offset, (series_name, value) in enumerate(
                    [("hybrid_empirical", hybrid_value), ("naive_proxy", naive_value)]
                ):
                    x = pair_start + offset * bar_width
                    if value is None:
                        ax.bar(
                            x,
                            missing_height,
                            width=bar_width,
                            facecolor="white",
                            edgecolor="#9A9A9A",
                            linewidth=BAR_EDGE_LINEWIDTH,
                            hatch="///",
                            zorder=3,
                        )
                    else:
                        length_peak = max(length_peak, float(value))
                        ax.bar(
                            x,
                            float(value),
                            width=bar_width,
                            facecolor=BAR_COLORS[series_name],
                            edgecolor="black",
                            linewidth=BAR_EDGE_LINEWIDTH,
                            zorder=3,
                        )

                pair_center = pair_start + 0.5 * bar_width
                xticks.append(pair_center)
                xticklabels.append(str(init_count))

            subgroup_width = len(init_counts) * (2 * bar_width + init_gap) - init_gap
            subgroup_center = subgroup_start + 0.5 * (subgroup_width - bar_width)
            subgroup_annotations.append((subgroup_center, limit_value, target_fraction))
            current_x += subgroup_width
            if subgroup_index != len(group) - 1:
                current_x += subgroup_gap

        length_end = current_x - bar_width
        length_center = 0.5 * (length_start + length_end)
        length_annotations.append((length_center, length, length_peak))
        current_x += length_gap

    title_suffix = f"5' extension: {fivep_label}" if fivep_label != "none" else "No 5' extension"
    ax.set_title(title_suffix, fontsize=TITLE_FONT_SIZE, pad=7)
    ax.set_xlabel("Initial independent set size", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_ylabel("Apparent conflict probability", fontsize=AXIS_LABEL_FONT_SIZE)
    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels, fontsize=TICK_LABEL_FONT_SIZE)
    ax.set_ylim(y_min, y_max)
    ax.tick_params(axis="y", labelsize=TICK_LABEL_FONT_SIZE, width=AXIS_LINEWIDTH, length=0)
    ax.tick_params(axis="x", width=AXIS_LINEWIDTH, length=0, pad=1)

    for spine in ax.spines.values():
        spine.set_linewidth(AXIS_LINEWIDTH)

    ax.grid(axis="y", color="#B5B5B5", linewidth=GRID_LINEWIDTH, alpha=0.8)
    ax.set_axisbelow(True)

    handles = [
        Patch(facecolor=BAR_COLORS["hybrid_empirical"], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label="Hybrid empirical"),
        Patch(facecolor=BAR_COLORS["naive_proxy"], edgecolor="black", linewidth=BAR_EDGE_LINEWIDTH, label="Naive implied"),
        Patch(facecolor="white", edgecolor="#9A9A9A", linewidth=BAR_EDGE_LINEWIDTH, hatch="///", label="Missing"),
    ]
    ax.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.16),
        ncol=3,
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        fontsize=LEGEND_FONT_SIZE,
        handlelength=1.2,
        borderaxespad=0.2,
    )

    for x_pos, length, peak in length_annotations:
        label_y = min(y_max * 0.96, peak + 0.06 if peak > 0 else y_max * 0.90)
        ax.text(
            x_pos,
            label_y,
            f"Length = {length}",
            ha="center",
            va="top",
            fontsize=ANNOTATION_FONT_SIZE,
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4},
        )

    for subgroup_center, limit_value, target_fraction in subgroup_annotations:
        ax.text(
            subgroup_center,
            y_min - 0.055 * (y_max - y_min),
            f"{limit_value:.2f}\nfb={target_fraction:.2f}",
            ha="center",
            va="top",
            fontsize=TICK_LABEL_FONT_SIZE,
            clip_on=False,
        )

    reference_labels = []
    for length, limit_label, _, _ in subgroups:
        key = (length, fivep_label, limit_label)
        if key not in init_source_lookup:
            continue
        reference_labels.append(f"len{length}/{limit_label}: rho from init{init_source_lookup[key]}")
    if reference_labels:
        ax.text(
            0.995,
            0.02,
            "; ".join(reference_labels),
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=ANNOTATION_FONT_SIZE,
        )

    fig.subplots_adjust(left=0.11, right=0.99, bottom=0.38, top=0.82)
    output_path = output_dir / f"{CONFLICT_OUTPUT_STEM}_5p_{fivep_label}.svg"
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_conflict_probability_diagnostics(
    *,
    fivep_label: str,
    hybrid_runs: list[HybridRunSummary],
    naive_rate_lookup: dict[tuple, float],
    output_dir: Path,
) -> list[Path]:
    """Plot apparent conflict probability versus seed-stage `pairs_after_vc` per condition."""
    grouped = defaultdict(list)
    for run in hybrid_runs:
        if run.fivep_label == fivep_label:
            grouped[(run.length, run.fivep_label, run.limit_label)].append(run)

    output_paths = []
    for key in sorted(grouped, key=lambda item: (item[0], item[1], parse_float_token(item[2]), item[2])):
        condition_runs = sorted(grouped[key], key=lambda run: run.init_count)
        if not condition_runs:
            continue

        first = condition_runs[0]
        fig, ax = plt.subplots(figsize=(5.8, 4.8))

        hybrid_x = []
        hybrid_y = []
        naive_x = []
        naive_y = []

        for run in condition_runs:
            if run.seed_size is None:
                continue
            hybrid_probability = None
            if run.empirical_rate is not None:
                hybrid_probability = apparent_conflict_probability_from_rate(run.empirical_rate, int(run.seed_size))
            naive_rate = naive_rate_lookup.get((run.length, run.fivep_label, run.limit_label, run.init_count))
            naive_probability = None
            if naive_rate is not None:
                naive_probability = apparent_conflict_probability_from_rate(naive_rate, int(run.seed_size))

            if hybrid_probability is not None:
                hybrid_x.append(int(run.seed_size))
                hybrid_y.append(float(hybrid_probability))
                ax.scatter(
                    int(run.seed_size),
                    float(hybrid_probability),
                    s=56,
                    color="#E76F51",
                    edgecolors="black",
                    linewidths=0.5,
                    marker="o",
                    zorder=3,
                )
                ax.annotate(
                    f"I{run.init_count}",
                    (int(run.seed_size), float(hybrid_probability)),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=8,
                    color="#E76F51",
                )

            if naive_probability is not None:
                naive_x.append(int(run.seed_size))
                naive_y.append(float(naive_probability))
                ax.scatter(
                    int(run.seed_size),
                    float(naive_probability),
                    s=56,
                    color="#2A9D8F",
                    edgecolors="black",
                    linewidths=0.5,
                    marker="s",
                    zorder=3,
                )
                ax.annotate(
                    f"I{run.init_count}",
                    (int(run.seed_size), float(naive_probability)),
                    xytext=(4, -12),
                    textcoords="offset points",
                    fontsize=8,
                    color="#2A9D8F",
                )

        title = f"len{first.length}, 5p_{first.fivep_label}, limit {first.offtarget_limit:.2f}"
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("pairs_after_vc (seed stage)")
        ax.set_ylabel("Apparent conflict probability")
        ax.grid(True, color="#D0D0D0", linewidth=0.6, alpha=0.8)
        ax.set_axisbelow(True)

        legend_handles = [
            Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="#E76F51", markeredgecolor="black", markeredgewidth=0.5, markersize=7, label="Hybrid empirical"),
            Line2D([0], [0], marker="s", linestyle="None", markerfacecolor="#2A9D8F", markeredgecolor="black", markeredgewidth=0.5, markersize=7, label="Naive implied"),
        ]
        ax.legend(handles=legend_handles, loc="upper right", frameon=True, facecolor="white", edgecolor="none", fontsize=8)

        output_path = output_dir / (
            f"{CONFLICT_OUTPUT_STEM}_diag_len{first.length}_5p_{first.fivep_label}_limit{first.limit_label}.png"
        )
        fig.tight_layout()
        fig.savefig(output_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
        output_paths.append(output_path)

    return output_paths


def summarize_missing_slots(expected_slots: list[ExpectedHybridSlot], hybrid_runs: list[HybridRunSummary]) -> list[ExpectedHybridSlot]:
    """Return expected hybrid slots that do not yet have a workbook."""
    observed = {
        (run.length, run.fivep_label, run.limit_label, run.init_count)
        for run in hybrid_runs
    }
    missing = [
        slot
        for slot in expected_slots
        if (slot.length, slot.fivep_label, slot.limit_label, slot.init_count) not in observed
    ]
    return sorted(missing, key=lambda slot: (slot.fivep_label, slot.length, slot.limit_value, slot.init_count))


def main() -> None:
    """Load the batch, compute rates, and write the comparison figure(s)."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DATA_ROOT,
        help="Directory containing the batch workbooks.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=SUMMARY_PATH,
        help="Generated batch_summary.toml describing the expected hybrid grid.",
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

    expected_slots, init_counts = load_expected_hybrid_slots(summary_path)
    hybrid_runs = [
        extract_hybrid_summary(path)
        for path in sorted(data_root.glob("len*/5p_*/*.xlsx"))
        if parse_workbook_filename(path) and parse_workbook_filename(path)["algorithm"] == "hybrid"
    ]
    naive_runs = [
        extract_naive_summary(path)
        for path in sorted(data_root.glob("len*/5p_*/*.xlsx"))
        if parse_workbook_filename(path) and parse_workbook_filename(path)["algorithm"] == "naive"
    ]

    naive_rate_lookup, fit_param_lookup, init_source_lookup = compute_naive_rate_lookup(naive_runs, hybrid_runs)
    missing_slots = summarize_missing_slots(expected_slots, hybrid_runs)

    print(f"data root: {data_root}")
    print(f"batch summary: {summary_path}")
    print(f"loaded hybrid workbooks: {len(hybrid_runs)}")
    print(f"loaded naive workbooks: {len(naive_runs)}")
    print(f"expected hybrid slots: {len(expected_slots)}")
    print(f"missing hybrid slots: {len(missing_slots)}")

    for key in sorted(init_source_lookup):
        length, fivep_label, limit_label = key
        print(f"rho_reference len{length} 5p_{fivep_label} limit{limit_label}: init{init_source_lookup[key]}")

    if missing_slots:
        print("missing hybrid slots:")
        for slot in missing_slots:
            print(f"  5p_{slot.fivep_label} len{slot.length} limit{slot.limit_label} init{slot.init_count}")

    fivep_labels = sorted({slot.fivep_label for slot in expected_slots})
    for fivep_label in fivep_labels:
        output_path = plot_fivep_group(
            fivep_label=fivep_label,
            expected_slots=expected_slots,
            hybrid_runs=hybrid_runs,
            init_counts=init_counts,
            naive_rate_lookup=naive_rate_lookup,
            init_source_lookup=init_source_lookup,
            output_dir=output_dir,
        )
        if output_path is not None:
            print(f"wrote plot: {output_path}")
        conflict_output_path = plot_conflict_probability_group(
            fivep_label=fivep_label,
            expected_slots=expected_slots,
            hybrid_runs=hybrid_runs,
            init_counts=init_counts,
            naive_rate_lookup=naive_rate_lookup,
            init_source_lookup=init_source_lookup,
            output_dir=output_dir,
        )
        if conflict_output_path is not None:
            print(f"wrote conflict plot: {conflict_output_path}")
        conflict_diagnostic_paths = plot_conflict_probability_diagnostics(
            fivep_label=fivep_label,
            hybrid_runs=hybrid_runs,
            naive_rate_lookup=naive_rate_lookup,
            output_dir=output_dir,
        )
        for conflict_diagnostic_path in conflict_diagnostic_paths:
            print(f"wrote conflict diagnostic: {conflict_diagnostic_path}")
        diagnostic_paths = plot_fit_diagnostics(
            fivep_label=fivep_label,
            naive_runs=naive_runs,
            hybrid_runs=hybrid_runs,
            naive_rate_lookup=naive_rate_lookup,
            fit_param_lookup=fit_param_lookup,
            init_source_lookup=init_source_lookup,
            output_dir=output_dir,
        )
        for diagnostic_path in diagnostic_paths:
            print(f"wrote diagnostic: {diagnostic_path}")


if __name__ == "__main__":
    main()
