import pandas as pd


from core_functions.plate_handling import generate_new_plate_from_slat_handle_df


data_df = pd.read_pickle("D:\Wyss_experiments\Echo_survery\low_wells.pkl").reset_index()


for plate_name in data_df['Plate'].unique():


    # some examples for creating the three needed columns for IDT: 'Name', 'Sequence', 'Description'
    plate_subset = data_df[data_df['Plate'] == plate_name].copy()
    plate_subset['Description'] = (
        "Refill for plate " + plate_name + ", well " + plate_subset['Well'].astype(str)
    )
    plate_subset['Sequence'] = 'N/A'
    plate_subset['Name'] = plate_subset['Well'].astype(str) + '_refill'


    # This function will automatically convert your df into a 96-well plate format and export it as an Excel file, ready for IDT
    # If you set a Name as 'SKIP', it will skip that well in the output (this way you can manually create gaps between wells)
    # furthermore, if you set restart_row_by_column to a column name, it will restart the row count when that column value changes (so that you can skip a row when a category changes)
    generate_new_plate_from_slat_handle_df(plate_subset, 'D:\Wyss_experiments\Echo_survery', 'test_file.xlsx',
                                           restart_row_by_column=None,
                                           data_type='IDT_order', plate_size=96, plate_name='TEST_PLATE')
