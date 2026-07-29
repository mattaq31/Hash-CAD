"""
load_sequences_from_xlsx_and_plot.py

Purpose:
    Load sequence pairs from a verified XLSX search report and recompute their
    on-target and off-target energy distributions with the current NUPACK
    settings.

Typical use case:
    - re-evaluate the final selected sequence pairs from a saved search report
    - plot energies from the canonical XLSX output format
"""

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata


if __name__ == "__main__":
    # 1) Load sequence pairs from a verified XLSX report.
    report_path = "results/ortho_10mers7_new_sheet.xlsx"
    found_pairs = load_found_pairs(report_path)
    metadata = load_metadata(report_path)
    sequence_pairs = list(zip(found_pairs["seq"], found_pairs["rc_seq"]))

    # 2) Configure the NUPACK model parameters recorded in the report.
    hf.set_nupack_params(
        material=metadata["nupack.material"],
        celsius=metadata["nupack.celsius"],
        sodium=metadata["nupack.sodium"],
        magnesium=metadata["nupack.magnesium"],
    )

    # 3) Compute on-target and self energies.
    on_e, self_e_seq, self_e_rc_seq = sc.compute_ontarget_energies(sequence_pairs)

    # 4) Compute off-target energies.
    off_e = sc.compute_offtarget_energies(sequence_pairs)

    # 5) Plot histograms and save them.
    stats = sc.plot_on_off_target_histograms(
        on_e,
        off_e,
        output_path="results/energy_hist_loaded_sequences_from_xlsx.pdf",
    )
    self_stats = sc.plot_self_energy_histogram(
        (self_e_seq, self_e_rc_seq),
        output_path="results/self_energy_hist_loaded_sequences_from_xlsx.pdf",
    )

    print(stats)
    print(self_stats)
