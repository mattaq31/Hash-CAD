import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc
from orthoseq_generator.vertex_cover_algorithms import evolutionary_vertex_cover

if __name__ == "__main__":
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 41
    random.seed(RANDOM_SEED)

    # Create candidate sequences
    ontarget7mer = sc.create_sequence_pairs_pool(length=7, fivep_ext="TT", threep_ext="", avoid_gggg=True)

    # Define energy thresholds
    offtarget_limit = -7.4
    max_ontarget = -9.6
    min_ontarget = -10.4

    # Set up precomputed energy library
    hf.choose_precompute_library("narrow_TT_7mers.pkl")
    hf.USE_LIBRARY = True

    # Run the heuristic vertex cover algorithm to select orthogonal sequences
    orthogonal_seq_pairs = evolutionary_vertex_cover(
        ontarget7mer,
        offtarget_limit,
        max_ontarget,
        min_ontarget,
        subsetsize=250,
        generations=2000
    )

    # Save and re-load selected sequences for inspection
    hf.save_sequence_pairs_to_txt(orthogonal_seq_pairs, filename='my_sequences.txt')
    #print(hf.load_sequence_pairs_from_txt('my_sequences.txt'))

    # Compute and plot final energy distributions
    hf.USE_LIBRARY = False  # force recomputation for plotting
    onef = sc.compute_ontarget_energies(orthogonal_seq_pairs)
    offef = sc.compute_offtarget_energies(orthogonal_seq_pairs)
    stats = sc.plot_on_off_target_histograms(
        onef,
        offef,
        output_path='result_energy_plot.pdf'
    )

