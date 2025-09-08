import pandas as pd

design_files_to_combine = ['/Users/matt/Desktop/all_designs/commands/32_handle_hexstar_echo_commands.csv',
                           '/Users/matt/Desktop/all_designs/commands/64_handle_hexstar_echo_commands.csv',
                           '/Users/matt/Desktop/all_designs/commands/hexagon_echo_commands.csv',
                           '/Users/matt/Desktop/all_designs/commands/recycling_echo_commands.csv',
                           '/Users/matt/Desktop/all_designs/commands/bird_echo_commands.csv']
# read in each csv file, combine together and then save to a new output file
combined_csv = pd.concat([pd.read_csv(f) for f in design_files_to_combine])

combined_csv.to_csv( "/Users/matt/Desktop/all_designs/commands/all_combined.csv", index=False)
