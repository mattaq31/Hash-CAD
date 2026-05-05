import numpy as np
import random
from collections import defaultdict


import logging

logger = logging.getLogger("orthoseq")
logger.addHandler(logging.NullHandler())
#logging.getLogger("nupack").setLevel(logging.ERROR)



def greedy_vertex_cover_heuristic(E, avoid_V=None, cleanup=True):
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
           c. Break ties randomly, preferring vertices in `avoid_V`.
           d. Add the selected vertex to the cover, remove it and its incident edges, and update degrees.
    
        Notes
        -----
        - `avoid_V` contains vertices that should be removed when possible, but they can still be kept.
        - Self-edges are covered immediately.
        - Orphan vertices (degree zero) are naturally independent and never need removal.
    
        :param E: Set of edges (u, v). Vertices can be any hashable.
        :type E: iterable of tuple
    
        :param avoid_V: Vertices you’d like to preferentially remove into the cover.
                        They can still be kept, just less likely.
        :type avoid_V: set, optional

        :param cleanup: If True, remove any redundant vertices from the final cover
                        without uncovering any edges.
        :type cleanup: bool
    
        :returns: A vertex cover (set of vertices touching every edge in E).
        :rtype: set
        """
       
       
       
       
       
        if avoid_V is None:
            avoid_V = set()
        
        
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

            # c) Last resort tie breaking. Pick at random but prefer ones in avoid_V if possible. The avoide will later not appear in the independent set, nudging the algorithm to explore more new sequences
            avoided = [v for v in min_overlap_vertices if v in avoid_V]

            if avoided:
                selected_vertex = random.choice(avoided)
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

        if cleanup and vertex_cover:
            # Try to remove redundant vertices without uncovering any edge.
            # We iterate over a copy so we can safely mutate `vertex_cover`.
            for v in list(vertex_cover):
                # Hypothetical cover if we drop v.
                cover_without_v = vertex_cover - {v}
                can_remove = True

                # If any edge incident to v would be uncovered after removing v,
                # then v must stay in the cover.
                for u, w in E:
                    if u == v or w == v:
                        # Pick the non-v endpoint of the edge (u, w).
                        other = w if u == v else u  # inline if: if v is u, take w; otherwise take u
                        if other not in cover_without_v:
                            can_remove = False
                            break

                if can_remove:
                    vertex_cover.remove(v)

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
              Self-edges (u == v) are included if u is not in the cover.
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

    # 2.1) Combine all noflank_results into one array
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))

    # 2.2) Sort each pair so that (i,j) and (j,i) become identical
    combined_infixes = np.sort(combined_infixes, axis=1)

    # 3) Remove duplicate rows to avoid counting the same edge twice
    combined_infixes = np.unique(combined_infixes, axis=0)

    # 4) Map local positions back to global sequence indices
    edges = [(indices[i], indices[j]) for i, j in combined_infixes]

    return edges


def compute_pair_conflict_probability(offtarget_dict, energy_cutoff):
    """
    Computes pair-level conflict probability using the same conflict rule as `build_edges`.

    A pair (i, j) with i != j is counted as conflicting if at least one of the three
    off-target interaction matrices violates `energy_cutoff`, exactly as in `build_edges`.

    :param offtarget_dict: Dictionary containing the three off-target energy matrices.
    :type offtarget_dict: dict

    :param energy_cutoff: Threshold below which an interaction defines a conflict.
    :type energy_cutoff: float

    :returns: Fraction of conflicting unordered sequence-pair pairs in [0, 1].
              Returns 0.0 if fewer than 2 sequence pairs are present.
    :rtype: float
    """
    hh = offtarget_dict['handle_handle_energies']
    hah = offtarget_dict['antihandle_handle_energies']
    ahah = offtarget_dict['antihandle_antihandle_energies']

    n = int(hh.shape[0])
    if hah.shape != hh.shape or ahah.shape != hh.shape:
        raise ValueError("Off-target matrices must have identical shapes.")

    if n < 2:
        return 0.0

    # Reuse the exact graph-construction logic for maximum consistency/readability.
    edges = build_edges(offtarget_dict, list(range(n)), energy_cutoff)
    # Pair-level conflict probability is defined on unordered distinct pairs only.
    conflict_edges = sum(1 for i, j in edges if i != j)
    total_pairs = n * (n - 1) // 2

    return float(conflict_edges / total_pairs) if total_pairs > 0 else 0.0




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


def iterative_vertex_cover_refinement(V, E, avoid_V=None, num_vertices_to_remove=150, max_iterations=200, limit=+np.inf, show_progress=False):
    """
    Attempts to find a small vertex cover via iterative randomized refinement.
    Strategically calls greedy_vertex_cover_heuristic.

    Algorithm Outline
    -----------------
    1. Compute an initial cover via the greedy heuristic.
    2. Repeat up to `max_iterations`:
       a. Remove `num_vertices_to_remove` random vertices from the current best cover.
       b. Find uncovered edges and re-cover them via the greedy heuristic.
       c. If the repaired cover is no larger than the best-so-far cover, keep it.
       d. Optionally print progress.

    Notes
    -----
    Because minimum vertex cover is NP-hard, this is a heuristic: it runs quickly but
    does not guarantee an optimal solution.

    :param V: All vertices in the graph (e.g., list or set of IDs).
              *Note:* V is only used for printing/monitoring; the graph is fully encoded by E.
    :type V: iterable

    :param E: All edges (u, v) in global index space.
    :type E: iterable of tuple

    :param avoid_V: Vertices to preferentially remove into the cover.
    :type avoid_V: set, optional

    :param num_vertices_to_remove: Number of vertices to drop each iteration.
    :type num_vertices_to_remove: int

    :param max_iterations: Max refine steps per restart.
    :type max_iterations: int

    :param limit: Target threshold for |V| - |cover|; stops early if reached.
    :type limit: float

    :param show_progress: If True, prints status each iteration.
    :type show_progress: bool

    :returns: Tuple of (best_vertex_cover, trajectories), where trajectories stores
              the independent set size after each refinement iteration.
    :rtype: tuple[set, list[list[int]]]
    """

    if avoid_V is None:
        avoid_V = set()

    def avoid_overlap_size(cover):
        return len(cover & avoid_V)

    best_vertex_cover = greedy_vertex_cover_heuristic(E, avoid_V=avoid_V)
    size_trajectory = []

    for iteration in range(1, max_iterations + 1):
        if len(V) - len(best_vertex_cover) >= limit:
            if show_progress:
                print("found desired set")
            break

        candidate_cover = best_vertex_cover.copy()
        vertices_to_remove = select_vertices_to_remove(candidate_cover, num_vertices_to_remove)
        candidate_cover -= vertices_to_remove

        uncovered_edges = find_uncovered_edges(E, candidate_cover)
        additional_cover = greedy_vertex_cover_heuristic(uncovered_edges, avoid_V=None)
        candidate_cover |= additional_cover

        if len(candidate_cover) < len(best_vertex_cover):
            best_vertex_cover = candidate_cover.copy()
        elif len(candidate_cover) == len(best_vertex_cover):
            if avoid_overlap_size(candidate_cover) > avoid_overlap_size(best_vertex_cover):
                best_vertex_cover = candidate_cover.copy()

        size_trajectory.append(len(V) - len(best_vertex_cover))
        if show_progress:
            print(
                f"Iteration {iteration}: Independent set size {len(V) - len(best_vertex_cover)}"
            )

    if len(size_trajectory) > 20:
        head = ", ".join(str(x) for x in size_trajectory[:10])
        tail = ", ".join(str(x) for x in size_trajectory[-10:])
        traj_str = f"[{head}, ..., {tail}]"
    else:
        traj_str = "[" + ", ".join(str(x) for x in size_trajectory) + "]"
    print(
        f"Current best independent set size: {len(V) - len(best_vertex_cover)} "
        f"| set size trajectory: {traj_str}"
    )
    return best_vertex_cover, [size_trajectory]





 
