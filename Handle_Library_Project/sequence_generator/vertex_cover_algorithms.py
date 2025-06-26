from sequence_generator import helper_functions as hf, sequence_computations as sc

import numpy as np
import random
from collections import defaultdict



def heuristic_vertex_cover_optimized2(E, preserve_V=None):
        if preserve_V is None:
            preserve_V = set()
        
        # Initialize the vertex cover set
        vertex_cover = set()

        # Remove self-edges

        for u, v in E:  # Create a copy of the set for iteration
            if u == v:
                vertex_cover.add(u)




        # build adjacent list

        adj_list = defaultdict(set)
        for u, v in E:
            if u!= v:
                # adj_list is an list of list. here vertex u has and adjescent vertex v and vice versa
                adj_list[u].add(v)
                adj_list[v].add(u)

        # Initialize degrees dictionary
        degrees = {v: len(neighbors) for v, neighbors in adj_list.items()}
        # keys are vertexes 
        # entries are number of neighbors
        
        
        # Loop until all edges are covered
        while degrees:
            # Find the maximum degree
            max_degree = max(degrees.values())

            # Get all vertices with the maximum degree
            max_degree_vertices = [v for v, deg in degrees.items() if deg == max_degree]

            # Calculate neighbor overlap for each max degree vertex

            min_overlap_count = +float('inf')
            min_overlap_vertices = []
            for v in max_degree_vertices:
                # Calculate the overlap: count of neighbors also in max_degree_vertices
                overlap_count = sum(1 for neighbor in adj_list[v] if neighbor in max_degree_vertices)

                # Select the vertex with the least neighbor overlap
                if overlap_count < min_overlap_count:
                    min_overlap_count = overlap_count
                    min_overlap_vertices = [v]  # Start a new list with this vertex
                elif overlap_count == min_overlap_count:
                    min_overlap_vertices.append(v)  # Add to the list if it's a tie

            # Prefer selecting a vertex that is NOT in preserve_V
            non_preserved = [v for v in min_overlap_vertices if v not in preserve_V]

            if non_preserved:
                selected_vertex = random.choice(non_preserved)
            else:
                selected_vertex = random.choice(min_overlap_vertices)

            vertex_cover.add(selected_vertex)

            # Remove the selected vertex from degrees and adjacency list
            neighbors = adj_list.pop(selected_vertex)
            degrees.pop(selected_vertex)

            # Remove all edges incident to the selected vertex
            for neighbor in neighbors:
                adj_list[neighbor].remove(selected_vertex)
                degrees[neighbor] -= 1
                if degrees[neighbor] == 0:
                    degrees.pop(neighbor)
                    adj_list.pop(neighbor)

        return vertex_cover


def find_uncovered_edges(E, vertex_cover):
    # Returns the set of edges not covered by the current vertex cover
    uncovered_edges = set()
    for u, v in E:
        if u not in vertex_cover and v not in vertex_cover:
            uncovered_edges.add((u, v))
        if u== v and u not in vertex_cover:
            uncovered_edges.add((u, v))
    return uncovered_edges


# Builds a list of index-pair edges from an off-target energy dictionary and a given index mapping.
# Only pairs with energies below the specified cutoff are included.
# Self-edges (i, i) are included.
#
# Parameters:
# - offtarget_dict: dictionary containing energy matrices with keys:
#     'handle_handle_energies', 'antihandle_handle_energies', 'antihandle_antihandle_energies'
# - indices: list of indices (e.g. into a full sequence list) used to map subset positions to global positions
# - energy_cutoff: float threshold below which an energy defines an edge
#
# Returns:
# - edges: list of (i, j) index pairs (edges) in global index space
def build_edges(offtarget_dict, indices, energy_cutoff):
    hh = offtarget_dict['handle_handle_energies']
    hah = offtarget_dict['antihandle_handle_energies']
    ahah = offtarget_dict['antihandle_antihandle_energies']

    # Find all index pairs where energy is below cutoff
    hh_infixes = np.argwhere(hh < energy_cutoff)
    hah_infixes = np.argwhere(hah < energy_cutoff)
    ahah_infixes = np.argwhere(ahah < energy_cutoff)

    # Combine
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))
    # Sort to make interaction  1,3 and 3,1 the same
    combined_infixes = np.sort(combined_infixes, axis=1)
    # remove double counts. incompatible is incompatible
    combined_infixes = np.unique(combined_infixes, axis=0)

    # Map back to original (global) indices
    edges = [(indices[i], indices[j]) for i, j in combined_infixes]

    return edges



def select_vertices_to_remove(vertex_cover, num_vertices_to_remove):
    # Selects vertices to remove from the vertex cover
    # Here we use random selection; you can change this to other criteria
    return set(random.sample(list(vertex_cover), min(num_vertices_to_remove, len(vertex_cover))))


def iterative_vertex_cover_multi(V, E, preserve_V=None, num_vertices_to_remove=150, max_iterations=200, limit=+np.inf, multistart=30, population_size=5, show_progress=False):
    # Initialize
    
    bestest_vertex_cover = None
   
    for i in range(multistart):
        
        if bestest_vertex_cover is None:
            current_bestest_size = 'None'
        else:
            current_bestest_size = len(V) - len(bestest_vertex_cover)
        

        best_vertex_cover = heuristic_vertex_cover_optimized2(E, preserve_V=preserve_V)
        current_vertex_cover = best_vertex_cover.copy()
        population = [current_vertex_cover]  # Start with the best vertex cover as the initial population
        iteration = 0
        #print("started new try")
        while iteration < max_iterations:
            iteration += 1
            # print(f"Iteration {iteration}, current best size: {len(best_vertex_cover) - len(V)}")
            if -len(best_vertex_cover) + len(V) >= limit:
                print('found desired set')
                break

            # print('population is of lenght')
            # print(len(population))
            
            new_guys = []
            for current_cover in population:
               
                current_cover2 = current_cover.copy()  # Create a copy to avoid modifying the original in the population

                # Step a: Remove vertices from the current cover
                vertices_to_remove = select_vertices_to_remove(current_cover2, num_vertices_to_remove)
                current_cover2 -= vertices_to_remove

                # Step b: Update the graph (find uncovered edges)
                uncovered_edges = find_uncovered_edges(E, current_cover2)
                # Build a subgraph with only uncovered edges
                # remaining_vertices = set(u for u, v in uncovered_edges) | set(v for u, v in uncovered_edges)

                # Re-run the heuristic on the subgraph
                additional_cover = heuristic_vertex_cover_optimized2(uncovered_edges, preserve_V=None)
                current_cover2 |= additional_cover  # Update the current vertex cover

                # Step d: Compare and update best solution

                # print(len(current_cover2))
                
                
                if len(current_cover2) < len(best_vertex_cover):
                    best_vertex_cover = current_cover2.copy()  # Copy to ensure best_vertex_cover remains separate
                    #
                    population = [best_vertex_cover]  # Reset population with the new best cover
                    new_guys = []
                    break
                elif len(current_cover2) == len(best_vertex_cover):
                    if all(current_cover2 != cover for cover in population):
                        new_guys.append(current_cover2.copy())  # Add a unique copy of the equal-sized cover

            population = new_guys + population
            if len(population) > population_size:
                population = random.sample(population, population_size)
                
            if show_progress:                                                    
                print(f"Iteration {iteration+1}: Found {len(population)} sets of size {-len(best_vertex_cover) + len(V)}") 

        print(f"Iteration {i + 1} of {multistart}| current bestest independent set size: {current_bestest_size}")
        if bestest_vertex_cover is None or len(best_vertex_cover) < len(bestest_vertex_cover):
            bestest_vertex_cover = best_vertex_cover.copy()
            print("update bestest")

    return bestest_vertex_cover








def evolutionary_vertex_cover(sequence_pairs, offtarget_limit, max_ontarget, min_ontarget, subsetsize=200, generations=100):
    non_cover_vertices = set()
    history = set()

    try:
        for i in range(generations):
            # Select sequences with on-target energy in desired range
            subset, indices = sc.select_subset_in_energy_range(
                sequence_pairs,
                energy_min=min_ontarget,
                energy_max=max_ontarget,
                max_size=subsetsize,
                Use_Library=True,
                avoid_indices=history
            )
            sorted_history = sorted(history)
            extra_pairs = [sequence_pairs[idx][1] for idx in sorted_history]
            subset += extra_pairs
            indices += list(sorted_history)

            assert len(indices) == len(set(indices)), (
                f"Duplicate index found! "
                f"indices={indices} "
                f"set(indices)={sorted(set(indices))}"
            )

            # Compute off-target energies for the subset
            off_e_subset = sc.compute_offtarget_energies(subset)

            # Build the off-target interaction graph
            Edges = build_edges(off_e_subset, indices, offtarget_limit)

            # Run the heuristic vertex cover algorithm
            #removed_vertices = heuristic_vertex_cover_optimized2(Edges, history)
            removed_vertices = iterative_vertex_cover_multi(indices,Edges, preserve_V=history,num_vertices_to_remove=len(indices)//2)

            # Identify sequences not selected by the heuristic
            Vertices = set(indices)
            new_non_cover_vertices = Vertices - removed_vertices
            

            if len(new_non_cover_vertices) >= len(non_cover_vertices):
                if len(new_non_cover_vertices) > len(non_cover_vertices):
                    history.clear()
                non_cover_vertices = new_non_cover_vertices
                
            if len(new_non_cover_vertices) >= len(non_cover_vertices)*0.95:
                history.update(new_non_cover_vertices)
                

            print(f"Generation {i + 1:2d} | Current: {len(new_non_cover_vertices):3d} sequences | Best so far: {len(non_cover_vertices):3d} | Preserved pool length: {len(history):3d}")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving best result so far...")

    # Save result
    final_pairs = [sequence_pairs[idx][1] for idx in sorted(non_cover_vertices)]
    hf.save_sequence_pairs_to_txt(final_pairs)

    return final_pairs


if __name__ == "__main__":
    # Run test to see if the functions above work
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # Create candidate sequences
    ontarget7mer = sc.create_sequence_pairs_pool(length=7, fivep_ext="TT", threep_ext="", avoid_gggg=False)
    #print(ontarget7mer)

    # Define energy thresholds
    offtarget_limit = -7.4
    max_ontarget = -9.6
    min_ontarget = -10.4
    '''
    # Select sequences with on-target energy in desired range
    subset, indices = select_subset_in_energy_range(
        ontarget7mer, energy_min=min_ontarget, energy_max=max_ontarget,
        max_size=30, Use_Library=True, avoid_indices=set()
    )
    
    # Compute off-target energies for the subset
    off_e_subset = compute_offtarget_energies(subset, Use_Library=False)

    # Build the off-target interaction graph
    Edges = build_edges(off_e_subset, indices, offtarget_limit)
    '''
    hf.choose_precompute_library("my_new_cache.pkl")  # filename setter you already have
    hf.USE_LIBRARY = True
    # Run the heuristic vertex cover algorithm
    orthogonal_seq_pairs = evolutionary_vertex_cover(ontarget7mer, offtarget_limit, max_ontarget, min_ontarget, subsetsize=50, generations= 3)
    hf.save_sequence_pairs_to_txt(orthogonal_seq_pairs, filename='my_sequences.txt')
    
    print(hf.load_sequence_pairs_from_txt('my_sequences.txt'))
    
    hf.USE_LIBRARY = False
    onef = sc.compute_ontarget_energies(orthogonal_seq_pairs)
    offef = sc.compute_offtarget_energies(orthogonal_seq_pairs)
    stats2 = sc.plot_on_off_target_histograms(onef, offef, output_path='../dump/test.pdf')
    print(stats2)



 
