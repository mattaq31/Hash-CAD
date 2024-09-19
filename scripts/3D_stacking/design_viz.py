
if __name__ == '__main__':
    from crisscross.assembly_handle_optimization.handle_evolution import evolve_handles_from_slat_array
    from crisscross.core_functions.megastructures import Megastructure
    import os

    design_folder = '/Users/matt/Documents/Shih_Lab_Postdoc/research_projects/3D_stacking'

    M1 = Megastructure(import_design_file=os.path.join(design_folder, 'design_with_4_layers.xlsx'))

    ergebnüsse = evolve_handles_from_slat_array(M1.slat_array, unique_handle_sequences=32,
                                                early_hamming_stop=28, evolution_population=30,
                                                generational_survivors=5,
                                                mutation_rate=0.03,
                                                process_count=None,
                                                evolution_generations=10,
                                                split_sequence_handles=False,
                                                progress_bar_update_iterations=2,
                                                log_tracking_directory='/Users/matt/Desktop')

# M1.create_standard_graphical_report(os.path.join(design_folder, 'visualization'),
#                                     colormap='Set1',
#                                     cargo_colormap='Dark2',
#                                     seed_color=(1.0, 1.0, 0.0))
