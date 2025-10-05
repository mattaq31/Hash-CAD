from crisscross.core_functions.slat_design import generate_standard_square_slats
from crisscross.slat_handle_match_evolver.tubular_slat_match_compute import multirule_oneshot_hamming, \
    multirule_precise_hamming
from crisscross.slat_handle_match_evolver import generate_random_slat_handles
from crisscross.core_functions.megastructures import Megastructure
import numpy as np
import time

if __name__ == '__main__':
    # JUST A TESTING AREA
    test_slat_array, unique_slats_per_layer = generate_standard_square_slats(32)  # standard square
    handle_array = generate_random_slat_handles(test_slat_array, 32)

    # print('Original Results:')
    # print(
    #     multirule_oneshot_hamming(test_slat_array, handle_array, per_layer_check=True, report_worst_slat_combinations=False,
    #                               request_substitute_risk_score=True))
    # print(multirule_precise_hamming(test_slat_array, handle_array, per_layer_check=True, request_substitute_risk_score=True))

    # megastructure = Megastructure(slat_array=test_slat_array)
    # megastructure.assign_assembly_handles(handle_array)
    # print(megastructure.get_match_strength_score())

    # megastructure = Megastructure(import_design_file="/Users/matt/Desktop/Tiny Hexagon Optim.xlsx")
    # megastructure = Megastructure(import_design_file="/Users/matt/Desktop/TEST_90.xlsx")
    # megastructure = Megastructure(
    #     import_design_file="/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/YXZ006_Nelson_Quimby_Mats/allantiEdna.xlsx")

    megastructure = Megastructure(
        import_design_file="/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/hash_cad_validation_designs/bird/bird_design_hashcad_seed.xlsx")

    print('------')
    t1 = time.time()
    print(
        multirule_oneshot_hamming(megastructure.generate_slat_occupancy_grid(),
                                  megastructure.generate_assembly_handle_grid(),
                                  per_layer_check=True, report_worst_slat_combinations=False,
                                  request_substitute_risk_score=True))
    t2 = time.time()
    print('------')
    t3 = time.time()
    print(megastructure.get_match_strength_score())
    t4 = time.time()
    print('old time:', t2 - t1)
    print('new time:', t4 - t3)
