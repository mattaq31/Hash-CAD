"""Exercise external-strand filtering, complete verification, XLSX replay and plotting without NUPACK."""

from contextlib import ExitStack
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd

from orthoseq_generator import energy_computations as ec
from orthoseq_generator import helper_functions as hf
from orthoseq_generator import search_algorithm as sa
from orthoseq_generator import search_reporting as reporting
from orthoseq_generator.energy_plots import plot_crossreference_histogram
from orthoseq_generator.search_report_reader import load_external_crossref, load_metadata, load_reference_sequences
from orthoseq_generator.sequence_generation import normalize_reference_sequences


class TestExternalReferencePool(unittest.TestCase):
    """Keep arbitrary reference strands separate from selected pairs throughout the workflow."""

    def setUp(self):
        """Use a small selected set, restore global settings and clean generated artifacts."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.addCleanup(hf.ALGORITHM_PARAMS.update, hf.ALGORITHM_PARAMS.copy())
        hf.set_algorithm("Gmax", "rule")
        self.pairs = [("AAAA", "TTTT"), ("CCCC", "GGGG")]
        self.selected = reporting.build_selected_sequence_data(self.pairs, [10, 20])
        self.verified = {
            "on_target_energies": np.array([-12., -12.]),
            "self_energy_seqs": np.zeros(2), "self_energy_rc_seqs": np.zeros(2),
            "off_target": {key: np.zeros((2, 2)) for key in (
                "handle_handle_energies", "antihandle_handle_energies", "antihandle_antihandle_energies",
            )},
        }

    def _validate(self, verified):
        """Run real validation with a fixed threshold and return checks by name."""
        rows = reporting.validate_selected_pairs(
            self.selected, verified, min_ontarget=-13., max_ontarget=-11.,
            self_energy_limit=-1., offtarget_limit=-8.,
        )
        return {row["check"]: row for row in rows}

    def test_normalization_and_excel_input(self):
        """An Excel report input retains explicit strands, normalizes case and removes duplicate blanks."""
        path = self.directory / "reference.xlsx"
        with pd.ExcelWriter(path) as writer:
            pd.DataFrame({"sequence": [" ac gt ", "", "ACGT", "gga"]}).to_excel(
                writer, sheet_name="reference_sequences", index=False,
            )
        self.assertEqual(load_reference_sequences(path), ["ACGT", "GGA"])
        self.assertEqual(normalize_reference_sequences(None), [])
        with self.assertRaisesRegex(ValueError, "collection"):
            normalize_reference_sequences("ACGT")

    def test_invalid_excel_reports_the_original_row(self):
        """Invalid input is rejected before the search, with its worksheet row intact."""
        path = self.directory / "invalid.xlsx"
        for value in ("ACNT", 123):
            with self.subTest(value=value):
                with pd.ExcelWriter(path) as writer:
                    pd.DataFrame({"sequence": ["ACGT", "", value]}).to_excel(
                        writer, sheet_name="reference_sequences", index=False,
                    )
                with self.assertRaisesRegex(ValueError, "row 4"):
                    load_reference_sequences(path)

    def test_required_sheet_and_column_and_legacy_reports(self):
        """External inputs require an explicit column; old reports may omit the feature entirely."""
        path = self.directory / "old.xlsx"
        pd.DataFrame({"seq": ["ACGT"]}).to_excel(path, sheet_name="found_pairs", index=False)
        self.assertEqual(load_reference_sequences(path, sheet_name="reference_sequences", required=False), [])
        self.assertIsNone(load_external_crossref(path))
        with self.assertRaisesRegex(ValueError, "sheet"):
            load_reference_sequences(path)
        pd.DataFrame({"wrong": ["ACGT"]}).to_excel(path, sheet_name="reference_sequences", index=False)
        with self.assertRaisesRegex(ValueError, "column"):
            load_reference_sequences(path)

    def test_found_pairs_take_precedence_without_combining_pools(self):
        """An existing report contributes only its selected strands, normalized across both columns."""
        path = self.directory / "existing_library.xlsx"
        with pd.ExcelWriter(path) as writer:
            pd.DataFrame({
                "seq": [" aa aa ", "cccc", "AAAA"], "rc_seq": ["tttt", "", "gggg"],
                "on_target_energy_verified": [-12., -12., -12.],
            }).to_excel(writer, sheet_name="found_pairs", index=False)
            pd.DataFrame({"sequence": ["ACAC"]}).to_excel(writer, sheet_name="reference_sequences", index=False)
        self.assertEqual(load_reference_sequences(path), ["AAAA", "CCCC", "TTTT", "GGGG"])
        self.assertEqual(load_reference_sequences(path, sheet_name="reference_sequences"), ["ACAC"])

    def test_invalid_found_pairs_fall_back_to_reference_list(self):
        """Missing pair columns or invalid pair bases allow the second supported layout to be used."""
        path = self.directory / "fallback.xlsx"
        for pairs in (pd.DataFrame({"seq": ["ACGT"]}),
                      pd.DataFrame({"seq": ["ACGT", "ACNT"], "rc_seq": ["TGCA", "GATT"]})):
            with self.subTest(columns=list(pairs.columns)):
                with pd.ExcelWriter(path) as writer:
                    pairs.to_excel(writer, sheet_name="found_pairs", index=False)
                    pd.DataFrame({"sequence": [" acac "]}).to_excel(
                        writer, sheet_name="reference_sequences", index=False,
                    )
                self.assertEqual(load_reference_sequences(path), ["ACAC"])

    def test_invalid_layouts_explain_both_formats_and_original_rows(self):
        """When both candidates fail, diagnostics identify the failing cells and accepted formats."""
        path = self.directory / "invalid_report.xlsx"
        with pd.ExcelWriter(path) as writer:
            pd.DataFrame({"seq": ["ACGT", "AAAA"], "rc_seq": ["TGCA", "ACNT"]}).to_excel(
                writer, sheet_name="found_pairs", index=False,
            )
            pd.DataFrame({"sequence": ["CNC"]}).to_excel(writer, sheet_name="reference_sequences", index=False)
        with self.assertRaises(ValueError) as failure:
            load_reference_sequences(path)
        message = str(failure.exception)
        self.assertIn("found_pairs", message)
        self.assertIn("reference_sequences", message)
        self.assertIn("row 3", message)
        self.assertIn("row 2", message)

    def test_replay_does_not_use_found_pairs_as_an_external_pool(self):
        """Explicit replay selection remains empty for a report without a recorded external library."""
        path = self.directory / "old_report.xlsx"
        pd.DataFrame({"seq": ["AAAA"], "rc_seq": ["TTTT"]}).to_excel(
            path, sheet_name="found_pairs", index=False,
        )
        self.assertEqual(load_reference_sequences(path), ["AAAA", "TTTT"])
        self.assertEqual(load_reference_sequences(path, sheet_name="reference_sequences", required=False), [])

    def test_empty_pool_and_padding_do_not_call_nupack(self):
        """Padding consumes no calls; arbitrary grouped strands get exactly two checks each."""
        with patch.object(ec, "compute_nupack_energy", return_value=(-8., 0., 0.)) as compute:
            self.assertEqual(ec.crossreference_sequences(self.pairs[0], [], -8.), (True, 0))
            pool = [("ACAC", "CACA"), ("AGAG", "")]
            self.assertEqual(ec.crossreference_sequences(self.pairs[0], pool, -8.), (True, 6))
        self.assertEqual(compute.call_count, 6)
        self.assertTrue(all(call.args[1] for call in compute.call_args_list))

    def test_crossreference_rejects_early_and_counts_only_executed_calls(self):
        """A strong interaction still short-circuits with the existing strict comparison."""
        with patch.object(ec, "compute_nupack_energy", return_value=(-9., 0., 0.)) as compute:
            self.assertEqual(ec.crossreference_sequences(self.pairs[0], [("ACAC", "")], -8.), (False, 1))
        self.assertEqual(compute.call_count, 1)

    def _hybrid_fixture(self, references=None, checkpoint=False):
        """Run both real collection passes with deterministic energies and an explicit stop signal."""
        pairs = self.pairs[:1] + [("GCGC", "CGCG")] + self.pairs[1:] + [("ACAC", "GTGT")]
        stop_event = threading.Event()
        checkpoint_event = threading.Event()
        callbacks = []
        draws = iter(enumerate(pairs))

        def sample_pair():
            """Stop after the last draw; request a checkpoint when collection begins."""
            pair_id, pair = next(draws)
            if checkpoint and pair_id == 2:
                checkpoint_event.set()
            if pair_id == 3:
                stop_event.set()
            return pair_id, pair

        def energy(a, b, **kwargs):
            """Make only the first and third candidates conflict with the external strand."""
            if (a, b) in pairs:
                return -12., 0., 0.
            if b == "TATA" and a in ("AAAA", "CCCC"):
                return -9., 0., 0.
            return -1., 0., 0.

        registry = Mock(sample_pair=sample_pair, get_pair_by_id=pairs.__getitem__)
        with ExitStack() as stack:
            compute = stack.enter_context(patch.object(ec, "compute_nupack_energy", side_effect=energy))
            stack.enter_context(patch.object(sa.sc, "compute_ontarget_energies",
                                             side_effect=lambda pairs: (np.full(len(pairs), -12.), [], [])))
            off = stack.enter_context(patch.object(sa.sc, "compute_offtarget_energies", return_value={}))
            stack.enter_context(patch.object(sa, "build_edges", return_value=[]))
            result = sa.hybrid_search(
                registry, -8., -11., -13., -1., initial_fresh_pair_count=1,
                total_nupack_budget=100, vc_max_iterations=1, stop_event=stop_event,
                checkpoint_event=checkpoint_event, checkpoint_callback=callbacks.append,
                return_diagnostics=True, external_sequences=references,
            )
        return result, pairs, compute.call_count, off, callbacks

    def test_both_passes_filter_external_pool_and_preserve_graph_scope(self):
        """External conflicts are excluded from both passes; graph pruning only sees fresh candidates."""
        for references, expected_calls in ((["tata", ""], 26), (["tata", "actg", "gc", ""], 34)):
            with self.subTest(references=references):
                snapshot = normalize_reference_sequences(references)
                result, pairs, calls, off, _ = self._hybrid_fixture(references)
                references[0] = "AAAA"
                self.assertEqual(result["external_sequences"], snapshot)
                self.assertEqual(result["seed_pair_ids"], [1])
                self.assertEqual(result["final_pair_ids"], [1, 3])
                self.assertEqual(result["final_pairs"], [pairs[1], pairs[3]])
                self.assertEqual([call.args[0] for call in off.call_args_list], [[pairs[1]], [pairs[3]]])
                self.assertEqual(result["total_nupack_calls"], calls + 4)
                self.assertEqual(result["total_nupack_calls"], expected_calls)

    def test_empty_reference_list_preserves_search_results_and_accounting(self):
        """Default and explicit empty pools produce identical search results and progress counters."""
        default, _, default_calls, _, _ = self._hybrid_fixture()
        empty, _, empty_calls, _, _ = self._hybrid_fixture([])
        for key in ("final_pairs", "final_pair_ids", "generation_data", "total_nupack_calls", "stopped_reason"):
            self.assertEqual(default[key], empty[key])
        self.assertEqual(default_calls, empty_calls)
        self.assertEqual(empty["final_pair_ids"], [0, 1, 2, 3])

    def test_checkpoint_retains_external_filter_on_resume(self):
        """A checkpoint resumes the same filtered collection and does not charge diagnostic graph work."""
        result, _, calls, _, callbacks = self._hybrid_fixture(["TATA"], checkpoint=True)
        self.assertEqual(result["final_pair_ids"], [1, 3])
        self.assertEqual(result["total_nupack_calls"], calls + 4)
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(callbacks[0]["initial_orthogonal"], 1)

    def test_complete_matrix_and_existing_internal_matrix_masks(self):
        """Rectangular verification computes every entry; internal matrices keep their original masks."""
        references = ["ACAC", "CACA", "AGAG"]
        with patch.dict("os.environ", {"ORTHOSEQ_NO_MP": "1"}), patch.object(hf, "require_nupack"):
            with patch.object(ec, "compute_nupack_energy", return_value=(-9., 0., 0.)) as compute:
                crossref = ec.compute_crossreference_energies(self.pairs, references)
                self.assertEqual(compute.call_count, 12)
                self.assertEqual([call.args[:2] for call in compute.call_args_list],
                                 [(strand, ref) for pair in self.pairs for strand in pair for ref in references])
                compute.reset_mock()
                internal = ec.compute_offtarget_energies(self.pairs)
                self.assertEqual(compute.call_count, ec.estimate_offtarget_nupack_calls(2))
        np.testing.assert_array_equal(crossref, np.full((4, 3), -9.))
        np.testing.assert_array_equal(internal["handle_handle_energies"], [[-9., 0.], [-9., -9.]])
        np.testing.assert_array_equal(internal["antihandle_antihandle_energies"], [[-9., 0.], [-9., -9.]])
        np.testing.assert_array_equal(internal["antihandle_handle_energies"], [[0., -9.], [-9., 0.]])
        with patch.object(hf, "require_nupack", side_effect=AssertionError("Unexpected NUPACK")):
            self.assertEqual(ec.compute_crossreference_energies(self.pairs, []).shape, (4, 0))

    def test_verification_adds_optional_external_data_only_once(self):
        """Post-run verification reuses the flat normalized list and leaves legacy payloads unchanged."""
        with patch.object(reporting, "compute_ontarget_energies", return_value=(np.zeros(2),) * 3), \
             patch.object(reporting, "compute_offtarget_energies", return_value={}), \
             patch.object(reporting, "compute_crossreference_energies", return_value=np.zeros((4, 1))) as compute:
            empty = reporting.verify_selected_pairs(self.selected, external_sequences=[])
            self.assertNotIn("external_crossref", empty)
            compute.assert_not_called()
            verified = reporting.verify_selected_pairs(self.selected, external_sequences=["acac", "ACAC"])
        compute.assert_called_once_with(self.pairs, ["ACAC"])
        self.assertEqual(verified["external_sequences"], ["ACAC"])

    def test_validation_threshold_and_worst_interaction(self):
        """Equality passes; one stronger interaction identifies its actual strand and reference."""
        verified = {**self.verified, "external_sequences": ["ACAC", "AGAG"],
                    "external_crossref": np.full((4, 2), -8.)}
        self.assertTrue(self._validate(verified)["external_off_target_violations"]["passed"])
        verified["external_crossref"][3, 1] = -9.
        checks = self._validate(verified)
        self.assertTrue(checks["external_crossref_complete"]["passed"])
        failed = checks["external_off_target_violations"]
        self.assertFalse(failed["passed"])
        self.assertEqual((failed["value"], failed["min_energy"]), (1, -9.))
        self.assertEqual((failed["selected_pair_id"], failed["selected_strand"], failed["reference_id"]),
                         (20, "rc_seq", 1))

    def test_incomplete_verification_never_passes(self):
        """Missing entries, wrong dimensions and nonfinite values cannot pass external validation."""
        for matrix in (None, np.zeros((3, 1)), np.full((4, 1), np.nan), np.full((4, 1), np.inf)):
            with self.subTest(matrix=matrix):
                verified = {**self.verified, "external_sequences": ["ACAC"]}
                if matrix is not None:
                    verified["external_crossref"] = matrix
                checks = self._validate(verified)
                self.assertFalse(checks["external_crossref_complete"]["passed"])
                self.assertFalse(checks["external_off_target_violations"]["passed"])

    def test_report_roundtrip_alignment_and_separate_accounting(self):
        """The report stores explicit references, all labelled cross energies and report-only call counts."""
        verified = {**self.verified, "external_sequences": ["ACAC", "AGAG", "CACA"],
                    "external_crossref": np.arange(12, dtype=float).reshape(4, 3) - 5.}
        path = self.directory / "report.xlsx"
        reporting.write_hybrid_search_result_xlsx(
            path, algorithm_name="hybrid_search", selected_sequence_data=self.selected, verified=verified,
            search_params={"total_nupack_calls": 26}, input_params={}, artifact_info={}, nupack_params={},
            generation_data=[], validation_data=list(self._validate(verified).values()),
        )
        self.assertEqual(
            load_reference_sequences(path, sheet_name="reference_sequences"), verified["external_sequences"],
        )
        matrix = load_external_crossref(path)
        np.testing.assert_array_equal(matrix.values, verified["external_crossref"])
        self.assertEqual(list(matrix.index), ["10:H:AAAA", "10:A:TTTT", "20:H:CCCC", "20:A:GGGG"])
        self.assertEqual(list(matrix.columns), ["0:R:ACAC", "1:R:AGAG", "2:R:CACA"])
        metadata = load_metadata(path)
        self.assertEqual(metadata["search.total_nupack_calls"], 26)
        self.assertEqual(metadata["verification.external_crossref_nupack_calls"], 12)

    def test_separate_plot_preserves_zero_energies_and_threshold(self):
        """Plot statistics use every rectangular entry and the configured cutoff, without NUPACK."""
        path = self.directory / "crossref.pdf"
        stats = plot_crossreference_histogram([[-9., -8.], [-1., 0.]], -8., output_path=path, show_plot=False)
        self.assertEqual((stats["interaction_count"], stats["violations"], stats["max_crossref"]), (4, 1, 0.))
        self.assertTrue(path.read_bytes().startswith(b"%PDF"))
        self.assertEqual(plot_crossreference_histogram(np.empty((4, 0)), -8.)["interaction_count"], 0)
        with self.assertRaisesRegex(ValueError, "finite"):
            plot_crossreference_histogram([np.nan], -8., show_plot=False)


if __name__ == "__main__":
    unittest.main()
