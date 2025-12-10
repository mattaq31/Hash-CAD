To re-generate plots of Figure 6, follow the steps below:

- You will need to obtain the raw data from Zenodo.  This will contain instructions on how to export all counts from QuPath.
- You will need to create two folders: set_A and set_B.  set_A corresponds to the first grid for each sample, while set_B corresponds to the second.  Export all counts from QuPath to each folder separately (i.e. export first grid counts to set_A and second grid counts to set_B).
- Run data_prep.py to generate the required pickle files.  You will need to update the file paths to match your system.
- Run yield_per_handle_assignment.py and growth_stage_distribution.py to generate the plots.  You will also need to update the file paths to match your system.

To generate the evo run plots, first obtain the evo run data from Zenodo (e.g. square_long_fast).

Next, go to evo_run_plots/plot_evo_run.py.  You will also need to update all the filepaths to match your system.
