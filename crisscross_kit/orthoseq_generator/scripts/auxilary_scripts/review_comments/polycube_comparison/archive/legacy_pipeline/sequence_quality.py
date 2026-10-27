"""Local comparison helpers for the weakest per-strand on/off-target specificity gap."""

import numpy as np


def compute_specificity_gaps(on_target_energies, off_target):
    """Return per-strand specificity and its minimum, including homodimers as competitors.

    Inputs use the canonical OrthoSeq matrix layout: lower-triangular HH/AA (including
    homodimers), and HA with H rows and A columns. Only the intended partner is excluded.
    Output strand indices list all H strands followed by all A strands. The energy
    convention is inherited from the inputs; use one consistent convention throughout.
    """
    on_target = np.asarray(on_target_energies, dtype=float)
    if on_target.ndim != 1 or on_target.size == 0 or not np.all(np.isfinite(on_target)):
        raise ValueError("On-target energies must be a nonempty finite one-dimensional array.")
    count = on_target.size
    hh, ha, aa = [np.asarray(off_target[name], dtype=float) for name in (
        "handle_handle_energies", "antihandle_handle_energies", "antihandle_antihandle_energies",
    )]
    lower = np.tril_indices(count)
    cross = ~np.eye(count, dtype=bool)
    for matrix, evaluated in [(hh, lower), (aa, lower), (ha, cross)]:
        if matrix.shape != (count, count) or not np.all(np.isfinite(matrix[evaluated])):
            raise ValueError("Off-target matrices must match the pair count and contain finite evaluated entries.")

    # Mirror only evaluated entries; zero placeholders must never become competing interactions.
    hh = np.tril(hh) + np.tril(hh, -1).T
    aa = np.tril(aa) + np.tril(aa, -1).T
    ha = ha.copy()
    np.fill_diagonal(ha, np.inf)
    competitors = np.block([[hh, ha], [ha.T, aa]])
    partner_indices = np.argmin(competitors, axis=1)
    strongest_off = competitors[np.arange(2 * count), partner_indices]
    strand_on = np.tile(on_target, 2)
    gaps = strongest_off - strand_on
    return {
        "minimum_gap": float(np.min(gaps)),
        "mean_gap": float(np.mean(gaps)),
        "strand_gaps": gaps,
        "on_target_energies": strand_on,
        "strongest_offtarget_energies": strongest_off,
        "strongest_offtarget_indices": partner_indices,
    }


def association_to_complex_energies(verified):
    """Recover exact raw complex energies from unclipped association and monomer energies.

    The shared association helper caps energies at -1 kcal/mol. A capped entry cannot
    be inverted, so reject such inputs instead of silently changing a raw-complex score.
    Returned matrices preserve the canonical zero placeholders and do not mutate inputs.
    """
    on_target = np.asarray(verified["on_target_energies"], dtype=float)
    self_h = np.asarray(verified["self_energy_seqs"], dtype=float)
    self_a = np.asarray(verified["self_energy_rc_seqs"], dtype=float)
    count = on_target.size
    if on_target.ndim != 1 or count == 0 or self_h.shape != (count,) or self_a.shape != (count,):
        raise ValueError("Association and monomer arrays must match a nonzero pair count.")
    lower = np.tril_indices(count)
    cross = ~np.eye(count, dtype=bool)
    raw_on = on_target + self_h + self_a
    raw_off = {}
    for name, row_self, column_self, evaluated in [
        ("handle_handle_energies", self_h, self_h, lower),
        ("antihandle_handle_energies", self_h, self_a, cross),
        ("antihandle_antihandle_energies", self_a, self_a, lower),
    ]:
        matrix = np.asarray(verified["off_target"][name], dtype=float)
        if matrix.shape != (count, count):
            raise ValueError("Off-target matrix dimensions must match the pair count.")
        if np.any(matrix[evaluated] >= -1.0) or np.any(on_target >= -1.0):
            raise RuntimeError("Capped association energies require a fresh raw-complex calculation.")
        recovered = matrix + row_self[:, None] + column_self[None, :]
        raw_off[name] = np.zeros_like(matrix)
        raw_off[name][evaluated] = recovered[evaluated]
    if not all(np.all(np.isfinite(values)) for values in (raw_on, self_h, self_a, *raw_off.values())):
        raise ValueError("Non-finite energies cannot be converted into raw complex energies.")
    return {"on_target_energies": raw_on, "off_target": raw_off}
