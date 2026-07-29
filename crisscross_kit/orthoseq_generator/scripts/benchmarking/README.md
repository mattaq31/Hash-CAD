# Benchmarking

This subtree contains two separate benchmark workflows.

## Short Seq

`short_seq/` is the saved-dataset benchmark workflow.

Use it when you want to:

- build finite benchmark datasets
- run offline benchmark sweeps on those saved datasets
- compare multiple algorithms against the same frozen candidate pool

Entry point:

- [short_seq/README.md](short_seq/README.md)

## Long Seq

`long_seq/` is the live-search benchmark workflow.

Use it when you want to:

- generate physical benchmark conditions from a prep TOML
- run the live naive or hybrid search on sampled sequence pairs
- analyze the canonical `batch_x...` benchmark outputs

Entry point:

- [long_seq/README.md](long_seq/README.md)

## Rule of Thumb

- if the benchmark starts from `dataset.toml` / `dataset.npz`, it belongs to `short_seq/`
- if the benchmark starts from generated condition TOMLs and writes live workbooks under `data/<batch_name>/`, it belongs to `long_seq/`
