"""Check model reuse across repeated calls, changed conditions, and worker process boundaries without NUPACK."""

import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from orthoseq_generator import energy_computations as ec
from orthoseq_generator import helper_functions as hf


class TestNupackModelReuse(unittest.TestCase):
    """Keep reused models tied to the active thermodynamic conditions and process."""

    def setUp(self):
        """Isolate model construction and restore the module's settings after each test."""
        self.addCleanup(hf.NUPACK_PARAMS.update, hf.NUPACK_PARAMS.copy())
        hf.set_nupack_params(material="dna", celsius=37, sodium=0.05, magnesium=0.025)
        ec._NUPACK_MODEL_CACHE.clear()
        self.addCleanup(ec._NUPACK_MODEL_CACHE.clear)
        self.constructor = Mock(side_effect=lambda **kwargs: object())
        fake_nupack = patch.dict(sys.modules, {"nupack": SimpleNamespace(Model=self.constructor)})
        fake_nupack.start()
        self.addCleanup(fake_nupack.stop)

    def test_repeated_conditions_reuse_model(self):
        """Repeated evaluations must not repeat the model's expensive setup."""
        model = ec._get_nupack_model()
        self.assertIs(ec._get_nupack_model(), model)
        self.constructor.assert_called_once_with(material="dna", celsius=37, sodium=0.05, magnesium=0.025)

    def test_each_changed_condition_rebuilds_model(self):
        """Changing any model parameter must not return a model with stale physical settings."""
        model = ec._get_nupack_model()
        for key, value in (("MATERIAL", "rna"), ("CELSIUS", 25), ("SODIUM", 1), ("MAGNESIUM", 0)):
            with self.subTest(parameter=key):
                hf.NUPACK_PARAMS[key] = value
                updated = ec._get_nupack_model()
                self.assertIsNot(updated, model)
                self.assertIs(ec._get_nupack_model(), updated)
                self.constructor.assert_called_with(**{key.lower(): value for key, value in hf.NUPACK_PARAMS.items()})
                model = updated
        self.assertEqual(self.constructor.call_count, 5)

    def test_child_process_rebuilds_inherited_model(self):
        """A forked child must build its own model even when it inherits a populated parent cache."""
        with patch.object(ec.os, "getpid", return_value=101) as pid:
            parent_model = ec._get_nupack_model()
            pid.return_value = 202
            child_model = ec._get_nupack_model()
            self.assertIsNot(child_model, parent_model)
            self.assertIs(ec._get_nupack_model(), child_model)
        self.assertEqual(self.constructor.call_count, 2)

    def test_failed_construction_is_not_cached(self):
        """A failed setup must propagate its error and allow a later retry with the requested conditions."""
        ec._get_nupack_model()
        hf.NUPACK_PARAMS["SODIUM"] = 1
        replacement = object()
        self.constructor.side_effect = [RuntimeError("model setup failed"), replacement]
        with self.assertRaisesRegex(RuntimeError, "model setup failed"):
            ec._get_nupack_model()
        self.assertIs(ec._get_nupack_model(), replacement)
        self.assertIs(ec._get_nupack_model(), replacement)
        self.assertEqual(self.constructor.call_count, 3)


if __name__ == "__main__":
    unittest.main()
