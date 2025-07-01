import random
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import vertex_cover_algorithms as vca
import pickle


if __name__ == "__main__":
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 41
    random.seed(RANDOM_SEED)

    with open('subset_data_7mers96to100.pkl', 'rb') as f:
        data = pickle.load(f)

    subset = data['subset']
    ids = data['ids']
    id_to_seq = dict(zip(ids, subset))
    
    
    off_energies = data['off_energies']
    
    offtarget_limit = -7.4
    
    edges = vca.build_edges(off_energies, ids, offtarget_limit)
    vertices = set(ids)
    #print(edges)

    vertex_cover = vca.iterative_vertex_cover_multi(vertices, edges, preserve_V=None, num_vertices_to_remove=200, max_iterations=200, limit=70,
                                 multistart=1, population_size=300, show_progress=True)
    
    independent = vertices- vertex_cover

    independent_sequences = [id_to_seq[i] for i in independent]
    print(independent_sequences)
    hf.save_sequence_pairs_to_txt(independent_sequences, 'independent_sequences.txt')
    