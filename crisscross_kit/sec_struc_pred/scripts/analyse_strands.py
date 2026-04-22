from pathlib import Path

from sec_struc_pred.nupack_wrapper import NupackTubeConfig, print_binding_summary, run_nupack_analysis
from sec_struc_pred.dot_brac_plotter import plot_nupack_result, set_simulation_params


title = "test12"
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
# parameters for the plotter. We use a relaxation algorithm. Its a toy version of a force field simulation
set_simulation_params(brownian_jitter=0.0)
set_simulation_params(relaxation_steps= 15000)

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
