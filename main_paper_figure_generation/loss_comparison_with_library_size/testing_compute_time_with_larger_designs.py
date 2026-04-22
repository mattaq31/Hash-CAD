import time
import numpy as np
from collections import OrderedDict
from crisscross.core_functions.megastructures import Megastructure
from eqcorr2d.eqcorr2d_interface import comprehensive_score_analysis
from pathlib import Path
import matplotlib.pyplot as plt

design_dir = Path('/Users/matt/Partners HealthCare Dropbox/Matthew Aquilina/Origami Crisscross Team Docs/Papers/hash_cad/supplementary_data/figure_5_designs_and_data')
mega_2_1 = Megastructure(import_design_file=str(design_dir / 'valency_2-1_design.xlsx'))

handles, antihandles = mega_2_1.get_bag_of_slat_handles()
match_counts, connection_graph = mega_2_1.get_slat_match_counts()

handle_length = next(iter(handles.values())).shape[0]
num_unique_handles = 64

target_sizes = [64, 500, 1000, 2000, 5000, 10000]
rng = np.random.default_rng(8)

run_tests = False

if run_tests:
    for target in target_sizes:
        expanded_handles = OrderedDict(handles)
        expanded_antihandles = OrderedDict(antihandles)

        existing_count = len(handles)
        for i in range(existing_count, target):
            expanded_handles[f'synthetic_h_{i}'] = rng.integers(1, num_unique_handles + 1, size=handle_length, dtype=np.int64)
            expanded_antihandles[f'synthetic_ah_{i}'] = rng.integers(1, num_unique_handles + 1, size=handle_length, dtype=np.int64)

        total_slats = len(expanded_handles) + len(expanded_antihandles)
        print(f'--- {total_slats} total slats ({len(expanded_handles)} handles, {len(expanded_antihandles)} antihandles) ---')

        start = time.perf_counter()
        result = comprehensive_score_analysis(expanded_handles, expanded_antihandles, match_counts, connection_graph, '90')
        elapsed = time.perf_counter() - start

        print(f'  Time: {elapsed:.2f}s | Worst match: {result["worst_match_score"]} | Mean log score: {result["mean_log_score"]:.4f}')
        print()
else:
    result_on_mac = [(128, 0.01), (1000, 0.68), (2000, 2.65), (4000, 10.81), (10000, 66.77), (20000, 267.24)]
    plt.plot(np.array(result_on_mac)[:, 0], np.array(result_on_mac)[:, 1])
    plt.xlabel('Total number of slats')
    plt.ylabel('Time (s)')
    plt.show()

