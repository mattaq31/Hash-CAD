#!/usr/bin/env python3

from __future__ import annotations

import argparse
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "test_init_pairs_sigma1p0_seed41"
OUTPUT_STEM = "long_seq_hybrid_budget_simple"

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

INIT_COLORS = {225: "#2A9D8F", 450: "#577590", 900: "#8E6C8A"}


def parse_number(text: str | None) -> float | None:
    if text is None:
        return None
    text = text.strip()
    if text in {"", "N.A."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_limit_token(token: str) -> float:
    return float(token.replace("m", "-").replace("p", "."))


def parse_name(path: Path) -> dict[str, object] | None:
    match = re.match(
        (
            r"(?P<algorithm>naive|hybrid)_len(?P<length>\d+)"
            r"_5p_(?P<fivep_label>[^_]+)"
            r"_limit(?P<limit_label>[a-z0-9]+)"
            r"(?:_budget(?P<budget>\d+))?"
            r"(?:_init(?P<init_count>\d+))?"
            r"_seed(?P<seed>\d+)\.xlsx$"
        ),
        path.name,
    )
    if match is None:
        return None
    init_count = match.group("init_count")
    return {
        "algorithm": match.group("algorithm"),
        "length": int(match.group("length")),
        "fivep_label": match.group("fivep_label") or "none",
        "limit_label": match.group("limit_label"),
        "init_count": None if init_count is None else int(init_count),
    }


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [
        "".join(node.text or "" for node in item.findall(".//main:t", NS))
        for item in root.findall("main:si", NS)
    ]


def get_sheet_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels.findall("pkgrel:Relationship", NS)
    }
    for sheet in workbook.findall("main:sheets/main:sheet", NS):
        if sheet.attrib.get("name") != sheet_name:
            continue
        rel_id = sheet.attrib.get(f"{{{NS['rel']}}}id")
        if rel_id:
            return f"xl/{rel_targets[rel_id]}"
    raise KeyError(sheet_name)


def read_cell(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", NS))
    value = cell.find("main:v", NS)
    if value is None:
        return ""
    raw = value.text or ""
    if cell_type == "s":
        return shared_strings[int(raw)]
    return raw


def read_rows(xlsx_path: Path, sheet_name: str) -> list[dict[str, str]]:
    with zipfile.ZipFile(xlsx_path) as archive:
        shared_strings = read_shared_strings(archive)
        sheet_path = get_sheet_path(archive, sheet_name)
        root = ET.fromstring(archive.read(sheet_path))

    raw_rows: list[dict[str, str]] = []
    for row in root.findall("main:sheetData/main:row", NS):
        values: dict[str, str] = {}
        for cell in row.findall("main:c", NS):
            ref = cell.attrib.get("r", "")
            match = re.match(r"([A-Z]+)", ref)
            if match:
                values[match.group(1)] = read_cell(cell, shared_strings)
        raw_rows.append(values)
    if not raw_rows:
        return []

    headers = {column: value for column, value in raw_rows[0].items() if value}
    table: list[dict[str, str]] = []
    for row in raw_rows[1:]:
        record = {header: row.get(column, "") for column, header in headers.items()}
        if any(value != "" for value in record.values()):
            table.append(record)
    return table


def read_metadata(xlsx_path: Path) -> dict[str, str]:
    rows = read_rows(xlsx_path, "run_metadata")
    metadata: dict[str, str] = {}
    for row in rows:
        key = row.get("key", "").strip() or row.get("A", "").strip()
        value = row.get("value", "").strip() or row.get("B", "").strip()
        if key:
            metadata[key] = value
    return metadata


def fit_yield(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    xs = [math.log(collected) for collected, _ in points if collected > 1.0]
    ys = [retained for collected, retained in points if collected > 1.0]
    if len(xs) < 2:
        return None
    design = np.column_stack([np.asarray(xs), np.ones(len(xs))])
    coeffs, _, rank, _ = np.linalg.lstsq(design, np.asarray(ys), rcond=None)
    if rank < 2:
        return None
    return float(coeffs[0]), float(coeffs[1])


def fit_naive_log1p(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    if len(points) < 3:
        return None
    x_values = np.asarray([point[0] for point in points], dtype=float)
    y_values = np.asarray([point[1] for point in points], dtype=float)
    if np.any(x_values <= 0.0) or np.any(y_values < 0.0):
        return None

    x_max = float(np.max(x_values))
    u_values = np.log(x_values)
    log_b_low = math.log(max(x_max * 1e-6, 1e-12))
    log_b_high = math.log(max(x_max * 1e2, 1e-6))

    best_a = float("nan")
    best_b = float("nan")
    best_sse = float("inf")

    for _ in range(8):
        b_grid = np.exp(np.linspace(log_b_low, log_b_high, 160))
        for b_value in b_grid:
            basis = np.log1p(np.exp(u_values) / b_value)
            denominator = float(np.dot(basis, basis))
            if denominator <= 0.0:
                continue
            a_value = float(np.dot(basis, y_values) / denominator)
            if a_value <= 0.0:
                continue
            residual = y_values - a_value * basis
            sse = float(np.dot(residual, residual))
            if sse < best_sse:
                best_sse = sse
                best_a = a_value
                best_b = float(b_value)

        if not math.isfinite(best_b):
            return None
        log_step = (log_b_high - log_b_low) / 159.0
        best_log_b = math.log(best_b)
        log_b_low = best_log_b - 3.0 * log_step
        log_b_high = best_log_b + 3.0 * log_step

    if not math.isfinite(best_a) or not math.isfinite(best_b):
        return None
    return best_a, best_b


def yield_value(fit: tuple[float, float], collected: float) -> float:
    if collected <= 0.0:
        return 0.0
    if collected <= 1.0:
        return collected
    a_value, b_value = fit
    predicted = a_value * math.log(collected) + b_value
    return max(0.0, min(collected, predicted))


def naive_value(fit: tuple[float, float], budget: np.ndarray) -> np.ndarray:
    a_value, b_value = fit
    return a_value * np.log1p(budget / b_value)


def solve_stage2(budget_remaining: float, rate: float) -> tuple[float, float]:
    if budget_remaining <= 0.0:
        return 0.0, 0.0
    if rate <= 0.0:
        return budget_remaining, 0.0
    alpha = 2.0 * rate * rate
    discriminant = 1.0 + 4.0 * alpha * budget_remaining
    nupack1 = (-1.0 + math.sqrt(discriminant)) / (2.0 * alpha)
    collected = rate * nupack1
    return nupack1, collected


def collect_condition_data(
    data_root: Path,
) -> tuple[
    dict[tuple[int, str, str], list[tuple[float, float]]],
    dict[tuple[int, str, str], list[dict[str, float | int | str]]],
    dict[tuple[int, str, str], list[tuple[float, float]]],
]:
    yield_points: dict[tuple[int, str, str], list[tuple[float, float]]] = defaultdict(list)
    runs: dict[tuple[int, str, str], list[dict[str, float | int | str]]] = defaultdict(list)
    naive_points: dict[tuple[int, str, str], list[tuple[float, float]]] = defaultdict(list)

    for xlsx_path in sorted(data_root.glob("len*/5p_*/*.xlsx")):
        parsed = parse_name(xlsx_path)
        if parsed is None:
            continue

        key = (
            int(parsed["length"]),
            str(parsed["fivep_label"]),
            str(parsed["limit_label"]),
        )

        if parsed["algorithm"] == "naive":
            progress = read_rows(xlsx_path, "search_progress")
            for row in progress:
                nupack_calls = parse_number(row.get("nupack_calls_executed"))
                pairs_found = None

                # Support the legacy naive progress schema.
                if row.get("step") == "accepted_pair":
                    pairs_found = parse_number(row.get("pairs_found"))

                # Support the current naive progress schema written by
                # naive_search_algorithm.py.
                elif row.get("pass") == "naive":
                    pairs_found = parse_number(row.get("pairs_collected"))
                    if pairs_found is None:
                        pairs_found = parse_number(row.get("total_retained"))

                if nupack_calls is None or pairs_found is None:
                    continue
                naive_points[key].append((float(nupack_calls), float(pairs_found)))
            continue

        if parsed["algorithm"] != "hybrid":
            continue

        progress = read_rows(xlsx_path, "search_progress")
        metadata = read_metadata(xlsx_path)
        seed_row = next((row for row in progress if row.get("pass") == "seed"), None)
        collection_row = next((row for row in progress if row.get("pass") == "collection"), None)
        if seed_row is None or collection_row is None:
            continue

        for row in (seed_row, collection_row):
            pairs_collected = parse_number(row.get("pairs_collected"))
            pairs_after_vc = parse_number(row.get("pairs_after_vc"))
            if pairs_collected is not None and pairs_after_vc is not None:
                yield_points[key].append((pairs_collected, pairs_after_vc))

        total_budget = parse_number(metadata.get("search.total_nupack_budget"))
        seed_calls = parse_number(seed_row.get("nupack_calls_executed"))
        seed_retained = parse_number(seed_row.get("pairs_after_vc"))
        collection_calls = parse_number(collection_row.get("nupack_calls_executed"))
        collection_pairs = parse_number(collection_row.get("pairs_collected"))
        final_total = parse_number(collection_row.get("total_retained"))
        if None in {total_budget, seed_calls, seed_retained, collection_calls, collection_pairs, final_total}:
            continue

        crossref_calls = collection_calls - 2.0 * collection_pairs * collection_pairs
        if crossref_calls <= 0.0:
            continue

        runs[key].append(
            {
                "init_count": int(parsed["init_count"]),
                "total_budget": float(total_budget),
                "seed_calls": float(seed_calls),
                "seed_retained": float(seed_retained),
                "collection_pairs": float(collection_pairs),
                "final_total": float(final_total),
                "stage2_rate": float(collection_pairs) / crossref_calls,
            }
        )

    return yield_points, runs, naive_points


def plot_condition(
    key: tuple[int, str, str],
    fit: tuple[float, float],
    runs: list[dict[str, float | int | str]],
    naive_fit: tuple[float, float] | None,
    naive_points: list[tuple[float, float]],
    output_dir: Path,
    budget_max: float,
    budget_steps: int,
) -> Path:
    length, fivep_label, limit_label = key
    limit_value = parse_limit_token(limit_label)

    budget_grid = np.linspace(0.0, budget_max, budget_steps)
    fig, ax = plt.subplots(figsize=(6.6, 5.0))

    if naive_fit is not None:
        ax.plot(
            budget_grid,
            naive_value(naive_fit, budget_grid),
            color="black",
            linewidth=1.7,
            linestyle="--",
            label="naive",
            zorder=1,
        )
        if naive_points:
            naive_endpoint = max(naive_points, key=lambda item: item[0])
            ax.scatter(
                [naive_endpoint[0]],
                [naive_endpoint[1]],
                color="black",
                marker="D",
                s=42,
                zorder=3,
            )

    for run in sorted(runs, key=lambda item: int(item["init_count"])):
        init_count = int(run["init_count"])
        color = INIT_COLORS.get(init_count, "#6C757D")
        seed_calls = float(run["seed_calls"])
        seed_retained = float(run["seed_retained"])
        stage2_rate = float(run["stage2_rate"])
        total_budget = float(run["total_budget"])

        predicted = np.full_like(budget_grid, np.nan, dtype=float)
        for idx, budget in enumerate(budget_grid):
            if budget < seed_calls:
                continue
            _, collected = solve_stage2(budget - seed_calls, stage2_rate)
            predicted[idx] = seed_retained + yield_value(fit, collected)

        _, observed_collected = solve_stage2(total_budget - seed_calls, stage2_rate)
        observed_pred = seed_retained + yield_value(fit, observed_collected)

        ax.plot(budget_grid, predicted, color=color, linewidth=1.8, label=f"init{init_count}")
        ax.scatter([total_budget], [float(run["final_total"])], color=color, edgecolors="black", linewidths=0.5, s=45, zorder=3)
        ax.scatter([total_budget], [observed_pred], color=color, marker="x", s=55, linewidths=1.2, zorder=3)

        print(
            f"len{length} limit{limit_label} init{init_count}: "
            f"observed={float(run['final_total']):.1f} predicted={observed_pred:.1f} "
            f"seed_calls={seed_calls:.0f} stage2_rate={stage2_rate:.6e}"
        )

    ax.set_title(f"len{length}, 5p_{fivep_label}, limit {limit_value:.2f}", fontsize=10)
    ax.set_xlabel("Total NUPACK budget")
    ax.set_ylabel("Predicted final retained set size")
    ax.grid(True, color="#D0D0D0", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", fontsize=8)
    ax.text(
        0.99,
        0.01,
        (
            f"yield: y = {fit[0]:.3f} ln(n) + {fit[1]:.3f}\n"
            + (
                f"naive: y = {naive_fit[0]:.3f} ln(1 + x / {naive_fit[1]:.1f})"
                if naive_fit is not None
                else "naive: unavailable"
            )
        ),
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.3},
    )
    fig.tight_layout()

    output_path = output_dir / f"{OUTPUT_STEM}_len{length}_5p_{fivep_label}_limit{limit_label}.png"
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--budget-max", type=float, default=10_000_000.0)
    parser.add_argument("--budget-steps", type=int, default=300)
    args = parser.parse_args()

    data_root = args.data_root.resolve()
    output_dir = data_root if args.output_dir is None else args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    yield_points_by_key, runs_by_key, naive_points_by_key = collect_condition_data(data_root)
    print(f"data root: {data_root}")

    for key in sorted(runs_by_key, key=lambda item: (item[0], item[1], parse_limit_token(item[2]), item[2])):
        fit = fit_yield(yield_points_by_key.get(key, []))
        if fit is None:
            continue
        naive_fit = fit_naive_log1p(naive_points_by_key.get(key, []))
        output_path = plot_condition(
            key,
            fit,
            runs_by_key[key],
            naive_fit,
            naive_points_by_key.get(key, []),
            output_dir,
            budget_max=args.budget_max,
            budget_steps=args.budget_steps,
        )
        print(f"wrote {output_path}")


if __name__ == "__main__":
    main()
