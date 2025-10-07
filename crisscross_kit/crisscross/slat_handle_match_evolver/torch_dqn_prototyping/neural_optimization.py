from collections import defaultdict

import numpy as np
from torch.utils.data import DataLoader
from tqdm import tqdm

from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import extract_handle_dicts, oneshot_hamming_compute
from crisscross.slat_handle_match_evolver.torch_dqn_prototyping.torch_hamming_compute import torch_index_handles, \
    torch_oneshot_hamming_compute
from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.slat_handle_match_evolver.torch_dqn_prototyping.handle_array_dataloader import HandleArrayDataset
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.ticker as ticker

from crisscross.helper_functions import save_list_dict_to_file


class MiniConvNet(nn.Module):
    def __init__(self, in_channels, kernel_size=3):
        super(MiniConvNet, self).__init__()
        padding = (kernel_size - 1) // 2
        self.conv = nn.Conv2d(in_channels, in_channels, kernel_size=kernel_size, padding=padding)
        self.activation = nn.ReLU()

    def forward(self, x):
        x = self.conv(x)
        x = self.activation(x)
        x = F.sigmoid(x)
        x = 31 * x + 1  # Scale to [1, 32]
        x = torch.round(x)  # Ensure discrete values

        return x


class Conv2dSame(torch.nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, bias=True, padding_layer=torch.nn.ReflectionPad2d):
        """It only support square kernels and stride=1, dilation=1, groups=1."""
        super(Conv2dSame, self).__init__()
        ka = kernel_size // 2
        kb = ka - 1 if kernel_size % 2 == 0 else ka
        self.net = nn.Sequential(
            padding_layer((ka, kb, ka, kb)),
            nn.Conv2d(in_channels, out_channels, kernel_size, bias=bias),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(True)
        )

    def forward(self, x):
        return self.net(x)


class DistanceEstimator(nn.Module):
    def __init__(self, in_channels):
        super(DistanceEstimator, self).__init__()
        # Define your CNN layers here
        self.conv_layers = nn.Sequential(
            nn.Conv2d(in_channels=in_channels, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels=16, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels=16, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(in_channels=16, out_channels=16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.fc_layers = nn.Sequential(
            nn.Linear(16 * (32 // 16) * (32 // 16), 100),
            nn.ReLU(),
            nn.Linear(100, 1)
        )

    def forward(self, x):
        x = x / 32 - 0.5
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc_layers(x)
        return x


class SudokuCNN(nn.Module):
    def __init__(self, channels):
        super(SudokuCNN, self).__init__()
        intermediate_channels = 16
        self.conv_layers = nn.Sequential(Conv2dSame(channels, intermediate_channels, 3),  # 1
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 2
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 3
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 4
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 5
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 6
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 7
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 8
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 9
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 10
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 11
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 12
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 13
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3),  # 14
                                         Conv2dSame(intermediate_channels, intermediate_channels, 3))  # 15
        self.last_conv = nn.Conv2d(intermediate_channels, channels, 1)

    def forward(self, x):
        x = self.conv_layers(x)
        x = self.last_conv(x)
        x = F.sigmoid(x)
        x = 31 * x + 1  # Scale to [1, 32]
        x = torch.round(x)  # Ensure discrete values

        return x


def hamming_network_setup_and_training(slat_array, data_folder, epochs=100, unique_sequences=32, slat_length=32):
    # NETWORK SETUP
    network = DistanceEstimator(in_channels=slat_array.shape[-1] - 1)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, network.parameters()), lr=1e-4)
    network.train()



    print('loading data....')
    dataset = HandleArrayDataset(data_folder, slat_array)
    val_dataset = HandleArrayDataset(
        '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization/val_set', slat_array,
        evo_cutoff=1000)

    train_loader = DataLoader(dataset, batch_size=10, num_workers=8, pin_memory=True,
                              shuffle=True, persistent_workers=True, multiprocessing_context="forkserver")
    val_loader = DataLoader(val_dataset, batch_size=1, num_workers=1, pin_memory=True,
                            shuffle=False, persistent_workers=True, multiprocessing_context="forkserver")
    print('data loading complete')

    loss_tracker = defaultdict(list)

    for epoch in range(1, epochs+1):
        with tqdm(total=len(train_loader) + len(val_loader), desc='Epoch %s' % epoch) as pbar:
            network.train()
            inner_train_tracker = []
            inner_val_tracker = []
            for batch in train_loader:
                input_array = batch['handle_array']
                model_score = network(input_array)
                optimizer.zero_grad()
                loss = criterion(batch['log_physics_score'], model_score.squeeze())
                inner_train_tracker.append(loss.detach().numpy())
                loss.backward()
                optimizer.step()
                pbar.update(1)
                pbar.set_postfix({f'Batch Train Loss': loss.item()})
            network.eval()
            for batch in val_loader:
                input_array = batch['handle_array']
                model_score = network(input_array)
                loss = criterion(batch['log_physics_score'].squeeze(), model_score.squeeze())
                inner_val_tracker.append(loss.detach().numpy())
                pbar.update(1)
                pbar.set_postfix({f'Batch Eval Loss': loss.item()})
        loss_tracker['train'].append(np.mean(inner_train_tracker))
        loss_tracker['eval'].append(np.mean(inner_val_tracker))

        fig, ax = plt.subplots(2, 1, figsize=(10, 10))

        for ind, (name, data) in enumerate(zip(['Train Loss',
                                                'Eval Loss'],
                                               [loss_tracker['train'],
                                                loss_tracker['eval']])):
            ax[ind].plot(data, linestyle='--', marker='o')
            ax[ind].set_xlabel('Epoch')
            ax[ind].set_ylabel('Loss Value')
            ax[ind].set_title(name)
            ax[ind].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        plt.tight_layout()
        plt.savefig('/Users/matt/Desktop/tracker.png', dpi=300)
        plt.close(fig)
        save_list_dict_to_file('/Users/matt/Desktop', 'metrics.csv',
                               loss_tracker, selected_data=epoch - 1 if epoch > 1 else None)

    return network, loss_tracker


def network_setup_and_training(slat_array, epochs=100, initial_handle_array=None, unique_sequences=32, slat_length=32):
    torch.autograd.set_detect_anomaly(True)
    # PREPARES HANDLE ARRAYS AND MASK
    if initial_handle_array is None:
        handle_array = generate_random_slat_handles(slat_array, unique_sequences)
    else:
        handle_array = initial_handle_array
    model_handle_array = torch.tensor(handle_array, dtype=torch.float32, requires_grad=True)
    slat_array_torch = torch.tensor(slat_array)
    permanent_handle_mask = torch.zeros((handle_array.shape[0], handle_array.shape[1], handle_array.shape[2]))
    permanent_handle_mask[handle_array > 0] = 1
    handle_index_list, antihandle_index_list = extract_handle_dicts(handle_array, slat_array, list_indices_only=True)

    # NETWORK SETUP
    network = SudokuCNN(channels=slat_array.shape[-1] - 1)
    # network = MiniConvNet(in_channels=slat_array.shape[-1]-1)

    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, network.parameters()), lr=1e-3)
    network.train()

    physics_tracker = []
    hamming_tracker = []

    # TRAINING LOOP
    with tqdm(total=epochs, desc='Evolution Progress', miniters=1) as pbar:
        for epoch in range(epochs):
            input_array = torch.tensor(generate_random_slat_handles(slat_array, unique_sequences), dtype=torch.float32,
                                       requires_grad=True)
            stacked_handles, stacked_antihandles = torch_index_handles(input_array, slat_array_torch, handle_index_list,
                                                                       antihandle_index_list)
            input_hamming = torch.min(torch_oneshot_hamming_compute(stacked_handles, stacked_antihandles, slat_length))
            input_array = (input_array / unique_sequences - 0.5) * permanent_handle_mask

            # model_handle_array = model_handle_array.detach()
            # model_handle_array.requires_grad = True

            model_handle_array = network(input_array.transpose(0, 2).unsqueeze(0))
            model_handle_array = model_handle_array.squeeze(dim=0).transpose(0, 2) * permanent_handle_mask
            stacked_handles, stacked_antihandles = torch_index_handles(model_handle_array, slat_array_torch,
                                                                       handle_index_list, antihandle_index_list)
            all_hammings = torch_oneshot_hamming_compute(stacked_handles, stacked_antihandles, slat_length)
            physics_score = torch.mean(torch.exp(-5 * (all_hammings - slat_length)))
            hamming_score = torch.min(all_hammings)
            optimizer.zero_grad()
            (input_hamming - hamming_score).backward()
            # if physics_score == torch.inf:  # the model will be very weak in the beginning, and should optimize hamming distance instead of physics score, which will be overflowing
            #     hamming_score.backward()
            # else:
            #     physics_score.backward()
            optimizer.step()
            pbar.update(1)
            pbar.set_postfix({f'Input Hamming score': input_hamming.detach().numpy(),
                              f'Hamming score': hamming_score.detach().numpy(),
                              'Physics Score': physics_score.detach().numpy()}, refresh=False)
            physics_tracker.append(physics_score.detach().numpy())
            hamming_tracker.append(-hamming_score.detach().numpy())

            # writer = pd.ExcelWriter(
            #     os.path.join('/Users/matt/Desktop/tst', f'handle_array_epoch_{epoch}.xlsx'), engine='xlsxwriter')
            # np_handle_array = np.array(model_handle_array.detach().numpy(), dtype=np.uint16)
            # # prints out slat dataframes in standard format
            # for layer_index in range(np_handle_array.shape[-1]):
            #     df = pd.DataFrame(np_handle_array[..., layer_index])
            #     df.to_excel(writer, sheet_name=f'handle_interface_{layer_index + 1}', index=False, header=False)
            #     # Apply conditional formatting for easy color-based identification
            #     writer.sheets[f'handle_interface_{layer_index + 1}'].conditional_format(0, 0, df.shape[0], df.shape[1] - 1,
            #                                                                             {'type': '3_color_scale',
            #                                                                              'criteria': '<>',
            #                                                                              'min_color': "#63BE7B",
            #                                                                              # Green
            #                                                                              'mid_color': "#FFEB84",
            #                                                                              # Yellow
            #                                                                              'max_color': "#F8696B",  # Red
            #                                                                              'value': 0})
            # writer.close()


if __name__ == '__main__':
    slat_array, _ = generate_standard_square_slats(32)  # standard square
    # glider_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/crisscross_code/scratch/design_testing_area/glider_test'
    # glider_file = 'layer_arrays.xlsx'
    # design_df = pd.read_excel(os.path.join(glider_folder, glider_file), sheet_name=None, header=None)
    # slat_array = np.zeros((design_df['Layer_0'].shape[0], design_df['Layer_0'].shape[1], len(design_df)))
    # for i, key in enumerate(design_df.keys()):
    #     slat_array[..., i] = design_df[key].values
    # slat_array[slat_array == -1] = 0
    base_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization/experiment_folders/comparing_random_vs_nonrandom_evolution'
    network, log_tracker = hamming_network_setup_and_training(slat_array, data_folder=base_folder, epochs=100)

    handle_array = np.array(pd.read_excel(
        '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/assembly_handle_optimization/experiment_folders/comparing_random_vs_nonrandom_evolution/optuna_params_library_sweep_with_extended_random_bug/base_square_20_handle_library/best_handle_array_generation_20.xlsx',
        sheet_name='handle_interface_1',
        header=None, engine='calamine'))

    handle_dict, antihandle_dict = extract_handle_dicts(np.expand_dims(handle_array, axis=-1), slat_array)
    real_hamming = oneshot_hamming_compute(handle_dict, antihandle_dict, 32)
    physics_score = np.average(np.exp(-10 * (real_hamming - 32)))
    log_physics_score = np.log10(physics_score).astype(np.float32)
    hamming_score = np.min(real_hamming)

    torch_score = network(torch.tensor(np.expand_dims(handle_array, axis=0), dtype=torch.float32).unsqueeze(0))
