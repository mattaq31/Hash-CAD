if __name__ == '__main__':

    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure
    import os

    # JUST A TESTING AREA
    folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/double_barrels/design_library/zigzag_ribbon/designs/'
    files = ['DB-90 Simple Ribbon 2-58.xlsx', 'DB-90 Simple Ribbon 2-58 and 30-58.xlsx']

    for file in files:
        full_file = os.path.join(folder, file)
        megastructure = Megastructure(import_design_file=full_file)
        print('Original Results:')
        print(megastructure.get_parasitic_interactions())
        evolve_manager =  EvolveManager(megastructure, unique_handle_sequences=64,
                                        early_max_valency_stop=0, evolution_population=50,
                                        generational_survivors=3,
                                        mutation_rate=1,
                                        process_count=4,
                                        evolution_generations=3000,
                                        split_sequence_handles=False,
                                        progress_bar_update_iterations=10,
                                        update_scope='all',
                                        log_tracking_directory=folder + file.replace('.xlsx', ' evolution'))
        evolve_manager.run_full_experiment(logging_interval=5)
        megastructure.clear_all_assembly_handles()
        megastructure.assign_assembly_handles(evolve_manager.handle_array)
        megastructure.export_design(file.replace('.xlsx', '-optim.xlsx'), folder)

        print('New Results:')
        print(megastructure.get_parasitic_interactions())
