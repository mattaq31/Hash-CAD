from pathlib import Path

from sec_struc_pred.nupack_wrapper import NupackTubeConfig, print_binding_summary, run_nupack_analysis
from sec_struc_pred.dot_brac_plotter import plot_nupack_result, set_simulation_params


def reverse_complement(sequence):
    return sequence.translate(str.maketrans("ACGTacgt", "TGCAtgca"))[::-1]


NELSON_SOCKET = "AATTACATCTCTCTCCCATCA"
KATZEN_LINKER = "TTA TTA TTA TTA"
NELSON_BINDING_REGION = reverse_complement(NELSON_SOCKET)
#NELSON_SOCKET= "TTTTT"+NELSON_SOCKET
PRIMER_5 = "CGT ACG GAA TTC GCT AGC"
PRIMER_3 = "GGA TCC GAG CTC CAC GTG"

APTAMER_CORES = {
    "STC_03_37": "CATATCCGCGTCGCTGCGCTCAGACCCACCACCACGCACC",
    "STC_06_37": "GGGCGGGGGTGCTGGGGGAATGGAGTGCTGCGTGCTGCGG",
    "STC_12_37": "GGACCGCAGGTGCACTGGGCGACGTCTCTGGGTGTGGTGT",
}

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "default_outputs" / "bak_apta"


def sequence_variants(core_sequence):
    return {
        "01_core_only": {
            "sequence": core_sequence,
            "include_nelson_socket": False,
        },
        "02_core_linker_nelson": {
            "sequence": f"{core_sequence}{KATZEN_LINKER}{NELSON_BINDING_REGION}",
            "include_nelson_socket": True,
        },
        "03_primers_core_linker_nelson": {
            "sequence": f"{PRIMER_5}{core_sequence}{PRIMER_3}{KATZEN_LINKER}{NELSON_BINDING_REGION}",
            "include_nelson_socket": True,
        },
        "04_primers_core": {
            "sequence": f"{PRIMER_5}{core_sequence}{PRIMER_3}",
            "include_nelson_socket": False,
        },
    }


def run_single_analysis(title, sequence, output_dir, include_nelson_socket=False):
    sequences = [[sequence, 1000]]
    if include_nelson_socket:
        sequences.append([NELSON_SOCKET, 1000])

    config = NupackTubeConfig(
        sequences=sequences,
        material="dna",
        celsius=25,
        sodium=0.05,
        magnesium=0.015,
        max_complex_size=2 if include_nelson_socket else 1,
        compute=["pfunc", "mfe"],
        tube_name=title,
        strand_prefix="seq",
    )

    result = run_nupack_analysis(config)
    print_binding_summary(title, result, save=output_dir)
    plot_nupack_result(
        title,
        result,
        save=output_dir,
        file_format="pdf",
    )


# Parameters for the plotter. We use a relaxation algorithm. Its a toy version of a force field simulation.
set_simulation_params(brownian_jitter=0.0)
set_simulation_params(relaxation_steps=15000)
set_simulation_params(backbone_straightness=0.01)
set_simulation_params(centering=0.0002)
# set_simulation_params(reference_sequence_length=300) # "start_radius": 95, "reference_sequence_length": 16


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for aptamer_name, core_sequence in APTAMER_CORES.items():
        aptamer_output_dir = OUTPUT_DIR / aptamer_name
        aptamer_output_dir.mkdir(parents=True, exist_ok=True)

        for variant_name, variant in sequence_variants(core_sequence).items():
            run_single_analysis(
                f"{aptamer_name}_{variant_name}",
                variant["sequence"],
                aptamer_output_dir,
                include_nelson_socket=variant["include_nelson_socket"],
            )
