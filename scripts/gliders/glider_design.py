import numpy as np
from matplotlib.patches import Rectangle, Circle
import matplotlib.pyplot as plt
import pandas as pd
import os


output_folder = '/Users/matt/Desktop'
######## GRID PREPARATION
xtot = 96  # grid lines
ytot = 66
slat_nodes = 32  # there are 32 positions for one slat
slat_length = 31  # length of slat is actually nodes - 1 (gaps between nodes)
chevron_standard_slat_count = 32  # number of slats in a typical chevron segment

pattern = np.zeros((xtot, ytot))  # just a grid to display when plotting
slat_positions = np.zeros((xtot, ytot, 4))  # 4 channels for 4 layers

for i in range(0, xtot, 2):  # generates the zig-zag pattern for the grid
    for j in range(0, ytot):
        if j % 2 == 0:
            pattern[i, j] = 1
        else:
            pattern[i + 1, j] = 1

fig, ax = plt.subplots(1, 1, figsize=(12, 12))
ax.axis('off')

hyp = 1  # distance between each slat is normalized to one here, but can be any value
yd = hyp / 2  # y-distance between grid nodes (calculated with trigonometry)
xd = np.sqrt(hyp ** 2 - yd ** 2)  # x-distance between grid nodes (")
slat_id = 1  # slat id counter

# plots grid points in advance
posx, posy = np.where(pattern > 0)
for i, j in zip(posx, posy):
    ax.add_patch(Circle((j * xd, i * yd), 0.1,
                        facecolor='blue', edgecolor="black", linewidth=1))


#### LAYER 0 [bottom + seed] (Blue)
for i in range(5):
    # set y position to 26 for previous design (and x position to 32)
    ax.add_patch(Rectangle(((chevron_standard_slat_count/2)*xd, (42 + i*2) * yd), 0.5, 16-1, color="blue", angle=60))
    for j in range(16):
        slat_positions[42 + (2 * i) + j, int((chevron_standard_slat_count/2) - j), 0] = -1

for i in range(int(chevron_standard_slat_count/2)):  # if moving seed back to right side, add a -2 here to remove impeding slats (and add + 4 to all y positions)
    ax.add_patch(Rectangle((int(chevron_standard_slat_count*(3/2))*xd, ((int(chevron_standard_slat_count/2)) + i*2) * yd), 0.1, slat_length, color="blue", angle=60))
    for j in range(chevron_standard_slat_count):
        slat_positions[(int(chevron_standard_slat_count/2)) + (2 * i) + j, int(chevron_standard_slat_count*(3/2)) - j, 0] = slat_id
    slat_id += 1


#### LAYER 1 (Yellow) ####
for i in range(chevron_standard_slat_count):
    ax.add_patch(Rectangle(((chevron_standard_slat_count - i) * xd, i * yd), 0.1, slat_length, color="yellow", angle=0))
    slat_positions[i:(slat_nodes*2)+i, chevron_standard_slat_count - i, 1] = slat_id
    slat_id += 1

for i in range(chevron_standard_slat_count):
    ax.add_patch(Rectangle(((chevron_standard_slat_count + 1) * xd, ((i*2)+1) * yd), 0.1, slat_length, color="yellow", angle=-60))
    for j in range(chevron_standard_slat_count):
        slat_positions[2*i + 1 + j, chevron_standard_slat_count + 1 + j, 1] = slat_id
    slat_id += 1


#### LAYER 2 (Green) ####
for i in range(chevron_standard_slat_count):
    ax.add_patch(Rectangle((chevron_standard_slat_count*xd, (2*i)*yd), 0.1, slat_length, color="green", angle=60))
    for j in range(chevron_standard_slat_count):
        slat_positions[2 * i + j, chevron_standard_slat_count - j, 2] = slat_id
    slat_id += 1

for i in range(chevron_standard_slat_count):
    ax.add_patch(Rectangle(((chevron_standard_slat_count + 1 + i) * xd, (i+1) * yd), 0.1, slat_length, color="green", angle=0))
    slat_positions[i+1:(slat_nodes*2) + 1 + i, chevron_standard_slat_count + 1 + i, 2] = slat_id
    slat_id += 1


#### LAYER 3 (Red) ####
for i in range(int(chevron_standard_slat_count/2)+1):  # 17 total: 1 extra to complete full side
    ax.add_patch(Rectangle(((int(chevron_standard_slat_count/2)+1)*xd, ((int(chevron_standard_slat_count/2) - 1) + i*2) * yd), 0.1, slat_length, color="red", angle=-60))
    for j in range(chevron_standard_slat_count):
        slat_positions[int(chevron_standard_slat_count/2) - 1 + (2 * i) + j, int(chevron_standard_slat_count/2) + 1 + j, 3] = slat_id
    slat_id += 1

# ensures the zig-zag pattern is enforced (just in case)
slat_positions[..., 0] = slat_positions[..., 0] * pattern
slat_positions[..., 1] = slat_positions[..., 1] * pattern
slat_positions[..., 2] = slat_positions[..., 2] * pattern
slat_positions[..., 3] = slat_positions[..., 3] * pattern


######### Design plotting and export
# graph formatting
# ax.set_ylim(-0.5, ytot + 0.5)
# ax.set_xlim(-0.5, xtot/2 + 0.5)
plt.axis('equal')
ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
# plt.tight_layout()
plt.savefig(os.path.join(output_folder, 'full_glider_design.pdf'))
plt.show()
plt.close()

# Inner layer vis and slat export
visual_layer_presentation = np.zeros_like(slat_positions)

visual_layer_presentation[slat_positions > 0] = 2
visual_layer_presentation[slat_positions == -1] = 1

fig, ax = plt.subplots(2, 2, figsize=(12, 12))

ax[0, 0].imshow(visual_layer_presentation[..., 0], cmap='plasma')
ax[0, 0].set_title('Layer 0')
ax[0, 0].axis('off')
ax[0, 0].set_aspect('equal')

ax[0, 1].imshow(visual_layer_presentation[..., 1], cmap='plasma')
ax[0, 1].set_title('Layer 1')
ax[0, 1].axis('off')
ax[0, 1].set_aspect('equal')

ax[1, 0].imshow(visual_layer_presentation[..., 2], cmap='plasma')
ax[1, 0].set_title('Layer 2')
ax[1, 0].axis('off')
ax[1, 0].set_aspect('equal')

ax[1, 1].imshow(visual_layer_presentation[..., 3], cmap='plasma')
ax[1, 1].set_title('Layer 3')
ax[1, 1].axis('off')
ax[1, 1].set_aspect('equal')

plt.axis('equal')
plt.tight_layout()
plt.savefig(os.path.join(output_folder, 'full_glider_design_layers.pdf'))
plt.close()

writer = pd.ExcelWriter(os.path.join(output_folder,'layer_arrays.xlsx'), engine='xlsxwriter')

for i in range(4):
    # Convert numpy array to pandas DataFrame
    df = pd.DataFrame(slat_positions[..., i])

    # Write each DataFrame to a separate worksheet
    df.to_excel(writer, sheet_name='Layer_%s' % i, index=False, header=False)

writer.close()
