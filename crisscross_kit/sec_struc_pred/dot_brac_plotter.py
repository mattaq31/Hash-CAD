from pathlib import Path
from math import cos, pi, sin
from random import Random
from xml.sax.saxutils import escape

import numpy as np


BASE_SIMULATION_PARAMS = {
    "backbone_distance": 34,
    "pair_distance_factor": 1.5,
    "start_radius": 95,
    "reference_sequence_length": 16,
    "relaxation_steps": 15000,
    "step_size": 1.00,
    "start_jitter": 8,
    "backbone_spring": 0.035,
    "pair_spring": 0.15,
    "backbone_straightness": 0.148,
    "centering": 0.0006,
    "neighbor_repulsion": 40,
    "base_repulsion": 1500,
    "scale": 0.5,
    "row_padding": 1000,
    "left_padding": 650,
    "text_gap": 600,
    "brownian_jitter": 0,
    "text_line_width": 105,
    "terminal_circle_radius": 6,
}
DEFAULT_SIMULATION_PARAMS = dict(BASE_SIMULATION_PARAMS)


def set_simulation_params(**params):
    unknown_params = set(params) - set(DEFAULT_SIMULATION_PARAMS)
    if unknown_params:
        raise KeyError(f"Unknown simulation params: {sorted(unknown_params)}")
    DEFAULT_SIMULATION_PARAMS.update(params)


def set_simulation_param(name, value):
    set_simulation_params(**{name: value})


def reset_simulation_params():
    DEFAULT_SIMULATION_PARAMS.clear()
    DEFAULT_SIMULATION_PARAMS.update(BASE_SIMULATION_PARAMS)


def get_simulation_params():
    return dict(DEFAULT_SIMULATION_PARAMS)


def parse_dot_bracket(dot_bracket):
    pairs = []
    stack = []
    base_index = 0

    for char in dot_bracket:
        if char == "+":
            continue
        if char == "(":
            stack.append(base_index)
        elif char == ")":
            pairs.append((stack.pop(), base_index))
        base_index += 1

    return pairs


def _simulation_params(simulation_params=None):
    params = dict(DEFAULT_SIMULATION_PARAMS)
    if simulation_params:
        params.update(simulation_params)
    params["pair_distance"] = params["backbone_distance"] * params["pair_distance_factor"]
    return params


def _initial_radius(sequence_length, params):
    return params["start_radius"] * sequence_length / params["reference_sequence_length"]


def _complex_radius(complex_data, params):
    sequence_length = sum(len(sequence) for sequence in complex_data["sequences"])
    return _initial_radius(sequence_length, params)


def _circle_positions(sequences, center_x, center_y, radius, params):
    sequence = "".join(sequences)
    positions = []
    labels = []
    n = len(sequence)
    rng = Random(1)

    for i, base in enumerate(sequence):
        angle = -pi / 2 + 2 * pi * i / n
        x = center_x + radius * cos(angle) + rng.uniform(-params["start_jitter"], params["start_jitter"])
        y = center_y + radius * sin(angle) + rng.uniform(-params["start_jitter"], params["start_jitter"])
        positions.append((x, y))
        labels.append(base)

    return positions, labels


def _add_springs(forces, positions, edges, target_distance, strength):
    if len(edges) == 0:
        return

    left = edges[:, 0]
    right = edges[:, 1]
    delta = positions[right] - positions[left]
    distance = np.linalg.norm(delta, axis=1)
    distance[distance == 0] = 0.001
    force = strength * (distance - target_distance)
    force_vectors = delta * (force / distance)[:, None]

    np.add.at(forces, left, force_vectors)
    np.add.at(forces, right, -force_vectors)


def _backbone_terms(sequences):
    edges = []
    triples = []
    start = 0

    for sequence in sequences:
        for i in range(start, start + len(sequence) - 1):
            edges.append((i, i + 1))
        for i in range(start + 1, start + len(sequence) - 1):
            triples.append((i - 1, i, i + 1))
        start += len(sequence)

    return np.array(edges, dtype=int), np.array(triples, dtype=int)


def _add_straightness(forces, positions, triples, strength):
    if len(triples) == 0:
        return

    left = triples[:, 0]
    mid = triples[:, 1]
    right = triples[:, 2]
    target = (positions[left] + positions[right]) / 2
    force_vectors = (target - positions[mid]) * strength

    np.add.at(forces, mid, force_vectors)
    np.add.at(forces, left, -force_vectors * 0.5)
    np.add.at(forces, right, -force_vectors * 0.5)


def _repulsion_matrix(num_positions, backbone_edges, params):
    repulsion = np.full((num_positions, num_positions), params["base_repulsion"], dtype=float)
    np.fill_diagonal(repulsion, 0)
    if len(backbone_edges):
        left = backbone_edges[:, 0]
        right = backbone_edges[:, 1]
        repulsion[left, right] = params["neighbor_repulsion"]
        repulsion[right, left] = params["neighbor_repulsion"]
    return repulsion


def _add_repulsion(forces, positions, repulsion):
    dx = positions[:, 0][None, :] - positions[:, 0][:, None]
    dy = positions[:, 1][None, :] - positions[:, 1][:, None]
    distance_squared = dx * dx + dy * dy
    distance_squared[distance_squared == 0] = 0.001

    force = repulsion / distance_squared
    distance = np.sqrt(distance_squared)
    fx = force * dx / distance
    fy = force * dy / distance

    forces[:, 0] -= fx.sum(axis=1)
    forces[:, 1] -= fy.sum(axis=1)


def _relax_positions(sequences, pairs, center_x, center_y, params):
    sequence_length = sum(len(sequence) for sequence in sequences)
    radius = _initial_radius(sequence_length, params)
    positions, labels = _circle_positions(sequences, center_x, center_y, radius, params)
    positions = np.array(positions, dtype=float)
    backbone_edges, backbone_triples = _backbone_terms(sequences)
    pair_edges = np.array(pairs, dtype=int)
    repulsion = _repulsion_matrix(len(positions), backbone_edges, params)
    rng = np.random.default_rng(2)
    center = np.array([center_x, center_y])

    for _ in range(params["relaxation_steps"]):
        forces = np.zeros_like(positions)

        _add_springs(forces, positions, backbone_edges, params["backbone_distance"], params["backbone_spring"])
        _add_straightness(forces, positions, backbone_triples, params["backbone_straightness"])
        _add_springs(forces, positions, pair_edges, params["pair_distance"], params["pair_spring"])
        _add_repulsion(forces, positions, repulsion)
        forces += (center - positions) * params["centering"]
        forces += rng.uniform(-params["brownian_jitter"], params["brownian_jitter"], size=forces.shape)

        movement = np.clip(forces * params["step_size"], -4, 4)
        positions += movement

    return positions.tolist(), labels


def _backbone_point_sets(sequences, positions):
    point_sets = []
    start = 0
    for sequence in sequences:
        end = start + len(sequence)
        point_sets.append(positions[start:end])
        start = end
    return point_sets


def _strand_terminal_indices(sequences):
    indices = []
    start = 0
    for sequence in sequences:
        end = start + len(sequence) - 1
        indices.append((start, end))
        start = end + 1
    return indices


def _complex_metadata_lines(complex_data):
    lines = []
    if "total_free_energy" in complex_data:
        lines.append(f"Total free energy: {complex_data['total_free_energy']:.4f} kcal/mol")
    if "minimum_free_energy" in complex_data:
        lines.append(f"Minimum free energy: {complex_data['minimum_free_energy']:.4f} kcal/mol")
    if "concentration_nM" in complex_data:
        lines.append(f"Concentration: {complex_data['concentration_nM']:.4f} nM")
    return lines


def _wrap_text(text, max_chars):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)] or [""]


def _complex_text_lines(complex_data, params):
    lines = [complex_data["title"]]
    for i, sequence in enumerate(complex_data["sequences"], start=1):
        for line in _wrap_text(sequence, params["text_line_width"]):
            lines.append(f"seq_{i}: {line}")
    for line in _wrap_text(complex_data["dot_bracket"], params["text_line_width"]):
        lines.append(f"dot: {line}")
    lines.extend(_complex_metadata_lines(complex_data))
    return lines


def _longest_text_line(complexes, params):
    return max(len(line) for complex_data in complexes for line in _complex_text_lines(complex_data, params))


def _base_class(base):
    return f"base-circle base-circle-{base.upper()}"


def _complex_svg(complex_data, center_x, center_y, radius, params):
    title = complex_data["title"]
    sequences = complex_data["sequences"]
    dot_bracket = complex_data["dot_bracket"]
    pairs = parse_dot_bracket(dot_bracket)
    positions, labels = _relax_positions(sequences, pairs, center_x, center_y, params)
    if len(labels) != len(dot_bracket.replace("+", "")):
        raise ValueError(f"{title}: sequence length does not match dot-bracket length")

    text_x = center_x + radius + params["text_gap"]
    text_y = center_y - 85
    svg = []
    for i, line in enumerate(_complex_text_lines(complex_data, params)):
        class_name = "title" if i == 0 else "subtle"
        svg.append(f'<text x="{text_x:.1f}" y="{text_y + i * 18:.1f}" class="{class_name}">{escape(line)}</text>')

    for points in _backbone_point_sets(sequences, positions):
        path = " ".join(
            f"{'M' if i == 0 else 'L'} {x:.1f} {y:.1f}"
            for i, (x, y) in enumerate(points)
        )
        svg.append(f'<path d="{path}" class="backbone"/>')

    for left_i, right_i in pairs:
        x1, y1 = positions[left_i]
        x2, y2 = positions[right_i]
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="bond"/>')

    terminal_bond_length = params["backbone_distance"] / 2 * 1.333
    for start_i, end_i in _strand_terminal_indices(sequences):
        terminal_data = [
            (start_i, start_i + 1, "5'", "five-prime"),
            (end_i, end_i - 1, "3'", "three-prime"),
        ]
        for index, neighbor_i, label, end_class in terminal_data:
            x, y = positions[index]
            neighbor_x, neighbor_y = positions[neighbor_i]
            dx = x - neighbor_x
            dy = y - neighbor_y
            distance = (dx * dx + dy * dy) ** 0.5 or 1
            label_x = x + terminal_bond_length * dx / distance
            label_y = y + terminal_bond_length * dy / distance
            svg.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{label_x:.1f}" y2="{label_y:.1f}" class="terminal-bond"/>')
            terminal_radius = params["terminal_circle_radius"]
            svg.append(f'<circle cx="{label_x:.1f}" cy="{label_y:.1f}" r="{terminal_radius}" class="terminal-circle terminal-{end_class}"/>')
            svg.append(f'<text x="{label_x:.1f}" y="{label_y + 4:.1f}" class="end-label">{label}</text>')

    for (x, base_y), base in zip(positions, labels):
        svg.append(f'<circle cx="{x:.1f}" cy="{base_y:.1f}" r="12" class="{_base_class(base)}"/>')

    for (x, base_y), base in zip(positions, labels):
        svg.append(f'<text x="{x:.1f}" y="{base_y + 5:.1f}" class="base">{escape(base)}</text>')

    return svg


def _write_plot_output(svg_text, output_path, file_format):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if file_format == "svg":
        output_path.write_text(svg_text)
    elif file_format == "pdf":
        try:
            import cairosvg
            cairosvg.svg2pdf(bytestring=svg_text.encode(), write_to=str(output_path))
        except (ImportError, OSError) as exc:
            raise RuntimeError(
                "PDF output needs cairosvg and the Cairo system library. "
                "In this conda environment, try: conda install -c conda-forge cairo cairosvg. "
                "Or use file_format='svg'."
            ) from exc
    else:
        raise ValueError("file_format must be 'svg' or 'pdf'")

    return output_path


def plot_dot_bracket_complexes(complexes, output_path, simulation_params=None, file_format="svg"):
    params = _simulation_params(simulation_params)
    row_padding = params["row_padding"]
    max_radius = max(_complex_radius(complex_data, params) for complex_data in complexes)
    row_heights = [2 * _complex_radius(complex_data, params) + row_padding for complex_data in complexes]
    text_width = _longest_text_line(complexes, params) * 8
    view_width = int(max(900, 2 * max_radius + params["left_padding"] + params["text_gap"] + text_width + 80))
    width = int(view_width * params["scale"])
    height = int((sum(row_heights) + 60) * params["scale"])
    view_height = int(sum(row_heights) + 60)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {view_width} {view_height}">',
        "<style>",
        "text { font-family: Helvetica, Arial, sans-serif; }",
        ".title { font-size: 18px; font-weight: 700; fill: #222; }",
        ".subtle { font-size: 13px; fill: #555; }",
        ".base { font-size: 13px; font-weight: 700; text-anchor: middle; fill: #111; }",
        ".end-label { font-size: 9px; font-weight: 700; text-anchor: middle; fill: #333; }",
        ".base-circle { stroke: #222; stroke-width: 1.4; }",
        ".terminal-circle { stroke: #666; stroke-width: 1.0; }",
        ".terminal-five-prime { fill: #008b8b; }",
        ".terminal-three-prime { fill: #ff7f11; }",
        ".terminal-bond { stroke: #999; stroke-width: 1.5; stroke-linecap: round; }",
        ".base-circle-A { fill: #9bbcff; }",
        ".base-circle-C { fill: #91d7a7; }",
        ".base-circle-G { fill: #c1a7e8; }",
        ".base-circle-T { fill: #d6b06a; }",
        ".base-circle-U { fill: #d6b06a; }",
        ".bond { stroke: #b3263a; stroke-width: 4.8; opacity: 0.9; }",
        ".backbone { fill: none; stroke: #999; stroke-width: 3.0; stroke-linecap: round; stroke-linejoin: round; }",
        "</style>",
    ]

    y = 30
    for complex_data, row_height in zip(complexes, row_heights):
        radius = _complex_radius(complex_data, params)
        center_x = max_radius + params["left_padding"]
        center_y = y + radius + row_padding / 2
        svg.extend(_complex_svg(
            complex_data,
            center_x,
            center_y,
            radius,
            params,
        ))
        y += row_height

    svg.append("</svg>")

    return _write_plot_output("\n".join(svg), output_path, file_format)


def _safe_filename(title):
    return "".join(char if char.isalnum() or char in "._- " else "_" for char in title).strip()


def _nupack_complex_to_plot_data(name, complex_data):
    minimum_free_energy = complex_data.get("minimum_free_energy")
    if not minimum_free_energy:
        return None

    return {
        "title": name,
        "sequences": complex_data["sequences"],
        "dot_bracket": minimum_free_energy["structure"],
        "total_free_energy": complex_data.get("total_free_energy"),
        "minimum_free_energy": minimum_free_energy.get("energy_kcal_per_mol"),
        "concentration_nM": complex_data.get("concentration_nM"),
    }


def plot_nupack_result(title, result, save="", simulation_params=None, file_format="svg"):
    complexes = []
    for name, complex_data in result["complexes"].items():
        plot_data = _nupack_complex_to_plot_data(name, complex_data)
        if plot_data:
            complexes.append(plot_data)

    if not save:
        save = Path(__file__).parent / "default_outputs"

    output_path = Path(save) / f"{_safe_filename(title)}.{file_format}"
    return plot_dot_bracket_complexes(
        complexes,
        output_path,
        simulation_params=simulation_params,
        file_format=file_format,
    )


if __name__ == "__main__":
    examples = [
        {
            "title": "(seq_1)",
            "sequences": ["CATATCCGCGTCGCTGCGCTCAGACCCACCACCACGCACC"],
            "dot_bracket": ".......((...))((((................))))..",
            "total_free_energy": -3.869,
            "minimum_free_energy": -2.664,
            "concentration_nM": 967.997,
        },
        {
            "title": "(seq_1+seq_1 long)",
            "sequences": [
                "CATATCCGCGTCGCTGCGCTCAGACCCACCACCACGCACC",
                "CATATCCGCGTCGCTGCGCTCAGACCCACCACCACGCACC",
            ],
            "dot_bracket": ".......(((.(((((((................))))..+.......))).)))((((................))))..",
            "total_free_energy": -16.215,
            "minimum_free_energy": -16.099,
            "concentration_nM": 16.002,
        },
        {
            "title": "(seq_1+seq_1)",
            "sequences": ["GCGTATGC", "GCGTATGC"],
            "dot_bracket": "((.((.((+)).)).))",
        },
        {
            "title": "(seq_2+seq_3)",
            "sequences": ["GCATACGC", "TTTTTTTT"],
            "dot_bracket": "....(...+.)......",
        },
    ]

    output = Path(__file__).parent / "default_outputs" / "test.svg"
    plot_dot_bracket_complexes(examples, output)
    print(f"Wrote {output}")
