from sequence_computations import *
import pickle
import matplotlib.pyplot as plt


if __name__ == "__main__":
# run test to see if the functions above work
# open current handles and compute their energies
    with open(os.path.join('.', 'core_32_sequences.pkl'), 'rb') as f:
        antihandles, handles = pickle.load(f)


    handle_energies = compute_matching_energies(handles)

    handle_energy_dict = {}  # Dictionary to store sequences and corresponding energy values

    for i, seq in enumerate(handles):
        handle_energy_dict[seq] = handle_energies[i]

       # Save the dictionary to a pickle file
    with open('handle_energy_dict.pkl', 'wb') as f:
        pickle.dump(handle_energy_dict, f)

    # Load the sequence-energy dictionary from the pickle file
    with open('sequence_energy_dict.pkl', 'rb') as f:
        sequence_energy_dict = pickle.load(f)

    # Extract the energy values into a NumPy array
    all_energy_vals = np.array(list(sequence_energy_dict.values()))

    mean_handle = np.mean(handle_energies)
    std_handle = np.std(handle_energies)
    max_handle = max(handle_energies)
    max_ontarget_energy = max_handle  # note that the energies are negative so the maximum energy is the weakes allowed on target binders
    max_energy_factor = 6
    min_ontarget_energy = mean_handle - max_energy_factor * std_handle



    # Generate random indices for the x-axis
    all_indices = range(len(all_energy_vals))
    handle_indices = [i - 6*len(handles) for i in range(len(handles))]
    # Create a scatter plot
    plt.figure(figsize=(15, 6))

    plt.axhline(y=max_ontarget_energy-1, color='black', linestyle='-', label='max allowed binding energy')
    plt.axhline(y=-13, color='black', linestyle='-', label='min allowed binding energy')
    plt.scatter(all_indices, all_energy_vals, s= 1.3, c='b',label='off-target' )
    plt.scatter(handle_indices, handle_energies, s= 4.3, c='r', label='on-targe')
    plt.legend()
    plt.xlabel('arbitrary index')
    plt.ylabel('Gibbs free energy (kcal/mol)')
    plt.title('On-target Gibbs free energy distribution')
    plt.savefig('./All_energies.pdf')
    plt.show()


    cross_corr_handle_dict= selfvalidate(handles,Report_energies=True)
    all_cross_energies = cross_corr_handle_dict['all_energies']
    all_cross_energies = all_cross_energies[all_cross_energies != 0]

    all_cross_indices = range(len(all_cross_energies))
    mean_cross= np.mean(all_cross_energies)
    std_cross= np.std(all_cross_energies)
    # the offfactor is just used for defining the cutoff here for visualization. Wont have any effect on other parts of the cod
    offfactor = 2.5
    min_extreme_offtarget = mean_cross- offfactor*std_cross
    min_mean_offtarget = mean_cross
    #plot these in the plot

    stat_dict = {}

    stat_dict['mean_off']= mean_cross
    stat_dict['std_off']= std_cross
    stat_dict['mean_on']= mean_handle
    stat_dict['std_on']= std_handle
    stat_dict['max_on']=max_handle




    #criteria_dict = {}

    #criteria_dict['min_extreme_offtarget'] = min_extreme_offtarget
    #criteria_dict['min_mean_offtarget'] = min_mean_offtarget
    #criteria_dict['min_ontarget'] = min_ontarget_energy
    #criteria_dict['max_ontarget'] = max_handle

    # Save the dictionary to a pickle file
    with open('stat_dict.pkl', 'wb') as f:
        pickle.dump(stat_dict, f)



    plt.scatter(all_cross_indices, all_cross_energies, s=1.3, c='b', label='off-target binding energies')
    plt.axhline(y=max_ontarget_energy-1, color='black', linestyle='-', label='cutoff on-target binding energy')
    #plt.axhline(y=-13, color='g', linestyle='-', label='cutoff off-target binding energy')
    plt.axhline(y=min_mean_offtarget, color='y', linestyle='-', label=' cutoff mean off-target binding energy')
    plt.scatter(handle_indices, handle_energies, s= 4.3, c='r', label='on-target binding energies')
    plt.legend()
    plt.xlabel('arbitrary index')
    plt.ylabel('Gibbs free energy (kcal/mol)')
    plt.title('off-targe vs on-target Gibbs free energy ')
    plt.savefig('./All_offtarget_energies.pdf')
    plt.show()
