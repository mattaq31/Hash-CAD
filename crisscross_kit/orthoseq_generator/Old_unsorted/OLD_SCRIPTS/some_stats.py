

import pickle
import numpy as np
import matplotlib.pyplot as plt

# Load the sequence-energy dictionary from the pickle file
with open('../sequence_energy_dict.pkl', 'rb') as f:
    sequence_energy_dict = pickle.load(f)

# Define the cutoff range
cutoff_low = -10.4
cutoff_high = -9.6

# Extract the energy values into a NumPy array
all_energy_vals = np.array(list(sequence_energy_dict.values()))

# Compute the mean and standard deviation
mean_energy = np.mean(all_energy_vals)
std_dev_energy = np.std(all_energy_vals)
print(f"Standard deviation of energy: {std_dev_energy}")
print(f"Mean energy: {mean_energy}")

# Plot the histogram of all energy values (Full Range)
plt.figure(figsize=(12, 6))
plt.hist(all_energy_vals, bins=np.arange(-15.5, -6.7, 0.12), edgecolor='black', alpha=0.7)
plt.xlabel('Binding Energy (kcal/mol)')
plt.ylabel('Frequency (#)')
plt.title('Histogram of All On-Target Energies')

# Add vertical lines for the cutoff range
plt.axvline(cutoff_low, color='black', linestyle='dashed', linewidth=3.5, label='Cutoff')
plt.axvline(cutoff_high, color='black', linestyle='dashed', linewidth=3.5)
plt.legend()

# Set the same x and y axis limits as for the filtered plot
plt.xlim(-15.5, -6.7)  # Ensures the x-axis is the same for both plots
plt.ylim(0, 350)   # Adjusts y-axis based on your data

# Save the full range plot
plt.savefig('allenergies_with_cutoff_range.pdf', format="pdf", dpi=600)
plt.show()

# Filter the energy values within the cutoff range
filtered_energy_vals = all_energy_vals[(all_energy_vals >= cutoff_low) & (all_energy_vals <= cutoff_high)]

# Plot the histogram of the filtered energy values (Cutoff Range)
plt.figure(figsize=(12, 6))
plt.hist(filtered_energy_vals, bins=np.arange(-15.5, -6.7, 0.12), edgecolor='black', alpha=0.7)
plt.xlabel('Binding Energy (kcal/mol)')
plt.ylabel('Frequency (#)')
plt.title('Histogram of On-Target Energies within Cutoff Range')

# Add vertical lines for the cutoff range
plt.axvline(cutoff_low, color='black', linestyle='dashed', linewidth=3.5, label='Cutoff')
plt.axvline(cutoff_high, color='black', linestyle='dashed', linewidth=3.5)
plt.legend()

# Set the same x and y axis limits as for the full range plot
plt.xlim(-15.5, -6.7)
plt.ylim(0, 350)

# Save the filtered range plot
plt.savefig('filtered_energies_cutoff_range.pdf', format="pdf", dpi=600)
plt.show()









import numpy as np
import matplotlib.pyplot as plt
import pickle

# Load the crossdick dictionary
with open('../TT_no_crosscheck96to104cross.pkl', 'rb') as f:
    crossdick = pickle.load(f)

# Extract the 2D arrays and flatten, removing zeros
hh = np.array(crossdick['handle_handle_energies']).flatten()
hah = np.array(crossdick['antihandle_handle_energies']).flatten()
ahah = np.array(crossdick['antihandle_antihandle_energies']).flatten()

# Remove zeros from each array
hh = hh[hh != 0]
hah = hah[hah != 0]
ahah = ahah[ahah != 0]

# Calculate mean and standard deviation for each dataset
mean_hh, std_hh = np.mean(hh), np.std(hh)
mean_hah, std_hah = np.mean(hah), np.std(hah)
mean_ahah, std_ahah = np.mean(ahah), np.std(ahah)

# Plot histograms for each dataset
plt.figure(figsize=(12, 8))

# Histogram for hh
plt.subplot(3, 1, 1)
plt.hist(hh, bins=60, edgecolor='black', alpha=0.7)
plt.axvline(mean_hh, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_hh:.2f}')
plt.axvline(mean_hh + std_hh, color='blue', linestyle='dashed', linewidth=1, label=f'+1 SD: {mean_hh + std_hh:.2f}')
plt.axvline(mean_hh - std_hh, color='blue', linestyle='dashed', linewidth=1, label=f'-1 SD: {mean_hh - std_hh:.2f}')
plt.title('Histogram of Handle-Handle Energies (hh)')
plt.xlabel('Energy Values')
plt.ylabel('Frequency')
plt.legend()

# Histogram for hah
plt.subplot(3, 1, 2)
plt.hist(hah, bins=60, edgecolor='black', alpha=0.7)
plt.axvline(mean_hah, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_hah:.2f}')
plt.axvline(mean_hah + std_hah, color='blue', linestyle='dashed', linewidth=1, label=f'+1 SD: {mean_hah + std_hah:.2f}')
plt.axvline(mean_hah - std_hah, color='blue', linestyle='dashed', linewidth=1, label=f'-1 SD: {mean_hah - std_hah:.2f}')
plt.title('Histogram of AntiHandle-Handle Energies (hah)')
plt.xlabel('Energy Values')
plt.ylabel('Frequency')
plt.legend()

# Histogram for ahah
plt.subplot(3, 1, 3)
plt.hist(ahah, bins=60, edgecolor='black', alpha=0.7)
plt.axvline(mean_ahah, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_ahah:.2f}')
plt.axvline(mean_ahah + std_ahah, color='blue', linestyle='dashed', linewidth=1, label=f'+1 SD: {mean_ahah + std_ahah:.2f}')
plt.axvline(mean_ahah - std_ahah, color='blue', linestyle='dashed', linewidth=1, label=f'-1 SD: {mean_ahah - std_ahah:.2f}')
plt.title('Histogram of AntiHandle-AntiHandle Energies (ahah)')
plt.xlabel('Energy Values')
plt.ylabel('Frequency')
plt.legend()

plt.tight_layout()
plt.show()

# Combine all data into a single dataset
all_data = np.concatenate([hh, hah, ahah])

# Calculate mean and standard deviation for the combined dataset
mean_all, std_all = np.mean(all_data), np.std(all_data)
# Plot histogram for the combined data
plt.figure(figsize=(8, 6))
plt.hist(all_data, bins=30, edgecolor='black', alpha=0.7)
plt.axvline(mean_all, color='red', linestyle='dashed', linewidth=1, label=f'Mean: {mean_all:.2f}')
plt.axvline(mean_all + std_all, color='blue', linestyle='dashed', linewidth=1,
            label=f'+1 SD: {mean_all + std_all:.2f}')
plt.axvline(mean_all - std_all, color='blue', linestyle='dashed', linewidth=1,
            label=f'-1 SD: {mean_all - std_all:.2f}')
plt.title('Combined Histogram of All Energies (hh, hah, ahah)')
plt.xlabel('Energy Values')
plt.ylabel('Frequency')
plt.legend()


plt.show()
