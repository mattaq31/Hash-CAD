"""Verify consistent algorithm labels, historical resume behavior, and cached benchmark reporting."""

from pathlib import Path
import importlib
import random
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.algorithm_names import algorithm_workflow, build_algorithm_name, normalize_algorithm_name

PACKAGE_DIR = Path(__file__).resolve().parents[2]
SHORT_DIR = PACKAGE_DIR / "orthoseq_generator/scripts/benchmarking/short_seq"
REVIEW_DIR = PACKAGE_DIR / (
    "orthoseq_generator/scripts/benchmarking/long_seq/scripts/auxiliary_analysis/gmin_gmax_comparison"
)


class TestAlgorithmNames(unittest.TestCase):
    """Keep old labels readable while ensuring different search modes have distinct new names."""

    def setUp(self):
        """Restore interpreter paths, shared configuration, and random state after each probe."""
        old_path = sys.path.copy()
        self.addCleanup(setattr, sys, "path", old_path)
        sys.path[:0] = [str(SHORT_DIR), str(SHORT_DIR / "scripts")]
        self.addCleanup(hf.ALGORITHM_PARAMS.update, hf.ALGORITHM_PARAMS.copy())
        self.addCleanup(random.setstate, random.getstate())

    def test_build_labels(self):
        """Cover graph and naive names, with execution mode last and pure greedy runs distinct."""
        self.assertEqual(build_algorithm_name("vertex_cover"), "vertex_cover_GMAX_rule")
        self.assertEqual(build_algorithm_name("hybrid", "Gmin", None), "hybrid_GMIN_rand")
        self.assertEqual(build_algorithm_name("vertex_cover", "Gmin", "rank", offline=True),
                         "vertex_cover_GMIN_rank_offline")
        self.assertEqual(build_algorithm_name("vertex_cover", "Gmax", "rule", offline=True, bare=True),
                         "vertex_cover_GMAX_rule_bare_offline")
        self.assertEqual(build_algorithm_name("naive"), "naive_rand")
        self.assertEqual(build_algorithm_name("naive", offline=True, ordering="weaker_first"), "naive_rank_offline")

    def test_aliases_preserve_historical_variants(self):
        """Older benchmark labels and every old comparison mode map to distinct canonical names."""
        expected = {
            "vertex_cover": "vertex_cover_GMAX_rule_offline",
            "vertex_cover_GMIN": "vertex_cover_GMIN_rule_offline",
            "naive_ordered": "naive_rank_offline",
            "hybrid_offline": "hybrid_GMAX_rule_offline",
            "naive_search": "naive_rand",
        }
        for old, canonical in expected.items():
            self.assertEqual(normalize_algorithm_name(old), canonical)
        variants = set()
        for heuristic in ("gmin", "gmax"):
            for ties in ("random", "rule", "rank"):
                for suffix in ("", "_iterative"):
                    canonical = normalize_algorithm_name(f"{heuristic}_{ties}{suffix}")
                    self.assertEqual(normalize_algorithm_name(canonical), canonical)
                    self.assertEqual("_bare_" in canonical, suffix == "")
                    variants.add(canonical)
        self.assertEqual(len(variants), 12)
        self.assertEqual(normalize_algorithm_name("figure1_random_sample"), "figure1_random_sample")
        self.assertEqual(algorithm_workflow("naive_search"), "naive")
        self.assertEqual(algorithm_workflow("hybrid_GMIN_rand"), "hybrid")

    def test_short_plot_reads_old_and_new_filenames(self):
        """Plot grouping accepts canonical names and historical benchmark filenames equally."""
        plotter = importlib.import_module("plot_batch_benchmark")
        old = plotter.parse_run_filename(Path("density0p2_vertex_cover_limit-8p0_seed41.xlsx"))
        new = plotter.parse_run_filename(Path("density0p2_vertex_cover_GMAX_rule_offline_limit-8p0_seed41.xlsx"))
        self.assertEqual(old, new)
        hybrid = plotter.parse_run_filename(
            Path("density0p2_hybrid_GMIN_rank_offline_limit-8p0_init50_prune0p2_seed41.xlsx")
        )
        self.assertEqual(hybrid["algorithm"], "hybrid_GMIN_rank_offline")
        self.assertEqual(hybrid["variant_label"], "init50_prune0p2")
        runs = pd.DataFrame([
            {"algorithm": "vertex_cover_GMIN_rule_offline", "initial_fresh_pair_count": None},
            {"algorithm": "hybrid_GMIN_rank_offline", "initial_fresh_pair_count": 50},
        ])
        keys = {row["key"] for row in plotter.build_plot_series_specs(runs)}
        self.assertEqual(keys, {"vertex_cover_GMIN_rule_offline", "hybrid_GMIN_rank_offline_init50"})

    def test_cached_vertex_cover_reports_the_executed_options(self):
        """Cached ranks must choose the weaker binder and metadata must match the resulting filename."""
        benchmark = importlib.import_module("benchmark_algorithms")
        dataset = {
            "metadata": {"derived": {"min_ontarget_energy": -21., "max_ontarget_energy": -18.}, "nupack": {}},
            "all_global_pair_ids": np.array([10, 20]), "matrix_global_pair_ids": np.array([10, 20]),
            "all_on_target_energies": np.array([-20., -19.]),
            "all_self_energy_seqs": np.zeros(2), "all_self_energy_rc_seqs": np.zeros(2),
            "handle_handle_energies": np.array([[0., 0.], [-9., 0.]]),
            "handle_antihandle_energies": np.zeros((2, 2)), "antihandle_antihandle_energies": np.zeros((2, 2)),
        }
        hf.set_algorithm("Gmin", "rank")
        with patch.object(benchmark, "load_dataset", return_value=dataset), \
             patch.object(benchmark, "get_selected_rows", side_effect=lambda data, ids: list(ids)), \
             patch.object(benchmark, "verify_selected_pairs", return_value={}), \
             patch.object(benchmark, "_write_benchmark_result_xlsx", side_effect=lambda path, **data: (path, data)):
            path, report = benchmark.run_vertex_cover_search_to_xlsx(
                "unused", offtarget_limit=-8., self_energy_limit=-1., heuristics="Gmin", vc_max_iterations=2,
            )
        self.assertEqual(report["selected_sequence_data"], [20])
        self.assertEqual(report["algorithm_name"], "vertex_cover_GMIN_rank_offline")
        self.assertTrue(path.name.startswith(report["algorithm_name"] + "_limit"))
        self.assertEqual(report["search_params"]["vc_tiebreak"], "rank")

    def _comparison_fixture(self, directory, seeds):
        """Store historical labels and an old output path in a workbook at its new location."""
        output_path = Path(directory) / "comparison.xlsx"
        old_output_path = Path(directory) / "old_location" / "comparison.xlsx"
        config_path = Path(directory) / "job.toml"
        old_config = (
            f'[run]\nbatch_name = "fixture"\nlength = 4\nrandom_seeds = {seeds}\nprune_fraction = 0.2\n'
            'algorithms = ["gmin_rank_iterative"]\n'
            f'[output]\nfile = "{old_output_path}"\n'
            '[[graphs]]\ninit_count = 25\nreport = "unused.xlsx"\n'
        )
        new_config = old_config.replace("gmin_rank_iterative", "vertex_cover_GMIN_rank_offline")
        config_path.write_text(new_config.replace(str(old_output_path), str(output_path)))
        with pd.ExcelWriter(output_path) as writer:
            pd.DataFrame({"toml": [old_config]}).to_excel(writer, sheet_name="config", index=False)
            pd.DataFrame([{
                "batch_name": "fixture", "length": 4, "init_count": 25, "algorithm": "gmin_rank_iterative",
                "prune_fraction": 0.2, "random_seed": 41, "retained_pair_count": 2,
                "retained_pair_ids": "10,20", "duration_s": 0.1,
            }]).to_excel(writer, sheet_name="results", index=False)
        return output_path, config_path

    def _run_comparison(self, config_path):
        """Exercise the real resume and Excel write flow with a small graph and a recorded solver call."""
        from orthoseq_generator import search_report_reader as reader
        from orthoseq_generator import vertex_cover_algorithms as vca

        seed_pairs = pd.DataFrame({"global_pair_id": [10, 20], "on_target_energy_verified": [-20., -19.]})
        matrices = {key: pd.DataFrame(np.zeros((2, 2))) for key in (
            "handle_handle_energies", "antihandle_handle_energies", "antihandle_antihandle_energies",
        )}
        with patch.object(sys, "argv", ["compare_gmin_gmax.py", "--config", str(config_path)]), \
             patch.object(reader, "load_metadata", return_value={"search.vc_max_iterations": 2,
                                                                  "search.offtarget_limit": -8.}), \
             patch.object(reader, "load_seed_pairs", return_value=seed_pairs), \
             patch.object(reader, "load_offtarget_matrices", return_value=matrices), \
             patch.object(vca, "iterative_vertex_cover_refinement", return_value=({10}, [])) as solver:
            runpy.run_path(str(REVIEW_DIR / "compare_gmin_gmax.py"), run_name="__main__")
        return solver

    def test_comparison_resume_recognizes_old_result_names(self):
        """Moving output and changing config labels must leave completed workbooks byte-identical."""
        with tempfile.TemporaryDirectory() as directory:
            output_path, config_path = self._comparison_fixture(directory, [41])
            before = output_path.read_bytes()
            self._run_comparison(config_path).assert_not_called()
            self.assertEqual(output_path.read_bytes(), before)

    def test_comparison_resume_rejects_changed_calculation_settings(self):
        """Ignoring output relocation must still reject changed pruning, inputs or seed lists."""
        with tempfile.TemporaryDirectory() as directory:
            output_path, config_path = self._comparison_fixture(directory, [41])
            before = output_path.read_bytes()
            original_config = config_path.read_text()
            for old, new in [("prune_fraction = 0.2", "prune_fraction = 0.3"),
                             ("unused.xlsx", "different.xlsx"), ("random_seeds = [41]", "random_seeds = [42]")]:
                with self.subTest(setting=old):
                    config_path.write_text(original_config.replace(old, new))
                    with self.assertRaisesRegex(ValueError, "different settings"):
                        self._run_comparison(config_path)
                    self.assertEqual(output_path.read_bytes(), before)

    def test_comparison_resume_appends_only_missing_seeds(self):
        """An interrupted, relocated job preserves completed measurements and adds only its missing seed."""
        with tempfile.TemporaryDirectory() as directory:
            output_path, config_path = self._comparison_fixture(directory, [41, 42])
            self._run_comparison(config_path).assert_called_once()
            results = pd.read_excel(output_path, sheet_name="results")
            self.assertEqual(results["random_seed"].tolist(), [41, 42])
            self.assertEqual(results["retained_pair_count"].tolist(), [2, 1])
            self.assertEqual(results["retained_pair_ids"].tolist(), ["10,20", "20"])
            self.assertEqual(results.iloc[0]["duration_s"], 0.1)
            self.assertEqual(results["algorithm"].tolist(), ["vertex_cover_GMIN_rank_offline"] * 2)
            self.assertEqual(pd.read_excel(output_path, sheet_name="config").iloc[0]["toml"], config_path.read_text())
            before = output_path.read_bytes()
            self._run_comparison(config_path).assert_not_called()
            self.assertEqual(output_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
