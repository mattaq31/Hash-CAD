from crisscross.core_functions.plate_handling import read_dna_plate_mapping
from crisscross.core_functions.plate_handling import generate_new_plate_from_slat_handle_df
from crisscross.plate_mapping import get_plateclass
from crisscross.plate_mapping.plate_constants import paint_h5_handles

input_filename = '/Users/yichenzhao/Documents/Wyss/Projects/CrissCross_Output/PAINT/P3628_SSW.xls'
output_folder = '/Users/yichenzhao/PycharmProjects/Crisscross-Design/cargo_plates'

df = read_dna_plate_mapping(input_filename, data_type='IDT_order', plate_size=384)


idt_plate = generate_new_plate_from_slat_handle_df(df,output_folder, 'P3628_SSW_plate.xlsx',
                                                   data_type = '2d_excel',plate_size = 384, output_generic_cargo_plate_mapping=True)

cargo_plate = get_plateclass('GenericPlate', paint_h5_handles,output_folder)
