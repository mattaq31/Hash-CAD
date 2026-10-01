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
    "scale": 0.85,
    "row_padding": 200,
    "left_padding": 80,
    "text_gap": 120,
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


BASE_COLORS = {"A": "#9bbcff", "C": "#91d7a7", "G": "#c1a7e8", "T": "#d6b06a", "U": "#d6b06a"}
TERMINAL_COLORS = {"five-prime": "#008b8b", "three-prime": "#ff7f11"}


def _compute_complex_layout(complex_data, center_x, center_y, radius, params):
    """Compute positions and drawing elements for a single complex (format-agnostic)."""
    title = complex_data["title"]
    sequences = complex_data["sequences"]
    dot_bracket = complex_data["dot_bracket"]
    pairs = parse_dot_bracket(dot_bracket)
    positions, labels = _relax_positions(sequences, pairs, center_x, center_y, params)
    if len(labels) != len(dot_bracket.replace("+", "")):
        raise ValueError(f"{title}: sequence length does not match dot-bracket length")

    text_lines = _complex_text_lines(complex_data, params)
    backbone_sets = _backbone_point_sets(sequences, positions)

    terminal_bond_length = params["backbone_distance"] / 2 * 1.333
    terminals = []
    for start_i, end_i in _strand_terminal_indices(sequences):
        for index, neighbor_i, label, end_class in [
            (start_i, start_i + 1, "5'", "five-prime"), (end_i, end_i - 1, "3'", "three-prime"),
        ]:
            x, y = positions[index]
            nx, ny = positions[neighbor_i]
            dx, dy = x - nx, y - ny
            dist = (dx * dx + dy * dy) ** 0.5 or 1
            lx = x + terminal_bond_length * dx / dist
            ly = y + terminal_bond_length * dy / dist
            terminals.append({"x": x, "y": y, "lx": lx, "ly": ly, "label": label, "end_class": end_class,
                              "radius": params["terminal_circle_radius"]})

    return {"positions": positions, "labels": labels, "pairs": pairs, "radius": radius,
            "text_lines": text_lines, "backbone_sets": backbone_sets, "terminals": terminals}


def _complex_svg(layout, text_x, text_y, struct_offset_x):
    """Render a complex layout to SVG elements. Text on left, structure shifted right by struct_offset_x."""
    svg = []
    for i, line in enumerate(layout["text_lines"]):
        cls = "title" if i == 0 else "subtle"
        svg.append(f'<text x="{text_x:.1f}" y="{text_y + i * 20:.1f}" class="{cls}">{escape(line)}</text>')

    for points in layout["backbone_sets"]:
        path = " ".join(f"{'M' if i == 0 else 'L'} {x + struct_offset_x:.1f} {y:.1f}"
                        for i, (x, y) in enumerate(points))
        svg.append(f'<path d="{path}" class="backbone"/>')

    for left_i, right_i in layout["pairs"]:
        x1, y1 = layout["positions"][left_i]
        x2, y2 = layout["positions"][right_i]
        svg.append(f'<line x1="{x1 + struct_offset_x:.1f}" y1="{y1:.1f}" '
                   f'x2="{x2 + struct_offset_x:.1f}" y2="{y2:.1f}" class="bond"/>')

    for t in layout["terminals"]:
        svg.append(f'<line x1="{t["x"] + struct_offset_x:.1f}" y1="{t["y"]:.1f}" '
                   f'x2="{t["lx"] + struct_offset_x:.1f}" y2="{t["ly"]:.1f}" class="terminal-bond"/>')
        svg.append(f'<circle cx="{t["lx"] + struct_offset_x:.1f}" cy="{t["ly"]:.1f}" r="{t["radius"]}" '
                   f'class="terminal-circle terminal-{t["end_class"]}"/>')
        svg.append(f'<text x="{t["lx"] + struct_offset_x:.1f}" y="{t["ly"] + 3:.1f}" '
                   f'class="end-label">{t["label"]}</text>')

    for (x, y), base in zip(layout["positions"], layout["labels"]):
        svg.append(f'<circle cx="{x + struct_offset_x:.1f}" cy="{y:.1f}" r="12" class="{_base_class(base)}"/>')

    for (x, y), base in zip(layout["positions"], layout["labels"]):
        svg.append(f'<text x="{x + struct_offset_x:.1f}" y="{y + 5:.1f}" class="base">{escape(base)}</text>')

    return svg


def _render_complexes_to_matplotlib(layouts, text_col_width, view_width, view_height, output_path, params):
    """Render complex layouts directly to PDF using matplotlib (no system dependencies needed)."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle as MplCircle

    fig_w = view_width * params["scale"] / 72
    fig_h = view_height * params["scale"] / 72
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(0, view_width)
    ax.set_ylim(view_height, 0)
    ax.set_aspect("equal")
    ax.axis("off")

    row_padding = params["row_padding"]
    text_x = params["left_padding"]
    struct_center_x = text_col_width + params["text_gap"]

    y = 20
    for layout in layouts:
        radius = layout["radius"]
        row_height = 2 * radius + row_padding
        center_y = y + radius + row_padding / 2
        text_y = center_y - 50

        for i, line in enumerate(layout["text_lines"]):
            fontsize = 11 if i == 0 else 8
            weight = "bold" if i == 0 else "normal"
            color = "#222" if i == 0 else "#555"
            ax.text(text_x, text_y + i * 16, line,
                    fontsize=fontsize, fontweight=weight, color=color, fontfamily="sans-serif", va="top")

        struct_offset_x = struct_center_x
        for points in layout["backbone_sets"]:
            xs = [p[0] + struct_offset_x for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, color="#999", linewidth=1.5, solid_capstyle="round", solid_joinstyle="round", zorder=1)

        for left_i, right_i in layout["pairs"]:
            x1, y1 = layout["positions"][left_i]
            x2, y2 = layout["positions"][right_i]
            ax.plot([x1 + struct_offset_x, x2 + struct_offset_x], [y1, y2],
                    color="#b3263a", linewidth=2.4, alpha=0.9, zorder=2)

        for t in layout["terminals"]:
            ax.plot([t["x"] + struct_offset_x, t["lx"] + struct_offset_x], [t["y"], t["ly"]],
                    color="#999", linewidth=0.75, zorder=3)
            circ = MplCircle((t["lx"] + struct_offset_x, t["ly"]), t["radius"],
                             facecolor=TERMINAL_COLORS[t["end_class"]], edgecolor="#666", linewidth=0.5, zorder=4)
            ax.add_patch(circ)
            ax.text(t["lx"] + struct_offset_x, t["ly"], t["label"], fontsize=4, fontweight="bold", color="#333",
                    ha="center", va="center", fontfamily="sans-serif", zorder=5)

        for (x, bx_y), base in zip(layout["positions"], layout["labels"]):
            circ = MplCircle((x + struct_offset_x, bx_y), 12, facecolor=BASE_COLORS.get(base.upper(), "#ccc"),
                             edgecolor="#222", linewidth=0.7, zorder=6)
            ax.add_patch(circ)

        for (x, bx_y), base in zip(layout["positions"], layout["labels"]):
            ax.text(x + struct_offset_x, bx_y, base, fontsize=8, fontweight="bold", color="#111",
                    ha="center", va="center", fontfamily="sans-serif", zorder=7)

        y += row_height

    fig.savefig(str(output_path), format="pdf", bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)


def _write_svg(svg_text, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg_text)
    return output_path


def plot_dot_bracket_complexes(complexes, output_path, simulation_params=None, file_format="svg"):
    if file_format not in ("svg", "pdf"):
        raise ValueError("file_format must be 'svg' or 'pdf'")

    params = _simulation_params(simulation_params)
    row_padding = params["row_padding"]
    max_radius = max(_complex_radius(cd, params) for cd in complexes)
    row_heights = [2 * _complex_radius(cd, params) + row_padding for cd in complexes]
    text_col_width = _longest_text_line(complexes, params) * 10
    struct_col_width = 2 * max_radius + 80
    view_width = int(params["left_padding"] + text_col_width + params["text_gap"] + struct_col_width + 40)
    view_height = int(sum(row_heights) + 40)

    layouts = []
    y = 20
    for complex_data, row_height in zip(complexes, row_heights):
        radius = _complex_radius(complex_data, params)
        center_x = 0
        center_y = y + radius + row_padding / 2
        layouts.append(_compute_complex_layout(complex_data, center_x, center_y, radius, params))
        y += row_height

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if file_format == "pdf":
        _render_complexes_to_matplotlib(layouts, text_col_width, view_width, view_height, output_path, params)
        return output_path

    text_x = params["left_padding"]
    struct_offset_x = text_col_width + params["text_gap"]
    width = int(view_width * params["scale"])
    height = int(view_height * params["scale"])
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {view_width} {view_height}">',
        "<style>",
        "text { font-family: Helvetica, Arial, sans-serif; }",
        ".title { font-size: 20px; font-weight: 700; fill: #222; }",
        ".subtle { font-size: 14px; fill: #555; }",
        ".base { font-size: 13px; font-weight: 700; text-anchor: middle; fill: #111; }",
        ".end-label { font-size: 7px; font-weight: 700; text-anchor: middle; fill: #333; }",
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

    y = 20
    for layout, row_height in zip(layouts, row_heights):
        radius = layout["radius"]
        center_y = y + radius + row_padding / 2
        text_y = center_y - 50
        svg.extend(_complex_svg(layout, text_x, text_y, struct_offset_x))
        y += row_height

    svg.append("</svg>")
    return _write_svg("\n".join(svg), output_path)


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
