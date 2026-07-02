"""
Extends P3518_MA_octahedron_patterning_v1 with two new cargo handles (antiOcta1, antiOcta2)
placed in rows I and J.  antiOcta1 mirrors antiBart positions, antiOcta2 mirrors antiEdna positions.
"""
import os

import pandas as pd

from crisscross.core_functions.plate_handling import read_dna_plate_mapping, export_standardized_plate_sheet
from crisscross.plate_mapping.plate_constants import (cargo_plate_folder, octahedron_patterning_v1,
                                                      slat_core, flat_staple_plate_folder)

########################################
# CONFIGURATION
########################################

# New cargo handle sequences (5'→3', lowercase tt linker included)
ANTI_OCTA1_HANDLE = 'ttACGGTTAT'  # mirrors antiBart positions
ANTI_OCTA2_HANDLE = 'ttATAACCGT'  # mirrors antiEdna positions

# Mapping: source cargo → new cargo name
CARGO_MAPPING = {
    'antiBart': 'antiOcta1',
    'antiEdna': 'antiOcta2',
}

# New handle sequences keyed by the new cargo name
NEW_HANDLES = {
    'antiOcta1': ANTI_OCTA1_HANDLE,
    'antiOcta2': ANTI_OCTA2_HANDLE,
}

# Target rows for new sequences
TARGET_ROWS = {
    'antiOcta1': 'I',
    'antiOcta2': 'J',
}

# Output location
OUTPUT_FOLDER = '/Users/matt/Desktop'
OUTPUT_FILENAME = 'P3518_MA_octahedron_patterning_v2_with_octa_handles.xlsx'

CONCENTRATION_UM = 500.0

########################################
# READ EXISTING PLATE AND CORE SEQUENCES
########################################

plate_path = os.path.join(cargo_plate_folder, octahedron_patterning_v1 + '.xlsx')
plate_df = read_dna_plate_mapping(plate_path, data_type='#-CAD')

# H5 core sequences from the flat staple plate
core_path = os.path.join(flat_staple_plate_folder, slat_core + '.xlsx')
core_df = read_dna_plate_mapping(core_path, data_type='#-CAD')

########################################
# BUILD NEW ENTRIES
########################################

new_rows = []

for source_cargo, new_cargo in CARGO_MAPPING.items():
    target_row = TARGET_ROWS[new_cargo]
    handle_seq = NEW_HANDLES[new_cargo]

    # Find all entries from the source cargo, sorted by numeric well column
    source_entries = plate_df[plate_df['name'].str.contains(source_cargo, na=False)].copy()
    source_entries['_well_num'] = source_entries['well'].str[1:].astype(int)
    source_entries = source_entries.sort_values('_well_num').reset_index(drop=True)

    for col_idx, (_, entry) in enumerate(source_entries.iterrows(), start=1):
        # Extract slat position from the source name (e.g. CARGO-antiBart-h2-position_2 → 2)
        name_parts = entry['name'].split('-')
        position = name_parts[3]  # e.g. 'position_2'
        pos_num = position.split('_')[1]

        # Get the H5 core sequence for this slat position
        h5_core = core_df[core_df['name'] == f'FLAT-BLANK-h5-position_{pos_num}']
        core_seq = h5_core.iloc[0]['sequence']

        new_sequence = core_seq + handle_seq
        new_name = f'CARGO-{new_cargo}-h5-{position}'
        new_description = (f'Cargo Handle For Slat Position {pos_num}, '
                           f'Side h5, Cargo ID {new_cargo}')
        new_well = f'{target_row}{col_idx}'

        new_rows.append({
            'well': new_well,
            'name': new_name,
            'sequence': new_sequence,
            'description': new_description,
            'concentration': CONCENTRATION_UM,
        })

new_entries_df = pd.DataFrame(new_rows)

########################################
# MERGE AND EXPORT
########################################

# Replace the empty rows I and J in the existing plate with the new entries
extended_df = plate_df.copy()
extended_df = extended_df[~extended_df['well'].str.startswith(('I', 'J'))].copy()
extended_df = pd.concat([extended_df, new_entries_df], ignore_index=True)

# Re-insert empty wells for remaining positions in rows I and J (columns 11-24)
all_wells_used = set(extended_df['well'].tolist())
empty_wells = []
for row_letter in ['I', 'J']:
    for col_num in range(1, 25):
        well = f'{row_letter}{col_num}'
        if well not in all_wells_used:
            empty_wells.append({
                'well': well, 'name': None, 'sequence': None,
                'description': None, 'concentration': None
            })

if empty_wells:
    extended_df = pd.concat([extended_df, pd.DataFrame(empty_wells)], ignore_index=True)

# Sort by well for proper plate ordering
well_order = [f'{letter}{num}' for letter in 'ABCDEFGHIJKLMNOP' for num in range(1, 25)]
extended_df['well_sort'] = extended_df['well'].map(lambda w: well_order.index(w) if w in well_order else 999)
extended_df = extended_df.sort_values('well_sort').drop(columns='well_sort').reset_index(drop=True)

# Export using the standardized plate sheet function
export_standardized_plate_sheet(extended_df, OUTPUT_FOLDER, OUTPUT_FILENAME)

print(f'Extended plate saved to: {os.path.join(OUTPUT_FOLDER, OUTPUT_FILENAME)}')
print(f'Added {len(new_entries_df)} new entries:')
for cargo in ['antiOcta1', 'antiOcta2']:
    count = len(new_entries_df[new_entries_df['name'].str.contains(cargo, na=False)])
    print(f'  {cargo}: {count} sequences in row {TARGET_ROWS[cargo]}')
