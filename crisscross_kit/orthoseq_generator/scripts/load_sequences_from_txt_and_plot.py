"""
load_sequences_from_txt_and_plot.py

Purpose:
    Load sequence pairs from a plain-text file and recompute their on-target
    and off-target energy distributions with the current NUPACK settings.

Typical use case:
    - evaluate sequence pairs that were produced outside the app
    - re-check an old `.txt` sequence list with the current thermodynamic model
"""

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


if __name__ == "__main__":
    # 1) Load sequence pairs from a text file.
    # By default, helper_functions looks in the standard results folder.
    sequence_pairs = hf.load_sequence_pairs_from_txt("the_new_64_seq.txt")

    # 2) Configure the NUPACK model parameters.
    hf.set_nupack_params(material="dna", celsius=37, sodium=0.05, magnesium=0.025)

    # 3) Compute on-target and self energies.
    on_e, self_e_seq, self_e_rc_seq = sc.compute_ontarget_energies(sequence_pairs)

    # 4) Compute off-target energies.
    off_e = sc.compute_offtarget_energies(sequence_pairs)

    # 5) Plot histograms and save them.
    stats = sc.plot_on_off_target_histograms(
        on_e,
        off_e,
        output_path="energy_hist_loaded_sequences_from_txt.pdf",
    )
    self_stats = sc.plot_self_energy_histogram(
        (self_e_seq, self_e_rc_seq),
        output_path="self_energy_hist_loaded_sequences_from_txt.pdf",
    )

    print(stats)
    print(self_stats)
