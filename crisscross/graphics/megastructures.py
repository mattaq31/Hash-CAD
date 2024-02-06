import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Circle

colorway = ['blue', 'green', 'black', 'purple']


# TODO: fix all the harcoding and make it more modular
def visualize_megastructure_handles(pattern, ax, title, alpha=0.2, xsize=32, ysize=32, slatPadding=0.25,
                                    plot_seed=False):
    """
    Plots out megastructure design and shows location of attachment in pre-planned pattern
    # TODO: currently only plots squares, extend to arbitrary shapes
    :param pattern: Pattern of special attachments, matching the slat array
    :param ax: Axis to plot with
    :param title: Plot title
    :param alpha: Alpha value to apply to slats
    :param xsize: Number of x-slats
    :param ysize: Number of y-slats
    :param slatPadding: Padding to use between slats (affects visualization only)
    :param plot_seed: Set to true to plot the location of the seed
    :return: N/A
    """

    # adds all slats first, all other plots will be on top
    for i in range(xsize):
        ax.add_patch(Rectangle((i, -slatPadding), 1 - 2 * slatPadding, ysize, color="red", alpha=alpha))

    for i in range(ysize):
        ax.add_patch(Rectangle((-slatPadding, i), xsize, 1 - 2 * slatPadding, color="red", alpha=alpha))

    # plots position of special handles using circles.  Colorway is pre-set.
    posx, posy = np.where(pattern > 0)
    for i, j in zip(posx, posy):
        ax.add_patch(Circle((i + slatPadding, j + slatPadding), 0.2,
                            facecolor=colorway[int(pattern[i, j]-1)], edgecolor="black", linewidth=1))

    # plots seed position as a rectangle (for now)
    if plot_seed:  # TODO: make this repositionable, also what are exact dimensions?
        ax.add_patch(Rectangle((16 - 2, 16 - 8), 5, 16, facecolor="yellow", edgecolor="black", linewidth=1))
        ax.text(16, 16, "SEED", ha="center", va="center", rotation=90, fontsize=38)

    # graph formatting
    ax.set_ylim(-0.5, ysize + 0.5)
    ax.set_xlim(-0.5, xsize + 0.5)
    ax.invert_yaxis()  # y-axis is inverted to match the way the slats and patterns are numbered
    ax.set_title(title, fontsize=24)


def one_side_plot(pattern, filename, alpha=0.2, xsize=32, ysize=32, slatPadding=0.25):
    """
    Plots megastructure top face only.
    :param pattern: Pattern of attachments to display
    :param filename: Filename to save/display
    :param alpha: Alpha value to apply to slats
    :param xsize: Number of x-slats
    :param ysize: Number of y-slats
    :param slatPadding: Padding to use between slats (affects visualization only)
    :return: N/A
    """
    fig, ax = plt.subplots(1, 1, figsize=(16, 16))
    ax.axis('off')
    visualize_megastructure_handles(pattern, ax, '', alpha=alpha, xsize=xsize, ysize=ysize, slatPadding=slatPadding)
    plt.suptitle(filename.replace('_', ' '), fontsize=30)
    plt.tight_layout()
    fig.savefig('/Users/matt/Desktop/%s.png' % filename.lower(), dpi=300)
    plt.show()
    plt.close()


def two_side_plot(side_1_pattern, side_2_pattern, filename, alpha=0.2, xsize=32, ysize=32, slatPadding=0.25):
    """
    Plots megastructure top and bottom attachments in a two-plot figure.  Seed only plotted on bottom.
    TODO: make configurable
    :param side_1_pattern: Pattern to place on top face
    :param side_2_pattern: Pattern to place on bottom face
    :param filename: Filename to save/display
    :param alpha: Alpha value to apply to slats
    :param xsize: Number of x-slats
    :param ysize: Number of y-slats
    :param slatPadding: Padding to use between slats (affects visualization only)
    :return: N/A
    """
    fig, ax = plt.subplots(1, 2, figsize=(32, 16))
    ax[0].axis('off')
    ax[1].axis('off')
    visualize_megastructure_handles(side_1_pattern, ax[0], 'Top', alpha=alpha, xsize=xsize, ysize=ysize,
                                    slatPadding=slatPadding)
    visualize_megastructure_handles(side_2_pattern, ax[1], 'Bottom', alpha=alpha, xsize=xsize, ysize=ysize,
                                    slatPadding=slatPadding, plot_seed=True)
    plt.suptitle(filename.replace('_', ' '), fontsize=30)
    plt.tight_layout()
    fig.savefig('/Users/matt/Desktop/%s.png' % filename.lower(), dpi=300)
    plt.show()
    plt.close()


def generate_patterned_square_cco(pattern='2_slat_jump'):
    """
    Pre-generates a square megastructure with specific repeatin patterns.
    :param pattern: Choose from the set of available pre-made patterns.
    :return: 2D array containing pattern
    TODO: link up with non-square systems?
    """
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


# just for testing
if __name__ == '__main__':
    pattern = generate_patterned_square_cco("diagonal_octahedron_top_corner")
    two_side_plot(pattern, pattern, 'Uncentred_Octahedrons')

    pattern = generate_patterned_square_cco("diagonal_octahedron_centred")
    two_side_plot(pattern, pattern, 'Centred_Octahedrons')

    pattern = generate_patterned_square_cco("diagonal_octahedron_centred")
    pattern2 = generate_patterned_square_cco("biotin_patterning")
    two_side_plot(pattern, pattern2, 'Centred_Octahedrons_With_Biotin_Underside')
