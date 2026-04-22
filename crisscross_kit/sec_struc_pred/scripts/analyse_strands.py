from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Nupack_wrapper import NupackTubeConfig, print_binding_summary, run_nupack_analysis
from dot_brac_plotter import plot_nupack_result, set_simulation_params


title = "test1"
standard_out = Path(__file__).resolve().parents[1] / "default_outputs"

direct_config = NupackTubeConfig(
    sequences=[
        ["TTTAAAATTTACTGGGCGCTGCAAGTTTTTTTTTTT", 1000],
        ["ACTTGCAGGCCCAGTTTTTTTAAAAAAAAAAAAA", 1000],
    ],
    material="dna",
    celsius=37,
    sodium=0.05,
    magnesium=0.015,
    max_complex_size=2,
    compute=["pfunc", "mfe"],
    tube_name=title,
    strand_prefix="seq",
)

set_simulation_params(brownian_jitter=0.0)
set_simulation_params(relaxation_steps= 55000)

direct_result = run_nupack_analysis(direct_config)
print_binding_summary(title, direct_result, save=standard_out)
plot_nupack_result(
    title,
    direct_result,
    save=standard_out,
    file_format="pdf", # file_format="svg",
)

# config_path = Path(__file__).resolve().parents[1] / "default_configs" / "simple_binding_example.toml"
# direct_config.write(config_path)
#
# file_result = run_nupack_analysis(config_path)
# print_binding_summary("Same analysis loaded from TOML", file_result)
# print()
# print(f"Wrote TOML config to: {config_path}")
