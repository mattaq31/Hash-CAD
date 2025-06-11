from distutils.command.build import build

import pulp
from Energy_computation_functions import *
from sequence_picking_tools import *
import pickle
import matplotlib.pyplot as plt
import numpy as np
import time
from collections import Counter
from collections import Counter, defaultdict
import random
import heapq
import math
from collections import defaultdict
import heapq
import networkx as nx


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



def select_vertices_to_remove(vertex_cover, num_vertices_to_remove):
    # Selects vertices to remove from the vertex cover
    # Here we use random selection; you can change this to other criteria
    return set(random.sample(list(vertex_cover), min(num_vertices_to_remove, len(vertex_cover))))



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



def iterative_vertex_cover2(sequence_pairs, offtarget_limit, max_ontarget, min_ontarget, subsetsize=200, generations= 100):

   non_cover_vertices= set()
   history = set()

   for i in range(generations):
       # Select sequences with on-target energy in desired range
        subset, indices = select_subset_in_energy_range(
           sequence_pairs, 
           energy_min=min_ontarget, 
           energy_max=max_ontarget,
           max_size=subsetsize, 
           Use_Library=True, 
           avoid_indices=non_cover_vertices,
        )
       
        sorted_uncovered = list(history)
        extra_pairs = [sequence_pairs[idx][1] for idx in history]
        subset += extra_pairs
        indices += sorted_uncovered
        # Compute off-target energies for the subset
        off_e_subset = compute_offtarget_energies(subset, Use_Library=True)

        # Build the off-target interaction graph
        Edges = build_edges(off_e_subset,indices, offtarget_limit)

        # Run the heuristic vertex cover algorithm
        removed_vertices = heuristic_vertex_cover_optimized2(Edges,history)

        # Identify sequences not selected by the heuristic
        Vertices = set(indices)
        new_non_cover_vertices = Vertices- removed_vertices
        
        if len(new_non_cover_vertices) >= len(non_cover_vertices):
            
            if len(new_non_cover_vertices) >len(non_cover_vertices):
                history.clear()
                
            non_cover_vertices = new_non_cover_vertices
            history.update(new_non_cover_vertices)

        print(f"Generation {i + 1:2d} | Current: {len(new_non_cover_vertices):3d} sequences | Best so far: {len(non_cover_vertices):3d} | Preserved pool length: {len(history):3d}")

   # Return the actual sequence pairs (seq, rc) in same format as sequence_pairs
   return [sequence_pairs[idx] for idx in sorted(non_cover_vertices)]


if __name__ == "__main__":
    # Run test to see if the functions above work
    # Set a fixed random seed for reproducibility
    RANDOM_SEED = 42
    random.seed(RANDOM_SEED)

    # Create candidate sequences
    ontarget7mer = create_sequence_pairs_pool(length=6, fivep_ext="", threep_ext="", avoid_gggg=False)

    # Define energy thresholds
    offtarget_limit = -5.5
    max_ontarget = -7.9
    min_ontarget = -9.5
    # Select sequences with on-target energy in desired range
    subset, indices = select_subset_in_energy_range(
        ontarget7mer, energy_min=min_ontarget, energy_max=max_ontarget,
        max_size=30, Use_Library=True, avoid_indices=set()
    )

    # Compute off-target energies for the subset
    off_e_subset = compute_offtarget_energies(subset, Use_Library=True)

    # Build the off-target interaction graph
    Edges = build_edges(off_e_subset, indices, offtarget_limit)


    # Run the heuristic vertex cover algorithm
    orthogonal_seq_pairs = iterative_vertex_cover2(ontarget7mer, offtarget_limit, max_ontarget, min_ontarget, subsetsize=150, generations= 350)
    print(orthogonal_seq_pairs)



 
