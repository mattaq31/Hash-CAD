#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import shutil
import tomllib
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
    parser = argparse.ArgumentParser(description="Stage the OrthoSeq benchmark data and optionally create its ZIP.")
    parser.add_argument("--no-zip", action="store_true", help="Update staged data and READMEs without rebuilding the ZIP.")
    args = parser.parse_args()

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
    short_seq_review_dir = benchmark_dir / "short_seq" / "data" / "len4_7_tttt5p_noGGGG_review"
    short_seq_extracted_dir = benchmark_dir / "short_seq" / "short_sequences"

    long_seq_generated_batches = [
        "batch_x_TTTT_sigma1p0_seed41",
        "batch_x______sigma1p0_seed41",
        "batch_x25TTTT_sigma1p0_seed41",
        "batch_x25_____sigma1p0_seed41",
        "batch_x_TTTT_sigma0p5_seed41",
        "batch_x______sigma0p5_seed41",
    ]
    long_seq_generated_dir = benchmark_dir / "long_seq" / "configs" / "generated"
    long_seq_data_dir = benchmark_dir / "long_seq" / "data"
    long_seq_extracted_dir = benchmark_dir / "long_seq" / "long_sequences"
    gmin_gmax_dir = benchmark_dir / "long_seq" / "scripts" / "auxiliary_analysis" / "gmin_gmax_comparison"

    comparison_dir = script_dir / "review_comments"
    nuad_dir = comparison_dir / "nuad_comparison"
    nuad_references = {
        "6mer": (
            short_seq_dataset_dir / "len6" / "results" / "benchmark_x"
            / "density0p1_vertex_cover_limit-6p583498094575131_seed2.xlsx"
        ),
        "12mer_wide": (
            long_seq_data_dir / "batch_x______sigma1p0_seed41" / "len12" / "5p_none"
            / "hybrid_len12_5p_none_limitm8p16_budget10000000_init250_seed41.xlsx"
        ),
        "12mer_narrow": (
            long_seq_data_dir / "batch_x______sigma0p5_seed41" / "len12" / "5p_none"
            / "hybrid_len12_5p_none_limitm8p16_budget10000000_init450_seed41.xlsx"
        ),
    }
    polycube_dir = comparison_dir / "polycube_comparison"
    polycube_workbooks = {
        "menger_published_sequences.xlsx": "published_polycube_sequences.xlsx",
        "menger_total.xlsx": "polycube_association_energies.xlsx",
        "menger_totalu.xlsx": "polycube_complex_energies.xlsx",
        "orthoseq_assembly_search_2026-10-08_19-51-55.xlsx": "orthoseq_polycube_search.xlsx",
        "orthoseq_totalu.xlsx": "orthoseq_polycube_complex_energies.xlsx",
    }

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

    # Preserve the existing ZIP while rebuilding the staged data, especially during --no-zip updates.
    if package_root.exists():
        shutil.rmtree(package_root)

    staging_root.mkdir(parents=True, exist_ok=True)

    copy_file(readme_source, standalone_readme)
    copy_file(readme_source, package_readme)

    copy_tree(
        short_seq_dataset_dir,
        package_root / "full_benchmark_results" / "short_seq" / "data" / short_seq_dataset_dir.name,
        ignore=ignore_common_junk,
    )
    short_seq_package_dir = package_root / "full_benchmark_results" / "short_seq" / "data" / short_seq_dataset_dir.name
    for dataset_dir in sorted(short_seq_review_dir.glob("len*")):
        if dataset_dir.is_dir():
            copy_tree(
                dataset_dir / "results" / "benchmark_x_review",
                short_seq_package_dir / dataset_dir.name / "results" / "benchmark_x_review",
                ignore=ignore_common_junk,
            )
    for summary in sorted(short_seq_review_dir.glob("benchmark_summary_*.toml")):
        copy_file(summary, short_seq_package_dir / summary.name)

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

    gmin_gmax_dest = package_root / "full_benchmark_results" / "long_seq" / "gmin_gmax_comparison"
    input_mapping = []
    for workbook in sorted((gmin_gmax_dir / "results" / "gmin_gmax_37C").glob("*.xlsx")):
        dest = gmin_gmax_dest / "results" / "gmin_gmax_37C" / workbook.name
        copy_file(workbook, dest)
        config_path = gmin_gmax_dir / "configs" / "generated" / "gmin_gmax_37C" / f"{workbook.stem}.toml"
        config = tomllib.loads(config_path.read_text())
        for graph in config["graphs"]:
            # Translate repository paths to archive paths without changing the historical workbooks.
            original_prefix = Path("crisscross_kit/orthoseq_generator/scripts/benchmarking/long_seq")
            relative_report = Path(graph["report"]).relative_to(original_prefix)
            input_report = package_root / "full_benchmark_results" / "long_seq" / relative_report
            if not input_report.is_file():
                raise FileNotFoundError(f"Missing packaged GMIN/GMAX input: {input_report}")
            input_mapping.append({
                "comparison_workbook": dest.relative_to(package_root).as_posix(),
                "initial_pair_count": graph["init_count"],
                "input_report": input_report.relative_to(package_root).as_posix(),
            })
    with (gmin_gmax_dest / "input_reports.tsv").open("w", newline="") as mapping_file:
        writer = csv.DictWriter(mapping_file, fieldnames=["comparison_workbook", "initial_pair_count", "input_report"],
                                delimiter="\t")
        writer.writeheader()
        writer.writerows(input_mapping)

    seqwalk_dir = package_root / "seqwalk_comparison"
    copy_file(figure5_seqwalk_max, seqwalk_dir / figure5_seqwalk_max.name)
    copy_file(figure5_seqwalk_hybrid, seqwalk_dir / figure5_seqwalk_hybrid.name)
    copy_file(figure5_benchmark_source, seqwalk_dir / figure5_benchmark_dest_name)

    for case, reference in nuad_references.items():
        source_dir = nuad_dir / "results" / case
        dest_dir = package_root / "nuad_comparison" / "results" / case
        copy_file(source_dir / "nuad.xlsx", dest_dir / "nuad.xlsx")
        copy_tree(source_dir / "raw_nuad", dest_dir / "raw_nuad", ignore=ignore_common_junk)
        # Duplicate the exact benchmark reference so each comparison can be read in one folder.
        copy_file(reference, dest_dir / "orthoseq.xlsx")

    for source_name, archive_name in polycube_workbooks.items():
        copy_file(polycube_dir / "data" / source_name, package_root / "polycube_comparison" / "data" / archive_name)

    clean_tree(staging_root)
    if not args.no_zip:
        zip_tree(package_root, zip_path)
    else:
        print("Skipped ZIP creation (--no-zip).")

    print(f"\nZenodo staging folder ready at: {staging_root}")
