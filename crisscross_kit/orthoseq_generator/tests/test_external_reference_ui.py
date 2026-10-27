"""Verify external-library upload state, UI workers and linked plots without running a full search."""

from io import BytesIO
import json
from pathlib import Path
import queue
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from orthoseq_generator.streamlit_app import plotly_utils as pu
from orthoseq_generator.streamlit_app import state_manager as state
from orthoseq_generator.streamlit_app.tabs import tab_refinement, tab_search
from orthoseq_generator.search_report_reader import load_metadata, load_reference_sequences


class TestExternalReferenceUI(unittest.TestCase):
    """Keep uploads optional and ensure plots and reports use the intended reference snapshot."""

    def setUp(self):
        """Use small deterministic energy fixtures and the canonical example workbook."""
        self.package_dir = Path(__file__).resolve().parents[1]
        self.example = self.package_dir / "scripts/examples/reference_sequences.xlsx"
        self.references = ["ACAC", "GGATCA", "TATGACCA"]
        self.pairs = [("AAAA", "TTTT"), ("CCCC", "GGGG")]
        self.on = np.array([-12., -11.])
        self.off = {key: np.array([[-5., 0.], [-6., -5.]]) for key in (
            "handle_handle_energies", "antihandle_handle_energies", "antihandle_antihandle_energies",
        )}

    def _state(self, uploaded, references=None):
        """Create only the state fields owned by the upload callback."""
        return SimpleNamespace(
            external_library_file=uploaded, external_sequences=references or [],
            external_reference_name=None, external_reference_error=None, crossref_e_range=np.zeros((4, 1)),
            on_e_range=self.on, off_e_range=self.off, final_cache_ready=True,
        )

    def _upload(self, name="reference.xlsx", content=None):
        """Represent the same name/getvalue interface used by Streamlit's UploadedFile."""
        return SimpleNamespace(name=name, getvalue=lambda: self.example.read_bytes() if content is None else content)

    def test_upload_enables_library_and_invalidates_only_external_energies(self):
        """Valid input supplies references automatically without clearing normal plots or completed reports."""
        session = self._state(self._upload(), ["AAAA"])
        with patch.object(state.st, "session_state", session), self.assertLogs("orthoseq", level="INFO") as logs:
            state.update_external_library()
        self.assertEqual(session.external_sequences, self.references)
        self.assertEqual(session.external_reference_name, "reference.xlsx")
        self.assertIsNone(session.external_reference_error)
        self.assertIsNone(session.crossref_e_range)
        self.assertIs(session.on_e_range, self.on)
        self.assertIs(session.off_e_range, self.off)
        self.assertTrue(session.final_cache_ready)
        self.assertIn("reference.xlsx (3 strands)", "\n".join(logs.output))

    def test_identical_pool_preserves_cached_energies(self):
        """Replacing a file with the same normalized strands does not need another energy calculation."""
        session = self._state(self._upload("renamed.xlsx"), list(self.references))
        cached = session.crossref_e_range
        with patch.object(state.st, "session_state", session):
            state.update_external_library()
        self.assertIs(session.crossref_e_range, cached)
        self.assertEqual(session.external_reference_name, "renamed.xlsx")

    def test_removing_upload_clears_the_pool_and_external_curve(self):
        """Removing the file restores an empty library while preserving the independent normal sample."""
        session = self._state(None, list(self.references))
        with patch.object(state.st, "session_state", session):
            state.update_external_library()
        self.assertEqual(session.external_sequences, [])
        self.assertIsNone(session.crossref_e_range)
        self.assertIsNone(session.external_reference_name)
        self.assertIs(session.off_e_range, self.off)

    def test_invalid_upload_cannot_keep_an_earlier_pool_active(self):
        """Rejected workbooks clear earlier references and expose the error to the global input guard."""
        session = self._state(self._upload(content=b"not an Excel workbook"), list(self.references))
        with patch.object(state.st, "session_state", session):
            state.update_external_library()
        self.assertEqual(session.external_sequences, [])
        self.assertIsNone(session.crossref_e_range)
        self.assertTrue(session.external_reference_error)

    def test_uploaded_report_uses_found_pairs_only(self):
        """The upload callback reuses the reader's priority without adding the report's earlier pool."""
        content = BytesIO()
        with pd.ExcelWriter(content) as writer:
            pd.DataFrame({"seq": ["AAAA"], "rc_seq": ["TTTT"]}).to_excel(
                writer, sheet_name="found_pairs", index=False,
            )
            pd.DataFrame({"sequence": ["ACAC"]}).to_excel(writer, sheet_name="reference_sequences", index=False)
        session = self._state(self._upload(content=content.getvalue()))
        with patch.object(state.st, "session_state", session):
            state.update_external_library()
        self.assertEqual(session.external_sequences, ["AAAA", "TTTT"])

    def test_linked_plot_has_both_cutoffs_and_keeps_all_external_values(self):
        """Both panels share ranges and bins, including actual zero values in the external matrix."""
        crossref = np.array([[-20., -7.], [-6., 0.]])
        for limit in (-8., -7.5):
            with self.subTest(limit=limit):
                fig = pu.create_interactive_histogram(self.on, self.off, -13., -10.,
                                                      off_limit=limit, crossref_energies=crossref)
                self.assertEqual(fig.layout.xaxis.matches, "x2")
                self.assertEqual(fig.layout.xaxis.range, fig.layout.xaxis2.range)
                self.assertLessEqual(fig.layout.xaxis.range[0], -20.)
                self.assertGreaterEqual(fig.layout.xaxis.range[1], 0.)
                external = fig.data[-1]
                np.testing.assert_array_equal(external.x, crossref.ravel())
                self.assertEqual(external.xaxis, "x2")
                self.assertEqual(external.xbins, fig.data[0].xbins)
                cutoffs = [shape for shape in fig.layout.shapes if shape.name == "off_limit"]
                self.assertEqual([(shape.xref, shape.yref) for shape in cutoffs],
                                 [("x", "y domain"), ("x2", "y2 domain")])
                self.assertTrue(all(shape.x0 == limit and shape.x1 == limit for shape in cutoffs))

    def test_no_references_preserves_the_original_single_plot(self):
        """Empty and absent reference energies produce the exact same figure, without a lower panel."""
        original = pu.create_interactive_histogram(self.on, self.off, -13., -10., off_limit=-8.)
        empty = pu.create_interactive_histogram(self.on, self.off, -13., -10.,
                                                off_limit=-8., crossref_energies=np.empty((4, 0)))
        self.assertEqual(original.to_json(), empty.to_json())
        self.assertNotIn("xaxis2", original.layout.to_plotly_json())

    def test_refinement_evaluates_the_same_sample_without_external_filtering(self):
        """The cutoff preview includes conflicting external energies rather than pre-rejecting those candidates."""
        out = queue.Queue()
        crossref = np.full((4, 3), -9.)
        with patch.object(tab_refinement.sc, "select_subset_in_energy_range",
                          return_value=(self.pairs, [10, 20], None, 0, {})) as select, \
             patch.object(tab_refinement.sc, "compute_ontarget_energies", return_value=(self.on, [], [])), \
             patch.object(tab_refinement.sc, "compute_offtarget_energies", return_value=self.off), \
             patch.object(tab_refinement.sc, "compute_crossreference_energies", return_value=crossref) as compute:
            tab_refinement._refine_worker(Mock(), -13., -10., -1., 2, out, self.references)
        self.assertNotIn("retained_pairs", select.call_args.kwargs)
        self.assertNotIn("offtarget_limit", select.call_args.kwargs)
        compute.assert_called_once_with(self.pairs, self.references)
        message = out.get_nowait()
        self.assertIs(message[4], crossref)
        self.assertIsNone(message[5])

    def test_refinement_with_no_library_adds_no_computation(self):
        """The old analysis path does not call the external energy helper."""
        out = queue.Queue()
        with patch.object(tab_refinement.sc, "select_subset_in_energy_range",
                          return_value=(self.pairs, [10, 20], None, 0, {})), \
             patch.object(tab_refinement.sc, "compute_ontarget_energies", return_value=(self.on, [], [])), \
             patch.object(tab_refinement.sc, "compute_offtarget_energies", return_value=self.off), \
             patch.object(tab_refinement.sc, "compute_crossreference_energies") as compute:
            tab_refinement._refine_worker(Mock(), -13., -10., -1., 2, out)
        compute.assert_not_called()
        self.assertIsNone(out.get_nowait()[4])

    def test_search_worker_passes_the_library_and_records_its_filename(self):
        """Search diagnostics keep the source filename alongside the backend's captured references."""
        out = queue.Queue()
        result = {"final_pairs": self.pairs, "external_sequences": list(self.references)}
        with patch.object(tab_search, "hybrid_search", return_value=result) as search:
            tab_search._search_worker(Mock(), -8., -10., -13., -1., 2, 1, 0.2,
                                      threading.Event(), threading.Event(), out, self.references, "library.xlsx")
        self.assertEqual(search.call_args.kwargs["external_sequences"], self.references)
        self.assertEqual(out.get_nowait()[1]["reference_sequence_file"], "library.xlsx")

    def test_app_renders_linked_panels_and_cutoff_changes_without_nupack(self):
        """The actual Streamlit page updates both cutoffs and returns to its old plot after library removal."""
        app = AppTest.from_file(str(self.package_dir / "streamlit_app/orthoseq_app.py"), default_timeout=20)
        app.run()
        self.assertFalse(app.exception)
        app.session_state["on_e_range"] = self.on
        app.session_state["off_e_range"] = self.off
        app.session_state["external_sequences"] = list(self.references)
        app.session_state["external_reference_name"] = "library.xlsx"
        app.session_state["crossref_e_range"] = np.full((4, 3), -6.)
        with patch.object(tab_refinement.sc, "compute_crossreference_energies") as compute:
            app.radio(key="active_step").set_value("3. Off-Target Limit").run()
            self.assertFalse(app.exception)
            plot = json.loads(app.get("plotly_chart")[0].proto.spec)
            self.assertEqual(plot["layout"]["xaxis"]["matches"], "x2")
            app.number_input(key="draft_offtarget_limit").set_value(-7.).run()
            self.assertFalse(app.exception)
            plot = json.loads(app.get("plotly_chart")[0].proto.spec)
            limits = [shape["x0"] for shape in plot["layout"]["shapes"] if shape.get("name") == "off_limit"]
            self.assertEqual(limits, [-7., -7.])
            app.session_state["external_sequences"] = []
            app.session_state["external_reference_name"] = None
            app.session_state["crossref_e_range"] = None
            app.run()
            self.assertFalse(app.exception)
            plot = json.loads(app.get("plotly_chart")[0].proto.spec)
            self.assertNotIn("xaxis2", plot["layout"])
        compute.assert_not_called()

    def test_upload_error_disables_analysis_and_search(self):
        """The actual app prevents starting calculations with a rejected external workbook."""
        app = AppTest.from_file(str(self.package_dir / "streamlit_app/orthoseq_app.py"), default_timeout=20)
        app.run()
        app.session_state["external_reference_error"] = "Invalid external workbook."
        app.radio(key="active_step").set_value("3. Off-Target Limit").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.button(key="btn_run_refine").disabled)
        app.radio(key="active_step").set_value("4. Sequence Search").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.button(key="btn_run_search").disabled)

    def test_completed_report_uses_the_run_snapshot_after_library_changes(self):
        """Final verification and workbook metadata stay attached to the completed run's external library."""
        app = AppTest.from_file(str(self.package_dir / "streamlit_app/orthoseq_app.py"), default_timeout=20)
        app.run()
        result = {
            "final_pairs": self.pairs, "final_pair_ids": [10, 20], "external_sequences": list(self.references),
            "reference_sequence_file": "original_library.xlsx", "seed_pairs": [], "seed_pair_ids": [],
            "seed_verified": None, "nupack": {}, "sequence_source": {},
            "search_params": {"random_seed": 41, "min_ontarget": -13., "max_ontarget": -10.,
                              "self_energy_limit": -1., "offtarget_limit": -8.},
            "total_nupack_calls": 26, "generation_data": [], "stopped_reason": "app_stop_event",
        }
        verified = {
            "on_target_energies": self.on, "off_target": self.off,
            "self_energy_seqs": np.zeros(2), "self_energy_rc_seqs": np.zeros(2),
            "external_sequences": list(self.references), "external_crossref": np.full((4, 3), -6.),
        }
        app.session_state["search_completed"] = True
        app.session_state["orthogonal_seq_pairs"] = self.pairs
        app.session_state["search_run_data"] = result
        app.session_state["external_sequences"] = ["AAAA"]
        app.session_state["external_reference_name"] = "replacement.xlsx"
        app.session_state["min_ontarget"] = -5.
        app.session_state["max_ontarget"] = -2.
        app.session_state["self_energy_limit"] = 0.5
        app.session_state["offtarget_limit"] = -4.
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(tab_search, "verify_selected_pairs", return_value=verified) as verify, \
             patch.object(tab_search.hf, "get_default_results_folder", return_value=directory):
            app.radio(key="active_step").set_value("4. Sequence Search").run()
            self.assertFalse(app.exception)
            verify.assert_called_once()
            self.assertEqual(verify.call_args.kwargs["external_sequences"], self.references)
            report = Path(app.session_state["search_report_path"])
            self.assertEqual(load_reference_sequences(report, sheet_name="reference_sequences"), self.references)
            self.assertEqual(load_metadata(report)["input.reference_sequence_file"], "original_library.xlsx")
            self.assertEqual(load_metadata(report)["search.random_seed"], 41)
            self.assertTrue(pd.read_excel(report, sheet_name="validation")["passed"].all())
            plot = json.loads(app.get("plotly_chart")[0].proto.spec)
            self.assertEqual(plot["layout"]["xaxis"]["matches"], "x2")
            cutoffs = [shape for shape in plot["layout"]["shapes"] if shape.get("name") == "off_limit"]
            self.assertEqual(len(cutoffs), 2)
            self.assertEqual([shape["x0"] for shape in cutoffs], [-8., -8.])
            self.assertEqual(len(app.get("plotly_chart")), 2)  # Linked distributions plus existing self-folding plot.

            # A completed run without references keeps its original plot even
            # if a new library has since been uploaded in Global Settings.
            result["external_sequences"] = []
            result["reference_sequence_file"] = None
            verified.pop("external_sequences")
            verified.pop("external_crossref")
            app.session_state["final_cache_ready"] = False
            verify.reset_mock()
            app.run()
            self.assertFalse(app.exception)
            verify.assert_called_once()
            self.assertEqual(verify.call_args.kwargs["external_sequences"], [])
            plot = json.loads(app.get("plotly_chart")[0].proto.spec)
            self.assertNotIn("xaxis2", plot["layout"])


if __name__ == "__main__":
    unittest.main()
