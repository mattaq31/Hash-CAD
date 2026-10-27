"""Design complementary libraries with nuad under the criteria of a saved OrthoSeq reference.

Comparison workflow:
    load_case() reads the reference library size, limits, and thermodynamic conditions.
    run_benchmark() builds a fresh nuad design and searches within the association-evaluation budget.
    write_verified_report() independently verifies the best sequences and writes the standard Excel report.

OrthoSeq finds a library whose size emerges from selection. Nuad needs a prescribed molecular design, so we
request exactly the number of complementary pairs found in the reference. The reference sequences are never
used as nuad's starting sequences. This compares feasibility at fixed N, rather than maximum library size.

Nuad owns initialization, mutations, acceptance, result reuse, and scoring. Our callbacks supply the reference
constraints through its public API. Association energies use the repository backend so the energy convention
matches OrthoSeq. Separate self-folding checks are monomer-only NUPACK calculations.

The budget counts association evaluations. Standalone monomer checks are recorded separately, and final
verification is outside the search budget. Native nuad checkpoints remain in raw_nuad/, while nuad.xlsx is
the benchmark's data interface. No custom optimizer or additional thermodynamic cache is introduced here.
"""

from ast import literal_eval
from contextlib import redirect_stdout
from importlib.metadata import version
from itertools import combinations_with_replacement
from pathlib import Path
import os
import re
import sys
import time

import nupack
import nuad.constraints as nc
import nuad.search as ns
import nuad.vienna_nupack as nv

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.energy_computations import compute_nupack_energy
from orthoseq_generator.search_report_reader import load_found_pairs, load_metadata
from orthoseq_generator.search_reporting import (
    build_selected_sequence_data, validate_selected_pairs, verify_selected_pairs, write_hybrid_search_result_xlsx,
)


def load_case(reference_report, seed, association_budget):
    """Build the comparison settings from an existing, verified OrthoSeq Excel report.

    The reference determines N and the physical acceptance criteria. The launcher supplies nuad's seed and
    budget because the short-sequence reference uses a reconstructed dataset cost, while the long references
    have search budgets. This avoids inventing energy limits or confusing those two accounting conventions.

    Return a case dictionary containing the reference path/metadata, target size, motifs, limits, and model
    parameters. The reference's sequences are used only to establish its size, never to initialize nuad.
    """
    reference_report = Path(reference_report).resolve()
    metadata = load_metadata(reference_report)
    if metadata.get("input.fivep_ext") or metadata.get("input.threep_ext"):
        raise ValueError("These three comparisons support extension-free references only.")
    if metadata["nupack.energy_type"] != "total" or metadata["nupack.material"] not in ("dna", "dna04.2"):
        raise ValueError("The reference must use DNA ensemble association energies (total).")
    pair_count = len(load_found_pairs(reference_report))
    if pair_count != metadata["found_pair_count"] or association_budget < 1:
        raise ValueError("Reference pair count must agree with metadata, and the budget must be positive.")
    # With negative energies, on_min is the stronger-binding boundary and on_max the weaker-binding boundary.
    # off_min and self_min are minimum allowed values: a more negative energy violates those constraints.
    return {"reference_report": reference_report, "reference_metadata": metadata, "seed": seed,
            "association_budget": association_budget, "pair_count": pair_count,
            "core_length": int(metadata["input.length"]),
            "forbidden_motifs": literal_eval(metadata["input.unwanted_substrings"]),
            "limits": {"on_min": float(metadata["search.min_ontarget"]),
                       "on_max": float(metadata["search.max_ontarget"]),
                       "off_min": float(metadata["search.offtarget_limit"]),
                       "self_min": float(metadata["search.self_energy_limit"])},
            "nupack_params": {"material": "dna04.2", "energy_type": "total",
                              "celsius": float(metadata["nupack.celsius"]),
                              "sodium": float(metadata["nupack.sodium"]),
                              "magnesium": float(metadata["nupack.magnesium"])}}


def configure_nupack(case):
    """Configure both calculation paths with the same reference model and serial execution.

    The repository helper reads hf's process-local settings. The isolated monomer callback uses the returned
    Model. Set both here so association and self-folding cannot silently use different salts or temperatures.
    ORTHOSEQ_NO_MP also makes the repository's final verification serial. These settings affect this process,
    not the installed conda environment. Avoid running differently configured cases concurrently in one process.
    """
    params = case["nupack_params"]
    hf.set_nupack_params(params["material"], params["celsius"], params["sodium"], params["magnesium"])
    hf.set_energy_type("total")
    nupack.config.threads = 1
    os.environ["ORTHOSEQ_NO_MP"] = "1"
    return nupack.Model(material=params["material"], celsius=params["celsius"],
                        sodium=params["sodium"], magnesium=params["magnesium"])


def create_design(case):
    """Return a fresh nuad Design and the list of its intended complementary strand pairs.

    A DomainPool describes allowed core sequences, rather than a precomputed OrthoSeq candidate library.
    Nuad assigns the initial sequences itself using the search seed. Each pair shares one mutable Domain:
    X uses its sequence and Y uses its starred, reverse-complementary version. Mutating the domain therefore
    updates both partners together and preserves complementarity throughout the search.
    """
    pool = nc.DomainPool(name="cores", length=case["core_length"],
                         numpy_filters=[nc.ForbiddenSubstringFilter(substrings=case["forbidden_motifs"])])
    design = nc.Design()
    pairs = []
    for index in range(case["pair_count"]):
        core = nc.Domain(name=f"core_{index}", pool=pool)
        strand_x = design.add_strand(domains=[core], starred_domain_indices=[], name=f"X_{index}")
        strand_y = design.add_strand(domains=[core], starred_domain_indices=[0], name=f"Y_{index}")
        pairs.append((strand_x, strand_y))
    return design, pairs


def create_constraints(design, pairs, case, model, counts, check_budget):
    """Translate the reference's three energy inequalities into public nuad constraints.

    Each callback receives sequence strings and returns Result(value=energy, excess=positive_violation).
    A satisfied constraint has zero excess. Nuad applies its default cubic transfer function and weight 1,
    so the displayed optimization score is a sum of cubed excesses, not an energy or a violation count.

    counts is the runner's mutable counter dictionary. check_budget stops before the next association
    evaluation exceeds the cap. Counters increase only when a callback actually calculates an energy.
    Nuad may reuse unchanged results or reject a trial before evaluating every constraint.
    """
    limits = case["limits"]
    # Strand names identify intended partners. frozenset makes X/Y and Y/X the same unordered interaction.
    intended = {frozenset((x.name, y.name)) for x, y in pairs}
    # Replacement includes X_i/X_i and Y_i/Y_i homodimers. Exclude only the N intended partner pairs.
    # Among 2N strands there are (2N)(2N+1)/2 unordered dimers, leaving exactly 2N**2 unintended complexes.
    off_pairs = [(x, y) for x, y in combinations_with_replacement(design.strands, 2)
                 if frozenset((x.name, y.name)) not in intended]
    assert len(off_pairs) == 2 * len(pairs) ** 2
    assert sum(x is y for x, y in off_pairs) == 2 * len(pairs)

    def evaluate_on_target(sequences, _):
        """Count one association evaluation and check both ends of the on-target window."""
        # Nuad also passes the associated design part; these callbacks need only its sequence strings.
        check_budget()
        counts["on_target"] += 1
        # One repository call calculates G_XY - G_X - G_Y in a dimer-plus-monomer NUPACK batch.
        # It is one association budget unit, even though the batch evaluates several complexes.
        energy, _, _ = compute_nupack_energy(*sequences, type="total")
        # Penalize either too-strong or too-weak intended binding. Inside the window both terms are nonpositive.
        excess = max(0.0, limits["on_min"] - energy, energy - limits["on_max"])
        return nc.Result(excess=excess, value=energy, unit="kcal/mol")

    def evaluate_off_target(sequences, _):
        """Count one association evaluation and check the off-target minimum."""
        check_budget()
        counts["off_target"] += 1
        energy, _, _ = compute_nupack_energy(*sequences, type="total")
        # For example, energy=-8.20 with off_min=-8.16 has excess 0.04 kcal/mol.
        return nc.Result(excess=max(0.0, limits["off_min"] - energy), value=energy, unit="kcal/mol")

    def evaluate_self(sequences, _):
        """Evaluate the monomer constraint separately, without doing an additional association calculation."""
        counts["self_folding"] += 1
        # The repository association helper exposes monomer energies alongside a dimer calculation.
        # Nuad also needs isolated monomer checks, so calculate only that complex here.
        monomer = nupack.Complex([nupack.Strand(sequences[0], name="X")])
        results = nupack.complex_analysis([monomer], model=model, compute=["pfunc"])
        energy = float(results[monomer].free_energy)
        return nc.Result(excess=max(0.0, limits["self_min"] - energy), value=energy, unit="kcal/mol")

    # Nuad uses these strand/domain relationships to choose which domain to mutate and which results to update.
    # Keep self-folding as a strand constraint and associations as pair constraints so its normal search applies.
    return [nc.StrandConstraint(description="Single-strand ensemble free energy minimum",
                               short_description="self_folding", strands=design.strands,
                               evaluate=evaluate_self, parallel=False),
            nc.StrandPairConstraint(description="On-target association energy window", short_description="on_target",
                                    pairs=pairs, evaluate=evaluate_on_target, parallel=False),
            nc.StrandPairConstraint(description="Off-target association energy minimum", short_description="off_target",
                                    pairs=off_pairs, evaluate=evaluate_off_target, parallel=False)]


def read_search_progress(log_path):
    """Convert nuad's printed iteration rows into records for the standard search_progress sheet.

    The seven columns correspond to our three constraints plus iteration, accepted-update, and score fields.
    This reads displayed values, with nuad's rounding. Row count can include the initial evaluation and is
    recorded as such in the metadata. Per-iteration association counts cannot be reconstructed from this table.
    """
    rows = []
    with Path(log_path).open(encoding="utf-8") as log:
        for line in log:
            if not re.match(r"^\|\s*\d+\s*\|", line):
                continue
            values = [value.strip() for value in line.strip().strip("|").split("|")]
            if len(values) != 7:
                raise ValueError(f"Unexpected nuad progress table: {line}")
            rows.append(dict(zip(("iteration", "update", "opt_score", "new_score", "self_folding",
                                  "on_target", "off_target"), [float(value) for value in values])))
    return rows


def summarize_validation(selected, verified, case):
    """Return standard validation rows and a detailed list of individually violated constraints.

    selected and verified use the existing repository report format. The repository validator supplies the
    usual pass/fail checks, but groups self-folding by complementary pair and off-target conflicts by pair
    combinations. Nuad's constraints and our figure tables count each strand or complex separately.
    Add those individual counts and their energy excesses without replacing the standard validation summary.
    """
    limits = case["limits"]
    checks = validate_selected_pairs(selected, verified, min_ontarget=limits["on_min"],
                                     max_ontarget=limits["on_max"], self_energy_limit=limits["self_min"],
                                     offtarget_limit=limits["off_min"])
    violations = []
    for index, pair in enumerate(selected):
        on = float(verified["on_target_energies"][index])
        excess = max(0.0, limits["on_min"] - on, on - limits["on_max"])
        if excess:
            violations.append({"constraint": "on_target", "strand_1": f"X_{index}", "strand_2": f"Y_{index}",
                               "energy_kcal_mol": on, "excess_kcal_mol": excess})
        for prefix, key in (("X", "self_energy_seqs"), ("Y", "self_energy_rc_seqs")):
            energy = float(verified[key][index])
            if energy < limits["self_min"]:
                violations.append({"constraint": "self_folding", "strand_1": f"{prefix}_{index}",
                                   "strand_2": "", "energy_kcal_mol": energy,
                                   "excess_kcal_mol": limits["self_min"] - energy})
    off = verified["off_target"]
    # HH and AA contain lower triangles including the diagonal. HA has both cross-pair orientations.
    # Read each populated entry once, excluding HA's diagonal because it denotes the intended X_i/Y_i pair.
    for i in range(len(selected)):
        for j in range(len(selected)):
            interactions = [("X", "Y", off["antihandle_handle_energies"][i, j])] if i != j else []
            if j <= i:
                interactions += [("X", "X", off["handle_handle_energies"][i, j]),
                                 ("Y", "Y", off["antihandle_antihandle_energies"][i, j])]
            for x, y, energy in interactions:
                if energy < limits["off_min"]:
                    violations.append({"constraint": "off_target", "strand_1": f"{x}_{i}",
                                       "strand_2": f"{y}_{j}", "energy_kcal_mol": float(energy),
                                       "excess_kcal_mol": float(limits["off_min"] - energy)})
    # Energy checks do not establish complementarity, length, or motif compliance. Check these separately.
    # nv.rc is only a reverse-complement utility; nuad's energy wrappers are not used by this module.
    complement_ok = all(row["rc_seq"] == nv.rc(row["seq"]) for row in selected)
    sequence_ok = all(len(seq) == case["core_length"] and not any(m in seq for m in case["forbidden_motifs"])
                      for row in selected for seq in (row["seq"], row["rc_seq"]))
    checks += [{"check": "all_pairs_complementary", "passed": complement_ok, "value": complement_ok},
               {"check": "all_lengths_and_motifs_valid", "passed": sequence_ok, "value": sequence_ok}]
    for name in ("self_folding", "on_target", "off_target"):
        count = sum(row["constraint"] == name for row in violations)
        checks.append({"check": f"individual_{name}_violations", "passed": count == 0, "value": count})
    return checks, violations


def write_verified_report(sequence_pairs, case, statistics, output_path, progress=None, extra_metadata=None):
    """Independently verify a complete final library and write the repository's standard Excel report.

    sequence_pairs contains the saved best X/Y sequences. Verification recalculates all required energies
    through the existing repository pipeline, without using nuad's cached constraint results or search counters.
    It is deliberately outside the search budget. Failed constraints remain in the report, with no pruning
    or relaxed criteria, so both libraries are compared at the prescribed N.

    statistics supplies the completed search counts and stopping information. A normal nuad return is labelled
    constraints_satisfied only if independent validation agrees. The function updates that stop_reason in place
    and returns (verified_energies, validation_checks, individual_violations).
    """
    configure_nupack(case)
    selected = build_selected_sequence_data(sequence_pairs, list(range(len(sequence_pairs))))
    if len(selected) != case["pair_count"]:
        raise ValueError("Saved design size does not match the reference.")
    verified = verify_selected_pairs(selected, nupack_params=case["nupack_params"])
    checks, violations = summarize_validation(selected, verified, case)
    if statistics["stop_reason"] == "nuad_returned":
        statistics["stop_reason"] = "constraints_satisfied" if all(row["passed"] for row in checks) else "nuad_returned"
    # These extra keys supplement the shared report fields without creating a second output format.
    metadata = {"benchmark_name": "nuad_comparison", "stopped_reason": statistics["stop_reason"],
                "source.reference_report": str(case["reference_report"]),
                "nuad.version": version("nuad"), "nupack.version": version("nupack"),
                "nuad.parallel": False, "nupack.threads": 1,
                "nuad.on_target_calls": statistics["on_target_calls"],
                "nuad.off_target_calls": statistics["off_target_calls"],
                "nuad.separate_self_folding_calls": statistics["separate_self_folding_calls"],
                "nuad.optimization_iterations": statistics["optimization_iterations"],
                "nuad.validated_design_source": statistics["validated_design_source"],
                "nuad.max_iterations": None,
                "counting.convention": "One association-energy evaluation is one budget unit; "
                                       "standalone self-folding and final verification are excluded.",
                "counting.reference_budget_kind": "reconstructed_full_candidate_graph" if case["core_length"] == 6
                                                  else "search_association_budget",
                "validation.individual_violation_count": len(violations),
                "validation.all_checks_passed": all(row["passed"] for row in checks)}
    metadata.update(extra_metadata or {})
    limits = case["limits"]
    # Despite its historical name, this is the repository's shared writer for multiple algorithms.
    write_hybrid_search_result_xlsx(
        output_path, algorithm_name="nuad", selected_sequence_data=selected, verified=verified,
        search_params={"min_ontarget": limits["on_min"], "max_ontarget": limits["on_max"],
                       "offtarget_limit": limits["off_min"], "self_energy_limit": limits["self_min"],
                       "random_seed": case["seed"], "total_nupack_calls": statistics["nupack_calls"],
                       "total_nupack_budget": case["association_budget"],
                       "search_duration_s": statistics["search_wall_seconds"]},
        input_params={"source_kind": "nuad_domain_pool", "length": case["core_length"],
                      "fivep_ext": None, "threep_ext": None, "unwanted_substrings": case["forbidden_motifs"],
                      "apply_unwanted_to": "full"},
        nupack_params=case["nupack_params"], artifact_info={}, generation_data=progress or [],
        validation_data=checks, extra_metadata=metadata, extra_sheets={"constraint_violations": violations})
    counts = tuple(sum(row["constraint"] == name for row in violations)
                   for name in ("self_folding", "on_target", "off_target"))
    print(f"Saved {output_path}; individual self/on/off violations: {counts}", flush=True)
    return verified, checks, violations


def run_benchmark(case, output_dir):
    """Run one fixed-N comparison and return the path to its independently verified Excel report.

    The launcher passes the reference-derived case and a new output directory. Nuad performs the search with
    its default optimizer, stopping normally at satisfaction or through our association-budget callback.
    There is no iteration cap. Save native nuad artifacts separately from the standard benchmark workbook.

    Keep a serialized copy of the best accepted design in memory. A budget exception can interrupt a proposed
    mutation before nuad accepts or reverts it, leaving the live Design in a trial state. Restoring our saved
    design ensures that final verification describes the best accepted library, not the interrupted proposal.
    """
    output_dir = Path(output_dir)
    # An explicit new directory avoids nuad's interactive prompt to clear existing results.
    if output_dir.exists():
        raise FileExistsError(f"Choose a new output directory; existing results are preserved: {output_dir}")
    output_dir.mkdir(parents=True)
    native_dir = output_dir / "raw_nuad"
    native_dir.mkdir()
    # Nuad requires its directory to be empty at startup, so capture stdout in the parent until it finishes.
    log_path = output_dir / "search.log"
    model = configure_nupack(case)
    design, pairs = create_design(case)
    counts = {"on_target": 0, "off_target": 0, "self_folding": 0}
    best = {"json": None, "source": "initial_sequences"}
    progress = {"last_print": time.perf_counter()}
    console = sys.stdout
    started = time.perf_counter()

    def check_budget():
        """Print occasional progress and stop before exceeding the association budget."""
        if best["json"] is None:
            # Nuad has now assigned initial sequences. Keep them in case the cap is reached before an improvement.
            best["json"] = design.to_json()
        total = counts["on_target"] + counts["off_target"]
        now = time.perf_counter()
        if now - progress["last_print"] >= 10:
            # Preserve the full table on disk, but show only its tail so a long run stays readable in PyCharm.
            search_log.flush()
            with log_path.open("rb") as recent:
                recent.seek(max(0, recent.seek(0, 2) - 4096))
                lines = recent.read().decode("utf-8", errors="replace").splitlines()
            for index in range(len(lines) - 1, -1, -1):
                if re.match(r"^\|\s*\d+\s*\|", lines[index]):
                    print("\n".join(lines[max(0, index - 2):index + 1]), file=console, flush=True)
                    break
            print(f"Progress: association evaluations {total:,}/{case['association_budget']:,} "
                  f"({100 * total / case['association_budget']:.2f}%); "
                  f"self-folding checks {counts['self_folding']:,}; elapsed {now - started:.0f}s.",
                  file=console, flush=True)
            progress["last_print"] = now
        # The energy callbacks call this before incrementing a counter or starting the next NUPACK calculation.
        if total >= case["association_budget"]:
            raise StopIteration("association budget exhausted")

    def save_best(_):
        """Retain the latest improvement in memory because a budget stop can interrupt a proposed mutation."""
        # Use the public improvement callback rather than reading nuad's asynchronously written checkpoint files.
        best["json"] = design.to_json()
        best["source"] = "nuad_best_improvement"

    constraints = create_constraints(design, pairs, case, model, counts, check_budget)
    params = ns.SearchParameters(constraints=constraints, random_seed=case["seed"], max_iterations=None,
                                 out_directory=str(native_dir), scrolling_output=True, info_log_file=True,
                                 on_improved_design=save_best)
    print(f"Running nuad: {case['pair_count']} pairs of {case['core_length']} nt; seed {case['seed']}; "
          f"budget {case['association_budget']:,}. Output: {output_dir}", flush=True)
    stop_reason = "nuad_returned"
    old_handlers = tuple(nc.logger.handlers)
    try:
        with log_path.open("w", encoding="utf-8") as search_log:
            with redirect_stdout(search_log):
                ns.search_for_sequences(design, params)
    except StopIteration as error:
        if str(error) != "association budget exhausted":
            raise
        stop_reason = "association_call_budget"
        design = nc.Design.from_json(best["json"])
    finally:
        # A constraint exception bypasses nuad's normal logger cleanup. Close only handlers added by this run,
        # preserving unrelated handlers and avoiding duplicate logs when rerunning in the same PyCharm console.
        for handler in tuple(nc.logger.handlers):
            if handler not in old_handlers:
                nc.logger.removeHandler(handler)
                handler.close()
    # Finish search accounting before independent verification adds more thermodynamic calculations.
    search_seconds = time.perf_counter() - started
    log_path.replace(native_dir / "search.log")
    strands = {strand.name: strand.sequence() for strand in design.strands}
    sequence_pairs = [(strands[f"X_{i}"], strands[f"Y_{i}"]) for i in range(case["pair_count"])]
    # Keep the exact report source in nuad's native format, separate from the benchmark data interface.
    (native_dir / "design_reported.json").write_text(design.to_json(), encoding="utf-8")
    rows = read_search_progress(native_dir / "search.log")
    statistics = {"nupack_calls": counts["on_target"] + counts["off_target"],
                  "on_target_calls": counts["on_target"], "off_target_calls": counts["off_target"],
                  "separate_self_folding_calls": counts["self_folding"], "optimization_iterations": len(rows),
                  "search_wall_seconds": search_seconds, "stop_reason": stop_reason,
                  "validated_design_source": best["source"] if stop_reason == "association_call_budget"
                                             else "nuad_final_design"}
    print("Search finished. Verifying the final sequences through the repository workflow...", flush=True)
    verified, checks, violations = write_verified_report(sequence_pairs, case, statistics, output_dir / "nuad.xlsx",
                                                         progress=rows)
    print(f"Finished: {statistics['stop_reason']}; validation "
          f"{'PASSED' if all(r['passed'] for r in checks) else 'FAILED'}.")
    return output_dir / "nuad.xlsx"
