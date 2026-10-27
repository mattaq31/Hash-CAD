"""Check algorithm log metadata and XLSX round-trips without running NUPACK calculations."""

from pathlib import Path
import tempfile
import threading
import unittest

import numpy as np
import pandas as pd

from orthoseq_generator import helper_functions as hf
from orthoseq_generator.algorithm_names import build_algorithm_name
from orthoseq_generator.search_algorithm import hybrid_search
from orthoseq_generator.search_report_reader import load_metadata
from orthoseq_generator.search_reporting import write_hybrid_search_result_xlsx
from orthoseq_generator.sequence_generation import SequencePairRegistry


class TestAlgorithmReporting(unittest.TestCase):
    """Verify saved settings describe the run even after helper defaults change."""

    def setUp(self):
        """Restore shared settings and remove generated workbooks after each test."""
        self.addCleanup(hf.ALGORITHM_PARAMS.update, hf.ALGORITHM_PARAMS.copy())
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.report_path = Path(directory.name) / "report.xlsx"

    def _stopped_search(self):
        """Obtain real search diagnostics and logs without evaluating any sequence energies."""
        stop_event = threading.Event()
        stop_event.set()
        with self.assertLogs("orthoseq", level="INFO") as logs:
            result = hybrid_search(
                SequencePairRegistry(length=4, seed=41), -8., -18., -21., -1.,
                stop_event=stop_event, return_diagnostics=True,
            )
        return result, "\n".join(logs.output)

    def _write_report(self, search_params):
        """Use the real writer with a small energy fixture to exercise metadata serialization."""
        verified = {
            "on_target_energies": np.array([-19.]),
            "self_energy_seqs": np.array([0.]),
            "self_energy_rc_seqs": np.array([0.]),
            "off_target": {
                "handle_handle_energies": np.zeros((1, 1)),
                "antihandle_handle_energies": np.zeros((1, 1)),
                "antihandle_antihandle_energies": np.zeros((1, 1)),
            },
        }
        write_hybrid_search_result_xlsx(
            self.report_path, algorithm_name="hybrid_search",
            selected_sequence_data=[{"seq": "AAAA", "rc_seq": "TTTT", "global_pair_id": 0}],
            verified=verified, search_params=search_params, input_params={}, artifact_info={},
            nupack_params={}, generation_data=[], validation_data=[],
        )
        return load_metadata(self.report_path)

    def test_logs_and_reports_preserve_all_algorithm_modes(self):
        """Explicit random ties survive serialization and exports never read later helper values."""
        for heuristics in ("Gmax", "Gmin"):
            for tiebreak in ("rule", "rank", None):
                with self.subTest(heuristics=heuristics, tiebreak=tiebreak):
                    hf.set_algorithm(heuristics, tiebreak)
                    result, logs = self._stopped_search()
                    params = result["search_params"]
                    self.assertEqual(params["vc_heuristics"], heuristics)
                    self.assertEqual(params["vc_tiebreak"], tiebreak)
                    label = tiebreak if tiebreak is not None else "random"
                    self.assertIn(f"Graph search heuristic: {heuristics}\n", logs)
                    self.assertIn(f"Graph search tie-breaking: {tiebreak}\n", logs)
                    hf.set_algorithm("Gmin" if heuristics == "Gmax" else "Gmax", "rule")
                    metadata = self._write_report(params)
                    self.assertEqual(metadata["algorithm_name"], build_algorithm_name("hybrid", heuristics, tiebreak))
                    self.assertEqual(metadata["search.vc_heuristics"], heuristics)
                    self.assertEqual(metadata["search.vc_tiebreak"], label)

    def test_unrecorded_settings_are_not_inferred_from_globals(self):
        """Older callers and non-graph searches must not acquire the current global configuration."""
        hf.set_algorithm("Gmin", None)
        metadata = self._write_report({})
        for key in ("search.vc_heuristics", "search.vc_tiebreak"):
            self.assertIsNone(metadata[key])

    def test_legacy_reports_remain_readable(self):
        """An old report without algorithm settings retains its existing metadata."""
        rows = [{"key": "algorithm_name", "value": "vertex_cover_GMIN"}, {"key": "found_pair_count", "value": "1"}]
        with pd.ExcelWriter(self.report_path) as writer:
            pd.DataFrame(rows).to_excel(writer, sheet_name="run_metadata", index=False)
        hf.set_algorithm("Gmax", "rank")
        metadata = load_metadata(self.report_path)
        self.assertEqual(metadata["algorithm_name"], "vertex_cover_GMIN")
        self.assertEqual(metadata["found_pair_count"], 1)
        self.assertEqual(metadata["nupack.energy_type"], "total")
        self.assertNotIn("search.vc_heuristics", metadata)


if __name__ == "__main__":
    unittest.main()
