#!/usr/bin/env python3

from pathlib import Path
import sys

import pandas as pd


# This script is meant for results/all_pairs.xlsx in this folder.
# The workbook has a title row, then columns:
# Handle Pair ID | Plus Handles | Minus Handles
THIS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = THIS_DIR / "results"
INPUT_FILE = RESULTS_DIR / "all_pairs.xlsx"
OUTPUT_FILE = RESULTS_DIR / "all_pairs_sorted_by_ontarget_energy.xlsx"

# Add crisscross_kit to the import path when running this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from orthoseq_generator import energy_computations as ec  # noqa: E402
from orthoseq_generator import helper_functions as hf  # noqa: E402


def clean_sequence(seq):
    return str(seq).strip().upper()


if __name__ == "__main__":
    df = pd.read_excel(INPUT_FILE, sheet_name="Orthogonal Handle Pairs", header=1)
    df.columns = df.columns.str.strip()

    sequence_pairs = [
        (clean_sequence(row["Plus Handles"]), clean_sequence(row["Minus Handles"]))
        for _, row in df.iterrows()
    ]

    hf.set_nupack_params(material="dna", celsius=37, sodium=0.05, magnesium=0.015)
    hf.set_energy_type("total")

    association_energies, plus_self_energies, minus_self_energies = ec.compute_ontarget_energies(
        sequence_pairs
    )

    df.insert(
        df.columns.get_loc("Plus Handles") + 1,
        "Plus secondary structure energy (kcal/mol)",
        plus_self_energies,
    )
    df.insert(
        df.columns.get_loc("Minus Handles") + 1,
        "Minus secondary structure energy (kcal/mol)",
        minus_self_energies,
    )
    df["Total association energy (kcal/mol)"] = association_energies
    df = df.sort_values("Total association energy (kcal/mol)", ascending=True)

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Wrote sorted sequence pairs to {OUTPUT_FILE}")
