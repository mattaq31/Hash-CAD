import tomllib
from pathlib import Path

from nupack import Model, SetSpec, Strand, Tube, tube_analysis


class NupackTubeConfig:
    """Small config object for NUPACK nucleic acid tube analysis."""

    def __init__(
            self,
            sequences,
            material="dna",
            celsius=37,
            sodium=0.05,
            magnesium=0.015,
            max_complex_size=2,
            compute=None,
            options=None,
            tube_name="tube_1",
            strand_prefix="strand",
    ):
        self.sequences = sequences
        self.material = material
        self.celsius = celsius
        self.sodium = sodium
        self.magnesium = magnesium
        self.max_complex_size = max_complex_size
        self.compute = compute or ["pfunc", "mfe"]
        self.options = options or {}
        self.tube_name = tube_name
        self.strand_prefix = strand_prefix

    def to_dict(self):
        return {
            "sequences": self.sequences,
            "material": self.material,
            "celsius": self.celsius,
            "sodium": self.sodium,
            "magnesium": self.magnesium,
            "max_complex_size": self.max_complex_size,
            "compute": self.compute,
            "options": self.options,
            "tube_name": self.tube_name,
            "strand_prefix": self.strand_prefix,
        }

    def write(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_toml())
        return path

    def to_toml(self):
        sequences = ",\n    ".join(
            f'["{sequence}", {concentration_nM}]'
            for sequence, concentration_nM in self.sequences
        )
        compute = ", ".join(f'"{item}"' for item in self.compute)
        options = "\n".join(f"{key} = {value}" for key, value in self.options.items())

        text = f"""sequences = [
    {sequences}
]

material = "{self.material}"
celsius = {self.celsius}
sodium = {self.sodium}
magnesium = {self.magnesium}
max_complex_size = {self.max_complex_size}
compute = [{compute}]
tube_name = "{self.tube_name}"
strand_prefix = "{self.strand_prefix}"

[options]
{options}
"""
        return text

    @classmethod
    def from_file(cls, path):
        with Path(path).open("rb") as f:
            return cls(**tomllib.load(f))


def _load_config(config):
    if isinstance(config, NupackTubeConfig):
        return config.to_dict()
    if isinstance(config, (str, Path)):
        return NupackTubeConfig.from_file(config).to_dict()
    return dict(config)


def _complex_to_dict(complex_obj, complex_result, concentration_m, strand_sequences):
    minimum_free_energy = None
    if complex_result.mfe:
        minimum_free_energy = {
            "structure": str(complex_result.mfe[0].structure),
            "energy_kcal_per_mol": float(complex_result.mfe[0].energy),
            "stack_energy_kcal_per_mol": float(complex_result.mfe[0].stack_energy),
        }

    return {
        "name": complex_obj.name,
        "strands": [strand.name for strand in complex_obj.strands],
        "sequences": [strand_sequences[strand.name] for strand in complex_obj.strands],
        "concentration_nM": float(concentration_m) * 1e9,
        "total_free_energy": complex_result.free_energy,
        "minimum_free_energy": minimum_free_energy,
    }


def run_nupack_analysis(config):
    config = _load_config(config)

    strands = {}
    strand_sequences = {}
    for i, (sequence, concentration_nM) in enumerate(config["sequences"], start=1):
        strand_name = f"{config.get('strand_prefix', 'strand')}_{i}"
        strand = Strand(sequence, name=strand_name)
        strands[strand] = concentration_nM * 1e-9
        strand_sequences[strand_name] = sequence

    model = Model(
        material=config.get("material", "dna"),
        celsius=config.get("celsius", 37),
        sodium=config.get("sodium", 0.05),
        magnesium=config.get("magnesium", 0.015),
    )
    tube = Tube(
        strands=strands,
        complexes=SetSpec(max_size=config.get("max_complex_size", 2)),
        name=config.get("tube_name", "tube_1"),
    )

    analysis_result = tube_analysis(
        tubes=[tube],
        model=model,
        compute=config.get("compute", ["pfunc", "mfe"]),
        options=config.get("options", {}),
    )

    tube_result = analysis_result[tube]
    complexes = {}
    for complex_obj, concentration_m in tube_result.complex_concentrations.items():
        complex_result = analysis_result[complex_obj]
        complexes[complex_obj.name] = _complex_to_dict(
            complex_obj,
            complex_result,
            concentration_m,
            strand_sequences,
        )

    return {
        "config": config,
        "direct_config": config,
        "fraction_bases_unpaired": tube_result.fraction_bases_unpaired,
        "complexes": complexes,
    }


def _format_optional_number(value, digits=3):
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def _result_rows(result):
    rows = []
    for name, data in result["complexes"].items():
        minimum_free_energy = data["minimum_free_energy"]
        minimum_free_energy_value = None
        minimum_free_energy_structure = None
        if minimum_free_energy is not None:
            minimum_free_energy_value = minimum_free_energy["energy_kcal_per_mol"]
            minimum_free_energy_structure = minimum_free_energy["structure"]

        rows.append({
            "complex": name,
            "sequences": " + ".join(data["sequences"]),
            "concentration_nM": data["concentration_nM"],
            "total_free_energy": data["total_free_energy"],
            "minimum_free_energy": minimum_free_energy_value,
            "minimum_free_energy_structure": minimum_free_energy_structure,
        })
    return rows


def _summary_text(title, result, rows):
    lines = [
        "",
        title,
        "=" * len(title),
        f"Fraction bases unpaired: {_format_optional_number(result['fraction_bases_unpaired'])}",
        "",
        f"{'Complex':20s} "
        f"{'Sequences':30s} "
        f"{'Conc nM':>12s} "
        f"{'Total free energy':>18s} "
        f"{'Minimum free energy':>20s} "
        f"{'Dot bracket':>25s}",
        "-" * 138,
    ]

    for row in rows:
        lines.append(
            f"{row['complex']:20s} "
            f"{row['sequences']:30s} "
            f"{row['concentration_nM']:12.3f} "
            f"{_format_optional_number(row['total_free_energy']):>18s} "
            f"{_format_optional_number(row['minimum_free_energy']):>20s} "
            f"{str(row['minimum_free_energy_structure'] or 'NA'):>25s}"
        )

    return "\n".join(lines)


def _config_rows(config):
    rows = []
    for key, value in config.items():
        if key == "sequences":
            for i, (sequence, concentration_nM) in enumerate(value, start=1):
                rows.append({"parameter": f"sequence_{i}", "value": sequence})
                rows.append({"parameter": f"sequence_{i}_concentration_nM", "value": concentration_nM})
        elif key == "options":
            for option_key, option_value in value.items():
                rows.append({"parameter": f"options.{option_key}", "value": option_value})
        else:
            rows.append({"parameter": key, "value": value})
    return rows


def _save_binding_summary(save, result_rows, config_rows):
    import pandas as pd

    excel_path = Path(save)
    excel_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(excel_path) as writer:
        pd.DataFrame(result_rows).to_excel(writer, sheet_name="results", index=False)
        pd.DataFrame(config_rows).to_excel(writer, sheet_name="config", index=False)


def print_binding_summary(title, result, save=""):
    rows = _result_rows(result)
    text = _summary_text(title, result, rows)
    print(text)

    if save:
        config = result.get("direct_config", result["config"])
        output_path = Path(save) / f"{title}.xlsx"
        _save_binding_summary(output_path, rows, _config_rows(config))


if __name__ == "__main__":
    test_config = NupackTubeConfig(
        sequences=[
            ["GCGTATGC", 1000],
            ["GCATACGC", 1000],
        ],
    )
    result = run_nupack_analysis(test_config)
    print_binding_summary("NUPACK analysis example", result)
