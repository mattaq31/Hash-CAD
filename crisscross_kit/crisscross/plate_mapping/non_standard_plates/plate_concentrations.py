import copy

# exact concentration of each staple in all available plates (in μM)
concentration_library = {
    # original assembly handles
    'P3247_SW': 500,
    'P3248_SW': 500,
    'P3249_SW': 500,
    'P3250_SW': 500,
    'P3251_CW': 500,
    'P3252_SW': 500,
    'P3533_SW': 500,
    'P3534_SW': 500,
    'P3535_SW': 500,
    'P3536_MA': 500,
    'P3537_MA': 500,
    'P3538_MA': 500,
    # taster set handle library v2
    'P3601_MA': 100,
    'P3602_MA': 100,
    'P3603_MA': 100,
    'P3604_MA': 100,
    'P3605_MA': 100,
    'P3606_MA': 100,
    # full handle library v2
    'P3649_MA': 500,
    'P3650_MA': 500,
    'P3651_MA': 500,
    'P3652_MA': 500,
    'P3653_MA': 500,
    'P3654_MA': 500,
    'P3655_MA': 500,
    'P3656_MA': 500,
    'P3657_MA': 500,
    'P3658_MA': 500,
    'P3659_MA': 500,
    'P3660_MA': 500,
    # source plates
    'sw_src002': 500,
    'sw_src004': 200,
    'sw_src005': 200,
    'sw_src007': 200,
    'sw_src009': 500,
    'sw_src010': 500,
    # seed plates
    'P3555_SSW': 500,
    'P3339_JL': 500,
    'P2854_CW': 500,
    'P3621_SSW': 200,
    'P3643_MA': 500,
    # other
    'P3518_MA': 200,
    'P3510_SSW': 200,
    'P3628_SSW': 200,
}

# some wells in certain plates have concentrations that differ from the rest in the plate,
# either due to a lab mistake or some other design consideration.
# This dictionary identifies said wells (it contains the multiplier that needs to be applied to match the concentration in the rest of the plate).
exception_wells = {('P3601_MA', 'N19'): 2,
                   ('P3601_MA', 'N22'): 2,
                   ('P3601_MA', 'N24'): 2}  # key is the plate/well affected, while value is the multiple that needs to be applied to the related volume


def apply_well_exceptions(complete_echo_df):
    """
    Some wells in certain plates have concentrations that differ from the rest in the plate,
    either due to a lab mistake or some other design consideration.  This function applies
    fixes to the specific wells we have identified, if found in the design.
    :param complete_echo_df: The full echo dataframe
    :return: Same echo dataframe with patches applied
    """
    fixed_df = copy.copy(complete_echo_df)

    for (plate, well), multiplier in exception_wells.items():
        fixed_df.loc[(fixed_df['Source Plate Name'] == plate) & (fixed_df['Source Well'] == well), 'Transfer Volume'] *= multiplier

    return fixed_df


