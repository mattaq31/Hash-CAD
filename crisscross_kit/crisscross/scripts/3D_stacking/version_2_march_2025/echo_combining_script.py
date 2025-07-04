import pandas as pd

design_files_to_combine = ['/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/PAINT/v1_both/echo_commands/sslat10_echo_base_commands.csv',
                           '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking/version_2/echo_commands/type_1_square_echo_commands.csv',
                           '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking/version_2/echo_commands/type_2_square_echo_commands.csv',
                           '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_mar_2025/echo_commands/new_columbia_pattern_2_step_purif_echo_plate_1.csv',
                           '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/optical_computers/design_mar_2025/echo_commands/new_columbia_pattern_2_step_purif_echo_plate_2.csv']
# read in each csv file, combine together and then save to a new output file
combined_csv = pd.concat([pd.read_csv(f) for f in design_files_to_combine])

combined_csv.to_csv( "/Users/matt/Desktop/combined_echo_march_11_2025.csv", index=False)
