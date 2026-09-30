"""Generate O2 comparison TOMLs, Slurm wrappers and submit_all.sh for the 37 C dataset."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from orthoseq_generator.scripts.benchmarking.long_seq.scripts.prepare_conditions import (
    build_server_script,
    toml_literal,
)


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    project_dir = Path(__file__).resolve().parents[5]
    experiment_name = "gmin_gmax_37C"
    lengths = [8, 9, 10, 12, 14, 16, 18, 20, 25]
    init_counts = [250, 450, 900]
    random_seeds = list(range(10))
    prune_fraction = 0.2
    algorithms = [
        "gmin_random", "gmin_rule", "gmin_rank", "gmax_random", "gmax_rule", "gmax_rank",
        "gmin_random_iterative", "gmin_rule_iterative", "gmin_rank_iterative",
        "gmax_random_iterative", "gmax_rule_iterative", "gmax_rank_iterative",
    ]
    batches = [("batch_x_TTTT_sigma1p0_seed41", "5p_TTTT"), ("batch_x______sigma1p0_seed41", "5p_none")]
    server_cfg = {
        "cpus": 1, "memory": "16G", "time": "5-00:00:00", "partition": "medium",
        "module_load": "conda/miniforge3/24.11.3-0", "conda_env": "cc",
    }
    data_dir = project_dir / "crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/data"
    config_dir = script_dir / "configs" / "generated" / experiment_name
    config_dir.mkdir(parents=True, exist_ok=True)
    runner_relpath = (script_dir / "compare_gmin_gmax.py").relative_to(project_dir).as_posix()
    submit_lines = [
        "#!/bin/bash",
        "# Submit the generated GMIN/GMAX comparison jobs from this folder.",
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
        'cd "$SCRIPT_DIR" || exit 1',
        'mkdir -p logs',
        "",
    ]

    for batch_name, fivep_label in batches:
        for length in lengths:
            job_name = f"gmin_gmax_len{length}_{fivep_label}"
            output_path = script_dir / "results" / experiment_name / f"{job_name}.xlsx"
            lines = ["[run]"]
            for key, value in {
                "batch_name": batch_name, "length": length, "random_seeds": random_seeds,
                "prune_fraction": prune_fraction, "algorithms": algorithms,
            }.items():
                lines.append(f"{key} = {toml_literal(value)}")
            lines.extend(["", "[output]", f"file = {toml_literal(output_path.relative_to(project_dir).as_posix())}"])
            for init_count in init_counts:
                report_dir = data_dir / batch_name / f"len{length}" / fivep_label
                # Resolve the stored cutoff from the filename instead of assuming one for every length.
                report_path, = report_dir.glob(f"hybrid_*_init{init_count}_seed41.xlsx")
                lines.extend([
                    "", "[[graphs]]", f"init_count = {init_count}",
                    f"report = {toml_literal(report_path.relative_to(project_dir).as_posix())}",
                ])
            config_path = config_dir / f"{job_name}.toml"
            config_path.write_text("\n".join(lines) + "\n")
            script_path = config_dir / f"{job_name}.sh"
            script_path.write_text(build_server_script(
                job_name=job_name, runner_relpath=runner_relpath,
                config_relpath=config_path.relative_to(project_dir).as_posix(),
                server_cfg=server_cfg, output_stem=f"logs/{job_name}",
            ))
            submit_lines.append(f"sbatch {script_path.name}")

    (config_dir / "submit_all.sh").write_text("\n".join(submit_lines) + "\n")
    print(f"Generated {len(batches) * len(lengths)} jobs: {config_dir}")
