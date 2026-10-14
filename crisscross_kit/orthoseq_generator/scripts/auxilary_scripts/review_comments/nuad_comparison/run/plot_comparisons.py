"""Regenerate all three comparison figures and their embedded tables from standard XLSX reports."""

from pathlib import Path
import sys


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[1]
    kit_folder = folder.parents[4]
    sys.path.insert(0, str(kit_folder))
    sys.path.insert(0, str(folder))
    from comparison_functions import plot_comparison
    from orthoseq_generator.search_report_reader import load_metadata

    cases = ["6mer", "12mer_wide", "12mer_narrow"]
    for case in cases:
        report = folder / "results" / case / "nuad.xlsx"
        reference = Path(load_metadata(report)["source.reference_report"])
        plot_comparison(report, reference, folder / "plots" / f"{case}_comparison.pdf")
