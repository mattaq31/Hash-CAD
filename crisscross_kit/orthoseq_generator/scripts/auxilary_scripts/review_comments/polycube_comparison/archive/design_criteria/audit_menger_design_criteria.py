"""Check published Menger cores against the candidate filters in the pinned authors' code."""

from pathlib import Path

import Bio
import pandas as pd
from Bio.SeqUtils import MeltingTemp
from nupack import Complex, Model, SetSpec, Strand, Tube, __version__ as nupack_version, mfe, tube_analysis

from orthoseq_generator.sequence_generation import revcom


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[2]
    handles = pd.read_excel(folder / "data" / "menger_published_sequences.xlsx", sheet_name="source_handles")
    cores = handles[["core", "global_pair_id"]].drop_duplicates().sort_values("core")
    screening_params = {"celsius": 15.0, "sodium": 0.05, "magnesium": 0.0125}
    optimization_params = {"celsius": 15.0, "sodium": 1.0, "magnesium": 0.0}
    strand_concentration = 1e-8
    spacer = "T" * 12
    screening_model = Model(material="dna", **screening_params)
    optimization_model = Model(material="dna", **optimization_params)
    tubes = {}
    for row in cores.itertuples(index=False):
        # Odd-length cores cannot equal their own reverse complement; evaluate each pair once.
        if row.core > revcom(row.core):
            continue
        first = Strand(row.core, name=f"pair{row.global_pair_id}_first")
        second = Strand(revcom(row.core), name=f"pair{row.global_pair_id}_second")
        tubes[row.global_pair_id] = Tube(
            strands={first: strand_concentration, second: strand_concentration},
            complexes=SetSpec(include=[Complex([first]), Complex([second]), Complex([first, second])]),
            name=f"pair{row.global_pair_id}",
        )
    screening_results = tube_analysis(tubes=list(tubes.values()), model=screening_model)
    free_fractions = {}
    for pair_id, tube in tubes.items():
        concentrations = screening_results[tube].complex_concentrations
        monomer_concentration = sum(float(c) for comp, c in concentrations.items() if len(comp.strands) == 1)
        free_fractions[pair_id] = monomer_concentration / (2 * strand_concentration)

    audit = []
    for row in cores.itertuples(index=False):
        # Match the authors' Biopython call on bare cores, rather than treating its target as an assembly Tm.
        tm = MeltingTemp.Tm_NN(
            row.core, dnac1=10, dnac2=10, Na=50, K=0, Tris=0, Mg=12.5, dNTPs=0, saltcorr=7,
        )
        exposed_mfe = mfe(strands=[spacer + row.core], model=optimization_model)[0]
        paired_bases = str(exposed_mfe.structure).count("(")
        fraction = free_fractions[row.global_pair_id]
        audit.append({
            "global_pair_id": row.global_pair_id,
            "core": row.core,
            "length": len(row.core),
            "gc_count": sum(base in "GC" for base in row.core),
            "contains_identical_triple": any(base * 3 in row.core for base in "ACGT"),
            "contains_all_four_bases": set(row.core) == set("ACGT"),
            "biopython_core_tm_C": tm,
            "passes_biopython_15C_window": 14.5 < tm < 15.5,
            "nupack_core_free_fraction_15C": fraction,
            "passes_nupack_initial_15C_gate": 0.45 < fraction < 0.55,
            "exposed_mfe_structure": str(exposed_mfe.structure),
            "exposed_mfe_energy_kcal_mol": float(exposed_mfe.energy),
            "passes_exposed_zero_mfe_pairs": paired_bases == 0,
        })
    audit = pd.DataFrame(audit)
    output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    audit.to_csv(output_dir / "menger_design_criteria_audit.tsv", sep="\t", index=False)
    summary = [
        "Audit of compatibility with published code; not a reconstruction of the undocumented Menger run.",
        "Source code commit: 9e0203cda2afac87399687f906f35eec8f6e0f01",
        f"Biopython: {Bio.__version__}; Tm_NN default DNA_NN3 table; salt correction 7.",
        "Bare-core Tm screening: Na 0.05 M, Mg 0.0125 M, each strand 10 nM.",
        f"NUPACK: {nupack_version}; screening model: {screening_model}.",
        "NUPACK initial screening gate: 0.45 < monomer free fraction < 0.55 at 15 C.",
        f"Spacer-inclusive MFE filter model: {optimization_model}; Na 1 M, Mg 0 M; 5' T12.",
        f"Core Tm range: {audit.biopython_core_tm_C.min():.6f} to {audit.biopython_core_tm_C.max():.6f} C.",
        f"Passing Biopython 15 +/- 0.5 C: {int(audit.passes_biopython_15C_window.sum())}/{len(audit)} cores.",
        f"Passing NUPACK initial 15 C gate: {int(audit.passes_nupack_initial_15C_gate.sum())}/{len(audit)} cores.",
        f"Passing exposed zero-MFE-pairs filter: {int(audit.passes_exposed_zero_mfe_pairs.sum())}/{len(audit)}.",
        "Authors' exact software versions and original Menger command remain unconfirmed.",
    ]
    (output_dir / "menger_design_criteria_audit_settings.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))
