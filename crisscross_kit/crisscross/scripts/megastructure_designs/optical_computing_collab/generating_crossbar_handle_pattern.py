import numpy as np

def find_multiple(dim, target):
    n = target + (dim/2)
    closest_multiple = n - (n % dim)

    return closest_multiple

def find_distance(dim, target, maxval, minval=0.0):
    """
    Finds the closest distance to a multiple of the specified dimension.
    """
    n = target + (dim/2)
    closest_multiple = n - (n % dim)
    if closest_multiple > maxval:
        return np.abs(maxval-target)
    if closest_multiple < minval:
        return np.abs(minval-target)
    return np.abs(closest_multiple-target)


def full_angle_compute(angle, sp, threshold=1.0, dim=14.0):
    """
    Given a crossbar angle and starting point,
    computes the number of matches with the base crisscross handles.
    """
    cb = np.zeros((32, 2))
    total_close = 0
    crossbar_markers = []
    exact_distances = []
    for i in range(32):
        cb[i, 0] = sp[0] + (i * dim) * np.sin(np.deg2rad(angle))
        cb[i, 1] = sp[1] + (i * dim) * np.cos(np.deg2rad(angle))
        dist_1 = find_distance(dim, cb[i, 0], np.max(base_array))
        dist_2 = find_distance(dim, cb[i, 1], np.max(base_array))
        direct_distance = np.sqrt(dist_1**2 + dist_2**2)
        if direct_distance < threshold:
            total_close += 1
            crossbar_markers.append('purple')
            exact_distances.append(direct_distance)
        else:
            crossbar_markers.append('red')
    return total_close, crossbar_markers, cb, exact_distances

# base square megastructure, with 14nm spacing between slat handles
base_array = np.zeros((32, 32, 2))
dim = 14
for i in range(32):
    for j in range(32):
        base_array[i, j, 0] = j*dim
        base_array[i, j, 1] = i*dim

# either just one or two crossbars
start_point = base_array[2, 21, :]
start_point_2 = base_array[4, 29, :]
angle = -37  # best angle found from earlier testing

total_accepted, cb_colours, crossbar, accepted_distances = full_angle_compute(angle, start_point, threshold=1.0, dim=14.0)
total_accepted_2, cb_colours_2, crossbar_2, _ = full_angle_compute(angle, start_point_2, threshold=1.0, dim=14.0)

accepted_markers = []
for i, colour in enumerate(cb_colours):
    if colour == 'purple':
        y = find_multiple(dim, crossbar[i, 1])/dim
        x = find_multiple(dim, crossbar[i, 0])/dim
        accepted_markers.append([x, y])
print(accepted_markers)

accepted_markers_2 = []
for i, colour in enumerate(cb_colours_2):
    if colour == 'purple':
        y = find_multiple(dim, crossbar_2[i, 1])/dim
        x = find_multiple(dim, crossbar_2[i, 0])/dim
        accepted_markers_2.append([x, y])
print(accepted_markers_2)
