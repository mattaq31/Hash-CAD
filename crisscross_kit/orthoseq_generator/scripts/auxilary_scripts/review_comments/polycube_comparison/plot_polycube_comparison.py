"""Plot measured Polycube and OrthoSeq results from their standard association and complex-energy reports."""

from pathlib import Path

from comparison_functions import load_comparison_data, plot_comparison


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent
    data_dir = folder / "data"
    plots_dir = folder / "plots" / "assembly_37C_Na50mM_Mg12p5mM"
    reports = {
        "Menger": {"total": data_dir / "menger_total.xlsx", "totalu": data_dir / "menger_totalu.xlsx"},
        "OrthoSeq": {"total": data_dir / "orthoseq_assembly_search_2026-10-08_19-51-55.xlsx",
                     "totalu": data_dir / "orthoseq_totalu.xlsx"},
    }
    display_names = {"Menger": "Polycubes", "OrthoSeq": "OrthoSeq"}
    bins, visible_max_energy = 100, -4.0
    figure_width_mm, figure_height_mm, table_height_mm = 165.1, 142, 30
    style_scale = 8 / 19
    libraries = load_comparison_data(reports)
    output_path = plots_dir / f"polycubes_vs_orthoseq_{libraries['OrthoSeq']['pair_count']}_comparison.pdf"
    plot_comparison(
        libraries, output_path, display_names, bins, visible_max_energy,
        figure_width_mm, figure_height_mm, table_height_mm, style_scale,
    )
