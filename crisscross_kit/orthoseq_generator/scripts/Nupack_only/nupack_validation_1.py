import math
from nupack import Model, pfunc, mfe, structure_probability, structure_energy

def main():
    seq = "GATTTTTTTTTTTTC"
    T_c = 37.0
    model = Model(material="dna", celsius=T_c)

    # RT in kcal/mol at temperature T
    R_kcal = 1.98720425864083e-3  # kcal/(mol*K)
    T_K = 273.15 + T_c
    RT = R_kcal * T_K

    # 1) Partition function and complex free energy
    Q_dec, Gp = pfunc(strands=[seq], model=model)  # returns (Q, ΔG) :contentReference[oaicite:3]{index=3}
    Q = (float(Q_dec))
    Qalso = math.exp(-Gp / RT)

    print(f"Sequence: {seq}")
    print(f"T = {T_c:.2f} °C  (RT = {RT:.6f} kcal/mol)")
    print(f"pfunc: Q = {Q_dec} , Gp = {Gp:.6f} kcal/mol")
    print(f"Computed Q={Qalso:.6f}")

    # 2) "Unbound microstate" = completely unpaired structure: '.' * N
    # NUPACK notes: an unpaired strand has free energy 0 (reference state) :contentReference[oaicite:4]{index=4}
    unpaired_structure = "." * len(seq)

    # (a) probability from NUPACK directly
    p_unpaired_direct = float(structure_probability(
        strands=[seq],
        structure=unpaired_structure,
        model=model
    ))

    # (b) probability from "NUPACK-only math": p = exp(-ΔG(struct)/RT) / Q :contentReference[oaicite:5]{index=5}
    G_unpaired = float(structure_energy(
        strands=[seq],
        structure=unpaired_structure,
        model=model
    ))
    p_unpaired_math = math.exp(-G_unpaired / RT) / Q

    print("\nAll-unpaired structure:")
    print(f"  structure = {unpaired_structure}")
    print(f"  ΔG(struct) = {G_unpaired:.6f} kcal/mol")
    print(f"  P(unpaired) via structure_probability = {p_unpaired_direct:.10f}")
    print(f"  P(unpaired) via exp(-ΔG/RT)/Q        = {p_unpaired_math:.10f}")

    # 3) MFE proxy structure probability
    mfe_list = mfe(strands=[seq], model=model)  # returns list of proxy structures :contentReference[oaicite:6]{index=6}
    mfe0 = mfe_list[0]
    mfe_struct = str(mfe0.structure)  # dot-parens notation
    mfe_proxy_energy = float(mfe0.energy)

    # (a) probability from NUPACK directly
    p_mfe_direct = float(structure_probability(
        strands=[seq],
        structure=mfe_struct,
        model=model
    ))

    # (b) probability from exp(-ΔG(struct)/RT)/Q using NUPACK's structure_energy
    # (this should agree with p_mfe_direct; both use ΔG(phi,s) in the formula) :contentReference[oaicite:7]{index=7}
    G_mfe_struct = float(structure_energy(
        strands=[seq],
        structure=mfe_struct,
        model=model
    ))
    p_mfe_math = math.exp(-G_mfe_struct / RT) / Q

    print("\nMFE proxy structure:")
    print(f"  structure = {mfe_struct}")
    print(f"  mfe()[0].energy (proxy) = {mfe_proxy_energy:.6f} kcal/mol")
    print(f"  ΔG(struct_energy)       = {G_mfe_struct:.6f} kcal/mol")
    print(f"  P(MFE) via structure_probability = {p_mfe_direct:.10f}")
    print(f"  P(MFE) via exp(-ΔG/RT)/Q        = {p_mfe_math:.10f}")

if __name__ == "__main__":
    main()
