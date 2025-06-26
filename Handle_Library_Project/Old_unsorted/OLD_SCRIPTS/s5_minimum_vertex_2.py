from sequence_generator.sequence_computations import *
from sequence_picking_tools import *
import pickle
import numpy as np
from collections import Counter



def create_graph_edges(cutoff,handles, crossdick):
    # Get the set of all handle indices
    all_handle_indices = set(range(len(handles)))

    hh = crossdick['handle_handle_energies']
    hah = crossdick['antihandle_handle_energies']
    ahah = crossdick['antihandle_antihandle_energies']


    # Find indices where values are less than min_extrem_off for each array
    hh_infixes = np.argwhere(hh < cutoff)
    hah_infixes = np.argwhere(hah < cutoff)
    ahah_infixes = np.argwhere(ahah < cutoff)

    # Combine the numpy arrays vertically into one
    combined_infixes = np.vstack((hh_infixes, hah_infixes, ahah_infixes))
    # Sort within the edges to later identify dublicates 1,2 and 2,1 are the same after sorting
    combined_infixes = np.sort(combined_infixes, axis=1)

    # Eliminate duplicates in place
    combined_infixes = np.unique(combined_infixes, axis=0)

    # Convert the combined array to a list of tuples for counting
    combined_infixes_list = [tuple(row) for row in combined_infixes]

    return  all_handle_indices, combined_infixes_list
def heuristic_vertex_cover(V, E):
    # Initialize an empty set to store the vertex cover
    vertex_cover = set()

    # Copy the edges list, so we can modify it
    edges = E.copy()
    print(len(edges))
    # Find and remove self-edges
    self_edges = [edge for edge in edges if edge[0] == edge[1]]
    for edge in self_edges:
        edges.remove(edge)

    # Loop until all edges are covered (i.e., E is empty)
    while edges:
        print(len(edges))
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

    # Return the resulting vertex cover
    return vertex_cover

if __name__ == "__main__":

    with open('TT_no_crosscheck975to1075.pkl', 'rb') as f:
        handle_energy_dict = pickle.load(f)

    handles = list(handle_energy_dict.keys())
    #with open('new_sequence_highenergy_cross2.pkl', 'rb') as f:
    with open('TT_no_crosscheck975to1075cross.pkl', 'rb') as f:
        crossdick = pickle.load(f)

    # Save the new_sequence_energy_dict to a pickle file with a fixed name
    with open('../test.pkl', 'wb') as f:
        pickle.dump(crossdick , f)
    print('hallo')

    # Load the statistics
    with open('../stat_dict.pkl', 'rb') as f:
        stat_dict = pickle.load(f)

    f1 = 2.41
    f3 = -13.60

    f2 =4

    max_on =stat_dict['max_on']
    min_on = stat_dict['mean_on']- f2 * stat_dict['std_on']


    min_extrem_off = stat_dict['mean_off']- f1*stat_dict['std_off']

    print(len(handles))


    handle_ids = set(range(len(handles)))
    # Example 'handles' list containing strings
    # Assuming handles contains enough elements to match the indices in the arrays
    # For example, handles = ['A', 'B', 'C', 'D', ...]

    def replace_indices_with_handles(infixes, handles):
        # Replace indices in the infixes with the corresponding values from handles list
        return [(handles[i], handles[j]) for i, j in infixes]






    all_vertices, all_edges= create_graph_edges(min_extrem_off ,handles, crossdick)

    vertex_cover = heuristic_vertex_cover(handle_ids, all_edges)
    # Subtract the vertex cover indices from the set of all handle indices


    #vertex_cover2 = ilp_vertex_cover(handle_ids, combined_infixes_list)
    print("Minimum Vertex Cover:", vertex_cover)

    # Map the vertex cover indices to the actual handle names
    vertex_cover_handles = [handles[i] for i in vertex_cover]


    # Subtract the vertex cover indices from the set of all handle indices
    non_vertex_cover_indices = all_vertices - vertex_cover
    print('I found handles')
    print(len(non_vertex_cover_indices))
    print(non_vertex_cover_indices)
    # Initialize an empty set to store vertices connected to non-vertex-cover vertices
    connected_vertices = set()

    # Iterate through each edge in all_edges
    for edge in all_edges:
     # Add edge that connects only non-vertex-cover vertices
        if edge[0] in non_vertex_cover_indices:
            connected_vertices.add(edge[1])  # Add connected vertex
        elif edge[1] in non_vertex_cover_indices:
            connected_vertices.add(edge[0])



    print('conncected vertices')
    print(len(connected_vertices))



    remaining_vertices = all_vertices- connected_vertices - non_vertex_cover_indices


    # Initialize a list to store edges that exclusively connect non-vertex-cover vertices
    remaining_edges = []

    for edge in all_edges:
        # Check if either vertex in the edge is in non_vertex_cover_indices
        if edge[0] in remaining_vertices and edge[1] in remaining_vertices:
            remaining_edges.append(edge)

    print('remaining vertices')
    print(remaining_vertices)
    print(len(remaining_vertices))

    print('remaining edges')
    print(remaining_edges)

    another_vertexcover = heuristic_vertex_cover(remaining_vertices, remaining_edges)

    fogottenvertex= remaining_vertices-another_vertexcover
    # Map the vertex cover indices to the actual handle names
    forgotton_vertex_cover_handles = [handles[i] for i in fogottenvertex]

    print('forgotton handles')
    print(forgotton_vertex_cover_handles)




    print(len( another_vertexcover))



            # Map the non-vertex cover indices to the actual handle names
    non_vertex_cover_handles = [handles[i] for i in non_vertex_cover_indices]


    allnewhandles = non_vertex_cover_handles + forgotton_vertex_cover_handles
    print(len(allnewhandles))
    # Print the handles that are not part of the vertex cover
    print("Non-Vertex Cover (Handles):", non_vertex_cover_handles)
    # Step 2: Access energy values for non-vertex cover handles from handle_energy_dict
    non_vertex_cover_energy_dict = {handle: handle_energy_dict[handle] for handle in non_vertex_cover_handles}

    # Step 3: Save the non-vertex cover energy dictionary to a new pickle file
    with open('non_vertex_cover_energy_dict.pkl', 'wb') as f:
        pickle.dump(non_vertex_cover_energy_dict, f)

    print(f"Non-vertex cover energy dictionary saved with {len(non_vertex_cover_energy_dict)} handles.")



    # Print the actual handles corresponding to the vertex cover
    print("Minimum Vertex Cover (Handles):", vertex_cover_handles)