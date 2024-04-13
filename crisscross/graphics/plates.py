import well_plate
import pandas as pd


# TODO: incomplete, does not work with boolean only values
def basic_plate_view(df, plate_size=384):

    wp = well_plate.WellPlate(plate_size, "rect")
    wp.data_dict['Z8'] = {'sequence': 0}
    wp.add_data(df['sequence'].astype('bool').astype('int'))
    wp.add_data(pd.Series(0, index=['Z8']))
    wp.plot(key='sequence')
