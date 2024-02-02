import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle


def visualize_megastructure_handles(pattern, ax, title, alpha=0.2, xsize=32, ysize=32, slatPadding=0.25, plot_seed=False):

    for i in range(xsize):
        ax.add_patch(Rectangle((i, -slatPadding), 1 - 2 * slatPadding, ysize, color="red", alpha=alpha))

    for i in range(ysize):
        ax.add_patch(Rectangle((-slatPadding, i), xsize, 1 - 2 * slatPadding, color="red", alpha=alpha))

    posx, posy = np.where(pattern == 1)
    for i, j in zip(posx, posy):
        ax.add_patch(Circle((i+slatPadding, j+slatPadding), 0.2,  facecolor="blue", edgecolor="black", linewidth=1))

    posx, posy = np.where(pattern == 2)
    for i, j in zip(posx, posy):
        ax.add_patch(Circle((i+slatPadding, j+slatPadding), 0.2,  facecolor="green", edgecolor="black", linewidth=1))

    posx, posy = np.where(pattern == 3)
    for i, j in zip(posx, posy):
        ax.add_patch(Circle((i+slatPadding, j+slatPadding), 0.2,  facecolor="black", edgecolor="black", linewidth=1))

    if plot_seed:
        ax.add_patch(Rectangle((16-2, 16-8), 4, 16,   facecolor="yellow", edgecolor="black", linewidth=1))
        ax.text(16, 16, "SEED", ha="center", va="center", rotation=90, fontsize=38)

    ax.set_ylim(-0.5, ysize + 0.5)
    ax.set_xlim(-0.5, xsize + 0.5)
    ax.set_title(title, fontsize=24)


def two_side_plot(side_1_pattern, side_2_pattern, filename, alpha=0.2, xsize=32, ysize=32, slatPadding=0.25):
    fig, ax = plt.subplots(1, 2, figsize=(32, 16))
    ax[0].axis('off')
    ax[1].axis('off')
    visualize_megastructure_handles(side_1_pattern, ax[0], 'Top', alpha=alpha, xsize=xsize, ysize=ysize, slatPadding=slatPadding)
    visualize_megastructure_handles(side_2_pattern, ax[1], 'Bottom', alpha=alpha, xsize=xsize, ysize=ysize, slatPadding=slatPadding, plot_seed=True)
    plt.suptitle(filename.replace('_', ' '), fontsize=30)
    plt.tight_layout()
    fig.savefig('/Users/matt/Desktop/%s.png' % filename.lower(), dpi=300)
    plt.show()
    plt.close()


def generate_patterned_square_cco(pattern='2_slat_jump'):
    base = np.zeros((32, 32))
    if pattern == '2_slat_jump':
        for i in range(1, 32, 4):
            for j in range(1, 32, 4):
                base[i, j] = 1
                base[i + 1, j + 1] = 1
                base[i, j + 1] = 1
                base[i + 1, j] = 1
    elif pattern == 'diagonal_octahedron_top_corner':
        for i in range(1, 31, 6):
            for j in range(1, 31, 6):
                base[i, j] = 1
                base[i + 1, j + 1] = 1
                base[i, j + 1] = 1
                base[i + 1, j] = 1
        for i in range(4, 31, 6):
            for j in range(4, 31, 6):
                base[i, j] = 2
                base[i + 1, j + 1] = 2
                base[i, j + 1] = 2
                base[i + 1, j] = 2

    elif pattern == 'diagonal_octahedron_centred':
        for i in range(3, 31, 6):
            for j in range(3, 31, 6):
                base[i, j] = 1
                base[i + 1, j + 1] = 1
                base[i, j + 1] = 1
                base[i + 1, j] = 1
        for i in range(6, 27, 6):
            for j in range(6, 27, 6):
                base[i, j] = 2
                base[i + 1, j + 1] = 2
                base[i, j + 1] = 2
                base[i + 1, j] = 2

    elif pattern == 'biotin_patterning':
        for i in range(2, 32, 3):
            base[1, i] = 3
            base[30, i] = 3

    return base


if __name__ == '__main__':
    pattern = generate_patterned_square_cco("diagonal_octahedron_top_corner")
    two_side_plot(pattern, pattern,  'Uncentred_Octahedrons')

    pattern = generate_patterned_square_cco("diagonal_octahedron_centred")
    two_side_plot(pattern, pattern, 'Centred_Octahedrons')

    pattern = generate_patterned_square_cco("diagonal_octahedron_centred")
    pattern2 = generate_patterned_square_cco("biotin_patterning")
    two_side_plot(pattern, pattern2, 'Centred_Octahedrons_With_Biotin_Underside')


