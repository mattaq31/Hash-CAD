"""
Read verified XLSX search reports written by `search_reporting.py`.

This module is the light-weight counterpart to the shared report writer. It is
intended for plotting, analysis, and notebook-style inspection code that needs
stable access to the standard workbook sheets without rewriting the same pandas
boilerplate in every script.

The functions here deliberately stay simple:

- metadata is returned as a plain `dict`
- tabular sheets are returned as plain pandas `DataFrame`s
- off-target matrices remain ordinary 2D DataFrames with their original string
  labels intact
- any parsing of matrix axis labels is provided as a separate helper rather
  than being forced into the matrix loader
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re

import pandas as pd

from orthoseq_generator.sequence_generation import normalize_reference_sequences


NA_VALUES = {"", "N.A.", "n.a.", "NA", "na", "None", "none"}
OFFTARGET_SHEET_NAMES = {
    ("selected", "hh"): "selected_hh",
    ("selected", "hah"): "selected_hah",
    ("selected", "ahah"): "selected_ahah",
    ("seed", "hh"): "seed_hh",
    ("seed", "hah"): "seed_hah",
    ("seed", "ahah"): "seed_ahah",
}


def _parse_metadata_value(value):
    """Convert one run-metadata cell into a more useful Python value."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, str):
        text = value.strip()
        if text in NA_VALUES:
            return None
        if text == "True":
            return True
        if text == "False":
            return False
        if re.fullmatch(r"[-+]?\d+", text):
            return int(text)
        if re.fullmatch(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", text):
            return float(text)
        return text
    return value


def _load_sheet(report_path: str | Path, sheet_name: str, *, index_col=None) -> pd.DataFrame:
    """Read one required workbook sheet."""
    return pd.read_excel(Path(report_path), sheet_name=sheet_name, index_col=index_col)


def _load_sheet_or_none(report_path: str | Path, sheet_name: str, *, index_col=None) -> pd.DataFrame | None:
    """Read one optional workbook sheet, returning `None` when absent."""
    report_path = Path(report_path)
    with pd.ExcelFile(report_path) as xls:
        if sheet_name not in xls.sheet_names:
            return None
    return pd.read_excel(report_path, sheet_name=sheet_name, index_col=index_col)


def load_metadata(report_path: str | Path) -> dict:
    """
    Load the `run_metadata` sheet as a plain dictionary.

    Values receive small convenience parsing:

    - workbook NA markers such as `N.A.` become `None`
    - `True` / `False` become booleans
    - numeric-looking strings become `int` or `float`

    Everything else is left as a string so the loader does not invent
    benchmark-specific semantics.
    """
    metadata_df = _load_sheet(report_path, "run_metadata")
    metadata = {}
    for _, row in metadata_df.iterrows():
        key = str(row["key"]).strip()
        if not key or key == "nan":
            continue
        metadata[key] = _parse_metadata_value(row["value"])
    metadata.setdefault("nupack.energy_type", "total")
    return metadata


def load_found_pairs(report_path: str | Path) -> pd.DataFrame:
    """Load the `found_pairs` sheet."""
    return _load_sheet(report_path, "found_pairs")


def load_reference_sequences(report_path: str | Path | BytesIO, *, required=True, sheet_name=None) -> list[str]:
    """Read the first valid external-library layout, without combining sheets.

    Try `found_pairs` with `seq` and `rc_seq` columns, then `reference_sequences`
    with a `sequence` column. Normalize explicit strands and deduplicate them.
    `sheet_name` restricts reading to one layout; report replay uses this to
    restore only its original external pool. `required=False` allows absent
    sheets, but malformed input still raises an error identifying the problem.
    """
    layouts = {"found_pairs": ["seq", "rc_seq"], "reference_sequences": ["sequence"]}
    if sheet_name is not None and sheet_name not in layouts:
        raise ValueError("Reference sheet must be 'found_pairs' or 'reference_sequences'.")
    candidates = [sheet_name] if sheet_name is not None else list(layouts)
    errors = []
    with pd.ExcelFile(report_path) as workbook:
        for candidate in candidates:
            if candidate not in workbook.sheet_names:
                continue
            columns = layouts[candidate]
            data = pd.read_excel(workbook, sheet_name=candidate, keep_default_na=False)
            if not all(column in data.columns for column in columns):
                errors.append(f"'{candidate}' requires columns {', '.join(columns)}")
                continue
            try:
                strands = []
                for column in columns:
                    # Normalize each column first so errors retain Excel row numbers.
                    strands.extend(normalize_reference_sequences(data[column], first_row=2))
                return normalize_reference_sequences(strands)
            except ValueError as exc:
                errors.append(f"'{candidate}': {exc}")
    if not errors and not required:
        return []
    expected = "'found_pairs' sheet with seq and rc_seq columns or 'reference_sequences' sheet with a sequence column"
    details = "; ".join(errors) if errors else "No supported sheet found."
    raise ValueError(f"Expected {expected}. {details}")


def load_external_crossref(report_path: str | Path) -> pd.DataFrame | None:
    """Load the optional complete selected-to-reference matrix with its strand labels."""
    return _load_sheet_or_none(report_path, "external_crossref", index_col=0)


def load_seed_pairs(report_path: str | Path) -> pd.DataFrame | None:
    """Load the optional `seed_pass_pairs` sheet for hybrid-style runs."""
    return _load_sheet_or_none(report_path, "seed_pass_pairs")


def load_search_progress(report_path: str | Path) -> pd.DataFrame | None:
    """
    Load the optional `search_progress` sheet.

    The returned DataFrame is intentionally raw. Different algorithms write
    different progress schemas, so callers are expected to interpret the
    columns they care about locally.
    """
    return _load_sheet_or_none(report_path, "search_progress")


def load_offtarget_matrix(report_path: str | Path, family: str, interaction: str) -> pd.DataFrame:
    """
    Load one off-target energy matrix from the workbook.

    Parameters
    ----------
    family:
        Either `selected` for the final found-pair set or `seed` for the
        hybrid seed-set matrices.

    interaction:
        One of `hh`, `hah`, or `ahah`.

    Returns
    -------
    pandas.DataFrame
        A normal 2D DataFrame whose row and column labels remain the original
        workbook strings such as `2:H:CGTAAGAGGTAATAGGGCAA`.
    """
    sheet_name = OFFTARGET_SHEET_NAMES[(family, interaction)]
    return _load_sheet(report_path, sheet_name, index_col=0)


def load_offtarget_matrices(report_path: str | Path, family: str = "selected") -> dict[str, pd.DataFrame]:
    """Load the three off-target matrices for one matrix family."""
    return {
        "handle_handle_energies": load_offtarget_matrix(report_path, family, "hh"),
        "antihandle_handle_energies": load_offtarget_matrix(report_path, family, "hah"),
        "antihandle_antihandle_energies": load_offtarget_matrix(report_path, family, "ahah"),
    }


def parse_pair_label(label: str) -> tuple[int, str, str]:
    """Split one matrix-axis label into `(pair_id, strand, sequence)`."""
    pair_id, strand, sequence = str(label).split(":", 2)
    return int(pair_id), strand, sequence


def parse_axis_labels(labels) -> pd.DataFrame:
    """
    Parse a collection of matrix-axis labels into a small lookup DataFrame.

    This is the optional structured view for callers that want to inspect the
    pair id, strand type, or raw sequence without altering the matrix itself.
    """
    rows = []
    for label in labels:
        pair_id, strand, sequence = parse_pair_label(label)
        rows.append(
            {
                "raw_label": str(label),
                "pair_id": pair_id,
                "strand": strand,
                "sequence": sequence,
            }
        )
    return pd.DataFrame(rows)
