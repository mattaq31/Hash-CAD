from sequence_picking_tools import *
import pickle
import numpy as np
from collections import Counter
import random
from collections import defaultdict


def heuristic_vertex_cover(V, E):
    # Initialize an empty set to store the vertex cover
    vertex_cover = set()

    # Copy the edges list, so we can modify it
    edges = E.copy()

    # Loop until all edges are covered (i.e., E is empty)
    while edges:
        # Count occurrences of each vertex in the edges
        vertex_counter = Counter([v for edge in edges for v in edge])

        # Find the maximum occurrence count
        max_count = max(vertex_counter.values())

        # Get all vertices that have this maximum occurrence count (handling ties)
        most_common_vertices = [v for v, count in vertex_counter.items() if count == max_count]

        # Randomly select one vertex from the tied most common vertices
        most_common_vertex = random.choice(most_common_vertices)

        # Add the selected vertex to the vertex cover
        vertex_cover.add(most_common_vertex)

        # Remove all edges that include the selected vertex
        edges = [edge for edge in edges if most_common_vertex not in edge]

        print(len(edges))
    # Return the resulting vertex cover
    return vertex_cover



def heuristic_vertex_cover_optimized(V, E):
    # Initialize the vertex cover set
    vertex_cover = set()

    # Remove self-edges

    to_remove = set()  # Collect pairs to remove from E
    for u, v in E:
        if u == v:
            vertex_cover.add(u)
            to_remove.add((u, v))  # Mark for removal

    E -= to_remove

    # build adjacent list

    adj_list = defaultdict(set)
    for u, v in E:

            adj_list[u].add(v)
            adj_list[v].add(u)


    # Initialize degrees
    degrees = {v: len(neighbors) for v, neighbors in adj_list.items()}

    # Loop until all edges are covered
    while degrees:
        # Find the maximum degree
        max_degree = max(degrees.values())
        # Get all vertices with the maximum degree
        max_degree_vertices = [v for v, deg in degrees.items() if deg == max_degree]
        # Randomly select one vertex from the tied vertices
        selected_vertex = random.choice(max_degree_vertices)
        # Add the selected vertex to the vertex cover
        vertex_cover.add(selected_vertex)
        # Remove the selected vertex from degrees and adjacency list
        neighbors = adj_list.pop(selected_vertex)
        degrees.pop(selected_vertex)
        # Remove edges incident to the selected vertex
        for neighbor in neighbors:
            adj_list[neighbor].remove(selected_vertex)
            # Update degrees
            degrees[neighbor] -= 1
            # If the neighbor has no more edges, remove it from degrees
            if degrees[neighbor] == 0:
                degrees.pop(neighbor)
                adj_list.pop(neighbor)

    # Return the vertex cover
    return vertex_cover

def heuristic_vertex_cover_optimized2(V, E):
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
                adj_list[u].add(v)
                adj_list[v].add(u)

        # Initialize degrees
        degrees = {v: len(neighbors) for v, neighbors in adj_list.items()}

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

            # Randomly select one of the vertices with the minimum overlap count
            min_overlap_vertex = random.choice(min_overlap_vertices)

            # Add the selected vertex to the vertex cover
            selected_vertex = min_overlap_vertex
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

def find_uncovered_edges2(E, vertex_cover):
    # Returns the set of edges not covered by the current vertex cover
    return {(u, v) for u, v in E if u not in vertex_cover and v not in vertex_cover}

def select_vertices_to_remove(vertex_cover, num_vertices_to_remove):
    # Selects vertices to remove from the vertex cover
    # Here we use random selection; you can change this to other criteria
    return set(random.sample(list(vertex_cover), min(num_vertices_to_remove, len(vertex_cover))))


def select_vertices_to_remove2(vertex_cover, additional_to_remove, specific_vertices_to_remove):
    # Remove specific vertices from the vertex cover if present
    removed_vertices = vertex_cover.intersection(specific_vertices_to_remove)

    # Randomly remove additional vertices if needed

    if additional_to_remove > 0:
        eligible_vertices = vertex_cover - removed_vertices
        additional_removed = set(random.sample(list(eligible_vertices),min(additional_to_remove, len(eligible_vertices))))
        removed_vertices |= additional_removed

    return removed_vertices







def iterative_vertex_cover(V, E, num_vertices_to_remove=150, max_iterations=42850, limit = 64):
    # Initialize

    size =450
    best_vertex_cover = heuristic_vertex_cover_optimized2(V, E)
    current_vertex_cover = best_vertex_cover.copy()
    population = [current_vertex_cover]  # Start with the best vertex cover as the initial population
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"Iteration {iteration}, current best size: {len(best_vertex_cover) - len(V)}")
        if -len(best_vertex_cover) + len(V)>=limit:
            print('found desired set')
            break

        print('population is of lenght')
        print(len(population))
        what = 0
        new_guys = []
        for current_cover in population:
            what = what +1
            current_cover2 = current_cover.copy()  # Create a copy to avoid modifying the original in the population

            # Step a: Remove vertices from the current cover
            vertices_to_remove = select_vertices_to_remove(current_cover2, num_vertices_to_remove)
            current_cover2 -= vertices_to_remove

            # Step b: Update the graph (find uncovered edges)
            uncovered_edges = find_uncovered_edges(E, current_cover2)
            # Build a subgraph with only uncovered edges
            remaining_vertices = set(u for u, v in uncovered_edges) | set(v for u, v in uncovered_edges)

            # Re-run the heuristic on the subgraph
            additional_cover = heuristic_vertex_cover_optimized2(remaining_vertices, uncovered_edges)
            current_cover2 |= additional_cover  # Update the current vertex cover

            # Step d: Compare and update best solution

            #print(len(current_cover2))
            #print(what)
            if len(current_cover2) < len(best_vertex_cover):
                best_vertex_cover = current_cover2.copy()  # Copy to ensure best_vertex_cover remains separate
                print(f"Found better set of size {len(best_vertex_cover) - len(V)}")
                population = [best_vertex_cover]  # Reset population with the new best cover
                new_guys= []
                break
            elif len(current_cover2) == len(best_vertex_cover):
                if all(current_cover2 != cover for cover in population):
                    new_guys.append(current_cover2.copy())  # Add a unique copy of the equal-sized cover

        population = new_guys+population
        if len(population) > size:
            population = random.sample(population, size)



    # Perform final local search on the best solution
    #best_vertex_cover = local_search_vertex_cover(V, E, best_vertex_cover)

    return best_vertex_cover







def evolutionary_vertex_cover(V, E, population_size=450, num_generations=650,
                              num_vertices_to_remove=840):
    # Initialize

    size = population_size
    best_vertex_cover = heuristic_vertex_cover_optimized2(V, E)
    current_vertex_cover = best_vertex_cover.copy()
    population = [current_vertex_cover]  # Start with the best vertex cover as the initial population
    iteration = 0

    while iteration < num_generations:
        iteration += 1
        print(f"Iteration {iteration}, current best size: {len(best_vertex_cover) - len(V)}")

        print('population is of lenght')
        print(len(population))
        what = 0
        new_guys = []
        # Assume this part is within your evolutionary algorithm loop
        for current_cover in population:
            what = what + 1
            current_cover2 = current_cover.copy()  # Create a copy to avoid modifying the original in the population

            # Step a: Remove vertices from the current cover
            vertices_to_remove = select_vertices_to_remove(current_cover2, num_vertices_to_remove)

            # Introduce another cover as a random sample from population, excluding current_cover
            other_population = [cover for cover in population if cover != current_cover]
            if other_population:  # Ensure there is at least one other cover
                another_cover = random.choice(other_population)
            else:
                another_cover = V
                # Compute V - another_cover and use it with select_vertices_to_remove2
            specific_vertices_to_remove = V - another_cover
            #print(len(specific_vertices_to_remove))
            vertices_to_remove = select_vertices_to_remove2(current_cover2, num_vertices_to_remove, specific_vertices_to_remove)
            current_cover2 -= vertices_to_remove

            # Step b: Update the graph (find uncovered edges)
            uncovered_edges = find_uncovered_edges(E, current_cover2)

            # Build a subgraph with only uncovered edges
            remaining_vertices = set(u for u, v in uncovered_edges) | set(v for u, v in uncovered_edges)

            # Re-run the heuristic on the subgraph
            additional_cover = heuristic_vertex_cover_optimized2(remaining_vertices, uncovered_edges)
            current_cover2 |= additional_cover  # Update the current vertex cover

            # Step d: Compare and update best solution

            # print(len(current_cover2))
            # print(what)
            if len(current_cover2) < len(best_vertex_cover):
                best_vertex_cover = current_cover2.copy()  # Copy to ensure best_vertex_cover remains separate
                print(f"Found better set of size {len(best_vertex_cover) - len(V)}")
                population = [best_vertex_cover]  # Reset population with the new best cover
                new_guys = []
                break
            elif len(current_cover2) == len(best_vertex_cover):
                if all(current_cover2 != cover for cover in population):
                    new_guys.append(current_cover2.copy())  # Add a unique copy of the equal-sized cover

        population = new_guys + population
        if len(population) > size:
            population = random.sample(population, size)

    # Perform final local search on the best solution
    # best_vertex_cover = local_search_vertex_cover(V, E, best_vertex_cover)

    return best_vertex_cover




if __name__ == "__main__":

    # open the old handle sequences as dictionary new_sequence_highenergy_cross
    #with open('new_sequence_toto_test_energy_dict_highenergyself3.pkl', 'rb') as f:

    name = 'TT_no_crosscheck96to104'
    with open(name + '.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    handles = list(handle_energy_dict.keys())
    #with open('new_sequence_highenergy_cross2.pkl', 'rb') as f:
    with open(name + 'cross.pkl', 'rb') as f:
        crossdick = pickle.load(f)

    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open('test.pkl', 'wb') as f:
        pickle.dump(crossdick , f)
    print('hallo')

    # Load the statistics
    with open('stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    f1 = 2.43
    f3 = -10.60

    f2 =4

    max_on = stat_dict['max_on']
    min_on = stat_dict['mean_on']- f2 * stat_dict['std_on']


    min_extrem_off = stat_dict['mean_off']- f1*stat_dict['std_off']
    print(min_extrem_off)
    print('cutoff is above')

    min_mean_off = stat_dict['mean_off']-f3*stat_dict['std_off']
    print(min_mean_off)


    hh=crossdick['handle_handle_energies']
    hah= crossdick['antihandle_handle_energies']
    ahah = crossdick['antihandle_antihandle_energies']
    all_energies = crossdick['all_energies']

    # Find indices where values are less than min_extrem_off for each array
    hh_infixes = np.argwhere(hh < min_extrem_off)
    hah_infixes = np.argwhere(hah < min_extrem_off)
    ahah_infixes = np.argwhere(ahah < min_extrem_off)

    # Print the results
    print("Indices in 'hh' where value < min_extrem_off:", hh_infixes)
    print("Indices in 'hah' where value < min_extrem_off:", hah_infixes)
    print("Indices in 'ahah' where value < min_extrem_off:", ahah_infixes)



    # Combine the numpy arrays vertically into one
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))
    print(combined_infixes)
    combined_infixes = np.sort(combined_infixes, axis=1)

    # Eliminate duplicates in place
    combined_infixes = np.unique(combined_infixes, axis=0)
    for test in combined_infixes:
        if test[1]==test[0]:
            print(test[0], test[1])
    print('sorted')
    print(combined_infixes)

    # Convert the combined array to a list of tuples for counting
    combined_infixes_list = [tuple(row) for row in combined_infixes]

    handle_ids = set(range(len(handles)))
    # Example 'handles' list containing strings
    # Assuming handles contains enough elements to match the indices in the arrays
    # For example, handles = ['A', 'B', 'C', 'D', ...]

    def replace_indices_with_handles(infixes, handles):
        # Replace indices in the infixes with the corresponding values from handles list
        return [(handles[i], handles[j]) for i, j in infixes]






    vertex_cover = iterative_vertex_cover(handle_ids, combined_infixes_list)

    #vertex_cover2 = ilp_vertex_cover(handle_ids, combined_infixes_list)
    print("Minimum Vertex Cover:", vertex_cover)

    # Map the vertex cover indices to the actual handle names
    vertex_cover_handles = [handles[i] for i in vertex_cover]

    # Get the set of all handle indices
    all_handle_indices = set(range(len(handles)))

    # Subtract the vertex cover indices from the set of all handle indices
    non_vertex_cover_indices = all_handle_indices - vertex_cover

    # Map the non-vertex cover indices to the actual handle names
    non_vertex_cover_handles = [handles[i] for i in non_vertex_cover_indices]
    print(len(non_vertex_cover_handles))
    # Print the handles that are not part of the vertex cover
    print("Non-Vertex Cover (Handles):", non_vertex_cover_handles)
    # Step 2: Access energy values for non-vertex cover handles from handle_energy_dict
    non_vertex_cover_energy_dict = {handle: handle_energy_dict[handle] for handle in non_vertex_cover_handles}

    # Step 3: Save the non-vertex cover energy dictionary to a new pickle file
    with open(name + 'handlesxx.pkl', 'wb') as f:
        pickle.dump(non_vertex_cover_energy_dict, f)

    print(f"Non-vertex cover energy dictionary saved with {len(non_vertex_cover_energy_dict)} handles.")



    # Print the actual handles corresponding to the vertex cover
    print("Minimum Vertex Cover (Handles):", vertex_cover_handles)

    # Save to a text file
    with open('min_extrem_off.txt', 'w') as f:
        f.write(str(min_extrem_off))