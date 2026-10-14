"""Verify helper algorithm settings, explicit overrides, and hybrid rank integration without NUPACK."""

import random
import unittest
from unittest.mock import Mock, patch

import numpy as np

from orthoseq_generator import helper_functions as hf
from orthoseq_generator import search_algorithm as sa
from orthoseq_generator import vertex_cover_algorithms as vca


class TestAlgorithmSettings(unittest.TestCase):
    """Keep configuration local to each test and verify its effects on actual graph selection."""

    def setUp(self):
        self.previous_settings = hf.ALGORITHM_PARAMS.copy()
        self.previous_random_state = random.getstate()
        self.addCleanup(hf.ALGORITHM_PARAMS.update, self.previous_settings)
        self.addCleanup(random.setstate, self.previous_random_state)
        hf.set_algorithm()

    def test_invalid_settings_leave_configuration_unchanged(self):
        """Reject invalid settings before replacing either previously configured value."""
        hf.set_algorithm("Gmin", None)
        for heuristics, tiebreak in [("exact", "rule"), ("Gmax", "invalid")]:
            with self.subTest(heuristics=heuristics, tiebreak=tiebreak):
                with self.assertRaises(ValueError):
                    hf.set_algorithm(heuristics, tiebreak)
                self.assertEqual(hf.ALGORITHM_PARAMS, {"HEURISTICS": "Gmin", "TIEBREAK": None})

    def test_helper_defaults_match_explicit_backend_settings(self):
        """All configured modes must produce the same cover and trajectory as explicit calls."""
        vertices = list(range(7))
        edges = [(0, 1), (1, 2), (2, 0), (2, 3), (3, 4), (4, 5), (5, 6), (6, 3)]
        ranks = {v: v for v in vertices}
        for heuristics in ("Gmax", "Gmin"):
            for tiebreak in ("rule", "rank", None):
                with self.subTest(heuristics=heuristics, tiebreak=tiebreak):
                    hf.set_algorithm(heuristics, tiebreak)
                    random.seed(41)
                    inherited = vca.iterative_vertex_cover_refinement(
                        vertices, edges, max_iterations=5, num_vertices_to_remove=2, vertex_ranks=ranks,
                    )
                    random.seed(41)
                    explicit = vca.iterative_vertex_cover_refinement(
                        vertices, edges, max_iterations=5, num_vertices_to_remove=2,
                        heuristics=heuristics, tiebreak=tiebreak, vertex_ranks=ranks,
                    )
                    self.assertEqual(inherited, explicit)
                    self.assertFalse(vca.find_uncovered_edges(edges, inherited[0]))

    def test_explicit_arguments_override_helper_settings_including_none(self):
        """An explicit random tie-break must not inherit the configured rank tie-break."""
        hf.set_algorithm("Gmin", "rank")
        with patch.object(vca, "greedy_vertex_cover_gmax", wraps=vca.greedy_vertex_cover_gmax) as gmax:
            with patch.object(vca, "greedy_vertex_cover_gmin", side_effect=AssertionError("Unexpected GMIN")):
                cover, _ = vca.iterative_vertex_cover_refinement(
                    [10, 20], [(10, 20)], max_iterations=2, heuristics="Gmax", tiebreak=None,
                )
        self.assertEqual(gmax.call_count, 3)
        self.assertTrue(all(call.kwargs["tiebreak"] is None for call in gmax.call_args_list))
        self.assertFalse(vca.find_uncovered_edges([(10, 20)], cover))
        self.assertEqual(hf.ALGORITHM_PARAMS, {"HEURISTICS": "Gmin", "TIEBREAK": "rank"})

    def test_gmin_settings_reach_initialization_and_repairs(self):
        """The configured heuristic and ranks must apply to every repair as well as initialization."""
        hf.set_algorithm("Gmin", "rank")
        ranks = {10: 1, 20: 0}
        with patch.object(vca, "greedy_vertex_cover_gmin", wraps=vca.greedy_vertex_cover_gmin) as gmin:
            cover, _ = vca.iterative_vertex_cover_refinement(
                [10, 20], [(10, 20)], max_iterations=2, num_vertices_to_remove=1, vertex_ranks=ranks,
            )
        self.assertEqual(cover, {10})
        self.assertEqual(gmin.call_count, 3)
        self.assertTrue(all(call.kwargs["tiebreak"] == "rank" for call in gmin.call_args_list))
        self.assertTrue(all(call.kwargs["vertex_ranks"] == ranks for call in gmin.call_args_list))

    def test_missing_ranks_keep_existing_warning_and_fallback(self):
        """Direct graph callers retain the documented fallback when they supply no ranks."""
        hf.set_algorithm("Gmin", "rank")
        with self.assertWarnsRegex(UserWarning, "No vertex ranks supplied"):
            cover, _ = vca.iterative_vertex_cover_refinement([10, 20], [(10, 20)], max_iterations=0)
        self.assertEqual(len(cover), 1)

    def test_candidate_ranks_use_negative_energy_and_account_for_recomputation(self):
        """A conflict keeps the weaker binder in rank mode and charges the extra energy work."""
        pairs = [("AAAA", "TTTT"), ("CCCC", "GGGG")]
        for heuristics in ("Gmax", "Gmin"):
            with self.subTest(heuristics=heuristics):
                hf.set_algorithm(heuristics, "rank")
                with patch.object(sa.sc, "compute_ontarget_energies", return_value=(np.array([-20., -19.]), [], [])):
                    with patch.object(sa.sc, "compute_offtarget_energies", return_value={}), \
                         patch.object(sa, "build_edges", return_value=[(10, 20)]):
                        retained, calls = sa._run_vertex_cover(pairs, [10, 20], -8., 0.2, 2)
                self.assertEqual(retained, {20})
                self.assertEqual(calls, sa.sc.estimate_offtarget_nupack_calls(2) + 2)

    def test_rule_mode_does_not_recompute_candidate_ontarget_energies(self):
        """The original default path retains its energy cost and needs no rank computation."""
        pairs = [("AAAA", "TTTT"), ("CCCC", "GGGG")]
        with patch.object(sa.sc, "compute_ontarget_energies", side_effect=AssertionError("Unexpected energy work")):
            with patch.object(sa.sc, "compute_offtarget_energies", return_value={}), \
                 patch.object(sa, "build_edges", return_value=[(10, 20)]):
                retained, calls = sa._run_vertex_cover(pairs, [10, 20], -8., 0.2, 2)
        self.assertEqual(len(retained), 1)
        self.assertEqual(calls, sa.sc.estimate_offtarget_nupack_calls(2))

    def test_seed_ranks_reuse_verification_energies(self):
        """Seed pruning uses existing energies for ranking and counts their search-essential cost."""
        hf.set_algorithm("Gmin", "rank")
        pairs = [("AAAA", "TTTT"), ("CCCC", "GGGG")]
        pairs_by_id = dict(zip([10, 20], pairs))
        registry = Mock(get_pair_by_id=pairs_by_id.__getitem__)
        stats = {"attempts": 2, "passed_ontarget_and_self": 2, "passed_homodimer": 0, "accepted_into_pool": 2}
        with patch.object(sa.sc, "select_subset_in_energy_range", return_value=(pairs, [10, 20], None, 2, stats)):
            with patch.object(sa.sc, "compute_ontarget_energies", return_value=(np.array([-20., -19.]), [], [])) as on:
                with patch.object(sa.sc, "compute_offtarget_energies", return_value={}), \
                     patch.object(sa, "build_edges", return_value=[(10, 20)]):
                    result = sa._run_seed_pass(
                        sequence_pairs=registry, offtarget_limit=-8., max_ontarget=-18., min_ontarget=-21.,
                        self_energy_limit=-1., initial_fresh_pair_count=2, total_nupack_budget=100,
                        prune_fraction=0.2, vc_max_iterations=2, stop_event=None, start_t=0,
                    )
        on.assert_called_once_with(pairs)
        self.assertEqual(result["retained_pair_ids"], {20})
        self.assertEqual(result["accounted_nupack_calls"], 2 + sa.sc.estimate_offtarget_nupack_calls(2) + 2)


if __name__ == "__main__":
    unittest.main()
