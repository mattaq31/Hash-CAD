#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import shutil
import zipfile


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"copied file: {src} -> {dst}")


def copy_tree(src: Path, dst: Path, *, ignore=None) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=ignore)
    print(f"copied tree: {src} -> {dst}")


def ignore_common_junk(_dir: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        if name in {".DS_Store", ".gitignore"}:
            ignored.add(name)
        elif name == "__pycache__":
            ignored.add(name)
        elif name.startswith("._"):
            ignored.add(name)
        elif name.startswith("~$") and name.endswith(".xlsx"):
            ignored.add(name)
    return ignored


def ignore_long_seq_batch_junk(_dir: str, names: list[str]) -> set[str]:
    ignored = ignore_common_junk(_dir, names)
    if "auxiliary_analysis" in names:
        ignored.add("auxiliary_analysis")
    return ignored


def clean_tree(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        name = path.name
        if name in {".DS_Store", ".gitignore"} or name == "__pycache__":
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
        elif name.startswith("._") and path.is_file():
            path.unlink()
        elif name.startswith("~$") and name.endswith(".xlsx") and path.is_file():
            path.unlink()


def zip_tree(src_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src_dir.rglob("*")):
            if path.is_file():
                zf.write(path, arcname=path.relative_to(src_dir.parent))
    print(f"wrote zip: {zip_path}")


if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    scripts_dir = script_dir.parent
    benchmark_dir = scripts_dir / "benchmarking"
    figure5_dir = scripts_dir / "auxilary_scripts" / "figures" / "Figure_5"

    readme_source = benchmark_dir / "ZENODO_BENCHMARK_README_DRAFT.md"
    staging_root = benchmark_dir / "zenodo"
    package_root = staging_root / "benchmark_data"
    standalone_readme = staging_root / "README.md"
    package_readme = package_root / "README.md"
    zip_path = staging_root / "orthoseq_benchmark_data.zip"

    short_seq_dataset_dir = benchmark_dir / "short_seq" / "data" / "len4_7_tttt5p_noGGGG"
    short_seq_extracted_dir = benchmark_dir / "short_seq" / "short_sequences"

    long_seq_generated_batches = [
        "batch_x_TTTT_sigma1p0_seed41",
        "batch_x______sigma1p0_seed41",
        "batch_x25TTTT_sigma1p0_seed41",
        "batch_x25_____sigma1p0_seed41",
    ]
    long_seq_generated_dir = benchmark_dir / "long_seq" / "configs" / "generated"
    long_seq_data_dir = benchmark_dir / "long_seq" / "data"
    long_seq_extracted_dir = benchmark_dir / "long_seq" / "long_sequences"

    figure5_seqwalk_max = (
        figure5_dir / "data" / "figure5_seqwalk_max_orthogonality_len16_n72_seed42.xlsx"
    )
    figure5_seqwalk_hybrid = (
        figure5_dir / "data" / "figure5_hybrid_len16_noflank_seqwalk_k6_seed42.xlsx"
    )
    figure5_benchmark_source = (
        benchmark_dir
        / "long_seq"
        / "data"
        / "batch_x______sigma1p0_seed41"
        / "len16"
        / "5p_none"
        / "hybrid_len16_5p_none_limitm8p16_budget10000000_init450_seed41.xlsx"
    )
    figure5_benchmark_dest_name = "figure5_search_only_hybrid_len16_noflank_init450.xlsx"

    if staging_root.exists():
        shutil.rmtree(staging_root)

    staging_root.mkdir(parents=True, exist_ok=True)

    copy_file(readme_source, standalone_readme)
    copy_file(readme_source, package_readme)

    copy_tree(
        short_seq_dataset_dir,
        package_root / "full_benchmark_results" / "short_seq" / "data" / short_seq_dataset_dir.name,
        ignore=ignore_common_junk,
    )
    copy_tree(
        short_seq_extracted_dir,
        package_root / "extracted_libraries" / "short_seq",
        ignore=ignore_common_junk,
    )

    for batch_name in long_seq_generated_batches:
        copy_tree(
            long_seq_generated_dir / batch_name,
            package_root / "full_benchmark_results" / "long_seq" / "configs" / "generated" / batch_name,
            ignore=ignore_common_junk,
        )

    for batch_name in long_seq_generated_batches:
        copy_tree(
            long_seq_data_dir / batch_name,
            package_root / "full_benchmark_results" / "long_seq" / "data" / batch_name,
            ignore=ignore_long_seq_batch_junk,
        )

    copy_tree(
        long_seq_extracted_dir,
        package_root / "extracted_libraries" / "long_seq",
        ignore=ignore_common_junk,
    )

    seqwalk_dir = package_root / "seqwalk_comparison"
    copy_file(figure5_seqwalk_max, seqwalk_dir / figure5_seqwalk_max.name)
    copy_file(figure5_seqwalk_hybrid, seqwalk_dir / figure5_seqwalk_hybrid.name)
    copy_file(figure5_benchmark_source, seqwalk_dir / figure5_benchmark_dest_name)

    clean_tree(staging_root)
    zip_tree(package_root, zip_path)

    print(f"\nZenodo staging folder ready at: {staging_root}")
