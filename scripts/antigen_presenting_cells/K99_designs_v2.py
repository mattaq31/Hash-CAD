from crisscross.core_functions.slat_design import read_design_from_excel, generate_standard_square_slats
from crisscross.graphics.megastructures import generate_patterned_square_cco
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

colorway = ['red', 'orange', 'black', 'purple']

folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_training/stella_scripts_and_data/20220927_megaplussign_2handlestagger/20220927_megacc6hb_plussign_2handlestagger_nonperiodic/'
# folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/miscellaneous_grant_docs/plus_sign_no_stagger/'

out_file = 'TEST'
patterning = True
base_array = read_design_from_excel(folder, ['slats_bottom.csv', 'slats_top.csv'])
# base_array, _ = generate_standard_square_slats(32)

x_slats = np.unique(base_array[:, :, 0])
y_slats = np.unique(base_array[:, :, 1])

dim_size = 66
xsize = 32
ysize = 32
alpha = 0.2
slatPadding = 0.2

pattern_array = np.zeros((dim_size, dim_size))
total_antigens = 196
square_side = int(np.sqrt(total_antigens))

if patterning:
    start_pos_x = int(33 - (int(square_side)/2))
    start_pos_y = int(34 - (int(square_side)/2))

    # limited random
    # mask = np.random.randint(1, 3, size=pattern_array.shape)
    # for a in range(total_antigens):
    #     xr = 1
    #     yr = 1
    #     while base_array[yr, xr, 0] == 0 or (xr ==1 and yr == 1):
    #         xr = np.random.randint(1, dim_size)
    #         yr = np.random.randint(1, dim_size)
    #     pattern_array[yr, xr] = mask[yr, xr]

    # FULLY RANDOM
    # pattern_array[np.where(base_array[:, :, 0] > 0)] = 1

    # how do I select a random subset of the array positions?

    # # random boolean mask for which values will be changed
    # mask = np.random.randint(1, 3, size=pattern_array.shape)

    # pattern_array = pattern_array * mask

    # alternating stripes of unit 1 and 2
    # for i in range(0, dim_size, 2):
    #     pattern_array[i, :] = 1
    #     pattern_array[i+1, :] = 2
    # pattern_array[np.where(base_array[:, :, 0] == 0)] = 0

    # for a in range(total_antigens):
    #     x = start_pos_x + a % square_side
    #     y = start_pos_y + a // square_side
    #     # alternating stripes within central area
    #     if (x % 2) == 0:
    #         pattern_array[y, x] = 1
    #     else:
    #         pattern_array[y, x] = 2

    # pattern_array[start_pos_y-1, start_pos_x-1:x+2] = 2
    # pattern_array[y+1, start_pos_x-1:x+2] = 2
    # pattern_array[start_pos_y-1:y+1, start_pos_x-1] = 2
    # pattern_array[start_pos_y-1:y+1, x+1] = 2

    corner_xs = [3, 63 - int(square_side/2), 32 - int(square_side/4), 32 - int(square_side/4)]
    corner_ys = [34 - int(square_side/4), 34 - int(square_side/4), 3, 63 - int(square_side/2)]

    for start_pos_x, start_pos_y in zip(corner_xs, corner_ys):
        for a in range(int(total_antigens/4)):
            x = int(start_pos_x + (a % (square_side/2)))
            y = int(start_pos_y + (a // (square_side/2)))
            # alternating stripes for each cluster
            if (x % 2) == 0:
                pattern_array[y, x] = 1
            else:
                pattern_array[y, x] = 2
            pattern_array[y, x] = 1
        pattern_array[start_pos_y-1, start_pos_x-1:x+2] = 2
        pattern_array[y+1, start_pos_x-1:x+2] = 2
        pattern_array[start_pos_y-1:y+1, start_pos_x-1] = 2
        pattern_array[start_pos_y-1:y+1, x+1] = 2

fig, ax = plt.subplots(1, 1, figsize=(16, 16))
ax.axis('off')

for xval in x_slats:
    if xval == 0:
        continue
    posns = np.where(base_array[:, :, 0] == xval)
    y1, x1 = np.min(posns[0]), np.min(posns[1])
    ax.add_patch(Rectangle((x1-slatPadding, y1), xsize, 1 - 2 * slatPadding, color="blue", alpha=alpha))

for yval in y_slats:
    if yval == 0:
        continue
    posns = np.where(base_array[:, :, 1] == yval)
    y1, x1 = np.min(posns[0]), np.min(posns[1])
    ax.add_patch(Rectangle((x1, y1-slatPadding), 1 - 2 * slatPadding, ysize, color="blue", alpha=alpha))

# plots position of special handles using circles.  Colorway is pre-set.
posx, posy = np.where(pattern_array > 0)
for i, j in zip(posx, posy):
    ax.add_patch(Circle((j + slatPadding, i + slatPadding), 0.45,
                        facecolor=colorway[int(pattern_array[i, j] - 1)], edgecolor="black", linewidth=1.5))

# graph formatting
ax.set_ylim(-0.5, dim_size + 0.5)
ax.set_xlim(-0.5, dim_size + 0.5)
ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
# ax.set_title(out_file, fontsize=24)

# fig.patch.set_facecolor('none')

plt.tight_layout()
fig.savefig('/Users/matt/Desktop/%s.png' % out_file.lower(), dpi=300)
plt.show()
