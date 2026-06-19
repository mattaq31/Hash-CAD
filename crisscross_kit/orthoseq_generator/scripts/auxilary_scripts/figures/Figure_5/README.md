# Figure 5 Workflow

This folder now supports a three-arm comparison:

1. `search only`
   - uses the canonical long-seq benchmark workbook directly
   - no SeqWalk prior
2. `SeqWalk + postfilter`
   - generates a SeqWalk candidate pool
   - runs the thermodynamic hybrid search on top of that pool
3. `pure SeqWalk max orthogonality`
   - generates a direct SeqWalk `max_orthogonality(...)` library
   - evaluates the full generated set thermodynamically afterward

The old raw full-library SeqWalk Figure 5 path is no longer part of this
workflow.

## Scripts

- `prepare_data_f5_hybrid_seqwalk.py`
  - builds the `SeqWalk + postfilter` workbook

- `prepare_data_f5_seqwalk_max_orthogonality.py`
  - builds the `pure SeqWalk max orthogonality` workbook

- `plot_figure_5.py`
  - plots the three available arms
  - skips missing workbooks cleanly

## Data Sources

The `search only` arm is not generated in this folder. It is read directly from
the canonical benchmark workbook:

`crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq/data/batch_x______sigma1p0_seed41/len16/5p_none/hybrid_len16_5p_none_limitm8p16_budget10000000_init450_seed41.xlsx`

This path is hardcoded in `plot_figure_5.py`.

The two SeqWalk-related arms write their workbooks into this folder's local
`data/` directory.

## Reporting Semantics

The two method families are not treated identically:

- `search only` and `SeqWalk + postfilter`
  - have predefined thermodynamic search criteria
  - the threshold lines in their reports are actual design constraints

- `pure SeqWalk max orthogonality`
  - SeqWalk does not use those thermodynamic constraints during generation
  - the workbook stores the observed thermodynamic extrema of the generated set
  - this lets the dataset be reported in the same format without pretending it
    was designed under the same thermodynamic constraints

## Barcode / Reverse-Complement Identity

When `plot_figure_5.py` prints the worst off-target interaction, it reports:

- strand slot: `handle` or `antihandle`
- sequence identity: `barcode`, `revcombarcode`, or `n.a.`
- the full pair context for both participating pairs

Important detail:

- `handle` and `antihandle` are report/storage slots, not biological truth
- because sequence pairs are canonicalized, the barcode can appear in either
  slot
- `barcode` vs `revcombarcode` is only determined when the workbook contains
  provenance (`origin_seq_with_flank`)
- benchmark workbooks that do not preserve origin provenance are reported as
  `n.a.`

The printed worst-off-target summary is organized as:

1. the interacting pair IDs / strand slots / energy
2. `pair A = (handle, antihandle)`
3. `pair B = (handle, antihandle)`
4. one compact line for each interacting participant:
   - `sequence = ...`
   - `identity = barcode | revcombarcode | n.a.`
   - `slot = handle | antihandle`

The script also prints the worst secondary-structure former as:

1. pair ID and self-energy
2. `pair = (handle, antihandle)`
3. one compact participant line with:
   - `sequence = ...`
   - `identity = barcode | revcombarcode | n.a.`
   - `slot = handle | antihandle`

## Typical Use

1. generate or reuse the `SeqWalk + postfilter` workbook
2. generate the `pure SeqWalk max orthogonality` workbook
3. run `plot_figure_5.py`

The plotting script will use whichever of the three workbooks are present.
