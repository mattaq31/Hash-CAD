"""Regenerate comparison figures and their embedded tables from completed standard XLSX reports."""

from pathlib import Path
import sys


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[1]
    kit_folder = folder.parents[4]
    sys.path.insert(0, str(kit_folder))
    sys.path.insert(0, str(folder))
    from comparison_functions import plot_comparison
    from orthoseq_generator.search_report_reader import load_metadata

    cases = {"6mer": "6mer", "12mer_wide": "12mer_wide", "12mer_narrow": "12mer_narrow",
             "20mer_Na1M_Mg0M": "20mer_Na1M_Mg0M_20261025_115004"}
    for case, result_folder in cases.items():
        report = folder / "results" / result_folder / "nuad.xlsx"
        # A pending search has no final workbook; native checkpoints are not verified plot inputs.
        if case == "20mer_Na1M_Mg0M" and not report.is_file():
            print(f"Skipping {case}: final report not yet available ({report}).")
            continue
        reference = Path(load_metadata(report)["source.reference_report"])
        plot_comparison(report, reference, folder / "plots" / f"{case}_comparison.pdf")
