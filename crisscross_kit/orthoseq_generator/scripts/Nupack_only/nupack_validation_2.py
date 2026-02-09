import math
from nupack import Model, Strand, Complex, Tube, SetSpec, tube_analysis, pfunc

# -------------------------
# Fixed constants
# -------------------------
T_C = 37.0
R_KCAL = 1.98720425864083e-3
RT = R_KCAL * (273.15 + T_C)

RHO_H2O = 55.0   # <-- YOU ASKED FOR THIS

# -------------------------
# Toy sequences (NOT palindromic)
# -------------------------
A_SEQ = "GCGTATGC"
B_SEQ = "GCATACGC"   # revcomp(A_SEQ)

# Input concentrations
A0 = 1e-6   # 1 µM
B0 = 1e-6   # 1 µM

# -------------------------
# Solve x = Kc (A0-x)(B0-x)
# -------------------------
def solve_AB(A0, B0, Kc):
    a = Kc
    b = -(Kc * (A0 + B0) + 1.0)
    c = Kc * A0 * B0

    disc = b*b - 4*a*c

    x= (-b - math.sqrt(disc)) / (2*a)

    return x

# -------------------------
# Main
# -------------------------
model = Model(material="dna", celsius=T_C)

# pfunc free energies
_, GA  = pfunc([A_SEQ], model=model)
_, GB  = pfunc([B_SEQ], model=model)
_, GAB = pfunc([A_SEQ, B_SEQ], model=model)

GA  = float(GA)
GB  = float(GB)
GAB = float(GAB)

dG_assoc = GAB - GA - GB

Kx = math.exp(-dG_assoc / RT)   # mole fraction equilibrium constant
Kc = Kx / RHO_H2O               # molar equilibrium constant

# Hand solution
AB_hand = solve_AB(A0, B0, Kc)

# -------------------------
# NUPACK tube (AB only)
# -------------------------
A = Strand(A_SEQ, name="A")
B = Strand(B_SEQ, name="B")

AA = Complex([A, A])
BB = Complex([B, B])

tube = Tube(
    strands={A: A0, B: B0},
    complexes=SetSpec(max_size=2, exclude=[AA, BB]),
    name="AB_only"
)

res = tube_analysis([tube], model=model)
tube_res = res[tube]

AB_nupack = None
for cx, conc in tube_res.complex_concentrations.items():
    names = sorted(s.name for s in cx.strands)
    if names == ["A", "B"]:
        AB_nupack = float(conc)

# -------------------------
# Output
# -------------------------
print("=== AB-only dimerization check ===")
print(f"A = {A_SEQ}")
print(f"B = {B_SEQ}")
print()
print(f"GA  = {GA:.6f} kcal/mol")
print(f"GB  = {GB:.6f} kcal/mol")
print(f"GAB = {GAB:.6f} kcal/mol")
print(f"dG_assoc = {dG_assoc:.6f} kcal/mol")
print()
print(f"RT = {RT:.6f} kcal/mol")
print(f"rho = {RHO_H2O:.1f} M")
print(f"Kx = {Kx:.6e}")
print(f"Kc = {Kc:.6e} 1/M")
print()
print(f"[AB] hand   = {AB_hand:.6e} M")
print(f"[AB] nupack = {AB_nupack:.6e} M")
print(f"diff        = {AB_hand - AB_nupack:.3e} M")
