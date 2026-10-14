# Historical investigation

This note preserves the investigation before cleanup. Its paths and script names describe the former layout.
Archived outputs are grouped under `15C_Na1M_Mg0M/`, `assembly_37C_89_pairs/`, `standalone_evaluation/`, and `design_criteria/`. See the current parent README for the active workflow.

# Published polycube Menger library

This folder extracts and evaluates the published sticky-end library from Diep et al.,
*Universal 3D Nanoscale Assembly with DNA Polycubes*, [ChemRxiv DOI 10.26434/chemrxiv-2025-qbk3f](https://doi.org/10.26434/chemrxiv-2025-qbk3f).
The full published library is retained without thermodynamic filtering or redesign.

## Files

- `sources/diep_polycubes_supplementary.pdf`: the downloaded supplementary PDF.
- `sources/authors_code/`: unchanged snapshots of the authors' sequence-design code and example commands.
- `extract_menger_sequences.py`: extraction, sequence decomposition, and pairing audit.
- `data/menger_published_sequences.xlsx`: exposed pairs, source handles, scaffold-binding references, and metadata.
- `data/menger_handle_entries.tsv`: every Table S22 handle with its decomposition and source provenance.
- `evaluate_menger_sequences.py`: direct NUPACK verification, canonical report export, and repo-style histograms.
- `evaluate_orthoseq_comparison.py`: reevaluate an exported OrthoSeq library at the same model as the Menger reference.
- `sequence_quality.py`: local helpers for per-strand specificity scores and energy-convention conversion.
- `test_sequence_quality.py`: local checks of specificity scoring and matrix/strand mapping.
- `results/assembly_37C_Na50mM_Mg12p5mM/menger_specificity_gaps.tsv`: per-strand scores and limiting competitors.
- `audit_menger_design_criteria.py`: check the published cores against candidate-screening and MFE filters.
- `results/assembly_37C_Na50mM_Mg12p5mM/`: current assembly-model report and energy summaries.
- `plots/assembly_37C_Na50mM_Mg12p5mM/`: current assembly-model vector PDF and SVG histograms.
- Existing files directly under `results/` and `plots/`: preserved original 15 C / 1 M Na / 0 Mg evaluation and audit.

## Extraction

Source: [supplementary PDF](https://www.cambridge.org/engage/api-gateway/coe/assets/orp/resource/item/6942549ce3cb457e131a20ae/original/supplementary-material.pdf),
Table S22, section S4.7, printed/PDF pages 100-109. Table S18 on pages 91-92 supplies the scaffold-binding
segments for each face/strand position. Pages in the workbook are 1-based and match the printed page numbers.

The script reads layout-preserved PDF rows and joins DNA-only continuation lines. For each S22 entry it
matches the corresponding S18 scaffold-binding prefix, removes that prefix, and separates exactly 12 T
bases from the remaining core. Leading T bases belonging to the core are preserved. The exposed sequence is
`5'-T12-core-3'`. Both members of each pair have their own 5' T12 spacer; the second full exposed strand is
not the reverse complement of the first full exposed strand.

Verified extraction counts: **216 published handles, 192 unique cores, and 96 reverse-complementary pairs**.
All cores are 9 nt and all spacers are T12. The 216 rows cover 54 complete four-strand faces across CT0-CT18.
Every full sequence reconstructs exactly from its S18 prefix, spacer, and core. All published occurrences
remain in `source_handles`, including repeated cores. Pair IDs are assigned deterministically by sorting
the complementary core pairs. Storage slots H/A do not imply biological direction or cube identity.

The extractor normalizes labels as `CT{cube}_{face}_{strand}` and retains the PDF-extracted label text.
The workbook records the PDF SHA-256, DOI, table/page provenance, binding references, and extraction method.

**Source discrepancy:** S1.8, page 33, reports Menger `L=8`, `Tm=15 +/- 0.5 C`, and GC fraction `5/8`.
The actual S22 cores are 9 nt with four GC bases each (GC fraction 4/9). The extraction uses the published sequences
and retains the reported settings as source metadata rather than modifying the sequences to fit them.

## Thermodynamic settings and conventions

The published workflow has different conditions for its two computational stages:

| Stage | Temperature | Sodium | Magnesium | Strand concentration |
| --- | --- | --- | --- | --- |
| Melting-temperature screening | Target 15 +/- 0.5 C in S1.8 | 0.05 M | 0.0125 M | 10 nM per strand |
| Optimization example | 15 C | 1 M (NUPACK default) | 0 M (NUPACK default) | Not used for complex energies |

These settings were checked against the public repository at commit
[`9e0203cda2afac87399687f906f35eec8f6e0f01`](https://github.com/sulcgroup/DNA3Dpolycubes/tree/9e0203cda2afac87399687f906f35eec8f6e0f01/SEdesign):

- `create_same_tm_seq_library.py`: `Tm_NN` uses 50 mM Na, 12.5 mM Mg, 10 nM per strand; its NUPACK tube
  model uses `sodium=0.05`, `magnesium=0.0125`, and 10 nM per strand.
- `example_optimization_call.sh`: explicitly passes `--celsius 15` and a T12 spacer.
- `orthogonal_seq_screen_parallel.py`: uses `Model(material='dna', celsius=celsius)` without salt overrides.
  Its fallback temperature is 20 C when no argument is provided; the example overrides it to 15 C.
- `sequence_optimization_functions.py`: adds the spacer before folding and cross-interaction evaluation.
  Its matrix stores raw complex ensemble free energies.
- [NUPACK model documentation](https://docs.nupack.org/model/): omitted salts default to 1 M sodium and
  zero magnesium; the ensemble defaults to `stacking`.

The original evaluation used **15 C, 1 M sodium, zero magnesium, DNA, and the stacking ensemble**, based on
the fresh-matrix model in the published optimization example. That report and its plots remain directly under
`results/` and `plots/`. **S1.8 does not state the temperature of the original Menger interaction-matrix run,
and the repository does not identify a Menger-specific command.** A cached authors' matrix also does not record
the model that produced it. The original Menger calculation settings remain unconfirmed.

The current evaluation script instead uses an explicit **assembly-buffer model: 37 C, 0.05 M sodium,
0.0125 M magnesium, DNA, and the stacking ensemble**. S2.1 (pages 35-36) reports Menger assembly in
1x TAE containing 12.5 mM Mg2+, with a slow ramp from 44 to 28.5 C followed by cooling to and holding at 20 C.
Figure S39 (page 57) shows increasing hydrodynamic sizes during cooling. We choose 37 C as a representative
comparison temperature within the annealing window; it is not a reported sequence-design calculation temperature.

**Model assumptions:** 50 mM monovalent salt is an explicit approximation, informed by the authors' Tm-screening
code. The paper's statement of 1x TAE does not specify NUPACK's sodium concentration. Magnesium is entered as
the reported nominal 12.5 mM, without a reconstruction of free-ion concentration. The report records these
assumptions and does not claim an exact reproduction of the experimental buffer or the original design run.
Association free energies do not use a strand-concentration parameter.

Output subdirectories are derived from the actual temperature and salt configuration, so the current run
does not overwrite the original model's artifacts. All 96 published pairs remain unfiltered. No search thresholds
from the earlier model are transferred to this evaluation; new search windows must use the new measured energies.

Per our evaluation choice, energies use the repo's **association energy** convention (`total`):
`DeltaG = G_AB - G_A - G_B`, or `G_AA - 2 G_A` for homodimers. This differs from the authors' raw-complex
matrix convention. Self-folding values are monomer ensemble free energies. The shared energy helper caps
association values greater than -1 kcal/mol at -1; this is recorded in the output metadata. The NUPACK
version and resolved DNA parameter model are also recorded; the authors do not specify an exact version.

The main off-target histogram contains each distinct cross-pair interaction once: 18,240 interactions
for 96 pairs. The canonical matrices also contain all 192 homodimers, which are listed separately in the
`homodimers` sheet. Zero matrix placeholders are not evaluated interactions. No thresholds are presented
as design constraints for this published library.

## Per-strand specificity score

The evaluation also rates the library by the objective in the authors' optimizer: the minimum, over all
strands, of the energy difference between an unintended partner and that strand's intended partner.
Every library strand can compete, including the strand itself (a homodimer); only the intended partner
is excluded. A larger positive gap indicates better worst-case separation. The authors optimize this
score for a requested, fixed number of pairs; OrthoSeq searches for a large library within energy bounds.

The local `sequence_quality.compute_specificity_gaps` function reads the canonical
on-target array and off-target matrices. It mirrors the evaluated triangular HH/AA entries and ignores
zero placeholders. The `specificity_gaps` report sheet and TSV contain 192 strand records per energy
convention, with the on-target energy, strongest competing energy, gap, and competitor provenance.
The `energy_summary` sheet/TSV contains the minimum and mean per-strand gap for each convention.

Both conventions are reported at the same model conditions:

- `total`: association energies, `G_AB - G_A - G_B`, as in our primary energy plots.
- `totalu`: raw complex energies, `G_AB`, as in the published optimization objective.

For a strand `i`, its intended partner `k`, and competitor `j`, the gap transformation is
`gap_total = gap_totalu + G_k - G_j`. The rated strand's monomer energy cancels, while the partner
monomer energies remain. The two scores are equal when those partner energies are equal; their limiting
competitors and rankings can otherwise differ.

Raw complex energies are recovered from the already verified association and monomer energies when
none of the evaluated association entries were capped. If capped entries occur, the script instead
uses `verify_selected_pairs` with the existing backend's `totalu` mode. The backend's normal -1 kcal/mol
cap is retained. At the current Menger model, no association entries are capped, so conversion is exact
and no additional full NUPACK evaluation is needed for the second convention.

Intended partners are excluded by identity. The published implementation masks all exact-zero energy
differences; our helper retains any unintended interaction with zero gap. There are no such unintended
ties in this evaluated library. These ratings use our stated common model and do not reproduce an
unconfirmed original Menger design run.

## Current evaluation findings (37 C / 50 mM Na / 12.5 mM Mg)

With the assembly-model assumptions above, on-target association energies span **-12.489 to -11.515 kcal/mol**,
with mean **-12.042 kcal/mol** and population standard deviation **0.224 kcal/mol**.
The strongest cross-pair association is **-9.686 kcal/mol**, between `CT5_BACK_2` (`T12-CGCAACTAT`)
and `CT4_BACK_2` (`T12-GCGACTTAT`). The least favorable on-target is therefore 1.829 kcal/mol stronger
than the strongest cross-pair off-target. The strongest homodimer association is **-9.009 kcal/mol**,
and the strongest monomer self-folding is **-0.734 kcal/mol**.

The minimum per-strand specificity gap, including homodimers, is **2.261829 kcal/mol** for `total`
and **2.331296 kcal/mol** for `totalu`; their mean per-strand gaps are **3.464572** and **3.479007 kcal/mol**.
Both minimum scores are limited by `CT4_BACK_2` (`T12-GCGACTTAT`) interacting with `CT5_BACK_2`
(`T12-CGCAACTAT`). The raw-complex minimum is 0.069467 kcal/mol larger at this model.
These per-strand values compare each competitor with the intended on-target of the strand involved,
so they differ from the global histogram separation of 1.829 kcal/mol.

The complete report contains all 96 pairs, 18,240 distinct cross-pair interactions, and 192 homodimers.
Independent direct NUPACK calls reproduced a representative on-target, the strongest cross-pair interaction,
the strongest homodimer, and the minima of both monomer-energy columns. Saved model metadata, interaction
counts, and energy summaries were checked after reopening the workbook; all report sheets and both vector
PDF plots were rendered and inspected. Input and original evaluation artifact hashes remained unchanged.
Both specificity minima were independently reproduced with direct NUPACK complex and monomer energies.
A separate exhaustive loop checked every strand against its 191 unintended competitors, and unit tests
cover HA orientation, triangular placeholders, homodimers, zero-gap ties, and raw-energy conversion.

These values characterize the published library at our chosen common model. They are not inferred author
selection thresholds and are not directly comparable to the original 15 C / 1 M Na / 0 Mg search outputs.

## Earlier 89-pair export reevaluated at the assembly model

`evaluate_orthoseq_comparison.py` initially reevaluated the saved 89-pair export from
`/Users/floriankatzmeier/Downloads/ortho_sequences (1).xlsx` at **37 C, 50 mM Na, and 12.5 mM Mg**.
Those sequences were selected at 15 C / 1 M Na / 0 Mg; this is a fixed-library reevaluation, not a new search
or evidence about an unexported ongoing run. All 89 pairs and their T12 spacers are retained.

The script checks that the existing 96-pair Menger report has the same model settings, NUPACK version,
and stacking ensemble. Both original input hashes and model/search metadata are recorded in the new report.
The original export and the Menger reference are not modified. Raw complex energies are evaluated in
the existing backend's `totalu` mode when association capping prevents exact reconstruction.

| Minimum per-strand gap (kcal/mol) | Menger, 96 pairs | OrthoSeq, 89 pairs |
| --- | --- | --- |
| `total` | 2.261829 | 3.109674 |
| `totalu` | 2.331296 | 2.931016 |

OrthoSeq has the larger minimum gap in both conventions for these fixed libraries. Its raw-complex gap is
approximately 25.7% larger. The pair counts differ; the comparison does not establish a result at matched
library size. OrthoSeq's on-target range is **-13.137 to -11.269 kcal/mol** (mean **-11.987**), strongest
cross-pair off-target **-8.561 kcal/mol**, strongest homodimer **-7.892 kcal/mol**, and strongest monomer
self-folding **-0.643 kcal/mol**.

The new report is `results/assembly_37C_Na50mM_Mg12p5mM/orthoseq_89_energy_evaluation.xlsx`;
its `comparison` sheet and companion `orthoseq_89_vs_menger.tsv` contain the library summaries.
The `specificity_gaps` sheet contains all 740 per-strand ratings across both libraries and conventions.
The canonical pair sheet and matrices contain OrthoSeq's newly evaluated energies: 15,664 distinct
cross-pair interactions and 178 homodimers. Independent direct NUPACK calls reproduced all four minimum
gaps. Model settings, source identity, counts, and summary values were checked after reopening the report,
and every report sheet was rendered and inspected.

## Completed 100-pair search at the assembly model

The completed run is copied without modification from `search_runs/` to
`results/assembly_37C_Na50mM_Mg12p5mM/orthoseq_assembly_search_2026-10-08_19-51-55.xlsx`.
It contains 100 pairs selected at 37 C, 50 mM sodium, and 12.5 mM magnesium, using association energies.
Its on-target window is [-12.50, -11.70] kcal/mol, off-target limit -8.05 kcal/mol, and self-folding
limit -0.50 kcal/mol. Cores are 9 nt with a 5' T12 spacer; AAA/CCC/GGG/TTT exclusions apply to the core.
The run used seed 42, 450 initial candidates, 5000 graph iterations, Gmax with rule tie-breaking,
prune fraction 0.4, and an unlimited NUPACK budget. It reports 1,454,030 search NUPACK calls.

The evaluation and plotting scripts now select this run. Earlier 89-pair outputs remain available.
All 100 pairs are retained and reevaluated with the same model as the complete 96-pair Menger library.
The new association energies agree with the saved search energies to 1e-10 kcal/mol. Raw complex
energies are computed directly because weak association entries were clipped at the backend's -1 floor.

| Quantity (kcal/mol except pair count) | Menger | OrthoSeq |
| --- | --- | --- |
| Pair count | 96 | 100 |
| Mean on-target association energy | -12.042183 | -11.999371 |
| Strongest cross-pair association | -9.686471 | -8.049794 |
| Strongest homodimer association | -9.009408 | -7.892037 |
| Strongest self-folding | -0.733751 | -0.499524 |
| Minimum per-strand association gap (`total`) | 2.261829 | 3.668551 |
| Minimum per-strand complex gap (`totalu`) | 2.331296 | 3.529912 |

At this common model, OrthoSeq has four more pairs and larger minimum gaps in both conventions.
The authors' raw-complex gap metric is about 51.4% larger. The mean on-target association energy is
0.042812 kcal/mol less negative for OrthoSeq; the improvement is in unwanted-interaction separation.
This is a comparison of two complete libraries with unequal sizes, not a matched-size optimization test
or a reproduction of the authors' unconfirmed original design run.

The comparison report is `results/assembly_37C_Na50mM_Mg12p5mM/orthoseq_100_energy_evaluation.xlsx`,
with the summary in `orthoseq_100_vs_menger.tsv`. Its 784 specificity records rate every strand of both
libraries under both conventions. The canonical OrthoSeq matrices contain 19,800 distinct cross-pair
interactions plus 200 homodimers. Independent direct NUPACK calls reproduced all four minimum gaps;
source identities, model settings, matrix values, counts, and summary statistics were checked.

The final stacked figure is `plots/assembly_37C_Na50mM_Mg12p5mM/menger_vs_orthoseq_100_comparison.pdf`,
with one association-energy panel and one self-folding panel per library. Its caption, settings (TOML),
and table (TSV) are stored alongside it. All four x axes are labeled and full-data histogram normalization
is preserved when the association-energy display is cropped. The plain table reports measured on-target
range and mean, minimum off-target energy, and minimum self-folding energy under the OrthoSeq criteria,
followed by the measured minimum complex free energy gap under the Polycube criterion. Both sections use kcal/mol.
The dataset is labeled "Polycubes" in the figure and table; the caption identifies the published Menger-cube library.

## Original evaluation findings (15 C / 1 M Na / 0 Mg)

At the original settings, on-target association energies span **-17.322 to -15.914 kcal/mol**,
with mean **-16.645 kcal/mol**.
The strongest cross-pair association is **-12.169 kcal/mol**, between the exposed strands from
`CT12_TOP_0` (`T12-AGGTTCGTA`) and `CT9_RIGHT_3` (`T12-ACGAATCTG`). The least favorable on-target
is therefore 3.745 kcal/mol stronger than the strongest cross-pair off-target.
The strongest homodimer association is **-11.571 kcal/mol**. The strongest monomer self-folding
is **-1.105 kcal/mol**, for `CT9_FRONT_3`.

The full evaluation completed for all 96 pairs, 18,240 distinct cross-pair interactions, and 192 homodimers.
Independent direct NUPACK calls reproduced a representative on-target, the strongest cross-pair interaction,
the strongest homodimer, and the minima of both monomer-energy columns. The extracted full sequences were
also checked against an independent PDFKit text extraction, and the final vector PDFs were rendered and inspected.

## Audit of the reported design criteria

The complete repository tree at the pinned commit contains generic SEdesign examples and development notebooks,
but no identified Menger-specific sequence-design command or input/output record. The example input file contains
654 8-nt sequences and does not contain the published 9-nt cores. It is not the Menger candidate library.

An independent audit uses the exact Biopython call in `create_same_tm_seq_library.py` on the bare published cores:
10 nM of each strand, 50 mM sodium, 12.5 mM magnesium, salt correction 7, and the default DNA_NN3 table.
With **Biopython 1.85**, the published core Tm values span **21.926698-24.099621 C**; **0/192** pass 15 +/- 0.5 C.
Using **NUPACK 4.0.2.0 / dna04.2** at the same salts, 15 C, and strand concentrations, **0/96 pairs** pass the
authors' initial NUPACK screening gate of 0.45-0.55 free-strand fraction. This is a gate check, not a NUPACK Tm sweep.

All published cores contain exactly four GC bases, contain all four nucleotide types, and exclude identical-base
triples. At the optimization-example model (15 C, 1 M sodium, zero magnesium), **189/192** exposed T12-core strands
pass the zero-base-pairs MFE filter. This MFE criterion is different from an ensemble self-energy cutoff.

These checks establish incompatibilities with the reported workflow under the recorded audit software versions.
They do not establish what the authors actually ran: their exact versions, screening branch, original inputs,
matrix cache settings, and Menger-specific command remain unconfirmed. The 15 C target therefore cannot serve
as a verified candidate-selection constraint for reproducing the published Menger library.

The per-core audit is saved in `results/menger_design_criteria_audit.tsv`, with settings in
`results/menger_design_criteria_audit_settings.txt`. Biopython was loaded from an isolated temporary wheel;
the configured project environment was not modified. Rerunning this audit additionally requires Biopython.

## Running

`plot_menger_orthoseq_comparison.py` reads the two existing assembly-model reports and writes a stacked
comparison PDF with a plain table. It calls the unchanged `plot_on_off_target_histograms` and
`plot_self_energy_histogram` functions; axes creation is supplied locally for each panel because these
functions create standalone figures. All layout and proportional scaling are confined to this auxiliary
script. The figure is 177.8 mm wide to accommodate self-folding panels next to the association panels.
The two libraries share association axes and bins, and separately share self-folding axes and bins.
The association display ends at -4 kcal/mol; identical bins cover the complete data before cropping,
so each histogram retains its full-data density normalization. The table contains achieved values,
with separate OrthoSeq association/self-folding and Menger raw-complex-gap sections. The off-target
cutoff is the minimum measured unintended association energy, including homodimers. The Menger gap
uses `totalU` at the same model conditions, not association energies or inferred original design settings.
Companion settings use TOML; the script also exports the table as TSV and the caption as plain text.
It does not export comparison PNG or SVG files and does not require a PDF-processing package.

Use the existing `crisscross-kit` environment with OrthoSeq installed. Extraction additionally requires
`pypdf`; energy evaluation requires NUPACK. Run from the repository root:

```bash
python crisscross_kit/orthoseq_generator/scripts/auxilary_scripts/review_comments/polycube_comparison/extract_menger_sequences.py
python crisscross_kit/orthoseq_generator/scripts/auxilary_scripts/review_comments/polycube_comparison/evaluate_menger_sequences.py
python crisscross_kit/orthoseq_generator/scripts/auxilary_scripts/review_comments/polycube_comparison/evaluate_orthoseq_comparison.py
python crisscross_kit/orthoseq_generator/scripts/auxilary_scripts/review_comments/polycube_comparison/plot_menger_orthoseq_comparison.py
```

Configuration lives inside each script's `if __name__ == "__main__":` block. The plotting script reuses
`load_found_pairs`, `load_metadata`, `verify_selected_pairs`, `write_hybrid_search_result_xlsx`,
`plot_on_off_target_histograms`, and `plot_self_energy_histogram`. The extractor reuses `revcom` and
`sorted_key`. Evaluation uses the exposed strands only, excluding their scaffold-binding segments.
