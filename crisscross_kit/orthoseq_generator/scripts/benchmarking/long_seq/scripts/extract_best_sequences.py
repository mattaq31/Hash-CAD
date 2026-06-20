#!/usr/bin/env python3
"""
Extract the best sequence libraries from the long-seq benchmark data.

For each of the 4 thermodynamic conditions (2 temperatures x 2 flank modes)
and each sequence length, this script picks the run that found the most
orthogonal pairs, then writes a reduced xlsx containing only run_metadata and
found_pairs into a clean folder structure.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata


def find_best_workbook(length_dir: Path) -> Path | None:
    """Return the xlsx with the most found_pairs rows inside a length folder."""
    subdirs = [d for d in length_dir.iterdir() if d.is_dir()]
    if not subdirs:
        return None

    best_count = -1
    best_path = None

    for subdir in subdirs:
        for xlsx in subdir.glob("*.xlsx"):
            try:
                df = load_found_pairs(xlsx)
            except Exception:
                continue
            if len(df) > best_count:
                best_count = len(df)
                best_path = xlsx

    return best_path


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
    batch_conditions = {
        "batch_x25TTTT_sigma1p0_seed41": ("25C", "TTTT_flank", "TTTT"),
        "batch_x25_____sigma1p0_seed41": ("25C", "no_flank", "noflank"),
        "batch_x_TTTT_sigma1p0_seed41": ("37C", "TTTT_flank", "TTTT"),
        "batch_x______sigma1p0_seed41": ("37C", "no_flank", "noflank"),
    }

    module_dir = Path(__file__).resolve().parents[1]
    data_dir = module_dir / "data"
    output_root = module_dir / "long_sequences"

    print(f"Reading from: {data_dir}")
    print(f"Writing to:   {output_root}\n")

    total_files = 0

    for batch_name, (temp_label, flank_label, flank_tag) in sorted(batch_conditions.items()):
        batch_dir = data_dir / batch_name
        if not batch_dir.is_dir():
            print(f"  SKIP {batch_name} (not found)")
            continue

        length_dirs = sorted(
            [d for d in batch_dir.iterdir() if d.is_dir() and d.name.startswith("len")],
            key=lambda p: int(p.name[3:]),
        )

        print(f"  {temp_label} / {flank_label} ({batch_name})")

        for length_dir in length_dirs:
            best = find_best_workbook(length_dir)
            if best is None:
                print(f"    {length_dir.name}: no xlsx found")
                continue

            filename = f"{length_dir.name}_{temp_label}_{flank_tag}.xlsx"
            dest = output_root / temp_label / flank_label / filename
            count = write_reduced_workbook(best, dest)
            total_files += 1
            print(f"    {length_dir.name}: {count} pairs (from {best.name})")

    print(f"\nDone. Wrote {total_files} reduced workbooks into {output_root}")
