"""
nupack_benchmark_two_modes.py

Single-file benchmark runner for two NUPACK baselines:

MODE = "tube"    -> tube_design with concentrations + off-target enumeration
MODE = "complex" -> complex_design without concentrations + explicit unwanted complexes

Minimal progress printing:
- Uses NUPACK checkpointing (interval=checkpoint_interval_s)
- Polls current_results() and prints ensemble_defect for each trial
- Lets NUPACK decide when to stop (DesignOptions max_time / f_stop / internal)

After design, runs your existing analysis:
- build pairs [(plus_i, minus_i), ...]
- compute on/off-target energies
- plot histogram PDF

Requires:
- nupack
- orthoseq_generator.helper_functions as hf
- orthoseq_generator.sequence_computations as sc
"""

import os
import time
from nupack import *
import shutil

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc


def run_with_progress(job, *, trials=1, checkpoint_base="nupack_chk",
                      checkpoint_interval_s=20, poll_interval_s=5):

    script_dir = os.path.dirname(os.path.abspath(__file__))
    chk_root = os.path.join(script_dir, checkpoint_base)
    os.makedirs(chk_root, exist_ok=True)

    checkpoint_dir = os.path.join(chk_root, f"run_{int(time.time())}")
    os.makedirs(checkpoint_dir, exist_ok=True)

    running = job.launch(trials=trials, checkpoint=checkpoint_dir, interval=checkpoint_interval_s)

    while True:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")

        current = running.current_results()

        bits = []
        for i, res in enumerate(current):
            if res is None:
                bits.append(f"t{i}:...")
            else:
                f = float(res.defects.ensemble_defect)
                bits.append(f"t{i}:{f:.3g}")
        print(f"[{now}] " + " | ".join(bits))

        finals = running.final_results()
        if all(r is not None for r in finals):
            print(f"[{now}] finished")
            return finals, checkpoint_dir

        time.sleep(poll_interval_s)


def make_model(p):
    return Model(
        material=p["material"],
        celsius=p["celsius"],
        sodium=p["sodium"],
        magnesium=p["magnesium"],
    )


def build_domains_and_strands(n_pairs, length):
    domains = [Domain("N" * length, name=f"d{i+1}") for i in range(n_pairs)]
    plus = [TargetStrand([domains[i]], name=f"s{i+1}") for i in range(n_pairs)]
    minus = [TargetStrand([~domains[i]], name=f"t{i+1}") for i in range(n_pairs)]
    return domains, plus, minus


def get_best_result(results):
    good = [r for r in results if r is not None]
    if not good:
        raise RuntimeError("No successful trial result produced (all trials returned None).")
    return min(good, key=lambda r: float(r.defects.ensemble_defect))


def design_tube(p):
    model = make_model(p)
    options_kwargs = dict(seed=p["seed"], f_stop=p["f_stop"], max_time=p["max_time"])
    if p["use_extra_options"]:
        options_kwargs.update(dict(M_bad=p["M_bad"], M_reseed=p["M_reseed"], M_reopt=p["M_reopt"]))
    options = DesignOptions(**options_kwargs)

    domains, plus, minus = build_domains_and_strands(p["n_pairs"], p["length"])

    duplexes = [
        TargetComplex([plus[i], minus[i]], f"D{p['length']}+", name=f"duplex{i+1}")
        for i in range(p["n_pairs"])
    ]

    tube = TargetTube(
        on_targets={duplexes[i]: p["conc"] for i in range(p["n_pairs"])},
        off_targets=SetSpec(max_size=2),
        name="crosstalk",
    )

    soft_constraints = []
    if p["use_energy_match"]:
        soft_constraints.append(EnergyMatch(domains, energy_ref=p["energy_ref"], weight=p["energy_weight"]))

    job = tube_design(
        tubes=[tube],
        model=model,
        options=options,
        soft_constraints=soft_constraints,
    )

    results , chk_dir = run_with_progress(
        job,
        trials=p["trials"],
        checkpoint_base=p["checkpoint_base"],
        checkpoint_interval_s=p["checkpoint_interval_s"],
        poll_interval_s=p["poll_interval_s"],
    )

    best = get_best_result(results)
    plus_seqs = {s.name: str(best.to_analysis(s)) for s in plus}
    minus_seqs = {t.name: str(best.to_analysis(t)) for t in minus}
    return best, plus_seqs, minus_seqs, chk_dir


def design_complex(p):
    model = make_model(p)

    options_kwargs = dict(seed=p["seed"], f_stop=p["f_stop"], max_time=p["max_time"])
    if p["use_extra_options"]:
        options_kwargs.update(dict(M_bad=p["M_bad"], M_reseed=p["M_reseed"], M_reopt=p["M_reopt"]))
    options = DesignOptions(**options_kwargs)

    domains, plus, minus = build_domains_and_strands(p["n_pairs"], p["length"])

    on_struct = f"D{p['length']}+"
    off_struct = "." * p["length"] + "+" + "." * p["length"]

    complexes = []
    for i in range(p["n_pairs"]):
        complexes.append(TargetComplex([plus[i], minus[i]], on_struct, name=f"on_{i+1}"))

    if p["include_mismatched_heterodimers"]:
        for i in range(p["n_pairs"]):
            for j in range(p["n_pairs"]):
                if i != j:
                    complexes.append(TargetComplex([plus[i], minus[j]], off_struct, name=f"off_s{i+1}_t{j+1}"))

    if p["include_homodimers"]:
        for i in range(p["n_pairs"]):
            for j in range(i + 1, p["n_pairs"]):
                complexes.append(TargetComplex([plus[i], plus[j]], off_struct, name=f"off_s{i+1}_s{j+1}"))
                complexes.append(TargetComplex([minus[i], minus[j]], off_struct, name=f"off_t{i+1}_t{j+1}"))

    soft_constraints = []
    if p["use_energy_match"]:
        soft_constraints.append(EnergyMatch(domains, energy_ref=p["energy_ref"], weight=p["energy_weight"]))

    job = complex_design(
        complexes=complexes,
        model=model,
        options=options,
        soft_constraints=soft_constraints,
    )

    results, chk_dir = run_with_progress(
        job,
        trials=p["trials"],
        checkpoint_base=p["checkpoint_base"],
        checkpoint_interval_s=p["checkpoint_interval_s"],
        poll_interval_s=p["poll_interval_s"],
    )

    best = get_best_result(results)
    plus_seqs = {s.name: str(best.to_analysis(s)) for s in plus}
    minus_seqs = {t.name: str(best.to_analysis(t)) for t in minus}
    return best, plus_seqs, minus_seqs, chk_dir


def run_analysis(plus, minus, *, output_path="energy_hist_nupack_only.pdf"):
    pairs = []
    for i in range(1, len(plus) + 1):
        pairs.append((plus[f"s{i}"], minus[f"t{i}"]))

    print(pairs)

    hf.choose_precompute_library("my_new_cache.pkl")
    hf.USE_LIBRARY = False

    on_e = sc.compute_ontarget_energies(pairs)
    off_e = sc.compute_offtarget_energies(pairs)

    stats = sc.plot_on_off_target_histograms(on_e, off_e, output_path=output_path)
    print(stats)


if __name__ == "__main__":
    # =======================
    # ONE KNOB BLOCK
    # =======================
    MODE = "tube"  # "tube" or "complex"
    MODE = "complex"

    P = {
        # shared
        "n_pairs": 10,
        "length": 7,
        "material": "dna",
        "celsius": 37,
        "sodium": 0.05,
        "magnesium": 0.025,

        "seed": 1,
        "f_stop": 0.03,
        "max_time": 300,
        "trials": 1,

        "checkpoint_base": "nupack_chk",
        "checkpoint_interval_s": 10,
        "poll_interval_s": 5,

        "use_energy_match": True,
        "energy_ref": -10.0,
        "energy_weight": 0.6,

        # tube-only
        "conc": 1e-4,

        # complex-only
        "include_mismatched_heterodimers": True,
        "include_homodimers": True,

        # extra optimizer options (complex-only, optional)
        "use_extra_options": True,
        "M_bad": 3000,
        "M_reseed": 300,
        "M_reopt": 20,
    }

    if MODE == "tube":
        best, plus, minus, chk_dir = design_tube(P)
    elif MODE == "complex":
        best, plus, minus, chk_dir= design_complex(P)
    else:
        raise ValueError("MODE must be 'tube' or 'complex'")

    print("\nBest defect:", float(best.defects.ensemble_defect))

    print("\nPlus:")
    for k, v in plus.items():
        print(k, v)

    print("\nMinus:")
    for k, v in minus.items():
        print(k, v)

    run_analysis(plus, minus, output_path="energy_hist_nupack_only.pdf")
    import shutil

    shutil.rmtree(chk_dir, ignore_errors=True)

