import math
import random
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import time

from collections import namedtuple, deque, defaultdict
from itertools import count
import os
import pandas as pd
import hashlib
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from tqdm import tqdm

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver import generate_random_slat_handles


def array_to_hash(array):
    return hashlib.sha256(array.tobytes()).hexdigest()


def calculate_array_metrics(slat_array, handle_array, value_cache, slat_length):

    array_hash = array_to_hash(handle_array)

    if array_hash in value_cache:
        return value_cache[array_hash]['Min Hamming'], value_cache[array_hash]['Log Physics Score'], True

    scores = multirule_oneshot_hamming(slat_array, handle_array,
                                       slat_length=slat_length,
                                       per_layer_check=False,
                                       report_worst_slat_combinations=False,
                                       request_substitute_risk_score=False)

    value_cache[array_hash]['Min Hamming'] = scores['Universal']
    value_cache[array_hash]['Log Physics Score'] = np.log10(-scores['Physics-Informed Partition Score']).astype(np.float32)

    return value_cache[array_hash]['Min Hamming'], value_cache[array_hash]['Log Physics Score'], False


def read_value_cache(vault_path):
    df = pd.read_csv(vault_path, dtype={"Hash": str, "Min Hamming": int,
                                        "Log Physics Score": float}, index_col='Hash')
    value_cache = df.to_dict(orient='index')
    value_cache = defaultdict(lambda: {}, value_cache)
    return value_cache


def save_value_cache(vault_path, value_cache):
    df_out = pd.DataFrame.from_dict(value_cache, orient='index')
    df_out.to_csv(vault_path, index=True, index_label='Hash')

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


def default_conv(in_channels, out_channels, kernel_size, bias=True):
    return nn.Conv2d(in_channels, out_channels, kernel_size, padding=(kernel_size//2), bias=bias)

class ConvBlock(nn.Module):
    def __init__(self, conv, n_feat, kernel_size, bias=True, bn=False, pool=False,
                 act=nn.ReLU(True), residual_bypass=False):
        super(ConvBlock, self).__init__()
        modules_body = []

        for i in range(2):
            modules_body.append(conv(n_feat, n_feat, kernel_size, bias=bias))
            if bn:
                modules_body.append(nn.BatchNorm2d(n_feat))
            if i == 0:
                modules_body.append(act)
        if pool:
            modules_body.append(nn.MaxPool2d(2))

        self.body = nn.Sequential(*modules_body)
        self.residual_bypass = residual_bypass

    def forward(self, x):
        res = self.body(x)
        if self.residual_bypass:
            res += x
        return res

class HDQN(nn.Module):

    def __init__(self, n_conv_blocks, num_conv_channels, grid_size, num_unique_handles=32):
        super(HDQN, self).__init__()

        self.head_conv = default_conv(1, num_conv_channels, 3)
        self.core_conv_layers = []
        for i in range(n_conv_blocks):
            self.core_conv_layers.append(ConvBlock(default_conv, num_conv_channels, 3, bn=True, pool=False,
                                                   residual_bypass=True))
        self.core_conv_layers = nn.Sequential(*self.core_conv_layers)

        self.fc1 = nn.Linear(grid_size[0]*grid_size[1]*num_conv_channels, grid_size[0]*grid_size[1]*num_conv_channels)
        self.fc2 = nn.Linear(grid_size[0]*grid_size[1]*num_conv_channels, int(grid_size[0]*grid_size[1]*num_conv_channels/2))
        self.fc_fin = nn.Linear(int(grid_size[0]*grid_size[1]*num_conv_channels/2), grid_size[0]*grid_size[1]*num_unique_handles)

    def forward(self, handle_array):
        x = self.core_conv_layers(self.head_conv(handle_array))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc_fin(x)

        return x


if __name__ == '__main__':
    random.seed(8)
    torch.manual_seed(8)
    np.random.seed(8)

    device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    hash_vault = '/Users/matt/Desktop/hash_vault.csv'
    if os.path.isfile(hash_vault):
        value_cache = read_value_cache(hash_vault)
    else:
        value_cache = defaultdict(dict)

    slat_length = 6
    unique_sequences = 6
    slat_array, unique_slats_per_layer = generate_standard_square_slats(slat_length)  # standard square

    # example_design = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_with_2_step_purif_oct_2024/full_design.xlsx'
    # design_df = pd.read_excel(example_design, sheet_name=None, header=None)
    # initial_handle_array = np.zeros((design_df['slat_layer_1'].shape[0], design_df['slat_layer_1'].shape[1], 1))
    # for i, key in enumerate(design_df.keys()):
    #     if 'handle_interface_' not in key:
    #         continue
    #     initial_handle_array[..., 0] = design_df[key].values

    initial_handle_array = generate_random_slat_handles(slat_array, unique_sequences)

    grid_max_id = slat_array.shape[0] * slat_array.shape[1]

    policy_net = HDQN(8, unique_sequences, grid_size=slat_array.shape[:-1], num_unique_handles=unique_sequences).to(device)
    target_net = HDQN(8, unique_sequences, grid_size=slat_array.shape[:-1], num_unique_handles=unique_sequences).to(device)
    target_net.load_state_dict(policy_net.state_dict())

    optimizer = optim.AdamW(policy_net.parameters(), lr=1e-4, amsgrad=True)
    memory = ReplayMemory(10000)

    max_steps = 2000
    eps_start = 0.9
    eps_end = 0.05
    eps_decay = 200
    target_update_rate = 0.005
    batch_size = 128
    gamma = 0.99

    state = torch.tensor(initial_handle_array.transpose(2, 0, 1), dtype=torch.float32, device=device).unsqueeze(0)
    s_hamming, s_phys_score, _ = calculate_array_metrics(slat_array, initial_handle_array, value_cache, slat_length=slat_length)

    hamming_tracker = []
    phys_tracker = []
    reward_tracker = []
    action_tracker = []
    loss_tracker = [0] * batch_size
    grad_norms = [0] * batch_size
    param_changes = [0] * batch_size
    hash_tracker = []
    num_unique_hashes = 0
    reward = 0

    initial_params = {}
    for name, param in policy_net.named_parameters():
        initial_params[name] = param.data.clone()

    for step in tqdm(range(max_steps), total=max_steps, desc='Training Progress'):
        sample = random.random()
        eps_threshold = eps_end + (eps_start - eps_end) * math.exp(-1. * step / eps_decay)
        if sample > eps_threshold:
            with torch.no_grad():
                model_selection = policy_net((state/ unique_sequences) - 0.5)
                action_index = model_selection.argmax().item()
            action_tracker.append(1)
        else:
            action_index = random.randint(0, (grid_max_id*unique_sequences)-1)
            action_tracker.append(0)

        next_state = state.clone()
        new_value = (action_index % unique_sequences) + 1
        new_value = torch.tensor(new_value, dtype=next_state.dtype, device=device)

        new_position_x = (action_index // unique_sequences) % slat_array.shape[1]
        new_position_y = (action_index // unique_sequences) // slat_array.shape[1]

        next_state[0,  0, new_position_y, new_position_x] = new_value

        n_hamming, n_phys_score, is_old = calculate_array_metrics(slat_array, next_state[0].cpu().numpy().transpose(1, 2, 0), value_cache, slat_length=slat_length)

        phys_tracker.append(n_phys_score)
        hamming_tracker.append(n_hamming)
        if not is_old:
            num_unique_hashes += 1
        hash_tracker.append(num_unique_hashes)


        if n_hamming < s_hamming:
            in_reward = -3
        elif n_hamming > s_hamming:
            in_reward = 3
        elif n_phys_score < s_phys_score:
            in_reward = 1
        elif n_phys_score == s_phys_score:
            in_reward = -0.1
        else:
            in_reward = -1
        if reward > 0 and in_reward > 0:
            reward += in_reward
        elif reward < 0 and in_reward < 0:
            reward -= in_reward
        else:
            reward = in_reward

        # print (n_phys_score, s_phys_score, n_phys_score-s_phys_score, reward)

        reward_tracker.append(reward)

        memory.push(state, torch.tensor([action_index], device=device, dtype=torch.int64), next_state, torch.tensor([reward], device=device))

        s_hamming = n_hamming
        s_phys_score = n_phys_score

        if step % 20 == 0:
            state = torch.tensor(generate_random_slat_handles(slat_array, unique_sequences).transpose(2, 0, 1), dtype=torch.float32, device=device).unsqueeze(0)
        else:
            state = next_state

        if len(memory) >= batch_size:
            transitions = memory.sample(batch_size)
            batch = Transition(*zip(*transitions))

            next_state_batch = torch.cat(batch.next_state)
            state_batch = torch.cat(batch.state)
            action_batch = torch.cat(batch.action)
            reward_batch = torch.cat(batch.reward)

            policy_net_q_values = policy_net((state_batch / unique_sequences) - 0.5)
            state_action_values = policy_net_q_values.gather(1, action_batch.unsqueeze(1))

            with torch.no_grad():
                optimal_next_actions = target_net((next_state_batch / unique_sequences) - 0.5)
                next_state_values = optimal_next_actions.max(1).values

            # Compute the expected Q values
            expected_state_action_values = (next_state_values * gamma) + reward_batch

            # Compute Huber loss
            criterion = nn.SmoothL1Loss()
            loss = criterion(state_action_values.squeeze(), expected_state_action_values)

            loss_tracker.append(loss.detach().cpu().numpy())

            # Optimize the model
            optimizer.zero_grad()
            loss.backward()

            # Compute and store total gradient norm
            total_grad_norm = 0
            for name, param in policy_net.named_parameters():
                if param.grad is not None:
                    param_grad_norm = param.grad.data.norm(2)
                    total_grad_norm += param_grad_norm.item() ** 2
            total_grad_norm = total_grad_norm ** 0.5
            grad_norms.append(total_grad_norm)

            # Compute and store parameter changes
            total_param_change = 0
            for name, param in policy_net.named_parameters():
                param_change = (param.data - initial_params[name]).norm(2)
                total_param_change += param_change.item() ** 2
            total_param_change = total_param_change ** 0.5
            param_changes.append(total_param_change)

            # In-place gradient clipping
            torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
            optimizer.step()

            if step % 20 == 0:
                fig, ax = plt.subplots(8, 1, figsize=(10, 16))
                for ind, (name, data) in enumerate(zip(['Hamming Distance',
                                                        'Corresponding Physics-Based Partition Score',
                                                        'Reward (Physics Score Delta)',
                                                        'Network Loss',
                                                        'Action Taken',
                                                        'Grad Norm',
                                                        'Param Change',
                                                        'Number of Unique Arrays'],
                                                       [hamming_tracker, phys_tracker, reward_tracker, loss_tracker,
                                                        action_tracker,
                                                        grad_norms, param_changes, hash_tracker])):
                    ax[ind].plot(data, linestyle='--', marker='o')
                    ax[ind].set_xlabel('Iteration')
                    ax[ind].set_ylabel('Measurement')
                    ax[ind].set_title(name)
                    ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

                # ax[2].set_ylim(-0.01, 0.01)
                # ax[1].set_yscale('log')
                plt.tight_layout()
                plt.show()
                plt.close(fig)

        # Soft update of the target network's weights
        # θ′ ← τ θ + (1 −τ )θ′
        target_net_state_dict = target_net.state_dict()
        policy_net_state_dict = policy_net.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key]*target_update_rate + target_net_state_dict[key]*(1-target_update_rate)
        target_net.load_state_dict(target_net_state_dict)

        save_value_cache(hash_vault, value_cache)

    full_state_dict = {'policy_net': policy_net.state_dict(), 'target_net': target_net.state_dict(),
                       'optimizer': optimizer.state_dict(), 'step': step}

    torch.save(full_state_dict, f'/Users/matt/Desktop/hdqn_checkpoint_{time.time_ns()}.pth')
