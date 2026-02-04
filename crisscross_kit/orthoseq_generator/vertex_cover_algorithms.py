from orthoseq_generator import sequence_computations as sc
from orthoseq_generator import helper_functions as hf

import numpy as np
import random
from collections import defaultdict


import logging

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())
#logging.getLogger("nupack").setLevel(logging.ERROR)



def heuristic_vertex_cover_optimized2(E, preserve_V=None):
        """
        This function is the core of the sequence search algorithm. It’s a heuristic approach
        to solve the NP-hard minimum vertex cover problem.
    
        Inspired by:
          - Joshi (2020), "Neighbourhood Evaluation Criteria for Vertex Cover Problem"
          - StackExchange discussion: https://cs.stackexchange.com/q/74546
    
        Algorithm Outline
        -----------------
        1. Immediately add any self-edge vertices (u == v) to the cover.
        2. Build an adjacency list for all non-self edges.
        3. Track the degree (number of neighbors) for each vertex.
        4. While edges remain:
           a. Identify the vertex/vertices with maximum degree.
           b. Among those, select the vertex with the fewest neighbors that also share that max degree.
           c. Break ties randomly, preferring vertices not in `preserve_V`.
           d. Add the selected vertex to the cover, remove it and its incident edges, and update degrees.
    
        Notes
        -----
        - `preserve_V` contains vertices that should be avoided when possible, but they can still be chosen.
        - Self-edges are covered immediately.
        - Orphan vertices (degree zero) are naturally independent and never need removal.
    
        :param E: Set of edges (u, v). Vertices can be any hashable.
        :type E: iterable of tuple
    
        :param preserve_V: Vertices you’d like to preferentially keep out of the cover.
                           They can still be removed, just less likely.
        :type preserve_V: set, optional
    
        :returns: A vertex cover (set of vertices touching every edge in E).
        :rtype: set
        """
       
       
       
       
       
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
    """
    Finds edges that are not covered by the current vertex cover.

    Description
    -----------
    Given a collection of edges `E` and a set `vertex_cover` of vertices, this function returns
    all edges which are not in the set. Technically, `vertex_cover` is not a full
    vertex cover of the graph but only a partial vertex cover.

    :param E: Collection of edges (u, v).
    :type E: iterable of tuple

    :param vertex_cover: Set of vertices currently in the cover.
    :type vertex_cover: set

    :returns: Edges (u, v) from `E` for which neither u nor v is in `vertex_cover`.
    :rtype: set
    """
    uncovered_edges = set()
    for u, v in E:
        if u not in vertex_cover and v not in vertex_cover:
            uncovered_edges.add((u, v))
        if u== v and u not in vertex_cover:
            uncovered_edges.add((u, v))
    return uncovered_edges


def build_edges(offtarget_dict, indices, energy_cutoff):

    """
    Builds a list of global index‐pair edges from off‐target energy matrices.
    (Global indices refer to the positions in the originally created sequence-pair list.)

    Procedure
    ---------
    1. Extract all (i, j) positions from each matrix where energy < `energy_cutoff`.
    2. Stack these positions together and sort each pair so (i, j) and (j, i) collapse to one.
    3. Remove duplicate pairs.
    4. Map local indices back to global sequence indices via the `indices` list.

    :param offtarget_dict: Dictionary containing three N×N numpy arrays under keys:
        - 'handle_handle_energies'
        - 'antihandle_handle_energies'
        - 'antihandle_antihandle_energies'
    :type offtarget_dict: dict

    :param indices: List of global sequence indices corresponding to matrix rows/columns.
    :type indices: list of int

    :param energy_cutoff: Threshold below which an energy defines an edge.
    :type energy_cutoff: float

    :returns: List of (i, j) tuples where each is a global‐index edge with off‐target energy < cutoff.
    :rtype: list of tuple
    """
    
    hh = offtarget_dict['handle_handle_energies']
    hah = offtarget_dict['antihandle_handle_energies']
    ahah = offtarget_dict['antihandle_antihandle_energies']

    # 1) Find all local index pairs where energy is below the cutoff
    hh_infixes = np.argwhere(hh < energy_cutoff)
    hah_infixes = np.argwhere(hah < energy_cutoff)
    ahah_infixes = np.argwhere(ahah < energy_cutoff)

    # 2.1) Combine all results into one array
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))

    # 2.2) Sort each pair so that (i,j) and (j,i) become identical
    combined_infixes = np.sort(combined_infixes, axis=1)

    # 3) Remove duplicate rows to avoid counting the same edge twice
    combined_infixes = np.unique(combined_infixes, axis=0)

    # 4) Map local positions back to global sequence indices
    edges = [(indices[i], indices[j]) for i, j in combined_infixes]

    return edges




def select_vertices_to_remove(vertex_cover, num_vertices_to_remove):
    """
    Selects a subset of vertices to remove from an existing vertex cover.

    :param vertex_cover: Current set of cover vertices.
    :type vertex_cover: set

    :param num_vertices_to_remove: Desired number of vertices to remove.
    :type num_vertices_to_remove: int

    :returns: Randomly chosen vertices to remove (size ≤ num_vertices_to_remove).
    :rtype: set
    """
    return set(random.sample(list(vertex_cover), min(num_vertices_to_remove, len(vertex_cover))))


def iterative_vertex_cover_multi(V, E, preserve_V=None, num_vertices_to_remove=150, max_iterations=200, limit=+np.inf, multistart=30, population_size=5, show_progress=False):
    """
    Attempts to find a small vertex cover via multiple randomized restarts and iterative refinement. Strategically calls heuristic_vertex_cover_optimized2

    Algorithm Outline
    -----------------
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
       d. If this attempt’s best cover is smaller than the global best, update it.

    Notes
    -----
    Because minimum vertex cover is NP-hard, this is a heuristic: it runs quickly but
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








def evolutionary_vertex_cover(sequence_pairs, offtarget_limit, max_ontarget, min_ontarget, subsetsize=200, generations=100, stop_event=None):
    
    """
    Evolves an independent set of sequences from a set of candidate sequence pairs by
    iteratively removing high-energy (off-target) interactions via vertex-cover heuristics.  
    Implements a form of genetic “survivor selection” via repeated vertex-cover:
    new sequences are sampled each generation and those with strong off-target interactions
    are “removed” again. The `history` variable ensures previously promising sequences
    re-enter the sampling pool.

    Procedure
    ---------
    1. Initialize:
       - `non_cover_vertices`: best independent set so far (sequences not in the cover).
       - `history`: indices to avoid reselection, preserving diversity.  
    2. For each of `generations` iterations:
       a. Check if `stop_event` is set. If so, break.
       b. Select a random subset of sequences whose on-target energies lie within
          [`min_ontarget`, `max_ontarget`], excluding those in `history`.  
       c. Re-add any sequences from `history` to ensure good candidates are retained.  
       d. Assert that there are no duplicate indices.  
       e. Compute off-target energies for the subset.  
       f. Build the off-target interaction graph (edges where energy < `offtarget_limit`).  
       g. Apply the multi-start, iterative vertex-cover heuristic to find `removed_vertices`.  
       h. Derive the new independent set: all selected indices minus `removed_vertices`.  
       i. If this independent set is at least as large as the previous best:
          - Update `non_cover_vertices`.
          - Clear `history` if strictly larger.  
       j. If its size ≥ 95% of the best, add its indices (deduplicated) to `history`.  
       k. Print generation summary statistics.  
    3. On user interrupt (Ctrl+C) or `stop_event`, exit gracefully and proceed to save the current best.  
    4. After all generations or interruption, save the final independent set to a text file.

    Notes
    -----
    - Catches `KeyboardInterrupt` to allow early exit: the best result so far is saved and plotted.

    :param sequence_pairs: List of (index, (seq, rc_seq)) tuples for candidate sequences.
    :type sequence_pairs: list of tuple

    :param offtarget_limit: Energy threshold below which an off-target interaction defines an edge.
    :type offtarget_limit: float

    :param max_ontarget: Upper bound for acceptable on-target energy.
    :type max_ontarget: float

    :param min_ontarget: Lower bound for acceptable on-target energy.
    :type min_ontarget: float

    :param subsetsize: Number of sequences to sample per generation.
    :type subsetsize: int

    :param generations: Number of evolutionary iterations to perform.
    :type generations: int

    :param stop_event: Optional threading.Event to stop the search.
    :type stop_event: threading.Event

    :returns: Final list of (seq, rc_seq) pairs forming the best independent set.
    :rtype: list of tuple
    """

    non_cover_vertices = set()
    history = set()



    try:
        for i in range(generations):
            if stop_event is not None and stop_event.is_set():
                print("Stop event detected. Stopping search...")
                break
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
            if isinstance(sequence_pairs, list):
                extra_pairs = [sequence_pairs[idx][1] for idx in sorted_history]
            else:
                extra_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted_history]
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
            logger.info(
                f"Generation {i + 1:2d} | "
                f"Current: {len(new_non_cover_vertices):3d} | "
                f"Best: {len(non_cover_vertices):3d} | "
                f"History size: {len(history):3d}"
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user. Saving best result so far...")

    # Save final result
    if isinstance(sequence_pairs, list):
        final_pairs = [sequence_pairs[idx][1] for idx in sorted(non_cover_vertices)]
    else:
        final_pairs = [sequence_pairs.get_pair_by_id(idx) for idx in sorted(non_cover_vertices)]

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



 
