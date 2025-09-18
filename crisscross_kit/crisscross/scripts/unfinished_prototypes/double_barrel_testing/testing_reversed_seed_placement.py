from crisscross.core_functions.megastructures import Megastructure
from crisscross.plate_mapping import get_plateclass

megastructure = Megastructure(import_design_file='/Users/matt/Desktop/T4.xlsx')
new_plate_1 = get_plateclass('HashCadPlate', 'triple_seed_plate', '/Users/matt/Desktop')
new_plate_db = get_plateclass('HashCadPlate', 'rev_seed_plate', '/Users/matt/Desktop')

########## PATCHING PLATES
megastructure.patch_placeholder_handles([new_plate_1, new_plate_db])

