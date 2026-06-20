#!/usr/bin/env python3
"""
Extract the best sequence libraries from the short-seq benchmark data.

For each sequence length, flank condition, and conflict probability level,
this script picks the run (across seeds and algorithms) that found the most
orthogonal pairs, then writes a reduced xlsx containing only run_metadata and
found_pairs into a clean folder structure.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata


FILENAME_PATTERN = re.compile(
    r"density(?P<density>\dp\d+)_"
    r"(?P<algorithm>[a-z_]+)_"
    r"limit(?P<limit>[^_]+)"
    r"(?:_init(?P<init>\d+))?"
    r"(?:_prune[^_]+)?"
    r"(?:_vc\d+)?"
    r"_seed(?P<seed>\d+)\.xlsx$"
)


def parse_length_dir(name: str) -> tuple[int, str]:
    """Parse 'len7_tttt5p' or 'len7' into (length, flank_key)."""
    if "_tttt5p" in name:
        length = int(name.split("_")[0][3:])
        return length, "tttt5p"
    else:
        length = int(name[3:])
        return length, "none"


def find_best_per_density(results_dir: Path) -> dict[str, Path]:
    """For each density level, return the xlsx with the most found_pairs."""
    best: dict[str, tuple[int, Path]] = {}

    for xlsx in results_dir.glob("*.xlsx"):
        m = FILENAME_PATTERN.match(xlsx.name)
        if not m:
            continue

        density = m.group("density")
        try:
            df = load_found_pairs(xlsx)
        except Exception:
            continue

        count = len(df)
        if density not in best or count > best[density][0]:
            best[density] = (count, xlsx)

    return {density: path for density, (_, path) in best.items()}


def write_reduced_workbook(source_path: Path, dest_path: Path) -> int:
    """Write a slim xlsx with only run_metadata and found_pairs. Returns pair count."""
    metadata = load_metadata(source_path)
    found_pairs = load_found_pairs(source_path)

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_rows = [{"key": k, "value": v} for k, v in metadata.items()]

    with pd.ExcelWriter(dest_path, engine="openpyxl") as writer:
        pd.DataFrame(metadata_rows).to_excel(writer, sheet_name="run_metadata", index=False)
        found_pairs.to_excel(writer, sheet_name="found_pairs", index=False)

    return len(found_pairs)


if __name__ == "__main__":
    dataset_parent_name = "len4_7_tttt5p_noGGGG"
    benchmark_name = "benchmark_x"
    temp_label = "37C"

    flank_conditions = {
        "tttt5p": ("TTTT_flank", "TTTT"),
        "none": ("no_flank", "noflank"),
    }

    module_dir = Path(__file__).resolve().parents[1]
    data_dir = module_dir / "data"
    dataset_dir = data_dir / dataset_parent_name
    output_root = module_dir / "short_sequences"

    print(f"Reading from: {dataset_dir}")
    print(f"Writing to:   {output_root}\n")

    total_files = 0

    length_dirs = sorted(
        [d for d in dataset_dir.iterdir() if d.is_dir() and d.name.startswith("len")],
        key=lambda p: parse_length_dir(p.name),
    )

    for length_dir in length_dirs:
        length, flank_key = parse_length_dir(length_dir.name)
        flank_label, flank_tag = flank_conditions[flank_key]

        results_dir = length_dir / "results" / benchmark_name
        if not results_dir.is_dir():
            print(f"  SKIP {length_dir.name} (no results/{benchmark_name})")
            continue

        best_per_density = find_best_per_density(results_dir)
        if not best_per_density:
            print(f"  SKIP {length_dir.name} (no valid xlsx)")
            continue

        print(f"  len{length} / {flank_label}")

        for density in sorted(best_per_density.keys()):
            source = best_per_density[density]
            filename = f"len{length}_{temp_label}_{flank_tag}_confprob_{density}.xlsx"
            dest = output_root / temp_label / flank_label / filename
            count = write_reduced_workbook(source, dest)
            total_files += 1
            print(f"    confprob {density}: {count} pairs (from {source.name})")

    print(f"\nDone. Wrote {total_files} reduced workbooks into {output_root}")
