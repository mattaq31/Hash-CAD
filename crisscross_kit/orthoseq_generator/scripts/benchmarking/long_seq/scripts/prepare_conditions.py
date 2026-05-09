#!/usr/bin/env python3
"""
Purpose:
    Prepare one batch of long-sequence benchmark conditions from a TOML config.

    The script loops over the requested sequence lengths and 5' extensions,
    samples live sequence pairs, estimates the on-target energy window from
    the sigma strategy, derives off-target and self-energy limits from
    physically interpreted fraction targets, and then writes:

    - one batch summary TOML
    - one condition TOML per off-target target
    - one Slurm script per generated run TOML
    - one submit-all shell script
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
import random
import sys
import tomllib

import numpy as np

PACKAGE_DIR = Path(__file__).resolve().parents[5]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import sequence_computations as sc

R_KCAL = 1.98720425864083e-3
RHO_H2O = 55.14


def toml_literal(value) -> str:
    """
    Serialize a small Python value into a TOML literal.

    This helper keeps the generated condition files and batch summary files
    self-contained without introducing another TOML-writing dependency.

    :param value: Primitive value to serialize. Supported inputs are `bool`,
                  `int`, `float`, `str`, and nested `list` / `tuple`
                  containers built from those types.
    :type value: object

    :returns: TOML-compatible literal text.
    :rtype: str
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(toml_literal(item) for item in value) + "]"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def _solve_ab_equilibrium(a0: float, b0: float, kc: float) -> float:
    """
    Solve the symmetric bimolecular binding equilibrium for AB concentration.

    This is the low-level physics helper used by
    `fraction_bound_from_dg(...)`. It converts total initial concentrations
    and an equilibrium constant into the equilibrium concentration of the
    bound complex.

    :param a0: Initial concentration of strand A in molar units.
    :type a0: float

    :param b0: Initial concentration of strand B in molar units.
    :type b0: float

    :param kc: Concentration-scale equilibrium constant for `A + B <-> AB`.
    :type kc: float

    :returns: Equilibrium concentration of `AB` in molar units.
    :rtype: float
    """
    a = kc
    b = -(kc * (a0 + b0) + 1.0)
    c = kc * a0 * b0
    disc = max(b * b - 4.0 * a * c, 0.0)
    return (-b - math.sqrt(disc)) / (2.0 * a)


def fraction_bound_from_dg(dg_assoc: float, conc_m: float, temp_c: float) -> float:
    """
    Convert an association free energy into fraction bound.

    In the long-seq prep workflow this is the forward physics map used to
    derive off-target thresholds from user-facing binding fractions. It is
    paired with `dg_from_fraction_bound(...)`, which numerically inverts this
    relationship.

    :param dg_assoc: Association free energy in kcal/mol.
    :type dg_assoc: float

    :param conc_m: Strand concentration in molar units.
    :type conc_m: float

    :param temp_c: Temperature in degrees Celsius.
    :type temp_c: float

    :returns: Fraction of strand present in the bound complex, clamped to
              `[0, 1]`.
    :rtype: float
    """
    if conc_m <= 0.0:
        return 0.0
    rt = R_KCAL * (273.15 + temp_c)
    kx = math.exp(-dg_assoc / rt)
    kc = kx / RHO_H2O
    ab = _solve_ab_equilibrium(conc_m, conc_m, kc)
    return max(min(ab / conc_m, 1.0), 0.0)


def dg_from_fraction_bound(target_fraction_bound: float, conc_m: float, temp_c: float) -> float:
    """
    Invert the binding model to obtain a free-energy cutoff.

    This is used during preparation to turn physically interpretable target
    off-target binding fractions into the `offtarget_limit` values written to
    the generated condition TOMLs.

    :param target_fraction_bound: Desired bound fraction for an off-target
                                  interaction. Must lie in `(0, 1)`.
    :type target_fraction_bound: float

    :param conc_m: Strand concentration in molar units.
    :type conc_m: float

    :param temp_c: Temperature in degrees Celsius.
    :type temp_c: float

    :returns: Association free energy in kcal/mol that yields the requested
              bound fraction under the specified conditions.
    :rtype: float
    """
    if not 0.0 < target_fraction_bound < 1.0:
        raise ValueError("target_fraction_bound must be between 0 and 1.")

    low = -60.0
    high = 0.0
    for _ in range(120):
        mid = 0.5 * (low + high)
        frac = fraction_bound_from_dg(mid, conc_m, temp_c)
        if frac > target_fraction_bound:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def self_energy_limit_from_unpaired_fraction(target_unpaired_fraction: float, temp_c: float) -> float:
    """
    Convert a target unpaired fraction into a self-energy threshold.

    In the prep workflow this defines `self_energy_limit` from a physical
    design rule such as "at least 20% unpaired".

    :param target_unpaired_fraction: Minimum desired unpaired fraction, in
                                     `(0, 1]`.
    :type target_unpaired_fraction: float

    :param temp_c: Temperature in degrees Celsius.
    :type temp_c: float

    :returns: Self-energy cutoff in kcal/mol.
    :rtype: float
    """
    if not 0.0 < target_unpaired_fraction <= 1.0:
        raise ValueError("target_unpaired_fraction must be in (0, 1].")
    rt = R_KCAL * (273.15 + temp_c)
    return rt * math.log(target_unpaired_fraction)


def slugify_float(value: float) -> str:
    """
    Convert a float into a filesystem-friendly token.

    This is used for family names, batch names, generated TOML names, and
    generated Slurm script names so the benchmark artifacts remain stable and
    shell-friendly.

    :param value: Float to encode.
    :type value: float

    :returns: String with `- -> m` and `. -> p`.
    :rtype: str
    """
    return str(value).replace("-", "m").replace(".", "p")


def family_tag(length: int, fivep_ext: str, threep_ext: str, range_sigma: float, seed: int) -> str:
    """
    Build the folder name for one physical condition family.

    A family groups all off-target fraction settings that share the same
    sequence length, flanks, sigma calibration rule, and random seed.

    :param length: Core sequence length.
    :type length: int

    :param fivep_ext: 5' extension string. Empty string is rendered as
                      `none`.
    :type fivep_ext: str

    :param threep_ext: 3' extension string. Empty string is rendered as
                       `none`.
    :type threep_ext: str

    :param range_sigma: Sigma multiplier used to derive the on-target window.
    :type range_sigma: float

    :param seed: Random seed used for sequence sampling.
    :type seed: int

    :returns: Stable family folder name.
    :rtype: str
    """
    fivep_label = fivep_ext if fivep_ext else "none"
    threep_label = threep_ext if threep_ext else "none"
    sigma_label = slugify_float(range_sigma)
    return f"len{length}_5p_{fivep_label}_3p_{threep_label}_sigma{sigma_label}_seed{seed}"


def batch_tag(batch_name: str, range_sigma: float, seed: int) -> str:
    """
    Build the top-level generated batch folder name.

    :param batch_name: Human-readable batch prefix from the prep config.
    :type batch_name: str

    :param range_sigma: Sigma multiplier used for calibration.
    :type range_sigma: float

    :param seed: Random seed used for sampling.
    :type seed: int

    :returns: Stable batch folder name.
    :rtype: str
    """
    sigma_label = slugify_float(range_sigma)
    return f"{batch_name}_sigma{sigma_label}_seed{seed}"


def write_text(path: Path, text: str) -> None:
    """
    Write ASCII text to disk, creating parent folders as needed.

    :param path: Target file path.
    :type path: pathlib.Path

    :param text: File contents to write.
    :type text: str

    :returns: None
    :rtype: None
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="ascii")


def build_run_toml(
    *,
    run_cfg: dict,
    nupack_cfg: dict,
    naive_cfg: dict,
    hybrid_cfg: dict,
    output_dir: str,
    min_ontarget: float,
    max_ontarget: float,
    offtarget_limit: float,
    self_energy_limit: float,
) -> str:
    """
    Build one generated long-seq condition TOML.

    The resulting file is consumed directly by both
    `run_long_seq_naive_search.py` and `run_long_seq_hybrid_search.py`. It
    contains shared run metadata plus both the `[naive]` and `[hybrid]`
    parameter sections so one physical condition is represented by one file.

    :param run_cfg: Per-condition run settings such as length, flanks,
                    random seed, and total NUPACK budget.
    :type run_cfg: dict

    :param nupack_cfg: Shared NUPACK chemistry settings.
    :type nupack_cfg: dict

    :param naive_cfg: Naive-search runner settings written into the `[naive]`
                      section.
    :type naive_cfg: dict

    :param hybrid_cfg: Hybrid-search runner settings written into the
                       `[hybrid]` section.
    :type hybrid_cfg: dict

    :param output_dir: Relative output directory written into the `[output]`
                       section.
    :type output_dir: str

    :param min_ontarget: Lower bound of the calibrated on-target window.
    :type min_ontarget: float

    :param max_ontarget: Upper bound of the calibrated on-target window.
    :type max_ontarget: float

    :param offtarget_limit: Derived off-target energy cutoff for one target
                            bound fraction.
    :type offtarget_limit: float

    :param self_energy_limit: Derived self-energy cutoff from the target
                              unpaired fraction.
    :type self_energy_limit: float

    :returns: Full TOML file contents.
    :rtype: str
    """
    lines = [
        "[run]",
        f"length = {toml_literal(int(run_cfg['length']))}",
        f"fivep_ext = {toml_literal(str(run_cfg.get('fivep_ext', '')))}",
        f"threep_ext = {toml_literal(str(run_cfg.get('threep_ext', '')))}",
        f"unwanted_substrings = {toml_literal(list(run_cfg.get('unwanted_substrings', [])))}",
        f"apply_unwanted_to = {toml_literal(str(run_cfg.get('apply_unwanted_to', 'core')))}",
        f"random_seed = {toml_literal(int(run_cfg['random_seed']))}",
        f"min_ontarget = {toml_literal(float(min_ontarget))}",
        f"max_ontarget = {toml_literal(float(max_ontarget))}",
        f"offtarget_limit = {toml_literal(float(offtarget_limit))}",
        f"self_energy_limit = {toml_literal(float(self_energy_limit))}",
        f"total_nupack_budget = {toml_literal(int(run_cfg['total_nupack_budget']))}",
        "",
        "[nupack]",
        f"material = {toml_literal(str(nupack_cfg['material']))}",
        f"celsius = {toml_literal(float(nupack_cfg['celsius']))}",
        f"sodium = {toml_literal(float(nupack_cfg['sodium']))}",
        f"magnesium = {toml_literal(float(nupack_cfg['magnesium']))}",
        "",
        "[output]",
        f"dir = {toml_literal(output_dir)}",
        "",
        "[naive]",
        f"progress_every = {toml_literal(int(naive_cfg.get('progress_every', 250)))}",
        "",
        "[hybrid]",
        f"initial_fresh_pair_count = {toml_literal(int(hybrid_cfg['initial_fresh_pair_count']))}",
        f"generations = {toml_literal(int(hybrid_cfg['generations']))}",
        f"allowed_violations = {toml_literal(int(hybrid_cfg['allowed_violations']))}",
        f"fresh_pair_search_budget = {toml_literal(int(hybrid_cfg['fresh_pair_search_budget']))}",
        f"prune_fraction = {toml_literal(float(hybrid_cfg['prune_fraction']))}",
        f"fresh_pair_scale = {toml_literal(float(hybrid_cfg['fresh_pair_scale']))}",
        f"vc_max_iterations = {toml_literal(int(hybrid_cfg['vc_max_iterations']))}",
        "",
    ]
    return "\n".join(lines)


def build_server_script(
    *,
    job_name: str,
    runner_relpath: str,
    config_relpath: str,
    server_cfg: dict,
) -> str:
    """
    Build one `sbatch` wrapper script for a generated condition.

    Each generated condition TOML gets two wrappers: one for the naive live
    runner and one for the hybrid live runner. The wrappers differ only in the
    runner entrypoint and Slurm job name.

    :param job_name: Slurm job name.
    :type job_name: str

    :param runner_relpath: Repo-relative path to the Python runner script.
    :type runner_relpath: str

    :param config_relpath: Repo-relative path to the generated condition TOML.
    :type config_relpath: str

    :param server_cfg: Server settings loaded from the prep config, including
                       Slurm resource requests and environment activation
                       commands.
    :type server_cfg: dict

    :returns: Shell script contents ready to be written to disk.
    :rtype: str
    """
    lines = [
        "#!/bin/bash",
        f"#SBATCH -J {job_name}",
        f"#SBATCH -c {int(server_cfg['cpus'])}",
        f"#SBATCH --mem={server_cfg['memory']}",
        f"#SBATCH -t {server_cfg['time']}",
        f"#SBATCH -p {server_cfg['partition']}",
    ]
    email = str(server_cfg.get("email", "")).strip()
    if email:
        lines.append("#SBATCH --mail-type=FAIL")
        lines.append(f"#SBATCH --mail-user={email}")
    lines.extend(
        [
            "",
            f"module load {server_cfg['module_load']}",
            f"conda activate {server_cfg['conda_env']}",
            f'PROJECT_ROOT="{server_cfg["project_root"]}"',
            f'python -u "$PROJECT_ROOT/{runner_relpath}" --config "$PROJECT_ROOT/{config_relpath}"',
            "",
        ]
    )
    return "\n".join(lines)


def write_batch_summary_toml(path: Path, *, header: dict, conditions: list[dict]) -> None:
    """
    Write one summary file describing the generated batch.

    This file documents the calibration inputs and the derived cutoffs for
    every generated condition. It is meant as a lightweight record of what the
    preparation step produced.

    :param path: Output path for the summary TOML.
    :type path: pathlib.Path

    :param header: Batch-level metadata shared by all generated conditions.
    :type header: dict

    :param conditions: List of per-condition summary rows.
    :type conditions: list[dict]

    :returns: None
    :rtype: None
    """
    lines = []
    for key, value in header.items():
        lines.append(f"{key} = {toml_literal(value)}")
    lines.append("")
    for row in conditions:
        lines.append("[[conditions]]")
        for key, value in row.items():
            lines.append(f"{key} = {toml_literal(value)}")
        lines.append("")
    write_text(path, "\n".join(lines).rstrip() + "\n")


def sample_on_target_data(registry, sample_size: int):
    """
    Sample unique live pairs and compute their on-target energies.

    This is the calibration step that estimates the on-target energy
    distribution for one `(length, 5' extension, 3' extension)` family before
    the benchmark condition TOMLs are generated.

    :param registry: `SequencePairRegistry` providing live candidate pairs.
    :type registry: object

    :param sample_size: Number of unique sequence pairs to sample.
    :type sample_size: int

    :returns: Sample records containing pair identifiers and computed
              on-target / self-energy values. The preparation step uses the
              on-target values to derive `min_ontarget` and `max_ontarget`.
    :rtype: list[dict]
    """
    rows = []
    seen_pair_ids = set()
    while len(rows) < sample_size:
        pair_id, (seq, rc_seq) = registry.sample_pair()
        if pair_id in seen_pair_ids:
            continue
        seen_pair_ids.add(pair_id)
        result = sc.compute_nupack_energy(seq, rc_seq, type="total")
        if not isinstance(result, tuple):
            continue
        on_energy, self_e_seq, self_e_rc = result
        rows.append(
            {
                "pair_id": int(pair_id),
                "seq": seq,
                "rc_seq": rc_seq,
                "on_target_energy": float(on_energy),
                "self_energy_seq": float(self_e_seq),
                "self_energy_rc_seq": float(self_e_rc),
            }
        )
    return rows


def main():
    """
    Generate one batch of long-seq benchmark conditions from a prep config.

    Workflow
    --------
    1. Read the batch definition from `--config`.
    2. Loop over all requested sequence lengths and 5' extensions.
    3. Sample live on-target energies for each family and derive the sigma
       window.
    4. Convert target off-target bound fractions into energy cutoffs.
    5. Convert the target unpaired fraction into `self_energy_limit`.
    6. Write one condition TOML and two `sbatch` scripts per off-target level.
    7. Write one batch summary TOML and one `submit_all.sh`.

    :returns: None
    :rtype: None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        required=True,
        help="Path to TOML prep config file.",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    with config_path.open("rb") as fh:
        cfg = tomllib.load(fh)

    run_cfg = cfg["run"]
    nupack_cfg = cfg["nupack"]
    prep_cfg = cfg["prep"]
    physics_cfg = cfg["physics"]
    budget_cfg = cfg["budget"]
    naive_cfg = cfg.get("naive", {})
    hybrid_cfg = cfg["hybrid"]
    server_cfg = cfg["server"]

    random_seed = int(run_cfg["random_seed"])
    random.seed(random_seed)

    lengths = [int(x) for x in run_cfg["lengths"]]
    fivep_exts = [str(x) for x in run_cfg["fivep_exts"]]
    threep_ext = str(run_cfg.get("threep_ext", ""))
    unwanted_substrings = list(run_cfg.get("unwanted_substrings", []))
    apply_unwanted_to = str(run_cfg.get("apply_unwanted_to", "core"))

    hf.set_nupack_params(
        material=str(nupack_cfg["material"]),
        celsius=float(nupack_cfg["celsius"]),
        sodium=float(nupack_cfg["sodium"]),
        magnesium=float(nupack_cfg["magnesium"]),
    )

    sample_size = int(prep_cfg["sample_size"])
    range_sigma = float(prep_cfg["range_sigma"])
    batch_name = str(prep_cfg.get("name", "long_seq_batch"))
    conc_nm = float(physics_cfg["strand_concentration_nM"])
    conc_m = conc_nm * 1e-9
    target_bound_fractions = [float(x) for x in physics_cfg["offtarget_target_bound_fractions"]]
    target_unpaired_fraction = float(physics_cfg["self_target_unpaired_fraction"])

    benchmark_root = Path(__file__).resolve().parents[1]
    batch_dir_name = batch_tag(batch_name, range_sigma, random_seed)
    config_root = benchmark_root / "configs" / "generated" / batch_dir_name

    config_root.mkdir(parents=True, exist_ok=True)

    print(f"Prep config: {config_path}")
    print(f"Prep batch: {batch_dir_name}")

    self_energy_limit = self_energy_limit_from_unpaired_fraction(
        target_unpaired_fraction,
        float(nupack_cfg["celsius"]),
    )

    runner_rel_naive = (
        "crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/"
        "run_long_seq_naive_search.py"
    )
    runner_rel_hybrid = (
        "crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/scripts/"
        "run_long_seq_hybrid_search.py"
    )
    generated_job_scripts = []
    summary_rows = []

    for length in lengths:
        for fivep_ext in fivep_exts:
            tag = family_tag(length, fivep_ext, threep_ext, range_sigma, random_seed)
            config_dir = config_root / tag
            config_dir.mkdir(parents=True, exist_ok=True)

            registry = sc.SequencePairRegistry(
                length=length,
                fivep_ext=fivep_ext,
                threep_ext=threep_ext,
                unwanted_substrings=unwanted_substrings,
                apply_unwanted_to=apply_unwanted_to,
                seed=random_seed,
                preselected_cores=None,
            )

            print(f"Sampling {sample_size} unique sequence pairs for {tag}...")
            sampled_rows = sample_on_target_data(registry, sample_size)
            on_target_values = np.array([row["on_target_energy"] for row in sampled_rows], dtype=float)
            mean_on = float(np.mean(on_target_values))
            std_on = float(np.std(on_target_values))
            window_delta = float(range_sigma) * std_on
            min_on = mean_on - window_delta
            max_on = mean_on

            output_rel_dir = f"data/len{length}/" + (f"5p_{fivep_ext}" if fivep_ext else "5p_none")
            run_base_cfg = {
                "length": length,
                "fivep_ext": fivep_ext,
                "threep_ext": threep_ext,
                "unwanted_substrings": unwanted_substrings,
                "apply_unwanted_to": apply_unwanted_to,
                "random_seed": random_seed,
                "total_nupack_budget": int(budget_cfg["total_nupack_budget"]),
            }

            for target_fraction in target_bound_fractions:
                offtarget_limit = dg_from_fraction_bound(
                    target_fraction,
                    conc_m,
                    float(nupack_cfg["celsius"]),
                )
                frac_label = slugify_float(target_fraction)
                run_toml_text = build_run_toml(
                    run_cfg=run_base_cfg,
                    nupack_cfg=nupack_cfg,
                    naive_cfg=naive_cfg,
                    hybrid_cfg=hybrid_cfg,
                    output_dir=output_rel_dir,
                    min_ontarget=min_on,
                    max_ontarget=max_on,
                    offtarget_limit=offtarget_limit,
                    self_energy_limit=self_energy_limit,
                )

                condition_toml_rel = (
                    "crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/"
                    f"configs/generated/{batch_dir_name}/{tag}/condition_fb{frac_label}.toml"
                )
                condition_toml_path = config_dir / f"condition_fb{frac_label}.toml"
                write_text(condition_toml_path, run_toml_text)

                naive_job_name = f"ls_naive_l{length}_fb{frac_label}"
                hybrid_job_name = f"ls_hybrid_l{length}_fb{frac_label}"
                naive_script_path = config_dir / f"naive_fb{frac_label}.sh"
                hybrid_script_path = config_dir / f"hybrid_fb{frac_label}.sh"
                write_text(
                    naive_script_path,
                    build_server_script(
                        job_name=naive_job_name,
                        runner_relpath=runner_rel_naive,
                        config_relpath=condition_toml_rel,
                        server_cfg=server_cfg,
                    ),
                )
                write_text(
                    hybrid_script_path,
                    build_server_script(
                        job_name=hybrid_job_name,
                        runner_relpath=runner_rel_hybrid,
                        config_relpath=condition_toml_rel,
                        server_cfg=server_cfg,
                    ),
                )
                generated_job_scripts.extend(
                    [
                        f"{tag}/{naive_script_path.name}",
                        f"{tag}/{hybrid_script_path.name}",
                    ]
                )
                summary_rows.append(
                    {
                        "family_tag": tag,
                        "length": length,
                        "fivep_ext": fivep_ext,
                        "threep_ext": threep_ext,
                        "target_fraction_bound": float(target_fraction),
                        "derived_offtarget_limit": float(offtarget_limit),
                        "min_ontarget": float(min_on),
                        "max_ontarget": float(max_on),
                        "self_energy_limit": float(self_energy_limit),
                        "sampled_mean_ontarget": float(mean_on),
                        "sampled_std_ontarget": float(std_on),
                        "output_rel_dir": output_rel_dir,
                        "condition_toml": str(condition_toml_path),
                        "naive_sbatch": str(naive_script_path),
                        "hybrid_sbatch": str(hybrid_script_path),
                    }
                )
                print(
                    f"{tag}: fb={target_fraction:.4f} -> offtarget_limit={offtarget_limit:.4f}"
                )

    submit_lines = [
        "#!/bin/bash",
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
        'cd "$SCRIPT_DIR"',
        "",
    ]
    for script_name in generated_job_scripts:
        submit_lines.append(f"sbatch {script_name}")
    submit_lines.append("")
    write_text(config_root / "submit_all.sh", "\n".join(submit_lines))

    write_batch_summary_toml(
        config_root / "batch_summary.toml",
        header={
            "source_prep_config": str(config_path),
            "batch_name": batch_name,
            "batch_dir_name": batch_dir_name,
            "lengths": lengths,
            "fivep_exts": fivep_exts,
            "threep_ext": threep_ext,
            "range_sigma": range_sigma,
            "sample_size": sample_size,
            "strand_concentration_nM": conc_nm,
            "offtarget_target_bound_fractions": target_bound_fractions,
            "self_target_unpaired_fraction": target_unpaired_fraction,
            "self_energy_limit": float(self_energy_limit),
        },
        conditions=summary_rows,
    )

    print(f"Wrote generated TOMLs to: {config_root}")
    print(f"Wrote sbatch scripts to: {config_root}")


if __name__ == "__main__":
    main()
