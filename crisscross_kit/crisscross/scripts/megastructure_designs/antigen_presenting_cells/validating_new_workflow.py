"""Quick workflow verification for the cargo-as-protector strategy."""
from nupack import Strand, Complex, SetSpec, Tube, tube_analysis, Model

WC = str.maketrans("ATCG", "TAGC")
def rc(seq): return seq.translate(WC)[::-1]

model = Model(material="dna", celsius=25, sodium=0.05, magnesium=0.015)

seqs = {
    "ON_SLAT":      "CTCCTCAATCACTATTCCTATTATAACTATACTT",
    "ANTI_BART":    "TCTATACCTTCATACCTACAC",
    "ANTI_EDNA":    "CCACTATCAACTTTTCACTCA",
    "CARGO_BART":   rc("TCTATACCTTCATACCTACAC"),
    "CARGO_EDNA":   rc("CCACTATCAACTTTTCACTCA"),
    "ON_BEAD":      "AAGTATAGTTATAATAGGAATAGT",
    "INVADER":      "AAGTATAGTTATAATAGGAATAGTGATTGAGGAG",
}
s = {name: Strand(seq, name=name) for name, seq in seqs.items()}

print("Sequences:")
for name, seq in seqs.items():
    print(f"  {name:15s}  {seq}  ({len(seq)} nt)")

SEP = "=" * 70
mega_conc = 0.5e-9


def report(tube_obj, results, pairs, concs):
    print(f"  {'Pair':35s}  {'Conc':>12s}  {'% of ref':>10s}  {'Verdict':>8s}")
    print(f"  {'-'*35}  {'-'*12}  {'-'*10}  {'-'*8}")
    for n1, n2, ref_name, expected in pairs:
        cx = Complex([s[n1], s[n2]], name=f"{n1}_x_{n2}_{tube_obj.name}")
        conc = results.tubes[tube_obj].complex_concentrations[cx]
        frac = conc / concs[ref_name] * 100
        if expected == "YES":
            verdict = "OK" if frac > 90 else "CONCERN"
        else:
            verdict = "OK" if frac < 1 else "CONCERN"
        print(f"  {n1:15s} x {n2:15s}  {conc:>12.2e}  {frac:>9.2f}%  {verdict:>8s}")


# ---- STEP 1: Pre-saturate ANTIs with cargo complements ----
step1_concs = {
    "ANTI_BART":   mega_conc * 160,        # 80 nM
    "ANTI_EDNA":   mega_conc * 160,        # 80 nM
    "ON_SLAT":     mega_conc * 8,          # 4 nM
    "CARGO_BART":  mega_conc * 160 * 5,    # 400 nM (5:1)
    "CARGO_EDNA":  mega_conc * 160 * 5,    # 400 nM (5:1)
}

print(f"\n{SEP}")
print("STEP 1: PRE-SATURATE — cargo complements bind ANTI handles")
print(f"  [ANTI_BART]  = {step1_concs['ANTI_BART']*1e9:.0f} nM  (0.5 nM x 160)")
print(f"  [ANTI_EDNA]  = {step1_concs['ANTI_EDNA']*1e9:.0f} nM  (0.5 nM x 160)")
print(f"  [ON_SLAT]    = {step1_concs['ON_SLAT']*1e9:.0f} nM  (0.5 nM x 8)")
print(f"  [CARGO_BART] = {step1_concs['CARGO_BART']*1e9:.0f} nM  (5:1 excess)")
print(f"  [CARGO_EDNA] = {step1_concs['CARGO_EDNA']*1e9:.0f} nM  (5:1 excess)")
print(SEP)

t1 = Tube(strands={s[n]: c for n, c in step1_concs.items()}, complexes=SetSpec(max_size=2), name="step1")
r1 = tube_analysis(tubes=[t1], model=model, compute=["pfunc"])

report(t1, r1, [
    ("CARGO_BART", "ANTI_BART",  "ANTI_BART",  "YES"),
    ("CARGO_EDNA", "ANTI_EDNA",  "ANTI_EDNA",  "YES"),
    ("CARGO_BART", "ON_SLAT",    "ON_SLAT",    "NO"),
    ("CARGO_EDNA", "ON_SLAT",    "ON_SLAT",    "NO"),
    ("CARGO_BART", "ANTI_EDNA",  "ANTI_EDNA",  "NO"),
    ("CARGO_EDNA", "ANTI_BART",  "ANTI_BART",  "NO"),
], step1_concs)


# ---- STEP 2: Add to beads ----
step2_concs = {
    "ANTI_BART":   mega_conc * 160,
    "ANTI_EDNA":   mega_conc * 160,
    "ON_SLAT":     mega_conc * 8,
    "CARGO_BART":  mega_conc * 160 * 5,
    "CARGO_EDNA":  mega_conc * 160 * 5,
    "ON_BEAD":     1.5e-9 * 7000,          # 10.5 µM
}

print(f"\n{SEP}")
print("STEP 2: BEAD BINDING — add mixture to ON_BEAD-coated beads")
print(f"  [ON_BEAD]    = {step2_concs['ON_BEAD']*1e6:.1f} uM  (huge excess from bead surface)")
print("  All other concentrations same as Step 1")
print(SEP)

t2 = Tube(strands={s[n]: c for n, c in step2_concs.items()}, complexes=SetSpec(max_size=2), name="step2")
r2 = tube_analysis(tubes=[t2], model=model, compute=["pfunc"])

report(t2, r2, [
    ("ON_BEAD",    "ON_SLAT",    "ON_SLAT",    "YES"),
    ("CARGO_BART", "ANTI_BART",  "ANTI_BART",  "YES"),
    ("CARGO_EDNA", "ANTI_EDNA",  "ANTI_EDNA",  "YES"),
    ("ON_BEAD",    "ANTI_BART",  "ANTI_BART",  "NO"),
    ("ON_BEAD",    "ANTI_EDNA",  "ANTI_EDNA",  "NO"),
    ("ON_BEAD",    "CARGO_BART", "CARGO_BART", "NO"),
    ("ON_BEAD",    "CARGO_EDNA", "CARGO_EDNA", "NO"),
], step2_concs)


# ---- STEP 4: Add INVADER to release megastructures ----
# After wash (step 3), only bead-bound megastructures remain.
# Cargo is now 1:1 with ANTI (excess washed away).
step4_concs = {
    "ANTI_BART":   mega_conc * 160,
    "ANTI_EDNA":   mega_conc * 160,
    "ON_SLAT":     mega_conc * 8,
    "CARGO_BART":  mega_conc * 160,     # 1:1, excess washed away
    "CARGO_EDNA":  mega_conc * 160,     # 1:1, excess washed away
    "ON_BEAD":     1.5e-9 * 7000,
    "INVADER":     50e-6,
}

print(f"\n{SEP}")
print("STEP 4: STRAND DISPLACEMENT — add INVADER to release from beads")
print(f"  [INVADER]    = {step4_concs['INVADER']*1e6:.0f} uM  (huge excess)")
print(f"  [CARGO_BART] = {step4_concs['CARGO_BART']*1e9:.0f} nM  (1:1 with ANTI, excess washed)")
print(f"  [CARGO_EDNA] = {step4_concs['CARGO_EDNA']*1e9:.0f} nM  (1:1 with ANTI, excess washed)")
print(f"  KEY TEST: Can INVADER displace perfect-match cargo from ANTIs?")
print(SEP)

t4 = Tube(strands={s[n]: c for n, c in step4_concs.items()}, complexes=SetSpec(max_size=2), name="step4")
r4 = tube_analysis(tubes=[t4], model=model, compute=["pfunc"])

report(t4, r4, [
    ("INVADER",    "ON_SLAT",    "ON_SLAT",    "YES"),
    ("CARGO_BART", "ANTI_BART",  "ANTI_BART",  "YES"),
    ("CARGO_EDNA", "ANTI_EDNA",  "ANTI_EDNA",  "YES"),
    ("ON_BEAD",    "ON_SLAT",    "ON_SLAT",    "NO"),
    ("INVADER",    "ANTI_BART",  "ANTI_BART",  "NO"),
    ("INVADER",    "ANTI_EDNA",  "ANTI_EDNA",  "NO"),
    ("INVADER",    "CARGO_BART", "CARGO_BART", "NO"),
    ("INVADER",    "CARGO_EDNA", "CARGO_EDNA", "NO"),
    ("ON_BEAD",    "ANTI_BART",  "ANTI_BART",  "NO"),
    ("ON_BEAD",    "ANTI_EDNA",  "ANTI_EDNA",  "NO"),
], step4_concs)
