"""
Purpose:
    Run compute -> compare -> plot using a simple TOML config.
"""




def main():
    import argparse
    import os
    import tomllib

    from compute_short_seq_energies import run_compute_short_seq
    from compare_algorithms_from_pkl import run_compare
    from plot_compare_results import plot_results
    parser = argparse.ArgumentParser()
    default_config = os.path.join(os.path.dirname(__file__), "pipeline_config.example.toml")
    parser.add_argument(
        "--config",
        default=default_config,
        help="Path to TOML config file",
    )
    args = parser.parse_args()

    # Config is a plain dict loaded from TOML.
    with open(args.config, "rb") as f:
        cfg = tomllib.load(f)

    compute_cfg = cfg.get("compute", {})
    compare_cfg = cfg.get("compare", {})
    plot_cfg = cfg.get("plot", {})
    output_dir = cfg.get("output", {}).get("dir", "results")

    # 1) Compute PKLs
    pkl_paths = []
    if compute_cfg.get("enabled", True):
        for length in compute_cfg.get("lengths", []):
            for sigma in compute_cfg.get("range_sigmas", []):
                pkl_paths.append(
                    run_compute_short_seq(
                        length=length,
                        range_sigma=sigma,
                        random_seed=compute_cfg.get("random_seed", 42),
                        fivep_ext=compute_cfg.get("fivep_ext", ""),
                        threep_ext=compute_cfg.get("threep_ext", ""),
                        avoid_gggg=compute_cfg.get("avoid_gggg", False),
                        use_library=compute_cfg.get("use_library", False),
                        output_dir=output_dir,
                    )
                )
    else:
        # Use existing PKLs when compute is disabled.
        pkl_paths = compare_cfg.get("pkl_paths", [])

    # 2) Compare for each PKL
    results_paths = []
    for pkl_path in pkl_paths:
        run_compare(
            pkl_path,
            offtarget_limits=compare_cfg.get("offtarget_limits"),
            random_seed=compare_cfg.get("random_seed", 41),
            num_runs=compare_cfg.get("num_runs", 10),
            num_vertices_to_remove=compare_cfg.get("num_vertices_to_remove"),
            max_iterations=compare_cfg.get("max_iterations", 200),
            limit=compare_cfg.get("limit", float("inf")),
            multistart=compare_cfg.get("multistart", 1),
            population_size=compare_cfg.get("population_size", 300),
            show_progress=compare_cfg.get("show_progress", False),
            offtarget_step=compare_cfg.get("offtarget_step", 0.1),
            target_conflict_prob=compare_cfg.get("target_conflict_prob", 0.5),
            max_steps=compare_cfg.get("max_steps", 2000),
            output_dir=output_dir,
        )
        base = os.path.splitext(os.path.basename(pkl_path))[0]
        results_paths.append(os.path.join(output_dir, f"{base}_compare_results.pkl"))

    # 3) Plot results
    if plot_cfg.get("enabled", True):
        for results_path in results_paths:
            plot_results(results_path)


if __name__ == "__main__":
    main()
