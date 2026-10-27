"""Prepare Polycube total/totalu and OrthoSeq totalu reports with the standard verification functions."""

from pathlib import Path

from orthoseq_generator.search_report_reader import load_found_pairs
from orthoseq_generator.search_reporting import build_selected_sequence_data
from comparison_functions import load_published_sequences, verify_and_write_report


if __name__ == "__main__":
    data_dir = Path(__file__).resolve().parent / "data"
    published_report = data_dir / "menger_published_sequences.xlsx"
    orthoseq_report = data_dir / "orthoseq_assembly_search_2026-10-08_19-51-55.xlsx"
    nupack_params = {"material": "dna", "celsius": 37.0, "sodium": 0.05, "magnesium": 0.0125}
    input_params = {"length": 9, "fivep_ext": "T" * 12, "threep_ext": ""}

    selected_menger, source_handles = load_published_sequences(published_report)
    for energy_type in ("total", "totalu"):
        verify_and_write_report(
            selected_menger, data_dir / f"menger_{energy_type}.xlsx",
            {**nupack_params, "energy_type": energy_type},
            {**input_params, "source_kind": "published_sequence_workbook"}, published_report, source_handles,
        )

    # Reuse OrthoSeq association energies from the search report; calculate only complex energies.
    pairs = load_found_pairs(orthoseq_report)
    selected_orthoseq = build_selected_sequence_data(
        list(zip(pairs["seq"], pairs["rc_seq"])), pairs["global_pair_id"].astype(int).tolist(),
    )
    verify_and_write_report(
        selected_orthoseq, data_dir / "orthoseq_totalu.xlsx", {**nupack_params, "energy_type": "totalu"},
        {**input_params, "source_kind": "search_report"}, orthoseq_report,
    )
