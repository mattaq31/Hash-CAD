from crisscross.plate_mapping.plate_constants import cargo_plate_folder, simpsons_mixplate_antihandles_maxed
from crisscross.plate_mapping import get_plateclass
from crisscross.core_functions.plate_handling import export_standardized_plate_sheet


src_010 = get_plateclass('HashCadPlate', simpsons_mixplate_antihandles_maxed, cargo_plate_folder)
plate_df = src_010.plates[0]

for index, entry in plate_df.iterrows():
    if isinstance(entry['name'], str) and not isinstance(entry['description'], str):
        n_split = entry['name'].split('-')
        # assign directly into the DataFrame so the change persists
        plate_df.at[index, 'description'] = f'{n_split[0]} Handle For Slat Position {n_split[-1].split("_")[-1]}, Side {n_split[2]}, Cargo ID {n_split[1]}'

export_standardized_plate_sheet(plate_df, '/Users/matt/Desktop', 'new_src010.xlsx', plate_size=384)
