import numpy as np


# TODO: refactor this code to remove duplicated regions
def central_cluster(pattern_array, total_cd3_antigens, cd28='border'):

    vertical_side = 12
    if cd28 == 'border':
        horizontal_side = int(total_cd3_antigens/(vertical_side))
    else:
        cd3_stripes = int(total_cd3_antigens/(vertical_side))
        horizontal_side = cd3_stripes + (cd3_stripes - 1)

    if cd28 == 'border':
        corner_xs = [34 - int((horizontal_side+2) / 2)]
    else:
        corner_xs = [34 - int(horizontal_side / 2)]
    corner_ys = [34 - int(vertical_side / 2)]

    for start_pos_x, start_pos_y in zip(corner_xs, corner_ys):
        square_position_tracker = 0
        cd3_tally = 0
        while cd3_tally < total_cd3_antigens:
            x = int(start_pos_x + (square_position_tracker % horizontal_side))
            x_tracker = square_position_tracker % horizontal_side
            y = int(start_pos_y + (square_position_tracker // horizontal_side))
            # alternating stripes for each cluster
            if cd28 == 'border':
                pattern_array[y, x] = 1
                cd3_tally += 1
            else:
                if (x_tracker % 2) == 0:
                    pattern_array[y, x] = 1
                    cd3_tally += 1
                else:
                    pattern_array[y, x] = 2

            square_position_tracker += 1

        if cd28 == 'border':
            pattern_array[start_pos_y - 1, start_pos_x - 1:x + 2] = 2
            pattern_array[y + 1, start_pos_x - 1:x + 2] = 2
            pattern_array[start_pos_y - 1:y + 1, start_pos_x - 1] = 2
            pattern_array[start_pos_y - 1:y + 1, x + 1] = 2


def peripheral_clusters(pattern_array, total_cd3_antigens, cd28='border'):

    vertical_side = 8
    if cd28 == 'border':
        horizontal_side = int(total_cd3_antigens/(vertical_side*4))
    else:
        cd3_stripes = int(total_cd3_antigens/(vertical_side*4))
        horizontal_side = cd3_stripes + (cd3_stripes - 1)

    if cd28 == 'border':
        corner_xs = [3, 63 - horizontal_side - 2, 33 - int((horizontal_side+2)/2), 33 - int((horizontal_side+2)/2)]
    else:
        corner_xs = [3, 63 - horizontal_side, 33 - int(horizontal_side/2), 33 - int(horizontal_side/2)]
    corner_ys = [33 - int(vertical_side / 2), 33 - int(vertical_side / 2), 3, 63 - vertical_side]

    for start_pos_x, start_pos_y in zip(corner_xs, corner_ys):
        square_position_tracker = 0
        cd3_tally = 0
        while cd3_tally < int(total_cd3_antigens/4):

            x = int(start_pos_x + (square_position_tracker % horizontal_side))
            x_tracker = square_position_tracker % horizontal_side
            y = int(start_pos_y + (square_position_tracker // horizontal_side))
            # alternating stripes for each cluster
            if cd28 == 'border':
                pattern_array[y, x] = 1
                cd3_tally += 1
            else:
                if (x_tracker % 2) == 0:
                    pattern_array[y, x] = 1
                    cd3_tally += 1
                else:
                    pattern_array[y, x] = 2

            square_position_tracker += 1

        if cd28 == 'border':
            pattern_array[start_pos_y - 1, start_pos_x - 1:x + 2] = 2
            pattern_array[y + 1, start_pos_x - 1:x + 2] = 2
            pattern_array[start_pos_y - 1:y + 1, start_pos_x - 1] = 2
            pattern_array[start_pos_y - 1:y + 1, x + 1] = 2


def random_pattern(pattern_array, slat_mask, total_antigens):
    for a in range(total_antigens):
        xr = 1
        yr = 1
        while slat_mask[yr, xr, 1] == 0 or (xr == 1 and yr == 1) or pattern_array[yr, xr] != 0:
            xr = np.random.randint(1, pattern_array.shape[0])
            yr = np.random.randint(1, pattern_array.shape[1])
        pattern_array[yr, xr] = 1

        while slat_mask[yr, xr, 1] == 0 or (xr == 1 and yr == 1) or pattern_array[yr, xr] != 0:
            xr = np.random.randint(1, pattern_array.shape[0])
            yr = np.random.randint(1, pattern_array.shape[1])
        pattern_array[yr, xr] = 2


def capc_pattern_generator(pattern_requested='random', slat_mask=None, total_cd3_antigens=192, capc_length=66):

    pattern_array = np.zeros((capc_length, capc_length))
    if pattern_requested == 'peripheral_dispersed':
        peripheral_clusters(pattern_array, total_cd3_antigens, cd28='dispersed')
    elif pattern_requested == 'peripheral_bordered':
        peripheral_clusters(pattern_array, total_cd3_antigens, cd28='border')
    elif pattern_requested == 'central_bordered':
        central_cluster(pattern_array, total_cd3_antigens, cd28='border')
    elif pattern_requested == 'central_dispersed':
        central_cluster(pattern_array, total_cd3_antigens, cd28='dispersed')
    elif pattern_requested == 'random':
        if slat_mask is None:
            raise ValueError('Slat mask is required for random pattern generation')
        random_pattern(pattern_array, slat_mask, total_cd3_antigens)
    return pattern_array
