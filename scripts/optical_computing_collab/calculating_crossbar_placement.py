import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle


# base square megastructure, with 14nm spacing between slat handles
base_array = np.zeros((32, 32, 2))
dim = 14
for i in range(32):
    for j in range(32):
        base_array[i, j, 0] = j*dim
        base_array[i, j, 1] = i*dim


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


# either just one or two crossbars
start_point = base_array[2, 21, :]
start_point_2 = base_array[4, 29, :]
angle = -37  # best angle found from earlier testing

fig, ax = plt.subplots(figsize=(10, 10))  # base array
for i in range(32):
    for j in range(32):
        plt.scatter(base_array[i, j, 0], base_array[i, j, 1], c='b', zorder=1, s=0.1)

total_accepted, cb_colours, crossbar, accepted_distances = full_angle_compute(angle, start_point, threshold=1.0, dim=14.0)
total_accepted_2, cb_colours_2, crossbar_2, _ = full_angle_compute(angle, start_point_2, threshold=1.0, dim=14.0)

print('Accepted distances:', accepted_distances)

plt.scatter(crossbar[:, 0], crossbar[:, 1], c=cb_colours, zorder=10)
plt.scatter(crossbar_2[:, 0], crossbar_2[:, 1], c=cb_colours_2, zorder=10)
ax.invert_yaxis()
red_patch = mpatches.Patch(color='red', label='Non-matching handles')
blue_patch = mpatches.Patch(color='purple', label='Matching handles (1nm tolerance)')

ax.add_patch(Rectangle((0, 0), 5*dim, 16*dim, facecolor="yellow", edgecolor="black", linewidth=1))
ax.text(5*(dim/2), 16*(dim/2), "SEED", ha="center", va="center", rotation=90, fontsize=38)

plt.xlabel('Distance (nm)')
plt.ylabel('Distance (nm)')
plt.legend(handles=[red_patch, blue_patch])
plt.tight_layout()
plt.savefig('/Users/matt/Desktop/crossbar_plot.png', dpi=300)
plt.show()

fig, ax = plt.subplots(figsize=(10, 10))
all_data = []
angles = []
start_point = base_array[2, 10, :]
for angle in np.arange(10, 80, 0.5):
    all_data.append(full_angle_compute(angle, start_point)[0])
    angles.append(angle)
plt.scatter(angles, all_data)
plt.xlabel('Crossbar Angle (degrees)')
plt.ylabel('Number of handle matches, with a tolerance of 1nm')
plt.tight_layout()
plt.savefig('/Users/matt/Desktop/angle_check.png', dpi=300)
plt.show()
print('best angle:', angles[all_data.index(max(all_data))])




