if __name__ == '__main__':

    from crisscross.slat_handle_match_evolver.handle_evolution import EvolveManager
    from crisscross.core_functions.megastructures import Megastructure
    import os

    # JUST A TESTING AREA
    folder = '/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Crisscross Designs/SW151_aarhus_rectwindow/'
    files = ['design_with_evolved_handles.xlsx']

    for file in files:
        full_file = os.path.join(folder, file)
        megastructure = Megastructure(import_design_file=full_file)
        megastructure.clear_all_assembly_handles()

        evolve_manager =  EvolveManager(megastructure, unique_handle_sequences=64,
                                        early_max_valency_stop=0, evolution_population=50,
                                        generational_survivors=3,
                                        mutation_rate=1,
                                        process_count=4,
                                        evolution_generations=1000,
                                        split_sequence_handles=False,
                                        progress_bar_update_iterations=10,
                                        update_scope='all',
                                        log_tracking_directory=folder + file.replace('.xlsx', ' evolution_continued'))
        evolve_manager.run_full_experiment(logging_interval=5)
        megastructure.clear_all_assembly_handles()
        megastructure.assign_assembly_handles(evolve_manager.handle_array)
        megastructure.export_design(file, folder)

        print('New Results:')
        print(megastructure.get_parasitic_interactions())
