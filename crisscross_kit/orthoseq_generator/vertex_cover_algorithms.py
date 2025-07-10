from orthoseq_generator import sequence_computations as sc
from orthoseq_generator import helper_functions as hf

import numpy as np
import random
from collections import defaultdict



def heuristic_vertex_cover_optimized2(E, preserve_V=None):
        '''
        This function is the core of the sequence search algorithm. It's a heuristic approach to solve the np hard minimum vertex cover problem.
        Inspired by:
             - Joshi (2020), "Neighbourhood Evaluation Criteria for Vertex Cover Problem"
            - StackExchange: https://cs.stackexchange.com/q/74546
            
        Heuristic algorithm to compute a vertex cover in an undirected graph, optimized by
        selecting highest‐degree vertices with minimal overlap among themselves.
    
        Input:
            - E (iterable of tuple): Set of edges (u, v). Vertices can be any hashable.
            - preserve_V (set, optional): Vertices you’d like to preferentially keep out of the cover. They can still be removed just less likely
    
        Output:
            - set: A vertex cover (i.e. set of vertices touching every edge in E).
    
        Notes:
            - Self‐edges (u == v) are immediately added to the cover.
            - We build an adjacency list (ignoring self‐edges), track degrees, then:
                1. Find the max degree.
                2. Among those vertices, choose one with the fewest neighbors that also have max degree.
                3. Break ties randomly, but prefer vertices *not* in preserve_V.
            - Remove the chosen vertex and all incident edges, updating degrees,
              until no edges remain.
        '''
       
       
       
       
       
        if preserve_V is None:
            preserve_V = set()
        
        
        vertex_cover = set()

        # 1) Immediately cover all self‐edges
        for u, v in E:  
            if u == v:
                vertex_cover.add(u)

        # 2) Build adjacency list for all non‐self edges
        adj_list = defaultdict(set)
        for u, v in E:
            if u!= v:
                # adj_list is a list of list. here vertex u has v as an adjacent vertex and vice versa
                adj_list[u].add(v)
                adj_list[v].add(u)

        # 3) Initialize degree counts
        # keys are vertexes 
        # entries are number of neighbors
        degrees = {v: len(neighbors) for v, neighbors in adj_list.items()}

        
        
        # 4) Greedily pick vertices until all edges are covered
        while degrees:
            # a) Find vertices of maximum degree
            max_degree = max(degrees.values())
            max_degree_vertices = [v for v, deg in degrees.items() if deg == max_degree]

           

            # b) Among those, pick those with minimal “overlap” between them. 
            min_overlap_count = +float('inf')
            min_overlap_vertices = []
            for v in max_degree_vertices:
                # Calculate the overlap: count of neighbors that are also part of in max_degree_vertices
                overlap_count = sum(1 for neighbor in adj_list[v] if neighbor in max_degree_vertices)

                # Select the vertex with the least neighbor overlap
                if overlap_count < min_overlap_count:
                    min_overlap_count = overlap_count
                    min_overlap_vertices = [v]  # Start a new list with this vertex
                elif overlap_count == min_overlap_count:
                    min_overlap_vertices.append(v)  # Add to the list if it's a tie

            # c) Last resort tie breaking. Pick at random but prefer ones not in preserve_V if possible 
            non_preserved = [v for v in min_overlap_vertices if v not in preserve_V]

            if non_preserved:
                selected_vertex = random.choice(non_preserved)
            else:
                selected_vertex = random.choice(min_overlap_vertices)

            vertex_cover.add(selected_vertex)

            # d) Remove selected vertex and its edges
            neighbors = adj_list.pop(selected_vertex)
            degrees.pop(selected_vertex)

            # Remove all edges incident to the selected vertex
            for neighbor in neighbors:
                adj_list[neighbor].remove(selected_vertex)
                degrees[neighbor] -= 1
                if degrees[neighbor] == 0:
                    # prune isolated vertices
                    degrees.pop(neighbor)
                    adj_list.pop(neighbor)

        return vertex_cover


def find_uncovered_edges(E, vertex_cover):
    '''
    Finds edges that are not covered by the current vertex cover. 
    Technically speaking the input variable is no longer a vertex cover.

    Input:
        - E (iterable of tuple): Collection of edges (u, v).
        - vertex_cover (set): Set of vertices currently in the cover.

    Output:
        - set: Edges (u, v) from E for which neither u nor v is in vertex_cover.
               Self‐edges (u == v) are included if u is not in the cover.
    '''
    uncovered_edges = set()
    for u, v in E:
        if u not in vertex_cover and v not in vertex_cover:
            uncovered_edges.add((u, v))
        if u== v and u not in vertex_cover:
            uncovered_edges.add((u, v))
    return uncovered_edges


def build_edges(offtarget_dict, indices, energy_cutoff):
    '''
    Builds a list of global index‐pair edges from off‐target energy matrices. (indices with respect to the initially created sequences list)

    Input:
        - offtarget_dict (dict): Contains three N×N numpy arrays under keys:
            • 'handle_handle_energies'
            • 'antihandle_handle_energies'
            • 'antihandle_antihandle_energies'
        - indices (list of int): Maps row/column positions in the matrices back to global sequence indices.
        - energy_cutoff (float): Threshold; any pair with energy < this value is considered an edge.

    Output:
        - list of tuple: Each tuple (i, j) is a global‐index edge where the off‐target energy is below cutoff.

    Procedure:
        1. Extract all (i,j) positions from each matrix where energy < cutoff.
        2. Stack these positions together and sort each pair so (i,j) and (j,i) collapse to one.
        3. Remove duplicate pairs.
        4. Map local indices back to global indices via the `indices` list.
    '''
    hh = offtarget_dict['handle_handle_energies']
    hah = offtarget_dict['antihandle_handle_energies']
    ahah = offtarget_dict['antihandle_antihandle_energies']

    # 1) Find all local index pairs where energy is below the cutoff
    hh_infixes = np.argwhere(hh < energy_cutoff)
    hah_infixes = np.argwhere(hah < energy_cutoff)
    ahah_infixes = np.argwhere(ahah < energy_cutoff)

    # 2) Combine all results into one array
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))

    # 3) Sort each pair so that (i,j) and (j,i) become identical
    combined_infixes = np.sort(combined_infixes, axis=1)

    # 4) Remove duplicate rows to avoid counting the same edge twice
    combined_infixes = np.unique(combined_infixes, axis=0)

    # 5) Map local positions back to global sequence indices
    edges = [(indices[i], indices[j]) for i, j in combined_infixes]

    return edges




def select_vertices_to_remove(vertex_cover, num_vertices_to_remove):
    '''
    Selects a subset of vertices to remove from an existing vertex cover.

    Input:
        - vertex_cover (set): Current set of cover vertices.
        - num_vertices_to_remove (int): Desired number of vertices to remove.

    Output:
        - set: Randomly chosen vertices (size ≤ num_vertices_to_remove).

    '''
    return set(random.sample(list(vertex_cover), min(num_vertices_to_remove, len(vertex_cover))))


def iterative_vertex_cover_multi(V, E, preserve_V=None, num_vertices_to_remove=150, max_iterations=200, limit=+np.inf, multistart=30, population_size=5, show_progress=False):
    """
    Attempts to find a small vertex cover via multiple randomized restarts and iterative refinement.

    .. rubric:: Algorithm Outline

    1. For each of `multistart` attempts:
       a. Compute an initial cover via the greedy heuristic.
       b. Initialize a population containing that cover.
       c. Repeat up to `max_iterations`:
          * For each cover in the population:
            - Remove `num_vertices_to_remove` random vertices (respecting `preserve_V`).
            - Find uncovered edges and re-cover via the heuristic.
            - If the new cover is smaller, reset the population to this cover.
            - If it’s the same size but unique, add it to the population.
          * Trim the population to `population_size` by random sampling.
          * Optionally print progress.
       d. If this attempt’s best cover is smaller than the global best, update it and continue.

    .. note::
       Because minimum vertex cover is NP-hard, this is a heuristic: it runs fast but
       does not guarantee an optimal solution.

    :param V: All vertices in the graph (e.g., list or set of IDs).  
              *Note:* V is only used for printing/monitoring; the graph is fully encoded by E.
    :type V: iterable

    :param E: All edges (u, v) in global index space.
    :type E: iterable of tuple

    :param preserve_V: Vertices to preferentially keep out of removal.
    :type preserve_V: set, optional

    :param num_vertices_to_remove: Number of vertices to drop each iteration.
    :type num_vertices_to_remove: int

    :param max_iterations: Max refine steps per restart.
    :type max_iterations: int

    :param limit: Target threshold for |V| - |cover|; stops early if reached.
    :type limit: float

    :param multistart: Number of independent greedy restarts.
    :type multistart: int

    :param population_size: Max number of equal-sized covers to retain each iteration.
    :type population_size: int

    :param show_progress: If True, prints status each iteration.
    :type show_progress: bool

    :returns: The best (smallest) vertex cover found across all restarts.
    :rtype: set
    """

    # This keeps track of the overall best (i.e., smallest) vertex cover found across all multistart iterations.
    # There is also a separate "best_vertex_cover" inside each iteration (the inner loop).
    bestest_vertex_cover = None
   
    for i in range(multistart):
        
        
        # Create one initial greedy cover.
        best_vertex_cover = heuristic_vertex_cover_optimized2(E, preserve_V=preserve_V)
        current_vertex_cover = best_vertex_cover.copy()
        population = [current_vertex_cover]  # Start with the best vertex cover as the initial population
        iteration = 0
        
        
        
        while iteration < max_iterations:
            iteration += 1

            # Early exit if desired independent set size reached
            if -len(best_vertex_cover) + len(V) >= limit:
                print('found desired set')
                break

            # print('population is of lenght')
            # print(len(population))
            
            new_guys = []
            #Do the following for all good candidates already in the population
            for current_cover in population:
               
                current_cover2 = current_cover.copy()  # Create a copy to avoid modifying the original in the population

                # Step a: Remove random vertices from the current cover
                vertices_to_remove = select_vertices_to_remove(current_cover2, num_vertices_to_remove)
                current_cover2 -= vertices_to_remove

                # Step b: find uncovered edges that appeared due to step a and build a new graph with these uncovered endges
                uncovered_edges = find_uncovered_edges(E, current_cover2)
                


                # Re-run the heuristic on the new sub graph of uncovered edges
                additional_cover = heuristic_vertex_cover_optimized2(uncovered_edges, preserve_V=None)
                current_cover2 |= additional_cover  # Add the newly found cover of the sub graph to the remaining cover  to create again a complete vertex cover

                # Step d: Compare and update best solution
                # if a smaller cover is found replace the best cover and reset the population
                if len(current_cover2) < len(best_vertex_cover):
                    best_vertex_cover = current_cover2.copy()  # Copy to ensure best_vertex_cover remains separate
                    #
                    population = [best_vertex_cover]  # Reset population with the new best cover
                    new_guys = []
                    break

                # if the same size is found add it to the population to diversify the search. Its only added to the population if its not already in there. To avoid having duplicates. 
                elif len(current_cover2) == len(best_vertex_cover):
                    if all(current_cover2 != cover for cover in population):
                        new_guys.append(current_cover2.copy())  # Add a unique copy of the equal-sized cover
                        
            # update the population outside the population loop to avoid making the loop longer while in it 
            population = new_guys + population
            
            # limit the population but ensure random search
            if len(population) > population_size:
                population = random.sample(population, population_size)
                
            if show_progress:                                                    
                print(f"Iteration {iteration+1}: Found {len(population)} sets of size {-len(best_vertex_cover) + len(V)}") 

        # update the bestest_vertex_cover. keep record which of the multistarts resulted in the best.
        if bestest_vertex_cover is None or len(best_vertex_cover) < len(bestest_vertex_cover):
            bestest_vertex_cover = best_vertex_cover.copy()
            print("update bestest")
        print(f"Iteration {i + 1} of {multistart}| current bestest independent set size: {len(V)-len(best_vertex_cover)}")
    return bestest_vertex_cover








def evolutionary_vertex_cover(sequence_pairs, offtarget_limit, max_ontarget, min_ontarget, subsetsize=200, generations=100):
    
    '''
    Evolves an independent set of sequences from a set of candidate sequence pairs.
    Removes high‐energy (off‐target) interactions via vertex‐cover heuristics. 

    Input:
        - sequence_pairs (list): List of (index, (seq, rc_seq)) tuples for candidate sequences.
        - offtarget_limit (float): Energy threshold; edges exist where off‐target energy < this value.
        - max_ontarget (float): Upper bound for acceptable on‐target energy.
        - min_ontarget (float): Lower bound for acceptable on‐target energy.
        - subsetsize (int): Number of sequences to sample per generation.
        - generations (int): Number of evolutionary iterations to perform.

    Output:
        - list: Final list of (seq, rc_seq) pairs that form the best independent set.

    Procedure:
        1. Initialize:
            - non_cover_vertices: current best independent set (sequences not in vertex cover).
            - history: indices to avoid reselection, preserving diversity.
        2. For each generation:
            a. Select a random subset of sequences whose on‐target energies lie within [min_ontarget, max_ontarget], excluding history.
            b. Add back any previously preserved sequences (history) to the subset.
            c. Assert no duplicate indices remain.
            d. Compute all off‐target energies for this subset.
            e. Build the interaction graph: edges = pairs below offtarget_limit.
            f. Run the multi‐start, iterative vertex‐cover heuristic to find `removed_vertices` (Vertex cover, Vertices with off target binding).
            g. Derive the new independent set: all selected indices minus removed_vertices.
            h. If the new set is at least as large as the previous best, update `non_cover_vertices`; clear history if strictly larger.
            i. If within 95% of best size, add new set to history to guide future sampling.
            j. Log generation stats.
        3. On user interrupt, exit gracefully and save current best.
        4. After all generations or interruption, save the final sequences to a text file.

    Notes:
        - This implements a form of genetic “survivor selection” via vertex‐cover: 
          sequences that interact too strongly (below energy cutoff) are “removed” each generation.
        - History ensures we add sequences which worked before again to the pool. Maybe a different combination of them works.
    '''

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
            # Re-add previously preserved sequences
            sorted_history = sorted(history)
            extra_pairs = [sequence_pairs[idx][1] for idx in sorted_history]
            subset += extra_pairs
            indices += list(sorted_history)

            # Ensure no duplicate indices
            assert len(indices) == len(set(indices)), (
                f"Duplicate index found! "
                f"indices={indices} "
                f"set(indices)={sorted(set(indices))}"
            )

            # Compute off-target energies and build interaction graph
            off_e_subset = sc.compute_offtarget_energies(subset)
            Edges = build_edges(off_e_subset, indices, offtarget_limit)

            # Find sequences to remove via vertex-cover heuristic
            removed_vertices = iterative_vertex_cover_multi(
                indices, Edges,
                preserve_V=history,
                num_vertices_to_remove=len(indices) // 2
            )

            # Update independent set
            Vertices = set(indices)
            new_non_cover_vertices = Vertices - removed_vertices

            # If we’ve improved or matched best, update non_cover_vertices and history
            if len(new_non_cover_vertices) >= len(non_cover_vertices):
                if len(new_non_cover_vertices) > len(non_cover_vertices):
                    history.clear()
                non_cover_vertices = new_non_cover_vertices

            # If within 95% of best size, preserve these in history
            if len(new_non_cover_vertices) >= len(non_cover_vertices) * 0.95:
                history.update(new_non_cover_vertices)

            print(
                f"Generation {i + 1:2d} | "
                f"Current: {len(new_non_cover_vertices):3d} | "
                f"Best: {len(non_cover_vertices):3d} | "
                f"History size: {len(history):3d}"
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving best result so far...")

    # Save final result
    final_pairs = [sequence_pairs[idx][1] for idx in sorted(non_cover_vertices)]
    hf.save_sequence_pairs_to_txt(final_pairs)

    return final_pairs


if __name__ == "__main__":
    # Run test to see if the functions above work
    # I use this for debugging
    
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
    stats2 = sc.plot_on_off_target_histograms(onef, offef, output_path='dump/test.pdf')
    print(stats2)



 
