import tomllib
from pathlib import Path

from nupack import Model, SetSpec, Strand, Tube, tube_analysis


def _normalize_sequence(sequence):
    return "".join(str(sequence).split())


class NupackTubeConfig:
    """Small config object for NUPACK nucleic acid tube analysis.

    sequences: list of [sequence_str, concentration_nM] pairs, e.g. [["GCGTATGC", 1000], ["GCATACGC", 500]].
    """

    def __init__(self, sequences, material="dna", celsius=37, sodium=0.05, magnesium=0.015,
                 max_complex_size=2, compute=None, options=None, tube_name="tube_1", strand_prefix="strand"):
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
            "sequences": self.sequences, "material": self.material, "celsius": self.celsius,
            "sodium": self.sodium, "magnesium": self.magnesium, "max_complex_size": self.max_complex_size,
            "compute": self.compute, "options": self.options,
            "tube_name": self.tube_name, "strand_prefix": self.strand_prefix,
        }

    def write(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_toml())
        return path

    def to_toml(self):
        sequences = ",\n    ".join(f'["{seq}", {conc}]' for seq, conc in self.sequences)
        compute = ", ".join(f'"{item}"' for item in self.compute)
        options = "\n".join(f"{k} = {v}" for k, v in self.options.items())

        return (f'sequences = [{sequences}]\n\n'
                f'material = "{self.material}"\ncelsius = {self.celsius}\n'
                f'sodium = {self.sodium}\nmagnesium = {self.magnesium}\n'
                f'max_complex_size = {self.max_complex_size}\ncompute = [{compute}]\n'
                f'tube_name = "{self.tube_name}"\nstrand_prefix = "{self.strand_prefix}"\n\n'
                f'[options]\n{options}\n')

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
        mfe = complex_result.mfe[0]
        minimum_free_energy = {
            "structure": str(mfe.structure), "energy_kcal_per_mol": float(mfe.energy),
            "stack_energy_kcal_per_mol": float(mfe.stack_energy),
        }

    return {
        "name": complex_obj.name,
        "strands": [s.name for s in complex_obj.strands],
        "sequences": [strand_sequences[s.name] for s in complex_obj.strands],
        "concentration_nM": float(concentration_m) * 1e9,
        "total_free_energy": complex_result.free_energy, "minimum_free_energy": minimum_free_energy,
    }


def run_nupack_analysis(config):
    """Run a NUPACK tube analysis. config.sequences holds [sequence_str, concentration_nM] pairs."""
    config = _load_config(config)

    strands = {}
    strand_sequences = {}
    for i, (sequence, concentration_nM) in enumerate(config["sequences"], start=1):  # (seq, conc_nM) pairs
        strand_name = f"{config.get('strand_prefix', 'strand')}_{i}"
        strand = Strand(sequence, name=strand_name)
        strands[strand] = concentration_nM * 1e-9
        strand_sequences[strand_name] = sequence

    model = Model(material=config.get("material", "dna"), celsius=config.get("celsius", 37),
                  sodium=config.get("sodium", 0.05), magnesium=config.get("magnesium", 0.015))
    tube = Tube(strands=strands, complexes=SetSpec(max_size=config.get("max_complex_size", 2)),
                name=config.get("tube_name", "tube_1"))

    analysis_result = tube_analysis(tubes=[tube], model=model, compute=config.get("compute", ["pfunc", "mfe"]),
                                    options=config.get("options", {}))

    tube_result = analysis_result[tube]
    complexes = {}
    for complex_obj, concentration_m in tube_result.complex_concentrations.items():
        complex_result = analysis_result[complex_obj]
        complexes[complex_obj.name] = _complex_to_dict(complex_obj, complex_result, concentration_m, strand_sequences)

    return {
        "config": config,
        "fraction_bases_unpaired": tube_result.fraction_bases_unpaired, "complexes": complexes,
    }


def _format_optional_number(value, digits=3):
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def _result_rows(result):
    rows = []
    for name, data in result["complexes"].items():
        mfe = data["minimum_free_energy"]
        mfe_value = mfe["energy_kcal_per_mol"] if mfe is not None else None
        mfe_structure = mfe["structure"] if mfe is not None else None
        rows.append({
            "complex": name, "sequences": " + ".join(data["sequences"]),
            "concentration_nM": data["concentration_nM"], "total_free_energy": data["total_free_energy"],
            "minimum_free_energy": mfe_value, "minimum_free_energy_structure": mfe_structure,
        })
    return rows


def _summary_text(title, result, rows):
    header = (f"{'Complex':20s} {'Sequences':30s} {'Conc nM':>12s} "
              f"{'Total free energy':>18s} {'Minimum free energy':>20s} {'Dot bracket':>25s}")
    lines = ["", title, "=" * len(title),
             f"Fraction bases unpaired: {_format_optional_number(result['fraction_bases_unpaired'])}",
             "", header, "-" * 138]

    for row in rows:
        lines.append(f"{row['complex']:20s} {row['sequences']:30s} {row['concentration_nM']:12.3f} "
                     f"{_format_optional_number(row['total_free_energy']):>18s} "
                     f"{_format_optional_number(row['minimum_free_energy']):>20s} "
                     f"{str(row['minimum_free_energy_structure'] or 'NA'):>25s}")

    return "\n".join(lines)


def _config_rows(config):
    """Flatten config dict into parameter/value rows. Sequences are unpacked as (sequence_str, concentration_nM)."""
    rows = []
    for key, value in config.items():
        if key == "sequences":
            for i, (sequence, conc) in enumerate(value, start=1):  # (seq, conc_nM) pairs
                rows.append({"parameter": f"sequence_{i}", "value": sequence})
                rows.append({"parameter": f"sequence_{i}_concentration_nM", "value": conc})
        elif key == "options":
            for opt_key, opt_value in value.items():
                rows.append({"parameter": f"options.{opt_key}", "value": opt_value})
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
        config = result["config"]
        output_path = Path(save) / f"{title}.xlsx"
        _save_binding_summary(output_path, rows, _config_rows(config))


if __name__ == "__main__":
    test_config = NupackTubeConfig(sequences=[["GCGTATGC", 1000], ["GCATACGC", 1000]])
    result = run_nupack_analysis(test_config)
    print_binding_summary("NUPACK analysis example", result)
