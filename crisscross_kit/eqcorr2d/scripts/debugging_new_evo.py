
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization.hamming_compute import multirule_oneshot_hamming, \
    multirule_precise_hamming, extract_handle_dicts
from crisscross.assembly_handle_optimization import generate_random_slat_handles
from crisscross.assembly_handle_optimization.handle_evolution import EvolveManager
from crisscross.core_functions.megastructures import Megastructure
import numpy as np


# def is_1D(coords):
#     # coords is list of (x, y) tuples
#     ys = [y for y, x in coords]  # row
#     xs = [x for y, x in coords]
#
#     if len(set(xs)) == 1:  # vertical
#         return True
#     if len(set(ys)) == 1:  # horizontal
#         return True
#
#     # check if all points are collinear (same slope)
#     (x0, y0) = coords[0]
#     (x1, y1) = coords[1]
#     for (x, y) in coords[2:]:
#         if (y1 - y0) * (x - x0) != (y - y0) * (x1 - x0):
#             return False
#     return True

def extract_subarray(arr, coords):

    ys = [y for y, x in coords]  # row
    xs = [x for y, x in coords]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    # Slice out the subarray (assuming arr[y][x] indexing)
    return arr[min_y:max_y+1, min_x:max_x+1]


def axial_array_from_coords(simple_coords, arr):
    """
    Create a dense numpy array from axial coordinates.
    simple_coords: list of (row, col) from the subarray
    arr: original slat array
    s_id: the integer island ID we are extracting
    """
    # Convert to axial
    axial_coords = [oddq_to_axial(col, row) for (row, col) in simple_coords]

    # Separate q, r
    qs = [q for (q, r) in axial_coords]
    rs = [r for (q, r) in axial_coords]

    # Normalize to start at (0,0)
    min_q, max_q = min(qs), max(qs)
    min_r, max_r = min(rs), max(rs)

    width = int(max_q - min_q + 1)
    height = int(max_r - min_r + 1)

    axial_array = np.zeros((height, width), dtype=int)

    # Fill in island cells
    for (y, x), (q, r) in zip(simple_coords, axial_coords):
        print(q,r)
        axial_array[r - min_r, q - min_q] = arr[y, x]

    return axial_array, (min_q, min_r)  # also return offset for debugging

def oddq_to_axial(col, row):
    q = col
    r = row/2 - col/2
    return q, r


if __name__ == '__main__':
    # JUST A TESTING AREA
    test_slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(test_slat_array, 32)

    print('Original Results:')
    print(
        multirule_oneshot_hamming(test_slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
                                  request_substitute_risk_score=True))
    print(multirule_precise_hamming(test_slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))

    megastructure = Megastructure(import_design_file="/Users/matt/Desktop/Tiny Hexagon Optim.xlsx")
    slat_array = megastructure.generate_slat_occupancy_grid()
    handle_array = megastructure.generate_assembly_handle_grid()

    # for s_id, slat in megastructure.slats():
    #     if not slat.one_dimensional_slat:





    # unique_slats_per_layer = []
    # for i in range(slat_array.shape[2]):
    #     slat_ids = np.unique(slat_array[:, :, i])
    #     slat_ids = slat_ids[slat_ids != 0]
    #     unique_slats_per_layer.append(slat_ids)
    #
    # layer = 0
    # for s_id in unique_slats_per_layer[layer]:
    #
    #     # get coordinates of s_id in slat_array
    #     coords = list(zip(*np.where(np.isin(slat_array[...,layer], s_id))))
    #     print(s_id, is_1D(coords))
    #
    #     if not is_1D(coords):
    #         handle_island_array = extract_subarray(handle_array[..., 0], coords)
    #         slat_island_array = extract_subarray(slat_array[..., 0], coords)
    #         handle_island_array[slat_island_array != s_id] = 0
    #         simple_coords = list(zip(*np.where(np.isin(slat_island_array, s_id))))
    #         # get min coordinate
    #
    #
    #
    #         [(c[0] - 93, c[1] - 32) for c in coords]
    #
    #         axial_array, (min_q, min_r) = axial_array_from_coords(simple_coords, handle_island_array)
    #         # convert coords to axial
    #         # for (row, col) in simple_coords:
    #         #     q, r = oddr_to_axial(col, row)
    #         #
    #         # # create a new array with converted coords
    #         # axial_coords = [oddr_to_axial(col, row) for (row, col) in simple_coords]
    #
    #     else:
    #         slat_island_array = slat_array[slat_array[..., layer] == s_id, layer]
    #     if s_id == 17:
    #         break
