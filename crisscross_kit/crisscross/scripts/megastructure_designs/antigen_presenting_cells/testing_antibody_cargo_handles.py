"""
NUPACK interaction analysis for antibody cargo handle sequences.

Checks for unintended cross-interactions between cargo sequences.
The ON BEAD and INVADER sequences are designed to be complementary to ON SLAT,
so those expected interactions are excluded from the analysis.
"""

from nupack import Strand, Complex, SetSpec, Tube, tube_analysis, Model
from itertools import combinations

# ---- Sequences ----
# Removed modifications (/SLAT/, /5Biosg/) as NUPACK only needs the DNA sequence.
SEQUENCES = {
    "ON_SLAT":      "CTCCTCAATCACTATTCCTATTATAACTATACTT",
    "ON_BEAD":      "AAGTATAGTTATAATAGGAATAGT",
    "INVADER":      "AAGTATAGTTATAATAGGAATAGTGATTGAGGAG",
    "ANTI_BART":    "TCTATACCTTCATACCTACAC",
    "ANTI_NELSON":  "AATTACATCTCTCTCCCATCA",
    "ANTI_QUIMBY":  "CCTACTTCATCCATTAAATCC",
    "ANTI_EDNA":    "CCACTATCAACTTTTCACTCA",
}

# Pairs whose interaction is expected by design (ignore these).
EXPECTED_PAIRS = {
    frozenset({"ON_SLAT", "ON_BEAD"}),
    frozenset({"ON_SLAT", "INVADER"}),
}

# ---- NUPACK setup ----
model = Model(material="dna", celsius=25, sodium=0.05, magnesium=0.015)  # 50 mM Na+ is NUPACK minimum

strands = {name: Strand(seq, name=name) for name, seq in SEQUENCES.items()}

# Build complexes: every single strand + every pairwise combination (excluding expected pairs).
complexes = {}
for name, strand in strands.items():
    complexes[(name,)] = Complex([strand], name=name)

pairs_to_check = []
for (n1, s1), (n2, s2) in combinations(strands.items(), 2):
    if frozenset({n1, n2}) in EXPECTED_PAIRS:
        continue
    pair_name = f"{n1}_x_{n2}"
    complexes[(n1, n2)] = Complex([s1, s2], name=pair_name)
    pairs_to_check.append((n1, n2))

# Put all strands in a single tube at 1 µM each.
tube = Tube(
    strands={s: 1e-6 for s in strands.values()},
    complexes=SetSpec(max_size=2),
    name="cargo_mix",
)

# ---- Run analysis ----
results = tube_analysis(tubes=[tube], model=model, compute=["pairs", "pfunc"])

# ---- Report ----
INTERACTION_THRESHOLD_KCAL = -5.0  # flag pairs with free energy below this

print("=" * 70)
print("NUPACK PAIRWISE INTERACTION ANALYSIS (partition function free energy)")
print(f"Model: DNA, 25 °C, [Na+]=50 mM (NUPACK min), [Mg2+]=15 mM")
print(f"Threshold for flagging: ΔG < {INTERACTION_THRESHOLD_KCAL} kcal/mol")
print("=" * 70)

# Self-structure (hairpins)
print("\n--- Single-strand ensemble free energy ---")
for name in SEQUENCES:
    c = complexes[(name,)]
    energy = results[c].free_energy
    flag = " *** FLAGGED" if energy < INTERACTION_THRESHOLD_KCAL else ""
    print(f"  {name:15s}  ΔG = {energy:+.2f} kcal/mol{flag}")

# Cross-interactions (excluding expected pairs)
print(f"\n--- Pairwise cross-interactions (unexpected only) ---")
print(f"  {'Pair':33s}  {'ΔG':>14s}  {'Fraction bound':>14s}")
print(f"  {'-'*33}  {'-'*14}  {'-'*14}")
flagged = []
for n1, n2 in pairs_to_check:
    c = complexes[(n1, n2)]
    energy = results[c].free_energy
    conc = results.tubes[tube].complex_concentrations[c]
    frac = conc / 1e-6 * 100  # as % of 1 µM input
    flag = ""
    if energy < INTERACTION_THRESHOLD_KCAL:
        flag = " *** FLAGGED"
        flagged.append((n1, n2, energy, frac))
    print(f"  {n1:15s} x {n2:15s}  {energy:+.2f} kcal/mol  {frac:>13.2f}%{flag}")

# Summary
print("\n" + "=" * 70)
if flagged:
    print(f"WARNING: {len(flagged)} pair(s) flagged with ΔG < {INTERACTION_THRESHOLD_KCAL} kcal/mol:")
    for n1, n2, e, f in flagged:
        print(f"  {n1} x {n2}: {e:+.2f} kcal/mol, {f:.2f}% bound")
else:
    print("No significant unintended interactions detected.")
print("=" * 70)


# ==========================================================================
# REALISTIC SCENARIO: 150 nm bead + megastructure
# ==========================================================================
# Assumptions:
#   - Megastructure concentration: 0.5 nM
#   - Bead concentration: 3x megastructure = 1.5 nM
#   - ~160 ANTI_BART handles per megastructure
#   - ~160 ANTI_EDNA handles per megastructure
#   - 150 nm bead densely coated with ON_BEAD
#     Surface area = 4π(75 nm)² ≈ 70,686 nm²
#     At ~10 nm² footprint per oligo → ~7,000 ON_BEAD per bead (conservative estimate)
#
# Effective strand concentrations (bead/megastructure conc × copies per particle):
#   [ON_BEAD]    = 1.5 nM × 7,000 = 10.5 µM
#   [ANTI_BART]  = 0.5 nM × 160   = 80 nM
#   [ANTI_EDNA]= 0.5 nM × 160   = 80 nM

MEGA_CONC = 0.5e-9          # 0.5 nM megastructure
BEAD_CONC = 3 * MEGA_CONC   # 1.5 nM beads (3-fold excess)
ON_BEAD_PER_BEAD = 7000     # estimated for 150 nm bead
ANTI_PER_MEGA = 160         # copies of each anti-handle per megastructure

effective_concs = {
    "ON_BEAD":      BEAD_CONC * ON_BEAD_PER_BEAD,     # 10.5 µM
    "ANTI_BART":    MEGA_CONC * ANTI_PER_MEGA,  # 80 nM
    "ANTI_EDNA":  MEGA_CONC * ANTI_PER_MEGA,         # 80 nM
}

scenario_strands = {name: strands[name] for name in effective_concs}

for temp_c in [25, 37]:
    scenario_model = Model(material="dna", celsius=temp_c, sodium=0.05, magnesium=0.015)

    scenario_tube = Tube(
        strands={scenario_strands[name]: conc for name, conc in effective_concs.items()},
        complexes=SetSpec(max_size=2),
        name=f"bead_mega_{temp_c}C",
    )

    scenario_results = tube_analysis(tubes=[scenario_tube], model=scenario_model, compute=["pairs", "pfunc"])

    print(f"\n{'=' * 70}")
    print(f"REALISTIC SCENARIO (but not considering effective concentration): 150 nm bead + megastructure @ {temp_c} °C")
    print(f"  [ON_BEAD]    = {effective_concs['ON_BEAD']*1e6:.1f} µM  (1.5 nM beads × {ON_BEAD_PER_BEAD} per bead)")
    print(f"  [ANTI_BART]  = {effective_concs['ANTI_BART']*1e9:.0f} nM  (0.5 nM mega × {ANTI_PER_MEGA} per mega)")
    print(f"  [ANTI_EDNA]= {effective_concs['ANTI_EDNA']*1e9:.0f} nM  (0.5 nM mega × {ANTI_PER_MEGA} per mega)")
    print(f"{'=' * 70}")

    # Report fraction bound for each pair
    scenario_pairs = [("ON_BEAD", "ANTI_BART"), ("ON_BEAD", "ANTI_EDNA"), ("ANTI_BART", "ANTI_EDNA")]
    print(f"  {'Pair':33s}  {'Conc (dimer)':>14s}  {'% ANTI bound':>14s}")
    print(f"  {'-'*33}  {'-'*14}  {'-'*14}")

    for n1, n2 in scenario_pairs:
        pair_complex = Complex([scenario_strands[n1], scenario_strands[n2]], name=f"{n1}_x_{n2}_{temp_c}C")
        dimer_conc = scenario_results.tubes[scenario_tube].complex_concentrations[pair_complex]
        # Report as fraction of the ANTI strand (the limiting/lower-conc species)
        if n1 == "ON_BEAD":
            ref_conc = effective_concs[n2]
        else:
            ref_conc = effective_concs[n1]  # both are 80 nM
        frac = dimer_conc / ref_conc * 100
        print(f"  {n1:15s} x {n2:15s}  {dimer_conc:.2e} M  {frac:>13.2f}%")


# ==========================================================================
# CAP STRAND DESIGN: toehold + complement of ANTI, screened against ON_SLAT
# ==========================================================================
# Cap structure: [10 nt toehold] -- [complement of ANTI sequence]
# The toehold enables later strand displacement to remove the cap.
# Goal: cap binds ANTI tightly, does NOT interact with ON_SLAT.

import random

random.seed(42)

WC = str.maketrans("ATCG", "TAGC")


def reverse_complement(seq):
    return seq.translate(WC)[::-1]


ANTI_TARGETS = {
    "ANTI_BART": SEQUENCES["ANTI_BART"],
    "ANTI_EDNA": SEQUENCES["ANTI_EDNA"],
}
ON_SLAT_SEQ = SEQUENCES["ON_SLAT"]

TOEHOLD_LEN = 10
NUM_CANDIDATES = 500
screen_model = Model(material="dna", celsius=25, sodium=0.05, magnesium=0.015)


def random_toehold(length, gc_min=0.4, gc_max=0.6):
    """Generate a random toehold with controlled GC content."""
    while True:
        seq = "".join(random.choice("ATCG") for _ in range(length))
        gc = (seq.count("G") + seq.count("C")) / length
        # Reject homopolymer runs of 3+
        if gc_min <= gc <= gc_max and not any(b * 3 in seq for b in "ATCG"):
            return seq


BEST_CAPS = {}  # populated during the screen below

print(f"\n\n{'=' * 70}")
print("CAP STRAND DESIGN")
print(f"Screening {NUM_CANDIDATES} random toeholds ({TOEHOLD_LEN} nt) per ANTI target")
print(f"Cap = [toehold] + [reverse complement of ANTI]")
print(f"Optimizing: strong ANTI binding, minimal ON_SLAT interaction")
print(f"{'=' * 70}")

for anti_name, anti_seq in ANTI_TARGETS.items():
    anti_rc = reverse_complement(anti_seq)

    # Generate candidates
    candidates = []
    for i in range(NUM_CANDIDATES):
        toehold = random_toehold(TOEHOLD_LEN)
        cap_seq = toehold + anti_rc

        cap_strand = Strand(cap_seq, name=f"cap_{i}")
        anti_strand = Strand(anti_seq, name=f"anti_{i}")
        slat_strand = Strand(ON_SLAT_SEQ, name=f"slat_{i}")

        # Complexes to evaluate
        cap_alone = Complex([cap_strand], name=f"cap_alone_{i}")
        cap_anti = Complex([cap_strand, anti_strand], name=f"cap_anti_{i}")
        cap_slat = Complex([cap_strand, slat_strand], name=f"cap_slat_{i}")
        anti_alone = Complex([anti_strand], name=f"anti_alone_{i}")
        slat_alone = Complex([slat_strand], name=f"slat_alone_{i}")

        # Tube: cap + anti + ON_SLAT at equal concentrations
        screen_tube = Tube(
            strands={cap_strand: 1e-6, anti_strand: 1e-6, slat_strand: 1e-6},
            complexes=SetSpec(max_size=2),
            name=f"screen_{i}",
        )

        screen_results = tube_analysis(tubes=[screen_tube], model=screen_model, compute=["pfunc"])

        cap_anti_conc = screen_results.tubes[screen_tube].complex_concentrations[cap_anti]
        cap_slat_conc = screen_results.tubes[screen_tube].complex_concentrations[cap_slat]
        cap_anti_frac = cap_anti_conc / 1e-6 * 100
        cap_slat_frac = cap_slat_conc / 1e-6 * 100
        cap_anti_dg = screen_results[cap_anti].free_energy
        cap_slat_dg = screen_results[cap_slat].free_energy

        candidates.append({
            "toehold": toehold,
            "cap_seq": cap_seq,
            "cap_anti_frac": cap_anti_frac,
            "cap_slat_frac": cap_slat_frac,
            "cap_anti_dg": cap_anti_dg,
            "cap_slat_dg": cap_slat_dg,
        })

    # Rank: maximize cap:ANTI binding, minimize cap:ON_SLAT binding
    # Sort by: lowest cap_slat_frac, then highest cap_anti_frac
    candidates.sort(key=lambda c: (-c["cap_anti_frac"], c["cap_slat_frac"]))

    print(f"\n--- Top 5 cap candidates for {anti_name} ({anti_seq}) ---")
    print(f"  {'Rank':>4s}  {'Toehold':12s}  {'Full cap sequence':>35s}  {'%ANTI bound':>11s}  {'%SLAT bound':>11s}  {'ΔG cap:ANTI':>12s}  {'ΔG cap:SLAT':>12s}")
    print(f"  {'-'*4}  {'-'*12}  {'-'*35}  {'-'*11}  {'-'*11}  {'-'*12}  {'-'*12}")
    for rank, c in enumerate(candidates[:5], 1):
        print(f"  {rank:4d}  {c['toehold']:12s}  {c['cap_seq']:>35s}  {c['cap_anti_frac']:>10.2f}%  {c['cap_slat_frac']:>10.4f}%  {c['cap_anti_dg']:>+10.2f}  {c['cap_slat_dg']:>+10.2f}")

    best = candidates[0]
    BEST_CAPS[anti_name] = best["cap_seq"]
    print(f"\n  RECOMMENDED for {anti_name}:")
    print(f"    Cap:     5'-{best['cap_seq']}-3'")
    print(f"    Invader: 5'-{reverse_complement(best['cap_seq'])}-3'")
    print(f"    Toehold region: {best['toehold']} ({TOEHOLD_LEN} nt)")

print(f"\n\n{'='*70}")
print("WORKFLOW VERIFICATION")
print(f"{'='*70}")

# Define all strands for the workflow
workflow_seqs = {
    "ON_SLAT":       SEQUENCES["ON_SLAT"],
    "ANTI_BART":     SEQUENCES["ANTI_BART"],
    "ANTI_EDNA":     SEQUENCES["ANTI_EDNA"],
    "CAP_BART":      BEST_CAPS["ANTI_BART"],
    "CAP_EDNA":      BEST_CAPS["ANTI_EDNA"],
    "ON_BEAD":       SEQUENCES["ON_BEAD"],
    "INVADER":       SEQUENCES["INVADER"],
    "INV_CAP_BART":  reverse_complement(BEST_CAPS["ANTI_BART"]),
    "INV_CAP_EDNA":  reverse_complement(BEST_CAPS["ANTI_EDNA"]),
}

print("\nStrands in workflow:")
for name, seq in workflow_seqs.items():
    print(f"  {name:15s}  5'-{seq}-3'  ({len(seq)} nt)")

wf_strands = {name: Strand(seq, name=name) for name, seq in workflow_seqs.items()}


def run_workflow_tube(tube_name, strand_concs, model, pairs_of_interest):
    """Run a tube analysis and report fraction bound for specific pairs."""
    tube_strands = {wf_strands[name]: conc for name, conc in strand_concs.items()}
    wf_tube = Tube(strands=tube_strands, complexes=SetSpec(max_size=2), name=tube_name)
    wf_results = tube_analysis(tubes=[wf_tube], model=model, compute=["pfunc"])

    print(f"\n  {'Pair':35s}  {'Conc':>12s}  {'% of limiting':>13s}  {'Verdict':>10s}")
    print(f"  {'-'*35}  {'-'*12}  {'-'*13}  {'-'*10}")

    for n1, n2, expected in pairs_of_interest:
        cx = Complex([wf_strands[n1], wf_strands[n2]], name=f"{n1}_x_{n2}_{tube_name}")
        conc = wf_results.tubes[wf_tube].complex_concentrations[cx]
        # Use the lower input concentration as the reference
        ref = min(strand_concs[n1], strand_concs[n2])
        frac = conc / ref * 100
        if expected == "YES":
            verdict = "OK" if frac > 90 else "CONCERN"
        else:
            verdict = "OK" if frac < 1 else "CONCERN"
        print(f"  {n1:15s} x {n2:15s}  {conc:>12.2e}  {frac:>12.2f}%  {verdict:>10s}")


# ---- STEP 1: Capping ----
# Mix ON_SLAT + ANTI_BART + ANTI_EDNA + CAP_BART + CAP_EDNA
# Expected: caps bind their ANTIs, nothing binds ON_SLAT
print(f"\n{'='*70}")
print("STEP 1: CAPPING — mix megastructure handles with caps")
print("  Present: ON_SLAT, ANTI_BART, ANTI_EDNA, CAP_BART, CAP_EDNA (1 µM each)")
print("  Expected: CAP_BART→ANTI_BART, CAP_EDNA→ANTI_EDNA, ON_SLAT free")
print(f"{'='*70}")

step1_concs = {
    "ON_SLAT": 1e-6, "ANTI_BART": 1e-6, "ANTI_EDNA": 1e-6,
    "CAP_BART": 1e-6, "CAP_EDNA": 1e-6,
}
step1_pairs = [
    ("CAP_BART",  "ANTI_BART",  "YES"),  # should bind
    ("CAP_EDNA",  "ANTI_EDNA",  "YES"),  # should bind
    ("CAP_BART",  "ON_SLAT",    "NO"),   # should NOT bind
    ("CAP_EDNA",  "ON_SLAT",    "NO"),   # should NOT bind
    ("CAP_BART",  "ANTI_EDNA",  "NO"),   # cross-cap, should NOT
    ("CAP_EDNA",  "ANTI_BART",  "NO"),   # cross-cap, should NOT
    ("CAP_BART",  "CAP_EDNA",   "NO"),   # cap-cap, should NOT
    ("ANTI_BART", "ON_SLAT",    "NO"),   # should NOT
    ("ANTI_EDNA", "ON_SLAT",    "NO"),   # should NOT
]
run_workflow_tube("step1_capping", step1_concs, screen_model, step1_pairs)


# ---- STEP 2: Bead binding ----
# Add ON_BEAD to the capped mix
# Expected: ON_BEAD binds ON_SLAT only, caps protect ANTIs
print(f"\n{'='*70}")
print("STEP 2: BEAD BINDING — add ON_BEAD to capped megastructure")
print("  Present: ON_SLAT, ANTI_BART, ANTI_EDNA, CAP_BART, CAP_EDNA, ON_BEAD (1 µM each)")
print("  Expected: ON_BEAD→ON_SLAT, caps remain on ANTIs")
print(f"{'='*70}")

step2_concs = {
    "ON_SLAT": 1e-6, "ANTI_BART": 1e-6, "ANTI_EDNA": 1e-6,
    "CAP_BART": 1e-6, "CAP_EDNA": 1e-6, "ON_BEAD": 1e-6,
}
step2_pairs = [
    ("ON_BEAD",   "ON_SLAT",    "YES"),  # intended binding
    ("CAP_BART",  "ANTI_BART",  "YES"),  # cap stays on
    ("CAP_EDNA",  "ANTI_EDNA",  "YES"),  # cap stays on
    ("ON_BEAD",   "ANTI_BART",  "NO"),   # blocked by cap
    ("ON_BEAD",   "ANTI_EDNA",  "NO"),   # blocked by cap
    ("ON_BEAD",   "CAP_BART",   "NO"),   # should NOT
    ("ON_BEAD",   "CAP_EDNA",   "NO"),   # should NOT
]
run_workflow_tube("step2_bead", step2_concs, screen_model, step2_pairs)


# ---- STEP 3: Strand displacement (uncapping) ----
# Add invaders at 50 µM excess. ON_BEAD is gone (spun away with beads).
# Expected: INVADER displaces nothing (ON_BEAD already removed, but binds ON_SLAT),
#           INV_CAP_BART displaces CAP_BART from ANTI_BART,
#           INV_CAP_EDNA displaces CAP_EDNA from ANTI_EDNA
#           No cross-displacement
print(f"\n{'='*70}")
print("STEP 3: STRAND DISPLACEMENT — add invaders to uncap (beads already removed)")
print("  Present: ON_SLAT, ANTI_BART, ANTI_EDNA, CAP_BART, CAP_EDNA @ 1 µM")
print("           INVADER, INV_CAP_BART, INV_CAP_EDNA @ 50 µM (excess)")
print("  Expected: INVADER→ON_SLAT, INV_CAP_BART→CAP_BART, INV_CAP_EDNA→CAP_EDNA")
print(f"{'='*70}")

step3_concs = {
    "ON_SLAT": 1e-6, "ANTI_BART": 1e-6, "ANTI_EDNA": 1e-6,
    "CAP_BART": 1e-6, "CAP_EDNA": 1e-6,
    "INVADER": 50e-6, "INV_CAP_BART": 50e-6, "INV_CAP_EDNA": 50e-6,
}
step3_pairs = [
    # Intended displacements — invader binds its full target (cap or ON_SLAT)
    ("INVADER",       "ON_SLAT",      "YES"),  # invader takes ON_SLAT
    ("INV_CAP_BART",  "CAP_BART",     "YES"),  # invader strips cap
    ("INV_CAP_EDNA",  "CAP_EDNA",     "YES"),  # invader strips cap
    # ANTIs should now be FREE (caps stripped)
    ("CAP_BART",      "ANTI_BART",    "NO"),   # cap removed
    ("CAP_EDNA",      "ANTI_EDNA",    "NO"),   # cap removed
    # Cross-interactions that must NOT happen
    ("INV_CAP_BART",  "ON_SLAT",      "NO"),   # wrong invader for ON_SLAT
    ("INV_CAP_EDNA",  "ON_SLAT",      "NO"),   # wrong invader for ON_SLAT
    ("INVADER",       "CAP_BART",     "NO"),   # wrong invader for cap
    ("INVADER",       "CAP_EDNA",     "NO"),   # wrong invader for cap
    ("INV_CAP_BART",  "CAP_EDNA",     "NO"),   # cross-invader
    ("INV_CAP_EDNA",  "CAP_BART",     "NO"),   # cross-invader
    # Invaders should not grab free ANTIs
    ("INVADER",       "ANTI_BART",    "NO"),
    ("INVADER",       "ANTI_EDNA",    "NO"),
    ("INV_CAP_BART",  "ANTI_BART",    "NO"),
    ("INV_CAP_EDNA",  "ANTI_EDNA",    "NO"),
    ("INV_CAP_BART",  "ANTI_EDNA",    "NO"),
    ("INV_CAP_EDNA",  "ANTI_BART",    "NO"),
]
run_workflow_tube("step3_displace", step3_concs, screen_model, step3_pairs)
