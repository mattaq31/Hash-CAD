#!/usr/bin/env python3

"""
Print the single-strand NUPACK MFE structure for one DNA sequence.
"""

from nupack import Complex, Model, Strand, complex_analysis


def structure_to_dot_bracket(structure):
    if hasattr(structure, "dotparensplus"):
        return structure.dotparensplus()
    if hasattr(structure, "dotparens"):
        return structure.dotparens()
    return str(structure)


if __name__ == "__main__":
    sequence = "GATTGCGATAGCGATC"

    strand = Strand(sequence, name="S")
    complex_obj = Complex([strand], name="(S)")
    model = Model(material="dna", celsius=37.0, sodium=0.05, magnesium=0.025)
    results = complex_analysis([complex_obj], model=model, compute=["mfe"])
    mfe_list = results[complex_obj].mfe

    if not mfe_list:
        raise RuntimeError("NUPACK returned no MFE structure.")

    mfe = mfe_list[0]
    print(f"sequence:    {sequence}")
    print(f"dot-bracket: {structure_to_dot_bracket(mfe.structure)}")
    print(f"mfe kcal/mol: {mfe.energy:.3f}")
