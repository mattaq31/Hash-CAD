from crisscross.assembly_handle_optimization.torch_dqn_prototyping.dqn_optimization_v2 import HDQN, read_value_cache, calculate_array_metrics
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from collections import defaultdict
import os
import numpy as np

import torch
from tqdm import tqdm

from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.assembly_handle_optimization import generate_random_slat_handles


if __name__ == '__main__':
    random.seed(8)
    torch.manual_seed(8)
    np.random.seed(8)

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    hash_vault = '/Users/matt/Desktop/hash_vault.csv'
    load_file = '/Users/matt/Desktop/hdqn_checkpoint_1732839880929743000.pth'


    if os.path.isfile(hash_vault):
        value_cache = read_value_cache(hash_vault)
    else:
        value_cache = defaultdict(dict)

    slat_length = 8
    unique_sequences = 8
    max_steps = 10
    slat_array, unique_slats_per_layer = generate_standard_square_slats(slat_length)  # standard square

    initial_handle_array = generate_random_slat_handles(slat_array, unique_sequences)


    num_unique_handles = 8
    grid_max_id = slat_array.shape[0] * slat_array.shape[1]

    policy_net = HDQN(8, unique_sequences, grid_size=slat_array.shape[:-1], num_unique_handles=num_unique_handles).to(device)
    state_dict = torch.load(load_file)
    policy_net.load_state_dict(state_dict['policy_net'])

    s_hamming, s_phys_score, _ = calculate_array_metrics(slat_array, initial_handle_array, value_cache, slat_length=slat_length)
    state = torch.tensor(initial_handle_array.transpose(2, 0, 1), dtype=torch.float32, device=device).unsqueeze(0)

    hamming_tracker = []
    phys_tracker = []

    for step in tqdm(range(max_steps), total=max_steps, desc='Training Progress'):

        # state = torch.tensor(generate_random_slat_handles(slat_array, unique_sequences).transpose(2, 0, 1), dtype=torch.float32, device=device).unsqueeze(0)
        # sample = random.random()
        with torch.no_grad():
            model_selection = policy_net(state / unique_sequences - 0.5)

        action_index = model_selection.argmax().item()
        print(action_index)
        new_value = (action_index % num_unique_handles) + 1
        new_value = torch.tensor(new_value, dtype=state.dtype, device=device)

        new_position_x = (action_index // num_unique_handles) % slat_array.shape[1]
        new_position_y = (action_index // num_unique_handles) // slat_array.shape[1]

        state[0,  0, new_position_y, new_position_x] = new_value

        n_hamming, n_phys_score, _ = calculate_array_metrics(slat_array, state[0].cpu().numpy().transpose(1, 2, 0), value_cache, slat_length=slat_length)

        phys_tracker.append(n_phys_score)
        hamming_tracker.append(n_hamming)

        fig, ax = plt.subplots(2, 1, figsize=(10, 10))
        for ind, (name, data) in enumerate(zip(['Hamming Distance',
                                                'Corresponding Physics-Based Partition Score'],
                                               [hamming_tracker, phys_tracker])):
            ax[ind].plot(data, linestyle='--', marker='o')
            ax[ind].set_xlabel('Iteration')
            ax[ind].set_ylabel('Measurement')
            ax[ind].set_title(name)
            ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        plt.tight_layout()
        plt.show()
        plt.close(fig)

