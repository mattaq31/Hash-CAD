# Polycube comparison

Compare the published Menger-cube sticky ends from *Universal 3D Nanoscale Assembly with DNA Polycubes*
([DOI](https://doi.org/10.26434/chemrxiv-2025-qbk3f)) with the completed OrthoSeq search.

## Pipeline

Run the commands below from this directory in the project's `crisscross-kit` environment with NUPACK 4 installed.
Extraction also requires `pypdf`.

### 1. Add the published source

Download the [supplementary PDF](https://www.cambridge.org/engage/api-gateway/coe/assets/orp/resource/item/6942549ce3cb457e131a20ae/original/supplementary-material.pdf)
and save it as `sources/diep_polycubes_supplementary.pdf`.
`sources/` is gitignored, including the reference snapshots of the authors' code in `sources/authors_code/`.
The authors' code is not required to run this pipeline.

### 2. Extract the Polycube sequences

```bash
python preparation/extract_menger_sequences.py
```

This reads Table S22 (pages 100–109), using Table S18 to identify the origami-binding segments.
It writes `data/menger_published_sequences.xlsx`: 96 unique complementary pairs in `found_pairs`, 216 handle
occurrences in `source_handles`, and the binding references and extraction metadata in separate sheets.
Both libraries are evaluated as 5' T12 followed by the 9-nt core, without the origami-binding segment.
The published table contains 9-nt cores despite the 8-nt description in Section S1.8; the table sequences are retained.

### 3. Run the OrthoSeq search

```bash
python preparation/run_orthoseq_assembly_search.py
```

The search writes a verified report to `data/orthoseq_assembly_search_<timestamp>.xlsx`.
Its settings are in the script's execution block: 37 °C, 50 mM sodium, 12.5 mM magnesium, 9-nt cores with T12,
on-target range −12.5 to −11.7 kcal/mol, off-target limit −8.05 kcal/mol, and self-folding limit −0.5 kcal/mol.
The script explicitly sets the backend model and energy convention before searching and verifying.

The completed 100-pair report is already in `data/`, so this step can be skipped when reproducing the current figure.
For a new search, set its report filename in `orthoseq_report` in `prepare_comparison_data.py` and in
`reports["OrthoSeq"]["total"]` in `plot_polycube_comparison.py`.

### 4. Prepare the energy reports

```bash
python prepare_comparison_data.py
```

Preparation reads the extraction workbook and directly computes both Polycube energy conventions and OrthoSeq
complex energies using `verify_selected_pairs()`. OrthoSeq association energies are reused from the search report.
Every verification explicitly supplies DNA, 37 °C, 50 mM sodium, 12.5 mM magnesium, and its energy type;
verification configures the backend and workers with these settings.
Reports use `write_hybrid_search_result_xlsx()` and its standard energy matrices; Polycube reports retain source handles.

### 5. Plot the comparison

```bash
python plot_polycube_comparison.py
```

Plotting reads the four reports below and uses the existing repository histogram functions.
It exports only `plots/assembly_37C_Na50mM_Mg12p5mM/polycubes_vs_orthoseq_100_comparison.pdf`.
The figure is 165.1 mm wide to match the manuscript text width, and 142 mm high, with no embedded caption.

## Data

All inputs and Excel reports are in `data/`. Generated data and plot folders are gitignored, including archived outputs:

| Library | Association energy (`total`) | Complex free energy (`totalu`) |
|---|---|---|
| Polycubes | `menger_total.xlsx` | `menger_totalu.xlsx` |
| OrthoSeq | `orthoseq_assembly_search_2026-10-08_19-51-55.xlsx` | `orthoseq_totalu.xlsx` |

The extraction workbook is the published sequence input; no duplicate CSV or TSV export is needed.
`total` means association free energy, G_AB − G_A − G_B; `totalu` means complex ensemble free energy, G_AB.
Both use the NUPACK DNA stacking ensemble. These are our common evaluation conditions, not confirmed author design settings.

## Figure

The panels show association-energy distributions and monomer ensemble self-folding energies for each library.
The table reports measured on-target range and mean, strongest off-target interaction, minimum self-folding energy,
and minimum specificity gap. The gap is calculated per strand from complex free energies, excluding its intended
partner and including homodimers: min_i [min_(j ≠ intended_i) G_ij − G_i,intended_i]. Larger gaps are better.

`comparison_functions.py` holds the sequence reader, report writer, gap calculation, and figure function.
The execution scripts hold their paths and settings inside `if __name__ == "__main__":`.
Inputs are assumed to follow the extraction and standard report formats. `archive/` retains previous scripts and results.
