"""Check specificity scoring against independent examples with asymmetric HA and homodimer competitors."""

import unittest

import numpy as np

from sequence_quality import association_to_complex_energies, compute_specificity_gaps


class TestSequenceQuality(unittest.TestCase):
    """Protect the strand mapping and raw-energy convention used for published-library comparisons."""

    def setUp(self):
        """Build a small library with known competitors and unequal monomer energies."""
        self.verified = {
            "on_target_energies": np.array([-10., -12.]),
            "self_energy_seqs": np.array([-0.1, -0.2]),
            "self_energy_rc_seqs": np.array([-0.3, -0.4]),
            "off_target": {
                "handle_handle_energies": np.array([[-3., 0.], [-8., -5.]]),
                "antihandle_handle_energies": np.array([[0., -9.], [-2., 0.]]),
                "antihandle_antihandle_energies": np.array([[-4., 0.], [-7., -6.]]),
            },
        }

    def test_asymmetric_ha_and_triangular_placeholders(self):
        """Both directions of HA must map back to the correct physical strand."""
        quality = compute_specificity_gaps(self.verified["on_target_energies"], self.verified["off_target"])
        np.testing.assert_allclose(quality["strand_gaps"], [1., 4., 3., 3.])
        np.testing.assert_array_equal(quality["strongest_offtarget_indices"], [3, 0, 3, 0])
        self.assertEqual(quality["minimum_gap"], 1.)
        self.assertEqual(quality["mean_gap"], 2.75)

    def test_homodimer_can_limit_the_score(self):
        """A stronger-than-intended homodimer must yield a negative specificity score."""
        self.verified["off_target"]["handle_handle_energies"][0, 0] = -11.
        quality = compute_specificity_gaps(self.verified["on_target_energies"], self.verified["off_target"])
        self.assertEqual(quality["minimum_gap"], -1.)
        self.assertEqual(quality["strongest_offtarget_indices"][0], 0)

    def test_unintended_interaction_equal_to_ontarget_is_retained(self):
        """Exclude partners by identity so zero-gap unintended interactions are not accidentally masked."""
        self.verified["off_target"]["handle_handle_energies"][1, 0] = -10.
        quality = compute_specificity_gaps(self.verified["on_target_energies"], self.verified["off_target"])
        self.assertEqual(quality["minimum_gap"], 0.)

    def test_raw_complex_conversion_changes_partner_specific_gap(self):
        """Unequal monomer energies change raw specificity and must use both partners' contributions."""
        raw = association_to_complex_energies(self.verified)
        np.testing.assert_allclose(raw["on_target_energies"], [-10.4, -12.6])
        np.testing.assert_allclose(raw["off_target"]["antihandle_handle_energies"], [[0., -9.5], [-2.5, 0.]])
        np.testing.assert_allclose(raw["off_target"]["handle_handle_energies"], [[-3.2, 0.], [-8.3, -5.4]])
        quality = compute_specificity_gaps(raw["on_target_energies"], raw["off_target"])
        np.testing.assert_allclose(quality["strand_gaps"], [0.9, 4.3, 2.7, 3.1])
        np.testing.assert_allclose(self.verified["on_target_energies"], [-10., -12.])

    def test_capped_values_trigger_direct_backend_fallback(self):
        """Only evaluated values count; the zero placeholders in every normal report are harmless."""
        self.verified["off_target"]["antihandle_handle_energies"][0, 1] = -1.
        with self.assertRaisesRegex(RuntimeError, "fresh raw-complex"):
            association_to_complex_energies(self.verified)

    def test_single_pair_still_has_two_homodimer_competitors(self):
        """The intended heterodimer is excluded, while each strand can still self-associate."""
        quality = compute_specificity_gaps([-10.], {
            "handle_handle_energies": [[-7.]],
            "antihandle_handle_energies": [[0.]],
            "antihandle_antihandle_energies": [[-8.]],
        })
        np.testing.assert_allclose(quality["strand_gaps"], [3., 2.])
        np.testing.assert_array_equal(quality["strongest_offtarget_indices"], [0, 1])


if __name__ == "__main__":
    unittest.main()
